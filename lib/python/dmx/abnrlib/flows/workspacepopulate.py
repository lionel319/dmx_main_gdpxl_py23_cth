#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/workspacepopulate.py#4 $
$Change: 7481939 $
$DateTime: 2023/02/13 16:43:47 $
$Author: kenvengn $

Description: plugin for "quick reporttree"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from builtins import object
import os
import re
import sys
import logging
import tempfile
import time
import datetime
import json

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, lib)

import dmx.abnrlib.icm
import dmx.abnrlib.workspace
import dmx.abnrlib.flows.workspace
import dmx.utillib.arcutils
from dmx.utillib.utils import run_command, quotify, create_tempfile_that_is_readable_by_everyone, get_proj_disk 
import dmx.utillib.stringifycmd
import dmx.utillib.washgroup
import dmx.utillib.dmxapicmdlineutils
from dmx.abnrlib.flows.workspace import Workspace
from dmx.errorlib.exceptions import *
import dmx.utillib.admin
import dmx.utillib.diskutils


class WorkspacePopulateError(Exception): pass

class WorkspacePopulate(object):

    USE_ICM_CLIENT_KEYWORD = ':icm:'

    def __init__(self, project, ip, bom, wsname, cfgfile='', deliverables=None, preview=False, debug=False, force_cache=False):
        self.project = project
        self.ip = ip 
        self.bom = bom
        self.wsname = wsname
        self.deliverables = deliverables if deliverables else []
        self.cfgfile = cfgfile
        self.preview = preview
        self.logger = logging.getLogger(__name__)
        self.cli = dmx.abnrlib.icm.ICManageCLI()
        self.wg = dmx.utillib.washgroup.WashGroup()
        self.debug = debug
        self.force_cache = force_cache
        self.tmpfile = self._create_tempfile_that_is_readable_by_everyone()

        self.wsdisk = self.get_workspace_disk()
        self.original_working_dir = os.getcwd()

    def get_workspace_disk(self):
        ret = os.getenv("DMX_WORKSPACE")
        if not ret:
            raise DmxErrorICWS02("$DMX_WORKSPACE not defined. All 'dmx workspace' commands need this environment variable to be defined. This env var should store the full path to the disk area of where your workspace should-be/have-been created.")
        if not ret.startswith('/'):
            raise DmxErrorICWS02("$DMX_WORKSPACE must be specified in fullpath. Relative path is not allowed.")
        return ret


    def is_ws_folder_exist(self):
        if not self._is_use_icm_client():
            return os.path.isdir(self._get_wsroot())


    def _create_tempfile_that_is_readable_by_everyone(self):
        username = os.getenv("USER")
        hostname = os.getenv("HOST")
        progname = 'dmxwspop_'
        userhotel = '/p/psg/data/{}/job'.format(username)

        self.tmpfile = tempfile.mkstemp(prefix=progname, suffix='_'+hostname, dir=userhotel)[1]
        self.logger.debug("tmpfile created: {}".format(self.tmpfile))
        os.system("chmod -R 777 {}".format(self.tmpfile))
        return self.tmpfile


    def _write_sync_configuration_into_tmpfile(self):
        ### if cfgfile is not specified, create a cfgfile with the given deliverables (if deliverables is specified) in self.tmpfile
        if not self.cfgfile and self.deliverables:
            dmx.abnrlib.flows.workspace.Workspace.write_sync_config_file(self.tmpfile, libtypes=self.deliverables)
       
        ### if cfgfile is not specified, and deliverables not specified, generate default config file (sync all) to self.tmpfile
        if not self.cfgfile and not self.deliverables:
            dmx.abnrlib.flows.workspace.Workspace.write_sync_config_file(self.tmpfile)

        ### if cfgfile is specified, copy it to self.tmpfile
        if self.cfgfile:
            os.system("cat {} > {}".format(self.cfgfile, self.tmpfile))
        
        self.logger.debug("cfgfile: {}".format(self.cfgfile))
        self.logger.debug("tmpfile: {}".format(self.tmpfile))


    def _create_workspace(self):
        self.logger.info('Creating workspace ...')

        if self._is_use_icm_client():
            ignore_clientname = False
            wsdir = self.wsdisk
        else:
            ignore_clientname = True
            wsdir = os.path.join(self.wsdisk, self.wsname)

        self.logger.debug("wsdir:{}".format(wsdir))
        self.wsclient = self.cli.add_workspace(self.project, self.ip, self.bom, dirname=wsdir, ignore_clientname=ignore_clientname)
        self.logger.info("Workspace({}) created at {}".format(self.wsclient, wsdir))


    def _get_wsroot(self):
        if self._is_use_icm_client():
            wsroot = os.path.join(self.wsdisk, self.wsclient)
        else:
            wsroot = os.path.join(self.wsdisk, self.wsname)
        return wsroot


    def _is_use_icm_client(self):
        return self.wsname == self.USE_ICM_CLIENT_KEYWORD

    def _is_bom_immutable(self):
        if self.bom.startswith('snap-') or self.bom.startswith('REL'):
            return True
        return False


    def _get_dmx_binary_path(self):
        exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'bin', 'dmx')
        exe = os.path.abspath(exe)
        return exe

    def _get_dmx_cmd(self):
        exe = self._get_dmx_binary_path()
        debugstr = ''
        if self.is_current_logger_level_debug():
            debugstr = ' --debug '
        cmd = '{} workspace populate -p {} -i {} -b {} -w {} -c {} {} ; '.format(exe, self.project, self.ip, self.bom, self.wsname, self.tmpfile, debugstr)
        return cmd

   
    def _get_final_cmd(self):
        basecmd = self._get_dmx_cmd()
        washopts = 'default'
        arcopts = 'default'
        sshopts = 'default'
        envvar = {'DB_FAMILIES': ':env:', 'DMX_WORKSPACE': ':env:'}
        sc = dmx.utillib.stringifycmd.StringifyCmd(basecmd=basecmd, envvar=envvar, sshopts=sshopts, washopts=None, arcopts=arcopts)
        sc.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
        sc.arcexe = 'arc'

        final_cmd = sc.get_finalcmd_string()
        self.logger.debug("stringifycmd: {}".format(final_cmd))
        return final_cmd


    def _rerun_dmx_workspace_populate_as_psginfraadm(self):
        final_cmd = self._get_final_cmd()
        return os.system(final_cmd)

            
    def _user_is_psginfraadm(self):
        return os.getenv("USER") == 'psginfraadm'

    def is_wsdisk_writable(self):
        return os.access(self.wsdisk, os.W_OK)


    def remove_arms_from_groups(self, groups):
        retlist = []
        for g in groups:
            if 'arm' not in g:
                retlist.append(g)
        return retlist

    def is_dmx_workspace_in_approved_disk(self):
        ret = dmx.utillib.utils.check_proj_restrict(self.project, self.wsdisk)
        if ret == 0 or ret == 1: 
            return True
        elif ret == 2: 
            return False 

    def remove_cache_area_folder(self):
        self.logger.info('Removing cache area folder')
        error, configparser = dmx.abnrlib.flows.workspace.Workspace.read_sync_config_file(self.tmpfile)
        vrt =  configparser.get('1','variants').split(' ')
        lt =  configparser.get('1','libtypes').split(' ')

        cmd = 'dmx report content -p {} -i {} -b {} --hier | sed \'s/\t//g\' | sort -u '.format(self.project, self.ip, self.bom)
        du = dmx.utillib.diskutils.DiskUtils(site=os.environ.get('EC_SITE')) 
        dd = du.get_all_disks_data("_sion2_")

        #print cmd
        exitcode, stdout, stderr = run_command(cmd)
        results = stdout.rstrip().rsplit('\n')

        all_path = []
        for result in results:
            match = re.search('(\S+)\/(\S+):(\S+)@(\S+)', result)
            if not match:
                continue

            project = match.group(1)
            ip = match.group(2)
            libtype = match.group(3)
            bom = match.group(4)

            if (lt != ['*'] and libtype not in lt) or (vrt != ['*'] and ip not in vrt):
                continue

            #print project, ip, libtype, bom
            # /nfs/site/disks/psg_sion2_1/da_i16/dai16liotest1/ipspec/REL1.0LTMrevA0__22ww315b
            path = du.find_exact_folder_from_disks_data(dd, '{}/{}/{}/{}/'.format(project, ip, libtype, bom))
            if os.path.exists(path):
                all_path.append(path)

        if not all_path:
            return 

        command = 'rm -rf {}'.format(' '.join(all_path))

        basecmd = command 
        washopts = 'default'
        arcopts = 'default'
        sshopts = 'default'
        envvar = {'DB_FAMILIES': ':env:', 'DMX_WORKSPACE': ':env:'}
        sc = dmx.utillib.stringifycmd.StringifyCmd(basecmd=basecmd, envvar=envvar, sshopts=sshopts, washopts=None, arcopts=arcopts)
        sc.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
        sc.arcexe = 'arc'

        final_cmd = sc.get_finalcmd_string()
        self.logger.debug("stringifycmd: {}".format(final_cmd))
 
        exitcode, stdout, stderr = run_command(final_cmd)

        self.logger.info('Remove cache ARC Job: {}'.format(stdout))
        if exitcode or stderr:
            raise DmxErrorICWS04(stderr)
        

    def run(self):
        start = time.time()
        today_date = datetime.date.today().strftime('%Y/%m/%d')
        if self.is_dmx_workspace_in_approved_disk():
            self.logger.info('$DMX_WORKSPACE is in approved disk. Continue...')
        else:
            approved_disks = '\n'.join(get_proj_disk(self.project))
            raise DmxErrorICWS04('$DMX_WORKSPACE does not in approved disk for {0}. This is the list of approved disk:\n{1}\nPlease set $DMX_WOKRPSACE in one of the above directory for project \'{0}\''.format(self.project, approved_disks))
        ret = 1

        if self.is_ws_folder_exist():
            raise DmxErrorICWS05("Workspace Folder ({}) already exist. If you still would like to populate to here, kindly run 'dmx workspace delete' to delete the existing workspace first.".format(self._get_wsroot()))

        if not self.is_wsdisk_writable():
            raise DmxErrorICWS06("Workspace Disk ({}) is not writable by ({}). Please make sure it is writable.".format(self.wsdisk, os.getenv("USER")))

        self.logger.debug("Writing sync configuration into tmpfile:{}".format(self.tmpfile))
        self._write_sync_configuration_into_tmpfile()

        
        self.logger.info("Checking if user has the necessary linux groups to populate this configuration ...")
        missing_groups = self.get_user_missing_groups_from_pvc()
        self.logger.debug("missing_groups: {}".format(missing_groups))
        missing_groups = self.remove_arms_from_groups(missing_groups)
        self.logger.debug("missing_groups_no_arms: {}".format(missing_groups))
        if not missing_groups:
            self.logger.info("You have all the necessary linux groups to run dmx workspace populate.".format(missing_groups))
        else:
            raise DmxErrorCFPM01("You({}) are missing these linux groups from running dmx workspace populate. Kindly request these linux groups: {}".format(os.getenv("USER"), missing_groups))


        if self.preview:
            self.logger.info("Workspace will not be creates, as this is a preview-mode.")
            return 0

        recall = os.getenv("DMX_WSPOP_RECALL", False)
        if not recall and not self.cli.user_has_icm_license() and self._is_bom_immutable() and not self._user_is_psginfraadm():
          #  return self._rerun_dmx_workspace_populate_as_psginfraadm()
            return self._rerun_dmx_workspace_populate_as_self_with_lesser_groups(as_psginfraadm=True)


        if self.force_cache:
            self.remove_cache_area_folder()

        if self.user_groups_in_current_process_is_over_16():
            return self._rerun_dmx_workspace_populate_as_self_with_lesser_groups()

        try:
            self._create_workspace()
            self.wsroot = self._get_wsroot()
    
            self.logger.info("Populating workspace ...")
            ret =  self.cli.sync_workspace(self.wsclient, skeleton=True)
            if ret != 0 :
                self.logger.error('Workspace skeleton sync return value is no 0')
                self.rollback_workspace()
    
            os.chdir(self.wsroot)
            ws = dmx.abnrlib.workspace.Workspace()
            ret, broken_link = ws.sync(cfgfile=self.tmpfile, force=False, sync_cache=True)
            if ret != 0:
                self.logger.error('Workspace sync return value is no 0')
                self.rollback_workspace()
            os.chdir(self.original_working_dir)

            self.report_broken_link(broken_link)

            ### If user is psginfraadm, we chmod the wsroot and everything underneath it to 770
            ### so that if user wanna delete them, they can.
            if self._user_is_psginfraadm():
                cmd = "chmod -R 770 {}".format(self.wsroot)
                self.logger.debug(cmd)
                os.system(cmd)
            else:
                try:
                    self.logger.info("Running post-sync-trigger ...")
                    # /p/psg/flows/common/icmadmin/gdpxl/1.0/icm_home/triggers/icmpm/enforce_icm_protection.py
                    exe = os.path.join(os.getenv("ICMADMIN_ROOT"), 'icm_home', 'triggers', 'icmpm', 'enforce_icm_protection.py')
                    cmd = '{} --client-dir {} --client {} --project {} --variant {}'.format(exe, self.wsroot, self.wsclient, self.project, self.ip)
                    os.system(cmd)
                except Exception as e:
                    self.logger.warning("post-sync-trigger failed.")
                    self.logger.warning(e)
 
            end = time.time()
            elapsed_time = round((end - start), 3)
            workspace_detail = {'PopulationTime': elapsed_time, 'PopulationDate':today_date}
            self.cli.add_workspace_properties(self.wsclient, workspace_detail)
            self.logger.info('Workspace populate sucessfully. ') 

            ret = 0
    
        except Exception as E:
            if os.path.exists(self.wsname):
                self.logger.error('Unexpected Error catch')
                self.logger.error(E)
                self.rollback_workspace()
            else:
                raise
        return ret


    def user_groups_in_current_process_is_over_16(self):
        usergroups = self.wg.get_user_groups(current_process=True)
        if len(usergroups) > 16:
            return True
        return False
  

    def rollback_workspace(self):
        self.logger.info("Rollback....")
        Workspace.delete_action(rmfiles=True, yes_to_all=True, workspacename=[self.wsname])
        sys.exit(0)

    def get_groups_by_pvc(self):
        if not self.cli.user_has_icm_license():
            exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'bin', 'dmx_api_cmdline.py')
            cmd = '{} get_groups_by_pvc --include_base_groups --include_eip_groups '.format(exe)
            cmd += ' -p {} -i {} -b {}'.format(self.project, self.ip, self.bom)

            if self.is_current_logger_level_debug():
                cmd += ' --debug'

            envvar = {'DB_FAMILIES': ':env:', 'WASHGROUP_DBFILE': ':env:'}
            s = dmx.utillib.stringifycmd.StringifyCmd(cmd, envvar=envvar, arcopts='default', sshopts='default', washopts='default')
            s.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
            finalcmd = s.get_finalcmd_string()
            exitcode, stdout, stderr = run_command(finalcmd)
            output = dmx.utillib.dmxapicmdlineutils.parse_output_to_dict(stdout + stderr)
            self.logger.debug("get groups by pvc: {}".format(output))
            return output
        else:
            return self.wg.get_groups_by_pvc(self.project, self.ip, self.bom, include_eip_groups=True, include_base_groups=True)

    def _rerun_dmx_workspace_populate_as_self_with_lesser_groups(self, as_psginfraadm=False):
        pvcgroups = self.get_groups_by_pvc()
        if len(pvcgroups) > 16:
            errmsg = """The required groups to populate this configuration has already exceeded 16 linux groups.
            These are the needed groups: {}
            Kindly contact psgicmsupport@intel.com for help.
            """.format(pvcgroups)
            raise DmxErrorCFPM01(errmsg)

        washopts = {'groups': ' '.join(pvcgroups) + ' psgda'}
        dmxcmd = self._get_dmx_cmd()
        if as_psginfraadm:
            arcopts = 'default'
            sshopts = 'default'
            envvar = {'DMX_WORKSPACE': ':env:', 'DMX_WSPOP_RECALL': '1'}
            s = dmx.utillib.stringifycmd.StringifyCmd(basecmd=dmxcmd, envvar=envvar, sshopts=sshopts, washopts=washopts, arcopts=arcopts)
            s.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
        else:
            envvar = {'DMX_WSPOP_RECALL': '1'}
            s = dmx.utillib.stringifycmd.StringifyCmd(dmxcmd, washopts=washopts, envvar=envvar)
        finalcmd = s.get_finalcmd_string()

        msg = """Your current process has more than 16 linux groups.
        We will be re-submitting your job by washing your linux groups.
        The following will be the command that we will be re-running:-
        > {}
        """.format(finalcmd)
        self.logger.info(msg)
        return os.system(finalcmd)


    def get_user_missing_groups_from_pvc(self):
        ### Running this as psginfraadm
        if not self.cli.user_has_icm_license():
            exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'bin', 'dmx_api_cmdline.py')
            cmd = '{} get_user_missing_groups_from_accessing_pvc'.format(exe)
            cmd += ' --userid {}'.format(os.getenv("USER"))
            cmd += ' -p {} -i {} -b {}'.format(self.project, self.ip, self.bom)

            if self.is_current_logger_level_debug():
                cmd += ' --debug'

            envvar = {'DB_FAMILIES': ':env:', 'WASHGROUP_DBFILE': ':env:'}
            s = dmx.utillib.stringifycmd.StringifyCmd(cmd, envvar=envvar, arcopts='default', sshopts='default', washopts='default')
            s.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
            finalcmd = s.get_finalcmd_string()
            exitcode, stdout, stderr = run_command(finalcmd)
            output = dmx.utillib.dmxapicmdlineutils.parse_output_to_dict(stdout + stderr)
            self.logger.debug("user missing groups: {}".format(output))
            return output
        
        ### Running this as self
        else:
            return self.wg.get_user_missing_groups_from_accessing_pvc(os.getenv("USER"), self.project, self.ip, self.bom)


    def is_current_logger_level_debug(self):
        #level = self.logger.getEffectiveLevel()
        #if level == logging.DEBUG:
        #    return True
        #return False
        return self.debug

    def report_broken_link(self, list_of_link):
        if not list_of_link: return
        for link_list in list_of_link:
            if type(link_list) is not list: continue
            for link in link_list:
                if not os.path.exists(link):
                    self.logger.warning('Broken Link: {}'.format(link))

