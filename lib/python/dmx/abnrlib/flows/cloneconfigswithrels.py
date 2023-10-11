#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cloneconfigswithrels.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: cloneconfigswithrels abnr subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import os
import sys
import logging
import textwrap

from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import format_configuration_name_for_printing
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.ecolib.ecosphere
from dmx.utillib.arcenv import ARCEnv

class CloneConfigsWithRelsError(Exception): pass

class CloneConfigsWithRels(object):
    '''
    Runs the cloneconfigswithrels command
    '''
    def __init__(self, project, variant, config, new_config, milestone, thread,
                 stop, use_labeled, preview=True):
        self.project = project
        self.variant = variant
        self.config = config
        self.new_config = new_config
        self.milestone = milestone
        self.thread = thread
        self.stop = stop
        self.use_labeled = use_labeled
        self.preview = preview

        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI(preview=self.preview)

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise CloneConfigsWithRelsError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else: 
            if not self.cli.project_exists(self.project):
                raise CloneConfigsWithRelsError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise CloneConfigsWithRelsError("{0}/{1} does not exist".format(self.project, self.variant))    
        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise CloneConfigsWithRelsError('Configuration {0} does not exist'.format(
                format_configuration_name_for_printing(self.project, self.variant,
                                                       self.config)
            ))

        if self.cli.config_exists(self.project, self.variant, self.new_config):
            raise CloneConfigsWithRelsError('New configuration {0} already exists'.format(
                format_configuration_name_for_printing(self.project, self.variant,
                                                       self.config)
            ))

        family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
        if not family.verify_roadmap(self.milestone, self.thread):
            raise CloneConfigsWithRelsError('Milestone and thread combination invalid')

    def run(self):
        '''
        Executes the subcommand
        '''
        ret = 1

        if self.clone_and_replace():
            ret = 0
        else:
            ret = 1

        return ret

    def clone_and_replace(self):
        '''
        Clones the configuration and replaces the subconfigs
        '''
        ret = False

        self.logger.info('Building source configuration tree')
        source_config = ConfigFactory.create_from_icm(self.project, self.variant, self.config,
                                                      preview=self.preview)

        clone = source_config.clone(self.new_config)

        if self.replace_with_rels(source_config, clone):
            if not clone.save(shallow=True):
                raise CloneConfigsWithRelsError('Problem saving new configuration {0}'.format(clone.get_full_name()))
            else:
                ret = True

        return ret


    def replace_with_rels(self, source_config, clone):
        '''
        Replaces all sub-configurations from source_config with the latest
        REL
        '''
        ret = False
        no_rel = False

        for sub_config in source_config.configurations:
            if sub_config.is_composite():
                latest_rel = self.cli.get_latest_rel_config(sub_config.project, sub_config.variant,
                                                   milestone=self.milestone,
                                                   thread=self.thread)
                if not latest_rel and self.use_labeled:
                    # Try again, this time considering labeled REL configs
                    latest_rel = self.cli.get_latest_rel_config_with_label(sub_config.project,
                                                                           sub_config.variant,
                                                                           milestone=self.milestone,
                                                                           thread=self.thread)
                if not latest_rel:
                    self.logger.warn('No REL{0}{1} configuration found for {2}/{3}'.format(self.milestone,
                                                                                self.thread,
                                                                                sub_config.project,
                                                                                sub_config.variant))
                    no_rel = True
                else:
                    rel_config = ConfigFactory.create_from_icm(sub_config.project, sub_config.variant,
                                                               latest_rel, preview=self.preview)
                    self.logger.info('Replacing {0} with {1}'.format(sub_config.get_full_name(), rel_config.get_full_name()))
                    clone.replace_config_in_tree(sub_config, rel_config)

        if no_rel and self.stop:
            self.logger.error('Could not find REL configurations for all composite sub-configurations. Stopping.')
        else:
            ret = True

        return ret
