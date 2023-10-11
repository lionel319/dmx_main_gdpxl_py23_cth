#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_view.py $
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
import dmx.ecolib.view

class TestView(unittest.TestCase):
    def setUp(self):
        self.family = 'Wharfrock'
        self.product = 'whr'

    def test_001___get_deliverables___found(self):
        v = dmx.ecolib.view.View(self.family, 'view_rtl')
        ret = [x.name for x in v.get_deliverables()]
        self.assertEqual(ret, ['bcmrbc', 'cdc', 'complib', 'cvrtl', 'dftdsm', 'dv', 'interrba', 'intfc', 'ippwrmod', 'ipspec', 'ipxact', 'lint', 'netlist', 'pintable', 'rdf', 'reldoc', 'rtl', 'rtlcompchk', 'upf_netlist', 'upf_rtl', 'upffc'])


if __name__ == '__main__':
    unittest.main()
