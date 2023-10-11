#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/ecosphere/test_milestone.py $
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
from dmx.ecolib.milestone import Milestone, MilestoneError

class TestMilestone(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.milestone = '99'
        self.db_project = os.environ['DB_PROJECT']
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_PROJECT'] = 'Falcon_Mesa i10socfm'
        os.environ['DB_DEVICE'] = "FM8"

    def tearDown(self):
        os.environ['DB_PROJECT'] = self.db_project
        os.environ['DB_DEVICE'] = self.db_device

    def test_object_instantiation(self):
        milestone = Milestone(self.family, self.milestone)
        self.assertIsInstance(milestone, Milestone)            

    def test_function_existence(self):
        milestone = Milestone(self.family, self.milestone)
        self.assertIsNotNone(milestone._preload)         
        self.assertIsNotNone(milestone._get_checkers)                
        self.assertIsNotNone(milestone.get_checkers)     
        self.assertIsNotNone(milestone.has_checker)      
        self.assertIsNotNone(milestone.get_checker)

if __name__ == '__main__':
    unittest.main()
