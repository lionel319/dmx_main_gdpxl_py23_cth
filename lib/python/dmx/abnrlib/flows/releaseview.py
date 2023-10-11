#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releaseview.py#1 $
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
import datetime

from dmx.abnrlib.icm import ICManageCLI
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
#from dmx.abnrlib.icmcompositeconfig import CompositeConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.multireleases import release_simple_config, release_composite_config, release_deliverable
from dmx.abnrlib.releaseinputvalidation import validate_inputs
from dmx.utillib.utils import format_configuration_name_for_printing, split_pvlc, get_thread_and_milestone_from_rel_config
from dmx.utillib.multiproc import run_mp
import dmx.ecolib.ecosphere
from dmx.utillib.admin import get_dmx_admins
from dmx.utillib.arcenv import ARCEnv

class ReleaseViewError(Exception): pass

class ReleaseView(object):
    '''
    Runs the releaseview abnr subcommand
    '''

    def __init__(self, project, variant, views, config, milestone, thread,
                 description, label=None, preview=True, syncpoint='', 
                 skipsyncpoint='', skipmscheck='', regmode=False):
        self.project = project
        self.variant = variant
        self.views = views
        self.config = config
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.description = description
        self.preview = preview
        self.rel_config = None
        self.syncpoint = syncpoint
        self.skipsyncpoint = skipsyncpoint
        self.skipmscheck = skipmscheck
        self.regmode = regmode

        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)

        # If project not given, get project from ARC
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise ReleaseViewError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            # Make sure the project exists
            if not self.cli.project_exists(self.project):
                raise ReleaseViewError("{0} is not a valid project".format(self.project))
            # Make sure the variant exist
            if not self.cli.variant_exists(self.project, self.variant):
                raise ReleaseViewError("{0}/{1} is not a valid variant".format(self.project, self.variant))

        # If milestone not given, get milestone from ARC
        if not self.milestone:
            self.milestone = ARCEnv().get_milestone()
        # If thread not given, get thread from ARC
        if not self.thread:
            self.thread = ARCEnv().get_thread()
        self.logger.info('Releasing with milestone {} and thread {}'.format(self.milestone, self.thread))            

        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise ReleaseViewError('{0} does not exist'.format(
                format_configuration_name_for_printing(self.project, self.variant,
                                                       self.config)
            ))

        # Common release input validation
        validate_inputs(self.project, self.milestone, self.thread, self.label,
                        [])            

        family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_thread(self.thread)
        product = self.thread.split('rev')[0]
        roadmap = family.get_product(product).roadmap

        for view in views:
            # Ensure only views are provided
            if not view.startswith('view_'):
                raise ReleaseViewError('{} cannot be provided together with view. Only views are allowed. View must start with \'view_\''.format(view))
            
            # Ensure views are valid
            try:
                viewobj = family.get_view(view)
            except Exception as e:
                self.logger.error('View ({}) does not exist'.format(view))
                raise ReleaseViewError(e)

        ip = family.get_ip(self.variant, self.project)
        libtypes_to_release = ip.get_deliverables(milestone=self.milestone, views=self.views, local=False, bom=self.config, roadmap=roadmap)
        self.source_cfg = ConfigFactory.create_from_icm(self.project, self.variant, self.config, preview=self.preview)

        self.deliverables = [x.deliverable for x in libtypes_to_release]

        # Do we have any unreleased ipspec in the tree?
        # We don't use flatten_tree as this is not a hierarchical release
        unreleased_ipspec = False
        for subconfig in self.source_cfg.configurations:
            if not subconfig.is_config() and not subconfig.is_released():
                if subconfig.libtype == 'ipspec':
                    unreleased_ipspec = True
                    break

    def run(self):
        '''
        The method that runs it all
        '''
        ret = 1

        # Filter the configuration tree to remove anything we don't need
        self.filter_tree()

        # Get all released simple configs in the tree - all the releases here are required for ip release
        released_simple_configs = [x for x in self.source_cfg.configurations if not x.is_config() and x.is_released()]
        # http://pg-rdjira:8080/browse/DI-653
        # Ensure that every released config's milestone is greater or equal to the milestone to release
        errors = []
        for simple_config in released_simple_configs:
            thread, milestone = get_thread_and_milestone_from_rel_config(simple_config.name)
            if milestone < self.milestone:
                errors.append(simple_config.get_full_name())

        # Every sub-composite configs must be released
        unreleased_composite_configs = [x.get_full_name() for x in self.source_cfg.configurations if x.is_config() and not x.is_released()]
        if unreleased_composite_configs:
            error_msg = 'The following BOMs need to be released or \'dmx release\' will not be able to release this IP:\n'
            for unreleased_composite_config in sorted(unreleased_composite_configs):
                error_msg = '{}\t{}\n'.format(error_msg, unreleased_composite_config)
            raise ReleaseViewError(error_msg) 

        # For released composite configs, they must satisfy the milestone requirement
        if not self.skipmscheck:
            released_composite_configs = [x for x in self.source_cfg.configurations if x.is_config() and x.is_released()]
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
                raise ReleaseViewError(error_msg) 

        # Phew, now we get to release the simple configs
        # Get all unreleased simple configs in the tree
        unreleased_simple_configs = [x for x in self.source_cfg.configurations if not x.is_config() and not x.is_released()]          
        # Release all simple configurations in the tree
        if unreleased_simple_configs:
            # We need to clone our filtered config and pass this config to ReleaseDeliverable or it will pick up the unfiltered configs
            datetimestr = datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
            self.cloned_config = self.source_cfg.clone('{}_releaseview_{}'.format(self.config, datetimestr))
            self.cloned_config.save()
            try:                
                self.release_simple_configs(unreleased_simple_configs)            
            except:
                raise                
            finally:                
                if not self.preview:
                    # Removes the cloned config when we are done
                    # self.cloned_config.delete()
                    pass
        else:
            self.logger.info('No simple config to be released for {}'.format(self.source_cfg))
        # Finally, release the composites            
        rel_tree = self.release_all_composite_configs()
        if not rel_tree:
            self.logger.error('Problem building release tree')
            ret = 1
        else:
            self.logger.info('Release BOM {0} built'.format(rel_tree.get_full_name()))
            self.rel_config = rel_tree
            ret = 0
             
        return ret

    def filter_tree(self):
        '''
        Filters self.source_cfg to remove any configurations that we don't want according
        to the command line arguments.
        '''
        simple_configs_to_remove = []
        # Remove deliverables outside of views
        for config in self.source_cfg.configurations:
            if not config.is_config() and config.libtype not in self.deliverables:
                simple_configs_to_remove.append(config)

        for config in simple_configs_to_remove:
            self.source_cfg.remove_object_from_tree(config)

    def release_simple_configs(self, unreleased_simple_configs):
        '''
        Releases all simple configs in unreleased_simple_configs

        :param unreleased_simple_configs: List of simple configs to release
        :type unreleased_simple_configs: list
        :return: Updated self.source_cfg
        :rtype: CompositeConfig
        '''
        # We are using self.cloned_config instead of self.source_cfg because we need ReleaseDeliverable to read in the filtered tree
        # Otherwise when ReleaseDeliverable creates it's own ConfigFactory object, it's gonna see an unfiltered tree
        mp_args = []
        for unreleased_simple in unreleased_simple_configs:
            ipspec_config = ''
            if unreleased_simple.libtype != 'ipspec':
                ipspec = self.cloned_config.search(project=unreleased_simple.project,
                                            variant='^{0}$'.format(unreleased_simple.variant),
                                            libtype='ipspec')

                if not ipspec:
                    raise ReleaseViewError('Cannot find ipspec for {0}'.format(unreleased_simple.get_full_name()))
                else:
                    ipspec = ipspec[0]
                    # Make sure we haven't extracted the wrong ipspec config name
                    if ipspec.variant != unreleased_simple.variant:
                        raise ReleaseViewError('Got a bad ipspec for {0}. Found ipspec {1}'.format(
                            unreleased_simple.get_full_name(), ipspec.get_full_name()
                        ))
                    ipspec_config = ipspec.name

            # http://pg-rdjira.altera.com:8080/browse/DI-560
            # With the new release flow, we provide the variant level config to release
            # libtype from, not the libtype config
            variant_config = self.cloned_config.search(project=unreleased_simple.project,
                                        variant='^{0}$'.format(unreleased_simple.variant))[0]

            mp_args.append([unreleased_simple.project, unreleased_simple.variant,
                            unreleased_simple.libtype, variant_config.config,
                            self.milestone, self.thread, self.label,
                            self.description, self.preview,
                            False, self.views, self.regmode])

        # We are doing this before releasing deliverable because in ReleaseDeliverable,
        # it might re-use the configuration objects already in the memory
        ConfigFactory.remove_all_objs()

        # http://pg-rdjira.altera.com:8080/browse/DI-560
        # Instead of calling release_simple_config, call release_deliverable
        # which supports the new release flow
        results = run_mp(release_deliverable, mp_args)

        for result in results:
            if not result['success']:
                raise ReleaseViewError('Problem releasing {0}/{1}:{2}@{3}'.format(
                    result['project'], result['variant'], result['libtype'],
                    result['original_config']
                ))
            else:
                # Only get from IC Manage if we're not in preview mode
                if not self.preview:
                    new_rel_cfg = ConfigFactory.create_from_icm(result['project'],
                                                                result['variant'],
                                                                result['released_config'],
                                                                libtype=result['libtype'],
                                                                preview=self.preview)
                else:
                    # Create a fake released config with false data. We're only in preview mode
                    # so this should suffice
                    new_rel_cfg = SimpleConfig(result['released_config'], result['project'],
                                               result['variant'], result['libtype'],
                                               'dev', '1',
                                               preview=self.preview, use_db=False)

                # But over here, we don't use self.cloned_config. Why?
                # Because we are using source_cfg object to modify the tree and eventually passes this to ReleaseVariant
                self.source_cfg.replace_all_instances_in_tree(new_rel_cfg.project, new_rel_cfg.variant, new_rel_cfg, libtype=new_rel_cfg.libtype)

        return self.source_cfg

    def release_all_composite_configs(self):
        '''
        Releases all composite configs in the tree. Keeps spinning, finding the smallest elements
        until everything is done.

        :return: Newly released configuration root
        :rtype: CompositeConfig
        '''
        configs_to_release = self.source_cfg.get_configs_ready_for_release()
        if configs_to_release:
            while configs_to_release:
                mp_args = []
                for unreleased_config in configs_to_release:
                    self.logger.info('Processing {0}'.format(unreleased_config.get_full_name()))
                    sub_configs = [x.get_full_name() for x in unreleased_config.configurations]
                    mp_args.append([unreleased_config.project, unreleased_config.variant, sub_configs,
                                    self.milestone, self.thread, self.label, self.description,
                                    self.preview, [],
                                    False, self.views, self.syncpoint, self.skipsyncpoint, 
                                    self.skipmscheck, None, self.regmode])
    
                results = run_mp(release_composite_config, mp_args)
    
                for result in results:
                    if result['success']:
                        new_rel_cfg = ConfigFactory.create_from_icm(result['project'], result['variant'], result['released_config'], preview=self.preview)
                    else:
                        raise ReleaseViewError('Problem releasing variant for {0}/{1}'.format(
                            result['project'], result['variant']))
    
                    # Did we just release root?
                    if len(configs_to_release) == 1 and configs_to_release[0] == self.source_cfg:
                        self.source_cfg = new_rel_cfg
                    else:
                        self.source_cfg.replace_all_instances_in_tree(new_rel_cfg.project, new_rel_cfg.variant,
                                                                  new_rel_cfg)
    
                configs_to_release = self.source_cfg.get_configs_ready_for_release()
        else:
            self.logger.info('No composite config to be released for {}'.format(self.source_cfg))                

        return self.source_cfg

