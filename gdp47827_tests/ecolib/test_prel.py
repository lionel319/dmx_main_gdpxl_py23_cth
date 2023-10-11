#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_prel.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.ecolib.prel

class TestPrel(unittest.TestCase):
    def setUp(self):
        self.family = 'Falcon'
        self.product = 'FM6'

    def test_001___get_deliverables___found(self):
        v = dmx.ecolib.prel.Prel(self.family, 'prel_qpds')
        ret = [x.name for x in v.get_deliverables()]
        print(ret)
        ans = ['bcmrbc', 'complibphys', 'ipfloorplan', 'ippwrmod', 'ipspec', 'pnr', 'rcxt', 'rdf', 'rtl', 'timemod', 'upf_netlist', 'upf_rtl']
        self.assertEqual(ret, ans)

    def test_002___get_deliverables___None(self):
        with self.assertRaises(Exception):
            v = dmx.ecolib.prel.Prel(self.family, 'aaa')

if __name__ == '__main__':
    unittest.main()
