#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr delconfig plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_deleteconfig.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.deleteconfig import *

class TestDeleteConfig(unittest.TestCase):
    '''
    Tests the delconfig plugin
    '''

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.config_exists')
    def setUp(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = True

        self.project = 'project'
        self.variant = 'variant'
        self.config = 'config'

        self.runner = DeleteConfig(self.project, self.variant, self.config,
                                      preview=True)

    def test_init_snap_config(self):
        '''
        Tests the init method with a snap- config
        '''
        with self.assertRaises(DeleteConfigError):
            DeleteConfig('project', 'variant', 'snap-config')

    def test_init_rel_config(self):
        '''
        Tests the init method with a REL config
        '''
        with self.assertRaises(DeleteConfigError):
            DeleteConfig('project', 'variant', 'REL1.0__config')

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.config_exists')
    def test_init_config_does_not_exist(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the config does not exist
        '''
        mock_config_exists.return_value = False
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = True

        with self.assertRaises(DeleteConfigError):
            DeleteConfig('project', 'variant', 'config')

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.config_exists')
    def test_init_simple_config_does_not_exist(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when simple configs don't exist
        '''
        mock_config_exists.return_value = False
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = True

        with self.assertRaises(DeleteConfigError):
            DeleteConfig('project', 'variant', 'config')

    @patch('dmx.abnrlib.flows.deleteconfig.DeleteConfig.delete_composite_config')
    def test_run_composite_config_error(self, mock_delete_composite_config,
                                        ):
        '''
        Tests the run method when deleting a composite config errors
        '''
        mock_delete_composite_config.return_value = 1

        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.deleteconfig.DeleteConfig.delete_composite_config')
    def test_run_composite_config_works(self, mock_delete_composite_config,
                                        ):
        '''
        Tests the run method when deleting a composite config works
        '''
        mock_delete_composite_config.return_value = 0

        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.deleteconfig.DeleteConfig.delete_composite_config')
    def test_run_simple_config_error(self, mock_delete_composite_config,
                                     ):
        '''
        Tests the run method when deleting a simple config errors
        '''
        mock_delete_composite_config.return_value = 1
        self.runner.libtypes = ['libtype1', 'libtype2']

        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.deleteconfig.DeleteConfig.delete_composite_config')
    def test_run_simple_config_works(self, mock_delete_composite_config,
                                     ):
        '''
        Tests the run method when deleting a simple config works
        '''
        mock_delete_composite_config.return_value = 0
        self.runner.libtypes = ['libtype1', 'libtype2']

        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.del_config')
    def test_delete_composite_config_error(self, mock_del_config):
        '''
        Tests the delete_composite_config method when there's an error
        '''
        mock_del_config.return_value = False
        self.runner.libtypes = ['libtype1', 'libtype2']

        self.assertEqual(self.runner.delete_composite_config(), 1)

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.del_config')
    def test_delete_composite_config_works(self, mock_del_config):
        '''
        Tests the delete_composite_config method when it works
        '''
        mock_del_config.return_value = True
        self.runner.libtypes = ['libtype1', 'libtype2']

        self.assertEqual(self.runner.delete_composite_config(), 0)

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.del_config')
    def test_delete_composite_config_error(self, mock_del_config):
        '''
        Tests the delete_composite_config method when there's an error
        '''
        mock_del_config.return_value = False

        self.assertEqual(self.runner.delete_composite_config(), 1)

    @patch('dmx.abnrlib.flows.deleteconfig.ICManageCLI.del_config')
    def test_delete_composite_config_works(self, mock_del_config):
        '''
        Tests the delete_composite_config method when it works
        '''
        mock_del_config.return_value = True

        self.assertEqual(self.runner.delete_composite_config(), 0)

if __name__ == '__main__':
    unittest.main()
