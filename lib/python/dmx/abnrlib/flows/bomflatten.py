#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/bomflatten.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr bom"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2013
All rights reserved.
'''
import sys
import logging
import textwrap
import multiprocessing

from dmx.utillib.utils import *
import dmx.abnrlib.icm
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.arcenv import ARCEnv

class BomFlattenError(Exception): pass

class BomFlatten(object):
    '''
    Runs the bom flatten command
    '''
    def __init__(self, project, ip, bom, dstbom):
        self.project = project
        self.ip = ip 
        self.bom = bom
        self.dstbom = dstbom
        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI()
        self.retlist = multiprocessing.Manager().list()


        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.ip):
                    self.project = arc_project
                    break
            if not self.project:
                raise BomFlattenError('Variant {0} is not found in projects: {1}'.format(self.ip, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise BomFlattenError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.ip):
                raise BomFlattenError("{0}/{1} does not exist".format(self.project, self.ip))   
        if not self.cli.config_exists(self.project, self.ip, self.bom):
            errmsg = "{0} does not exist".format(format_configuration_name_for_printing(
                    self.project, self.ip, self.bom))                            
            raise BomFlattenError(errmsg)            

    def get_config_tree(self):
        '''
        Returns the configuration object that references the project/variant@config
        passed in on the command line
        '''
        self.logger.debug("Building configuration tree")
        config_obj = ConfigFactory.create_from_icm(self.project, self.ip, self.bom)

        return config_obj


    def get_root_config(self, config):
        for ea_cfg in config:
            if ea_cfg.project == self.project and ea_cfg.variant == self.ip:
                return ea_cfg 

    def create_config_of_flatten_bom(self, config):
        parent_configs = self.get_parent_config(config, self.dstbom)
        root_config = self.get_root_config(parent_configs)
        for ea_config in parent_configs:
            if ea_config == root_config: continue
            root_config.add_configuration(ea_config)

        # Try to save the configuration
        if root_config.save():
            self.logger.info("Configuration {0} built".format(root_config.get_full_name()))
            ret = 0
        else:
            raise BomFlattenError("Could not save {0} to the IC Manage database".format(
                root_config.get_full_name()
            ))
 

    def get_parent_config(self, config, dstbom):
        parent_config = ''
        all_parent_config = []
        flatten_bom = config.flatten_tree()

        for ea_bom in flatten_bom:
            local_simple_config = []
            if ea_bom.is_config():
                local_configs = ea_bom.get_local_objects()
                for ea_local_config in local_configs:
                    if ea_local_config.is_config():
                        parent_config = ea_local_config
                    elif ea_local_config.is_library():
                        local_simple_config.append(ea_local_config)

                parent_config_object = IcmConfig(dstbom, parent_config.project, parent_config.variant, local_simple_config)
                all_parent_config.append(parent_config_object)

        return all_parent_config

    def run(self):
        '''
        Actually runs the bom command
        '''
        ret = 1
        self.logger.info('Flattening Bom...')
        if self.cli.config_exists(self.project, self.ip, self.dstbom):
            raise BomFlattenError('{}/{}@{} exists. Please use different destination bom'.format(self.project, self.ip, self.dstbom))
        config = self.get_config_tree()
        ret = self.create_config_of_flatten_bom(config)
        return ret

