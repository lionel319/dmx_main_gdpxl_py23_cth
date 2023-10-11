#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint list
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.list import *

class TestList(unittest.TestCase):
    '''
    Tests the syncpoint list plugin
    '''

    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_category_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.ICManageCLI.variant_exists')
    def setUp(self, mock_variant_exists, mock_project_exists, mock_syncpoint_exists,mock_syncpoint_category_exists):
        mock_syncpoint_category_exists.return_value = True
        mock_syncpoint_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = True
        self.runner = ListRunner('syncpoint', 'syncpoint-category', 'project', 'variant', False, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_exists')
    def test_init_syncpoint_does_not_exist(self, mock_syncpoint_exists):
        mock_syncpoint_exists.return_value = False

        with self.assertRaises(ListError):
            ListRunner('syncpoint', 'syncpoint-category', 'project', 'variant', False, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_category_exists')
    def test_init_syncpoint_category_does_not_exist(self, mock_syncpoint_exists, mock_syncpoint_category_exists):
        mock_syncpoint_exists.return_value = True
        mock_syncpoint_category_exists.return_value = False

        with self.assertRaises(ListError):
            ListRunner('syncpoint', 'syncpoint-category', 'project', 'variant', False, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_category_exists')
    def test_init_only_variant_given(self, mock_syncpoint_exists, mock_syncpoint_category_exists):
        mock_syncpoint_exists.return_value = True
        mock_syncpoint_category_exists.return_value = False

        with self.assertRaises(ListError):
            ListRunner('syncpoint', 'syncpoint-category', None, 'variant', False, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.list.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_category_exists')
    def test_init_variant_does_not_exist(self, mock_syncpoint_exists, mock_syncpoint_category_exists, mock_variant_exists):
        mock_syncpoint_exists.return_value = True
        mock_syncpoint_category_exists.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(ListError):
             ListRunner('syncpoint', 'syncpoint-category', 'project', 'variant', False, False)
    
    @patch('dmx.syncpointlib.syncpoint_plugins.list.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.syncpoint_category_exists')
    def test_init_project_does_not_exist(self, mock_syncpoint_exists, mock_syncpoint_category_exists, mock_variant_exists, mock_project_exists):
        mock_syncpoint_exists.return_value = True
        mock_syncpoint_category_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = False

        with self.assertRaises(ListError):
             ListRunner('syncpoint', 'syncpoint-category', 'project', 'variant', False, False)
    
    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.get_syncpoints')
    def test_get_list_of_syncpoints(self, mock_get_syncpoints):
        mock_get_syncpoints.return_value = [['sync1', 'my_sync'],['sync2', 'my_sync']]
        self.assertEqual(self.runner.get_list_of_syncpoints()[0], ['my_sync', 'sync1'])
        self.assertEqual(self.runner.get_list_of_syncpoints('my_sync'), ['sync1', 'sync2'])

    @patch('dmx.syncpointlib.syncpoint_plugins.list.SyncpointWebAPI.get_releases_from_syncpoint')
    def test_get_list_of_releases(self, mock_get_releases_from_syncpoint):
        mock_get_releases_from_syncpoint.return_value = [['projA','varA','cfgA'],['projA','varB','cfgC']]
        self.assertEqual(self.runner.get_list_of_releases('syncpoint')[0][0], 'projA')
        self.assertEqual(self.runner.get_list_of_releases('syncpoint', 'projA')[0][1], 'cfgA')
        self.assertEqual(self.runner.get_list_of_releases('syncpoint', 'projA', 'varB'), 'cfgC')  

if __name__ == '__main__':
    unittest.main()
