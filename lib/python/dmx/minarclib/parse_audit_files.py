from datetime import datetime
import json
import os
import psutil
import shutil
import stat
import subprocess
import sys
import xlrd
import xml.etree.ElementTree as ElementTree

from dmx.utillib.decorators import memoized
from joblib import Parallel, delayed
from dmx.abnrlib.workspace import Workspace
from dmx.ecolib.ecosphere import EcoSphere
from dmx.ecolib.iptype import IPTypeError
from dmx.ipqclib.ipqc import IPQC
from dmx.tnrlib.audit_check import AuditFile
from dmx.utillib.arcenv import ARCEnv
from dmx.utillib.arcutils import ArcUtils

from printers import DBPrinter, StdoutPrinter
from logger import Logger

logger = Logger()

# TODO: still not totally atomic, if audit files aren't
#       parsed, the cells and deliverables should be removed
def atomic_parse(
    ip_name, 
    milestone,
    rel_id=None, 
    preserve_workspace=True, 
    cli=False,
    single_deliverable=None,
    arc_override=None,
    output_file=None): 

    printer = None
    if cli:
        printer = StdoutPrinter(override_file=arc_override, output_file=output_file)
    else:
        printer = DBPrinter()
    
    include_hierarchy = False
    if not ip_name:
        include_hierarchy = True
        ip_name = workspace._ip

    printer.store_ip(ip_name)
    workspace_location = printer.store_rel(rel_id)

    printer.lock()

    # get ecosystem info for extracting cells & deliverables 
    os.chdir(workspace_location)

    workspace = Workspace()
    ip = EcoSphere().get_family().get_ip(ip_name)

    # IPQC class is needed to get the correct status for POR, hierachy, etc
    ipqc = IPQC(milestone, ip_name)
    ipqc.init_ip()

    parse(ip_name, ipqc, ip, milestone, rel_id, workspace_location, single_deliverable, printer) 

    if include_hierarchy: 
        for sub_ipqc in ipqc.hierarchy:
            printer.store_ip(sub_ipqc.ip.name)
            ip = EcoSphere().get_family().get_ip(sub_ipqc.ip.name)
            parse(sub_ipqc.ip.name, sub_ipqc, ip, sub_ipqc.ip.milestone, rel_id, workspace_location, single_deliverable, printer) 

    printer.unlock()

    if preserve_workspace == False:
        workspace.delete()
        shutil.rmtree(workspace_location)


def parse(ip_name, ipqc, ip, milestone, rel_id, workspace_location, single_deliverable, printer): 
    rel_name = ipqc.bom

    # set the owner for the rel
    printer.store_owner(ip.owner)

    # need to perform a check in order to get waiver status
    arc = ARCEnv()
    
    # the project id is needed for the hierarchy
    project = ipqc.ip.project
    
    # resolve flat hierarchy by linking the sub-Rels together
    #
    # TODO: For now, we're assuming any sub-Rel is already registered
    #       into the database. It was suggested to recursively resolve
    #       the hierarchy. There may be a use case where this is needed.
    for sub_ip, bom in ipqc.ip.boms.items():
        
        # if the sub ip is the name of the ip, it's not a sub ip
        if sub_ip == ip_name:
            continue

        printer.store_hierarchy(sub_ip, bom)

    needed_deliverables = []
    
    # store cells & deliverables for future use
    if single_deliverable:
        
        # see if the deliverable is part of this IP. If not, don't bother
        # running the rest of the code for this deliverable
        try:
            d = ip.get_deliverable(single_deliverable)
            d.del_id = None
            needed_deliverables.append(d)
        except IPTypeError: 
            return 
    else:

        # if we're checking all deliverables, we can't assume statuses
        # such as por, waived, ect. So only run the relevant part of
        # of the workspace check. 
        ipqc.ip.workspace.check(
            ip_name,
            milestone,
            arc.get_thread(), 
            deliverable=None,
            nowarnings=True,
            validate_deliverable_existence_check=True, 
            validate_type_check=False, 
            validate_checksum_check=False, 
            validate_result_check=False, 
            validate_goldenarc_check=False, 
            familyobj=ipqc.ip.family
        )
    
        deliverables = ip.get_all_deliverables()

        # put all the cells and deliverables into the db
        for deliverable in deliverables:
            d = ipqc.ip.get_deliverable_ipqc(deliverable.name)

            bom = d.bom

            # can't use d.owner as it only provides email
            owner = deliverable.get_deliverable_owner(
                project,
                ipqc.ip.name,
                d.name,
                bom
            )

            # check for POR / not POR now
            not_por = d.is_unneeded

            # waived status must be generated after ws.check
            deliverable_errors = ipqc \
                .ip \
                .workspace \
                .get_deliverable_existence_errors(d.name)

            d.waived = False
            if deliverable_errors['waived'] != []:
                d.waived = True

            waived = d.waived
            
            del_id = printer.store_deliverable(
                deliverable.name, not_por, 
                bom, owner, d.owner, waived
            )

            if not not_por and not waived:
                deliverable.del_id = del_id
                needed_deliverables.append(deliverable)

    cells = ipqc.ip.topcells
    for cell in cells:
        cell.cell_id = printer.store_cell(cell.name)
    
    # data structure to hold audit files
    auditList = {}

    # get checkers for the important deliverables
    for deliverable in needed_deliverables:
        for cell in cells:
            not_por = False
            for ipqc_del in cell.deliverables:
                if deliverable.name == ipqc_del.name:
                    not_por = ipqc_del.is_unneeded
                    break

            for checker in deliverable.get_checkers():
                checker = {
                    'ref': checker,
                    'cell_id': cell.cell_id,
                    'cell_name': cell.name,
                    'del_id': deliverable.del_id,
                    'del_name': deliverable.name,
                    'audits': [],
                    'not_por': not_por
                }

                if deliverable.name not in auditList.keys():
                    auditList[deliverable.name] = [checker,]
                else:
                    auditList[deliverable.name].append(checker)

    min_resources = generate_min_resources(project)
    
