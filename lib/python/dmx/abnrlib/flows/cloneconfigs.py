#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cloneconfigs.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import logging
import textwrap

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.arcenv import ARCEnv

class CloneConfigsError(Exception): pass

class CloneConfigs(object):
    '''
    Runner class for abnr cloneconfigs
    '''
    def __init__(self, project, variant, config, dst_config,
                 libtype=None, clone_simple=False,
                 clone_immutable=False, reuse=False,
                 preview=True):
        self.libtype = libtype
        self.dst_config = dst_config
        self.clone_simple = clone_simple
        self.clone_immutable = clone_immutable
        self.reuse = reuse
        self.preview = preview
        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI(preview)

        # We cannot create REL/snap configs this way
        if self.dst_config.startswith('REL') or self.dst_config.startswith('snap'):
            raise CloneConfigsError('{0} is an invalid destination BOM name'.format(self.dst_config))

        # reuse switch cannot be used together with clone_simple and clone_immutable
        if self.reuse and (self.clone_simple or self.clone_immutable):
            raise CloneConfigsError('--reuse switch does not work together with --clone-immutable or --clone-deliverable')

        # If project not given, get project from IP
        if not project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, variant):
                    project = arc_project
                    break
            if not project:
                raise CloneConfigsError('Variant {0} is not found in projects: {1}'.format(variant, arc_projects))
        else:
            if not self.cli.project_exists(project):
                raise CloneConfigsError("{0} does not exist".format(project))
            if not self.cli.variant_exists(project, variant):
                raise CloneConfigsError("{0}/{1} does not exist".format(project, variant))
        self.src_config = ConfigFactory.create_from_icm(project, variant, config,
                                                        libtype=self.libtype,
                                                        preview=self.preview)


    def run(self):
        '''
        Executes the abnr cloneconfigs command
        :return: 0 == success, non-zero == failure
        :type return: int
        '''
        ret = 1

        if self.libtype:
            clone = self.src_config.clone(self.dst_config)
        else:
            if self.reuse:
                clone = self.src_config.clone(self.dst_config)
            else:
                clone = self.src_config.clone_tree(self.dst_config, clone_simple=self.clone_simple,
                                                   clone_immutable=self.clone_immutable, 
                                                   reuse_existing_config=True)

        if clone.save(shallow=False):
            ret = 0
            self.clone = clone  # save to property for easier enabling of regression test purposes.

        return ret
