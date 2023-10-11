#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_parentsbom.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
from datetime import date
import os, sys
import logging
import socket
import datetime
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.loggingutils
LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
import dmx.abnrlib.icm
import dmx.abnrlib.flows.parentsbom
import dmx.abnrlib.config_factory

class TestParrentsBom(unittest.TestCase):
    '''
    >dmx report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --hier
    INFO: DMX-id: dmx_lionelta_20220328_scc919025_16597_sc
    Project: Raton_Mesa, IP: rtmliotest2, BOM: REL1.0RTMrevA0__22ww135a
            Last modified: 2022/03/25 09:15:25 (in server timezone)
    Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a
            Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c
            Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a
            Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a
                    Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a
                    Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d
        
    '''
    def setUp(self):
        self.cli = dmx.abnrlib.icm.ICManageCLI(site='intel')
        self.project = 'Raton_Mesa'
        self.ip = 'rtmliotest1'
        self.libtype = 'reldoc'
        self.libtype_release = 'REL1.0RTMrevA0__22ww135d'
        self.config = 'REL1.0RTMrevA0__22ww135a'
        self.parentsbom = dmx.abnrlib.flows.parentsbom.ParentsBom(self.project, self.ip, self.config, None, None)
        self.parentsbom_libtype = dmx.abnrlib.flows.parentsbom.ParentsBom(self.project, 'rtmliotest1', self.libtype_release, self.libtype , None)
    
    def test_001___run_pm_command(self):
        result = ['Raton_Mesa/liotest2@two_libtypes', 'Raton_Mesa/liotest4@two_libtypes']
        ret = self.parentsbom.run_pm_command()
        pprint(ret)
        self.assertIn('Raton_Mesa/rtmliotest2@snap-1', ret)
        self.assertIn('Raton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a', ret)

    def test_002___invalid_parentbom(self):

        with self.assertRaises(Exception):
            self.invalid_parentsbom = dmx.abnrlib.flows.parentsbom.ParentsBom('invalid', self.ip, self.libtype_release, self.libtype , None).run_pm_command()

    def test_003___run_pm_command_got_deliverable(self):
        ret = self.parentsbom_libtype.run_pm_command()
        pprint(ret)
        self.assertIn('Raton_Mesa/rtmliotest1@snap-1', ret)
        self.assertIn('Raton_Mesa/rtmliotest1@REL1.0RTMrevA0__22ww135a', ret)
        

    def test_004___run_pass(self):
        self.assertEqual(0, self.parentsbom_libtype.run())


if __name__ == '__main__':
    unittest.main()
