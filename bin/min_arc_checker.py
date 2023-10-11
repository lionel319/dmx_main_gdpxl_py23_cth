#!/usr/bin/env python

import sys
import os
import xml.etree.ElementTree as ET
import xlrd
import collections
import re
import multiprocessing
from prettytable import PrettyTable
from collections import defaultdict
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.arcutils
from pprint import pprint
import argparse
import csv
import datetime
import json
import subprocess
import dmx.tnrlib.test_runner
import dmx.tnrlib.audit_check
from collections import defaultdict
from dmx.dmxlib.workspace import Workspace
from dmx.ecolib.ecosphere import EcoSphere
from altera.decorators import memoized
from joblib import Parallel, delayed

_MET = "Met"
_NOT_MET = "Not Met"
_NEED_ATTENTION = "To Be Reviewed"
_IGNORED = "Ignored"

_COLORS = {_MET: "Green", _NOT_MET: "Red", _NEED_ATTENTION: "Yellow", _IGNORED: "Green"}

ecosphere = EcoSphere()


#jtag_dict = []
jtag_common={}
pid = str(os.getpid())
projectName = ['Falcon_Mesa', 'Mercury', 'Pajaro_River', 'Patagon', 'hpsi10', 'i10socfm']
printedLibList = ['pnr','timemod','bcmrbc','cvrtl','fv','schmisc','rcxt','sta','rv','dftdsm','lint','cdc','ippwrmod','upf_rtl','syn','rtlcompchk','yx2gln','stamod','rdf','cvsignoff','fvpnr','upf_netlist','cvimpl','fvsyn']
checkedLibList = ['cdl','oasis','pnr','timemod','bcmrbc','cvrtl','fv','schmisc','rcxt','sta','rv','dftdsm','lint','cdc','ippwrmod','upf_rtl','syn','rtlcompchk','yx2gln','stamod','rdf','cvsignoff','fvpnr','upf_netlist','cvimpl','fvsyn']
libT = ['bcmrbc','bumps','cdc','cdl','circuitsim','complib','complibphys','complibphysfci','cvimpl','cvrtl','cvsignoff','dftdsm','dv','fcpwrmod','fctimemod','fv','fvpnr','fvsyn','gln_filelist','gp ilib','interrba','intfc','ipfloorplan','ippwrmod','ipspec','ipxact','laymisc','lint','netlist','oa','oa_sim','oasis','pintable','pnr','pv','r2g2','rcxt','rdf','reldoc','rtl','rtlcompchk','rv','rvfci','schmisc','sdf','sta','stamod','syn','timemod','toppnr','trackphys','upf_netlist','upf_rtl','upffc','yx2gln']
t = PrettyTable(['Variant', 'LibType', 'audit_Xml File', 'Resource', 'Minimum Version', 'Last Important Update Version', 'Used Version', 'Result' , 'Color'])
p = PrettyTable(['Variant', 'LibType', 'audit_Xml File', 'Resource', 'Minimum Version', 'Last Important Update Version', 'Used Version', 'Result' , 'Color'])
m = PrettyTable(['Variant', 'LibType', 'audit_Xml File', 'Resource', 'Minimum Version', 'Last Important Update Version', 'Used Version', 'Result' , 'Color'])
k = PrettyTable(['Resource', 'Release Notes'])
excelFile = '/nfs/site/disks/da_infra_1/reports/testaudit/Minimum_Resource.xlsx'



@memoized
def get_excel_sheet():
    workbook = xlrd.open_workbook(excelFile,"rb")
    sheets = workbook.sheet_names()
    for sheet_name in sheets:
        if sheet_name == 'Latest Arc Bundle':
            sh = workbook.sheet_by_name(sheet_name)
            return sh

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


