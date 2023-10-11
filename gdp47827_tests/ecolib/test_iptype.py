#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_iptype.py $
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
from dmx.ecolib.ip import IP
from dmx.ecolib.iptype import IPType, IPTypeError

class TestIPType(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.iptype = 'asic'
        self.roadmap = 'FM8'
        self.milestone = '5.0'
        
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_DEVICE'] = 'FM8'
        self.IPType = IPType(self.family, self.iptype)

    def tearDown(self):
        os.environ['DB_DEVICE'] = self.db_device


    def test_iptype_properties(self):
        '''
        Tests the IPType object properties
        '''
        self.assertEqual(self.IPType.family, self.family)           
        self.assertEqual(self.IPType.iptype, self.iptype)

    def test__preload(self):
        self.IPType._preload()
        self.assertIn(self.roadmap, self.IPType._deliverables)   
        self.assertIn(self.milestone, self.IPType._deliverables[self.roadmap])   
        self.assertIn('rtl', [x.deliverable for x in self.IPType._deliverables[self.roadmap][self.milestone]])

    def test__get_deliverables(self):
        deliverables = self.IPType._get_deliverables()[self.roadmap]
        self.assertIn('rtl', [x.deliverable for x in deliverables['99']])

    def test_get_all_deliverables(self):
        deliverables = [x.deliverable for x in self.IPType.get_all_deliverables(roadmap=self.roadmap)]
        self.assertIn('rtl', deliverables)
            
    def test_get_all_deliverables_regex_cannot_compile(self):
        with self.assertRaises(IPTypeError):
            self.IPType.get_all_deliverables('!@#$^&*(')

    def test_get_all_deliverables_with_deliverable_filter(self):
        deliverables = [x.deliverable for x in self.IPType.get_all_deliverables('rtl', roadmap=self.roadmap)] 
        self.assertIn('rtl', deliverables)

    def test_get_all_deliverables_with_milestone_filter(self):
        deliverables = [x.deliverable for x in self.IPType.get_all_deliverables(milestone=self.milestone, roadmap=self.roadmap)]
        self.assertIn('rtl', deliverables)

    def test_has_deliverable(self):
        self.assertTrue(self.IPType.has_deliverable('rtl', roadmap=self.roadmap))

    def test_has_deliverable_with_milestone(self):
        self.assertTrue(self.IPType.has_deliverable('rtl', self.milestone, roadmap=self.roadmap))    

    def test_has_no_deliverable(self):
        self.assertFalse(self.IPType.has_deliverable('non_existing'))            

    def test_get_deliverable(self):
        self.assertEqual('rtl', self.IPType.get_deliverable('rtl', roadmap=self.roadmap).deliverable)        

    def test_get_deliverable_with_milestone(self):
        self.assertEqual('rtl', self.IPType.get_deliverable('rtl', self.milestone, roadmap=self.roadmap).deliverable)   

    def test_get_non_existing_deliverable(self):
        with self.assertRaises(IPTypeError):
            self.IPType.get_deliverable('non_existing')

if __name__ == '__main__':
    unittest.main()
