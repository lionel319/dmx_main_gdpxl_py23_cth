#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/workspacelocaledit.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "quick reporttree"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import os
import re
import sys
import logging
import tempfile
import time
import datetime
import configparser 
import glob

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, lib)

import dmx.abnrlib.icm
import dmx.abnrlib.workspace
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.utillib.arcutils
from dmx.utillib.utils import run_command, quotify, get_workspace_disk
import dmx.utillib.stringifycmd
import subprocess
from shutil import copyfile


class WorkspaceLocalEditError(Exception): pass

class WorkspaceLocalEdit(object):

    def __init__(self, wsname, ip=None, deliverables=None, files=None, preview=False):
        self.preview = preview
        self.wsname = wsname
        self.ip = ip
        self.deliverables = deliverables if deliverables else []
        self.files = files 
        self.logger = logging.getLogger(__name__)
        self.cli = dmx.abnrlib.icm.ICManageCLI()
        self.wsdisk = get_workspace_disk()

        self.original_working_dir = os.getcwd()
   
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
                raise WorkspaceLocalEditError('{} is not an icm workspace'.format(path))
 

    def _get_edit_path(self):
        '''
        Get all file path that need to be chmod 
        '''
        all_path = []
        for ea_d in self.deliverables:
            path = '{}/{}/{}'.format(self.wsroot, self.ip, ea_d)
            if self.files:
                for ea_f in self.files:
                    path = '{}/{}/{}/{}'.format(self.wsroot, self.ip, ea_d, ea_f)
                    for glob_file in glob.glob(path):     
                        if not os.path.exists(glob_file):
                            raise WorkspaceLocalEditError('\'{}\' not found.'.format(path))
                        if glob_file not in all_path:
                            all_path.append(glob_file)
            else:
                for dirpath, dirnames, files in os.walk(path):
                    for ea_f in files:
                        if ea_f.startswith('.'): continue
                        file_to_chmod = dirpath + '/' +  ea_f
                        all_path.append(file_to_chmod)
    
            
        return all_path

    def make_editable_by_chmod(self, all_path, preview):
        '''
        Given a list of files and chmod 0770
        '''
        for ea_path in all_path:
            # check if symlink then remove link and move file into directory
            if os.path.islink(ea_path):
                if not preview:
                    symlink_path = os.path.realpath(ea_path)
                    os.remove(ea_path)
                    copyfile(symlink_path, ea_path)     

            if not preview:
                self.logger.debug("chmod 770 {}".format(ea_path))      
                os.chmod(ea_path, 0o770)
                print(type(ea_path))
                print('{} is locally editable'.format(ea_path))


    def run(self):
        if not self.cli.user_has_icm_license() :
            raise WorkspaceLocalEditError('License-less user cannot run dmx workspace edit ')

        self.is_icm_workspace(self.wsname)
        os.chdir(self.wsroot)

        all_path =  self._get_edit_path()
        self.make_editable_by_chmod(all_path, preview=self.preview)
