#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/workspace.py#4 $
$Change: 7486380 $
$DateTime: 2023/02/16 01:50:47 $
$Author: wplim $

Description: plugin for "quick newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''
from __future__ import print_function

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

from future import standard_library
standard_library.install_aliases()
from builtins import input
from builtins import str
from builtins import object
import os
import sys
import logging
import textwrap
import argparse
import io
import csv
import json
import dmx.utillib.stringifycmd

### curdir = /../dmx.abnrlib/quick_plugins/.
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, rootdir)
from dmx.utillib.utils import run_command, get_icmanage_path, list_of_dict_to_csv, user_is_psginfraadm, rephrase_messages_in_layman_terms
from dmx.utillib.dicttoxml import dicttoxml
from dmx.abnrlib.icm import ICManageCLI, ICManageError
import dmx.dmlib.ICManageWorkspace
from dmx.dmlib.dmError import dmError
import configparser
import dmx.tnrlib.test_runner
from dmx.tnrlib.tnr_dashboard import TNRDashboardForQuick
from datetime import datetime
from dmx.tnrlib.waivers import Waivers
from dmx.tnrlib.waiver_file import WaiverFile
from pprint import pprint
import dmx.ecolib.ecosphere
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.arcenv import ARCEnv
import dmx.utillib.version
import dmx.abnrlib.workspace
import dmx.abnrlib.flows.printconfig
from datetime import datetime
from collections import OrderedDict 
import xml.dom.minidom
import dmx.abnrlib.icm
import dmx.tnrlib.goldenarc_check
import dmx.utillib.gkutils
import dmx.tnrlib.test_result
import dmx.utillib.naa
import dmx.utillib.cache

LOGGER = logging.getLogger(__name__)

class WorkspaceError(Exception): 
    ''' Error class for Workspace '''
    pass

