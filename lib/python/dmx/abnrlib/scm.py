#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/scm.py#3 $
$Change: 7521490 $
$DateTime: 2023/03/12 23:00:52 $
$Author: wplim $

Description: Abstract base class used for representing IC Manage configurations. See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import division
from __future__ import print_function

## @addtogroup dmxlib
## @{

from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import os
import sys
import re
import shutil
import logging
import glob
import argparse
import datetime
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.abnrlib.icm 
from dmx.utillib.utils import run_command
import dmx.utillib.naa 
import dmx.ecolib.ecosphere
import dmx.dmlib.ICManageWorkspace
import dmx.dmlib.ICManageWorkspaceMock
import dmx.abnrlib.config_factory
import dmx.utillib.admin

ICMADMIN = 'icmAdmin'
LOGGER = logging.getLogger(__name__)
EXCLUDED_FILES = ['.icminfo']
EXCLUDED_DIRS = ['.naa_tmp']

class SCMError(Exception): pass

class SCM(object):
    def __init__(self, preview=False):
        self.preview = preview
        self.cli = dmx.abnrlib.icm.ICManageCLI(preview=preview)
        self.naa = dmx.utillib.naa.NAA(preview=preview)
        self.logger = LOGGER
        self.eco = dmx.ecolib.ecosphere.EcoSphere(preview=preview)
        self.scm_path = os.path.realpath(__file__)
        self.icmp4 = 'xlp4'
        ### HIDDEN FEATURE:
        ### Only works for ADMINS:
        ### We are relying on 'xlp4' to prevent checkins of symlinks.
        ### But if there is a need to bypass that restrictions, u can set this env var
        if dmx.utillib.admin.is_admin():
            if os.getenv("DMX_SCM_NOCHECK", "") == '1':
                self.icmp4 = '_xlp4'


    def _get_naa_tmp_dir(self, workspaceroot, ip, deliverable):
        running_counter = 1
        base_naa_tmp_dir = '{}/{}/{}/.naa_tmp'.format(workspaceroot, ip, deliverable)
        found = False
        while not found:
            new_naa_tmp_dir = '{}.{}'.format(base_naa_tmp_dir, running_counter)
            if os.path.exists(new_naa_tmp_dir):
                running_counter += 1
            else:
                found = True
        return new_naa_tmp_dir                

    def _is_file_naa_managed(self, filename):
        '''
        check if file is NAA managed. NAA managed files need to fulfill the following criteria:-
        - is icm managed
        - is a symlink to naa path.
        '''
        if self._is_file_managed(filename):
            if self.naa.is_path_naa_path(filename):
                return True
        return False        

    def _is_file_diff(self, first_file, second_file):
        '''
        Compare 2 physical files
        Returns True if files are different
        '''
        ret = False
        command = 'cmp --silent {} {}'.format(first_file, second_file)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            ret = True
                            
        return ret

    def _glob_perforce_pattern_for_checkin(self, pattern):
        '''
        Returns physical filepath to be checkin with Perforce file pattern
        '''
        command = '{} status {}'.format(self.icmp4, pattern)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        results = []            
        for line in stdout.splitlines():
            m = re.match('(.*?) - (.*) (//.*)', line)
            if m:
                physfile = m.group(1)
                operation = m.group(2)
                perforcefile = m.group(3)
                self.logger.debug("_glob_perforce_pattern_for_checkin:{}".format([physfile, operation, perforcefile]))
                results.append((physfile, operation, perforcefile))
            else:
                ### Print out files that failed to be checked-out so that
                ### this ease in debugging.
                self.logger.warning(stdout + stderr)
        return results                

    def _glob_perforce_pattern_for_checkout(self, pattern):
        '''
        Returns physical filepath to be checkout with Perforce file pattern
        '''
        command = '{} edit -n {}'.format(self.icmp4, pattern)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        results = []            
        for line in stdout.splitlines():
            m = re.match('(.*?)#(.*?) - (.*)', line)
            if m:
                perforcefile = m.group(1)
                version = m.group(2)
                operation = m.group(3)
                results.append((perforcefile,version,  operation))
            else:
                ### Print out files that failed to be checked-out so that
                ### this ease in debugging.
                self.logger.warning(stdout + stderr)
        return results          

    def _glob_perforce_pattern_for_revert(self, pattern):
        '''
        Returns physical filepath to be reverted with Perforce file pattern
        '''
        command = '{} revert -n {}'.format(self.icmp4, pattern)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        results = []            
        for line in stdout.splitlines():
            m = re.match('(.*?)#(.*?) - (.*)', line)
            if m:
                perforcefile = m.group(1)
                version = m.group(2)
                operation = m.group(3)
                results.append((perforcefile,version,  operation))
            else:
                ### Print out files that failed to be checked-out so that
                ### this ease in debugging.
                self.logger.warning(stdout + stderr)
        return results           

    def _glob_perforce_pattern_for_delete(self, pattern):
        '''
        Returns physical filepath to be deleted with Perforce file pattern
        '''
        command = '{} delete -n {}'.format(self.icmp4, pattern)
        exitcode, stdout, stderr = run_command(command)
        self.logger.debug("_glob_perforce_pattern_for_delete: cmd:{}\n- exitcode:{}\n- stdout:{}\n- stderr:{}\n".format(command, exitcode, stdout, stderr))
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        results = []            
        for line in stdout.splitlines():
            m = re.match('(.*?)#(.*?) - (.*)', line)
            if m:
                perforcefile = m.group(1)
                version = m.group(2)
                operation = m.group(3)
                results.append((perforcefile,version,  operation))
            else:
                ### Print out files that failed to be checked-out so that
                ### this ease in debugging.
                self.logger.warning(stdout + stderr)
        return results           

    def _copy_file(self, source, dest):
        '''
        Copy file from source to dest
        '''
        command = 'cp -rf {} {}'.format(source, dest)
        self.logger.debug("_copy_file: {}".format(command))
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))

    def _create_directory(self, path):
        '''
        Create nested directory
        '''
        command = 'mkdir -p {}'.format(path)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))
                
           
    def _edit_symlink_in_icm(self, symlink):   
        '''
        Mark symlink as edit in ICM
        '''
        command = '{} edit -t symlink+l {}'.format(self.icmp4, symlink)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))

    def _add_symlink_to_icm(self, symlink):   
        '''
        Mark symlink as add in ICM
        '''
        command = '{} add -t symlink+l {}'.format(self.icmp4, symlink)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))

    def _add_file_to_icm(self, file):
        '''
        Mark file as add in ICM
        '''
        command = '{} add {}'.format(self.icmp4, file)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))            

    def _edit_file_in_icm(self, file):   
        '''
        Mark file as edit in ICM
        '''
        command = '{} edit {}'.format(self.icmp4, file)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))            

    def _submit_to_icm(self, changelist=None, description='', filespec='...'):
        '''
        Submit changelist to ICM
        If changelist is None, submit everything and expects description to be provided
        If changelist is an integer, submit only the changelist
        '''
        if changelist:
            command = '{} submit -c {}'.format(self.icmp4, changelist)
        else:
            command = '{} submit -d \"{}\" {}'.format(self.icmp4, description, filespec)
        self.logger.debug("Submitting files to icm ...")
        self.logger.debug("command: {}".format(command))
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            self.logger.debug(stdout + stderr)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))                    

    def _revert_file_in_workspace(self, file):
        '''
        Revery file in a workspace
        '''
        command = '{} revert {}'.format(self.icmp4, file)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))                

    def _delete_file_in_workspace(self, file):
        '''
        Delete a file
        '''
        command = '{} delete {}'.format(self.icmp4, file)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))

    def _delete_file_in_depot(self, path):
        '''
        Delete files in depot
        '''
        ret = 1
        command = '{} delete -k {}'.format(self.icmp4, path)
        self.logger.debug("Deleting files in depot ...")
        self.logger.debug("command: {}".format(command))
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            self.logger.debug(stdout + stderr)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))

            if 'file(s) not on client' in stderr:
                ret = 0

        return ret

    def _is_file_managed(self, file):
        '''
        Returns True if file is managed
        '''
        ret = True
        command = '{} have {}'.format(self.icmp4, file)
        exitcode, stdout, stderr = run_command(command)
        self.logger.debug("_is_file_managed({}) : \nexitcode:{}\nstdout:{}\nstderr:{}\n".format(file, exitcode, stdout, stderr))
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        if 'file(s) not on client' in stderr:
            ret = False
        return ret  
        
    def _is_file_checked_out_globally(self, file):
        '''
        Returns True if file is checked out globally
        '''
        ret = True
        command = '{} opened -a {}'.format(self.icmp4, file)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        if ' not opened ' in stderr:
            ret = False
        else:
            self.logger.debug(stderr)
            self.logger.debug(stdout)
        # icmp4 opened -x returns files in exclusive lock
        # in the past, -a would suffice, but with distribution system, we need both -x and -a
        # In gdpxl, we do not have distribution system currentyle, we will diable the -x argument
        command = '{} opened {}'.format(self.icmp4, file)
        #command = '{} opened -x {}'.format(self.icmp4, file)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        if ' not opened ' in stderr:
            ret = False
        else:
            self.logger.debug(stderr)
            self.logger.debug(stdout)                        
        return ret                                 

    def _is_file_checked_out_in_this_workspace(self, file):
        '''
        Returns True if file is checked out in the current workspace
        '''
        ret = True
        command = '{} opened {}'.format(self.icmp4, file)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        if 'file(s) not opened on this client' in stderr:
            ret = False
        return ret          

    def _get_changelist_spec(self):
        '''
        Get changelist specification
        '''
        command = '{} change -o'.format(self.icmp4)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))                          
        return stdout.splitlines()            

    def _add_changelist_to_icm(self, spec):
        '''
        Add a changelist specification to ICM
        '''
        changelist = ''
        command = '{} change -i < {}'.format(self.icmp4, spec)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stdout + stderr)
                raise SCMError('Failed to run {}'.format(command))                          
            m = re.match('Change (.*?)\s', str(stdout))
            if m:
                changelist = m.group(1)
            else:
                raise SCMError('Failed to retrieve changelist number')            
        return changelist                

    def _get_latest_naa_file(self, family, project, ip, deliverable, bom, file):        
        '''
        Get the latest filename in NAA storage
        NAA filename: <filename>.<numeric>
                      abc.txt.2
        '''
        not_found = True
        latest = '{}.1'.format(file)
        count = 1
        while not_found:
            filename = '{}.{}'.format(file, count)
            if not self.naa.file_exists(family, project, ip, deliverable, bom, filename):
                not_found = False
                latest = filename                
            count = count + 1

        return latest                     

    def _get_opened_files(self, workspaceroot, project, ip, deliverable):
        '''
        Get opened files in workspaceroot/ip/deliverable
        '''
        results = []
        command = '{} opened {}/{}/{}/...'.format(self.icmp4, workspaceroot, ip, deliverable)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        for line in stdout.splitlines():
            m = re.match('\/\/depot\/gdpxl\/intel\/{}\/{}\/{}\/\S*?\/(.*)#.*-\s(.*?)\s.*'.format(project, ip,deliverable), line)
            if m:
                opened_file = m.group(1)
                operation = m.group(2)
                results.append((opened_file, operation))
        return results                    
        
    def _get_files_from_depotpath(self, depotpath, only_symlink_files=True):
        '''
        Get list of files in the given depotpath
        '''
        results = []
        command = '{} files {}'.format(self.icmp4, depotpath)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        for line in stdout.splitlines():
            ### if it is not a symlink, ignore
            ### https://jira.devtools.intel.com/browse/PSGDMX-1584
            if only_symlink_files and '(symlink' not in line:
                self.logger.debug("Skip non-symlink file: {}".format(line))
                continue

            m = re.match('(.*) -\s(.*?)\s.*', line)
            if m:
                file = m.group(1)
                operation = m.group(2)
                results.append((file, operation))
        return results        

    def _get_opened_file_depotpath(self, file):
        '''
        Get file's ICM depotpath
        '''
        depotpath = ''
        command = '{} opened {}'.format(self.icmp4, file)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        for line in stdout.splitlines():
            m = re.match('(.*?) -', line)
            if m:
                depotpath = m.group(1)
        return depotpath

    def _print_depotpath_content(self, depotpath):
        '''
        Prints content of an ICManage depotpath
        '''
        result = ''
        command = '{} print {}'.format(self.icmp4, depotpath)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stdout + stderr)
            raise SCMError('Failed to run {}'.format(command))
        if len(stdout.splitlines()) == 2:
            result = stdout.splitlines()[-1]
        
        return result

    def _get_tnr_patterns(self, ip, deliverable):
        '''
        returns ['ip/deliverable/audit/...', 'ip/deliverable/tnrwaivers.csv'] 
        '''
        return ['{}/{}/audit/...'.format(ip, deliverable), '{}/{}/tnrwaivers.csv'.format(ip, deliverable)]

    def validate_inputs(self, workspaceroot, project, ip, deliverable, library=None):
        '''
        Validate inputs and ensure inputs are valid
        '''
        # Ensure workspaceroot is an icm workspace
        if not self.cli.is_dir_an_icm_workspace(workspaceroot):
            raise SCMError('{} is not an ICManage workspace'.format(workspaceroot))
         # Ensure project exists
        if not self.cli.project_exists(project):
            raise SCMError('{} is not a valid project'.format(project))
        # Ensure ip exists
        if not self.cli.variant_exists(project, ip):
            raise SCMError('{}/{} is not a valid IP'.format(project, ip))
        # Ensure deliverable exists
        if not self.cli.libtype_exists(project, ip, deliverable):
            raise SCMError('{}/{}:{} is not a valid deliverable'.format(project, ip, deliverable))
        if library:            
            # Ensure library exists
            if not self.cli.library_exists(project, ip, deliverable, library):
                raise SCMError('{}/{}:{}/{} is not a valid library'.format(project, ip, deliverable, library))        

    def add_data(self, files, project, ip, deliverable, library, workspaceroot, family=None):
        '''
        Adds a new non-large data to ICM
        This API does not submit the files to ICManage, use submit_data to submit the files to ICM
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable, library=library)
        family = self.eco.get_family(os.getenv("DB_FAMILY")) if not family else family

        # Now we check-in files to ICManage
        for file in files:
            # Add file to ICmanage
            self._add_file_to_icm(file)

            self.logger.info('Marked {} as a new file'.format(file))

    def add_large_data(self, files, project, ip, deliverable, library, workspaceroot, family=None):
        '''
        Adds a new large data to NAA storage path:
        1. Copy src file from workspace to NAA storage
        2. Rename src file to file.tmp
        3. Creates a symlink from workspace to NAA
        4. Adds symlink to ICManage
        6. Removes the file.tmp from workspace

        This API does not submit the symlinks to ICManage, use submit_data to submit the symlinks to ICM

        NAA tag is library for mutable config and config for immutable config
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable, library=library)
        family = self.eco.get_family(os.getenv("DB_FAMILY")) if not family else family

        dict = {}
        for file in files:
            # Split workspaceroot from filepath
            filepath = os.path.abspath(file)
            m = re.match('{}/{}/{}/(.*)'.format(workspaceroot, ip, deliverable), filepath)
            if m:
                file = m.group(1)
            else:
                raise SCMError('Failed to retrieve filepath from {}'.format(filepath))
            # Split subdir from filename
            if '/' in file:
                filename = file.split('/')[-1]
                subdir = '/'.join(file.split('/')[:-1])
            else:
                filename = file
                subdir = None
            # Ensure file is not a symlink
            if os.path.islink(filepath):
                raise SCMError('{} is a symlink'.format(filepath))
            # Ensure file exists and is not a directory
            if not os.path.exists(filepath):
                raise SCMError('{} does not exist'.format(filepath))
            if os.path.isdir(filepath):
                raise SCMError('{} is a directory'.format(filepath))
            
            # Store subdir and the tuple (file, filepath) into dict
            if subdir not in dict:
                dict[subdir] = []
            dict[subdir].append((file, filepath))                

        # All checks end here. From here onwards, API will push data to NAA storage        
        naa_tmp_dir = self._get_naa_tmp_dir(workspaceroot, ip, deliverable)
        if not self.preview:
            os.mkdir(naa_tmp_dir)   

        new_filenames_dict = {}
        for subdir in dict:
            # First copy the files to be checked-in to naa_tmp_dir while preserving the nested dir
            if subdir == None:
                subdir_tmp = naa_tmp_dir
            else:   
                subdirs = subdir.split('/')             
                for num in range(0, len(subdirs)):
                    subdir_tmp = '{}/{}'.format(naa_tmp_dir, '/'.join(subdirs[:num+1]))
                    # If subdir_tmp does not exist, create it
                    if not self.preview:   
                        if not os.path.exists(subdir_tmp):
                            os.mkdir(subdir_tmp)               

            for file, filepath in dict[subdir]:
                new_filename = self._get_latest_naa_file(family, project, ip, deliverable, library, file)
                new_filenames_dict[new_filename] = (file, filepath)
                new_filepath = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, new_filename)
                
                if not self.preview:
                    # Rename file to new_filepath
                    os.rename(filepath, new_filepath)

                    # Move new_filepath to subdir
                    shutil.move(new_filepath, subdir_tmp)

        # Push file to NAA
        if self.naa.push_to_naa(family, project, ip, deliverable, library, naa_tmp_dir):
            # Restore files in .naa_tmp back to original location
            if not self.preview:
                original_dir = naa_tmp_dir.split('.naa_tmp')[0]
                for subdir in dict:
                    if subdir == None:
                        subdir_tmp = naa_tmp_dir
                    else:                
                        subdir_tmp = '{}/{}'.format(naa_tmp_dir, subdir)

                    for file in os.listdir(subdir_tmp):
                        filepath = '{}/{}'.format(subdir_tmp, file)
                        if not os.path.isdir(filepath):
                            original_filepath = '{}/{}/{}'.format(original_dir, '' if subdir == None else subdir, '.'.join(file.split('.')[:-1]))
                            os.rename(filepath, original_filepath)
                shutil.rmtree(naa_tmp_dir)
            raise SCMError('Failed to push {} to NAA'.format(naa_tmp_dir))
        self.logger.debug('{} successfully pushed to NAA'.format(naa_tmp_dir))
                                     
        # Now we check-in symlink to ICManage
        for new_filename in new_filenames_dict:
            file, filepath = new_filenames_dict[new_filename]
            file_naapath = self.naa.get_naa_path(family, project, ip, deliverable, library, new_filename)

            if not self.preview:
                # http://pg-rdjira:8080/browse/DI-1312
                # List the directory to refresh the directory, otherwise python might not be able to find the file...                
                os.listdir(os.path.dirname(file_naapath))            

                # Ensure file is present in NAA 
                if not os.path.exists(file_naapath):
                    raise SCMError('{} does not exist'.format(file_naapath))

                # Create a symlink from workspace to NAA path
                os.symlink(file_naapath, filepath)

            # Add symlink to ICmanage
            self._add_symlink_to_icm(filepath)

            self.logger.info('Marked {} as a new file'.format(filepath))

            # Symlink doesn't resolve immediately in the workspace, so we need to run a find command to refresh the path
            command = 'find {}'.format(file_naapath)
            run_command(command)

        # http://pg-rdjira:8080/browse/DI-1312
        # temp directory removal should be last
        # Removes naa_tmp_dir
        if not self.preview:
           shutil.rmtree(naa_tmp_dir)            

    def edit_data(self, files, project, ip, deliverable, workspaceroot):
        '''
        Edits an existing non-large data in NAA
        Runs 'icmp4 edit' on provided files
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable)
       
        files_to_edit = []
        for file in files:
            # Split workspaceroot from filepath
            filepath = os.path.abspath(file)
            m = re.match('{}/{}/{}/(.*)'.format(workspaceroot, ip, deliverable), filepath)
            if m:
                file = m.group(1)
            else:
                raise SCMError('Failed to retrieve filepath from {}'.format(filepath))

            # Ensure file is managed in ICM            
            if not self._is_file_managed(filepath):
                raise SCMError('{} is not managed in ICM'.format())                   
            files_to_edit.append((file, filepath))
            
        # All checks end here. From here onwards, API will check-out files from ICM
        for file, filepath in files_to_edit:
            try:
                # Mark symlink as edit 
                self._edit_file_in_icm(filepath)

                self.logger.info('{} checked-out in the current workspace'.format(file)) 
            except Exception as e:
                self.logger.error('Failed to check-out {}'.format(file))
                self.logger.debug(e)

    def edit_large_data(self, files, project, ip, deliverable, workspaceroot, copy_file=True):
        '''
        Edits an existing large data in NAA
        
        1. Mark symlink as edit in ICM (icmp4 edit)
        2. Remove symlink from workspace
        3. If copy_file is True, copy physical file from NAA to workspace

        This API does not submit the symlinks to ICManage, use submit_data to submit the symlinks to ICM
        NAA tag is library for mutable config and config for immutable config
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable)
       
        files_to_edit = []
        for file in files:
            # Split workspaceroot from filepath
            filepath = os.path.abspath(file)
            m = re.match('{}/{}/{}/(.*)'.format(workspaceroot, ip, deliverable), filepath)
            if m:
                file = m.group(1)
            else:
                raise SCMError('Failed to retrieve filepath from {}'.format(filepath))

            # Ensure file is a symlink
            if not os.path.islink(filepath):
                raise SCMError('{} is not a symlink'.format(filepath))
            # Ensure symlink is managed in ICM            
            if not self._is_file_managed(filepath):
                raise SCMError('{} is not managed in ICM'.format())                   
            files_to_edit.append((file, filepath))
            
        # All checks end here. From here onwards, API will check-out files from NAA storage
        for file, filepath in files_to_edit:
            try:
                # Mark symlink as edit 
                self._edit_symlink_in_icm(filepath)

                file_naapath = os.path.realpath(filepath)
                # Remove the symlink 
                if not self.preview:
                    os.remove(filepath)

                if copy_file:
                    dest_filename = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, file)
                    # Copy the naa file to workspace
                    if not self.preview:
                        shutil.copy(file_naapath, dest_filename)
                        
                        ### chmod 750 for all checked-out files
                        ### http://pg-rdjira:8080/browse/DI-1023
                        os.chmod(dest_filename, 0o750)

                self.logger.info('{} checked-out in the current workspace'.format(file)) 
            except Exception as e:
                self.logger.error('Failed to check-out {}'.format(file))
                self.logger.debug(e)                

    def submit_data(self, files, project, ip, deliverable, library, workspaceroot, desc='', family=None):
        '''
        Submits all opened non-large files found in path to ICManage        
        NAA tag is library for mutable config and config for immutable config
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable, library=library)

        family = self.eco.get_family(os.getenv("DB_FAMILY")) if not family else family

        # Get all opened files in workspace
        opened_files = self._get_opened_files(workspaceroot, project, ip, deliverable)
        # Filter opened files from a list of files we are supposed to submit
        # filtered_opened_files = [(opened_file, operation) for opened_file, operation in opened_files for file in files if opened_file in file]
        # http://pg-rdjira:8080/browse/DI-1023 (fixed the bug above)
        filtered_opened_files = []
        for f in files:
            for opened_file, operation in opened_files:
                if f.endswith(opened_file):
                    filtered_opened_files.append((opened_file, operation))
                    break

        # All checks end here. From here onwards, API will submit files to ICM
        if filtered_opened_files:
            desc = "Submitted by {}. Reasons: {}".format(os.getenv('USER'), 'Not given' if not desc else desc)
            # Create a changelist for each opened file to be submitted
            # First, get changelist spec
            changelist_spec = self._get_changelist_spec()

            # Remove file not supposed to be checked-in from changelist_spec
            new_spec = []
            found = False
            while changelist_spec:                    
                line = changelist_spec.pop(0)
                if not found:
                    if line.startswith('Description:'):
                        new_spec.append(line)
                        line = changelist_spec.pop(0)
                        new_spec.append('\t{}'.format(desc))
                    elif line.startswith('Files:'):
                        found = True
                        new_spec.append(line)
                    else:
                        new_spec.append(line)                        
                else:                    
                    for file, operation in filtered_opened_files:
                        if file in line:
                            new_spec.append(line)
                            break
            new_spec = '\n'.join(new_spec)                

            # Write spec to a physical file
            spec_file = '{}/spec.tmp.txt'.format(os.getcwd())
            if not self.preview:
                with open(spec_file, 'w') as f:
                    for line in new_spec:
                        f.write(line)

            # Create the pending changelist
            changelist_num = self._add_changelist_to_icm(spec_file)

            # Remove spec file
            if not self.preview:
                os.remove(spec_file)            
            
            # Submit the changelist to ICManage
            self._submit_to_icm(changelist_num)
            self.logger.info('Submitted change {} to ICManage'.format(changelist_num))
        else:
            self.logger.info('No opened files to submit')                      

    def submit_large_data(self, files, project, ip, deliverable, library, workspaceroot, desc='', family=None):
        '''
        Submits all opened large files found in path to ICManage        
        NAA tag is library for mutable config and config for immutable config
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable, library=library)

        family = self.eco.get_family(os.getenv("DB_FAMILY")) if not family else family

        # Get all opened files in workspace
        opened_files = self._get_opened_files(workspaceroot, project, ip, deliverable)
        # Filter opened files from a list of files we are supposed to submit
        # filtered_opened_files = [(opened_file, operation) for opened_file, operation in opened_files for file in files if opened_file in file]
        # http://pg-rdjira:8080/browse/DI-1023 (fixed the bug above)
        filtered_opened_files = []
        for f in files:
            for opened_file, operation in opened_files:
                if f.endswith(opened_file):
                    filtered_opened_files.append((opened_file, operation))
                    break

        # Get dict of files that we need to push for files that are edited
        dict = {}
        for file, operation in filtered_opened_files:
            filepath = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, file)
            if operation == 'edit':
                # Split subdir from filename
                if '/' in file:
                    filename = file.split('/')[-1]
                    subdir = '/'.join(file.split('/')[:-1])
                else:
                    filename = file
                    subdir = None

                # Ensure file is not a symlink
                if os.path.islink(filepath):
                    raise SCMError('{} is a symlink'.format(filepath))
                # Ensure file exists and is not a directory
                if not os.path.exists(filepath):
                    raise SCMError('{} does not exist'.format(filepath))
                if os.path.isdir(filepath):
                    raise SCMError('{} is a directory'.format(filepath))

                # Store subdir and the tuple (file, filepath) into dict
                if subdir not in dict:
                    dict[subdir] = []   
                dict[subdir].append((file, filepath))                          
            elif operation == 'add':
                # Ensure file is a symlink
                if not os.path.islink(filepath):
                    raise SCMError('{} is not a symlink'.format(filepath))
            elif operation == 'delete':
                # Nothing needs to be done for delete
                pass

        # All checks end here. From here onwards, API will push files to NAA storage
        # Only run NAA operation if there are files in the dict to be pushed
        if dict:
            naa_tmp_dir = self._get_naa_tmp_dir(workspaceroot, ip, deliverable)
    
            if not self.preview:
                os.mkdir(naa_tmp_dir)   

            new_filenames_dict = {}
            for subdir in dict:
                # First copy the files to be checked-in to naa_tmp_dir while preserving the nested dir
                if subdir == None:
                    subdir_tmp = naa_tmp_dir
                else:   
                    subdirs = subdir.split('/')             
                    for num in range(0, len(subdirs)):
                        subdir_tmp = '{}/{}'.format(naa_tmp_dir, '/'.join(subdirs[:num+1]))
                        # If subdir_tmp does not exist, create it
                        if not self.preview:   
                            if not os.path.exists(subdir_tmp):
                                os.mkdir(subdir_tmp)               

                for file, filepath in dict[subdir]:
                    new_filename = self._get_latest_naa_file(family, project, ip, deliverable, library, file)
                    new_filenames_dict[new_filename] = (file, filepath)
                    new_filepath = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, new_filename)
                    
                    if not self.preview:
                        # Rename file to new_filepath
                        os.rename(filepath, new_filepath)

                        # Move new_filepath to subdir
                        shutil.move(new_filepath, subdir_tmp)

            # Push file to NAA
            if self.naa.push_to_naa(family, project, ip, deliverable, library, naa_tmp_dir):
                # Restore files in .naa_tmp back to original location
                if not self.preview:
                    original_dir = naa_tmp_dir.split('.naa_tmp')[0]
                    for subdir in dict:
                        if subdir == None:
                            subdir_tmp = naa_tmp_dir
                        else:                
                            subdir_tmp = '{}/{}'.format(naa_tmp_dir, subdir)

                        for file in os.listdir(subdir_tmp):
                            filepath = '{}/{}'.format(subdir_tmp, file)
                            if not os.path.isdir(filepath):
                                original_filepath = '{}/{}/{}'.format(original_dir, '' if subdir == None else subdir, '.'.join(file.split('.')[:-1]))
                                os.rename(filepath, original_filepath)
                    shutil.rmtree(naa_tmp_dir)
                raise SCMError('Failed to push {} to NAA'.format(naa_tmp_dir))
            self.logger.debug('{} successfully pushed to NAA'.format(naa_tmp_dir))
                                         
            # Now we create the symlink to newpath in NAA
            for new_filename in new_filenames_dict:
                file, filepath = new_filenames_dict[new_filename]
                file_naapath = self.naa.get_naa_path(family, project, ip, deliverable, library, new_filename)

                # Create a symlink from workspace to NAA path
                if not self.preview:
                    # http://pg-rdjira:8080/browse/DI-1312
                    # List the directory to refresh the directory, otherwise python might not be able to find the file...                
                    os.listdir(os.path.dirname(file_naapath))

                    # Ensure file is present in NAA 
                    if not os.path.exists(file_naapath):
                        raise SCMError('{} does not exist'.format(file_naapath))

                    os.symlink(file_naapath, filepath)
                    
                # Symlink doesn't resolve immediately in the workspace, so we need to run a find command to refresh the path
                command = 'find {}'.format(file_naapath)
                run_command(command)                                    

            # http://pg-rdjira:8080/browse/DI-1312
            # temp directory removal should be last
            # Removes naa_tmp_dir
            if not self.preview:
               shutil.rmtree(naa_tmp_dir)                    
                            
        # Only submit files to ICM if there are files to be submitted
        if filtered_opened_files:
            desc = "Submitted by {}. Reasons: {}".format(os.getenv('USER'), 'Not given' if not desc else desc)
            # Create a changelist for each opened file to be submitted
            # First, get changelist spec
            changelist_spec = self._get_changelist_spec()

            # Remove file not supposed to be checked-in from changelist_spec
            new_spec = []
            found = False
            while changelist_spec:                    
                line = changelist_spec.pop(0)
                if not found:
                    if line.startswith('Description:'):
                        new_spec.append(line)
                        line = changelist_spec.pop(0)
                        new_spec.append('\t{}'.format(desc))
                    elif line.startswith('Files:'):
                        found = True
                        new_spec.append(line)
                    else:
                        new_spec.append(line)                        
                else:                    
                    for file, operation in filtered_opened_files:
                        if file in line:
                            new_spec.append(line)
                            break
            new_spec = '\n'.join(new_spec)                

            # Write spec to a physical file
            spec_file = '{}/spec.tmp.txt'.format(os.getcwd())
            if not self.preview:
                with open(spec_file, 'w') as f:
                    for line in new_spec:
                        f.write(line)

            # Create the pending changelist
            changelist_num = self._add_changelist_to_icm(spec_file)

            # Remove spec file
            if not self.preview:
                os.remove(spec_file)            
            
            # Submit the changelist to ICManage
            self._submit_to_icm(changelist_num)
            self.logger.info('Submitted change {} to ICManage'.format(changelist_num))
        else:
            self.logger.info('No opened files to submit')            
        
    def revert_data(self, files, project, ip, deliverable, workspaceroot):
        '''
        Revert an opened data from workspace
        This API can be used by both large and non-large data deliverable
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable)
        
        files_to_revert = []
        for file in files:
            # Split workspaceroot from filepath
            filepath = os.path.abspath(file)
            m = re.match('{}/{}/{}/(.*)'.format(workspaceroot, ip, deliverable), filepath)
            if m:
                file = m.group(1)
            else:
                raise SCMError('Failed to retrieve filepath from {}'.format(filepath))

            # Ensure file is already marked as checked out
            if not self._is_file_checked_out_in_this_workspace(filepath):
                raise SCMError('{} is not checked out'.format(filepath))

            files_to_revert.append((file, filepath))

        # All checks end here. From here onwards, API will revert files in the workspace
        for file, filepath in files_to_revert:                    
            # Revert opened file in ICM
            self._revert_file_in_workspace(filepath)

            self.logger.info('{} reverted'.format(file))

    def delete_data(self, files, project, ip, deliverable, workspaceroot):
        '''
        Mark data as deleted from workspace/repository
        This API can be used by both large and non-large data deliverable

        This API does not submit the change to ICManage, use submit_data to submit the change to ICM
        NAA tag is library for mutable config and config for immutable config
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable)
        
        files_to_delete = []
        for file in files:
            # Split workspaceroot from filepath
            filepath = os.path.abspath(file)
            m = re.match('{}/{}/{}/(.*)'.format(workspaceroot, ip, deliverable), filepath)
            if m:
                file = m.group(1)
            else:
                raise SCMError('Failed to retrieve filepath from {}'.format(filepath))

            # Ensure file is not checked out
            if self._is_file_checked_out_globally(filepath):
                raise SCMError('{} is checked out. File cannot be removed.'.format(filepath))

            files_to_delete.append((file, filepath))                
                    
        # All checks end here. From here onwards, API will delete files from repo
        for file, filepath in files_to_delete:                                 
            # Delete file
            self._delete_file_in_workspace(filepath)

            self.logger.info('{} marked for deletion'.format(file))

    def overlay_data(self, files_to_overlay, path_to_remove, project, ip, deliverable, deliverable_library, workspaceroot):
        '''
        Overlay files from source to dest

        * Deletes all files in path_to_remove via delete_action
        * Copies files listed in files_to_overlay from NAA storage to workspace
        * Check-in files listed in files_to_overlay to NAA via checkin_action
        '''
        self.logger.debug("""overlay_data:
            - files_to_overlay: {}
            - path_to_remove: {}
            - project: {}, ip: {}, deliverable: {}
            - deliverable_library: {}
            - workspaceroot: {}
        """.format(files_to_overlay, path_to_remove, project, ip, deliverable, deliverable_library, workspaceroot))
        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable)
        
        user = os.getenv('USER')                           
        date = datetime.datetime.today()            

        # Delete all files in path_to_remove from workspace via delete_action
        desc = 'Removing files as part of dmx overlay by {} on {}'.format(user, date)
        self.logger.debug(desc)
        self.delete_action(workspaceroot, [path_to_remove], ip=ip, deliverable=deliverable, desc=desc, project=project)

        for file in files_to_overlay:
            source_path = file
            m = re.match('.*\/{}\/{}\/{}\/.*?\/(.*)\.'.format(project, ip, deliverable), file)
            if m:
                dest_path = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, m.group(1))
            else:
                raise SCMError('Failed to get dest_path of {}'.format(source_path))

            dest_dir = '/'.join(dest_path.split('/')[:-1])

            # Create the dest directory in the workspace
            self._create_directory(dest_dir)
            
            # Copy the file from source to dest
            self._copy_file(source_path, dest_path)

        # Check-in all files via checkin_action        
        desc = 'Checking-in files as part of dmx overlay by {} on {}'.format(user, date)    
        # Since we have removed everything under large data deliverable directory, it is safe to assume to check-in everything in that path
        checkin_path = '{}/{}/...'.format(ip, deliverable)
        self.logger.debug(desc)
        self.checkin_action(workspaceroot, [checkin_path], ip=ip, deliverable=deliverable, desc=desc, project=project)

    def overlay_workspace_data(self, files_to_overlay, path_to_remove, project, ip, deliverable, deliverable_library, workspaceroot):
        '''
        Overlay files from workspace to depot

        * Deletes all files in path_to_remove via delete_action
        * Check-in files listed in files_to_overlay to NAA via checkin_action
        '''
        self.logger.debug("""overlay_workspace_data()
        - files_to_overlay: {}
        - path_to_remove: {}
        - project/ip/deliverable:  {}/{}/{}
        - deliverable_library: {}
        - workspaceroot: {}
        """.format(files_to_overlay, path_to_remove, project, ip, deliverable, deliverable_library, workspaceroot))

        workspaceroot = os.path.realpath(workspaceroot)
        self.validate_inputs(workspaceroot, project, ip, deliverable)
        
        user = os.getenv('USER')                           
        date = datetime.datetime.today()            

        # Delete all files in path_to_remove from workspace via delete_action
        # Since we are only removing the files from server end, we will not call delete_action
        # Instead we simply run "icmp4 delete -k"
        if files_to_overlay:
            desc = 'Removing files as part of dmx overlay by {} on {}'.format(user, date)
            if self._delete_file_in_depot(path_to_remove):
                if self._have_opened_files(path_to_remove):
                    self._submit_to_icm(description=desc, filespec=path_to_remove)

            # Check-in all files via checkin_action        
            desc = 'Checking-in files as part of dmx overlay by {} on {}'.format(user, date)    
            self.checkin_action(workspaceroot, files_to_overlay, ip=ip, deliverable=deliverable, desc=desc)

    def _have_opened_files(self, filespec):
        ret = 1
        cmd = '{} opened {}'.format(self.icmp4, filespec)
        exitcode, stdout, stderr = run_command(cmd)
        self.logger.debug('cmd: {}\nexitcode: {}\nstdout: {}\nstderr: {}\n'.format(cmd, exitcode, stdout, stderr))
        syntax = 'not opened on this client' 
        if syntax in stdout or syntax in stderr:
            return False
        return True

    def derive_data(self, files, project, ip, deliverable, workspaceroot, source_library, dest_library, family=None):
        '''
        '''
        workspaceroot = os.path.realpath(workspaceroot)
        if not self.preview:
            self.validate_inputs(workspaceroot, project, ip, deliverable)
            family = self.eco.get_family(os.getenv("DB_FAMILY")) if not family else family
        
        filenames_to_derive = []
        for file, symlink in files:            
            # Ensure file is in NAA storage
            if not file.startswith(self.naa.naa_basepath):
                raise SCMError('{} is not a file in NAA storage'.format(file))
            subdir = '/'.join(symlink.split('/')[:-1])
            if subdir:
                filename_to_derive = '{}/{}'.format(subdir, file.split('/')[-1])
            else:
                filename_to_derive = file.split('/')[-1]
            filenames_to_derive.append((filename_to_derive, symlink))
    
        # All checks end here. From here onwards, API will derive files from source_library to dest_library
        # Clone tag in NAA
        tmp_file = '{}/.naa_clone_filename.txt'.format(os.getcwd())
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        with open(tmp_file, 'w') as f:
            for file, symlink in filenames_to_derive:
                f.write('{}\n'.format(file))                
        if self.naa.clone_tag(family, project, ip, deliverable, source_library, tmp_file, dest_library):
            raise SCMError('Failed to clone from {} to {} in NAA'.format(source_library, dest_library))
        self.logger.debug('{} successfully clone to {} in NAA'.format(source_library, dest_library))
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        
        if not self.preview:                             
            os.chdir('{}/{}'.format(ip, deliverable))                                     
        for filename_to_derive, symlink in filenames_to_derive:
            if not self.preview:
                dest_naapath = self.naa.get_naa_path(family, project, ip, deliverable, dest_library, filename_to_derive)

                # Create the subdir            
                subdir = '/'.join(symlink.split('/')[:-1])
                if subdir:
                    if not os.path.exists(subdir):
                        os.makedirs(subdir)
            
                # Create a symlink from workspace to NAA path
                os.symlink(dest_naapath, symlink)

            # Add symlink to ICManage
            self._add_symlink_to_icm(symlink)
            self.logger.info('Marked {} as a new file'.format(symlink))

        # Only submit if there are files to derive
        # Submit will run into errors if changelists is empty
        if filenames_to_derive:
            desc = 'Checked in files as part derive from {} to {} by {}'.format(source_library, dest_library, os.getenv('USER'))
            self._submit_to_icm(description=desc)
                        
    def validate_workspace(self, cwd, file='', manifest=False, ip='', deliverable='', config=False, project=''):
        '''
        Check if current working directory (cwd) is an ICManage workspace
        Determine ip and deliverable from cwd if not given
        Returns tuple of (icmws, ip, deliverable)
        '''
        # Ensure we are in an icm workspace
        if not self.cli.is_dir_an_icm_workspace(cwd):
            raise SCMError('{} is not an ICManage workspace'.format(cwd))
        # Get workspace information
        icmws = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(cwd)
        workspaceroot = icmws._workspaceroot
        family = self.eco.get_family(os.getenv("DB_FAMILY"))
        # Flag to define that the workspace is a simple workspace (created from simple configuration)            
        is_simple = True if icmws._attributesAlwaysAccessViaMethod['LibType'] else False

        # chdir to the workspaceroot
        os.chdir(workspaceroot)
        if file:
            # If file is given, ignore ip and deliverable var
            # Grep ip and deliverable from <cwd>/<file>
            # http://pg-rdjira:8080/browse/DI-1201
            # Get the abspath of file 
            file_path = os.path.abspath('{}/{}'.format(cwd, file))
            subdir = ''
            m = re.match('{}/(.*?)/(.*?)/.*'.format(workspaceroot), file_path)
            if m:
                ip = m.group(1)
                deliverable = m.group(2)
            else:
                raise SCMError('Failed to get IP and deliverable from <cwd>/<file>. Please ensure that file given exists.(workspaceroot:{}, file_path:{})'.format(workspaceroot, file_path))
        if manifest or config:                
            # If ip is not given, look for ip in cwd
            if not ip:
                m = re.match('{}\/(.*)'.format(workspaceroot), os.path.realpath(cwd))
                if m:
                    ip = m.group(1).split('/')[0]
                else:
                    raise SCMError('Failed to get IP from workspace path. Please ensure that -i is provided, or CD into an IP directory of the workspace.')       
            # If deliverable is not given, look for deliverable in cwd
            if not deliverable:
                m = re.match('{}\/{}\/(.*)'.format(workspaceroot, ip),os.path.realpath(cwd))
                if m:
                    deliverable = m.group(1).split('/')[0]
                else:
                    raise SCMError('Failed to get deliverable from workspace path. Please ensure that -d is provided or CD into a deliverable directory of the workspace.')        

        # Ensure IP is part of the workspace
        if is_simple:
            # NOTE: ICManageWorkspace does not support simple workspace. This is only a workaround so that scm commands and overlay may work with simple workspace
            # This should be revisited in the future if ICManageWorkspace should support simple workspace
            if ip != str(icmws.ipName):
                raise SCMError('{} is not present in this workspace'.format(ip))
        else:            
            if ip not in icmws.get_ips():
                raise SCMError('{} is not present in this workspace'.format(ip))
        # Ensure IP@deliverable is part of the workspace
        if is_simple:
            # NOTE: ICManageWorkspace does not support simple workspace. This is only a workaround so that scm commands and overlay may work with simple workspace
            # This should be revisited in the future if ICManageWorkspace should support simple workspace
            if deliverable != str(icmws._attributesAlwaysAccessViaMethod['LibType']):
                raise SCMError('{}@{} is not present in this workspace'.format(ip, deliverable))
        else:
            if deliverable not in icmws.get_deliverables(ip):
                raise SCMError('{}@{} is not present in this workspace'.format(ip, deliverable))
        
        if not project:
            project = icmws.get_project_of_ip(ip)

        # Ensure that the config for the ip@deliverable is mutable
        try:
            if is_simple:
                # If workspace is simple, we build our own configuration object
                # This is because ICManageWorkspace does not support simple workspace fully
                cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, ip, str(icmws._configurationName), libtype=deliverable)
                if cf.is_library():
                    deliverable_bom = str(cf.library)
                else:
                    deliverable_bom = str(cf.lib_release)
                #deliverable_bom = str(dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, ip, str(icmws._configurationName), libtype=deliverable).)
            else:                    
                #deliverable_bom = str([x['Configuration'] for x in icmws.configurations if 'LibType' in x if x['Variant']==ip and x['LibType']==deliverable][0])
                deliverable_bom = str([x['config'] for x in icmws.configurations if 'libtype' in x if x['variant']==ip and x['libtype']==deliverable][0])
        except:
            raise SCMError('Failed to get BOM of {}:{}'.format(ip, deliverable))
        if deliverable_bom.startswith('REL') or deliverable_bom.startswith('snap'):
            raise SCMError('{}:{}@{} is an immutable BOM'.format(ip, deliverable, deliverable_bom))
        # Ensure that the library for the ip@deliverable is ActiveDev
        [library, release] = self.cli.get_library_release_from_libtype_config(project, ip, deliverable, deliverable_bom)
        #if self.cli.get_configs_release(project, ip, deliverable, deliverable_bom) != '#ActiveDev':
        if library != '#ActiveDev' and release is not None:
            raise SCMError('{}:{}@{}\' library is not ActiveDev'.format(ip, deliverable, deliverable_bom))                        

        # http://pg-rdjira:8080/browse/DI-1272
        # Now we have the ip and deliverable that we need to perform scm command
        # Ensure that the library for ip/deliverable is the same as the library in the configuration used by the workspace, ergo: workspace is updated for this library
        is_updated = False if 'notupdated' in icmws._attributesAlwaysAccessViaMethod['Attr'] else True
        if not is_updated:
            # Check if the ip/deliverable that we are running scm commands are updated
            latest_library_in_bom = self.cli.get_config(project, ip , deliverable_bom, libtype=deliverable)['library']
            workspace_library_info = self.cli.get_workspace_library_info(workspaceroot)
            for library_info in workspace_library_info:
                if project == library_info['project'] and ip == library_info['variant'] and deliverable == library_info['libtype']:
                    library_in_workspace = library_info['library']
                    break
            else:
                raise SCMError('Failed to find library info from "icmp4 library" for {}'.format(workspaceroot))

            if latest_library_in_bom == library_in_workspace:
                # If the library is identical, we allow scm proceed and warn user to run update for other deliverables
                self.logger.warning('This workspace is not updated to the latest BOM definition but does not hinder current SCM operation. Please update the workspace after SCM command has completed.')
            else:
                # If the library is not identical, disallow scm to proceed
                raise SCMError('{}/{} library for this workspace ({}) is not identical to the library of the BOM used by the workspace ({}). Please update the workspace before running SCM command.'.format(ip, deliverable, library_in_workspace, latest_library_in_bom))
        
        return (icmws, ip, deliverable)

    def get_manifest_files(self, workspaceroot, ip, deliverable, family, cells=[], project=''): 
        '''
        Return files defined in manifest that exist in the workspace
        '''
        patterns = []
        files = []
        if cells:
            for cell in cells:
                patterns = patterns + list(family.get_ip(ip, project_filter=project).get_deliverable(deliverable).get_patterns(ip=ip, cell=cell).keys())
        else:
            patterns = list(family.get_ip(ip, project_filter=project).get_deliverable(deliverable).get_patterns(ip=ip, cell='*').keys())
        patterns += self._get_tnr_patterns(ip, deliverable)
        patterns = sorted(list(set(patterns)))
        

        # Get physical files that exist in workspace that match the patterns
        for pattern in patterns:
            walk_files = []
            filepath = '{}/{}'.format(workspaceroot, pattern)
            if '...' in filepath:
                filepath = filepath.replace('...', '')
                #filepath = filepath.replace('...', '*')
                #print(filepath)
                for root, dirs, wfiles in os.walk(filepath):
                    for name in wfiles:
                        walk_files.append(os.path.join(root, name))
                #print(walk_files)
                files = files + walk_files
            else:
                filepath = filepath.replace('...', '*')
                files = files + glob.glob(filepath)
            #files = files + glob.glob(filepath)
        files = sorted(list(set(files)))
        
        return files         

    def checkout_action(self, cwd, filespec=[], manifest=False, ip='', deliverable='', cells=[]):
        '''
        For existing files managed in ICManage, mark the files as edit and copy the files 
        from NAA to workspace
        '''
        # Ensure at least filespec or manifest is given
        if not filespec and not manifest:
            raise SCMError('Filespec or --manifest needs to be specified.')

        # Why do we need such bad coding?
        # This is to ensure that any filespec given together with manifest is properly checked if the filespec comes from the same deliverable as manifest
        # We do not allow user to mixmatch a deliverable manifest with file from another deliverable
        if manifest:        
            filespec.append('')
        ip_del = []    
        for file in filespec:
            (icmws, ip_tmp, del_tmp) = self.validate_workspace(cwd, file=file, manifest=manifest, ip=ip, deliverable=deliverable)
            if ip_del:
                if (ip_tmp, del_tmp) not in ip_del:
                    raise SCMError('Filespec(s) provided must come from the same ip/deliverable')
            else:
                ip_del.append((ip_tmp, del_tmp))
        ip = ip_tmp
        deliverable = del_tmp
        workspaceroot = icmws._workspaceroot
        project = str(icmws._projectName)
        workspacename = str(icmws._attributesAlwaysAccessViaMethod['Workspace'])
        family = self.eco.get_family(os.getenv("DB_FAMILY"))
        is_large = family.get_ip(ip, icmws.get_project_of_ip(ip)).get_deliverable(deliverable).large

        files = []
        if filespec:
            for file in filespec:
                # Get files defined by file pattern
                # http://pg-rdjira:8080/browse/DI-1184
                # Add support for fullpath
                if file.startswith('/p/'):
                    m = re.match('(.*)\/(.*)'.format(), file)
                    if m:
                        file_dir = os.path.realpath(m.group(1))
                        file_name = m.group(2)
                        file = os.path.join(file_dir, file_name)
                    else:
                        raise SCMError('Failed to get directory and filename from {}'.format(file))
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file.startswith('/nfs/'):
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file == '':
                    continue
                else:
                    pattern = '{}/{}'.format(cwd, file)
                patterns = self._glob_perforce_pattern_for_checkout(pattern)

                for perforcefile, version, operation in patterns:
                    # For safety, we skip .icminfo file
                    # .icminfo aren't allowed to be opened
                    if perforcefile.endswith('.icminfo'):
                        continue                    
                    # Get filepath
                    m = re.match('\/\/depot\/gdpxl\/intel\/{}\/{}\/{}\/.*?/(.*)'.format(project, ip, deliverable), perforcefile)
                    if m:
                        physfile = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, m.group(1))
                        # Skip files already opened by others
                        if 'can\'t edit' not in operation:
                            files.append(physfile)
        if manifest:                        
            files = files + self.get_manifest_files(workspaceroot, ip, deliverable, family, cells=cells, project=icmws.get_project_of_ip(ip))

        if is_large:
            # Find if files are NAA managed
            # http://pg-rdjira:8080/browse/DI-1086
            managed_files = [x for x in files if self._is_file_naa_managed(x)]
            self.logger.debug("Ignoring non-naa files: {}".format(set(files) - set(managed_files)))

            # Find files that are not checked out
            unchecked_out_files = [x for x in managed_files if not self._is_file_checked_out_globally(x)]

            # Filter only symlinks
            # Theoretically, at this stage, all files in the list should be symlinks
            files_to_checkout = [x for x in unchecked_out_files if os.path.islink(x)]
            self.logger.debug("Ignoring non-symlink files: {}".format(set(unchecked_out_files) - set(files_to_checkout)))
        else:
            # Find if files are managed in ICM
            managed_files = [x for x in files if self._is_file_managed(x)]

            # Find files that are not checked out
            files_to_checkout = [x for x in managed_files if not self._is_file_checked_out_globally(x)]

        if files_to_checkout:
            # Sync each unchecked_out_file to workspace
            # http://pg-rdjira:8080/browse/DI-1272
            # Do not update workspace on behalf of users when syncing files to be checked-out
            self.cli.sync_workspace(workspacename, skeleton=False, specs=files_to_checkout, force=True, skip_update=True)
            try:
                # Mark unchecked_out_files as edit   
                if is_large:
                    self.edit_large_data(files_to_checkout, project, ip, deliverable, workspaceroot)
                else:
                    self.edit_data(files_to_checkout, project, ip, deliverable, workspaceroot)
            except Exception as e:
                self.logger.error(e)
                raise SCMError('Please ensure that files are already checked-in or not already checked-out from previous check-out.')                
        else:
            self.logger.info('No files to check-out. Some files might have already been checked-out. ') 
            self.logger.info("You may take a look on following BKM - https://wiki.ith.intel.com/pages/viewpage.action?pageId=826455987#id-2.1.4ICManageFAQ-Unabletocheckoutorcheckinfilesusing'dmxscm'command(INFO:Nofilestocheck-out.Somefilesmighthavealreadybeenchecked-out/INFO:Nofilestocheck-in.)") 
    
    def checkin_action(self, cwd, filespec=[], manifest=False, ip='', deliverable='', cells=[], desc='', config='', project=''):
        '''
        For each file in manifest that exists in the workspace:
        * If the file is opened in workspace (has been checked-out previously), submit the files
        * If the file is not opened in workspace and exist in NAA, do nothing
        * If the file is not opened in workspace and does not exist in NAA, add and submit the files
        '''
        self.logger.debug("""checkin_action:-
        - cwd: {}
        - filespec: {}
        - manifest: {}
        - ip:{}, deliverable: {}, cells: {}
        - desc: {}
        - config: {}, project: {}
        """.format(cwd, filespec, manifest, ip, deliverable, cells, desc, config, project))
        # Ensure at least file or manifest is given
        if not filespec and not manifest and not config:
            raise SCMError('Filespec, --manifest or --cfg needs to be specified.')
        if config:
            if filespec or manifest:
                raise SCMError('--cfg cannot be provided together with filespec or --manifest.')
            config = os.path.realpath(config)
            if not os.path.isfile(config):
                raise SCMError('Configuration file {} does not exist.'.format(config))

        # Why do we need such bad coding?
        # This is to ensure that any filespec given together with manifest is properly checked if the filespec comes from the same deliverable as manifest
        # We do not allow user to mixmatch a deliverable manifest with file from another deliverable
        if manifest or config:        
            filespec.append('')
        ip_del = []    
        for file in filespec:
            (icmws, ip_tmp, del_tmp) = self.validate_workspace(cwd, file=file, manifest=manifest, ip=ip, deliverable=deliverable, config=True if config else False, project=project)
            if ip_del:
                if (ip_tmp, del_tmp) not in ip_del:
                    raise SCMError('Filespec(s) provided must come from the same ip/deliverable')
            else:
                ip_del.append((ip_tmp, del_tmp))
        ip = ip_tmp
        deliverable = del_tmp
        workspaceroot = icmws._workspaceroot
        if not project:
            project = icmws.get_project_of_ip(ip)
            #project = str(icmws._projectName)
        family = self.eco.get_family(os.getenv("DB_FAMILY"))
        is_large = family.get_ip(ip, icmws.get_project_of_ip(ip)).get_deliverable(deliverable).large
        ws_config = str(icmws.configurationName)
        deliverable_library = None

        try:
            #print project, ip, deliverable, ws_config
            for x in icmws.configurations :
                if 'libtype' in x and x['variant']==ip and x['libtype']==deliverable and x['type'] == 'library':    
                    deliverable_library = x['name']
            if not deliverable_library:
                deliverable_library = self.cli.get_libtype_config_details(project, ip, deliverable, ws_config, retkeys=['name'])
           # deliverable_library = str([x['Library'] for x in icmws.configurations if 'LibType' in x if x['Variant']==ip and x['LibType']==deliverable][0])        
        except :
            raise SCMError('Failed to get library of {}:{}'.format(ip, deliverable))

        files = []
        if filespec:
            for file in filespec:
                # Get files defined by file pattern
                # http://pg-rdjira:8080/browse/DI-1184
                # Add support for fullpath
                if file.startswith('/p/'):
                    m = re.match('(.*)\/(.*)'.format(), file)
                    if m:
                        file_dir = os.path.realpath(m.group(1))
                        file_name = m.group(2)
                        file = os.path.join(file_dir, file_name)
                    else:
                        raise SCMError('Failed to get directory and filename from {}'.format(file))
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file.startswith('/nfs/'):
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file == '':
                    continue
                else:
                    pattern = '{}/{}'.format(cwd, file)

                patterns = self._glob_perforce_pattern_for_checkin(pattern)
                skip = False
                for physfile, operation, perforcefile in patterns:
                    skip = False
                    # Skip delete operation for now
                    if 'delete' in operation:
                        skip = True
                    # Skip excluded files
                    for excluded_file in EXCLUDED_FILES:
                        if perforcefile.endswith(excluded_file):
                            skip = True
                    # Skip excluded dirs
                    for excluded_dir in EXCLUDED_DIRS:
                        if excluded_dir in perforcefile:
                            skip = True
                    if not skip:                        
                        files.append(physfile)

        if manifest:                                
            files = files + self.get_manifest_files(workspaceroot, ip, deliverable, family, cells=cells, project=icmws.get_project_of_ip(ip))

        if config:
            with open(config) as cfgfile:
                lines = cfgfile.readlines()
                # Removed commented lines
                lines = [x for x in lines if '#' not in x and not x.startswith('//')]

            for line in lines:
                pattern, status = line.split()
                pattern_ip, pattern_del = pattern.split('/')[:2]
                if pattern_ip != ip or pattern_del != deliverable:
                    continue
                required = True if 'required' in status else False
                # Get physical files that exist in workspace that match the patterns
                filepath = '{}/{}'.format(workspaceroot, pattern)
                filepath = filepath.replace('...', '*')
                ws_files = glob.glob(filepath)
                if required and not ws_files:
                    raise SCMError('No files found for {}. At least a single file is required to be checked-in.'.format(pattern))
                files = files + ws_files
            files = sorted(list(set(files))) 

        # Find if files are unmanaged in ICM
        unmanaged_files = [x for x in files if not self._is_file_managed(x)]

        # http://pg-rdjira:8080/browse/DI-1019
        # Look for files that are not opened but already managed
        managed_not_opened_files = [x for x in files if not self._is_file_checked_out_in_this_workspace(x) and self._is_file_managed(x)]
        if managed_not_opened_files:
            self.logger.warning('The following file(s) already checked-in to repository:')
            for file in managed_not_opened_files:
                self.logger.warning('* {}'.format(file))
            self.logger.warning('Please run icmp4 sync or dmx workspace sync to sync the latest file(s) from repository.')
        # To prevent submit_data from running a NAA job when there are no files to push, substract managed_not_opened_files from files
        files = list(set(files) - set(managed_not_opened_files))

        if is_large:
            # Find total file size
            total_file_size = 0
            for file in files:
                file_size = os.path.getsize(file)
                total_file_size = total_file_size + file_size
            # 200MB/min
            # 209715200bytes = 1min
            eta = old_div(total_file_size,209715200)
                                                  
        # Add unmanaged_files
        if unmanaged_files:
            if is_large:
                self.add_large_data(unmanaged_files, project, ip, deliverable, deliverable_library, workspaceroot, family=family)
            else:                
                self.add_data(unmanaged_files, project, ip, deliverable, deliverable_library, workspaceroot, family=family)

        # Submit all opened files to ICM
        if files:    
            try:
                if is_large:
                    self.submit_large_data(files, project, ip, deliverable, deliverable_library, workspaceroot, desc=desc, family=family)
                else:
                    self.submit_data(files, project, ip, deliverable, deliverable_library, workspaceroot, desc=desc, family=family)
            except Exception as e:
                self.logger.error(e)
                raise SCMError('Please ensure that files are checked-out first before trying to check-in.')
            if is_large:
                self.logger.info('Files are now available locally, however, it will take approximately {} minutes for the files to be available in remote site.'.format(eta))
        else:
            self.logger.info('No files to check-in')            
        
    def revert_action(self, cwd, filespec=[], manifest=False, ip='', deliverable='', cells=[], unchanged=False):
        '''
        For each opened file in manifest that exists in the workspace:
        * If the file is opened in workspace (has been checked-out previously), revert the file
        '''
        # Ensure at least file or manifest is given
        if not filespec and not manifest:
            raise SCMError('Filespec or --manifest needs to be specified.')
        # Why do we need such bad coding?
        # This is to ensure that any filespec given together with manifest is properly checked if the filespec comes from the same deliverable as manifest
        # We do not allow user to mixmatch a deliverable manifest with file from another deliverable
        if manifest:        
            filespec.append('')
        ip_del = []    
        for file in filespec:
            (icmws, ip_tmp, del_tmp) = self.validate_workspace(cwd, file=file, manifest=manifest, ip=ip, deliverable=deliverable)
            if ip_del:
                if (ip_tmp, del_tmp) not in ip_del:
                    raise SCMError('Filespec(s) provided must come from the same ip/deliverable')
            else:
                ip_del.append((ip_tmp, del_tmp))
        ip = ip_tmp
        deliverable = del_tmp
        workspaceroot = icmws._workspaceroot
        project = str(icmws._projectName)
        family = self.eco.get_family(os.getenv("DB_FAMILY"))
                    
        files = []
        # File bypasses manifest
        if filespec:
            for file in filespec:
                # http://pg-rdjira:8080/browse/DI-1184
                # Add support for fullpath
                if file.startswith('/p/'):
                    m = re.match('(.*)\/(.*)'.format(), file)
                    if m:
                        file_dir = os.path.realpath(m.group(1))
                        file_name = m.group(2)
                        file = os.path.join(file_dir, file_name)
                    else:
                        raise SCMError('Failed to get directory and filename from {}'.format(file))
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file.startswith('/nfs/'):
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file == '':
                    continue
                else:
                    pattern = '{}/{}'.format(cwd, file)
                patterns = self._glob_perforce_pattern_for_revert(pattern)
                for perforcefile, version, operation in patterns:
                    # For safety, we skip .icminfo file
                    # .icminfo aren't allowed to be opened
                    if perforcefile.endswith('.icminfo'):
                        continue
                    # Get filepath
                    m = re.match('\/\/depot\/gdpxl\/intel\/{}\/{}\/{}\/.*?/(.*)'.format(project, ip, deliverable), perforcefile)
                    if m:
                        physfile = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, m.group(1))
                        files.append(physfile)
        if manifest:  
            files = files + self.get_manifest_files(workspaceroot, ip, deliverable, family, cells=cells, project=icmws.get_project_of_ip(ip))

        # Find if files are managed in ICM
        managed_files = [x for x in files if self._is_file_managed(x)]

        # Find files that are checked out in this workspace
        checked_out_files = [x for x in managed_files if self._is_file_checked_out_in_this_workspace(x)]

        files_to_revert = []
        # If --unchanged is specified, diff the file in workspace and the file in repo
        # If they are the same, schedule them for revert. Otherwise, ignore.
        if unchanged:
            for file in checked_out_files:
                file_depotpath = self._get_opened_file_depotpath(file)
                file_naapath = self._print_depotpath_content(file_depotpath)
                if not self._is_file_diff(file, file_naapath):
                    files_to_revert.append(file)
        else:
            files_to_revert = checked_out_files                  
                             
        if files_to_revert:
            # Revert the files
            try:
                self.revert_data(files_to_revert, project, ip, deliverable, workspaceroot)
            except Exception as e:
                self.logger.error(e)
                raise SCMError('Please ensure that files are checked-out first before trying to revert them.')
        else:
            self.logger.info('No files to revert.')

    def delete_action(self, cwd, filespec=[], manifest=False, ip='', deliverable='', cells=[], desc='', project=''):
        '''
        * Delete the file (must not be checked-out) in the workspace/repository
        '''
        self.logger.debug("""delete_action:
        - cwd: {}
        - filespec: {}
        - manifest: {}, ip: {}, deliverable: {}
        - cells: {}
        - desc: {}
        - project: {}
        """.format(cwd, filespec, manifest, ip, deliverable, cells, desc, project))
        # Ensure at least file or manifest is given
        if not filespec and not manifest:
            raise SCMError('Filespec or --manifest needs to be specified.')
        # Why do we need such bad coding?
        # This is to ensure that any filespec given together with manifest is properly checked if the filespec comes from the same deliverable as manifest
        # We do not allow user to mixmatch a deliverable manifest with file from another deliverable
        if manifest:        
            filespec.append('')
        ip_del = []    
        for file in filespec:
            (icmws, ip_tmp, del_tmp) = self.validate_workspace(cwd, file=file, manifest=manifest, ip=ip, deliverable=deliverable, project=project)
            if ip_del:
                if (ip_tmp, del_tmp) not in ip_del:
                    raise SCMError('Filespec(s) provided must come from the same ip/deliverable')
            else:
                ip_del.append((ip_tmp, del_tmp))
        ip = ip_tmp
        deliverable = del_tmp
        workspaceroot = icmws._workspaceroot
        if not project:
            project = icmws.get_project_of_ip(ip)
            #project = str(icmws._projectName)
        config = str(icmws.configurationName)
        family = self.eco.get_family(os.getenv("DB_FAMILY"))                            
        is_large = family.get_ip(ip, icmws.get_project_of_ip(ip)).get_deliverable(deliverable).large
        self.logger.debug("is_large: {}".format(is_large))
        deliverable_library = None

        try:
            for x in icmws.configurations :
                if 'libtype' in x and x['variant']==ip and x['libtype']==deliverable and x['type'] == 'library':    
                    deliverable_library = x['name']
            if not deliverable_library:
                deliverable_library = self.cli.get_libtype_config_details(project, ip, deliverable, config, retkeys=['name'])
        except :
            raise SCMError('Failed to get library of {}:{}'.format(ip, deliverable))

        files = []
        # File bypasses manifest
        if filespec:
            for file in filespec:
                # http://pg-rdjira:8080/browse/DI-1184
                # Add support for fullpath
                if file.startswith('/p/'):
                    m = re.match('(.*)\/(.*)'.format(), file)
                    if m:
                        file_dir = os.path.realpath(m.group(1))
                        file_name = m.group(2)
                        file = os.path.join(file_dir, file_name)
                    else:
                        raise SCMError('Failed to get directory and filename from {}'.format(file))
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file.startswith('/nfs/'):
                    m = re.match(cwd, file)
                    if m:
                        pattern = file
                    else:
                        pattern = '{}/{}'.format(cwd, file)
                elif file == '':
                    continue
                else:
                    pattern = '{}/{}'.format(cwd, file)
                patterns = self._glob_perforce_pattern_for_delete(pattern)
                self.logger.debug("pattern: {}, patterns: {}".format(pattern, patterns))
                for perforcefile, version, operation in patterns:
                    # For safety, we skip .icminfo file
                    # .icminfo aren't allowed to be opened
                    if perforcefile.endswith('.icminfo'):
                        continue
                    # Get filepath
                    m = re.match('\/\/depot\/gdpxl\/intel\/{}\/{}\/{}\/.*?/(.*)'.format(project, ip, deliverable), perforcefile)
                    if m:
                        physfile = '{}/{}/{}/{}'.format(workspaceroot, ip, deliverable, m.group(1))
                        files.append(physfile)
        if manifest:                    
            files = files + self.get_manifest_files(workspaceroot, ip, deliverable, family, cells=cells, project=icmws.get_project_of_ip(ip))

        # Find if files are managed in ICM
        self.logger.debug("files:{}".format(files))
        managed_files = [x for x in files if self._is_file_managed(x)]
        self.logger.debug("managed_files:{}".format(managed_files))

        # Find files remove (must not be checked out previously)
        files_to_remove = [x for x in managed_files if not self._is_file_checked_out_globally(x)]
        self.logger.debug("files_to_remove: {}".format(files_to_remove))

        if files_to_remove:
            # Delete the files
            self.delete_data(files_to_remove, project, ip, deliverable, workspaceroot)
            
            # Submit to repository
            if is_large:
                self.submit_large_data(files_to_remove, project, ip, deliverable, deliverable_library, workspaceroot, desc=desc, family=family)
            else:
                self.submit_data(files_to_remove, project, ip, deliverable, deliverable_library, workspaceroot, desc=desc, family=family)
        else:
            self.logger.info('No files to delete.')            


    def overlay_action(self, workspaceroot, ip, deliverable, source_path, dest_path, project=''):
        '''
        This is the overlay remote mode that works by copying files from source depotpath to dest depotpath
        source_path is ICManage depot path
        dest_path is ICManage depot path
        Overlay files from a source path to a dest path
        '''
        icmws, ip, deliverable = self.validate_workspace(workspaceroot, ip=ip, deliverable=deliverable, project=project)
        self.logger.debug("icmws, ip, deliverable: {}, {}, {}".format(icmws, ip, deliverable))
        workspaceroot = icmws._workspaceroot
        self.logger.debug("workspaceroot: {}".format(workspaceroot))
        workspacename = str(icmws._attributesAlwaysAccessViaMethod['Workspace'])
        self.logger.debug("workspacename: {}".format(workspacename))
        config = str(icmws._attributesAlwaysAccessViaMethod['Config'])
        deliverable_library = None
        if not project:
            project = icmws.get_project_of_ip(ip)
            #project = str(icmws._projectName)
        self.logger.debug("project: {}".format(project))
        family = self.eco.get_family(os.getenv("DB_FAMILY")) 
        self.logger.debug("family: {}".format(family))
        try:
            for x in icmws.configurations :
                if 'libtype' in x and x['variant']==ip and x['libtype']==deliverable and x['type'] == 'library':    
                    deliverable_library = x['name']
            if not deliverable_library:
                deliverable_library = self.cli.get_libtype_config_details(project, ip, deliverable, config, retkeys=['name'])
        except:
            raise SCMError('Failed to get library of {}:{}'.format(ip, deliverable))

        # Get dest_path relative path
        m = re.match('\/\/depot\/gdpxl\/intel/{}\/(.*)\/{}\/(.*)'.format(project, deliverable_library), dest_path)
       # m = re.match('\/\/depot\/gdpxl\/intel/{}\/(.*)\/(\S+)\/(.*)'.format(project), dest_path)
        if m:            
            path_to_remove = '{}/{}'.format(m.group(1), m.group(2))
        else:
            raise SCMError('Failed to get relative path of {}'.format(dest_path))

        self.logger.debug("overlay_action: source_path: {}".format(json.dumps(source_path, indent=4)))
        self.logger.debug("overlay_action: dest_path: {}".format(json.dumps(dest_path, indent=4)))

        files_to_overlay = []
        # Get list of files to overlay from source_path
        source_files = self._get_files_from_depotpath(source_path)
        self.logger.debug("overlay_action: source_files: {}".format(json.dumps(source_files, indent=4)))

        for source_file, operation in source_files:
            # Don't overlay deleted file
            if operation != 'delete':
                source_naapath = self._print_depotpath_content(source_file)
                if source_naapath:
                    files_to_overlay.append(source_naapath)
        self.logger.debug("overlay_action: files_to_overlay: {}".format(json.dumps(files_to_overlay, indent=4)))
        
        # Sync deliverable in the workspace before overlay
        self.logger.debug("syncing workspace ...")
        self.cli.sync_workspace(workspacename, skeleton=False, specs=['{}/{}/...'.format(ip, deliverable)], force=True)

        self.logger.debug("overlaying data ...")
        self.overlay_data(files_to_overlay, path_to_remove, project, ip, deliverable, deliverable_library, workspaceroot)            

    def overlay_workspace_action(self, workspaceroot, ip, deliverable):
        '''
        This is the overlay local mode that works by removing all files from depot then checking-in all files from workspace to depot
        Overlay files from workspace to depot
        '''
        self.logger.debug("""overlay_workspace_action()
        - workspaceroot: {}
        - ip/deliverable: {}/{}
        """.format(workspaceroot, ip, deliverable))
        icmws, ip, deliverable = self.validate_workspace(workspaceroot, ip=ip, deliverable=deliverable)
        workspaceroot = icmws._workspaceroot
        workspacename = str(icmws._attributesAlwaysAccessViaMethod['Workspace'])
        project = str(icmws._projectName)
        family = self.eco.get_family(os.getenv("DB_FAMILY")) 
        try:
            for x in icmws.configurations :
                if 'libtype' in x and x['variant']==ip and x['libtype']==deliverable and x['type'] == 'library':    
                    deliverable_library = x['name']
        except:
            raise SCMError('Failed to get library of {}:{}'.format(ip, deliverable))
        path_to_remove = '{}/{}/{}/...'.format(workspaceroot, ip, deliverable)

        files_to_overlay = []
        symlink_files = []
        for root, dirs, files in os.walk(os.path.join(workspaceroot, ip, deliverable)):
            self.logger.debug("{}".format([root, dirs, files]))
            for f in files:
                # Do not overlay .icmconfig and .icminfo files
                if f in ['.icmconfig', '.icminfo']:
                    continue

                # Do not overlay links
                filepath = os.path.join(root, f)
                if not os.path.islink(filepath):
                    ### Remove workspaceroot from filepath
                    relative_filepath = os.path.relpath(os.path.realpath(filepath), os.path.realpath(workspaceroot))
                    files_to_overlay.append(relative_filepath)
                else:
                    symlink_files.append(os.path.realpath(filepath))

        ### Abort local overlay when symlinks found. 
        ### https://jira01.devtools.intel.com/browse/PSGDMX-1489
        if symlink_files:
            self.logger.error("The following symlinks found in workospace. Program Aborted!")
            self.logger.error(symlink_files)
            return 1
            
        self.logger.info("Files to overlay: {}".format(files_to_overlay))

        self.overlay_workspace_data(files_to_overlay, path_to_remove, project, ip, deliverable, deliverable_library, workspaceroot)                   

    def derive_action(self, workspaceroot, ip, deliverable, source_config, dest_config):
        '''
        source_config is ICManage simple configuration
        dest_config is ICManage simple configuration
        Derive files from a source library to dest library
        '''
        if self.preview:
            # For derive, preview mode is different from the rest of the actions because workspace isn't created 
            # Mock workspace values
            workspacename = 'dummy.icm.workspace'
            project = dest_config.project
        else:       
            icmws, ip, deliverable = self.validate_workspace(workspaceroot, ip=ip, deliverable=deliverable, project=dest_config.project)
            workspaceroot = icmws._workspaceroot
            workspacename = str(icmws._attributesAlwaysAccessViaMethod['Workspace'])
            project = str(icmws._projectName)
        family = self.eco.get_family(os.getenv("DB_FAMILY"))            
        source_library = source_config.library
        dest_library = dest_config.library

        files_to_derive = []
        # Get list of files to derive from source_config
        source_path = source_config.get_bom(p4=True)[0]
        source_files = self._get_files_from_depotpath(source_path)
        for source_file, operation in source_files:
            skip_this_file = False
            # Skip files defined in EXCLUDED_FILES
            for excluded_file in EXCLUDED_FILES:
                if excluded_file in source_file:
                    skip_this_file = True
                    break
            # Don't derive deleted file
            if operation != 'delete' and not skip_this_file:
                source_naapath = self._print_depotpath_content(source_file)
                if source_naapath:
                    m = re.match('\/\/depot\/gdpxl\/intel\/{}\/{}\/{}\/{}\/(.*)#'.format(project, ip, deliverable, source_library), source_file)
                    if m:
                        symlink_to_checkin = m.group(1)
                    else:
                        raise SCMError('Failed to get filepath from {}'.format(source_file))
                    files_to_derive.append((source_naapath, symlink_to_checkin))
                        
        self.derive_data(files_to_derive, project, ip, deliverable, workspaceroot, source_library, dest_library, family=family)
        self.logger.info('Successfully derive {} to {}'.format(source_config.get_full_name(), dest_config.get_full_name()))        


    def status_action(self, project, user, status, remote_status):
        
        cmd = 'python /p/psg/flows/common/naa/1.4/naa.py info ' 
        if project:
            cmd = cmd + '-i {} '.format(project)
        if user:
            cmd = cmd + '-u {} '.format(user)
        if status:
            cmd = cmd + '-s \'{}\' '.format(status)
        if remote_status:
            cmd = cmd + '-r \'{}\' '.format(remote_status)


        self.logger.debug(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode or stderr:
            raise SCMError(stderr) 

        convert_mysql_output_to_csv(stdout.rstrip())

def convert_mysql_output_to_csv(data):

        for line in data.split('\n'):
            line = line.replace('\t',',')
            print(line)




def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='subparser_name')

    checkin = subparser.add_parser('checkin')
    checkin.add_argument('--cwd')
    checkin.add_argument('--ip')
    checkin.add_argument('--deliverable')
    checkin.add_argument('--cell', nargs='+', default=[])
    checkin.add_argument('--file')
    checkin.add_argument('--desc')
    checkin.add_argument('--preview', action='store_true')
    checkin.add_argument('--debug', action='store_true')
    checkin.set_defaults(func=checkin_action)

    args = parser.parse_args()
    # If --preview is set, indicate in logger's levelname
    if args.preview:
        levelname = '%(levelname)s-PREVIEW'     
    else:            
        levelname = '%(levelname)s' 
             
    if args.debug:
        logging.basicConfig(stream=sys.stdout, format="{} [%(asctime)s]: %(message)s".format(levelname))
        LOGGER.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, format="{}: %(message)s".format(levelname))
        LOGGER.setLevel(logging.INFO)            

    args.func(args)

def checkin_action(args):
    scm = SCM(preview=args.preview)
    scm.checkin_action(args.cwd, args.ip, args.deliverable, args.cell, args.file, args.desc)

if __name__ == "__main__":
    sys.exit(main())            

## @}
