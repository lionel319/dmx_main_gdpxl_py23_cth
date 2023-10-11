#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/parentsbom.py#1 $
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

from dmx.utillib.utils import *
import dmx.abnrlib.icm
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.arcenv import ARCEnv

class ParentsBomError(Exception): pass

class ParentsBom(object):
    '''
    Runs the abnr bom command
    '''
    def __init__(self, project, ip, clr, deliverable, reportall, hierarchy=False):
        self.project = project
        self.ip = ip
        self.clr = clr  # it could be: config or library or release
        self.deliverable = deliverable
        self.reportall = reportall
        self.hierarchy = hierarchy
        self.cli = ICManageCLI()
        errmsg = ''
            

    def run_pm_command(self):
        '''
        Run pm command and return formatted result
        ''' 
        format_name = []

        result = self.cli.get_parent_boms(self.project, self.ip, self.clr, self.deliverable, hierarchy=self.hierarchy)

        for line in result:
            proj = line['project:parent:name']
            ip = line['variant:parent:name']
            bom = line['config:parent:name']
            config_name = format_configuration_name_for_printing(proj, ip, bom)
            if not self.reportall:
                if 'tnr-placeholder' in config_name: continue 
            format_name.append(config_name)


        return format_name


    def run(self):
        '''
        Actually runs the bom command
        '''

        ret = self.run_pm_command()
        for ea_name in ret:
            print(ea_name)

        if ret:
            return 0
        else:
            return 1

