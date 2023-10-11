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
from dmx.syncpointlib.syncpoint_user_plugins.delete import DeleteRunner

class TestDelete(unittest.TestCase):
    '''
    Tests the syncpoint_user delete plugin
    '''
    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.DeleteRunner.user_exists')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.get_altera_userid')
    def setUp(self, mock_get_altera_userid, mock_user_exists, mock_get_user_roles):
        mock_user_exists.return_value = True
        mock_get_user_roles.return_value = ['admin','user']
        mock_get_altera_userid.return_value = 'user'
        self.runner = DeleteRunner(['user'], ['user'])

    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.DeleteRunner.get_altera_userid')
    def _test_init_user_does_not_exist(self, mock_user_exists):
        mock_user_exists.return_value = False

        with self.assertRaises(Exception):
            DeleteRunner(['user'], ['role'])

    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.DeleteRunner.user_exists')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.get_altera_userid')
    def test_init_user_role(self, mock_get_altera_userid, mock_user_exists, mock_get_user_roles):
        mock_user_exists.return_value = True
        mock_get_user_roles.return_value = ['user']

        with self.assertRaises(Exception):
            DeleteRunner(['user'], ['admin'])

        mock_get_altera_userid.return_value = 'user'
        mock_get_user_roles.return_value = ['admin']
        DeleteRunner(['user'], ['admin'])
    
    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.SyncpointWebAPI.delete_user')
    def test_run_pass(self, mock_delete_user):
        mock_delete_user.return_value = 0 
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.syncpointlib.syncpoint_user_plugins.delete.SyncpointWebAPI.delete_user')
    def test_run_fail(self, mock_delete_user):
        mock_delete_user.return_value = 1
        #expect no error, delete plugin will print out error messages and continue to process other users
        self.assertEqual(self.runner.run(), 0)

if __name__ == '__main__':
    unittest.main()
