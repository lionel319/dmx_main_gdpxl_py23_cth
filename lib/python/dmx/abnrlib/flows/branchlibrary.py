#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/branchlibrary.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr branchlibrary"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import os
import sys
import logging
import textwrap

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.utillib.utils import format_configuration_name_for_printing, normalize_config_name, get_ww_details
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.namevalidator import ICMName
import dmx.ecolib.ecosphere
from dmx.utillib.arcenv import ARCEnv
import dmx.abnrlib.scm
# This information should live in family.json in the future, leave it here for now
SCRATCH_AREA = '/nfs/site/disks/psg_dmx_1/ws'

class BranchLibraryError(Exception): pass

class BranchLibrary(object):
    '''
    Class that handles the running of abnr branchlibrary
    '''

    def __init__(self, source_project, source_variant, libtype, config, target_library,
                 target_project='', target_variant='', target_config='', description='', 
                 called_from_branch_libraries=False,
                 directory=None,
                 preview=True):
        self.source_project = source_project
        self.source_variant = source_variant
        self.libtype = libtype
        self.config = config
        self.target_library = target_library
        self.target_project = target_project
        self.target_variant = target_variant
        self.target_config = target_config
        self.preview = preview
        self.description = description
        self.called_from_branch_libraries = called_from_branch_libraries
        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI(preview=preview)
               
        # If project not given, get project from IP
        if not self.source_project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.source_variant):
                    self.source_project = arc_project
                    break
            if not self.source_project:
                raise BranchLibraryError('Variant {0} is not found in projects: {1}'.format(self.source_variant, arc_projects))
        else:
            if not self.cli.project_exists(self.source_project):
                raise BranchLibraryError("{0} does not exist".format(self.source_project))
            if not self.cli.variant_exists(self.source_project, self.source_variant):
                raise BranchLibraryError("{0}/{1} does not exist".format(self.source_project, self.source_variant))   
               
        # If the target project/variant are empty set them to source
        if not self.target_project:
            self.target_project = self.source_project

        if not self.target_variant:
            self.target_variant = self.source_variant

        # If the target config is empty set it to target library
        if not self.target_config:
            self.target_config = self.target_library

        if not ICMName.is_library_name_valid(self.target_library):
            raise BranchLibraryError('{0} is not a valid branch name'.format(
                self.target_library
            ))

        # we need to build the config named normalize(BOM)__THREAD__dev
        # library name normalize(BOM)__THREAD__dev_<timestamp>
        if self.config.startswith('REL') or self.config.startswith('snap'):
            # if called from branchlibraries, target_config and target_library already built
            # don't have to build them again
            if not self.called_from_branch_libraries:
                normalized_config = normalize_config_name(self.config)
                (year, ww, day) = get_ww_details()
                #self.target_library = '{0}_{1}ww{2}{3}'.format(normalize_config_name(self.target_library),
                                                               #year, ww, day)
        
                # Bertrand doesn't want the configuration name to include the ww datestamp
                # See Fogbugz case 254315        
                self.target_config = 'b{0}__{1}__dev'.format(normalized_config, target_library)
                self.target_libray  = self.target_config

        if not self.cli.libtype_exists(self.source_project, self.source_variant, self.libtype):
            raise BranchLibraryError("{0}/{1}:{2} does not exist".format(self.source_project, self.source_variant, self.libtype))               
        # Make sure the source exists
        if not self.cli.config_exists(self.source_project, self.source_variant, self.config,
                                      libtype=self.libtype):
            raise BranchLibraryError('Source configuration {0} does not exist'.format(
                format_configuration_name_for_printing(self.source_project, self.source_variant,
                                                       self.config, libtype=self.libtype)
            ))

        # Make sure the target library does not exist
        if self.cli.library_exists(self.target_project, self.target_variant, self.libtype, self.target_library):
            raise BranchLibraryError('Target library {0}/{1}:{2}/{3} already exists'.format(
                self.target_project, self.target_variant, self.libtype, self.target_library
            ))

        # Make sure the target config does not exist
        if self.cli.config_exists(self.target_project, self.target_variant, self.target_config,
                                  libtype=self.libtype):
            raise BranchLibraryError('Target configuration {0} already exists'.format(
                format_configuration_name_for_printing(
                    self.target_project, self.target_variant, self.target_config,
                    libtype=self.libtype)
            ))
        self.family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))

        # If directory is given, check that it's valid            
        # Else use the scratch_disk provided
        if directory:
            if os.path.isdir(directory):
                self.directory= os.path.realpath(directory)
            else:
                raise BranchLibraryError('{} is not a valid directory'.format(directory))
        else:
            self.directory = os.path.realpath(SCRATCH_AREA)

        # https://jira01.devtools.intel.com/browse/PSGDMX-21
        # Check if deliverable is part of roadmap
        try:
            delobj = self.family.get_ip(self.source_variant, project_filter=self.source_project).get_deliverable(self.libtype)
        except:
            self.logger.error('Failed to derive for {}, deliverable {} is no longer part of roadmap.'.format(
                [self.source_project, self.source_variant, self.libtype, self.config], self.libtype))
            raise


    def run(self):
        '''
        Executes the branchlibrary command
        Returns 1 on error
        0 on success
        '''
        ret = 1

        source_config = ConfigFactory.create_from_icm(self.source_project, self.source_variant,
                                                     self.config, libtype=self.libtype,
                                                     preview=self.preview)

        self.logger.info('Branching from {0}/{1}:{2}/{3}@{4} to {5}/{6}:{7}/{8}'.format(
            source_config.project, source_config.variant, source_config.libtype, source_config.library,
            source_config.lib_release, self.target_project, self.target_variant, self.libtype,
            self.target_library
        ))

        # If deliverable is large data type and IP is not excluded, follows different algorithm
        delobj = self.family.get_ip(self.source_variant, project_filter=self.source_project).get_deliverable(self.libtype)
        is_large = delobj.large
        large_excluded_ip = delobj.large_excluded_ip
        if is_large and self.source_variant not in large_excluded_ip:
            # Since we are using add_libraries instead of branch_library API, we need to set our own description if it's not given
            if not self.description:
                self.description = "Branched from {0}/{1}:{2}/{3}@{4}".format(self.source_project, self.source_variant, self.libtype, source_config.library, source_config.lib_release)

            # Don't branch library, instead just create the dest library
            if not self.cli.add_libraries(self.target_project, self.target_variant, [self.libtype], library=self.target_library, description=self.description):
                # Create the new config
                new_cfg = IcmLibrary(self.target_project, self.target_variant, self.libtype, 
                                          self.target_library, description=self.description,
                                          preview=self.preview)

                if new_cfg.save():
                    # Create dest workspace
                    workspacename = self.cli.add_workspace(self.target_project, self.target_variant, new_cfg.library, dirname=self.directory, libtype=self.libtype)
                    workspaceroot = '{}/{}'.format(self.directory, workspacename)
                    self.logger.debug('Staging workspace = {}'.format(workspaceroot))
                    orig_cwd = os.getcwd()
                    if not self.preview:
                        # Skeleton-sync workspace 
                        self.cli.sync_workspace(workspacename)
                        os.chdir(workspaceroot)

                    # Derive the deliverable using scm module
                    scm = dmx.abnrlib.scm.SCM(self.preview)
                    scm.derive_action(workspaceroot, self.target_variant, self.libtype, source_config, new_cfg)

                    if not self.preview:
                        os.chdir(orig_cwd)
                        # Skeleton-sync workspace 
                        # Remove the staging workspace                
                        self.cli.del_workspace(workspacename, preserve=False, force=True)

                    ret = 0
                else:
                    self.logger.error('Could not save library configuration {0}'.format(new_cfg.get_full_name()))
                    ret = 1
        else:            
            # Branch the library
            if self.cli.branch_library(source_config.project, source_config.variant, source_config.libtype,
                                       source_config.library, self.target_library,
                                       target_project=self.target_project,
                                       target_variant=self.target_variant,
                                       desc=self.description, target_config=self.target_config):
                                      # relname=source_config.lib_release):
                ret = 0

        return ret
