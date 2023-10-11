#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_slice.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.ecolib.slice

class TestSlice(unittest.TestCase):
    def setUp(self):
        self.family = 'Wharfrock'
        self.product = 'whr'

    def test_001___get_patterns___found_1(self):
        s = dmx.ecolib.slice.Slice(self.family, 'oa', 'lay', roadmap=self.product)
        self.assertEqual(s.get_patterns(), {'ip_name/oa/ip_name/cell_name/layout/...': {'id': 'file', 'optional': False}} )

    def test_001___get_patterns___found_2(self):
        s = dmx.ecolib.slice.Slice(self.family, 'oa', 'sch', roadmap=self.product)
        self.assertEqual(s.get_patterns(), {'ip_name/oa/ip_name/cell_name/symbol/...': {'optional': False, 'id': 'file'}, 'ip_name/oa/ip_name/cell_name/schematic/...': {'optional': False, 'id': 'file'}, 'ip_name/oa/ip_name/cell_name/data.dm': {'optional': False, 'id': 'file'}} )

    def test_001___get_patterns___None(self):
        s = dmx.ecolib.slice.Slice(self.family, 'oa', 'xxx', roadmap=self.product)
        self.assertEqual(s.get_patterns(), {})

if __name__ == '__main__':
    unittest.main()
