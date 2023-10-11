#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint delete
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.delete import *

class TestDelete(unittest.TestCase):
    '''
    Tests the syncpoint delete plugin
    '''
    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.project_variant_exists')
    def setUp(self, mock_project_variant_exists, mock_variant_exists, mock_syncpoint_exists, mock_get_user_roles, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_a.return_value = True
        mock_get_user_roles.return_value = ['fclead']
        mock_variant_exists.return_value = True
        mock_project_variant_exists.return_value = True
        self.runner = DeleteRunner('syncpoint', 'project', 'variant', True, False, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    def test_init_syncpoint_does_not_exist(self, mock_syncpoint_exists, mock_get_user_roles, mock_a):
        mock_get_user_roles.return_value = ['fclead']
        mock_a.return_value = True
        mock_syncpoint_exists.return_value = False

        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint', 'project', 'variant', False, False, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    def test_init_project_does_not_exist(self, mock_syncpoint_exists, mock_project_exists, mock_variant_exists, mock_get_user_roles, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_a.return_value = True
        mock_project_exists.return_value = False
        mock_get_user_roles.return_value = ['fclead']
        mock_variant_exists.return_value = False

        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint','project', 'variant', False, False, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    def test_init_variant_does_not_exist(self, mock_syncpoint_exists, mock_variant_exists, mock_get_user_roles, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_get_user_roles.return_value = ['fclead']
        mock_a.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint','project', 'variant', False, False, False)
            
    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.project_variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    def test_init_project_variant_does_not_exist(self, mock_syncpoint_exists, mock_variant_exists, mock_project_variant_exists, mock_get_user_roles, mock_a):
        mock_syncpoint_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_get_user_roles.return_value = ['fclead']
        mock_a.return_value = True
        mock_project_variant_exists.return_value = False

        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint','project', 'variant', False, False, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    def test_init_only_project_or_variant_given(self, mock_syncpoint_exists, mock_get_user_roles, mock_a):
        mock_a.return_value = True
        mock_syncpoint_exists.return_value = True
        mock_get_user_roles.return_value = ['fclead']

        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint', 'project', None, False, False, False)
        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint', None, 'variant', False, False, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.get_releases_from_syncpoint')
    def test_init_syncpoint_contains_project_variant(self, mock_syncpoint_exists, mock_get_releases_from_syncpoint, mock_get_user_roles, mock_a):
        mock_get_user_roles.return_value = ['fclead']
        mock_syncpoint_exists.return_value = True
        mock_a.return_value = True
        mock_get_releases_from_syncpoint.return_value = ['projA','varA','cfgA']
        with self.assertRaises(Exception):
            DeleteRunner('syncpoint', None, None, False, False, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.delete_syncpoint')
    def test_run_pass(self, mock_delete_syncpoint, mock_get_user_roles, mock_a):
        mock_get_user_roles.return_value = ['fclead']
        mock_a.return_value = True
        mock_delete_syncpoint.return_value = 0 
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.delete_syncpoint')
    def test_run_fail(self, mock_delete_syncpoint, mock_get_user_roles, mock_a):
        mock_get_user_roles.return_value = ['fclead']
        mock_a.return_value = True
        mock_delete_syncpoint.return_value = 1 
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.project_variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.syncpoint_exists')
    def test_init_force_switch(self, mock_syncpoint_exists, mock_variant_exists, mock_project_exists, mock_project_variant_exists, mock_get_user_roles, mock_a):
        mock_get_user_roles.return_value = ['fclead']
        mock_a.return_value = True
        mock_syncpoint_exists.return_value = True
        mock_project_exists.return_value = False
        mock_variant_exists.return_value = True
        mock_project_variant_exists.return_value = False
        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint','project', 'variant', False, True, False)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False
        mock_project_variant_exists.return_value = False
        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint','project', 'variant', False, True, False)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False
        mock_project_variant_exists.return_value = True
        DeleteRunner('syncpoint','project', 'variant', False, True, False)

    @patch('dmx.syncpointlib.syncpointlock_api.SyncpointLockApi.raise_error_if_syncpoint_is_locked')
    @patch('dmx.syncpointlib.syncpoint_plugins.delete.SyncpointWebAPI.get_user_roles')
    def test_init_user_not_admin_to_run_delete_all(self, mock_get_user_roles, mock_a):
        mock_get_user_roles.return_value = ['owner']
        mock_a.return_value = True

        with self.assertRaises(DeleteError):
            DeleteRunner('syncpoint','project', 'variant', False, True, True)

if __name__ == '__main__':
    unittest.main()
