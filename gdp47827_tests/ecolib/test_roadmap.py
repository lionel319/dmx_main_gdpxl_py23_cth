#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_roadmap.py $
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
from dmx.ecolib.product import Product
from dmx.ecolib.roadmap import Roadmap, RoadmapError

class TestRoadmap(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.roadmap = 'FM8'
        self.milestone = '99'
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_DEVICE'] = 'FM8'
        self.Roadmap = Roadmap(self.family, self.roadmap)

    def tearDown(self):
        os.environ['DB_DEVICE'] = self.db_device

    def test_roadmap_properties(self):
        '''
        Tests the Roadmap object properties
        '''
        self.assertEqual(self.Roadmap.family, self.family)           
        self.assertEqual(self.Roadmap.roadmap, self.roadmap)

    def test__preload(self):
        self.Roadmap._preload()
        milestones = [x.milestone for x in self.Roadmap._milestones]
        self.assertIn(self.milestone, milestones)

    def test__get_milestones(self):
        milestones = [x.milestone for x in self.Roadmap._get_milestones()]        
        self.assertIn(self.milestone, milestones)

    def test_get_milestones(self):
        milestones = [x.milestone for x in self.Roadmap.get_milestones()]        
        self.assertIn(self.milestone, milestones)

    def test_get_milestones_with_milestone_filter(self):
        milestones = [x.milestone for x in self.Roadmap.get_milestones('99')]
        self.assertIn(self.milestone, milestones)

    def test_has_milestone(self):
        self.assertTrue(self.Roadmap.has_milestone('99'))        

    def test_has_no_milestone(self):
        self.assertFalse(self.Roadmap.has_milestone('doesnotexist'))    
            
    def test_get_milestone(self):
        self.assertEqual('99', self.Roadmap.get_milestone('99').milestone)            

    def test_get_non_existing_milestone(self):
        with self.assertRaises(RoadmapError):
            self.Roadmap.get_milestone('doesnotexist')

    def test_get_milestone_invalid_character(self):
        with self.assertRaises(RoadmapError):
            self.Roadmap.get_milestone('@#$')                                              
            
if __name__ == '__main__':
    unittest.main()
