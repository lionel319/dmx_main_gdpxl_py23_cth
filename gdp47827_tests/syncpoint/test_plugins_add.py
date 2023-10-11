#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint add
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.add import AddRunner, AddError

class TestAdd(unittest.TestCase):
    '''
    Tests the syncpoint add plugin
    '''
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.project_variant_exists')
    def setUp(self, mock_project_variant_exists, mock_variant_exists, mock_syncpoint_exists, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_a.return_value = ['fclead']
        mock_variant_exists.return_value = True
        mock_project_variant_exists.return_value = False
        self.runner = AddRunner('syncpoint', 'project', 'variant')

    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.syncpoint_exists')
    def test_init_syncpoint_does_not_exist(self, mock_syncpoint_exists, mock_a):
        mock_a.return_value = ['fclead']
        mock_syncpoint_exists.return_value = False

        with self.assertRaises(AddError):
            AddRunner('syncpoint', 'project', 'variant')

    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.syncpoint_exists')
    def test_init_project_does_not_exist(self, mock_syncpoint_exists, mock_project_exists, mock_variant_exists, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_project_exists.return_value = False
        mock_a.return_value = ['fclead']
        mock_variant_exists.return_value = False

        with self.assertRaises(AddError):
            AddRunner('syncpoint','project', 'variant')

    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.syncpoint_exists')
    def test_init_variant_does_not_exist(self, mock_syncpoint_exists, mock_variant_exists, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_a.return_value = ['fclead']
        mock_variant_exists.return_value = False

        with self.assertRaises(AddError):
            AddRunner('syncpoint','project', 'variant')
    
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.project_variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.syncpoint_exists')
    def test_init_project_variant_already_exists(self, mock_syncpoint_exists, mock_variant_exists, mock_project_variant_exists, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_a.return_value = ['fclead']
        mock_variant_exists.return_value = True
        mock_project_variant_exists.return_value = True

        with self.assertRaises(AddError):
            AddRunner('syncpoint','project', 'variant')

    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.add_syncpoint')
    def test_run_pass(self, mock_add_syncpoint, mock_a):
        mock_add_syncpoint.return_value = 0 
        mock_a.return_value = ['fclead']
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.add.SyncpointWebAPI.add_syncpoint')
    def test_run_fail(self, mock_add_syncpoint, mock_a):
        mock_add_syncpoint.return_value = 1 
        mock_a.return_value = ['fclead']
        self.assertEqual(self.runner.run(), 1)
    
if __name__ == '__main__':
    unittest.main()
