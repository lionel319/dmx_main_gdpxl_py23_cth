#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr createsnapshot plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_createconfig.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import Mock, PropertyMock, patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.createconfig import *
#from dmx.abnrlib.icm import ICManageCLI, convert_altera_config_name_to_icm
#from dmx.abnrlib.icmicmconfig import CompositeConfig
import tempfile

class TestBuildConfig(unittest.TestCase):
    '''
    Tests the createconfig abnr command
    '''

    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def setUp(self, mock_icm_cli):
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = True
        mock_cli.variant_exists.return_value = True
        mock_cli.is_name_immutable.return_value = False
        mock_cli.config_exists.return_value = False
        self.runner = CreateConfig('project', 'variant', 'config', ['project/variant:libtype@subconfigs'], '',
                                        'description', preview=True)
        self.runner2 = CreateConfig('project', 'variant', 'config', ['project2/variant2@subconfigs'], '',
                                        'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.ConfigFactory')
    def test_convert_subconfigs_to_objects(self, mock_config_factory):
        '''
        Tests the convert_subconfigs_to_objects method with a simple config
        '''
        subconfig_objects = self.runner.convert_sub_configs_to_objects()
        self.assertTrue(len(subconfig_objects) == 1)

    @patch('dmx.abnrlib.flows.createconfig.ConfigFactory')
    def test_convert_subconfigs_to_objects_with_subip(self, mock_config_factory):
        '''
        Tests the convert_subconfigs_to_objects method with a simple config
        '''
        subconfig_objects = self.runner2.convert_sub_configs_to_objects()
        self.assertTrue(len(subconfig_objects) == 1)


    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def test_build_config_runner_cannot_create_rel(self, mock_icm_cli):
        '''
        Tests that the build_config_runner object will not create a REL config
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = True
        mock_cli.variant_exists.return_value = True
        mock_cli.config_exists.return_value = False

        with self.assertRaises(CreateConfigError):
            CreateConfig('project', 'variant', 'RELconfig', ['subconfig'], '',
                              'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def test_build_config_runner_project_does_not_exist(self, mock_icm_cli):
        '''
        Tests that the build_config_runner when the project does not exist
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = False

        with self.assertRaises(CreateConfigError):
            CreateConfig('project', 'variant', 'config', ['subconfig'], '',
                              'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def test_build_config_runner_variant_does_not_exist(self, mock_icm_cli):
        '''
        Tests that the build_config_runner when the variant does not exist
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = True
        mock_cli.variant_exists.return_value = True

        with self.assertRaises(CreateConfigError):
            CreateConfig('project', 'variant', 'config', ['subconfig'], '',
                              'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def test_build_config_runner_config_already_exists(self, mock_icm_cli):
        '''
        Tests that the build_config_runner when the config already exists
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = True
        mock_cli.variant_exists.return_value = True
        mock_cli.config_exists.return_value = True

        with self.assertRaises(CreateConfigError):
            CreateConfig('project', 'variant', 'config', ['subconfig'], '',
                              'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def test_build_config_runner_no_sub_configs(self, mock_icm_cli):
        '''
        Tests that the build_config_runner when there are no sub configs
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = True
        mock_cli.variant_exists.return_value = True
        mock_cli.config_exists.return_value = False

        with self.assertRaises(CreateConfigError):
            CreateConfig('project', 'variant', 'config', [], '',
                              'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.ICManageCLI')
    def test_build_config_runner_file_does_not_exist(self, mock_icm_cli):
        '''
        Tests that the build_config_runner when there are no sub configs
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.project_exists.return_value = True
        mock_cli.variant_exists.return_value = True
        mock_cli.config_exists.return_value = False

        with self.assertRaises(CreateConfigError):
            CreateConfig('project', 'variant', 'config', [], '/this/should/not/exist',
                              'description', preview=True)

    @patch('dmx.abnrlib.flows.createconfig.IcmConfig')
    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.convert_sub_configs_to_objects')
    def test_run_saving_config_fails(self, mock_convert_subconfigs_to_objects,
                                                mock_icm_config,
                                                ):
        '''
        Tests the run method when saving the configuration fails
        '''
        mock_icm = mock_icm_config.return_value
        mock_icm.save.return_value = False
        mock_convert_subconfigs_to_objects.return_value = ['subconfigs']

        with self.assertRaises(CreateConfigError):
            self.runner.run()

    @patch('dmx.abnrlib.flows.createconfig.IcmConfig')
    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.convert_sub_configs_to_objects')
    def test_run_saving_config_works(self, mock_convert_subconfigs_to_objects,
                                              mock_icm_config,
                                              ):
        '''
        Tests the build_config run method when saving the configuration works
        '''
        mock_icm = mock_icm_config.return_value
        mock_icm.save.return_value = True
        mock_convert_subconfigs_to_objects.return_value = ['subconfigs']

        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.get_list_of_configs_from_file')
    @patch('dmx.abnrlib.flows.createconfig.IcmConfig')
    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.convert_sub_configs_to_objects')
    def test_run_saving_works_with_file(self, mock_convert_subconfigs_to_objects,
                                              mock_icm_config,
                                              mock_get_list_of_configs_from_file,
                                              ):
        '''
        Tests the build_config run method when a file has been specified
        '''
        mock_icm = mock_icm_config.return_value
        mock_icm.save.return_value = True
        mock_convert_subconfigs_to_objects.return_value = ['subconfigs']
        mock_get_list_of_configs_from_file.return_value = []
        self.runner.config_file = 'test.file'

        self.assertEqual(self.runner.run(), 0)
        self.assertEqual(mock_get_list_of_configs_from_file.call_count, 1)

    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.get_full_config_names_from_syncpoint_configs')
    @patch('dmx.abnrlib.flows.createconfig.IcmConfig')
    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.convert_sub_configs_to_objects')
    def test_run_saving_works_with_syncpoint_configs(self, mock_convert_subconfigs_to_objects,
                                                     mock_icm_config,
                                                     mock_get_full_config_names_from_syncpoint_configs,
                                                     ):
        '''
        Tests the build_config run method when a syncpoint config has been specified
        '''
        mock_icm = mock_icm_config.return_value
        mock_icm.save.return_value = True
        mock_convert_subconfigs_to_objects.return_value = ['subconfigs']
        mock_get_full_config_names_from_syncpoint_configs.return_value = []
        self.runner.syncpoint_configs = ['syncpoint']

        self.assertEqual(self.runner.run(), 0)
        self.assertEqual(mock_get_full_config_names_from_syncpoint_configs.call_count, 1)

    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.get_full_config_names_from_syncpoints')
    @patch('dmx.abnrlib.flows.createconfig.IcmConfig')
    @patch('dmx.abnrlib.flows.createconfig.CreateConfig.convert_sub_configs_to_objects')
    def test_run_saving_works_with_syncpoint(self, mock_convert_subconfigs_to_objects,
                                             mock_icm_config,
                                             mock_get_full_config_names_from_syncpoints,
                                             ):
        '''
        Tests the build_config run method when a syncpoint has been specified
        '''
        mock_icm = mock_icm_config.return_value
        mock_icm.save.return_value = True
        mock_convert_subconfigs_to_objects.return_value = ['subconfigs']
        mock_get_full_config_names_from_syncpoints.return_value = []
        self.runner.syncpoints = ['syncpoint']

        self.assertEqual(self.runner.run(), 0)
        self.assertEqual(mock_get_full_config_names_from_syncpoints.call_count, 1)

    def test_get_list_of_configs_from_file_file_does_not_exist(self):
        '''
        Tests the get_list_of_configs_from_file method when the file does not exist
        '''
        self.runner.config_file = '/this/should/not/exist'
        with self.assertRaises(IOError):
            self.runner.get_list_of_configs_from_file()

    def test_get_list_of_configs_from_file_empty_file(self):
        '''
        Tests the get_list_of_configs_from_file method when the file is empty
        '''
        with tempfile.NamedTemporaryFile() as temp:
            self.runner.config_file = temp.name
            self.assertFalse(self.runner.get_list_of_configs_from_file())

    def test_get_list_of_configs_from_file_works(self):
        '''
        Tests the get_list_of_configs_from_file method works
        '''
        lines = [
            'project/variant@config',
            'project/variant:libtype@config',
        ]
        comments = [
            '#This is a comment',
            '#  this is also a comment',
        ]

        with tempfile.NamedTemporaryFile('w') as temp:
            for i in range(len(lines)):
                temp.write('{0}\n'.format(lines[i]))
                temp.write('{0}\n'.format(comments[i]))

            temp.flush()
            self.runner.config_file = temp.name
            configs = self.runner.get_list_of_configs_from_file()

            for line in lines:
                self.assertIn(line, configs)
            for comment in comments:
                self.assertNotIn(comment, configs)

    @patch('dmx.abnrlib.flows.createconfig.SyncPoint')
    def test_get_full_config_names_from_syncpoint_configs(self, mock_syncpoint):
        '''
        Tests the get_full_config_names_from_syncpoint_configs method works
        '''
        full_config_name = 'project/variant@config'
        mock_sp = mock_syncpoint.return_value
        mock_sp.split_syncpoint_name.return_value = ('project', 'variant', 'syncpoint')
        mock_sp.convert_syncpoint_to_full_config_name.return_value = full_config_name

        self.runner.syncpoint_configs = ['project/variant@syncpoint']

        self.assertEqual(self.runner.get_full_config_names_from_syncpoint_configs(), [full_config_name])

    @patch('dmx.abnrlib.flows.createconfig.SyncPoint.get_all_configs_for_syncpoint')
    def test_get_full_config_names_from_syncpoints_no_configs_in_syncpoint(self,
                                                                           mock_get_all_configs_for_syncpoint):
        '''
        Tests the get_full_config_names_from_syncpoints method when there are no configs in a syncpoint
        '''
        mock_get_all_configs_for_syncpoint.return_value = []
        self.runner.syncpoints = ['syncpoint']

        with self.assertRaises(CreateConfigError):
            self.runner.get_full_config_names_from_syncpoints()

    @patch('dmx.abnrlib.flows.createconfig.SyncPoint.get_all_configs_for_syncpoint')
    def test_get_full_config_names_from_syncpoints_works(self, mock_get_all_configs_for_syncpoint):
        '''
        Tests the get_full_config_names_from_syncpoints method when it works
        '''
        project = 'project'
        variant = 'variant'
        config = 'config'
        full_config_name = 'project/variant@config'
        mock_get_all_configs_for_syncpoint.return_value = [(project, variant, config), (project, variant, None)]
        self.runner.syncpoints = ['syncpoint']

        self.assertEqual(self.runner.get_full_config_names_from_syncpoints(), [full_config_name])

if __name__ == '__main__':
    unittest.main()
