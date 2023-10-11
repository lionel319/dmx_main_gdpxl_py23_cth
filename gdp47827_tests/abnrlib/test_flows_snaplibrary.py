#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_snaplibrary.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
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
import dmx.abnrlib.flows.snaplibrary
import dmx.utillib.contextmgr

class TestSnapLibrary(unittest.TestCase):

    def setUp(self):
        self.cli = dmx.abnrlib.icm.ICManageCLI(site='intel')

    @patch.object(dmx.abnrlib.icm.ICManageCLI, "get_activedev_changenum")
    def test_001___is_already_released___found_1(self, mock):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        l = 'ipspec'
        c = 'dev'
        mock.return_value = '89'
        with dmx.utillib.contextmgr.setenv({"DB_FAMILY": "Ratonmesa", "DB_DEVICE": "RTM"}):
            s = dmx.abnrlib.flows.snaplibrary.SnapLibrary(p, v, l, c, force=False) 
            ret = s.is_already_released(c)
            print(ret)
            self.assertEqual(ret, 'snap-fortnr_2')


    @patch.object(dmx.abnrlib.icm.ICManageCLI, "get_activedev_changenum")
    def test_001___is_already_released___not_found(self, mock):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        l = 'ipspec'
        c = 'dev'
        mock.return_value = '0000'
        with dmx.utillib.contextmgr.setenv({"DB_FAMILY": "Ratonmesa", "DB_DEVICE": "RTM"}):
            s = dmx.abnrlib.flows.snaplibrary.SnapLibrary(p, v, l, c, force=False) 
            ret = s.is_already_released(c)
            print(ret)
            self.assertEqual(ret, False)


if __name__ == '__main__':
    unittest.main()
