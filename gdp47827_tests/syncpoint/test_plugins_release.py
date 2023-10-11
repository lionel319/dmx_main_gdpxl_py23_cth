#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint release
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.release import *

class TestRelease(unittest.TestCase):
    '''
    Tests the syncpoint release plugin
    '''
    @patch('dmx.abnrlib.flows.checkconfigs.CheckConfigs')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.CompositeConfigHierarchy.get_configs_top_down')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.CompositeConfigHierarchy.__init__')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.CheckConflict.build_config_dict')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.CheckConflict.check_config_conflict')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.config_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.project_variant_exists')
    def setUp(self, mock_project_variant_exists, mock_config_exists, mock_syncpoint_exists, mock_get_user_roles, mock_ccc, mock_bcd, mock_cch, mock_gctd, mock_cc):
        mock_cch.return_value = None
        mock_gctd = [[]]
        mock_bcd.return_value = [[]]
        mock_ccc.return_value = [[]]
        mock_syncpoint_exists.return_value = True
        mock_config_exists.return_value = True
        mock_project_variant_exists.return_value = True
        mock_get_user_roles.return_value = ['owner']
        mock_cc.return_value = MockCheckConfigs()
        self.runner = ReleaseRunner('syncpoint', 'project', 'variant', 'REL', True, True, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    def test_init_syncpoint_does_not_exist(self, mock_syncpoint_exists):
        mock_syncpoint_exists.return_value = False

        with self.assertRaises(ReleaseError):
            ReleaseRunner('syncpoint', 'project', 'variant', 'REL', False, True, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.config_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    def test_init_project_does_not_exist(self, mock_syncpoint_exists, mock_project_exists, mock_variant_exists, mock_config_exists):
        mock_syncpoint_exists.return_value = True
        mock_project_exists.return_value = False
        mock_variant_exists.return_value = False
        mock_config_exists.return_value = False

        with self.assertRaises(ReleaseError):
            ReleaseRunner('syncpoint','project', 'variant', 'REL', False, True, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.config_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.project_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    def test_init_variant_does_not_exist(self, mock_syncpoint_exists, mock_project_exists, mock_variant_exists, mock_config_exists):
        mock_syncpoint_exists.return_value = True
        mock_variant_exists.return_value = False
        mock_config_exists.return_value = False
        mock_project_exists.return_value = True

        with self.assertRaises(ReleaseError):
            ReleaseRunner('syncpoint','project', 'variant', 'REL', False, True, False)
           
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.config_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    def test_init_config_does_not_exist(self, mock_syncpoint_exists, mock_variant_exists, mock_config_exists):
        mock_syncpoint_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = False

        with self.assertRaises(ReleaseError):
            ReleaseRunner('syncpoint','project', 'variant', 'REL', False, True, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.project_variant_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.config_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    def test_init_project_variant_does_not_exist(self, mock_syncpoint_exists, mock_config_exists, mock_project_variant_exists):
        mock_syncpoint_exists.return_value = True
        mock_config_exists.return_value = True
        mock_project_variant_exists.return_value = False

        with self.assertRaises(ReleaseError):
            ReleaseRunner('syncpoint','project', 'variant', 'REL', False, True, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.ICManageCLI.config_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    def test_init_cfg_not_rel(self, mock_syncpoint_exists, mock_config_exists):
        mock_syncpoint_exists.return_value = True
        mock_config_exists.return_value = True

        with self.assertRaises(ReleaseError):
            ReleaseRunner('syncpoint','project', 'variant', 'dev', False, True, False)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.get_releases_from_syncpoint')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.project_variant_released')
    def test_run_user_not_lead_to_rerelease(self, mock_project_variant_released, mock_get_releases_from_syncpoint):
        mock_get_releases_from_syncpoint.return_value = [('project','variant','REL')]
        mock_project_variant_released.return_value = True
        with self.assertRaises(ReleaseError):
            self.runner.run()

    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.get_users_by_role')  
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.project_variant_exists')  
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.syncpoint_exists')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.get_user_roles')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.release_syncpoint')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.project_variant_released')  
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ReleaseRunner.send_email')
    def test_run_pass(self, mock_send_email, mock_project_variant_released, mock_release_syncpoint, mock_ur, mock_se, mock_pve, mock_gubr):
        mock_project_variant_released.return_value = False
        mock_se.return_value = True
        mock_send_email.return_value = True
        mock_gubr.return_value = ['userA']
        mock_pve.return_value = True
        mock_ur.return_value = ['fclead']
        mock_release_syncpoint.return_value = 0 
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.release_syncpoint')
    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.project_variant_released')  
    @patch('dmx.syncpointlib.syncpoint_plugins.release.ReleaseRunner.send_email')
    def test_run_fail(self, mock_send_email, mock_project_variant_released, mock_release_syncpoint):
        mock_project_variant_released.return_value = False
        mock_send_email.return_value = True
        mock_release_syncpoint.return_value = 1 
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.syncpointlib.syncpoint_plugins.release.SyncpointWebAPI.get_releases_from_syncpoint')
    def test_get_release_of_project_variant(self, mock_get_releases_from_syncpoint):
        mock_get_releases_from_syncpoint.return_value = [['projA','varA','cfgA']]
        self.assertEqual(self.runner.get_release_of_project_variant('syncpoint','projA','varA'), 'cfgA')

    @patch('dmx.syncpointlib.syncpoint_plugins.release.ReleaseRunner.send_email')
    def test_send_email(self, mock_send_email):
        mock_send_email.return_value = True
        self.assertEqual(self.runner.send_email('abc', 'test', 'test', 'def'), True)

   
class MockCheckConfigs(object):
    def __init__(self):
        return None
    def run(self):
        return False

if __name__ == '__main__':
    unittest.main()
