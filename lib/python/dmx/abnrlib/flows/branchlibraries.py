#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/branchlibraries.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr branchlibraries"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import sys
import os
import logging
import textwrap
import itertools

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.utils import normalize_config_name, get_ww_details, \
    format_configuration_name_for_printing, add_common_args
from dmx.utillib.multiproc import run_mp
from dmx.abnrlib.flows.branchlibrary import BranchLibrary
from dmx.utillib.arcenv import ARCEnv

class BranchLibrariesError(Exception): pass

class BranchLibraries(object):
    '''
    Class that handles running abnr branchlibraries
    '''

    def __init__(self, project, variant, config, branch, libtypes=[], description='', reuse=False, exact=False, directory=None, preview=True, hierarchy=False, derivative=False):
        self.project = project
        self.variant = variant
        self.config = config
        self.branch = branch
        self.libtypes = libtypes
        self.description = description
        self.reuse = reuse
        self.directory = directory
        self.preview = preview
        self.exact = exact
        self.hierarchy = hierarchy
        self.derivative = derivative

        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI(preview=preview)

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise BranchLibrariesError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))                
        else:
            if not self.cli.project_exists(self.project):
                raise BranchLibrariesError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise BranchLibrariesError("{0}/{1} does not exist".format(self.project, self.variant))       
        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise BranchLibrariesError('{0} does not exist'.format(format_configuration_name_for_printing(
                self.project, self.variant, self.config))
            )
        
        if self.config.startswith('REL') or self.config.startswith('snap'):
            normalized_config = normalize_config_name(self.config)
            (year, ww, day) = get_ww_details()
            # in GDPXL they branch name will be the same as the thread/config name
            #if not self.exact and not self.derivative:
            #    self.branch = '{0}_{1}ww{2}{3}'.format(normalize_config_name(self.branch),
                                                       #year, ww, day)
    
            if self.exact:
                self.new_config_name = self.branch
            else:            
                # Bertrand doesn't want the configuration name to include the ww datestamp
                # See Fogbugz case 254315        
                self.new_config_name = 'b{0}__{1}__dev'.format(normalized_config, branch)
        else:
            self.new_config_name = self.branch                
        
    def run(self):
        '''
        Entry point for running abnr branch
        '''
        ret = 1
        ret = self.do_the_branch()

        return ret

    def check_if_branch_already_exists(self, source_config_tree):
        '''
        Checks the configuration tree to ensure the branch doesn't already
        exist somewhere
        :param source_config_tree: The source configuration tree
        :type source_config_tree: IcmConfig
        :return: None
        '''        
        # branch/library renamed to thread
        self.logger.info('Checking for existing threads of the same name')
        library_configs = [x for x in source_config_tree.flatten_tree() if not x.is_config()]
        for library_config in library_configs:
            if self.cli.library_exists(library_config.project, library_config.variant,
                                       library_config.libtype, self.branch):
                raise BranchLibrariesError('Branch {0} already exists in {0}/{1}:{2}'.format(self.branch,
                                                                                       library_config.project,
                                                                                       library_config.variant,
                                                                                       library_config.libtype))

        return True

    def check_if_config_already_exists(self, source_config_tree):
        '''
        Checks the configuration tree to ensure the config doesn't already
        exist 
        :param source_config_tree: The source configuration tree
        :type source_config_tree: IcmConfig
        :return: None
        '''
        self.logger.info('Checking for existing config of the same name')
        library_configs = [x for x in source_config_tree.flatten_tree() if not x.is_config()]
        for library_config in library_configs:
            if self.cli.config_exists(library_config.project, library_config.variant,
                                       library_config.libtype, self.new_config_name):
                raise BranchLibrariesError('Config {0} already exists in {0}/{1}:{2}'.format(self.new_config_name,
                                                                                       library_config.project,
                                                                                       library_config.variant,
                                                                                       library_config.libtype))

        return True

    def do_the_branch(self):
        '''
        Creates the new branches and configuration tree
        :return: int
        '''
        ret = 1

        source_config_tree, branch_config_tree = self.get_config_trees()
        if source_config_tree is None:
            raise BranchLibrariesError('Unable to build source configuration tree')
        if branch_config_tree is None:
            raise BranchLibrariesError('Unable to create initial branch configuration tree')

        if not self.reuse:
            # Since branchname will always have timestamp appended, it is no longer accurate to  check for existnece of branch
            # Instead check for existence of config to be branched
            #self.check_if_branch_already_exists(source_config_tree)
            self.check_if_config_already_exists(source_config_tree)

        num_branched = self.branch_libraries(source_config_tree, branch_config_tree)

        if not self.reuse and num_branched < 1:
            raise BranchLibrariesError('No branches created')

        if self.hierarchy:
            self.rename_composite_configs(branch_config_tree)

        #branch_config_tree._saved = False
        if not branch_config_tree.save():
            raise BranchLibrariesError('Error saving new branch configuration {0}'.format(branch_config_tree.get_full_name()))
        else:
            ret = 0

        # config renamed to bom
        self.logger.info('Created BOM {0}'.format(branch_config_tree.get_full_name()))

        return ret

    def get_config_trees(self):
        '''
        Builds the input configuration tree in memory and also
        creates a clone of that tree for us to work on
        :return: (source, branch) tuple
        '''
        self.logger.debug('Building input configuration tree')
        source_config_tree = ConfigFactory.create_from_icm(self.project, self.variant, self.config,
                                                           preview=self.preview)

        ### support for --derivative option
        ### https://jira.devtools.intel.com/browse/PSGDMX-1578
        if not self.derivative:
            configname = self.new_config_name
        else:
            configname = '{}_dev'.format(self.branch)

        if self.reuse and self.cli.config_exists(self.project, self.variant, configname):
            self.logger.debug("Destination config already exists: {}/{}@{}. Reusing it.".format(self.project, self.variant, configname))
            branch_config_tree = ConfigFactory.create_from_icm(self.project, self.variant, configname, preview=self.preview)
        else:
            branch_config_tree = source_config_tree.clone(configname)
            branch_config_tree.description = self.description

        return (source_config_tree, branch_config_tree)

    def branch_libraries(self, source_config_tree, branch_config_tree):
        '''
        Walks through all library configs in source_config_tree, branches them
        and replaces the original with the branch in branch_config_tree
        :param source_config_tree: The source configuration tree
        :type source_config_tree: IcmConfig
        :param branch_config_tree: The branch configuration tree
        :type branch_config_tree: IcmConfig
        :return:
        '''
        total_num_replaced = 0
        mp_args = []
        library_configs = set([x for x in source_config_tree.flatten_tree() if not x.is_config()])

        for library_config in library_configs:
            self.logger.debug('Processing {0}'.format(library_config.get_full_name()))
            if self.libtypes and library_config.libtype not in self.libtypes:
                self.logger.debug('Skipping {0}'.format(library_config.get_full_name()))
                continue
            if not self.hierarchy and self.variant != library_config.variant:
                self.logger.debug('Skipping {0} due to non-hierarchical mode.'.format(library_config.get_full_name()))
                continue

            ### support for --derivative option
            ### https://jira.devtools.intel.com/browse/PSGDMX-1578
            if not self.derivative:
                branchname = self.branch
                configname = self.new_config_name
            else:
                if library_config.library in ['dev', 'lay', 'ciw']:
                    branchname = configname = '{}_{}'.format(self.branch, library_config.library)
                else:
                    branchname = configname = '{}_dev'.format(self.branch)


            # Add to the list of arguments for multiprocessing
            mp_args.append([library_config.project, library_config.variant, library_config.libtype,
                           library_config.library, branchname, configname,
                           self.description, self.preview, self.reuse, self.directory])

        ### This part is added so that the (Section: BRANCHPARALLEL) is ran in series, so that
        ### we can debug easier.
        ### *** IMPORTANT NOTES ***
        ### - Since now reuse is always True, thus, I(lionel) only migrated the reuse=True sections from section:BRANCHPARALLEL
        ### - We also didn't migrated preview=False
        if os.getenv("DMX_DISABLE_PARALLEL", False) and mp_args:
            self.logger.info("DMX_DISABLE_PARALLEL detected! Running jobs in series ...")
            for (simple_config_project, simple_config_variant, simple_config_libtype, simple_config_config, branchname, configname, desc, preview, reuse, directory) in mp_args:
                result = branch_library(simple_config_project, simple_config_variant, simple_config_libtype, simple_config_config, branchname, configname, desc, preview, reuse, directory)
                branch_library_config = ConfigFactory.create_from_icm(result['project'],
                                                                     result['variant'],
                                                                     result['branch_config'],
                                                                     libtype=result['libtype'],
                                                                     preview=self.preview)

                num_replaced = branch_config_tree.replace_all_instances_in_tree(result['project'],
                                                                                result['variant'],
                                                                                branch_simple_config,
                                                                                libtype=result['libtype'])
                if self.reuse and num_replaced < 1:
                    ### if reuse, but nothing is replaced, this means the pvlc does not exist in the branch_config_tree.
                    ### Thus, we need to add that in to the branch_config_tree
                    vcf = branch_config_tree.search(project=result['project'], variant=result['variant'], libtype=None)
                    if vcf:
                        self.logger.debug("Adding reuse library config {} ...".format(branch_library_config.get_full_name())) 
                        ### If library-config already exist, print warning instead of raise exception.
                        try:
                            vcf[0].add_configuration(branch_library_config)
                        except Exception as e:
                            self.logger.warning(str(e))
                if not self.reuse and num_replaced < 1:
                    raise BranchLibrariesError('Could not replace {0}/{1}:{2}@{3} with {4} in the branch configuration'.format(
                        result['project'], result['variant'], result['libtype'], result['original_config'],
                        branch_library_config.get_full_name()
                    ))
                else:
                    total_num_replaced += num_replaced

            return total_num_replaced


        ### Section: BRANCHPARALLEL
        # Branch the libraries in parallel
        if mp_args:
            # GDPXL multiprocessing have problem, set to 1 for now
            branch_results = run_mp(branch_library, mp_args, num_processes=1)
            for result in branch_results:
                # If we're in preview mode the config won't exist so fake it
                if self.preview and not self.cli.config_exists(result['project'],
                                                               result['variant'],
                                                               result['branch_config'],
                                                               libtype=result['libtype']):

                    if self.cli.is_name_immutable(result['branch_config']):
                        release = result['branch_config']
                        library = icm.get_library_from_release(result['project'], result['variant'], result['libtype'], release)
                    else:
                        library = result['branch_config']
                        release = ''

                    branch_library_config = IcmLibrary(result['project'],
                                                      result['variant'],
                                                      result['libtype'],
                                                      library,
                                                      release,
                                                      changenum='#ActiveDev',
                                                      preview=self.preview)
                    branch_library_config.save()
                else:
                    branch_library_config = ConfigFactory.create_from_icm(result['project'],
                                                                         result['variant'],
                                                                         result['branch_config'],
                                                                         libtype=result['libtype'],
                                                                         preview=self.preview)

                num_replaced = branch_config_tree.replace_all_instances_in_tree(result['project'],
                                                                                result['variant'],
                                                                                branch_library_config,
                                                                                libtype=result['libtype'])
                if self.reuse and num_replaced < 1:
                    ### if reuse, but nothing is replaced, this means the pvlc does not exist in the branch_config_tree.
                    ### Thus, we need to add that in to the branch_config_tree
                    vcf = branch_config_tree.search(project=result['project'], variant=result['variant'], libtype=None)
                    if vcf:
                        self.logger.debug("Adding reuse library config {} ...".format(branch_library_config.get_full_name())) 
                        ### If library-config already exist, print warning instead of raise exception.
                        try:
                            vcf[0].add_configuration(branch_library_config)
                        except Exception as e:
                            self.logger.warning(str(e))
                    

                if not self.reuse and num_replaced < 1:
                    raise BranchLibrariesError('Could not replace {0}/{1}:{2}@{3} with {4} in the branch configuration'.format(
                        result['project'], result['variant'], result['libtype'], result['original_config'],
                        branch_library_config.get_full_name()
                    ))
                else:
                    total_num_replaced += num_replaced

        return total_num_replaced

    def rename_composite_configs(self, branch_config_tree):
        '''
        Renames all composite configurations in the tree to branch
        '''
        num_renamed = 0
        composite_configs = [x for x in branch_config_tree.flatten_tree() if x.is_config()]
        # Remove the top-level config from the list
        composite_configs.remove(branch_config_tree)

        ### support for --derivative option
        ### https://jira.devtools.intel.com/browse/PSGDMX-1578
        if not self.derivative:
            configname = self.new_config_name
        else:
            configname = '{}_dev'.format(self.branch)

        for config in composite_configs:
            if self.cli.config_exists(config.project, config.variant, configname) and self.reuse:
                branch_composite = ConfigFactory.create_from_icm(config.project, config.variant, configname)
                ### Do not raise error when source and dest config are the same
                try:
                    branch_config_tree.replace_object_in_tree(config, branch_composite)
                except Exception as e:
                    self.logger.warning(str(e))
            else:                
                branch_composite = config.clone(configname)
                branch_composite.description = self.description
                ### Do not raise error when source and dest config are the same
                try:
                    num_renamed += branch_config_tree.replace_object_in_tree(config, branch_composite)
                except Exception as e:
                    self.logger.warning(str(e))

        
        return num_renamed

