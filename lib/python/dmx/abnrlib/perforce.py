'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/perforce.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  Altera Build 'N Release
              dmx.abnrlib.icm : utility functions for interfacing with ICManage commands

Author: Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''

import os
import re
import sys
import logging
from dmx.utillib.utils import run_command
import dmx.abnrlib.scm
import dmx.abnrlib.icm
import dmx.abnrlib.config_factory 
import dmx.utillib.utils

LOGGER = logging.getLogger(__name__)   

DM = 'perforce'

# This information should live in family.json in the future, leave it here for now
SCRATCH_AREA = '/nfs/site/disks/psg_dmx_1/ws'

class PerforceError(Exception): pass

class Perforce(object):
    def __init__(self, host, port, preview=False):
        self.__P4 = 'p4'
        self.host = host
        self.port = port
        self.preview = preview
        self._dm = DM
        self.cli = dmx.abnrlib.icm.ICManageCLI(preview=preview)
        self.scm = dmx.abnrlib.scm.SCM(preview=preview)
        self.host = host
        self.port = port
        
        if not self.host:
            raise PerforceError('Host {} is invalid'.format(self.host))
        if not self.port:
            raise PerforceError('Port {} is invalid'.format(self.port))
    
        self.server = '{}:{}'.format(self.host, self.port)

    def _run_write_command(self, command):
        exitcode = 0
        stdout = ''
        stderr = ''
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode or stderr:
                raise PerforceError(stderr)
        return (exitcode, stdout, stderr)

    def _run_read_command(self, command):
        exitcode, stdout, stderr = run_command(command)
        if exitcode or stderr:
            LOGGER.debug('cmd: {}'.format(command))
            LOGGER.debug('stdout: {}'.format(stdout))
            LOGGER.debug('stderr: {}'.format(stderr))
            raise PerforceError
        return (exitcode, stdout, stderr)

    def get_perforce_info_from_config(self, file):
        '''
        File format:
        type=perforce
        depot=//depot/da/infra/arc

        Returns depot
        '''
        lines = []
        depot = ''
        selector = ''
        if not os.path.exists(file):
            raise PerforceError('{} does not exist'.format(file))

        with open(file) as f:
            lines = f.readlines()

        for line in lines:
            if not line.startswith('#') and not line.startswith('//'):                
                if '=' in line:
                    key, value = line.strip().split('=')
                    if 'depot' in key:
                        depot = value

        return depot

    def is_perforce_config(self, file):
        '''
        File format:
        type=perforce
        depot=//depot/da/infra/arc

        Returns True if type == perforce
        '''
        ret = False
        if not os.path.exists(file):
            raise PerforceError('{} does not exist'.format(file))

        with open(file) as f:
            lines = f.readlines()

        for line in lines:
            if not line.startswith('#') and not line.startswith('//'):                
                if '=' in line:
                    key, value = line.strip().split('=')
                    if key == 'type' and value == self._dm:
                        ret = True
                        break
        return ret

    def get_perforce_config(self, path=os.getcwd()):
        '''
        Filename: .dm_info
        '''
        file = '{}/.dm_info'.format(path)
        if not os.path.exists(file):
            raise PerforceError('{} does not exist'.format(file))
        if not self.is_perforce_config(file):
            raise PerforceError('{} is not a Perforce configuration file'.format(file))
        return file

    def get_perforce_clientspec(self):
        command = '{} -p {} client -o'.format(self.__P4, self.server)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_read_command(command)
        return stdout

    def create_client_from_clientspec(self, clientspec):
        ret = 0
        command = '{} -p {} client -i < {}'.format(self.__P4, self.server, clientspec)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_write_command(command)
        ret = 1
        return ret

    def delete_client(self, clientname):
        ret = 0
        command = '{} -p {} client -d {}'.format(self.__P4, self.server, clientname)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_write_command(command)
        ret = 1
        return ret

    def create_client(self, depot, path=os.getcwd()):
        clientname = '{}_{}'.format(os.getenv('USER'), os.getenv('ARC_JOB_ID'))
        # Create p4 client
        clientspec = self.get_perforce_clientspec().splitlines()

        new_clientspec = []
        old_clientname = ''
        view_added = False
        # Rename client name
        for line in clientspec:
            if line.startswith('Client'):
                key, value = line.split(':')
                old_clientname = value.strip()
                newline = '{}: {}'.format(key, clientname)
                new_clientspec.append(newline)
            elif line.startswith('Root'):
                key, value = line.split(':')
                newline = '{}: {}'.format(key, path)
                new_clientspec.append(newline)
            elif line.startswith('\t//'):
                if not view_added:
                    if depot:
                        newline = '\t{}/... //{}/...'.format(depot, clientname)
                        new_clientspec.append(newline)
                    else:
                        newline = '\t//depot/... //{}/...'.format(clientname)
                        new_clientspec.append(newline)
                    view_added = True
            else:
                new_clientspec.append(line)

        clientspec_file = '{}/.clientspec'.format(path)
        with open(clientspec_file, 'w') as f:
            f.write('\n'.join(new_clientspec))

        self.create_client_from_clientspec(clientspec_file)

        return clientname

    def sync_client(self, clientname, specs=[]):
        command = '{} -p {} -c {} sync'.format(self.__P4, self.server, clientname)
        if specs:
            for spec in specs:
                command += ' {}'.format(spec)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_write_command(command)
        LOGGER.debug(stdout)
        ret = 1
        return ret

    def get_files(self, depot):
        command = '{} -p {} files -e {}/...'.format(self.__P4, self.server, depot)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_read_command(command)
        LOGGER.debug(stdout)
        ret = stdout.splitlines()
        return ret
    
    
    def populate(self, depot, path=os.getcwd(), specs=[]):
        ret = 0        
        os.chdir(path)
        clientname = self.create_client(depot, path=path)

        ret = self.sync_client(clientname, specs=specs)

        ret = self.delete_client(clientname)
        ret = 1            
        return ret

    def write_filelist(self, name, path=os.getcwd(), depot=None):
        '''
        //depot/da/infra/arc,//depot/da/infra/arc/Makefile,1
        //depot/da/infra/arc,//depot/da/infra/arc/README,2
        //depot/da/infra/arc,//depot/da/infra/arc/bin/automated_project_builder.py,20
        '''
        file_versions = []
        if not os.path.exists(path):
            raise PerforceError('{} does not exist'.format(path))
        
        files = self.get_files(depot)
        for file in files:
            m = re.match('(.*)#(.*) - ', file)
            if m:
                filename = m.group(1)
                version = m.group(2)
                file_versions.append((filename, version))

        if not self.preview:
            cfg_dir = '{}/.dm_configs/'.format(path)
            if not os.path.exists(cfg_dir):
                os.mkdir(cfg_dir)
            filelist = '{}/.{}'.format(cfg_dir, name)

            if os.path.exists(filelist):
                raise PerforceError('{} already exists, cannot write to existing file'.format(filelist))

            with open(filelist, 'w') as f:
                for file, version in file_versions:
                    f.write('{},{},{}\n'.format(depot, file, version))
        return filelist

    def get_filelist(self, name, path=os.getcwd()):
        '''
        File content:
        //depot/da/infra/arc,//depot/da/infra/arc/Makefile,1
        //depot/da/infra/arc,//depot/da/infra/arc/README,2
        //depot/da/infra/arc,//depot/da/infra/arc/bin/automated_project_builder.py,20

        Returns (depot, file, version)
        '''
        if not os.path.exists(path):
            raise PerforceError('{} does not exist'.format(path))

        filelist = '{}/.dm_configs/.{}'.format(path, name)
        if not os.path.exists(filelist):
            raise PerforceError('{} does not exist'.format(filelist))

        results = []
        with open(filelist) as f:
            lines = f.readlines()

        for line in lines:
            if ',' in line:
                depot, file, version = line.strip().split(',')
                results.append((depot, file, version))

        return results

    def write_config_file(self, depot='', path=os.getcwd()):
        if not os.path.exists(path):
            raise PerforceError('{} does not exist'.format(path))
        config_file = '{}/.dm_info'.format(path)
        if os.path.exists(config_file):
            raise PerforceError('{} already exists'.format(config_file))
        
        with open(config_file, 'w') as f:
            f.write('type={}\n'.format(self._dm))
            f.write('depot={}\n'.format(depot))
        return config_file

    def populate_action(self, name=None, path=os.getcwd()):
        '''
        If not name:
        1. Get perforce info from .dm_info
        2. Populate everything based on depot

        If name:
        1. Get perforce info from .dm_info
        2. Get filelist from .filelist/.<name>
        3. Populate based on specs in .filelist/.<name>
        '''
        ret = 0
        if not os.path.exists(path):
            raise PerforceError('{} does not exist'.format(path))

        p4_config = self.get_perforce_config(path=path)
        depot = self.get_perforce_info_from_config(p4_config)

        if name:
            specs = []
            depotpath = ''
            files = self.get_filelist(name, path=path)
            for d, file, version in files:
                if not depot:
                    depot = d
                specs.append('{}#{}'.format(file, version))
            ret = self.populate(path=path, depot=depot, specs=specs)
        else:
            ret = self.populate(path=path, depot=depot)

        return ret

    def sync_perforce_deliverable_to_icmanage_workspace(self, wsroot, ip, deliverable, wsbom):
        '''
        wsbom format = project/ip@bom
        wsbom is the BOM used to create the ICManage workspace
        '''
        wsproject, wsip, wsbom = dmx.utillib.utils.split_pvc(wsbom)

        deliverable_dir = '{}/{}/{}'.format(wsroot, ip, deliverable)
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(wsproject, wsip, wsbom)
        deliverable_bom = cfobj.search(variant=ip,
                                       libtype=deliverable)[0]
        name = None
        if not deliverable_bom.is_mutable():
            name = '{}__{}'.format(deliverable_bom.library, deliverable_bom.lib_release)                                
        os.chdir(deliverable_dir)
        ret = self.populate_action(name=name, path=deliverable_dir)
        if not ret:
            LOGGER.error('Failed to sync {}:{} to {}'.format(ip, deliverable, wsroot))
        
        return ret

    def add_config_file_into_icmanage_deliverable(self, project, ip, deliverable, bom):
        if not self.preview:
            scratch_area = os.path.realpath(SCRATCH_AREA)
            #Create an ICM workspace in scratch_area
            wsname = self.cli.add_workspace(project, ip, bom, dirname=scratch_area, libtype=deliverable)
            #Skeleton sync the workspace
            self.cli.sync_workspace(wsname, skeleton=True)
            deliverable_dir = '{}/{}/{}/{}'.format(scratch_area, wsname, ip, deliverable)
            os.chdir(deliverable_dir)
            # Create the config file
            config_file = self.write_config_file(path=deliverable_dir)
            # Add and submit config to ICM
            self.scm._add_file_to_icm(config_file) 
            desc = 'Initial configuration file created by dmx'
            self.scm._submit_to_icm(description=desc)
            # Remove workspace
            self.cli.del_workspace(wsname, preserve=False, force=True)

    def add_filelist_into_icmanage_deliverable(self, project, ip ,deliverable, bom, library):
        if not self.preview:
            scratch_area = os.path.realpath(SCRATCH_AREA)
            #Create a workspace in scratch
            wsname = self.cli.add_workspace(project, ip, bom, dirname=scratch_area, libtype=deliverable)
            #Skeleton sync the workspace
            self.cli.sync_workspace(wsname, skeleton=False)
            deliverable_dir = '{}/{}/{}/{}'.format(scratch_area, wsname, ip, deliverable)
            os.chdir(deliverable_dir)
            # Create the config file
            config_file = self.get_perforce_config(path=deliverable_dir)
            depot = self.get_perforce_info_from_config(file=config_file)
            release = self.cli.get_next_library_release_number(project, ip, deliverable, library)
            name = '{}__{}'.format(library, release)
            filelist = self.write_filelist(name, path=deliverable_dir, depot=depot)
            # Add and submit config to ICM
            self.scm._add_file_to_icm(filelist) 
            desc = 'Filelist for library@release {}@{}'.format(library, release)
            self.scm._submit_to_icm(description=desc)
            # Remove workspace
            self.cli.del_workspace(wsname, preserve=False, force=True)



    






