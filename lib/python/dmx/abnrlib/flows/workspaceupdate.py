#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/workspaceupdate.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

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
import configparser 

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, lib)

import dmx.abnrlib.icm
import dmx.abnrlib.workspace
import dmx.utillib.arcutils
from dmx.utillib.utils import run_command, quotify, get_workspace_disk
import dmx.utillib.stringifycmd
import subprocess

class WorkspaceUpdateError(Exception): pass

class WorkspaceUpdate(object):

    def __init__(self, wsname, cfgfile='', deliverables=None, original_user='', preview=False, force=False):
        self.force = force
        self.preview = preview
        self.wsname = wsname
        self.deliverables = deliverables if deliverables else []
        self.cfgfile = os.path.abspath(cfgfile) if cfgfile else ''
        self.logger = logging.getLogger(__name__)
        self.cli = dmx.abnrlib.icm.ICManageCLI()
        self.original_user = original_user
        self.wsroot = ''   
        self._ip = ''
        self._project = ''
        self.tmpfile = self._create_tempfile_that_is_readable_by_everyone()

        self.wsdisk = get_workspace_disk()
        self.original_working_dir = os.getcwd()
    


    def _create_tempconfigfile_that_is_readable_by_everyone(self, name):
        username = os.getenv("USER")
        hostname = os.getenv("HOST")
        progname = 'dmxwspop_'
        userhotel = '/p/psg/data/{}/job'.format(username)

        tmpfile = tempfile.mkstemp(prefix=progname, suffix='_'+hostname+'_'+name, dir=userhotel)[1]
        self.logger.debug("tmpfile created: {}".format(tmpfile))
        os.system("chmod -R 777 {}".format(tmpfile))
        return tmpfile


    def _create_tempfile_that_is_readable_by_everyone(self):
        username = os.getenv("USER")
        hostname = os.getenv("HOST")
        progname = 'dmxwspop_'
        userhotel = '/p/psg/data/{}/job'.format(username)

        self.tmpfile = tempfile.mkstemp(prefix=progname, suffix='_'+hostname, dir=userhotel)[1]
        self.logger.debug("tmpfile created: {}".format(self.tmpfile))
        os.system("chmod -R 777 {}".format(self.tmpfile))
        return self.tmpfile

    def get_type_of_config_file(self, config_type):
        os.chdir(self.wsroot)
        ws = dmx.abnrlib.workspace.Workspace()
        cf = ws.get_config_factory_object()
        config_data = dmx.abnrlib.config_factory.ConfigFactory.get_deliverable_type_from_config_factory_object(cf, config_type)
        config_dict = self.get_dict_from_config(self.tmpfile, config_data)
        return self.write_cfg_file(config_dict, config_type) 



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

        self.immutable_config_file = self.get_type_of_config_file('immutable')
        self.mutable_config_file = self.get_type_of_config_file('mutable')
        self.logger.debug("cfgfile: {}".format(self.cfgfile))
        self.logger.debug("tmpfile: {}".format(self.tmpfile))
        #sys.exit(1) 

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
        force_opt = ''
        if self.force:
            force_opt = '--force'
        cfgfile_opt = ''
        if self.cfgfile:
            cfgfile_opt = '-c {}'.format(self.cfgfile)
        cmd = '{} workspace update -w {} -o {} {} {} --debug ; '.format(exe, self.wsname, self.original_user, force_opt, cfgfile_opt)
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


    def _rerun_dmx_workspace_update_as_psginfraadm(self):
        final_cmd = self._get_final_cmd()
        return os.system(final_cmd)

            
    def _user_is_psginfraadm(self):
        return os.getenv("USER") == 'psginfraadm'

    def is_icm_workspace(self, path):
        '''
        Check if the given path is icm workspace 
        '''    
        ws_path = self.wsdisk + '/' + path 
        try:
            ws = dmx.abnrlib.workspace.Workspace(workspacepath=ws_path)
            self.wsroot = ws_path
            self.bom = ws._bom
            return True
        except dmx.abnrlib.workspace.WorkspaceError:
            try:
                ws_detail = self.cli.get_workspace_details(path)
                self.wsroot = ws_detail.get('Dir')
                self.bom = ws_detail.get('Config')
            except IndexError:
                raise WorkspaceUpdateError('{} is not an icm workspace'.format(path))
    
    def remove_all_file(self):
        '''
        sync #0 to remove all file
        ''' 
        os.chdir(self.wsroot)
        cmd = 'icmp4 sync -f ...#0'
        ret = subprocess.call([cmd], shell=True)
        return ret

    def remove_immutable_file_link(self):
        '''
        remove all immutable file with sync #0
        ''' 
        os.chdir(self.wsroot)
        immutable_file_path = self.get_type_of_path('immutable')
        ret = ''
        for ea_path in immutable_file_path:
            cmd = 'icmp4 sync -f {}...#0'.format(ea_path)
            ret = subprocess.call([cmd], shell=True)
        return ret


    def get_type_of_path(self, types):
        '''
        Get mutable or immutable libtype path from workspace  
        '''
        os.chdir(self.wsroot)
        ws = dmx.abnrlib.workspace.Workspace()
        cf = ws.get_config_factory_object()
        mutable_path = []
        immutable_path = []
        all_path = []
        
        for conf in cf.flatten_tree():

            if conf.is_simple() and conf.is_mutable() and types == 'mutable':
                path =  '{}/{}/{}'.format(self.wsroot, conf._variant, conf._libtype)
                all_path.append(path)
            elif conf.is_simple() and not conf.is_mutable() and types == 'immutable':
                path =  '{}/{}/{}'.format(self.wsroot, conf._variant, conf._libtype)
                all_path.append(path)

        return all_path

    def read_config_file(self, cfg):
        config = configparser.ConfigParser()
        config.read(cfg)
        data = {}
        for ea_section in config.sections():
            variants =  config.get(ea_section, 'variants')
            libtypes =  config.get(ea_section, 'libtypes')
            data[variants] = libtypes        
        return data

    def write_cfg_file(self, wd, config_type):
        '''
        Read in dictionary and write config file
        '''

        self.temp_file = self._create_tempconfigfile_that_is_readable_by_everyone(config_type)
        self.logger.debug("{}_cfgfile: {}".format(config_type, self.temp_file))

        fo = open(self.temp_file, 'w+')
        num = 1
        for k, v in list(wd.items()):
            if v == '': continue
            fo.write('[{}]\n'.format(num))
            fo.write('variants: {}\n'.format(k))
            fo.write('libtypes: {}\n\n'.format(v))
            num = num + 1

        return self.temp_file


    def get_dict_from_config(self, cfgfile, config_data):
        '''
        Read config file and return dict with mutable or immutable
        '''
        data = self.read_config_file(cfgfile)
        num = 1
        wd = {}
        for variant, libtype in list(data.items()):
            temp_libtype = []
            if variant == '*':
                for var in list(config_data.keys()):
                   # wd[var] = ''

                    if libtype == '*':
                        wd[var] = ' '.join(config_data.get(var))
                        continue

                    libtypes = libtype.split(' ')
                    for ea_libtype in libtypes:
                        if ea_libtype in config_data.get(var):
                            if ea_libtype in temp_libtype: continue 
                            temp_libtype.append(ea_libtype)
                    if wd.get(var):
                        wd[var] = wd[var] + ' ' +  ' '.join(temp_libtype)
                    else:
                        wd[var] = ' '.join(temp_libtype)    
            else:
                temp_libtype = []
                variants_split = variant.split(' ')
                for ea_variant in variants_split:
                    if ea_variant in list(config_data.keys()):
                     #   wd[ea_variant] = '' 
      
                        if libtype == '*':
                            wd[ea_variant] = ' '.join(config_data.get(ea_variant)) 
                            continue 

                        libtypes = libtype.split(' ')
                        for ea_libtype in libtypes:
                            if ea_libtype in config_data.get(ea_variant):
                                if ea_libtype not in temp_libtype:
                                    temp_libtype.append(ea_libtype)
                        if wd.get(ea_variant):
                            wd[ea_variant] = wd[ea_variant] + ' ' + ' '.join(temp_libtype)
                        else:
                            wd[ea_variant] = ' '.join(temp_libtype)
                num = num + 1
        return wd

    def get_deliverable_path(self, config_file):
        DELIVERABLE_PATH = []
        if self.deliverables:
            config = dmx.abnrlib.workspace.Workspace().read_sync_config_file(config_file)

            for section in config.sections():
                var = config.get(section, 'variants')
                deliverable = config.get(section, 'libtypes')
                rp = '{}/{}/{}'.format(self.wsroot, var, deliverable)
                DELIVERABLE_PATH.append(rp)
        return DELIVERABLE_PATH

    def is_workspace_accessible(self):
        return os.access(os.path.join(self.wsdisk, self.wsname), os.W_OK)
   
    def run_dmx_moab(self):
        self.logger.info('Proceed to perform Dmx Moab')
        if self._ip == '' and self._project == '' :
            os.chdir(self.wsroot)
            ws = dmx.abnrlib.workspace.Workspace()
            self._ip = ws.ip
            self._project= ws.project
        dmx_moab = DmxMoab(wsroot=self.wsroot, bom=self.bom, ip=self._ip, project=self._project)
        dmx_moab.process()
        self.logger.info('Dmx Moab Process Ends ')


    def run(self):
        broken_link_immutable = ''
        if not self.is_workspace_accessible():
            raise WorkspaceUpdateError('Workspace {} does not exists!'.format(os.path.join(self.wsdisk, self.wsname)))
        
        if not self.cli.user_has_icm_license() and not self._user_is_psginfraadm():
            return self._rerun_dmx_workspace_update_as_psginfraadm()
 
        if self.is_icm_workspace(self.wsname):
            os.chdir(self.wsroot)
            ws = dmx.abnrlib.workspace.Workspace(preview=self.preview)
            self.bom = ws._bom
            if not self._is_bom_immutable() and self._user_is_psginfraadm() and self.original_user!='psginfraadm':
                raise WorkspaceUpdateError('License-less user cannot run update with mutable bom ')
             
        self._write_sync_configuration_into_tmpfile()
        os.chdir(self.wsroot)
        
        if self.force:
            self.logger.info('-f/--force found. Force update...')
            deliverable_path = self.get_deliverable_path(self.immutable_config_file)
            if self.original_working_dir in deliverable_path:
                raise WorkspaceUpdateError('Your current deliverable directory will be deleted and resync. Please run the command in other directory')
            for path in deliverable_path:
                cmd = 'rm -rf {}/*'.format(path)
                self.logger.debug(cmd)
                exitcode, stdout, stderr = run_command(cmd)

                if exitcode or stderr:
                    raise WorkspaceUpdateError(stderr)

        if os.stat(self.immutable_config_file).st_size != 0:
            ret, broken_link_immutable = ws.sync(cfgfile=self.immutable_config_file, force=False, sync_cache=True, update_without_skeleton_sync=True)

        if os.stat(self.mutable_config_file).st_size != 0: 
            ws.sync(cfgfile=self.mutable_config_file, force=self.force, sync_cache=False, update_without_skeleton_sync=True)
        os.chdir(self.original_working_dir)


        ws.report_broken_link(broken_link_immutable)

        if self._user_is_psginfraadm():
            cmd = "chmod -R 770 {}".format(self.wsroot)
            self.logger.debug(cmd)
            os.system(cmd)

        self.logger.info('Workspace update done.') 
