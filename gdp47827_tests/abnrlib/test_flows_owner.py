#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_owner.py $
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
import dmx.abnrlib.flows.owner

class TestFlowsOwner(unittest.TestCase):

    def setUp(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        c = 'dev'
        l = None
        self.owner = dmx.abnrlib.flows.owner.Owner(p, v, c, l)

    def test_010___get_configuration_designers___config(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        c = 'dev'
        l = None
        owner = dmx.abnrlib.flows.owner.Owner(p, v, c, l)
        ret = owner.get_configuration_designers(p, v, c, l)
        print(ret)
        gold = [[1, u'lionelta', u'2022-03-23T03:02:45.609Z'], [2, u'jwquah', u'2022-03-23T03:02:46.371Z']]
        self.assertEqual(ret, gold)

    def test_011___get_configuration_designers___library(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        c = 'dev'
        l = 'ipspec'
        owner = dmx.abnrlib.flows.owner.Owner(p, v, c, l)
        ret = owner.get_configuration_designers(p, v, c, l)
        print(ret)
        gold = [[1, u'lionelta', u'2022-03-23T03:02:41.693Z'], [2, u'jwquah', u'2022-03-23T03:02:42.271Z']]
        gold = [[1, u'lionelta', u'2022-03-23T03:02:41.693Z'], [2, u'jwquah', u'2022-04-01T15:48:01.630Z']]
        self.assertEqual(ret, gold)

    def test_012___get_configuration_designers___release(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        c = 'snap-fortnr_1'
        l = 'ipspec'
        owner = dmx.abnrlib.flows.owner.Owner(p, v, c, l)
        ret = owner.get_configuration_designers(p, v, c, l)
        print(ret)
        gold = [[1, u'psginfraadm', u'2022-03-23T10:18:36.576Z']]
        gold = [[1, u'psginfraadm', u'2022-03-23T10:18:36.576Z'], [2, u'psginfraadm', u'2022-04-01T15:48:07.863Z']]
        self.assertEqual(ret, gold)

    def test_020___user_exist___yes(self):
        self.assertTrue(self.owner.user_exist('lionelta'))

    def test_020___user_exist___no(self):
        self.assertFalse(self.owner.user_exist('xxxxxxxxx'))

    def test_021___get_full_name(self):
        self.assertEqual(self.owner.get_full_name('lionelta'), 'yoke.liang.tan')

if __name__ == '__main__':
    unittest.main()
