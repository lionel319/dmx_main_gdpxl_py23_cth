#!/usr/intel/pkgs/python3/3.9.6/bin/python3

# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/gdp47827_tests/abnrlib/flows/test_derivebom.py $
# $Revision: #1 $
# $Change: 7480240 $
# $DateTime: 2023/02/12 19:21:29 $
# $Author: wplim $

from __future__ import print_function
import UsrIntel.R1

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))), 'lib', 'python')
print(LIB)
sys.path.insert(0, LIB)
import cmx.utillib.utils
import cmx.abnrlib.flows.derivebom

class TestDeriveBom(unittest.TestCase):
    def setUp(self):
        self.project = 'proj'
        self.ip = 'ip'
        self.source_bom = 'sb'
        self.dest_bom = 'db'
        self.cells = []
        self.deliverable = 'deliverable'
        self.exact = True
        self.hier = True
        self.db = cmx.abnrlib.flows.derivebom.DeriveBom(self.project, self.ip, self.source_bom, self.dest_bom, self.deliverable, self.exact, self.hier)
        
    def tearDown(self):
        pass

    def test_001___get_normalized_config__exact_is_false_bom_is_mutable(self):
        bom = 'dest_bom'
        result = self.db.get_normalized_config(bom, False)
        self.assertEqual(result, bom)

    def test_002___get_normalized_config__exact_is_false_bom_is_rel(self):
        bom = 'REL123'
        result = self.db.get_normalized_config(bom, False)
        self.assertEqual(result, 'bREL123__REL123__dev')

    def test_003___get_normalized_config__exact_is_false_bom_is_snap(self):
        bom = 'snap-123'
        result = self.db.get_normalized_config(bom, False)
        self.assertEqual(result, 'bsnap-123__snap-123__dev')

    def test_004___get_normalized_config__exact_is_true_bom_is_mutable(self):
        bom = 'dest_bom'
        result = self.db.get_normalized_config(bom, True)
        self.assertEqual(result, bom)

    def test_005___get_normalized_config__exact_is_true_bom_is_rel(self):
        bom = 'REL123'
        result = self.db.get_normalized_config(bom, True)
        self.assertEqual(result, bom)

    def test_006___get_normalized_config__exact_is_true_bom_is_snap(self):
        bom = 'snap-123'
        result = self.db.get_normalized_config(bom, True)
        self.assertEqual(result, bom)




if __name__ == '__main__':
    unittest.main()
