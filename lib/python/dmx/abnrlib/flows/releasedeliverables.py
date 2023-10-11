#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releasedeliverables.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "releasetee" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import logging
import textwrap
from collections import namedtuple
import itertools
import sys, os

from dmx.abnrlib.config_factory import ConfigFactory
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.multireleases import release_deliverable
from dmx.abnrlib.releaseinputvalidation import validate_inputs
from dmx.utillib.multiproc import run_mp
from dmx.abnrlib.icm import ICManageCLI
import dmx.ecolib.ecosphere 
from dmx.utillib.admin import get_dmx_admins
from dmx.utillib.arcenv import ARCEnv

class ReleaseDeliverablesError(Exception): pass

class ReleaseDeliverables(object):
    '''
    Runner subclass for the abnr releaselibraries command
    '''

    def __init__(self, project, ip, bom, deliverables, milestone, thread, description,
                 label=None, force=False, preview=True, regmode=False):

        self.logger = logging.getLogger(__name__)
        self.logger.info('Building input configuration tree')  
        self.project = project
        self.variant = ip          
        self.config = bom
        self.libtypes = deliverables
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.preview = preview
        self.description = description
        self.force = force
        self.regmode = regmode
        self.cli = ICManageCLI(preview=preview)
        self.waiver_files = []

        # If project not given, get project from ARC
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise ReleaseDeliverablesError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            # Make sure the project exists
            if not self.cli.project_exists(self.project):
                raise ReleaseDeliverablesError("{0} is not a valid project".format(self.project))
            # Make sure the variant exist
            if not self.cli.variant_exists(self.project, self.variant):
                raise ReleaseDeliverablesError("{0}/{1} is not a valid variant".format(self.project, self.variant))

        # If milestone not given, get milestone from ARC
        if not self.milestone:
            self.milestone = ARCEnv().get_milestone()
        # If thread not given, get thread from ARC
        if not self.thread:
            self.thread = ARCEnv().get_thread()
        self.logger.info('Releasing with milestone {} and thread {}'.format(self.milestone, self.thread))            

        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise ReleaseDeliverablesError('{0} does not exist'.format((self.project, self.variant, self.config)))

        for libtype in self.libtypes:
            # Make sure the libtype is defined within the system
            if not self.cli.libtype_defined(libtype):
                raise ReleaseDeliverablesError('Libtype {0} is not defined within the system.'.format(libtype))            
            
        # Common release input validation
        validate_inputs(self.project, self.milestone, self.thread, self.label, self.waiver_files)
        self.source_config = ConfigFactory.create_from_icm(self.project, self.variant, self.config, preview=preview)

    def release_all_simple_configs(self):
        '''
        Releases all unreleased simple configs provided in self.libtypes

        :param wip_config: The work-in-progress CompositeConfig object
        :type wip_config: CompositeConfig
        '''
        unreleased_simple_configs = [x for x in self.source_config.flatten_tree() if not x.is_config() and not x.is_released()]

        configs_to_release = self.filter_configs(unreleased_simple_configs)
        released_configs = self.release_configs(configs_to_release)
        return released_configs

    def release_configs(self, configs_to_release):
        '''
        Runs multiple releaselibs in parallel in order to release the simple configs.

        :param config_pairs: List of ConfigPairs
        :type config_pairs: list
        :return: List of released configs
        :rtype: list
        '''
        mp_args = []
        for config in configs_to_release:            
            self.logger.debug('Adding release request for {0} to pool'.format(
                config.get_full_name()
            ))
            # We need to provide the composite config not the libtype config
            parent_config = list(config.parents)[0].config
            mp_args.append([config.project, config.variant, config.libtype, parent_config,
                            self.milestone, self.thread, self.label,
                            self.description, self.preview, 
                            self.force, [], self.regmode])

        results = run_mp(release_deliverable, mp_args)
        released_configs = []
        for result in results:
            if not result['success']:
                raise ReleaseDeliverablesError('Problem releasing {0}/{1}:{2}@{3}'.format(
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
                    new_rel_cfg = IcmLibrary(result['project'],
                                               result['variant'], result['libtype'],
                                               'dev', result['released_config'],
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
        if not self.libtypes:
            filtered_configs = configs
        else:
            filtered_configs = [x for x in configs if x.libtype in self.libtypes]

        return filtered_configs

    def run(self):
        '''
        Runs the ReleaseDeliverables 
        '''
        ret = 1

        self.logger.info('Releasing deliverables')        
        released_configs = self.release_all_simple_configs()
        self.logger.info('BOMs released:')
        for config in sorted(released_configs):
            self.logger.info('\t{}'.format(config.get_full_name()))

        ret = 0

        return ret

