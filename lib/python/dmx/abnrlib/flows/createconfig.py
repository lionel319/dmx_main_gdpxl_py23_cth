#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/createconfig.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: bomcreate abnr subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2013
All rights reserved.
'''

import sys
import logging
import textwrap
import itertools
import os
import re

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.utillib.utils import format_configuration_name_for_printing, add_common_args
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.syncpoint import SyncPoint
from dmx.utillib.arcenv import ARCEnv

class CreateConfigError(Exception): pass

class CreateConfig(object):
    '''
    The class that handles the exection of the bomcreate command
    Builds a new configuration containing the configurations specified
    by the user on the command line
    '''
    def __init__(self, project, variant, config, sub_configs, config_file, description, 
                 syncpoints=None, syncpoint_configs=None, preview=True):
        '''
        Class initialiser
        '''
        self.project = project
        self.variant = variant
        self.config = config
        self.preview = preview
        self.config_file = config_file
        self.sub_configs = sub_configs
        self.description = description
        self.syncpoints = syncpoints
        self.syncpoint_configs = syncpoint_configs
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise CreateConfigError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))

        else:
            if not self.cli.project_exists(self.project):
                raise CreateConfigError("Project {0} does not exist".format(self.project))

            if not self.cli.variant_exists(self.project, self.variant):
                raise CreateConfigError("Variant {0} does not exist in project {1}".format(self.variant, self.project))

        # If the configuration already exists this is an error
        if self.cli.config_exists(self.project, self.variant, self.config):
            raise CreateConfigError("{0} already exists. This command can only be used to build new configurations".format(format_configuration_name_for_printing(self.project, self.variant, self.config)))

        # We cannot create a immutable configuration, only dmx snap/release can do that
        if self.cli.is_name_immutable(self.config):
            raise CreateConfigError("You cannot use dmx bom create to create immutable configurations. Use dmx snap/release instead.")

        # If there are no sub_configs we have nothing to do
        if not self.sub_configs and not self.config_file and not self.syncpoints and not self.syncpoint_configs:
            raise CreateConfigError("You have not specified any configurations to include, input file or syncpoints")

        # If the file is specified make sure it exists
        if self.config_file:
            if not os.path.exists(self.config_file):
                raise CreateConfigError('File {0} does not exist'.format(self.config_file))

    def run(self):
        '''
        Builds the configuration
        '''
        ret = 1

        # If an input file was specified read the contents and add
        # to sub_configs
        if self.config_file:
            self.sub_configs.extend(self.get_list_of_configs_from_file())

        # Add the syncpoint config names
        if self.syncpoint_configs:
            self.sub_configs.extend(self.get_full_config_names_from_syncpoint_configs())

        # Add all onfigs from any syncpoints
        if self.syncpoints:
            self.sub_configs.extend(self.get_full_config_names_from_syncpoints())

        # Get the list of sub configuration objects
        sub_configurations = self.convert_sub_configs_to_objects()

        if sub_configurations:
            # Build our new configuration
            self.logger.info("Building configuration {0}".format(format_configuration_name_for_printing(self.project, self.variant, self.config)))
            new_config = IcmConfig(self.config, self.project, self.variant, sub_configurations, description=self.description, preview=self.preview)

            # Try to save the configuration
            if new_config.save(shallow=True):
                self.logger.info("Configuration {0} built".format(new_config.get_full_name()))
                ret = 0
            else:
                raise CreateConfigError("Could not save {0} to the IC Manage database".format(new_config.get_full_name()))
        else:
            self.logger.error("Problem building sub configurations")
            ret = 1

        return ret

    def get_list_of_configs_from_file(self):
        '''
        Reads the input file and returns a list of configurations
        specified within
        '''
        ret = []
        with open(self.config_file, 'r') as config_file:
            for line in config_file.readlines():
                # Skip comments and empty lines
                if line.startswith('#'):
                    continue

                if not line.rstrip():
                    continue

                ret.append(line.rstrip())

        return ret

    def convert_sub_configs_to_objects(self):
        '''
        Converts the list of sub_configs into IC Manage configuration objects
        '''
        config_objects = []

        for config_arg in self.sub_configs:

            ### config_arg might be
            ### - project/variant@config
            ### - project/variant:libtype@config
            ### tmp might be
            ### - [project, variant, config]
            ### - [project, variant, libtype, config]
            tmp = re.sub('[/:@]', ' ', config_arg.strip()).split()
            project = tmp[0]
            variant = tmp[1]
            if len(tmp) == 3:
                libtype = ''
                config = tmp[2]
            else:
                libtype = tmp[2]
                config = tmp[3]

            self.logger.debug("Processing {}".format(config_arg))
            config_objects.append(ConfigFactory.create_from_icm(project, variant, config, libtype=libtype, preview=self.preview))

        return config_objects

    def get_full_config_names_from_syncpoint_configs(self):
        '''
        Converts the list of project/variant@syncpoints into a list of full config names - i.e.
        project/variant@config
        '''
        ret = []
        sp = SyncPoint()

        for syncpoint_config_name in self.syncpoint_configs:
            (project, variant, syncpoint) = sp.split_syncpoint_name(syncpoint_config_name)
            full_config_name = sp.convert_syncpoint_to_full_config_name(project, variant, syncpoint)
            ret.append(full_config_name)

        return ret

    def get_full_config_names_from_syncpoints(self):
        '''
        For each config associated with a syncpoint gets it's full config name
        Returns a list of all the full config names associated with a syncpoint
        '''
        ret = []
        sp = SyncPoint()

        for syncpoint in self.syncpoints:
            all_syncpoint_configs = sp.get_all_configs_for_syncpoint(syncpoint)
            if not all_syncpoint_configs:
                raise CreateConfigError('Syncpoint {0} does not have any configs associated with it'.format(
                    syncpoint
                ))

            for (project, variant, config) in all_syncpoint_configs:
                if config is not None:
                    ret.append(format_configuration_name_for_printing(project, variant, config))
                else:
                    self.logger.warn('{0}/{1} has no associated configuration for syncpoint {2}'.format(
                        project, variant, syncpoint
                    ))

        return ret
