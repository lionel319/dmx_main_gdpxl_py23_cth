#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/file_print.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $

Description: Another ABNR plugin
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import sys
import os
import textwrap
import logging
from collections import namedtuple

from dmx.abnrlib.command import Command
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.arcenv import ARCEnv

class PrintError(Exception): pass

FileSpec = namedtuple('FileSpec', 'variant libtype path')

class Print(object):
    '''
    Runs the abnr print command
    '''

    def __init__(self, project, variant, config, filespec, quiet, preview=True, libtype=None):
        self.quiet = quiet
        self.preview = preview
        self.project = project
        self.variant = variant
        self.clr = config 
        self.libtype = libtype

        filespec_elements = filespec.split('/', 2)
        self.filespec = FileSpec(filespec_elements[0], filespec_elements[1], filespec_elements[2])
        self.cli = ICManageCLI(preview=self.preview)
        self.logger = logging.getLogger(__name__)

        # If project not given, get project from IP
        if not project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, variant):
                    project = arc_project
                    break
            if not project:
                raise PrintError('Variant {0} is not found in projects: {1}'.format(variant, arc_projects))
        else:
            if not self.cli.project_exists(project):
                raise PrintError("{0} does not exist".format(project))
            if not self.cli.variant_exists(project, variant):
                raise PrintError("{0}/{1} does not exist".format(project, variant))       
        self.config = ConfigFactory.create_from_icm(project, variant, config, libtype=libtype, preview=preview)


    def run(self):
        '''
        Runs the abnr print command
        '''
        ret = 1

        full_filespec = self.get_filespec_with_changenum()
        self.logger.debug('full_filespec: {}'.format(full_filespec))
        print_output = self.cli.p4_print(full_filespec, quiet=self.quiet)
        if print_output:
            print(print_output)
            ret = 0
        else:
            raise PrintError('Problem printing {0}'.format(full_filespec))
        
        return ret

    def get_filespec_with_changenum(self):
        '''
        Gets the full Perforce filespec including the relevant changenumer
        :return: Full gilespec with changenum
        :type return: str
        '''
        full_filespec = ''
        c = self.get_simple_config()

        if c.is_library():
            full_filespec = '//depot/gdpxl{}/{}{}'.format(c._defprops['path'], self.filespec.path, c._defprops['change'])
        elif c.is_release():
            ### release's path == /intel/i10socfm/liotest1/ipspec/dev/snap-2
            ### we should change it to /intel/i10socfm/liotest1/ipspec/dev
            full_filespec = '//depot/gdpxl{}/{}{}'.format(os.path.dirname(c._defprops['path']), self.filespec.path, c._defprops['change'])
        
        return full_filespec

    def get_simple_config(self):
        '''
        Finds the simple config in the tree that contains the filespec
        :return: simple config object
        :type return: SimpleConfig
        '''
        simple_config = None

        # First find the configuration in the tree that contains the sought file
        simple_configs = self.config.search(variant='^{0}$'.format(self.filespec.variant), libtype='^{0}$'.format(self.filespec.libtype))

        if not simple_configs:
            raise PrintError('Could not find a configuration for {}/{} in {}'.format(self.filespec.variant, self.filespec.libtype, self.config.get_full_name()))

        elif len(simple_configs) > 1:
            raise PrintError('Found multiple configs for {}/{} in {}'.format(self.filespec.variant, self.filespec.libtype, self.config.get_full_name()))
        else:
            # Search always returns a list, but there should only be one match
            simple_config = simple_configs[0]

        return simple_config