### BEGIN
def set_resource_result(ip, topCell, deliverable, audit, true_flow, true_subflow, overall={}, total={}):
   
    ############################################################
    # Parse audit and get resources / flow / subflow information
    ############################################################
    resourceList, aud_subflow, aud_flow = parseAudit(audit, deliverable, ip.name, topCell)
    print("DEBUG 3")
    print(resourceList)

    if not resourceList and not aud_subflow:
       return (overall, total)

    if resourceList == 'dummy':
        if not(resourceList in overall.keys()):
                overall[resourceList] = {_MET: {'count': 0, 'minimum': '', 'last_important': '', 'used_version': ''}, _NOT_MET: {'count': 0, 'minimum': '', 'last_important': '', 'used_version': ''}, _NEED_ATTENTION: {'count': 0, 'minimum': '', 'last_important': '', 'used_version': ''}}
        if not(resourceList in total.keys()):
            total[resourceList] = {}

        status = _MET
        overall[resourceList][status]['count'] = overall[resourceList][_MET]['count'] + 1
        overall[resourceList][status]['minimum'] = '-'
        overall[resourceList][status]['last_important'] = '-'
        overall[resourceList][status]['used_version'] = '-'
        total[resourceList][os.path.basename(audit)] = jsonOutputSimple(deliverable, os.path.basename(audit), '-', '-', '-', '-', _MET, _COLORS[_MET], topCell, true_flow, true_subflow)
        return (overall, total)

#    elif resourceList == '':
#        overall[res][status]['count'] = overall[res][_NOT_MET]['count'] + 1
#        overall[res][status]['minimum'] = '-'
#        overall[res][status]['last_important'] = '-'
#        overall[res][status]['used_version'] = '-'
#        total[res][os.path.basename(audit)] = jsonOutputSimple(deliverable, os.path.basename(audit), '-', '-', '-', '-', _NOT_MET, _COLORS[_NOT_MET], topCell, true_flow, true_subflow)
#        return (overall, total)
    


    minimumList, criticalList, checkList = readExcel(deliverable, aud_subflow, aud_flow)
    
    if not minimumList and not criticalList:
        if 1 in checkList:
            print("-Warning - The subflow of this {} is not part of the check" .format(audit))
            print "         - LibType:",deliverable
            print "         - Subflow:", aud_subflow
            print "         - Audit file:",audit
    else:
        print("HERE {}" .format(resourceList))
        #################################################################
        # Parse excel resource definition and compare with audit resource
        #################################################################
        ret = parseExcel(minimumList, criticalList, deliverable, resourceList, audit, ip.name, topCell, aud_flow, aud_subflow)
        for res, values in ret.iteritems():
            if not(res in overall.keys()):
                overall[res] = {_MET: {'count': 0, 'minimum': '', 'last_important': '', 'used_version': ''}, _NOT_MET: {'count': 0, 'minimum': '', 'last_important': '', 'used_version': ''}, _NEED_ATTENTION: {'count': 0, 'minimum': '', 'last_important': '', 'used_version': ''}}

            if not(res in total.keys()):
                total[res] = {}

            resource = values[3]
            minimum = values[4]
            last_important = values[5]
            used_version = values[6]
            status = values[7]

            overall[res][status]['count'] = overall[res][status]['count'] + 1
            overall[res][status]['minimum'] = minimum
            overall[res][status]['last_important'] = last_important
            overall[res][status]['used_version'] = used_version

            total[res][os.path.basename(audit)] = jsonOutputSimple(deliverable, os.path.basename(audit), values[3], values[4], values[5], values[6], values[7], values[8], topCell, true_flow, true_subflow)

    return (overall, total)


### END

