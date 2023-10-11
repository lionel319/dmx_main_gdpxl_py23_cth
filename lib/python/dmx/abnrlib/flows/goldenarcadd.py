#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/goldenarcadd.py#1 $
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

class GoldenarcAddError(Exception): pass

class GoldenarcAdd(object):
    '''
    '''

    def __init__(self, thread, milestone, flow, arc, subflow='', source='proddb', preview=False):        
        '''
        '''
        self.thread = thread
        self.milestone = milestone
        self.flow = flow
        self.subflow = subflow
        self.arc = arc
        self.preview = preview
        self.source = source
        self.logger = logging.getLogger(__name__)

        self.tool, self.version = dmx.utillib.arcutils.ArcUtils()._split_type_address_from_resource_name(self.arc)


    def run(self):

        if self.preview:
            print("Dryrun mode is not supported for this command.")
            return 0

        prod = False
        if self.source == 'proddb':
            prod = True

        g = dmx.abnrlib.goldenarc_db.GoldenarcDb(prod=prod)
        g.connect()
        ret = g.add_goldenarc_list(self.thread, self.milestone, self.flow, self.subflow, self.tool, self.version)
        self.logger.info("Data added/updated: {}".format(ret))
        return 0


