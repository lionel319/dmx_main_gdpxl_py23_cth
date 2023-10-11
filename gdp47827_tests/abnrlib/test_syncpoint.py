#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr syncpoint library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_syncpoint.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.syncpoint import SyncPoint

class TestSyncpoint(unittest.TestCase):
    '''
    Tests the abnr syncpoint library
    '''
    def setUp(self):
        server = 'sj-webdev1.altera.com'
        self.syncpoint = SyncPoint(server=server)

    @patch('dmx.abnrlib.syncpoint.SyncpointWebAPI.get_syncpoint_configuration')
    def test_convert_syncpoint_to_full_config_name_no_config_for_syncpoint(self,
                                                                           mock_get_syncpoint_configuration):
        '''
        Tests the convert_syncpoint_to_full_config_name method when there's no config associated with the syncpoint
        '''
        mock_get_syncpoint_configuration.return_value = ''
        self.assertFalse(self.syncpoint.convert_syncpoint_to_full_config_name('project', 'variant', 'syncpoint'))

    @patch('dmx.abnrlib.syncpoint.format_configuration_name_for_printing')
    @patch('dmx.abnrlib.syncpoint.SyncpointWebAPI.get_syncpoint_configuration')
    def test_convert_syncpoint_to_full_config_name_config_is_associated_with_syncpoint(self,
                                                                                       mock_get_syncpoint_config,
                                                                                       mock_format_config_name):
        '''
        Tests the convert_syncpoint_to_full_config_name wheneverything works
        '''
        project = 'project'
        variant = 'variant'
        syncpoint = 'syncpoint'
        config = 'config'
        full_config_name = '{0}/{1}@{2}'.format(project, variant, config)

        mock_get_syncpoint_config.return_value = config
        mock_format_config_name.return_value = full_config_name

        self.assertEqual(self.syncpoint.convert_syncpoint_to_full_config_name(project, variant, syncpoint),
                         full_config_name)

    def test_split_syncpoint_name_works(self):
        '''
        Tests the split_syncpoint_name method works
        '''
        syncpoint_project = 'syncpoint_project'
        syncpoint_variant = 'syncpoint_variant'
        syncpoint_name = 'syncpont_name'
        full_syncpoint_name = '{0}/{1}@{2}'.format(syncpoint_project, syncpoint_variant, syncpoint_name)

        (ret_project, ret_variant, ret_syncpoint) = self.syncpoint.split_syncpoint_name(full_syncpoint_name)
        self.assertEqual(syncpoint_project, ret_project)
        self.assertEqual(syncpoint_variant, ret_variant)
        self.assertEqual(syncpoint_name, ret_syncpoint)

    @patch('dmx.abnrlib.syncpoint.SyncpointWebAPI.get_releases_from_syncpoint')
    def test_get_all_configs_for_syncpoint_no_config(self, mock_get_releases_from_syncpoint):
        '''
        Tests the get_all_configs_for_syncpoint method when a syncpoint has not configs
        '''
        mock_get_releases_from_syncpoint.return_value = [
            ['not.a.real.project', 'not.a.real.variant', '']
        ]

        self.assertFalse(self.syncpoint.get_all_configs_for_syncpoint('syncpoint_name'))

    @patch('dmx.abnrlib.syncpoint.SyncpointWebAPI.get_releases_from_syncpoint')
    def test_get_all_configs_for_syncpoint_works(self, mock_get_releases_from_syncpoint):
        '''
        Tests the get_all_configs_for_syncpoint method when it works
        '''
        all_configs = [
            ['project_one', 'variant_one', 'config_one'],
            ['project_two', 'variant_two', 'config_two']
        ]
        mock_get_releases_from_syncpoint.return_value = all_configs

        config_tuples = self.syncpoint.get_all_configs_for_syncpoint('syncpoint_name')

        self.assertEqual(len(all_configs), len(config_tuples))
        for config in all_configs:
            self.assertIn((config[0], config[1], config[2]), config_tuples)


if __name__ == '__main__':
    unittest.main()