def get_status_resource_from_audit(deliverable, audits, cell, ip, json_result):
    print("Start processing min ARC version for cell {} deliverable {}" .format(cell.name, deliverable))
    for audit_file in audits:
        basename = os.path.basename(audit_file)
        
        if not(cell.name in basename):
            continue

        if audit_file.endswith('.xml'):
            extension = 'xml'
        elif audit_file.endswith('.f'):
            extension = 'f'

        d = ip.get_deliverable(deliverable)
        
        true_flow = ""
        true_subflow = ""

        for checker in d.get_checkers():

            pattern = "audit.{}.({})(_{}).{}" .format(cell.name, checker.flow, checker.subflow, extension)

            match = re.search(pattern, audit_file)
            if match:
                true_flow = checker.flow
                true_subflow = checker.subflow
                break


        if (true_flow == "") and (true_subflow == ""):
            for checker in d.get_checkers():
                if checker.subflow != "":
                    continue
                pattern2 = "audit.{}.({}).{}" .format(cell.name, checker.flow, extension)
                match2 = re.search(pattern2, audit_file)
                if match2:
                    true_flow = checker.flow
                    true_subflow = checker.subflow
                    break

        topCell = cell.name

        total = {}
        overall = {}

        if audit_file.endswith('.xml'):
            print("Processing XML {}" .format(audit_file))
            (overall, total) = set_resource_result(ip, topCell, deliverable, audit_file, true_flow, true_subflow, overall=overall, total=total)
            

        elif audit_file.endswith('.f'):
            print("Processing Filelist {}" .format(audit_file))
            audit_from_filelist = read_audit_filelist(audit_file)
            for audit in audit_from_filelist:
                (overall, total) = set_resource_result(ip, topCell, deliverable, audit, true_flow, true_subflow, overall=overall, total=total)


        for resource in total.keys():

            if not deliverable in json_result[cell.name].keys():
                json_result[cell.name][deliverable] = {}

            if not(basename in json_result[cell.name][deliverable].keys()):
                json_result[cell.name][deliverable][basename] = {}
                json_result[cell.name][deliverable][basename]['flow'] = true_flow
                json_result[cell.name][deliverable][basename]['subflow'] = true_subflow


            json_result[cell.name][deliverable][basename][resource] = {}

            if overall[resource][_NOT_MET]['count'] != 0:
                minimum = overall[resource][_NOT_MET]['minimum']
                last_important = overall[resource][_NOT_MET]['last_important']
                used_version = overall[resource][_NOT_MET]['used_version']
                status = _NOT_MET
            elif overall[resource][_NEED_ATTENTION]['count'] != 0:
                minimum = overall[resource][_NEED_ATTENTION]['minimum']
                last_important = overall[resource][_NEED_ATTENTION]['last_important']
                used_version = overall[resource][_NEED_ATTENTION]['used_version']
                status = _NEED_ATTENTION
            elif overall[resource][_MET]['count'] != 0:
                minimum = overall[resource][_MET]['minimum']
                last_important = overall[resource][_MET]['last_important']
                used_version = overall[resource][_MET]['used_version']
                status = _MET

            json_result[cell.name][deliverable][basename][resource]['minimum'] =    minimum
            json_result[cell.name][deliverable][basename][resource]['last_important'] = last_important
            json_result[cell.name][deliverable][basename][resource]['used'] = used_version
            json_result[cell.name][deliverable][basename][resource]['result'] = status
            json_result[cell.name][deliverable][basename][resource]['color'] = _COLORS[status]
            
            if audit_file.endswith('.f'):
                json_result[cell.name][deliverable][basename][resource]['audits'] = total[resource]
    print("End processing min ARC version for cell {} deliverable {}" .format(cell.name, deliverable))
    return 0

def easy_parallelize(auditList, cell, ip, json_result):
    print("Start processing min ARC version for cell {}" .format(cell.name))
    results = []
    njobs = (multiprocessing.cpu_count() * 2)
    results = Parallel(n_jobs=len(auditList.keys()), backend="threading")(delayed(get_status_resource_from_audit)(deliverable, auditList[deliverable], cell, ip, json_result) for deliverable, audits in auditList.iteritems())
    print("End processing min ARC version for cell {} {}" .format(cell.name, results))
    return results


