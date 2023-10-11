#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/goldenarcdelete.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "recertify" subcommand plugin
Author: Lionel Tan Yoke Liang
Documentation: https://wiki.ith.intel.com/display/tdmaInfra/Release+Configuration+Re-Certification
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
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

class GoldenarcDeleteError(Exception): pass

class GoldenarcDelete(object):
    '''
    '''

    def __init__(self, thread, milestone, flow, arc, subflow='', devmode=False, source='proddb', preview=False):        
        '''
        '''
        self.thread = thread
        self.milestone = milestone
        self.flow = flow
        self.subflow = subflow
        self.arc = arc
        self.devmode = devmode
        self.source = source
        self.preview = preview
        self.logger = logging.getLogger(__name__)

        self.tool, self.version = dmx.utillib.arcutils.ArcUtils()._split_type_address_from_resource_name(self.arc)


    def run(self):
        prod = False
        if self.source == 'proddb':
            prod = True
        g = dmx.abnrlib.goldenarc_db.GoldenarcDb(prod=prod)
        g.connect()
        data = g.delete_goldenarc_list(self.thread, self.milestone, self.flow, self.subflow, self.tool, self.version)
        if data and data.deleted_count:
            self.logger.info("One data deleted.")
        else:
            self.logger.info("No matching data found. Nothing deleted.")
        self.logger.debug(data.raw_result)
        return 0


