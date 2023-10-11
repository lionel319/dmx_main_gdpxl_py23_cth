#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releaselibraries.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "releasetee" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.

DEPRECATED: Replaced by releasedeliverables.py

'''
import logging
import textwrap
from collections import namedtuple
import itertools
import sys, os

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.multireleases import release_simple_config
from dmx.abnrlib.releaseinputvalidation import validate_inputs
from dmx.utillib.multiproc import run_mp
from dmx.abnrlib.icm import ICManageCLI

ConfigPair = namedtuple('ConfigPair', 'config ipspec')
class ReleaseLibrariesError(Exception): pass

class ReleaseLibraries(object):
    '''
    Runner subclass for the abnr releaselibraries command
    '''

    def __init__(self, project, variant, config, milestone, thread, description, label=None,
                 variant_filter=[], libtype_filter=[], inplace=False, new_config=None, 
                 waiver_files=None, force=False, release_snap=False, 
                 preview=True):

        self.logger = logging.getLogger(__name__)
        self.logger.info('Building input configuration tree')
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.preview = preview
        self.description = description
        self.variant_filter = variant_filter
        self.libtype_filter = libtype_filter
        self.inplace = inplace
        self.new_config = new_config
        self.waiver_files = waiver_files
        self.force = force
        self.release_snap = release_snap
        self.cli = ICManageCLI(preview=preview)

        # Make sure the project exists
        if not self.cli.project_exists(project):
            raise ReleaseLibrariesError("{0} is not a valid project".format(project))
        # Make sure the variant exist
        if not self.cli.variant_exists(project, variant):
            raise ReleaseLibrariesError("{0}/{1} is not a valid variant".format(project, variant))

        # Common release input validation
        validate_inputs(project, self.milestone, self.thread, self.label,
                        self.waiver_files)

        if not self.inplace and not self.new_config:
            raise ReleaseLibrariesError('You must specify at least one of --inplace or --new-config')

        if self.inplace and config.startswith(('snap-', 'REL')):
            raise ReleaseLibrariesError('Cannot modify an immutable configuration in place. Use the --new-config option.')

        if self.new_config and self.new_config.startswith(('snap-', 'REL')):
            raise ReleaseLibrariesError('The --new-config configuration name cannot be an immutable config')
        
        self.source_config = ConfigFactory.create_from_icm(project, variant, config,
                                                           preview=preview)

    def release_ipspecs(self, wip_config):
        '''
        Releases all unreleased ipspec simple configs within the filters and places
        the REL configs into wip_config.

        :param wip_config: The work-in-progress CompositeConfig object
        :type wip_config: CompositeConfig
        '''
        if self.release_snap:
            unreleased_ipspecs = [x for x in wip_config.flatten_tree() if x.is_simple() and x.libtype == 'ipspec' and not x.config.startswith('REL')]            
        else:            
            unreleased_ipspecs = [x for x in wip_config.flatten_tree() if x.is_simple() and x.libtype == 'ipspec' and x.is_mutable()]

        ipspecs_to_release = self.filter_configs(unreleased_ipspecs)
        # Build the ConfigPairs list with empty ipspecs
        config_pairs = []
        for ipspec in ipspecs_to_release:
            config_pairs.append(ConfigPair(config=ipspec, ipspec=None))

        released_ipspecs = self.release_configs(config_pairs)
        for released_ipspec in released_ipspecs:
            wip_config.replace_all_instances_in_tree(released_ipspec.project, released_ipspec.variant,
                                                     released_ipspec, libtype=released_ipspec.libtype)

    def release_all_simple_configs(self, wip_config):
        '''
        Releases all unreleased simple configs that are within the filters and places the REL configs
        into the wip_config tree.

        :param wip_config: The work-in-progress CompositeConfig object
        :type wip_config: CompositeConfig
        '''
        if self.release_snap:
            unreleased_simple_configs = [x for x in wip_config.flatten_tree() if x.is_simple() and not x.config.startswith('REL')]
        else:            
            unreleased_simple_configs = [x for x in wip_config.flatten_tree() if x.is_simple() and x.is_mutable()]

        configs_to_release = self.filter_configs(unreleased_simple_configs)
        # Build the ConfigPairs list with ipspecs
        config_pairs = []
        for simple_config in configs_to_release:
            ipspec = wip_config.search(project='^{0}$'.format(simple_config.project),
                                       variant='^{0}$'.format(simple_config.variant),
                                       libtype='^ipspec$')[0]
            config_pairs.append(ConfigPair(config=simple_config, ipspec=ipspec))
        released_configs = self.release_configs(config_pairs)
        for released_config in released_configs:
            wip_config.replace_all_instances_in_tree(released_config.project, released_config.variant,
                                                     released_config, libtype=released_config.libtype)

    def release_configs(self, config_pairs):
        '''
        Runs multiple releaselibs in parallel in order to release the simple configs.

        :param config_pairs: List of ConfigPairs
        :type config_pairs: list
        :return: List of released configs
        :rtype: list
        '''
        mp_args = []
        for pair in config_pairs:
            config = pair.config
            # ipspec won't be set if we're trying to release ipspec so work
            # around the possibility of it being None in the pair
            if pair.ipspec is not None:
                ipspec_config = pair.ipspec.config
            else:
                ipspec_config = ''

            self.logger.debug('Adding release request for {0} with ipspec {1} to pool'.format(
                config.get_full_name(), ipspec_config
            ))
            mp_args.append([config.project, config.variant, config.libtype, config.config,
                            ipspec_config, self.milestone, self.thread, self.label,
                            self.description, self.preview, 
                            self.waiver_files, self.force])

        results = run_mp(release_simple_config, mp_args)
        released_configs = []
        for result in results:
            if not result['success']:
                raise ReleaseLibrariesError('Problem releasing {0}/{1}:{2}@{3}'.format(
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

                released_configs.append(new_rel_cfg)

        return released_configs


    def filter_configs(self, configs):
        '''
        Removes all configurations from configs that do not match our filters.

        :param configs: List of simple configuration objects
        :type configs: list
        :return: Filtered list of simple configs
        :rtype: list
        '''
        filtered_configs = []
        # Only apply the filters if there are any!
        if not self.libtype_filter and not self.variant_filter:
            filtered_configs = configs
        else:
            for config in configs:
                variant_match = False
                libtype_match = False

                if self.variant_filter:
                    if config.variant in self.variant_filter:
                        variant_match = True
                else:
                    variant_match = True

                if self.libtype_filter:
                    # All ipspecs must be released in order to release other libtypes
                    # from the variant
                    if config.libtype in self.libtype_filter or config.libtype == 'ipspec':
                        libtype_match = True
                else:
                    libtype_match = True

                if variant_match and libtype_match:
                    filtered_configs.append(config)

        return filtered_configs

    def rename_modified_configs(self, wip_config):
        '''
        Renames any modified configs to self.new_config

        :param wip_config: Work in progress IC Manage composite config object
        :type wip_config: CompositeConfig
        '''
        # First we need to update the immutable configs
        wip_config.convert_modified_immutable_configs_into_mutable(self.new_config)

        # Only modify the mutable configs if we're not in 'in place' mode
        if not self.inplace:
            wip_config.rename_modified_mutable_configs(self.new_config)

    def run(self):
        '''
        Runs the ReleaseLibraries 
        '''
        ret = 1

        if self.inplace:
            wip_config = self.source_config
        else:
            wip_config = self.source_config.clone(self.new_config)

        self.logger.info('Releasing all ipspecs')
        self.release_ipspecs(wip_config)
        self.logger.info('Releasing simple configs')
        self.release_all_simple_configs(wip_config)

        if self.new_config:
            self.rename_modified_configs(wip_config)

        if wip_config.save(shallow=False):
            ret = 0
        else:
            ret = 1

        return ret