#def easy_parallelize_cell(auditList, ip, json_result):
#    results = []
#    njobs = (multiprocessing.cpu_count() * 2)
#    results = Parallel(n_jobs=njobs, backend="threading")(delayed(easy_parallelize)(auditList, cell, ip, json_result) for cell in ip.get_cells())
#    results = Parallel(n_jobs=len(ip.get_cells()), backend="threading")(delayed(easy_parallelize)(auditList, cell, ip, json_result) for cell in [ip.get_cell('io_common_custom_ufi_18bits')])
    return results


def main():

    pwd = os.getcwd()
    jtag_dict = []

    ### Create workspace object and get topcells for the variant given as input
    workspace = Workspace()
    topcells = workspace.get_cells_for_ip(result.ip_name)

    ### Get IP object from ecosphere
    ip = ecosphere.get_family().get_ip(result.ip_name)

    ### Read the spreadsheet to load the ARC versions
    print("Begin reading spreadsheet")
    sh = get_excel_sheet()
    arc_shell = sh.cell(0,3).value
    for rownum in range(sh.nrows):
        if sh.cell(rownum,1).value == "Signoff Reviewed by Designer":
              k.hrules = 1
              resource = sh.cell(rownum,25).value
              release_notes =  sh.cell(rownum,7).value
              k.add_row([resource,release_notes])
    print("End reading spreadsheet")

    print "-I- Program started"

    json_result = {}
    
    #manager = Manager()
    #json_result = manager.dict()

    ### Get audit files
    auditList = {}
    currentPath = os.getcwd()
    notValidDeliverables = []
    
    for deliverable in ip.get_all_deliverables():
        if not(deliverable.name in checkedLibList):
            notValidDeliverables.append(deliverable.name)
            continue

        auditList[deliverable.name] = []

        for cell in ip.get_cells():
            if not cell.name in json_result.keys():
                json_result[cell.name] = {}

            for checker in deliverable.get_checkers(): 
                auditList[deliverable.name] = auditList[deliverable.name] + dmx.tnrlib.audit_check.AuditFile.get_audit_file_paths_for_testable_item(currentPath, ip.name, deliverable.name, cell.name, checker.flow, checker.subflow)
    ### End get audit files


    if notValidDeliverables != []:
        print "-Warning - LibType:",','.join(notValidDeliverables) + " is not part of the audit review check"
        print "         - The checks is only valid for the 24 libTypes as shown below:" 
        print printedLibList

    if auditList != {}:

        for cell in ip.get_cells():
            easy_parallelize(auditList, cell, ip, json_result)

    checkLibTypeList = auditList.keys()
    subflow_checker(checkLibTypeList)
    json.dump(json_result, jTag, indent=4 )



