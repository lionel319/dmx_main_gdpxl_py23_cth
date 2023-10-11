#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/deleteconfig.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: unofficial plugin for deleting a rel config

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import sys
import logging
import textwrap

from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import format_configuration_name_for_printing
from dmx.utillib.arcenv import ARCEnv

LOGGER = logging.getLogger(__name__)

class DeleteConfigError(Exception): pass

class DeleteConfig(object):
    '''
    Runs the abnr deleteconfig command
    '''
    def __init__(self, project, variant, config, preview=True):
        self.project = project
        self.variant = variant
        self.config = config
        self.preview = preview
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)

        if self.cli.is_name_immutable(self.config):
            raise DeleteConfigError('You cannot delete immutable configurations')

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise DeleteConfigError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise DeleteConfigError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise DeleteConfigError("{0}/{1} does not exist".format(self.project, self.variant))                

        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise DeleteConfigError('Configuration {0} does not exist'.format(format_configuration_name_for_printing(self.project, self.variant, self.config)))

    def run(self):
        '''
        Runs the abnr deleteconfig command
        :return: 0 = success, 1 = fail
        '''
        ret = 1
        ret = self.delete_composite_config()
        return ret

    def delete_composite_config(self):
        '''
        Deletes the composite config
        :return: 0 = success, 1 = error
        '''
        ret = 1

        config_name = format_configuration_name_for_printing(self.project, self.variant, self.config)
        self.logger.info('Deleting configuration {0}'.format(config_name))

        if self.cli.del_config(self.project, self.variant, self.config):
            ret = 0
        else:
            ret = 1
            self.logger.error('Could not delete {0}'.format(config_name))

        return ret