def branch_library(project, variant, libtype, config, branch_name, branch_config,
                   description, preview, reuse, directory=None):
    '''
    Branches the library pointed to by project/variant:libtype@config and creates
    a new library config referencing the branch.

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param libtype: The IC Manage libtype
    :type libtype: str
    :param config: The source IC Manage configuration
    :type config: str
    :param branch_name: The name of the branch we want to create
    :type branch_name: str
    :param branch_config: The name of the new configuration to create for the branch
    :type branch_config: str
    :param description: The branch description
    :type description: str
    :param preview: Flag indicating whether or not we're in preview mode
    :type preview: bool
    :return: Dictionary containing project, variant, libtype original config and branch config
    :rtype: dict
    '''
    cli = ICManageCLI(preview=preview)

    if cli.config_exists(project, variant, branch_config, libtype=libtype):
         # If reuse is specified, reuse the library config if it exists
        if reuse:
             return {
                'project' : project,
                'variant' : variant,
                'libtype' : libtype,
                'branch_config' : branch_config,
                'original_config' : config,
            }
        else:            
            raise BranchLibrariesError('Library Configuration {}/{}:{}@{} already exists'.format(project, variant, libtype, branch_config))

    
    # If the branch doesn't exist, create it
    if not cli.library_exists(project, variant, libtype, branch_name):
        branchlib = BranchLibrary(project, variant, libtype, config, branch_name,
                                 target_config=branch_config, preview=preview,
                                 called_from_branch_libraries=True,
                                 description=description,
                                 directory=directory)

        if branchlib.run() is 1:
            raise BranchLibrariesError('Problem creating branch {0}/{1}:{2}/{3}'.format(
                project, variant, libtype, branch_name
            ))

    # If we didn't create the branch above then the config may not exist
    # If not, create it
    if not cli.config_exists(project, variant, branch_config, libtype=libtype):
        new_config = IcmLibrary(project, variant, libtype,
                                  branch_name, preview=preview)
        if not new_config.save():
            raise BranchLibrariesError('Problem creating library branch configuration: {0}'.format(
                new_config.get_full_name()
            ))

    return {
        'project' : project,
        'variant' : variant,
        'libtype' : libtype,
        'branch_config' : branch_config,
        'original_config' : config,
    }
        