def subflow_checker(checkLibTypeList):
    #subflow_checker = {}
    res = {}
    subflowCheck = []
    subRes = []
    subcell = {}
    for lib_type in checkLibTypeList:    
        sh = get_excel_sheet()
        for rownum in range(sh.nrows):
            match = sh.cell(rownum,1)
            matchRes = str(match).replace('text:u','')
            if matchRes == "'Signoff Reviewed by Designer'":
               libType1 = sh.cell(rownum,26).value
               libType2 = sh.cell(rownum,27).value
               libType3 = sh.cell(rownum,28).value
               libType4 = sh.cell(rownum,29).value
               libType5 = sh.cell(rownum,30).value
               libType6 = sh.cell(rownum,31).value
               libType7 = sh.cell(rownum,32).value
               if lib_type == libType1 or lib_type == libType2 or lib_type == libType3 or lib_type == libType4 or lib_type == libType5 or lib_type == libType6 == lib_type == libType7: 
                  subflow = sh.cell(rownum,5).value
                  subFlowList =  str(subflow).split("\n")
                  if subFlowList != None:
                     for sflow in subFlowList:
                         sub = str(sflow).split("/")
                         flow = sub[-1]
                         lib_t = sub[0]
                         if lib_t == lib_type:
                            if flow != "-":
                               resource_name = sh.cell(rownum,25).value
                               res[resource_name + "/" + lib_t +"/"+flow] = lib_t,flow  
                               subflow_checker = {
                                            lib_t + "_" + flow:{
                                                              "flow" : lib_t,
                                                              "subflow" : flow,
                                                              "resource" : []
                                                                 }
                                                                }
                               subflowCheck.append(subflow_checker)
                            else:
                              resource_name = sh.cell(rownum,25).value
                              res[resource_name+"/"+lib_t] = lib_t,flow
                              subflow_checker = {
                                            lib_t:{
                                                              "flow" : lib_t,
                                                              "subflow" : flow,
                                                              "resource" : []
                                                                 }
                                                                }

                              subflowCheck.append(subflow_checker)
    listCheck = {}
    for sub in subflowCheck:
        for q,v in sub.iteritems():
            listCheck.setdefault(q,{}).update(v)
    for sub in listCheck:
         s_flow = listCheck[sub]["flow"]
         s_sub = listCheck[sub]["subflow"]
         for r in res:
            if res[r][0] == s_flow and res[r][1]==s_sub:
                  reso = str(r).split("/")
                  listCheck[sub]["resource"].append(reso[0])
    #print listCheck
    #for d in subflowCheck:
    #    for q,v in d.iteritems():
    #        subcell.setdefault(q, []).append(v)   
    #res = []
    #jRes = {}
    json.dump(listCheck, checkTag, indent=4 )
        
 

@memoized
def get_arc_resource(resource):
    print("MEMOIZED - Begin")
    resource_info = {}
    cmd = 'arc resource {}' .format(resource)
    res = subprocess.check_output(cmd, shell=True)
    res = res.strip()
    l = res.split('\n')
    for e in l:
        resource_info[e.split(':')[0].strip()] = e.split(':')[1].strip()
    print("MEMOIZED - End")
    print(resource_info)
    return resource_info


############## parseAudit ##############
# get <environment> from audit.xml
# return resources when found
########################################
def parseAudit(audit_file, userlibType, varX, topCell):

    try:

        root = ET.parse(audit_file)
        enviro = root.findall('environment')
        flow = root.findall('./flow')
        resources = enviro[0].attrib['arc_resources']
        
        ### Exception for RV
        if userlibType == "rv":
            result = root.findall("./results")
            rv_dummy =  result[0][0].attrib['text']
            if rv_dummy == "dummy_status" or rv_dummy == "Dummy Cruise Check As Workaround For Shared RV Libtype":
                aud_flow = flow[0].attrib['libtype']
                subFlow = flow[0].attrib['subflow']
                return ('dummy','','')
        
        if resources == 'No resources logged during testing.':
            return ('','','')
            
        
        xList = str(resources).split(',')
        for resource in xList:
            if resource.startswith('project'):
                try:
                    r = get_arc_resource(resource)
                    aud_flow = flow[0].attrib['libtype']
                    subFlow = flow[0].attrib['subflow']
                    return (resources, subFlow, aud_flow)
                except subprocess.CalledProcessError as e:
                    aud_flow = flow[0].attrib['libtype']
                    subFlow = flow[0].attrib['subflow']
                    print "-Error - Not valid resource:", resource
                    print "       - Audit File:",audit_file
                    return ('','','')
    
    except (ET.ParseError) as err :
        print("ET.ParseError error: {}" .format(err))
        return ('','','')
    except(IOError) as err:
        print("IOError error: {}" .format(err))
        return ('','','')
    except(IndexError) as err:
        print("IndexError error: {}" .format(err))
        return ('','','')
    except Exception as err:
        print("Exception error: {}" .format(err))
        return ('','','')  



