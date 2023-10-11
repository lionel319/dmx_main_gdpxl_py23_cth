#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_iem.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.iem

class TestIem(unittest.TestCase):

    def setUp(self):
        self.a = dmx.utillib.iem.IEM()

    def _test_010___get_group_members(self):
        ret = self.a.get_group_members('psgrnr')
        print(ret)
        self.assertIn('lionelta', ret)

    def _test_020___get_user_iem_groups(self):
        ret = self.a.get_user_iem_groups('psginfraadm')
        print(ret)
        self.assertIn('psgeng', ret)


if __name__ == '__main__':
    unittest.main()