class Workspace(object):
    '''plugin for "quick newws"'''
        
    def __init__(self):
        ''' for pylint '''        
        pass

    @classmethod
    def info_action(cls):
        icm = ICManageCLI()
        try:
            icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace()
        except dmError as eobj:
            LOGGER.error("This command only works within an IC Manage Workspace.")
            LOGGER.debug(str(eobj))
            raise

        if icm.is_workspace_up_to_date(icmws.path):
            attr = 'up-to-date'
        else:
            attr = 'need update'

        msg = '\n'
        msg += "wsroot: {}\n".format(icmws.path)
        msg += "wsname: {}\n".format(icmws.workspaceName)
        msg += "project: {}\n".format(icmws.projectName)
        msg += "ip: {}\n".format(icmws.ipName)
        msg += "bom: {}\n".format(icmws.configurationName)
        msg += "Attrs: {}\n".format(attr)
        msg += "==============================\n"
        LOGGER.info(msg)
        dmx.abnrlib.flows.printconfig.PrintConfig(
            icmws.projectName, icmws.ipName, icmws.configurationName, 
            show_simple=True, nohier=False).run()

    @classmethod
    def sync_action(cls, cfgfile=None, yes_to_all=False, force=False, cache=False, preview=False, untar=False, untaronly=False):
        ws = None
        icm = ICManageCLI(preview=preview)
        try:
            ws = dmx.abnrlib.workspace.Workspace(preview=preview)
        except Exception as e:
            LOGGER.error("This command only works within an ICManage Workspace.")
            LOGGER.debug(str(e))
            raise

        # Section removed as it's no longer relevant
        '''
        ### Check if user has permission access
        retval = icm.workspace_access(icmws.workspaceName)
        if retval:
            msg  = "You do not have permission to access to {}/{}@{}.\n".format(icmws.projectName, icmws.ipName, icmws.configurationName)
            msg += "Please contact psgicmsupport@intel.com for help.\n"
            LOGGER.error(msg)
            LOGGER.debug("access denied reason - ({})".format(retval))
            raise
        '''

        family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
        if cfgfile:
            cfgfile = cfgfile
        else:
            cfgfile = os.path.join(ws._workspaceroot, 'quicksync.cfg')

        if os.path.isfile(cfgfile):
            errmsg, config = cls.read_sync_config_file(cfgfile)
        else:
            errmsg, config = cls.write_sync_config_file(cfgfile)

        if errmsg or not config:
            raise

        msg = 'Sync workspace for ...\n'
        for section in config.sections():
            msg += '[{}]\n'.format(section)
            if config.has_option(section, 'specs'):
                msg += "- specs: {}\n".format(config.get(section, 'specs'))
            else:
                for key in ['variants', 'libtypes']:
                    msg += "- {}: {}\n".format(key, config.get(section, key))
        LOGGER.info(msg)
        if yes_to_all:
            ans = 'y'
        else:
            ans = input("(y/n)?")

        if ans.lower() == 'y':
            try:
                if not untaronly:
                    ws.sync(skeleton=False, cfgfile=cfgfile, force=force, sync_cache=cache, verbose=True)
                    ### Always sync ipspec libtype for all variants (fogbugz 220876)
                    ws.sync(skeleton=False, variants=['*'], libtypes=['ipspec'], force=force, sync_cache=cache, verbose=True)
                
                if untar or untaronly:
                    ws.untar_files(cfgfile=cfgfile)

            except Exception as e:
                LOGGER.error(e)
                raise WorkspaceError("There were some problem syncing workspace {}".format(ws.name))
        else:
            LOGGER.info("Info: Workspace {} not sync'ed.".format(ws.name))
        
        LOGGER.info("Sync Completed.")

    @classmethod
    def read_sync_config_file(cls, cfgfile):
        '''
        Read quicksync configuration file and return the config object
        Validate and make sure all sections contain these key:-
        - variants & libtypes -or-
        - specs
        '''
        error = ''
        config = configparser.RawConfigParser()
        config.read(cfgfile)
        for section in config.sections():
            if 'specs' in config.options(section):
                continue
            if 'variants' not in config.options(section):
                error += 'variants: key not found in section [{}] in cfgfile {}\n'.format(section, cfgfile)
            if 'libtypes' not in config.options(section):
                error += 'libtypes: key not found in section [{}] in cfgfile {}'.format(section, cfgfile)
        if error:
            config = None
            LOGGER.error(error)
        return [error, config]

    @classmethod
    def write_sync_config_file(cls, cfgfile, variants=['*'], libtypes=['*']):
        '''
        Writes a new quicksync configuration file and return the config object
        '''
        config = configparser.RawConfigParser()
        section = '1'
        config.add_section(section)
        config.set(section, 'variants', ' '.join(variants))
        config.set(section, 'libtypes', ' '.join(libtypes))
        errmsg = ''
        try:
            with open(cfgfile, 'w') as fp:
                config.write(fp)
        except IOError as eobj:
            LOGGER.debug(str(eobj))
            errmsg = 'Unable to create cfgfile at {}'.format(cfgfile)
            LOGGER.error(errmsg)
        return [errmsg, config]

    @classmethod
    def get_dmx_binary_path(cls):
        '''
        return dmx binary as relative to file. Allow testing to be happen when running dmx workspace populate and dmx workspace delete
        '''
        exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'bin', 'dmx')
        exe = os.path.abspath(exe)

        return exe

    @classmethod
    def rerun_dmx_workspace_delete_as_psginfraadm_cmd(cls, workspacename=None):
        '''
        It will remove file, and default yes-to-all
        '''
        exe = cls.get_dmx_binary_path()
        workspacename = ' '.join(workspacename)
        basecmd = '{} workspace delete -w {} -y -r --debug ; '.format(exe, workspacename)

        washopts = 'default'
        arcopts = 'default'
        sshopts = 'default'
        envvar = {'DB_FAMILIES': ':env:', 'DMX_WORKSPACE': ':env:'}
        sc = dmx.utillib.stringifycmd.StringifyCmd(basecmd=basecmd, envvar=envvar, sshopts=sshopts, washopts=None, arcopts=arcopts)
        sc.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
        sc.arcexe = 'arc'

        final_cmd = sc.get_finalcmd_string()
        LOGGER.debug("stringifycmd: {}".format(final_cmd))
        return final_cmd


    @classmethod
    def delete_action(cls, rmfiles=False, yes_to_all=False, workspacename=None, older_than=False, preview=False):
        ''' 
        Description
        ===========
        Delete an existing IC Manage workspace.

        If -w/--workspacename is specified, will delete the workspace from IC Manage. 
        (files in the workspace path will NOT be deleted)
        If -w/--workspacename is NOT specified, and current directory is within an IC Manage
        workspace, then delete the current IC Manage workspace.
        If -r option is used, files and folders will be deleted altogether.
        If --older_than option is specified, will delete all of your workspace that have not been accessed 
        in the last specified days.
        If -y/--yes_to_all option is used, skip confirmation and force all (y/n) to y.
        

        Example
        =======
        ### Delete the current workspace (for this case, it is yltan.t20socanf.ar_lib.23)
        ### but don't delete the files/directories in it.
        %cd /icd_da/da/DA/yltan/yltan.t20socanf.ar_lib.23/ar_lib/oa
        %quick workspace delete

        ### Delete workspace yltan.t20socanf.ar_lib.23 and yltan.t20socanf.ar_lib.45 all it's files/directories.
        %quick workspace delete -w yltan.t20socanf.ar_lib.23 yltan.t20socanf.ar_lib.45 -r

        ### To delete all your workspaces that have not been accessed in 30 days, but don't delete the files:
        %quick workspace delete --older_than 30

        ### To delete all your workspaces that have not been accessed in 60 days, and all it's files:
        %quick workspace delete --older_than 60 --rmfiles

        .
        '''

        icm = ICManageCLI(preview=preview)
        wslist = []
        dmx_ws_name_list = []
        clientlist = [] 
        DMX_WORKSPACE = os.environ.get('DMX_WORKSPACE', '')

        if not workspacename and not older_than:
            # Non-ICM user only allowed to use with -w option
            if not icm.user_has_icm_license() and not user_is_psginfraadm():
                if rmfiles is not False and yes_to_all is not False and older_than is not False and preview is not False or not workspacename:
                    raise WorkspaceError('Non-ICM user only allowed to run with -w switch.')

            try:
                icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace()
                clientlist.append(icmws.workspaceName)
                dmx_ws_name_list = icmws.path
            except dmError as excobj:
                LOGGER.debug(excobj)
                LOGGER.error(textwrap.dedent("""You are not currently inside an IC Manage workspace, and the [-w|-o] option is not specified.
                    Either run this command within an IC Manage workspace,
                    or spicify a workspace name thru the [-w|-o] option."""))
                sys.exit(1) 

            wslist = [icmws.workspaceName]
            LOGGER.debug(wslist)


        elif workspacename:
            wslist = workspacename
            dmx_ws_list = []
            if not icm.user_has_icm_license() and not user_is_psginfraadm():
                for wsname in workspacename:
                    try:
                        icm.workspace_exists(wsname)
                    except ICManageError as excobj:
                        dmx_ws = DMX_WORKSPACE+'/'+wsname
                        if not os.path.exists(dmx_ws):
                            raise WorkspaceError('Cannot find {}'.format(dmx_ws))
                        dmx_ws_list.append(dmx_ws) 

                print("This will remove all folders and files. Are you sure you want to delete the client and workspaces?")
                print("{}".format('\n'.join(dmx_ws_list)))
                ans = input("(y/n)?")
                if ans.lower() == 'y':
                    LOGGER.debug('User {} does not have icm license. Rerun as psginfraadm'.format(os.environ.get('USER')))
                    final_cmd = cls.rerun_dmx_workspace_delete_as_psginfraadm_cmd(workspacename=workspacename)
                    return os.system(final_cmd)
                else:
                    LOGGER.info("No Workspace deleted.")
                    sys.exit(1) 




            ### checking for workspace existance.
            dmx_ws_name_list = []
            for wsname in wslist:
                
                try:
                    icm.workspace_exists(wsname)
                    clientlist.append(wsname)
                except ICManageError as excobj:
                    dmx_ws_name = DMX_WORKSPACE+'/'+wsname
                    dmx_ws_name_list.append(dmx_ws_name)
                    try:
                        icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(workspacePath=dmx_ws_name)
                        clientname = icmws.getWorkspaceAttribute("Workspace")
                        wsuser = icmws.getWorkspaceAttribute("User")
                        user =  os.environ.get('USER')
                        if wsuser != user and wsuser != 'psginfraadm':
                            raise WorkspaceError('User {} are not allowed to remove other user\'s workspace - {}'.format(user, clientname))
                        clientlist.append(clientname)
                    except dmError as excobj:
                        LOGGER.debug(excobj)
                        LOGGER.error(textwrap.dedent("""{} is not an IC Manage workspace.""".format(wsname)))
                        sys.exit(1) 

        elif older_than:
            
            ### older_than has to be a positive integer.
            try:
                older_than = int(older_than)
            except ValueError as eobj:
                LOGGER.debug(str(eobj))
                LOGGER.error("--older_than option must be an Integer.")
                sys.exit(1)
            if older_than < 0:
                LOGGER.error("--older_than option must be a POSITIVE integer.")
                sys.exit(1)

            try:
                wslist = icm.get_workspaces_for_user_by_age(os.environ['USER'], older_than=older_than)
            except ICManageError as excobj:
                LOGGER.debug(str(excobj))
                LOGGER.error("No Workspace found.")
                sys.exit(1)
            if not wslist:
                LOGGER.error("No Workspace which are inactive for more than {} days found.".format(older_than))
                sys.exit(1)

        wslist = clientlist

        if yes_to_all:
            ans = 'y'
        else:
            print("Are you sure you want to delete these workspaces?")
            print("{}".format("\n".join(wslist)))
            ans = input("(y/n)?")
        if ans.lower() == 'y':
            for wsname in wslist:
                if rmfiles:
                    LOGGER.info("Deleting workspace {} and its files ...".format(wsname))
                    flag = False
                else:
                    LOGGER.info("Deleting workspace {} only ...".format(wsname))
                    flag = True 
                
                if not icm.pending_changelists_exist(wsname):
                    if not icm.opened_files_exist(wsname):
                        try:
                            icm.del_workspace(wsname, preserve=flag)
                        except ICManageError as excobj:
                            LOGGER.debug(str(excobj))
                            sys.exit(1)
                    else:
                        LOGGER.error("There are opened files in the workspace, no workspace deleted")
                        LOGGER.error("Please submit the opened files: xlp4 submit")
                        LOGGER.error("Or revert the opened files: xlp4 revert")
                        sys.exit(1)
                else:
                    LOGGER.error("There are pending changelists in the workspace, no workspace deleted")
                    LOGGER.error("Please submit the changelists: xlp4 submit")
                    LOGGER.error("Or remove the changelists: xlp4 changelist -d")
                    sys.exit(1)
        
            # Need to run rm -rf again to remove the folder. Not sure why sometimes will have residue file remain
            # Need to debug later
            if dmx_ws_name_list and preview==False:
                cmd = 'rm -rf {}'.format(" ".join(dmx_ws_name_list))
                exitcode, stdout, stderr = run_command(cmd)
                LOGGER.debug(stdout)
                LOGGER.debug(stderr)

            LOGGER.info("Delete completed.")
        else:
            LOGGER.info("No Workspace deleted.")

    @classmethod
    def list_action(cls, user=None, older_than=0, tabulated=False, preview=False, format='human', project=None, ip=None, bom=None):
        ''' 
        Description
        ===========
        List all the workspaces which meet a given set of criteria.
        If --user/-u is not specified, your username will be used.
        If --older_than/-o is not specified, defaul:60 days

        Example
        =======
        ### List all workspace for user 'yltan' which has been inactive for 35 days
        %quick workspace list -u yltan -o 35
        '''
        icm = ICManageCLI(preview=preview)
        if older_than < 0:
            older_than = 0
    
        if project:
            workspaces = cls.get_workspaces(project=project, variant=ip, libtype=None, config=bom)
            list_of_workspaces = [d['workspace'] for d in workspaces if 'workspace' in d]
            workspaces = icm.get_workspaces_by_age(older_than, list_of_workspaces)
        elif ip or bom:
            raise WorkspaceError('You need to specify project/ip or project/ip@bom ') 
        else:
            # default dmx workspace list command result
            if not user:
                user = os.environ.get('USER')
            workspaces = icm.get_workspaces_for_user_by_age(user, older_than)

        # id user is specified, then check the user workspace. if not,use all workspace
        if user:
            user_workspaces = icm.get_workspaces_for_user_by_age(user, older_than)
            common_ws = [x for x in user_workspaces if x in workspaces]
            workspaces = common_ws

        if workspaces:
            LOGGER.info('Listing workspaces {}'.format('' if not older_than else 'which have been inactive for {} days'.format(older_than)))
            if tabulated:
                msg = cls.list_workspace_format(workspaces, format)
                LOGGER.info("\n{}".format(''.join(msg)))
            elif format == 'csv':
                result = cls.list_workspace_format(workspaces, format)
                for ea_line in result:
                    print(ea_line)
            elif format == 'json':
                result = cls.list_workspace_format(workspaces, format)
                print(result) 
            elif format == 'xml':
                result = cls.list_workspace_format(workspaces, format)
                print(result)
            else:
                for wsname in workspaces:
                    LOGGER.info('- {}'.format(wsname))
        else:
            #LOGGER.info('No workspaces found for {} which has been inactive for {} days.'.format(user, older_than))
            LOGGER.info('No workspaces found.')

    @classmethod
    def list_workspace_format(cls, workspaces, format):
        '''
        Given a list of workspace and return nicely formated result
        '''
        icm = ICManageCLI()
        tabform = '{:<4} {:<50} {:<25} {:<30} {:<40} {:<6} {}\n' 
        msg = ['']
 
        for i, wsname in enumerate(workspaces):
            #ret = ['project:parent:name', 'variant:parent:name', 'user', 'rootDir', 'name']
            ret = ['name', 'project:parent:name', 'variant:parent:name', 'config:parent:name', 'rootDir', 'created-by', 'abc']
            details = dmx.abnrlib.icm.ICManageCLI().get_workspace_details(wsname, ret)
            #print icm._get_objects('/workspace/{}'.format(wsname), retkeys=ret)[0]
            opened = icm.get_opened_files(wsname)
            project = details.get('project:parent:name')
            ip = details.get('variant:parent:name')   
            bom = details.get('config:parent:name') 
            ws_len = len(opened)
            path = details.get('rootDir')
            user = details.get('created-by')
            workspace_name = details.get('name')
            client_details = icm.get_client_detail(workspace_name)
            try:
                last_accessed = client_details.get('last_accessed')
            except AttributeError:
                #pm workpsace got but dont have accessdate
                #LOGGER.warning("Cannot found last_accessed date for \'{}\'".format(workspace_name))
                pass 

            today_date = datetime.today()            
            delta = today_date.date() - last_accessed
            inactive_days = delta.days

            if format == 'human':
                #if i == 0:
                msg[0] = tabform.format('CNT', 'WORKSPACE NAME', 'PROJECT', 'VARIANT', 'CONFIG', 'OPENED', 'WSDIR')
                tabform = '{:<4} {:<50} {:<25} {:<30} {:<40} {:<6} {}\n' 
                msg.append(tabform.format(i+1, wsname, project, ip, bom, len(opened), path))
            else: 
                if i == 0: msg.pop()
                ws_detail = icm.get_workspace_properties(workspace_name) 
                population_date = ws_detail.get('PopulationDate')
                population_time = ws_detail.get('PopulationTime')
                rows = OrderedDict()
                rows['PROJECT'] = project
                rows['IP'] = ip
                rows['BOM'] = bom
                rows['PATH'] = path
                rows['WORKSPACE_NAME'] = workspace_name
                rows['USER'] = user
                if population_date and population_time:
                    rows['POPULATION_DATEnTIME'] = '{} {}sec'.format(population_date, population_time)
                else:
                    rows['POPULATION_DATEnTIME'] = 'None' 
                rows['NUMBER_OF_DAYS_INACTIVE'] = inactive_days
                msg.append(rows)

                # If it is last element, nicely format the result to different format
                if wsname == workspaces[-1]:
                    if format == 'csv':
                        msg = list_of_dict_to_csv(msg)
                    elif format == 'json':
                        msg = json.dumps(msg, indent=4)
                    elif format == 'xml':
                        msg = dicttoxml(msg, attr_type=False)
                        dom = xml.dom.minidom.parseString(msg) # or xml.dom.minidom.parseString(xml_string)
                        msg = dom.toprettyxml()


        return msg
        


    @classmethod
    def create_action(cls, project, variant, config, directory='.', no_clientname=False, preview=False, yes=False):
        username = os.environ['USER']
        icm = ICManageCLI(preview=preview)

        # If project not given, get project from ARC
        if not project:
            LOGGER.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if icm.variant_exists(arc_project, variant):
                    project = arc_project
                    break
            if not project:
                raise WorkspaceError('Variant {0} is not found in projects: {1}'.format(variant, arc_projects))
        if not os.path.exists(directory) and not preview:
            if yes:
                ans = 'y'
            else:                
                LOGGER.warning('{} does not exist, create it?'.format(directory))
                ans = input("(y/n)?")
            if ans.lower() == 'y':
                os.mkdir(directory)
            else:
                raise WorkspaceError('{} does not exist'.format(directory))            
        dirname = os.path.realpath(os.path.abspath(directory))                

        icmws = False
        stdout = sys.stdout     ### This is to suppress the message printout from ICManageWorkspace()
        sys.stdout = io.StringIO()
       
        ### The logging.disable(logging.WARNING) is to shut off the following message from dm.ICManageWorkspace
        ### >>> logging.warning("WARNING: The path '/ice_da/da/nadder/kmartine' is not within an IC Manage workspace
        ###                    because there is no .icmconfig file in it or the directories above it.")
        ### The logging.disable(logging.NOTSET) is to reset the logging.disable() command so that everything goes back
        ### to the original state of settings.
        logging.disable(logging.WARNING)
        try:
            icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(workspacePath=dirname)
        except dmError as excobj:
            # PASS: This is not an icm managed workspace
            LOGGER.debug(excobj)
            LOGGER.debug(sys.stdout.getvalue())
        finally:
            sys.stdout = stdout
        logging.disable(logging.NOTSET)

        if icmws:
            LOGGER.error("You are currently inside workspace {}".format(icmws.workspaceName))
            LOGGER.error("Can not create new IC Manage workspace within an existing IC Manage workspace.")
            sys.exit(1)

        if not cls.is_workspace_path_allowed(project, variant, dirname):
            #LOGGER.error("{}/{} is not allowed to be created at {}. Please visit {} for the full list of allowable disk.".format(project, variant, dirname, 'http://rd/ice/product/Nadder/DA/Wiki/NadderDiskVolumes.aspx'))
            disks = cls.get_approved_disks(project)
            error_msg = "{0}/{1} is not allowed to be created at {2}. These are the approved disks for {0}:\n".format(project, variant, dirname)
            for disk in disks:
                error_msg = error_msg + '\t{}\n'.format(disk)
            error_msg = error_msg + 'Please contact da_icm_admin@intel.com if you need further help'                
            LOGGER.error(error_msg)
            sys.exit(1)

        if not icm.project_exists(project):
            LOGGER.error("Project {} does not exist".format(project))
            sys.exit(1)
        if not icm.variant_exists(project, variant):
            LOGGER.error("Variant {}/{} does not exist".format(project, variant))
            sys.exit(1)
        if not icm.config_exists(project, variant, config):
            LOGGER.error("Config {}/{}@{} does not exist".format(project, variant, config))
            sys.exit(1)
        if not os.path.isdir(dirname):
            LOGGER.error("Directory {} does not exist".format(dirname))
            sys.exit(1)
        if not os.access(dirname, os.W_OK):
            LOGGER.error("You do not have write access to directory {}".format(dirname))
            sys.exit(1)
        
        LOGGER.info("Creating {}/{}@{} workspace for user {} at {}".format(project, variant, config, username, dirname))
        try:
            workspacename = icm.add_workspace(project, variant, config, username, dirname, ignore_clientname=no_clientname)
            cls._workspacename = workspacename
        except ICManageError as eobj:
            LOGGER.debug(str(eobj))
            LOGGER.error("Failed to create a workspace for {}/{}@{}".format(project, variant, config))
            raise

        LOGGER.info("New Workspace Created. ({})".format(workspacename))
        LOGGER.info("Syncing folders (skeleton sync) for workspace {}".format(workspacename))

        try:
            # If in preview mode, workspace is not created, sync cannot be performed
            if not preview:
                icm.sync_workspace(workspacename, skeleton=True)
        except ICManageError as eobj:
            LOGGER.error("There was some problem when syncing workspace {}.".format(workspacename))
            raise

        LOGGER.info("Syncing completed.")

        return 0

    @classmethod
    def get_approved_disks(cls, project):
        '''
        Return a list of approved disks for a project
        '''
        p4port = os.getenv("P4PORT", '')
        if not p4port:
            LOGGER.error("Your current environment doesn't have P4PORT set. Please make sure that you are in the correct arc shell.")
            sys.exit(1)

        # We purposely fail the pre-sync check to get the list of approved disks
        # icm_pre_sync.py does not care what variant is
        variant = 'variant'
        # /tmp is definitely not an approved path      
        dirname = '/tmp'

        cmd = '{}/triggers/icmpm/icm_pre_sync.py dummy {} {} {} {}'.format(
            get_icmanage_path(), dirname, project, variant, p4port)
        (exitcode, stdout, stderr) = run_command(cmd)
        disks = stdout.splitlines()[-2].replace('[','').replace(']','').replace('\'','').split(',')
        disks = [x.strip() for x in disks]

        return sorted(disks)

    @classmethod
    def is_workspace_path_allowed(cls, project, variant, dirname):
        ''' 
        Check and make sure that the dirname path is an allowable path to create workspace 
        for the specific project/variant.
        '''
        p4port = os.getenv("P4PORT", '')
        if not p4port:
            LOGGER.error("Your current environment doesn't have P4PORT set. Please make sure that you are in the correct arc shell.")
            sys.exit(1)

        cmd = '{}/triggers/icmpm/icm_pre_sync.py dummy {} {} {} {}'.format(
            get_icmanage_path(), dirname, project, variant, p4port)
        (exitcode, stdout, stderr) = run_command(cmd)
        return not exitcode

    @classmethod
    def check_action(cls, project, variant, configuration, milestone, thread, libtype=None, logfile=None, dashboard=None, celllist_file=None, nowarnings=False, waiver_file=[], preview=False, views=None, validate_deliverable_existence_check=True, validate_type_check=True, validate_checksum_check=True, validate_result_check=True, validate_goldenarc_check=False, cfobj=None, familyobj=None, only_run_flow_subflow_list=None, source='proddb'):
        '''quick check command'''
        icm = ICManageCLI(preview=preview) 

        if cfobj:
            cls.icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace()     ### cls.icmws is needed in other places. Thus we need this statement.
            cls.cfobj = cfobj
        else:
            cls.cfobj = cls.get_config_factory_object()

        # http://pg-rdjira:8080/browse/DI-1356
        version = dmx.utillib.version.Version()
        LOGGER.info('Runnning workspace check with dmx/{} and dmxdata/{}'.format(version.dmx, version.dmxdata))

        '''
        # If project not given, get project from ARC
        if not project:
            LOGGER.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if icm.variant_exists(arc_project, variant):
                    project = arc_project
                    break
            if not project:
                raise WorkspaceError('Variant {0} is not found in projects: {1}'.format(variant, arc_projects))
        '''
        ### We should not look for the project from arc environment
        ### Project should be extracted from workspace 
        ### https://jira01.devtools.intel.com/browse/PSGDMX-1506
        if not project:
            LOGGER.info("Looking for project from workspace config ...")
            retlist = cls.cfobj.search(variant='^{}$'.format(variant))
            if not retlist:
                raise WorkspaceError("Variant {} not found in workspace.".format(variant))
            project = retlist[0].project
            LOGGER.debug("Variant:{} Project:{} found.".format(variant, project))


        # If milestone not given, get milestone from ARC
        if not milestone:
            milestone = ARCEnv().get_milestone()
        # If thread not given, get thread from ARC
        if not thread:
            thread = ARCEnv().get_thread()
        LOGGER.info('Checking workspace with milestone {} and thread {}'.format(milestone, thread))                
        # http://pg-rdjira:8080/browse/DI-1169
        # If configuration is given, prints warning and ignore
        if configuration:
            LOGGER.warning('"--bom {}" will be ignored, using BOM from workspace instead'.format(configuration))

        ### writes all output to a logfile if --logfile is specified.
        if cls.set_personal_logfile(logfile):
            return 1

        ### Check if this is an IC Manage Workspace, and register all user supplied options to class variables.
        cls.get_request_details(project, variant, configuration, milestone, thread, libtype, waiver_file, celllist_file, preview)
        cls.views = views

        ### Validate request
        cls.familyobj = familyobj
        if cls.validate_request():
            return 1

        ### Start running the checks.
        log_audit = False
        if dashboard:
            log_audit = True
        cls.testrunner = dmx.tnrlib.test_runner.TestRunner(cls.project, cls.variant, cls.libtype, cls.config, cls.wsroot, cls.milestone, cls.thread, cls.webapi, splunk_app_name='periodic', log_audit_validation_to_splunk=log_audit, views=cls.views, validate_deliverable_existence_check=validate_deliverable_existence_check, validate_type_check=validate_type_check, validate_checksum_check=validate_checksum_check, validate_result_check=validate_result_check, validate_goldenarc_check=False, familyobj=familyobj, only_run_flow_subflow_list=only_run_flow_subflow_list, prel=cls.prel)
        errors = cls.testrunner.run_tests()
       
        LOGGER.info("validate_goldenarc_check: {}".format(validate_goldenarc_check)) 
        if validate_goldenarc_check:
            prod = False
            if source == 'proddb':
                prod = True
            gc = dmx.tnrlib.goldenarc_check.GoldenArcCheck(cls.project, cls.variant, cls.libtype, cls.config, cls.wsroot, cls.milestone, cls.thread, cls.views, cls.prel, prod=prod)
            gc._cfobj = cls.cfobj   # So that gc don't need to recreate the config_factory object.
            gc.run_test()
            LOGGER.info("gc result:{}".format(gc.result))
            gcerrors = gc.report(printout=False)
            errors += gcerrors

        skip_turnin = os.environ.get("DMX_SKIP_TURNIN", False)
        if not skip_turnin and cls.libtype and cls.libtype == 'cthfe':
            gk = dmx.utillib.gkutils.GkUtils()
            retcode, retmsg = gk.run_turnin_from_icm_workspace(cls.wsroot, cls.project, cls.variant, cls.libtype, cls.thread, cls.milestone, mock=True)
            if retcode:
                retmsg += ' (UNWAIVABLE)'
                result = dmx.tnrlib.test_result.TestFailure(cls.variant, cls.libtype, 'NA', 'turnin', '', retmsg)
                errors += [result]


        ### initializing 
        cls.exit_code = 0
        cls.errors = {'waived':[], 'unwaived':[]}
        cls.report_message = ''

        ### error reporting
        cls.report_errors(errors)

        ### Generate tnrerror.csv
        cls.create_tnrerror_csv(cls.errors['unwaived'])

        ### report loaded waiver files
        cls.report_loaded_waiver_files()

        ### report loaded dmx hsdes waiver case
        cls.report_loaded_dmx_waiver_hsdcase()



        ### Log Test Results to Splunk
        if dashboard:
            LOGGER.info("Logging test errors to dashboard ...")
            cls.log_test_results_to_splunk(errors, dashboard)


        ### Report all the required files that are out-of-sync with the depot
        if not nowarnings:
            cls.report_required_tests_owners(errors)
            cls.report_required_files_that_are_out_of_sync()
            cls.report_opened_files()

        return cls.exit_code

    @classmethod
    def report_loaded_dmx_waiver_hsdcase(cls):
        ''' report out all the automatically loaded hsd waiver files '''
        if cls.loaded_hsdcase:
            msg = "Loaded hsd waiver case:-\n"
        else:
            msg = 'No hsd waiver cases loaded.\n'
        for f in cls.loaded_hsdcase:
            msg += "- {0} : https://hsdes.intel.com/appstore/article/#/{0} \n".format(f)
        LOGGER.info(msg)
        return msg


    @classmethod
    def report_loaded_waiver_files(cls):
        ''' report out all the automatically loaded waiver files '''
        if cls.loaded_waiver_files:
            msg = "Loaded waiver files:-\n"
        else:
            msg = 'No waiver files loaded.\n'
        for f in cls.loaded_waiver_files:
            msg += "- {}\n".format(f)
        LOGGER.info(msg)
        return msg


    @classmethod
    def report_required_tests_owners(cls, errors):
        ''' List out all owners for the the flow/subflow that has errors. '''

        ### create a lookup table that stores all the flow/subflow that has errors. 
        ### The table is a dictionary that looks like data[flow][subflow] = ''
        data = {}
        for err in errors:
            if err.flow not in data:
                data[err.flow] = {}
            data[err.flow][err.subflow] = ''
        
        msg = "Here are the list of flows with their respective owners:-\n"
        errcount = 0
        for (libtype, flow, subflow, checktype, checkname, ownername, owneremail, ownerphone) in cls.required_tests:
            if flow in data and subflow in data[flow]:
                msg += '- {} {}: {}\n'.format(flow, subflow, ownername)
                errcount += 1

        if errcount:
            LOGGER.info(msg)

        return msg


    @classmethod
    def report_opened_files(cls):
        ''' report all the opened files (output from 'xlp4 opened')
        '''
        exitcode, stdout, stderr = run_command('_xlp4 opened')

        ### Reporting
        if stdout:
            txt = 'These files are found opened and not checked-in in this workspace:-\n'
        else:
            txt = 'There are no opened files found in this workspace.\n'
        #LOGGER.info(txt + stdout)



    @classmethod
    def report_required_files_that_are_out_of_sync(cls):
        ''' Definition of 'required files' for a given project/variant:(libtype):-
        - all the required audit logs
        - all the referenced audit files in the audit filelists
        - required files referenced by all those audit logs

        
        for all the 'required files':
            if file is 'xlp4 opened':
                warn("file is opened ...")
            elif file is 'xlp4 reconcile':
                warn("file needs to be added|deleted|edited ...")
        '''
        ### cls.testrunner.get_required_audit_logs() return all the required audit log files with
        ### workspaceroot removed, leaving behind /variant/libtype/audit/audit.topcell.flow_subflow.xml
        ### we need to remove the leading '/' in order for 'xlp4 reconcile/opened' to recognise it as
        ### a relative path file. (Yeah I know, this looks like a monkey patch. Will look into this to make
        ### the change in test_runner.py when time permits, which is already in Fogbugz 336457)
        required_audit_logs = cls.testrunner.get_required_audit_logs(include_all_files=True)
        LOGGER.debug("required_audit_logs(original):{}".format(required_audit_logs))
        
        #-- monkey pathching starts here ..... 
        #-- first, remove all the one-character elements
        required_audit_logs = [f for f in required_audit_logs if len(f) > 1]
        #-- next, remove the leading '/' if it has only 4 '/' in the path 
        #--   /variant/libtype/audit/audit.xml is wrong! it should be ...
        #--    variant/libtype/audit/audit.xml (without the leading '/')
        required_audit_logs = [f.lstrip('/') if f.count('/') < 5 else f for f in required_audit_logs]
        LOGGER.debug("required_audit_logs:{}".format(required_audit_logs))


        required_files_from_required_audits = cls.testrunner.get_required_files_from_required_audits(include_all_files=True)
        LOGGER.debug("required_files_from_required_audits:{}".format(required_files_from_required_audits))
        required_files = set(required_audit_logs + required_files_from_required_audits)

        ### We need to cd to workspace root before running all the is_file_opened() and
        ### is_file_out_of_sync() checks because all the returned required_files are in 
        ### relative path from the workspace root.
        currdir = os.getcwd()
        os.chdir(cls.wsroot)
        naa = dmx.utillib.naa.NAA()
        cache = dmx.utillib.cache.Cache()

        retlist = {'opened': [], 'reconcile': []}
        for filename in required_files:
            ret = cls.is_file_opened(filename)
            if ret:
                retlist['opened'].append(ret)
            else:
                ret = cls.is_file_out_of_sync(filename)
                if ret:
                    fullpath = os.path.realpath(filename)
                    if not naa.is_path_naa_path(fullpath) and not cache.is_path_cache_path(fullpath):
                        retlist['reconcile'].append(ret)

        if retlist['opened'] or retlist['reconcile']:
            LOGGER.info('Current state of this workspace does not match repository. Please review the following errors before running release.\n')

        ### Reporting 
        if retlist['opened']:
            txt = ''
            for msg in retlist['opened']:
                txt += '- ' + msg + "\n"
            if txt:
                txt = "The following required files were found opened, but not submitted. You might want to submit these opened files before running the release command.\n" + txt
                LOGGER.warning(txt)

        if retlist['reconcile']:
            txt = ''
            for msg in retlist['reconcile']:
                if 'opened for delete' not in msg:
                    txt += '- ' + msg + "\n"
            if txt:
                txt = "The following required files were found different (out-of-sync) from the files in the depot. The suggested action is printed after the file.\n" + txt
                LOGGER.warning(txt)

        #if retlist['opened'] or retlist['reconcile']:
        if True:
            errmsg = ''
            errmsg += textwrap.dedent("""
            ==============================================
            ============= STATE OF WORKSPACE =============
            ==============================================
            FILES OPENED AND NOT SUBMITTED      : {}
            FILES OUT OF SYNC                   : {}
            ==============================================
            TOTAL ERRORS FOUND                  : {}
            ==============================================
            """.format(len(retlist['opened']), len(retlist['reconcile']), len(retlist['opened'])+len(retlist['reconcile'])))
            LOGGER.info(errmsg)
                

        os.chdir(currdir)
        return retlist


    @classmethod
    def is_file_out_of_sync(cls, filename):
        ''' check if the file is out-of-sync with the depot version.
        - return the output string (of 'xlp4 reconcile') if it is out-of-sync
        - else return an empty string

        Running 'xlp4 reconcile -n -l' on a file which is NOT out-of-sync produces:-
        >>> EXIT:0
        >>> OUT :
        >>> ERR :/ice_da/da2/nadder/yltan/yltan.LionelLabProject.v004_asic.217/v004_asic/ipspec/test_reconcile/in_sync - no file(s) to reconcile.

        Running 'xlp4 reconcile -n -l' on a file which is out-of-sync produces:-
        >>> EXIT:0
        >>> OUT :/ice_da/da2/nadder/yltan/yltan.LionelLabProject.v004_asic.217/v004_asic/ipspec/test_reconcile/deleted_from_ws#1 - opened for delete
        >>> ERR :
                    -or-
        >>> EXIT:0
        >>> OUT :/ice_da/da2/nadder/yltan/yltan.LionelLabProject.v004_asic.217/v004_asic/ipspec/test_reconcile/not_in_depot#1 - opened for add
        >>> ERR :
                    -or-
        >>> EXIT:0
        >>> OUT :/ice_da/da2/nadder/yltan/yltan.LionelLabProject.v004_asic.217/v004_asic/ipspec/test_reconcile/diff_from_depot#1 - opened for edit
        >>> ERR :
        '''
        cmd = '_xlp4 reconcile -n -l {}'.format(filename)
        LOGGER.debug(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        LOGGER.debug("STDOUT:{}".format(stdout))
        LOGGER.debug("STDERR:{}".format(stderr))
        msg = 'no file(s) to reconcile'
        if msg in stderr or msg in stdout:
            return ''
        else:
            return stdout.strip()


    @classmethod
    def is_file_opened(cls, filename):
        ''' check if the file is 'xlp4 opened'.
        - return the output string (of 'xlp4 opened') if it is opened
        - else return an empty string

        Running 'xlp4 opened' on a file which is NOT-opened/does-not-exist produces:-
        >>> EXIT:0
        >>> STDOUT :
        >>> STDERR :/ice_da/da2/nadder/yltan/yltan.LionelLabProject.v004_asic.217/v004_asic/ipspec/test_reconcile/aaa - file(s) not opened on this client.

        Running 'xlp4 opened' on a file which is opened produces:-
        >>> EXIT:0
        >>> STDOUT ://depot/icm/proj/LionelLabProject/v004_asic/ipspec/dev/test_reconcile/opened_file#1 - edit default change (text+l) *exclusive*
        >>> STDERR :
        '''
        cmd = '_xlp4 opened {}'.format(filename)
        LOGGER.debug(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        LOGGER.debug("STDOUT:{}".format(stdout))
        LOGGER.debug("STDERR:{}".format(stderr))
        msg = 'not opened'
        if msg in stderr or msg in stdout:
            return ''
        else:
            return stdout.strip()


    @classmethod
    def log_test_results_to_splunk(cls, errors, mode):
        ''' '''
        devmode = True
        if mode == 'prod':
            devmode = False

        db = TNRDashboardForQuick('periodic', cls.icmws.workspaceName, cls.milestone, cls.thread, cls.project, cls.variant, cls.libtype, 
            cls.config, os.getenv("USER", ''), str(datetime.now()), development_mode=devmode)
        #for res in errors:
        for res in cls.testrunner.get_test_results():
            db.write_test_result(res)

    @classmethod
    def set_personal_logfile(cls, logfile):
        '''
        writes all output to a logfile if --logfile is specified.
        return 0 if no error, else return 1
        '''
        if logfile:
            ### Check if the directory is writable
            if not os.access(os.path.dirname(os.path.abspath(logfile)), os.W_OK):
                LOGGER.error("You have no permission to write to -logfile {}.".format(logfile))
                return 1

            mylog = logging.FileHandler(logfile, mode='w')
            mylog.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            LOGGER.addHandler(mylog)
        return 0



    @classmethod
    def get_config_factory_object(cls):
        if not hasattr(cls, 'cfobj') or not cls.cfobj:
            try:
                cls.icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace() 
            except dmError as eobj:
                LOGGER.error("This command only works within an IC Manage Workspace.")
                LOGGER.debug(str(eobj))
                rephrase_messages_in_layman_terms(stdout=str(eobj), stderr='')
                sys.exit(1)
            cls.cfobj = ConfigFactory.create_from_icm(cls.icmws.projectName, cls.icmws.ipName, cls.icmws.configurationName)
            LOGGER.debug('Creating ConfigFactory({}, {}, {})'.format(cls.icmws.projectName, cls.icmws.ipName, cls.icmws.configurationName))
        else:
            LOGGER.debug('Reusing ConfigFactory Object({}, {}, {})'.format(cls.cfobj.project, cls.cfobj.variant, cls.cfobj.config))
        return cls.cfobj


    @classmethod
    def get_request_details(cls, project, variant, configuration, milestone, thread, libtype, waiver_file, celllist_file, preview):
        '''
        Check if this is an IC Manage Workspace.
        '''

        cls.cfobj = cls.get_config_factory_object()
        
        cls.icmcli = ICManageCLI(preview=preview) 
        cls.project = project
        cls.variant = variant   

        ### This should be the config of the variant, instead of the config of the workspace
        #cf = ConfigFactory.create_from_icm(cls.icmws.projectName, cls.icmws.ipName, cls.icmws.configurationName)
        #results = cf.search(project=cls.project, variant='^{}$'.format(cls.variant), libtype=None)
        results = cls.cfobj.search(project='.*', variant='^{}$'.format(cls.variant), libtype=None)
        cls.config = results[0].config
        #cls.config = cls.icmws.configurationName

        cls.wsroot = cls.icmws.path
        cls.milestone = milestone
        cls.thread = thread
        cls.webapi = None
        if libtype:
            if libtype.startswith("prel_"):
                if ':' in libtype:
                    cls.prel, cls.libtype = libtype.split(":")
                else:
                    cls.libtype = None
                    cls.prel = libtype
            else:
                cls.libtype = libtype
                cls.prel = None
        else:
            cls.prel = None
            cls.libtype = libtype

        cls.waiver_files = waiver_file
        #cls.waivers = Waivers('Nadder', '', '2014-11-11', None, milestone, args.thread)
        cls.waivers = Waivers()
        cls.celllist_file = celllist_file

    @classmethod
    def validate_request(cls):
        '''
        Validate to make sure the options supplied are valid.
        return the error message if fail, '' if pass.
        We could have just returned 0/1. Returning the errmsg 
        instead ease in writing test codes.
        '''
        ### check if project exists
        if not cls.icmcli.project_exists(cls.project):
            errmsg = "{} is not a valid project".format(cls.project) 
            LOGGER.error(errmsg)
            return errmsg

        ### check if variant exists
        if not cls.icmcli.variant_exists(cls.project, cls.variant):
            errmsg = "{} is not a valid variant for project {}".format(cls.variant, cls.project)
            LOGGER.error(errmsg)
            return errmsg
            
        ### check if libtype exists
        if cls.libtype and not cls.icmcli.libtype_exists(cls.project, cls.variant, cls.libtype):
            errmsg = "{} is not a valid libtype for {}/{}".format(cls.libtype, cls.project, cls.variant)
            LOGGER.error(errmsg)
            return errmsg
        
        ### check if config exists
        if cls.libtype:
            # http://pg-rdjira:8080/browse/DI-758
            # libtype config has to be queried from variant config
            '''
            variant_config = ConfigFactory.create_from_icm(cls.project, cls.variant, cls.config)
            results = variant_config.search(project=cls.project, 
                                            variant='^{}$'.format(cls.variant),
                                            libtype='^{}$'.format(cls.libtype))
            '''
            results = cls.cfobj.search(project=cls.project, 
                                            variant='^{}$'.format(cls.variant),
                                            libtype='^{}$'.format(cls.libtype))
            if not results:
                errmsg = "{}'s BOM is not present {}/{}@{} BOM".format(cls.libtype, cls.project, cls.variant, cls.config)
                LOGGER.error(errmsg)
                return errmsg

            #libtype_config = results[0].config
            libtype_config = results[0].name
            if not cls.icmcli.config_exists(cls.project, cls.variant, libtype_config, cls.libtype):
                errmsg = "{} is not a valid configuration for {}/{}'s libtype {}".format(libtype_config, cls.project, cls.variant, cls.libtype)
                LOGGER.error(errmsg)
                return errmsg
            # Override cls.config to pass back to TestRunner class
            cls.config = libtype_config
        else:
            if not cls.icmcli.config_exists(cls.project, cls.variant, cls.config):
                errmsg = "{} is not a valid configuration for {}/{}".format(cls.config, cls.project, cls.variant)
                LOGGER.error(errmsg)
                return errmsg

        ### check if the project/variant has a variant_type
        variant_type = cls.get_variant_type()
        if not variant_type:
            errmsg = "Project/Variant for ({}/{}) doesn't have a variant_type. Please make sure you specified the correct project/variant.".format(cls.project, cls.variant)
            LOGGER.error(errmsg)
            return errmsg

        '''
        ### Check if the user supplied milestone/thread is a valid one.
        if not cls.is_milestone_thread_valid():
            errmsg = """Supplied milestone/thread ({}/{}) does not match with currently available roadmap. Please refer to http://goto/psg_roadmap for a list of available milestone/thread.""".format(cls.milestone, cls.thread)
            LOGGER.error(errmsg)
            cls.show_available_milestone_thread()
            return errmsg
        '''

        ### if waiver_files is given, check if files exist
        '''
        if cls.waiver_files:
            errmsg = ''
            for filename in cls.waiver_files:
                if not os.path.isfile(filename):
                    errmsg += "Couldn't find WaiverFile {}\n".format(filename)
                elif not os.access(filename, os.R_OK):
                    errmsg += "Don't have read permission on WaiverFile {}\n".format(filename)
            if errmsg:
                LOGGER.error(errmsg)
                return errmsg

            ### If no errors found, add all waiver_files to Waiver instance
            for filename in cls.waiver_files:
                wf = WaiverFile()
                wf.load_from_file(filename)
                cls.waivers.add_waiver_file(wf)
        '''
        wf = WaiverFile()
        wf.autoload_tnr_waivers(cls.wsroot, cls.variant, cls.libtype)
        wf.autoload_hsdes_waivers(cls.thread, cls.variant, cls.milestone)
        cls.loaded_hsdcase = wf.all_hsdescase
        cls.waivers.add_waiver_file(wf)
        cls.loaded_waiver_files = list(set([x.filepath for x in wf.waivers]))
        

        ### Set cls attr for variant_type and required_tests
        cls.variant_type = variant_type
        #cls.required_tests = cls.webapi.get_required_tests(cls.project, cls.milestone, cls.thread, cls.variant_type)
        cls.testrunner = dmx.tnrlib.test_runner.TestRunner(cls.project, cls.variant, cls.libtype, cls.config, cls.wsroot, cls.milestone, cls.thread, cls.webapi, splunk_app_name='periodic', log_audit_validation_to_splunk=False, views=cls.views, familyobj=cls.familyobj)
        cls.required_tests = cls.testrunner.get_required_tests(cls.project, cls.milestone, cls.thread, cls.variant_type)


        ### If celllist_file is given, check if file exist,
        ### and parse all celllist into cls.celllist
        if cls.celllist_file:
            errmsg = ''
            if not os.path.isfile(cls.celllist_file):
                errmsg += "Couldn't find Celllist File {}\n".format(cls.celllist_file)
            elif not os.access(cls.celllist_file, os.R_OK):
                errmsg += "Don't have read permission on Celllist File {}\n".format(cls.celllist_file)
            if errmsg:
                LOGGER.error(errmsg)
                return errmsg
            cls.celllist = cls.parse_celllist_file()
        else:
            cls.celllist = []

        return ''

    @classmethod
    def parse_celllist_file(cls):
        '''
        Parse the celllist file, and return all the cell list in it.
        The celllist file contains one cellname per line.

        return = ['cell1', 'cell2', 'cell4', ...]
        '''
        retlist = []
        f = open(cls.celllist_file, 'r')
        for line in f:
            sline = line.strip()
            if sline and not sline.startswith("#") and not sline.isspace():
                retlist.append(sline)
        f.close()
        return retlist


    @classmethod
    def report_errors(cls, errors):
        '''
        Reports the TestFailure objects sorted by
        - flow, subflow, variant, libtype, topcell, error
        TestFailure object == TestFailure(variant=u'an', libtype='lint', topcell='', flow='deliverable', subflow='type', error='VP/templateset not yet available')
        '''
        
        sum = {'failed':0, 'hsdeswaived':0, 'cmdwaived':0, 'webwaived':0, 'total':0}

        errmsg = ''
        waivemsg = ''
        if errors:
            errors = sorted(errors, key=lambda e: (e.flow, e.subflow, e.variant, e.libtype, e.topcell, e.error))
            
            if cls.libtype:
                errmsg = "dmx workspace check(library-level) for {}/{}@{} ({}) completed with errors found!\n".format(cls.project, cls.variant, cls.config, cls.libtype)
            else:
                errmsg = "dmx workspace check(variant-level) for {}/{}@{} completed with errors found!\n".format(cls.project, cls.variant, cls.config)
            for num, err in enumerate(errors):
            
                # Only report as error if the topcell are in the given celllist file
                if cls.celllist and err.topcell not in cls.celllist:
                    continue

                if err.error:
                    checkname = cls.get_checker_name(err)
                    matched_waiver = cls.waivers.find_matching_waiver(err.variant, err.flow, err.subflow, err.error)
                    matched_hsdes_waiver = cls.waivers.find_matching_hsdes_waiver(err.variant, err.flow, err.subflow, err.error)

                    if not matched_waiver and not matched_hsdes_waiver:
                        sum['failed'] += 1
                        sum['total'] += 1
                        if err.topcell:
                            errmsg += "  {}: {} {} for {}: {}\n".format(sum['failed'], err.flow, err.subflow, err.topcell, err.error)
                        else:
                            errmsg += "  {}: {} {}: {}\n".format(sum['failed'], err.flow, err.subflow, err.error)
                        
                        if 'Could not find any audit files' in err.error:
                            errmsg += "     - Please run {} to generate the missing audit file(s).\n".format(checkname)
                        cls.errors['unwaived'].append(err)

                    elif matched_waiver:
                        if 'CommandLine' in matched_waiver:
                            sum['cmdwaived'] += 1
                            sum['total'] += 1
                        else:
                            sum['webwaived'] += 1
                            sum['total'] += 1
                        waivemsg += "  {}: {} {}: {}\n".format(sum['cmdwaived']+sum['webwaived'], err.flow, err.subflow, err.error)

                        cls.errors['waived'].append(err)

                    elif matched_hsdes_waiver:
                        if 'HsdesWaiver' in matched_hsdes_waiver:
                            sum['hsdeswaived'] += 1
                            sum['total'] += 1
                        else:
                            sum['webwaived'] += 1
                            sum['total'] += 1
                        waivemsg += "  {}: {} {}: {}\n".format(sum['hsdeswaived']+sum['webwaived'], err.flow, err.subflow, err.error)

                        cls.errors['waived'].append(err)


            errmsg += textwrap.dedent("""
            Tests are based on this list of checkers: http://goto/psg_roadmap
            Please consult that site for documentation, owners and ready status of the checkers.
            If you get a missing audit log failure and the corresponding check is marked "not ready" on the web site, 
            please continue with your release. Automatic waivers are created for not ready checks, so that failure
            will not prevent the release. You will need to re-release once the checker is ready.
            """)
        else:
            if cls.libtype:
                errmsg = "dmx workspace check(library-level) for {}/{}@{} ({}) completed with no errors!\n".format(cls.project, cls.variant, cls.config, cls.libtype)
            else:
                errmsg = "dmx workspace check(variant-level) for {}/{}@{} completed with no errors!\n".format(cls.project, cls.variant, cls.config)
        
        if waivemsg:
            errmsg += textwrap.dedent("""
            ========================================================
            ============= These are the Waived errors. ============= 
            ========================================================
            """)
            errmsg += waivemsg

        errmsg += textwrap.dedent("""
        ===================================
        ============= SUMMARY =============
        ===================================
        ERRORS NOT WAIVED          : {failed}
        ERRORS WITH HSDES WAIVED   : {hsdeswaived}
        ERRORS WITH CMDLINE WAIVED : {cmdwaived}
        ERRORS WITH SW-WEB  WAIVED : {webwaived}
        ===================================
        TOTAL ERRORS FOUND         : {total}
        ===================================
        """.format(**sum))
        LOGGER.info(errmsg)

        # http://pg-rdjira:8080/browse/DI-779
        # 0 = check executed and no error found
        # 1 = (check executed and error found) or (system error)
        if int(sum['failed']) > 0:
            cls.exit_code = 1
        cls.report_message = errmsg

        return errmsg

    @classmethod
    def create_tnrerror_csv(cls, errors, wsroot=None):
        if wsroot:
            tnrerror_path = wsroot + '/tnrerrors.csv'
        else:
            tnrerror_path = cls.wsroot + '/tnrerrors.csv'
        fo = open(tnrerror_path, 'w+')

        # Create waiver file for all remaining waivable error 
        LOGGER.debug("Create tnrerrors.csv for remainding error")
        tnrerror_list = []

        for num, err in enumerate(errors):
            if not err.variant:
                err = err._replace(variant='*')
            if not err.flow:
                err = err._replace(flow='*')
            if not err.subflow:
                err = err._replace(subflow='*')
            if not err.error:
                err = err._replace(error='*')
            tnrerror = '\"{}\",\"{}\",\"{}\",\"{}\",\"{}\"\n'.format(err.variant, err.flow, err.subflow, 'autogen by dmx workspace check', err.error)
            fo.write(tnrerror)
 
        fo.close()
        LOGGER.info('tnrerrors.csv succesfully generated at {}'.format(tnrerror_path)) 

    @classmethod
    def get_checker_name(cls, err):
        '''
        OLD webapi.get_required_tests: (libtype, flow, subflow, check_type)
        NEW webapi.get_required_tests: (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone)       
        err object == TestFailure(variant=u'an', libtype='lint', topcell='', flow='deliverable', subflow='type', error='VP/templateset not yet available')
        '''
        ### For backward compatibility (rev older than icd_cad_qa/1.10)
        checkname = "{}_check".format(err.flow)
        if err.subflow:
            checkname = "{}_{}_check".format(err.flow, err.subflow)
      
        if cls.required_tests and len(cls.required_tests[0]) >= 8:
            for tup in cls.required_tests:
                if tup[0] == err.libtype and tup[1] == err.flow and tup[2] == err.subflow and tup[3]:
                    checkname = tup[4]
                    break
        return checkname


    @classmethod
    def is_milestone_thread_valid(cls):
        '''
        check if the milestone/thread is a valid schedule_item
        for the given project.
        Return False if fail, else True
        '''
        schedule_items = cls.get_valid_milestones_threads(cls.project)
        return (cls.milestone, cls.thread) in schedule_items

    @classmethod
    def get_variant_type(cls):
        ''' 
        Check if this project/variant has a 'Variant Type'
        return None if fail
        '''
        variant_property = {}
        try:
            variant_property = cls.icmcli.get_variant_properties(cls.project, cls.variant)
            LOGGER.debug("variant_property: {}".format(variant_property))
        except ICManageError as eobj:
            variant_property = {}
            LOGGER.debug(str(eobj))
        return variant_property.get('iptype')

    @classmethod
    def show_available_milestone_thread(cls):
        ''' Show all available options for this current workspace '''
        infostr = "Here are the available milestone/thread option for family {}:-\n".format(cls.project)
        for (milestone, thread) in cls.get_valid_milestones_threads(cls.project):
            infostr += "- milestone:{} thread:{}\n".format(milestone, thread)
        LOGGER.error(infostr)
        return infostr

    @classmethod
    def get_valid_milestones_threads(cls, project):
        ''' get a list of valid [(ms, thread), (ms, thread), ...] for a given project '''
        family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
        return family.get_valid_milestones_threads()

    @classmethod
    def get_workspaces(self, project=None, variant=None, libtype=None, config=None):
        '''
        We can longer use existing gdp get_workspace command. This is to map to our LEGACY icm.get_workspaces command
        libtype workspace is not supported in PSG methodogy, drop this        

        ==============================================================================

        Returns a list of all workspaces in the system
        If any of project, variant, libtype or config are specified then
        filters by those criteria

        :param project: Optional IC Manage project name
        :type project: str
        :param variant: Optional IC Manage variant name
        :type variant: str
        :param libtype: Optional IC Manage libtype name
        :type libtype: str
        :param config: Optional IC Manage configuration name:
        :type config: str
        :return: List of dicts, each one describing a workspace
        :rtype: list
        :raises: ICManageError
        '''
        icm = ICManageCLI()
        workspaces = []
        retkey = ['name','project:parent:name', 'variant:parent:name', 'config:parent:name','rootDir','created-by']
        results = icm.get_workspaces(retkeys=retkey)

        for line in results:
            workspace_name = line.get('name')
            workspace_dir = line.get('rootDir')
            workspace_user = line.get('created-by')
            workspace_name = line.get('name')
            workspace_project = line.get('project:parent:name')
            workspace_variant = line.get('variant:parent:name')
            workspace_libtype = '' 
            workspace_config = line.get('config:parent:name') 
            if project and project != workspace_project:
                continue

            if variant and variant != workspace_variant:
                continue

            if libtype and libtype != workspace_libtype:
                continue

            if config and config != workspace_config:
                continue

            workspace = {
                'workspace' : workspace_name,
                'user' : workspace_user, 
                'dir' : workspace_dir,
                'config' : workspace_config,
                'conf_type' : '',
                'variant' : workspace_variant,
                'libtype' : '',
                'project' : workspace_project,
                'location' : '',
                'description' : '',
            }
            workspaces.append(workspace)

        return workspaces