def readExcel(userlibType,subFlow,aud_flow):
        chkList = []
        minimum_resource = []
        critical_resource = []
        sh = get_excel_sheet()

        for rownum in range(sh.nrows):
            match = sh.cell(rownum,1)
            matchRes = str(match).replace('text:u','')
            if matchRes == "'Signoff Reviewed by Designer'":
               libType1 = sh.cell(rownum,26).value
               libType2 = sh.cell(rownum,27).value
               libType3 = sh.cell(rownum,28).value
               libType4 = sh.cell(rownum,29).value
               libType5 = sh.cell(rownum,30).value
               libType6 = sh.cell(rownum,31).value
               libType7 = sh.cell(rownum,32).value
               if userlibType == libType1 or userlibType == libType2 or userlibType == libType3 or userlibType == libType4 or userlibType == libType5 or userlibType == libType6 or userlibType == libType7:
                  libChk = 1
                  chkList.append(libChk)
                  if subFlow != "":
                     subflow = sh.cell(rownum,5).value
                     subFlowList =  str(subflow).split("\n")
                     if subFlowList != None:
                        for sflow in subFlowList:
                            sub = str(sflow).split("/")
                            flow = sub[-1]
                            lib_t = sub[0]
                            if str(flow).replace('\n','') == subFlow and lib_t == aud_flow:
                               required_data = sh.cell(rownum,15).value
                               minimum_resource.append(required_data)
                               criticalCell = sh.cell(rownum,23).value
                               critical_resource.append(criticalCell)
                  else:
                       subflow = sh.cell(rownum,5).value
                       subFlowList =  str(subflow).split("\n")
                       if subFlowList != None:
                           for sflow in subFlowList:
                               sub = str(sflow).split("/")
                               flow = sub[-1]
                               lib_t = sub[0]
                               if str(flow).replace('\n','') == "-" and lib_t == aud_flow:
                                  required_data = sh.cell(rownum,15).value
                                  minimum_resource.append(required_data)
                                  criticalCell = sh.cell(rownum,23).value
                                  critical_resource.append(criticalCell)
               else:
                    libChk = 0
                    chkList.append(libChk)
        return(minimum_resource,critical_resource,chkList)


@memoized
def get_arc_resolved_resources(resources):
    a = dmx.utillib.arcutils.ArcUtils()
    return a.get_resolved_list_from_resources(resources)


def parseExcel(minimumList, criticalList, deliverable, resources, audit_file, ipName, topCell, flow, subflow):
    if resources== None:
        return

    resources_result = {}
    basename_auditfile = os.path.basename(audit_file)

    # resource can be a bundle project/falcon/branch/fm6dot2main/4.0/rtl/2019WW10
    # needs to split this bundle into individual resources to be able to match the resource defined in Excel
    # returns a dict:
    #   {
    #       'devacds_vars': 'nios2m/2015WW224', 
    #       'cadence_spectre-lic': 'license', 
    #       'synopsys_waveview': 'N-2017.12'
    #   }
    resources = get_arc_resolved_resources(resources)

    for resource, version in resources.iteritems():

        audit_resource = resource + version
        version = version.strip("/")
              
        for ele in minimumList:
            eleMatch = re.search("^([a-zA-Z0-9_]+)\/(\S+)$",str(ele).replace("\n",''))

            if eleMatch == None:
                continue
            
            excelResource = eleMatch.group(1)
            excelVersion = eleMatch.group(2).strip("/")

            if not(excelResource == resource):
                continue

            if result.overide_arc != None:
                filepath = result.overide_arc
                arcOveride = open(filepath,"r" )
                arc_overide_list = arcOveride.read().splitlines()
                arc_overide = resource + version

                if arc_overide in arc_overide_list:
                    resources_result[resource] = [ipName, deliverable, basename_auditfile, resource, "-", "-", version, _NOT_MET, _COLORS[_NOT_MET]]
                    continue
                    
            for cri in criticalList:
                cri_resource = str(cri).replace("'","")
                min_res =  excelResource + "/" + excelVersion
                criMatch = re.search("^([a-zA-Z0-9_]+)\/(\S+)$",str(cri).replace("'",''))

                if criMatch == None:
                    continue

                criMatched1 = criMatch.group(1)
                cri_g1 = criMatch.group(2)
                criMatched2 = cri_g1.strip("/")

                if criMatched1 != resource:
                    continue

                if version == criMatched2:
                    resources_result[resource] = [ipName, deliverable, basename_auditfile, criMatched1, excelVersion, criMatched2, version, _MET, _COLORS[_MET]] 
                else:
                    # get ARC resource id for critical resource defined in golden source
                    output = get_arc_resource(cri_resource)
                    criId = output["id"]
                    # get ARC resource id for resource defined in audit
                    output = get_arc_resource(audit_resource)
                    audId = output["id"]
                    # get ARC resource id for minimum resource defined in golden source
                    output = get_arc_resource(min_res)
                    minId = output["id"]

                    if int(audId) > int(criId):
                        resources_result[resource] = [ipName, deliverable, basename_auditfile, criMatched1, excelVersion, criMatched2, version, _MET, _COLORS[_MET]]
                    else:
                        if (version == excelVersion) or (int(audId) > int(minId)):
                            resources_result[resource] = [ipName, deliverable, basename_auditfile, criMatched1, excelVersion, criMatched2, version, _NEED_ATTENTION, _COLORS[_NEED_ATTENTION]]
                        else:
                            resources_result[resource] = [ipName, deliverable, basename_auditfile, criMatched1, excelVersion, criMatched2, version, _NOT_MET, _COLORS[_NOT_MET]]

    return resources_result


