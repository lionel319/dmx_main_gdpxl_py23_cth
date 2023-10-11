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
from dmx.syncpointlib.syncpoint_user_plugins.list import ListRunner

class TestList(unittest.TestCase):
    '''
    Tests the syncpoint_user list plugin
    '''
  
    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.ListRunner.user_exists')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.get_altera_userid')   
    def test_init_user_does_not_exist(self,mock_get_altera_userid, mock_user_exists):
        mock_user_exists.return_value = False
        mock_get_altera_userid.return_value = 'user'

        with self.assertRaises(Exception):
            ListRunner('user', 'role')

    def test_init_argument_not_given(self):
        with self.assertRaises(Exception):
            ListRunner('','')

    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.ListRunner.user_exists')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.get_altera_userid')
    def test_run_users_role(self, mock_get_altera_userid, mock_get_user_roles, mock_user_exists):
        mock_get_user_roles.return_value = []
        mock_user_exists.return_value = True
        mock_get_altera_userid.return_value = 'user'
        self.runner = ListRunner('user','')
        self.assertEqual(self.runner.run(),0)

    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.ListRunner.user_exists')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.SyncpointWebAPI.get_users_by_role')
    @patch('dmx.syncpointlib.syncpoint_user_plugins.list.get_altera_userid')
    def test_run_users_by_role(self, mock_get_altera_userid, mock_get_users_by_role, mock_user_exists):
        mock_get_users_by_role.return_value = []
        mock_user_exists.return_value = True
        mock_get_altera_userid.return_value = ''
        self.runner = ListRunner('','role')
        self.assertEqual(self.runner.run(),0)


if __name__ == '__main__':
    unittest.main()
