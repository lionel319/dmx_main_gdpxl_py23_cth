#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releasetree.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "releasetee" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import logging
import textwrap
import itertools
import os

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.multireleases import release_simple_config, release_composite_config, release_deliverable
from dmx.abnrlib.releaseinputvalidation import validate_inputs
from dmx.utillib.utils import format_configuration_name_for_printing, get_abnr_id, split_pvlc, get_thread_and_milestone_from_rel_config
from dmx.utillib.multiproc import run_mp
import dmx.ecolib.ecosphere 
from dmx.utillib.admin import get_dmx_admins
from dmx.utillib.arcenv import ARCEnv

class ReleaseTreeError(Exception): pass

class ReleaseTree(object):
    '''
    Runs the releasetree abnr subcommand
    '''

    def __init__(self, project, variant, config, milestone, thread, description, label=None,
                 required_only=False, intermediate=False,  
                 waiver_files=None, force=False, preview=True, 
                 syncpoint='', skipsyncpoint='', skipmscheck='', views=None, regmode=False):
        self.project = project
        self.variant = variant
        self.config = config
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.description = description
        self.required_only = required_only
        self.preview = preview
        self.waiver_files = waiver_files
        self.intermediate = intermediate
        self.force = force
        self.rel_config = None
        self.syncpoint = syncpoint
        self.skipsyncpoint = skipsyncpoint
        self.skipmscheck = skipmscheck
        self.views = views
        self.regmode = regmode

        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)
        self.abnr_id = get_abnr_id()

        # If project not given, get project from ARC
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise ReleaseTreeError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            # Make sure the project exists
            if not self.cli.project_exists(self.project):
                raise ReleaseTreeError("{0} is not a valid project".format(self.project))
            # Make sure the variant exist
            if not self.cli.variant_exists(self.project, self.variant):
                raise ReleaseTreeError("{0}/{1} is not a valid variant".format(self.project, self.variant))

        # If milestone not given, get milestone from ARC
        if not self.milestone:
            self.milestone = ARCEnv().get_milestone()
        # If thread not given, get thread from ARC
        if not self.thread:
            self.thread = ARCEnv().get_thread()
        self.logger.info('Releasing with milestone {} and thread {}'.format(self.milestone, self.thread))            

        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise ReleaseTreeError('{0} does not exist'.format(format_configuration_name_for_printing(self.project, self.variant, self.config)))

        config = ConfigFactory.create_from_icm(self.project, self.variant, self.config)
        # Do we have any unreleased ipspec in the tree?
        unreleased_ipspec = False
        for subconfig in config.flatten_tree():
            if not subconfig.is_config() and not subconfig.is_released():
                if subconfig.libtype == 'ipspec':
                    unreleased_ipspec = True
                    break

        # Common release input validation
        validate_inputs(self.project, self.milestone, self.thread, self.label, self.waiver_files)

    def run(self):
        '''
        The method that runs it all
        '''
        ret = 1
        source_cfg = None

        try:
            # Create the source configuration that we need to walk
            self.logger.info('Building input configuration tree')
            source_cfg = ConfigFactory.create_from_icm(self.project, self.variant, self.config, preview=self.preview)

            # Filter the configuration tree to remove anything we don't need
            self.filter_tree(source_cfg)

            # We no longer need to release ipspec first with the new release flow
            # ipspec can be mutable when we release other deliverable
            #self.release_ipspecs_in_tree(source_cfg)

            # Get all released simple configs in the tree - all the releases here are required for ip release
            released_simple_configs = [x for x in source_cfg.flatten_tree() if not x.is_config() and x.is_released()]
            # http://pg-rdjira:8080/browse/DI-653
            # Ensure that every released config's milestone is greater or equal to the milestone to release
            errors = []
            for simple_config in released_simple_configs:
                thread, milestone = get_thread_and_milestone_from_rel_config(simple_config.name)
                if milestone < self.milestone:
                    errors.append(simple_config.get_full_name())

            # Get all released composite configs in the tree - all the releases here are required for final ip release
            released_composite_configs = [x for x in source_cfg.flatten_tree() if x.is_config() and x.is_released()]
            # http://pg-rdjira:8080/browse/DI-1374
            # Don't  check if skipmscheck is specified
            if not self.skipmscheck:
                # http://pg-rdjira:8080/browse/DI-653
                # Ensure that every released config's milestone is greater or equal to the milestone to release
                for composite_config in released_composite_configs:
                    thread, milestone = get_thread_and_milestone_from_rel_config(composite_config.config)
                    if milestone < self.milestone:
                        errors.append(composite_config.get_full_name())
                if errors:
                    error_msg = 'The following BOMs need to be re-released for milestone {} or \'dmx release\' will not be able to release every IP hierarchically:\n'.format(self.milestone)
                    for error in sorted(errors):
                        error_msg = '{}\t{}\n'.format(error_msg, error)
                    # http://pg-rdjira:8080/browse/DI-1084
                    # Reinstate error status 
                    raise ReleaseTreeError(error_msg)

            # Get all unreleased simple configs in the tree
            unreleased_simple_configs = [x for x in source_cfg.flatten_tree() if not x.is_config() and not x.is_released()]          
            # Release all simple configurations in the tree
            if unreleased_simple_configs:
                self.release_simple_configs(source_cfg, unreleased_simple_configs)
            else:
                self.logger.info('No simple config to be released for {}'.format(source_cfg))
            # Finally, release the composites            
            rel_tree = self.release_all_composite_configs(source_cfg)
            if not rel_tree:
                self.logger.error('Problem building release tree')
                ret = 1
            else:
                self.logger.info('Release Tree {0} built'.format(rel_tree.get_full_name()))
                self.rel_config = rel_tree
                ret = 0
        except Exception:
            if self.intermediate and source_cfg is not None:
                self.build_intermediate_tree(source_cfg)
            raise                

        return ret

    def build_intermediate_tree(self, config_root):
        '''
        Converts the configuration tree in config_root into an intermediate,
        partially released tree and saves it.

        :param config_root: The root of the in-progress configuration tree
        :type config_root: CompositeConfig
        '''
        # First let's clone the root into a new tree
        intermediate_root = config_root.clone(self.intermediate)

        # Now extract all immutable configurations that have been changed, clone
        # them into intermediate configs and then insert them into the intermediate
        # config tree
        # Keep spinning until there's nothing left to do
        configs_to_clone = [x for x in intermediate_root.flatten_tree() if not x.is_mutable() and not x.is_saved(shallow=True)]
        while configs_to_clone:
            for config_to_clone in configs_to_clone:
                new_intermediate = config_to_clone.clone(self.intermediate)
                intermediate_root.replace_object_in_tree(config_to_clone, new_intermediate)

            configs_to_clone = [x for x in intermediate_root.flatten_tree() if not x.is_mutable() and not x.is_saved(shallow=True)]

        # We're done so save the new tree
        if not intermediate_root.save(shallow=False):
            raise ReleaseTreeError('Problem saving intermediate configuration {0}'.format(intermediate_root.get_full_name()))

        return intermediate_root

    def filter_tree(self, root_config):
        '''
        Filters root_config to remove any configurations that we don't want according
        to the command line arguments.

        :param root_config: The root IC Manage configuration object
        :type root_config: CompositeConfig
        '''
        # Only apply the filter to unreleased simple configs
        # that aren't ipspec
        unreleased_simple_configs = [x for x in root_config.flatten_tree() if not x.is_config() and not x.is_released()]
        unreleased_simple_configs = [x for x in unreleased_simple_configs if x.libtype != 'ipspec']

        # Now apply the filters to the tree
        for unreleased_simple in unreleased_simple_configs:
            ipspec_config = self.get_ipspec_config_from_root_config(unreleased_simple.project, unreleased_simple.variant, root_config)
            if not self.should_release_config(unreleased_simple, ipspec_config):
                root_config.remove_object_from_tree(unreleased_simple)

        # Filtering out libtypes can leave us with empty composite configs
        # in the tree, so remove them
        root_config.remove_empty_configs()

    def get_ipspec_config_from_root_config(self, project, variant, root_config):
        ipspec_config = root_config.search('^{}$'.format(project), '^{}$'.format(variant), '^ipspec$')
        if ipspec_config:
            return ipspec_config[0]
        else:
            self.logger.error("Cannot find ipspec for {} from root_config!".format([project, variant]))
            return False

    def release_simple_configs(self, root_config, unreleased_simple_configs):
        '''
        Releases all simple configs in unreleased_simple_configs

        :param root_config: The root configuration object
        :type root_config: CompositeConfig
        :param unreleased_simple_configs: List of simple configs to release
        :type unreleased_simple_configs: list
        :return: Updated root_config
        :rtype: CompositeConfig
        '''
        mp_args = []
        for unreleased_simple in unreleased_simple_configs:
            ipspec_config = ''
            if unreleased_simple.libtype != 'ipspec':
                ipspec = root_config.search(project=unreleased_simple.project, variant='^{0}$'.format(unreleased_simple.variant), libtype='ipspec')

                if not ipspec:
                    raise ReleaseTreeError('Cannot find ipspec for {0}'.format(unreleased_simple.get_full_name()))
                else:
                    ipspec = ipspec[0]
                    # Make sure we haven't extracted the wrong ipspec config name
                    if ipspec.variant != unreleased_simple.variant:
                        raise ReleaseTreeError('Got a bad ipspec for {0}. Found ipspec {1}'.format(unreleased_simple.get_full_name(), ipspec.get_full_name()))
                    ipspec_config = ipspec.name

            # http://pg-rdjira.altera.com:8080/browse/DI-560
            # With the new release flow, we provide the variant level config to release
            # libtype from, not the libtype config
            variant_config = root_config.search(project=unreleased_simple.project, variant='^{0}$'.format(unreleased_simple.variant))[0]

            mp_args.append([unreleased_simple.project, unreleased_simple.variant, unreleased_simple.libtype, variant_config.config, self.milestone, self.thread, self.label, self.description, self.preview, self.force, self.views, self.regmode])

        # We are doing this before releasing deliverable because in ReleaseDeliverable,
        # it might re-use the configuration objects already in the memory
        ConfigFactory.remove_all_objs()

        # http://pg-rdjira.altera.com:8080/browse/DI-560
        # Instead of calling release_simple_config, call release_deliverable
        # which supports the new release flow
        results = run_mp(release_deliverable, mp_args)

        for result in results:
            if not result['success']:
                raise ReleaseTreeError('Problem releasing {0}/{1}:{2}@{3}'.format(result['project'], result['variant'], result['libtype'], result['original_config']))
            else:
                # Only get from IC Manage if we're not in preview mode
                if not self.preview:
                    new_rel_cfg = ConfigFactory.create_from_icm(result['project'], result['variant'], result['released_config'], libtype=result['libtype'], preview=self.preview)
                else:
                    # Create a fake released config with false data. We're only in preview mode
                    # so this should suffice
                    new_rel_cfg = IcmLibrary(result['project'], result['variant'], result['libtype'], 'dev', result['released_config'], preview=self.preview, use_db=False)

                root_config.replace_all_instances_in_tree(new_rel_cfg.project, new_rel_cfg.variant, new_rel_cfg, libtype=new_rel_cfg.libtype)

        return root_config

    def release_all_composite_configs(self, root_config):
        '''
        Releases all composite configs in the tree. Keeps spinning, finding the smallest elements
        until everything is done.

        :param root_config: The root configuration object
        :type root_config: CompositeConfig
        :return: Newly released configuration root
        :rtype: CompositeConfig
        '''
        configs_to_release = root_config.get_configs_ready_for_release()
        if configs_to_release:
            while configs_to_release:
                mp_args = []
                for unreleased_config in configs_to_release:
                    self.logger.info('Processing {0}'.format(unreleased_config.get_full_name()))
                    sub_configs = [x.get_full_name() for x in unreleased_config.configurations]
                    mp_args.append([unreleased_config.project, unreleased_config.variant, sub_configs, self.milestone, self.thread, self.label, self.description, self.preview, self.waiver_files, self.force, self.views, self.syncpoint, self.skipsyncpoint, self.skipmscheck, None, self.regmode])
    
                results = run_mp(release_composite_config, mp_args)
    
                for result in results:
                    if result['success']:
                        if not self.preview:
                            new_rel_cfg = ConfigFactory.create_from_icm(result['project'], result['variant'], result['released_config'], preview=self.preview)
                        else:
                            # Create a fake released config with false data. We're only in preview mode
                            # so this should suffice
                            new_rel_cfg = IcmConfig(result['released_config'], result['project'], result['variant'], [], preview=self.preview)
                    else:
                        raise ReleaseTreeError('Problem releasing variant for {0}/{1}'.format(result['project'], result['variant']))
    
                    # Did we just release root?
                    if len(configs_to_release) == 1 and configs_to_release[0] == root_config:
                        root_config = new_rel_cfg
                    else:
                        root_config.replace_all_instances_in_tree(new_rel_cfg.project, new_rel_cfg.variant, new_rel_cfg)
    
                configs_to_release = root_config.get_configs_ready_for_release()
        else:
            self.logger.info('No composite config to be released for {}'.format(root_config))                

        return root_config

    def should_release_config(self, simple_config, ipspec_config):
        '''
        Checks if simple_config should be released
        Returns True if it should, False if it shouldn't
        :param simple_config: Simple Configuration being checked
        :type simple_config: SimpleConfig
        :return: bool
        '''
        ret = True

        # Do we need to release this config according to the roadmap?
        if self.required_only and not self.is_libtype_required_by_milestone_and_thread(simple_config, ipspec_config):
            ret = False

        return ret

    def find_ipspecs(self, root_config):
        '''
        Finds and returns all ipspec simple configs within root_config
        :param root_config: The root composite configuration
        :type root_config: ICMConfig
        :return: List of ipspec SimpleConfigs
        '''
        results = root_config.search(libtype='ipspec')
        # Remove duplicates
        ipspecs = list(set(results))

        return ipspecs

    def release_ipspecs_in_tree(self, root_config):
        '''
        Replaces all instances of non-released ipspsecs
        with their released equivalents
        :param root_config: The root IC Manage Composite config
        :type root_config: CompositeConfig
        '''
        ipspecs = self.find_ipspecs(root_config)
        ipspecs_to_release = [x for x in ipspecs if not x.is_released()]
        if ipspecs_to_release:
            self.release_simple_configs(root_config, ipspecs_to_release)
        else:
            self.logger.info('No ipspec to be released for {}'.format(root_config))           

    def is_libtype_required_by_milestone_and_thread(self, simple_config, ipspec_config):
        '''
        Determines if the content referenced by simple_config is required to be
        released within this milestone/thread combination
        :param simple_config: The Simple Config being considered for release
        :return: bool
        '''
        ret = False

        product = self.thread.split('rev')[0]
        family = dmx.ecolib.ecosphere.EcoSphere(preview=True).get_family_for_thread(self.thread)
        roadmap = family.get_product(product).roadmap

        ip = family.get_ip(simple_config.variant, simple_config.project)
        ipspecbom = 'ipspec@{}'.format(ipspec_config.name)
        required_libtypes = [x.deliverable for x in ip.get_deliverables(milestone=self.milestone, roadmap=roadmap, views=self.views, local=False, bom=ipspecbom)]

        if simple_config.libtype in required_libtypes:
            ret = True

        return ret
