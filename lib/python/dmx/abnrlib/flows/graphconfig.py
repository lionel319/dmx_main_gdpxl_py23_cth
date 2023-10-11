#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/graphconfig.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr graphconfig"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import subprocess
import logging
import textwrap
import os

from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import format_configuration_name_for_printing, run_command
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.arcenv import ARCEnv

class GraphConfigError(Exception): pass

class GraphConfig(object):
    '''
    Runs the abnr graphconfig command
    '''
    def __init__(self, project, variant, config, file_name):
        self.project = project
        self.variant = variant
        self.config = config
        self.base_file_name = file_name
        self.dot_file_name = '{}.dot'.format(self.base_file_name)
        self.gif_file_name = '{}.gif'.format(self.base_file_name)
        self.cli = ICManageCLI()
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
                raise GraphConfigError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise GraphConfigError('Project {0} does not exist'.format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise GraphConfigError('Variant {0} does not exist'.format(self.project, self.variant))
        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise GraphConfigError('Configuration {0} does not exist'.format(
                format_configuration_name_for_printing(self.project, self.variant,
                                                       self.config)
            ))

    def run(self):
        '''
        Runs the graphconfig command
        '''
        ret = 1

        self.logger.info('Building source configuration tree')
        source_config = ConfigFactory.create_from_icm(self.project, self.variant, self.config)

        if self.write_dot_file(source_config):
            if self.create_gif():
                ret = 0

        return ret

    def write_dot_file(self, source_config):
        '''
        Writes a dot file based upon the configuration contents
        '''

        lines = source_config.get_dot()
        self.logger.info('Generating dot file {}'.format(self.dot_file_name))
        with open(self.dot_file_name, 'w') as fd:
            fd.write('digraph "{0}" {{\n'.format(source_config.get_full_name()))
            fd.write('\n'.join(lines))
            fd.write("}")

        return os.path.exists(self.dot_file_name)

    def create_gif(self):
        '''
        Creates the gif file from the dot file
        '''
        self.logger.info('Generating gif file {}'.format(self.gif_file_name))
        command = ['dot', '-Tgif', '{}'.format(self.dot_file_name)]
        with open(self.gif_file_name, 'w') as fd:
            subprocess.call(command, stdout=fd)

        return os.path.exists(self.gif_file_name)

