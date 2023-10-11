#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/ecosphere/test_checker.py $
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

from dmx.ecolib.checker import Checker

class TestChecker(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.flow = 'rtl'
        self.subflow = 'name'        
        self.db_project = os.environ['DB_PROJECT']
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_PROJECT'] = 'Falcon_Mesa i10socfm'
        os.environ['DB_DEVICE'] = 'FM8'

    def tearDown(self):
        os.environ['DB_PROJECT'] = self.db_project
        os.environ['DB_DEVICE'] = self.db_device

    def test_object_instantiation(self):
        checker = Checker(self.family, self.flow, self.subflow)
        self.assertIsInstance(checker, Checker)            

    def test_function_existence(self):
        checker = Checker(self.family, self.flow, self.subflow)
        self.assertIsNotNone(checker._preload)         
        self.assertIsNotNone(checker.get_check_info)         

if __name__ == '__main__':
    unittest.main()
