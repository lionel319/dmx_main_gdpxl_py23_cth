#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/bomdetail.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr bom"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2013
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import sys
import logging
import textwrap
import multiprocessing

from dmx.utillib.utils import *
import dmx.abnrlib.icm
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.arcenv import ARCEnv

class BomDetailError(Exception): pass

class BomDetail(object):
    '''
    Runs the abnr bom command
    '''
    def __init__(self, project, variant, clr, p4=False, libtypes=[], relpath=False, libtype=''):
        self.project = project
        self.variant = variant
        self.config = clr
        self.p4 = p4
        self.libtypes = libtypes
        self.libtype = libtype
        self.relpath = relpath
        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI()
        self.retlist = multiprocessing.Manager().list()


        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise BomDetailError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise BomDetailError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise BomDetailError("{0}/{1} does not exist".format(self.project, self.variant))

        errmsg = ''
        if self.libtype:
            if self.cli.is_name_immutable(self.config):
                library = self.cli.get_library_from_release(self.project, self.variant, self.libtype, self.config)
                if not self.cli.release_exists(self.project, self.variant, self.libtype, library, self.config):
                    errmsg = "{0} does not exist".format(format_configuration_name_for_printing(self.project, self.variant, self.config, libtype=self.libtype))
            else:
                if not self.cli.library_exists(self.project, self.variant, self.libtype, self.config):
                    errmsg = "{0} does not exist".format(format_configuration_name_for_printing(self.project, self.variant, self.config, libtype=self.libtype))
        else:
            if not self.cli.config_exists(self.project, self.variant, self.config):
                errmsg = "{0} does not exist".format(format_configuration_name_for_printing(self.project, self.variant, self.config))
        if errmsg:
            raise BomDetailError(errmsg)            


    def get_config_tree(self):
        '''
        Returns the configuration object that references the project/variant@config
        passed in on the command line
        '''
        self.logger.debug("Building configuration tree")
        config_obj = ConfigFactory.create_from_icm(self.project, self.variant, self.config, libtype=self.libtype)

        return config_obj

    def build_bom(self, config_tree):
        '''
        Builds a bom from config_tree
        '''
        self.logger.debug("Building bom")
        return config_tree.get_bom(libtypes=self.libtypes, p4=self.p4,
                                   relchange=self.relpath)

    def run(self):
        '''
        Actually runs the bom command
        '''
        ret = 1
        config = self.get_config_tree()
        if not config:
            ret = 1
        else:
            retlist = self.get_depot_path()
            for t in sorted(retlist):
                print(t)



    def get_depot_path(self, changenumdigit=False):
        cfobj = ConfigFactory.create_from_icm(self.project, self.variant, self.config, libtype=self.libtype)
        retlist = []
        for c in cfobj.flatten_tree():
            if not c.is_config():
                if c.is_library():
                    if changenumdigit:
                        changenum = '@{}'.format(c.changenumdigit)
                    else:
                        changenum = c._defprops['change']   # this, by right, should be always '@now'
                    #path = '//depot/gdpxl{}/...{}'.format(c._defprops['path'], c._defprops['change'])
                    path = '//depot/gdpxl{}/...{}'.format(c._defprops['path'], changenum)
                elif c.is_release():
                    ### release's path == /intel/i10socfm/liotest1/ipspec/dev/snap-2
                    ### we should change it to /intel/i10socfm/liotest1/ipspec/dev
                    path = '//depot/gdpxl{}/...{}'.format(os.path.dirname(c._defprops['path']), c._defprops['change'])
                retlist.append(path)
        self.retlist = retlist
        return retlist


    def get_depot_path_worker(self, cfobj):
        ret = cfobj._SimpleConfig__get_depot_path()
        self.retlist.append(ret)

