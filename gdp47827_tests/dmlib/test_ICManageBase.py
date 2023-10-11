#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmlib/test_ICManageBase.py $
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
import dmx.dmlib.ICManageBase

class TestICManageBase(unittest.TestCase):

    def setUp(self):
        self.icmp4 = '/p/psg/eda/icmanage/gdp/40058/linux64/suse12/bin/icmp4'
        self.icmb = dmx.dmlib.ICManageBase.ICManageBase

    def _test_000__which(self):
        self.assertEqual(self.icmp4, dmx.dmlib.ICManageBase.which('icmp4'))

    def test_001___isUserLoggedIn_true(self):
        self.assertTrue(dmx.dmlib.ICManageBase.isUserLoggedIn())
    
    @patch('dmx.dmlib.ICManageBase.subprocess.check_output')
    def test_002___isUserLoggedIn_false(self, mock_check_output):
        if sys.version_info[0] > 2:
            mock_check_output.return_value = b'unkwon'
        else:
            mock_check_output.return_value = 'unkwon'
        self.assertFalse(dmx.dmlib.ICManageBase.isUserLoggedIn())
    
    def test_003__getLibType_lay(self):
        self.assertEqual('oa', self.icmb.getLibType('LAY'))

    def test_004__getLibType_sch(self):
        self.assertEqual('oa', self.icmb.getLibType('SCH'))

    def test_005__getLibType_rtl(self):
        self.assertEqual('rtl', self.icmb.getLibType('RTL'))

    def test_006__getLibType_unknown(self):
        self.assertEqual('unknown', self.icmb.getLibType('unkNOWN'))

    def test_007__getDeliverableName_unknown(self):
        self.assertEqual('UNKNOWN', self.icmb.getDeliverableName('unknown'))

    def test_008__getDeliverableName_rtl(self):
        self.assertEqual('RTL', self.icmb.getDeliverableName('RTL'))

    def test_009__checkICManageAvailable(self):
        self.assertIsNone(self.icmb._checkICManageAvailable())





if __name__ == '__main__':
    unittest.main()
