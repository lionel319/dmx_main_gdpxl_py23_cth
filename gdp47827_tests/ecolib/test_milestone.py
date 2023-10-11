#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_milestone.py $
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
os.environ['DMXDB'] = 'DMXTEST'
from dmx.ecolib.milestone import Milestone, MilestoneError

class TestMilestone(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.milestone = '5.0'
        self.roadmap = 'FM8'
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_DEVICE'] = 'FM8'
        self.Milestone = Milestone(self.family, self.milestone, roadmap=self.roadmap)

    def tearDown(self):
        os.environ['DB_DEVICE'] = self.db_device

    def test_milestone_properties(self):
        '''
        Tests the Milestone object properties
        '''
        self.assertEqual(self.Milestone.family, self.family)           
        self.assertEqual(self.Milestone.milestone, self.milestone)

    def test__preload(self):
        self.Milestone._preload()
        checkers = [x.checkname for x in self.Milestone._checkers]
        self.assertIn('rtl_name_check', checkers)        

    def test__get_checkers(self):
        checkers = [x.checkname for x in self.Milestone._get_checkers()[self.roadmap]]
        self.assertIn('rtl_name_check', checkers)
        
    def test_get_checkers(self):
        checkers = [x.checkname for x in self.Milestone.get_checkers()]        
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_regex_cannot_compile(self):
        with self.assertRaises(MilestoneError):
            self.Milestone.get_checkers(flow_filter='!@#$%^&*(')        
        with self.assertRaises(MilestoneError):
            self.Milestone.get_checkers(subflow_filter='!@#$%^&*(')     
        with self.assertRaises(MilestoneError):
            self.Milestone.get_checkers(checker_filter='!@#$%^&*(')                                 
    def test_get_checkers_with_flow(self):
        checkers = [x.checkname for x in self.Milestone.get_checkers(flow_filter='rtl')]  
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_with_subflow(self):
        checkers = [x.checkname for x in self.Milestone.get_checkers(subflow_filter='name')]  
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_with_checkname(self):
        checkers = [x.checkname for x in self.Milestone.get_checkers(checker_filter='rtl_name_check')]  
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_with_deliverable(self):
        checkers = [x.checkname for x in self.Milestone.get_checkers(deliverable='rtl')]  
        self.assertIn('rtl_name_check', checkers)

    def test_has_checker(self):
        self.assertTrue(self.Milestone.has_checker('rtl', 'name', 'rtl_name_check'))

    def test_has_no_checker(self):
        self.assertFalse(self.Milestone.has_checker('does', 'not', 'exist'))

    def test_get_checker(self):
        checker = self.Milestone.get_checker('rtl', 'name', 'rtl_name_check')        
        self.assertEqual('rtl_name_check', checker.checkname)

    def test_get_non_existing_checker(self):
        with self.assertRaises(MilestoneError):
            self.Milestone.get_checker('does', 'not', 'exist')        
       
    def test_get_checker_invalid_character(self):
        with self.assertRaises(MilestoneError):
            self.Milestone.get_checker('@#', '@#', '#$')        

    def test_get_checker(self):
        checker = self.Milestone.get_checker('rtl', 'name', 'rtl_name_check', 'rtl')        
        self.assertEqual('rtl_name_check', checker.checkname)
            
if __name__ == '__main__':
    unittest.main()
