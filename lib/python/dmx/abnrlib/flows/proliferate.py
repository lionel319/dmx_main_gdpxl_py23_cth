#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/proliferate.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr proliferate"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''
import os
import sys
import logging
import textwrap

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmcompositeconfig import CompositeConfig
from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.config_naming_scheme import ConfigNamingScheme
from dmx.abnrlib.flows.releaselibraries import ReleaseLibraries
from dmx.utillib.arcenv import ARCEnv

class ProliferateError(Exception): pass

class Proliferate(object):
    '''
    Actually runs abnr proliferate
    '''
    def __init__(self, project, variant, config, dest_variant, preview=True):
        self.project = project
        self.variant = variant
        self.preview = preview
        self.cli = ICManageCLI(preview=self.preview)
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
                raise ProliferateError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise ProliferateError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise ProliferateError("{0}/{1} does not exist".format(self.project, self.variant))       
        self.config = ConfigFactory.create_from_icm(self.project,
                                                    self.variant,
                                                    config)
        self.dest_variant = dest_variant
        self.wip_config = None
        self.waiver_file = None

        if not self.config.is_released():
            raise ProliferateError('Source config {} is not a REL. Please provide a REL config as source config'.format(config))

        if self.cli.variant_exists(self.project, self.dest_variant):
            raise ProliferateError('Dest variant {}/{} already exists'.format(self.project, self.dest_variant))

    def run(self):
        '''
        Runs proliferate
        :return: Zero on success, non-zero on failure
        :type return: int
        '''
        ret = 0       

        if self.clone_variant():
            ret = 1

        if self.create_wip_config():
            ret = 1
        
        if self.create_waiver_file():
            ret = 1

        if self.release_simple_configs():
            ret = 1            
        
        ret = 0

        return ret

    def add_libtype_and_integrate_library(self, runner):
        ret = 0
        for libtype in runner.libtypes:
            source_simple_configs = [x for x in self.config.configurations if x.is_simple()]
            source_libtypes = [x.libtype for x in source_simple_configs if x.is_simple()]
            default_config = 'dev'
            default_library = 'dev'

            self.cli.add_libtypes_to_variant(self.project, self.dest_variant, [libtype])
            if not self.preview and not self.cli.libtype_exists(self.project, self.dest_variant, libtype):
                raise ProliferateError('Failed to add libtype {0} to {1}/{2}'.format(
                    libtype, self.project, self.dest_variant))

            if libtype in source_libtypes:
                source_simple_config = [x for x in source_simple_configs if x.libtype == libtype][0]
                source_project = source_simple_config.project
                source_variant = source_simple_config.variant
                source_libtype = source_simple_config.libtype
                source_library = source_simple_config.library
                source_lib_release = source_simple_config.lib_release
                dest_library = 'dev'                
                desc = 'Proliferated from {}/{}:{}/{}/{} by {}'.format(source_project, source_variant, 
                                                                       source_libtype, source_library,
                                                                       source_lib_release,
                                                                       os.environ['USER'])
                if not self.cli.branch_library(source_project, source_variant, source_libtype, 
                                               source_library, dest_library, source_project, 
                                               self.dest_variant, desc):
                    raise ProliferateError('Error branching library {0}/{1}:{2}/{3}/{4} to {0}/{5}:{2}/{3}/#dev'.format(
                        source_project, source_variant, source_libtype, source_library, 
                        dest_library, self.dest_variant))
            else:
                self.cli.add_libraries(self.project, self.dest_variant, [libtype])

            if not self.preview and not self.cli.library_exists(self.project, self.dest_variant, libtype, default_library):
                raise ProliferateError('Failed to add dev library to {0}/{1}:{2}'.format(
                    self.project, self.dest_variant, libtype))

            dev_cfg = SimpleConfig(default_config, self.project, self.dest_variant, libtype, 
                                   default_library, '#ActiveDev', preview=self.preview)
            if not dev_cfg.save():
                raise ProliferateError('Failed to create simple config {0}/{1}:{2}@{3}'.format(
                    self.project, self.dest_variant, libtype, default_config))
            ret = 1                
        return ret                

    def clone_variant(self):
        ret = 1
        self.logger.info('Cloning variant {0}/{1} to {0}/{2}'.format(self.project, 
                                                                     self.variant, 
                                                                     self.dest_variant))
        variant_type = self.cli.get_variant_properties(self.project, self.variant)['Variant Type']
        desc = 'Proliferated from {} by {}'.format(self.config, os.environ['USER'])
        try:            
            runner = CreateVariantRunner(self.project, self.dest_variant, variant_type, 
                                         preview=self.preview, description=desc)
            
            if runner.create_variant():
                if self.add_libtype_and_integrate_library(runner):
                    if runner.create_dev_configs():
                        ret = 0
                    else:
                        ret = 1
                else:
                    ret = 1
            else:
                ret = 1
        except Exception as e:
            self.logger.error(e)
            raise ProliferateError('Error cloning variant {0}/{1} to {0}/{2}.'.format(self.project,
                                                                                      self.variant,
                                                                                      self.dest_variant))
                        
        return ret
        
    def create_wip_config(self):
        ret = 1
        wip_configname = 'RC_proliferated'
        self.logger.info('Creating {}/{}@{}'.format(self.project, self.dest_variant, wip_configname))
        dest_dev_config = ConfigFactory.create_from_icm(self.project,
                                                        self.dest_variant,
                                                        'dev')
        released_libtypes_in_source_config = [x.libtype for x in self.config.configurations if x.is_simple()]
        simple_configs = [x for x in dest_dev_config.configurations if x.is_simple() and x.libtype in released_libtypes_in_source_config]
        sub_ip_composite_configs = [x for x in self.config.configurations if x.is_composite and x.variant != self.variant]
        configurations = simple_configs + sub_ip_composite_configs
        desc = 'RC config for proliferation form {}'.format(self.config)
        self.wip_config = CompositeConfig(wip_configname, self.project, self.dest_variant, 
                                          configurations, description=desc, preview=self.preview)
        if not self.preview:
            self.wip_config.save()
        ret = 0     
               
        return ret            

    def release_simple_configs(self):
        ret = 1
        self.logger.info('Releasing simple configs in {}'.format(self.wip_config))

        if self.wip_config:
            scheme = ConfigNamingScheme()
            configname_details = scheme.get_data_for_release_config(self.config.config)
            milestone = configname_details['milestone']
            thread = '{}rev{}'.format(configname_details['thread'], configname_details['rev'])
            label = configname_details['label']
            description = 'Released for proliferation from {}'.format(self.config)
            try:
                runner = ReleaseLibrariesRunner(self.project, self.dest_variant, 
                                                 self.wip_config.config, milestone, thread, 
                                                 label, self.preview, description, [], [], True, 
                                                 None, 
                                                 waiver_files=[self.waiver_file], force=False, 
                                                 release_snap=False)
                runner.run()
                ret = 0
            except Exception as e:
                self.logger.error(e)
                raise ProliferateError('Error releasing simple configs for {}'.format(self.wip_config))
        return ret                

    def create_waiver_file(self):
        self.logger.info('Creating waiver file')
        ret = 1
        waive_reason = 'waived for proliferation from {}/{}@{}'.format(self.project, 
                                                                       self.variant, 
                                                                       self.config.config)
        waivers = '*,*,*,\"{}\",*\n'.format(waive_reason)
        self.waiver_file = '{}/waivers.csv'.format(os.getcwd())
        with open(self.waiver_file, 'w') as f:
            f.write(waivers)
        ret = 0
        return ret            