def jsonOutputSimple(lib, aud, criMatched1, matchedEle2, criMatched2, arc_ele2,result_json,color_json,topCell,aud_flow,aud_subflow):

    return {"flow" : aud_flow, "subflow" : aud_subflow, criMatched1: {"minimum" : matchedEle2, "last_important" : criMatched2, "used": arc_ele2, "result": result_json, "color": color_json}}

def jsonOutput(lib, aud, criMatched1, matchedEle2, criMatched2, arc_ele2,result_json,color_json,topCell,aud_flow,aud_subflow, total=None):
    if total != None:
        jtag_common = {
            topCell:{
                lib: {
                    aud: {
                        "flow" : aud_flow,
                        "subflow" : aud_subflow,
                        criMatched1: {
                            "minimum" : matchedEle2,
                            "last_important" : criMatched2,
                            "used": arc_ele2,
                            "result": result_json,
                            "color": color_json
                        },

                        "audits": total
                    }
                }
            }
        }

    else:
        jtag_common = {
            topCell:{
                lib: {
                    aud: {
                        "flow" : aud_flow,
                        "subflow" : aud_subflow,
                        criMatched1: {
                            "minimum" : matchedEle2,
                            "last_important" : criMatched2,
                            "used": arc_ele2,
                            "result": result_json,
                            "color": color_json
                        },
                        "audits": ""
                    }
                }
            }
        }

    return jtag_common
#    jtag_dict.append(jtag_common)
    #json.dump(jtag_common, jTag,sort_keys=False, indent=4 )
    
def is_writable_file(arg):
    try:
        checkTag  = open(arg, 'w')
    except IOError:
        checkTag = open('/tmp/' + arg, 'w')
    return checkTag


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Option to filter by workspace,variant and libType')
    parser.add_argument('-v', dest='ip_name', required=True, help='Specify the variant')
    parser.add_argument('-l', dest='lib_type', help='Specify the libType')
    parser.add_argument('-o', dest='overide_arc', help='Specify the full path to the arc override txt')
    parser.add_argument('-output', dest='output', default="minimum_resource_checkList.json", type=is_writable_file, help='Specify the full output file name')
    parser.add_argument('-checker', dest='checker', type=is_writable_file, default="checker_arc_requirements.json", help="Specify the checker file name")

    result = parser.parse_args()
    checkTag = result.checker
    jTag = result.output
    

    sys.exit(main())

