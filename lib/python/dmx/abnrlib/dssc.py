'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/dssc.py#1 $
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
import sys
import logging
from dmx.utillib.utils import run_command
import dmx.abnrlib.scm
import dmx.abnrlib.icm
import dmx.abnrlib.config_factory 
import dmx.utillib.utils

LOGGER = logging.getLogger(__name__)   

DM = 'designsync'

# This information should live in family.json in the future, leave it here for now
SCRATCH_AREA = '/nfs/site/disks/psg_dmx_1/ws'

class DesignSyncError(Exception): pass

class DesignSync(object):
    def __init__(self, host, port, preview=False):
        self.__DSSC = 'dssc'
        self.preview = preview
        self._dm = DM
        self.cli = dmx.abnrlib.icm.ICManageCLI(preview=preview)
        self.scm = dmx.abnrlib.scm.SCM(preview=preview)
        self.host = host
        self.port = port

        if not self.host:
            raise DesignSyncError('Host {} is invalid'.format(self.host))
        if not self.port:
            raise DesignSyncError('Port {} is invalid'.format(self.port))

        self.vault_header = 'sync://{}:{}'.format(self.host, self.port)

    def _parse_designsync_output(self, output):
        '''
        DesignSync output always begin with the following 2 lines followed by an empty line:
        Logging to /nfs/png/home/kwlim/dss_04062018_153553.log
        V6R2011x
        
        This API will trim away the first 3 lines and return the output as list
        '''
        return output.splitlines()[3:]

    def _split_branch_tag(self, selector):
        '''
        selector = branch:tag
        '''
        branch = ''
        tag = ''
        if ':' in selector:
            branch, tag = selector.split(':')
        else:
            branch = selector
        return (branch, tag)    
    
    def _run_write_command(self, command):
        exitcode = 0
        stdout = ''
        stderr = ''
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode or stderr:
                raise DesignSyncError(stderr)
        return (exitcode, stdout, stderr)

    def _run_read_command(self, command):
        exitcode, stdout, stderr = run_command(command)
        if exitcode or stderr:
            LOGGER.debug('cmd: {}'.format(command))
            LOGGER.debug('stdout: {}'.format(stdout))
            LOGGER.debug('stderr: {}'.format(stderr))
            raise DesignSyncError
        return (exitcode, stdout, stderr)

    def get_vault(self, path=os.getcwd()):
        command = '{} url vault {}'.format(self.__DSSC, path)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_read_command(command)

        return self._parse_designsync_output(stdout)[0]

    def set_vault(self, vault, path=os.getcwd()):
        ret = 0
        command = '{} setvault {} {}'.format(self.__DSSC, vault, path)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_write_command(command)
        ret = 1
        return ret

    def get_selector(self, path=os.getcwd()):
        command = '{} url selector {}'.format(self.__DSSC, path)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_read_command(command)

        return self._parse_designsync_output(stdout)[0]

    def set_selector(self, selector, path=os.getcwd()):
        ret = 0
        command = '{} setselector {} {}'.format(self.__DSSC, selector, path)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_write_command(command)
        ret = 1
        return ret

    def get_branch(self, path=os.getcwd()):
        selector = self.get_selector(path=path)
        branch, tag = self._split_branch_tag(selector)
        return branch

    def get_tag(self, path=os.getcwd()):
        selector = self.get_selector(path=path)
        branch, tag = self._split_branch_tag(selector)
        return tag

    def is_vault_valid(self, vault):
        '''
        Valid vault begins with sync://
        '''
        return True if vault.startswith('sync://') else False

    def populate(self, path=os.getcwd(), vault=None, selector='Trunk:Latest', specs=[]):
        ret = 0        
        if vault:
            self.set_vault(vault, path=path)
        else:
            # If vault is not given, check if current vault is valid
            current_vault = self.get_vault(path=path)
            if not self.is_vault_valid(current_vault):
                LOGGER.error('Current vault {} is invalid. Please provide a valid vault in ICManage DM_CONFIG property'.format(current_vault))
                return ret
        if selector:
            self.set_selector(selector, path=path)

        if specs:
            command = '{} pop'.format(self.__DSSC)
            for spec in specs:
                filepath = '{}/{}'.format(path, spec)
                command = '{} {}'.format(command, filepath)
        else:                    
            command = '{} pop {}'.format(self.__DSSC, path)
        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_write_command(command)
        LOGGER.debug(stdout)
        ret = 1            
        return ret

    def get_files(self, path, selector='Trunk:Latest'):
        command = '{} url contents {}'.format(self.__DSSC, path)
        if selector:
            command = '{} -all -version {}'.format(command, selector)

        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_read_command(command)
        results = [x.rstrip(';') for x in self._parse_designsync_output(stdout)]

        return results

    def get_version(self, path, selector='Trunk:Latest'):
        command = '{} url resolvetag \"{};\"'.format(self.__DSSC, path)
        if selector:
            command = '{} -version {}'.format(command, selector)

        LOGGER.debug(command)
        exitcode, stdout, stderr = self._run_read_command(command)

        return self._parse_designsync_output(stdout)[0]

    def build_vault_url(self, folder):
        return '{}/{}'.format(self.vault_header, folder)

    def get_designsync_vault_from_icmanage(self, project, variant, libtype):
        '''
        Format:
        Project="i10socfm" Variant="liotest1" LibType="bumps" Property="DM_CONFIG" Value="Projects/FALCON_MESA_8_A0_C4/die/prod" Behavior="explicit"

        Folder = ICM DM_CONFIG property

        Returns vault
        '''
        vault = ''

        properties = self.cli.get_libtype_properties(project, variant, libtype)
        if 'DM_CONFIG' not in properties:
            raise DesignSyncError('DM_CONFIG property does not exist for {}/{}/{}. Please run "pm propval" command to add the property.'.format(project, variant, libtype))
        folder = properties['DM_CONFIG']
        vault = self.build_vault_url(folder)

        return vault

    def get_designsync_selector_from_icmanage(self, library, config):
        '''
        Selector = <ICM Library>:<ICM Simple Config>
        If ICM Simple Config is dev, DSSC tag should be Latest
        If ICM library is dev, DSSC branch should be Trunk

        Example:
        Config = bumps@dev      
        Library = dev
        Selector = Trunk:Latest

        Config = bumps@abc    
        Library = trunk2
        Selector = trunk2:abc

        Returns selector
        '''
        selector = ''

        branch = 'Trunk' if library == 'dev' else library
        tag = 'Latest' if config == 'dev' else config
        selector = '{}:{}'.format(branch, tag)

        return  selector

    def write_filelist(self, name, path=os.getcwd(), vault=None, selector='Trunk:Latest'):
        '''
        sync://pkg.sync.intel.com:25013/Projects/FALCON_MESA_8_A0_C4/die/prod,FALCON_MESA_8_A0_C4.ucr,1.2
        sync://pkg.sync.intel.com:25013/Projects/FALCON_MESA_8_A0_C4/die/prod,FALCON_MESA_8_A0_C4.dpr,1.2
        sync://pkg.sync.intel.com:25013/Projects/FALCON_MESA_8_A0_C4/die/prod,FALCON_MESA_8_A0_C4.si_drc,1.2
        '''
        file_versions = []
        if not os.path.exists(path):
            raise DesignSyncError('{} does not exist'.format(path))
        
        files = self.get_files(vault, selector=selector)
        for file in files:
            version = self.get_version(file, selector=selector)
            # Strip vault from file
            file = file.split(vault)[-1].lstrip('/')
            file_versions.append((file, version))

        if not self.preview:
            cfg_dir = '{}/.dm_configs/'.format(path)
            if not os.path.exists(cfg_dir):
                os.mkdir(cfg_dir)
            filelist = '{}/.{}'.format(cfg_dir, name)

            if os.path.exists(filelist):
                raise DesignSyncError('{} already exists, cannot write to existing file'.format(filelist))

            with open(filelist, 'w') as f:
                for file, version in file_versions:
                    f.write('{},{},{}\n'.format(vault, file, version))
        return filelist

    def get_filelist(self, name, path=os.getcwd()):
        '''
        File content:
        sync://pkg.sync.intel.com:25013/Projects/FALCON_MESA_8_A0_C4/die/prod,FALCON_MESA_8_A0_C4.ucr,1.2
        sync://pkg.sync.intel.com:25013/Projects/FALCON_MESA_8_A0_C4/die/prod,FALCON_MESA_8_A0_C4.dpr,1.2
        sync://pkg.sync.intel.com:25013/Projects/FALCON_MESA_8_A0_C4/die/prod,FALCON_MESA_8_A0_C4.si_drc,1.2

        Returns (vault, file, version)
        '''
        if not os.path.exists(path):
            raise DesignSyncError('{} does not exist'.format(path))

        filelist = '{}/.dm_configs/.{}'.format(path, name)
        if not os.path.exists(filelist):
            raise DesignSyncError('{} does not exist'.format(filelist))

        results = []
        with open(filelist) as f:
            lines = f.readlines()

        for line in lines:
            if ',' in line:
                vault, file, version = line.strip().split(',')
                results.append((vault, file, version))

        return results

    def sync_designsync_deliverable_to_icmanage_workspace(self, wsroot, ip, deliverable, wsbom, dm_meta):
        '''
        wsbom format = project/ip@bom
        wsbom is the BOM used to create the ICManage workspace

        If deliverable is mutable:
        1. Get designsync info from manifest
        2. If designinfo not found in manifest, get info from icm property 
        2. Populate everything based on vault and selector

        If deliverable is not mutable:
        1. Get filelist from .filelist/.<name>
        2. Populate based on specs in .filelist/.<name>

        '''
        wsproject, wsip, wsbom = dmx.utillib.utils.split_pvc(wsbom)

        deliverable_dir = '{}/{}/{}'.format(wsroot, ip, deliverable)
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(wsproject, wsip, wsbom)
        retlist = cfobj.search(variant=ip, libtype=deliverable)
        if not retlist:
            LOGGER.info("Skip sync as {}/{} does not exist.".format(ip, deliverable))
            return 0
        else:
            deliverable_bom = retlist[0]
        

        orig_dir = os.getcwd()
        os.chdir(deliverable_dir)

        name = None
        if not deliverable_bom.is_mutable():
            name = '{}__{}'.format(deliverable_bom.library, deliverable_bom.lib_release)                                
            specs = []
            vault = ''
            files = self.get_filelist(name, path=deliverable_dir)
            for v, file, version in files:
                if not vault:
                    vault = v
                specs.append('{}@{}'.format(file, version))
            ret = self.populate(path=deliverable_dir, vault=vault, specs=specs)
        else:
            path = dm_meta['path'] if 'path' in dm_meta else ''
            
            if path: 
                vault = self.build_vault_url(path)
            else:
                vault = self.get_designsync_vault_from_icmanage(deliverable_bom.project, deliverable_bom.variant, deliverable_bom.libtype)
            selector = self.get_designsync_selector_from_icmanage(deliverable_bom.library, deliverable_bom.config)

            ret = self.populate(path=deliverable_dir, vault=vault, selector=selector)

        if not ret:
            LOGGER.error('Failed to sync {}:{} to {}'.format(ip, deliverable, wsroot))
        
        os.chdir(orig_dir)
        return ret

    def add_filelist_into_icmanage_deliverable(self, project, ip ,deliverable, bom, library, dm_meta):
        if not self.preview:
            scratch_area = os.path.realpath(SCRATCH_AREA)
            #Create a workspace in scratch
            wsname = self.cli.add_workspace(project, ip, bom, dirname=scratch_area, libtype=deliverable)
            #Skeleton sync the workspace
            self.cli.sync_workspace(wsname, skeleton=False)
            deliverable_dir = '{}/{}/{}/{}'.format(scratch_area, wsname, ip, deliverable)
            orig_dir = os.getcwd()
            os.chdir(deliverable_dir)

            path = dm_meta['path'] if 'path' in dm_meta else ''            
            if path: 
                vault = self.build_vault_url(path)
                selector = self.get_designsync_selector_from_icmanage(library, bom)
            else:
                vault = self.get_designsync_vault_from_icmanage(project, ip, deliverable)
                selector = self.get_designsync_selector_from_icmanage(library, bom)

            release = self.cli.get_next_library_release_number(project, ip, deliverable, library)
            name = '{}__{}'.format(library, release)
             # Create the filelist
            filelist = self.write_filelist(name, path=deliverable_dir, vault=vault, selector=selector)
            # Add and submit config to ICM
            self.scm._add_file_to_icm(filelist) 
            desc = 'Filelist for library@release {}@{}'.format(library, release)
            self.scm._submit_to_icm(description=desc)
            # Remove workspace
            self.cli.del_workspace(wsname, preserve=False, force=True)

            os.chdir(orig_dir)



    






