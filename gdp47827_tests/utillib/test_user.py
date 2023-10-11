#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_user.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import os
import sys
import unittest
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.utillib.utils import run_command
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.user


class TestUser(unittest.TestCase):
    
    def setUp(self):
        self.a = dmx.utillib.user.User('lionelta')

    def tearDown(self):
        pass

    def test_001___get_idsid(self):
        self.assertEqual(self.a.get_idsid(), 'lionelta')

    def test_002___get_wwid(self):
        self.assertEqual(self.a.get_wwid(), '11645384')

    def test_002___get_email(self):
        self.assertEqual(self.a.get_email(), 'yoke.liang.tan@intel.com')

    def test_003___is_exists___true(self):
        self.assertTrue(dmx.utillib.user.User('lionelta').is_exists())

    def test_003___is_exists___false(self):
        self.assertFalse(dmx.utillib.user.User('ceeeeeeeb').is_exists())



if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

