#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/goldenarclist.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "recertify" subcommand plugin
Author: Lionel Tan Yoke Liang
Documentation: https://wiki.ith.intel.com/display/tdmaInfra/Release+Configuration+Re-Certification
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import str
from builtins import object
import sys
import os
import logging
import textwrap
from pprint import pprint

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, rootdir)

import dmx.abnrlib.icm
import dmx.abnrlib.config_factory
import dmx.utillib.arcutils
import dmx.utillib.utils
import dmx.dmxlib.workspace
import dmx.abnrlib.goldenarc_db
import dmx.abnrlib.certificate_db
import dmx.utillib.arcutils
import json
from pprint import pprint
from tabulate import tabulate

class GoldenarcListError(Exception): pass

class GoldenarcList(object):
    '''
    '''

    def __init__(self, thread=None, milestone=None, flow=None, subflow=None, tool=None, version=None, source='proddb', preview=False):
        '''
        '''
        self.thread = thread
        self.milestone = milestone
        self.flow = flow
        self.subflow = subflow
        self.tool = tool
        self.version = version
        self.preview = preview
        self.source = source
        self.logger = logging.getLogger(__name__)



    def run(self):
        if self.preview:
            self.logger.info("This command does not support dryrun mode.")
            return 0

        prod = False
        if self.source == 'proddb':
            prod = True
        g = dmx.abnrlib.goldenarc_db.GoldenarcDb(prod=prod)
        g.connect()
        self.data = g.get_goldenarc_list(thread=self.thread, milestone=self.milestone, flow=self.flow, subflow=self.subflow, tool=self.tool, version=self.version)

        tablestr = self.generate_tabulate_string(self.data)
        print(tablestr)

        return 0

    def generate_tabulate_string(self, data):
        headers = ['thread', 'milestone', 'flow', 'subflow', 'tool', 'version']
        table = []
        for d in data:
            tmp = []
            for key in headers:
                tmp.append(str(d[key]))
            table.append(tmp), 
        return tabulate(table, headers, tablefmt='pretty', floatfmt='.1f')


