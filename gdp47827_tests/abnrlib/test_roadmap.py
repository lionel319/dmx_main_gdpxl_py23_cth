#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_roadmap.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $


import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.ecolib.family import Family
from mock_ecolib import *

class TestRoadmap(unittest.TestCase):
    '''
    Tests the functions in the releasequeue library
    '''
    @patch('dmx.ecolib.family.Family._get_family_properties')
    def setUp(self, mock_get_family_properties):
        self.family = Family('_Testdata')

    @patch('dmx.ecolib.family.Family.get_valid_milestones_threads')
    def test_no_roadmap(self, mock_get_valid_milestones_threads):
        '''
        '''
        mock_get_valid_milestones_threads.return_value = None
        self.assertFalse(self.family.verify_roadmap('', ''))

    @patch('dmx.ecolib.family.Family.get_valid_milestones_threads')
    def test_milestone_thread_not_in_roadmap(self, mock_get_valid_milestones_threads):
        '''
        '''
        mock_get_valid_milestones_threads.return_value = [('5.0','ND5revA')]
        self.assertFalse(self.family.verify_roadmap('4.0', 'ND5revA'))

    @patch('dmx.ecolib.family.Family.get_valid_milestones_threads')
    def test_milestone_thread_in_roadmap(self, mock_get_valid_milestones_threads):
        '''
        '''
        mock_get_valid_milestones_threads.return_value = [('5.0','ND5revA')]
        self.assertTrue(self.family.verify_roadmap('5.0', 'ND5revA'))

    @patch('dmx.ecolib.family.Family.get_products')
    def test_get_valid_milestones_threads(self, mock_get_products):
        mock_product = MockProduct('family', 'ND1')
        mock_product._milestones = [MockMilestone('1.0'), MockMilestone('2.0')]
        mock_product._revisions = [MockRevision('A')]
        mock_get_products.return_value = [mock_product]
        self.assertIn(('1.0', 'ND1revA'), self.family.get_valid_milestones_threads())
        self.assertIn(('2.0', 'ND1revA'), self.family.get_valid_milestones_threads())

if __name__ == '__main__':
    unittest.main()
