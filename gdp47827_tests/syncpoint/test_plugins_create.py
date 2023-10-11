#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint create
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.create import *

class TestCreate(unittest.TestCase):
    '''
    Tests the syncpoint create plugin
    '''
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    def setUp(self, mock_syncpoint_exists, mock_ur):
        mock_syncpoint_exists.return_value = False
        mock_ur.return_value = ['fclead']
        self.runner = CreateRunner('syncpoint', 'syncpoint-category', 'description')

    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    def test_init_syncpoint_already_exists(self, mock_syncpoint_exists, mock_ur):
        mock_syncpoint_exists.return_value = True
        mock_ur.return_value = ['fclead']

        with self.assertRaises(CreateError):
            CreateRunner('syncpoint', 'syncpoint-category', 'description')

    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_run_pass(self, mock_create_syncpoint, mock_ur):
        mock_create_syncpoint.return_value = 0 
        mock_ur.return_value = ['fclead']
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_run_fail(self, mock_create_syncpoint, mock_ur):
        mock_create_syncpoint.return_value = 1 
        mock_ur.return_value = ['fclead']
        self.assertEqual(self.runner.run(), 1)
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_fail___with_space(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_se.return_value = False
        mock_ur.return_value = ['fclead']
        with self.assertRaises(CreateError):
            CreateRunner('syncpoint name', 'syncpoint-category', 'description').run()
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_fail___with_special_chars(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_se.return_value = False
        mock_create_syncpoint.return_value = 0 
        mock_ur.return_value = ['fclead']
        with self.assertRaises(CreateError): 
            CreateRunner('syncpoint@name', 'syncpoint-category', 'description').run()
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_fail___start_with_digit(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_se.return_value = False
        mock_ur.return_value = ['fclead']
        with self.assertRaises(CreateError): 
            CreateRunner('123syncpoint', 'syncpoint-category', 'description').run()
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_fail___start_with_special_chars(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_ur.return_value = ['fclead']
        mock_se.return_value = False
        with self.assertRaises(CreateError): 
            CreateRunner('__syncpoint', 'syncpoint-category', 'description').run()
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_fail___end_with_special_chars(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_se.return_value = False
        mock_ur.return_value = ['fclead']
        with self.assertRaises(CreateError): 
            CreateRunner('syncpoint__', 'syncpoint-category', 'description').run()
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_pass___with_special_chars(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_se.return_value = False
        mock_ur.return_value = ['fclead']
        ret = CreateRunner('sync-point__name', 'syncpoint-category', 'description').run()
        self.assertEqual(ret, 0)

    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_pass___with_special_chars_and_digit(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_se.return_value = False
        mock_ur.return_value = ['fclead']
        ret = CreateRunner('sync-point_123_name', 'syncpoint-category', 'description').run()
        self.assertEqual(ret, 0)
   
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.create.SyncpointWebAPI.create_syncpoint')
    def test_syncpoint_name_pass___official_name(self, mock_create_syncpoint, mock_ur, mock_se):
        mock_create_syncpoint.return_value = 0 
        mock_se.return_value = False
        mock_ur.return_value = ['fclead']
        ret = CreateRunner('RRTTLL3.0FM8revA0', 'syncpoint-category', 'description').run()
        self.assertEqual(ret, 0)
   



if __name__ == '__main__':
    unittest.main()