#    Parallel(
#        n_jobs=len(auditList.keys()), 
#        backend="threading"
#    )(delayed(get_audit_status)(
#        min_resources,
#        ip.name,
#        rel_name,
#        checkers,
#        workspace_location,
#        printer
#    ) for key, checkers in auditList.items())

    for key, checkers in auditList.items():
        get_audit_status(    
            min_resources,
            ip.name,
            rel_name,
            checkers,
            workspace_location,
            printer
        )

def generate_min_resources(project):

    # bring min/crit resource versions into memory
    # TODO: store this into the database
    #       then extract the data from the db
    fp = '/nfs/site/disks/da_infra_1/reports/testaudit/FM6RevB_Minimum_Resource.xlsm'
    if (project == 'rnr'):
        fp = '/nfs/site/disks/da_infra_1/reports/testaudit/RNR_Minimum_Resource.xlsm'
    if (project == 'gdr'):
        fp = '/nfs/site/disks/da_infra_1/reports/testaudit/GDR_Minimum_Resource.xlsm'

    sheet = xlrd.open_workbook(fp, 'rb').sheet_by_name('Latest Arc Bundle')
 
    # increasing mem usage for shorter runtime here
    #
    # instead of iterating through all min_resources, create a data structure
    # of min_res[deliverable][flow][subflow] and store duplicates of any resource
    # fitting those conditions.
    min_resources = {} 
    for row_num in range(sheet.nrows):
        if sheet.cell(row_num, 1).value != 'Signoff Reviewed by Designer':
            continue
        
        minimum = sheet.cell(row_num, 15).value.split('/', 1)
        if len(minimum) != 2:
            continue

        minimum = minimum[1]
        last_important = sheet.cell(row_num, 23).value
        
        if not len(str(last_important).strip()):
            last_important = minimum
        else:
            last_important = last_important.split('/', 1)
            if len(last_important) == 1:
                last_important = last_important[0]
            else:
                last_important = last_important[1] 
        resource = {
            'minimum': minimum,
            'last_important': last_important,
            'name': sheet.cell(row_num, 3).value.split('/', 1)[0]
        }

        for libtype in  [
                sheet.cell(row_num, 26).value,
                sheet.cell(row_num, 27).value,
                sheet.cell(row_num, 28).value,
                sheet.cell(row_num, 29).value,
                sheet.cell(row_num, 30).value,
                sheet.cell(row_num, 31).value,
                sheet.cell(row_num, 32).value
            ]:

            if not libtype:
                continue

            if libtype not in min_resources.keys():
                min_resources[libtype] = {}

            for flow_subflow in sheet.cell(row_num, 5).value.strip().split('\n'):
                if flow_subflow == 'manual' or flow_subflow == 'N/A':
                    continue
                
                flow, subflow = flow_subflow.split('/', 1)
                if flow != libtype:
                    continue

                # this is redundant - 90% of the time flow = libtype
                # TODO: talk to DA and see if we can adhere to naming scheme
                if flow not in min_resources[libtype].keys():
                    min_resources[libtype][flow] = {}

                if subflow not in min_resources[libtype][flow].keys():
                    min_resources[libtype][flow][subflow] = []

                min_resources[libtype][flow][subflow].append(resource)

    return min_resources

