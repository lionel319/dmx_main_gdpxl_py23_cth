#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/ecosphere/test_cell.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os, sys
DMX_LIB = os.getenv('DMX_LIB')
if DMX_LIB and 'main' in DMX_LIB:
    LIB = DMX_LIB
else:
    LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.ecolib.cell import Cell, CellError

class TestCell(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.product = 'FM8'
        self.ip = 'ar_lib'
        self.cell = 'ar_spine_3_bf'

    def test_object_instantiation(self):
        cell = Cell(self.family, self.product, self.ip, self.cell)
        self.assertIsInstance(cell, Cell)            

    def test_function_existence(self):
        cell = Cell(self.family, self.product, self.ip, self.cell)
        self.assertIsNotNone(cell._preload)         
        self.assertIsNotNone(cell._load_cell_properties)    
        self.assertIsNotNone(cell.get_applicable_products)              
        self.assertIsNotNone(cell.get_all_deliverables)       
        self.assertIsNotNone(cell.get_deliverables)      
        self.assertIsNotNone(cell.get_unneeded_deliverables_history)         
        self.assertIsNotNone(cell.add_unneeded_deliverable)         
        self.assertIsNotNone(cell.delete_unneeded_deliverable)         

if __name__ == '__main__':
    unittest.main()