def get_audit_status(
    min_resources, 
    ip_name, 
    rel_name, 
    checkers, 
    workspace_location,
    printer):

    
    for checker in checkers:

        # make a flow/subflow to compare to min/crit versions
        subflow = checker['ref'].subflow
        if not subflow:
            subflow = '-'
        flow = checker['ref'].flow

        # skip the entire process if there are no resources to check
        try:
            x = min_resources[checker['del_name']][flow][subflow]
        except KeyError: 
            continue


        files = AuditFile().get_audit_file_paths_for_testable_item(
            workspace_location, 
            ip_name, 
            checker['del_name'], 
            checker['cell_name'], 
            checker['ref'].flow, 
            checker['ref'].subflow
        )

        for f in files:
            if not f:
                continue
            elif f.endswith('.f'):
                checker['audits'] = read_audit_filelist(f)
                checker['audit_list'] = f
            else:
                checker['audits'] = [f,]
        
        deliverable = checker['del_name']            
        del_id = checker['del_id']
        cell_id = checker['cell_id']
        
        
        printer.store_checker(checker)
       
        if checker['not_por']:
            continue
        used_resources = []
        dummy = False

        for audit in checker['audits']:

            # if the audit file is invalid, only do the bare minimum
            root = 0
            try:
                root = ElementTree.parse(audit)
            except ElementTree.ParseError as err:
                continue

            # TODO: should there be different behavior for the catchall?
            except Exception as err:
                continue

            env = root.findall('environment')
            used_res = env[0].attrib['arc_resources']
            if used_res == 'No resources logged during testing.':
                continue

            used_resources.append(used_res)
            
        if dummy:
            continue

        # playing with the resources to increase memoized hits. Spawning
        # subprocesses is the bottleneck
        resolved_res = {}
        for resource in used_resources:
            res = resource.split(',')
            for r in res:
                if r.startswith('project'):
                    resolved_res.update(arc_resolve(r))
                else:
                    name, version = r.split('/', 1)
                    resolved_res[name] = '/'+version

        
        # go through the min resources to extract necessary flows/subflows
        for resource in min_resources[deliverable][flow][subflow]:

            name = resource['name']
        
            
            if name in resolved_res.keys():
                pass
            else:
                printer.store_resource(
                    checker,
                    name,
                    '-',
                    'Fatal', 
                    '-',
                    '-'
                )
                continue

            
            # calc status of used vs min versions and store in db
            used_version = resolved_res[name]
            crit_version = resource['minimum']
            min_version = resource['last_important']

            used_arc = arc_info(name+used_version)
            min_arc = arc_info(name+'/'+crit_version)
            li_arc = arc_info(name+'/'+min_version)
           
            
            # pass if the versions are the exact same or used > min
            status = 'Not Met'
            if int(used_arc) >= int(li_arc):
                status = 'Met'
            elif int(used_arc) >= int(min_arc):
                status = 'To Be Reviewed'
            
            printer.store_resource(
                checker,
                name,
                used_version, 
                status, 
                min_version,
                crit_version
            )    
      
    
# Helper tools from legacy min_version_checker.py
#
# Minor optimization 6/20: add just id to arc resource, prevent 
# unnecessary string manipulation
@memoized
def arc_info(resource):
    resource_info = {}
    cmd = 'arc resource {} id' .format(resource)
    res = None
    try: 
        res = subprocess.check_output(cmd, shell=True)
        res = res.strip()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(str(e))
        return -1
    
    return res

# TODO: possibly preprocess resources for caching, it 
#       might make the parser run a bit quicker
@memoized
def arc_resolve(resources):
    a = ArcUtils()
    b = a.get_resolved_list_from_resources(resources)
   
    return b
     
# another utility function pulled from the legacy system
def read_audit_filelist(filepath):
    """
    Reads in the audit "filelist".
    Assumes there is one file path per line.
    Lines that begin with a # are comments and ignored.
    Blank lines (or all spaces/tabs) are also ignored.
    File paths must be relative to the filelist location.
    """
    files = []
    filepath_dir = os.path.dirname(filepath)
    with open(filepath,'r') as filelist:
        for line in filelist.readlines():
            clean_line = line.strip(' \t\n')
            if not clean_line.startswith('#') and len(clean_line)>1:
                files.append(os.path.join(filepath_dir, clean_line))
    return files

if __name__ == '__main__':
    main()   
