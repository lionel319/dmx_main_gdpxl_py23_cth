#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr branch plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_branchlibraries.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.branchlibraries import *

class TestBranchLibraries(unittest.TestCase):
    '''
    Tests the BranchLibraries class
    '''

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    def setUp(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True        
        mock_project_exists.return_value = True
        self.runner = BranchLibraries('project', 'variant', 'REL1.0', 'branch', [],
                                   'Unit tests', False, False, True, hierarchy=True)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    def test_init_config_does_not_exist(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the config does not exist
        '''
        mock_variant_exists.return_value = True        
        mock_project_exists.return_value = True
        mock_config_exists.return_value = False
        with self.assertRaises(BranchLibrariesError):
            BranchLibraries('project', 'variant', 'RELconfig', 'branch', [],
                         'Unit tests', False, True, False)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.variant_exists')
    def test_init_variant_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the variant does not exist
        '''
        mock_variant_exists.return_value = False
        mock_project_exists.return_value = True
        with self.assertRaises(BranchLibrariesError):
            BranchLibraries('project', 'variant', 'RELconfig', 'branch', [],
                         'Unit tests', False, True, False)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.project_exists')
    def test_init_project_does_not_exist(self, mock_project_exists):
        '''
        Tests the init method when the ptoject does not exist
        '''
        mock_project_exists.return_value = False
        with self.assertRaises(BranchLibrariesError):
            BranchLibraries('project', 'variant', 'RELconfig', 'branch', [],
                         'Unit tests', False, True, False)
            

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    def test_init_config_is_not_rel(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the config is not REL
        '''
        mock_variant_exists.return_value = True        
        mock_project_exists.return_value = True
        mock_config_exists.return_value = False
        with self.assertRaises(BranchLibrariesError):
            BranchLibraries('project', 'variant', 'config', 'branch', [],
                         'Unit tests', False, True, False)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    def test_init_exact_name_for_config(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when exact is specified
        '''
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = True
        runner = BranchLibraries('project', 'variant', 'RELconfig', 'branch', [],
                                 'Unit tests', False, True, True)
        self.assertEqual(runner.new_config_name, 'branch')
        self.assertEqual(runner.branch, 'branch')            

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.do_the_branch')
    def test_run_branch_fails(self, mock_do_the_branch):
        '''
        Tests the run method when do_the_branch fails
        '''
        mock_do_the_branch.return_value = 1
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.do_the_branch')
    def test_run_branch_works(self, mock_do_the_branch):
        '''
        Tests the run method when do_the_branch works
        '''
        mock_do_the_branch.return_value = 0
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.do_the_branch')
    def test_run_exception(self, mock_do_the_branch):
        '''
        Tests the run method when do_the_branch raises an exception
        '''
        mock_do_the_branch.side_effect = BranchLibrariesError('unit testing')
        with self.assertRaises(BranchLibrariesError):
            self.runner.run()

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.get_config_trees')
    def test_do_the_branch_no_source_config(self, mock_get_config_trees):
        '''
        Tests the do_the_branch method when the source config tree cannot
        be built
        '''
        mock_get_config_trees.return_value = (None, 'branch_config_tree')
        with self.assertRaises(BranchLibrariesError):
            self.runner.do_the_branch()

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.get_config_trees')
    def test_do_the_branch_no_branch_config(self, mock_get_config_trees):
        '''
        Tests the do_the_branch method when the initial branch config tree cannot
        be built
        '''
        mock_get_config_trees.return_value = ('source_config_tree', None)
        with self.assertRaises(BranchLibrariesError):
            self.runner.do_the_branch()

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.check_if_branch_already_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.branch_libraries')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.get_config_trees')
    def test_do_the_branch_no_libraries_branched(self, mock_get_config_trees, mock_branch_libraries,
                                                 mock_composite_config, mock_check_if_branch_already_exists):
        '''
        Tests the do_the_branch method when no libraries were branched
        '''
        mock_composite = mock_composite_config.return_value
        mock_get_config_trees.return_value = (mock_composite, mock_composite)
        mock_branch_libraries.return_value = 0
        mock_check_if_branch_already_exists.return_value = None
        with self.assertRaises(BranchLibrariesError):
            self.runner.do_the_branch()

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.check_if_branch_already_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.rename_composite_configs')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.branch_libraries')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.get_config_trees')
    def test_do_the_branch_save_branch_tree_fails(self, mock_get_config_trees, mock_branch_libraries,
                                                 mock_composite_config, mock_rename_composite_configs,
                                                 mock_check_if_branch_already_exists):
        '''
        Tests the do_the_branch method when saving the composite config fails
        '''
        mock_composite = mock_composite_config.return_value
        mock_composite.save.return_value = False
        mock_get_config_trees.return_value = (mock_composite, mock_composite)
        mock_branch_libraries.return_value = 1
        mock_rename_composite_configs.return_value = 0
        mock_check_if_branch_already_exists.return_value = None
        with self.assertRaises(BranchLibrariesError):
            self.runner.do_the_branch()

    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.check_if_branch_already_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.rename_composite_configs')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.branch_libraries')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibraries.get_config_trees')
    def test_do_the_branch_save_branch_tree_works(self, mock_get_config_trees, mock_branch_libraries,
                                                 mock_composite_config, mock_rename_composite_configs,
                                                 mock_check_if_branch_already_exists):
        '''
        Tests the do_the_branch method when branching works
        '''
        mock_composite = mock_composite_config.return_value
        mock_composite.save.return_value = True
        mock_get_config_trees.return_value = (mock_composite, mock_composite)
        mock_branch_libraries.return_value = 1
        mock_rename_composite_configs.return_value = 1
        mock_check_if_branch_already_exists.return_value = None
        self.assertNotEqual(self.runner.do_the_branch(), 1)

    @patch('dmx.abnrlib.flows.branchlibraries.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_get_config_trees(self, mock_composite_config, mock_create_from_icm):
        '''
        Tests the get_config_trees method
        '''
        mock_composite = mock_composite_config.return_value
        mock_composite.clone.return_value = mock_composite
        mock_create_from_icm.return_value = mock_composite
        (source, branch) = self.runner.get_config_trees()
        self.assertEqual(source, mock_composite)
        self.assertEqual(branch, mock_composite)

    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_branch_libraries_no_library_configs(self, mock_composite_config):
        '''
        Tests the branch_libraries method when there are no library configs
        '''
        mock_source = mock_composite_config.return_value
        mock_branch = mock_composite_config.return_value

        mock_source.search.return_value = []

        self.assertEqual(self.runner.branch_libraries(mock_source, mock_branch), 0)

    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_branch_libraries_only_process_libtypes_in_filter(self, mock_composite_config, mock_library_config):
        '''
        Tests the branch_libraries method when there are no library configs that match the
        libtype filter
        '''
        mock_source = mock_composite_config.return_value
        mock_branch = mock_composite_config.return_value

        mock_library = mock_library_config.return_value
        mock_library.libtype.return_value = 'oa'
        mock_library.is_library.return_value = True

        mock_source.flatten_tree.return_value = [mock_library]

        self.runner.libtypes = ['rtl']

        self.assertEqual(self.runner.branch_libraries(mock_source, mock_branch), 0)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.branchlibraries.run_mp')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_branch_libraries_no_replacements_in_tree(self, mock_composite_config, mock_library_config,
                                                      mock_run_mp, mock_create_from_icm,
                                                      mock_config_exists):
        '''
        Tests the branch_libraries method when the library is branched but no matches
        are found and replaced in the branch tree
        '''
        mock_source = mock_composite_config.return_value
        mock_branch = mock_composite_config.return_value
        mock_branch.replace_all_instances_in_tree.return_value = 0

        mock_library_source = mock_library_config.return_value
        mock_library_source.libtype.return_value = 'oa'
        mock_library_source.is_config.return_value = False

        mock_source.flatten_tree.return_value = [mock_library_source]

        mock_library_branch = mock_library_config.return_value
        mock_create_from_icm.return_value = mock_library_branch
        mock_run_mp.return_value = [
            {
                'project' : 'project',
                'variant' : 'variant',
                'libtype' : 'libtype',
                'original_config' : 'original_config',
                'branch_config' : 'branch_config'
            }
        ]
        mock_config_exists.return_value = True
        with self.assertRaises(BranchLibrariesError):
            self.runner.branch_libraries(mock_source, mock_branch)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.branchlibraries.run_mp')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_branch_libraries_works(self, mock_composite_config, mock_library_config,
                                    mock_run_mp, mock_create_from_icm,
                                    mock_config_exists):
        '''
        Tests the branch_libraries method when it works
        '''
        mock_source = mock_composite_config.return_value
        mock_branch = mock_composite_config.return_value
        mock_branch.replace_all_instances_in_tree.return_value = 1
        mock_library_source = mock_library_config.return_value
        mock_library_source.libtype.return_value = 'oa'
        mock_library_source.is_config.return_value = False 

        mock_source.flatten_tree.return_value = [mock_library_source]

        mock_library_branch = mock_library_config.return_value
        mock_create_from_icm.return_value = mock_library_branch
        mock_run_mp.return_value = [
            {
                'project' : 'project',
                'variant' : 'variant',
                'libtype' : 'libtype',
                'original_config' : 'original_config',
                'branch_config' : 'branch_config'
            }
        ]
        mock_config_exists.return_value = True

        self.assertEqual(self.runner.branch_libraries(mock_source, mock_branch), 1)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.branchlibraries.run_mp')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_branch_libraries_preview_mode_config_doesnt_exist(self, mock_composite_config,
                                                               mock_library_config, mock_run_mp,
                                                               mock_config_exists):
        '''
        Tests the branch_libraries method when running in preview mode and a branched
        config does not exist
        '''
        mock_source = mock_composite_config.return_value
        mock_branch = mock_composite_config.return_value
        mock_branch.replace_all_instances_in_tree.return_value = 1

        mock_library_source = mock_library_config.return_value
        mock_library_source.libtype.return_value = 'oa'
        mock_library_source.is_config.return_value = False

        mock_source.flatten_tree.return_value = [mock_library_source]

        mock_library_branch = mock_library_config.return_value
        mock_run_mp.return_value = [
            {
                'project' : 'project',
                'variant' : 'variant',
                'libtype' : 'libtype',
                'original_config' : 'original_config',
                'branch_config' : 'branch_config'
            }
        ]
        mock_config_exists.return_value = False

        self.assertEqual(self.runner.branch_libraries(mock_source, mock_branch), 1)

    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_rename_composite_configs_no_composites(self, mock_composite_config):
        '''
        Tests the rename_composite_configs method when there are no composite configs
        '''
        mock_branch_tree = mock_composite_config.return_value
        mock_branch_tree.flatten_tree.return_value = []
        self.assertEqual(self.runner.rename_composite_configs(mock_branch_tree), 0)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    def test_rename_composite_configs_no_composites(self, mock_icm_cli):
        '''
        Tests the rename_composite_configs method when there are no composite configs
        '''
        mock_cli = mock_icm_cli.return_value
        mock_cli.config_exists.return_value = False
        self.runner.cli = mock_cli

        sub_config = IcmConfig('sub-config', 'project1', 'variant', [], preview=True)
        top_config = IcmConfig('top-config', 'project2', 'variant', [sub_config], preview=True)

        self.assertEqual(self.runner.rename_composite_configs(top_config), 1)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_check_if_branch_already_exists_does_exist(self, mock_composite_config, mock_library_config,
                                                       mock_icm_cli):
        '''
        Tests the check_if_branch_already_exists method when it does exist
        '''
        mock_composite = mock_composite_config.return_value
        mock_library = mock_library_config.return_value
        mock_library.is_config.return_value = False
        mock_composite.flatten_tree.return_value = [mock_library]
        mock_cli = mock_icm_cli.return_value
        mock_cli.library_exists.return_value = True
        self.runner.cli = mock_cli
        with self.assertRaises(BranchLibrariesError):
            self.runner.check_if_branch_already_exists(mock_composite)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.IcmConfig')
    def test_check_if_branch_already_exists_does_not_exist(self, mock_composite_config, mock_library_config,
                                                           mock_icm_cli):
        '''
        Tests the check_if_branch_already_exists method when it does not exist
        '''
        mock_composite = mock_composite_config.return_value
        mock_library = mock_library_config.return_value
        mock_library.is_config.return_value = False
        mock_composite.flatten_tree.return_value = [mock_library]
        mock_cli = mock_icm_cli.return_value
        mock_cli.library_exists.return_value = False
        self.runner.cli = mock_cli
        self.assertTrue(self.runner.check_if_branch_already_exists(mock_composite))

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibrary')
    def test_branch_library_branchlib_fails_branching_library(self, mock_branchlibrunner, mock_icm_cli):
        '''
        Tests the branch_library function when invoking branchlib fails to create the branch
        '''
        mock_branchlib = mock_branchlibrunner.return_value
        mock_branchlib.run.return_value = 1
        mock_cli = mock_icm_cli.return_value
        mock_cli.library_exists.return_value = False

        with self.assertRaises(BranchLibrariesError):
            branch_library('project', 'variant', 'libtype', 'config', 'branch_name',
                           'branch_config', 'description', True, False)

    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary.save')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibrary')
    def test_branch_library_branchlib_branch_works_config_save_fails(self, mock_branchlibrunner, mock_icm_cli,
                                                                     mock_save):
        '''
        Tests the branch_library function when invoking branchlib creates the branch but fails to create config
        '''
        mock_branchlib = mock_branchlibrunner.return_value
        mock_branchlib.run.return_value = 1
        mock_cli = mock_icm_cli.return_value
        mock_cli.library_exists.return_value = False
        mock_cli.config_exists.return_value = False
        mock_save.return_value = True

        with self.assertRaises(BranchLibrariesError):
            branch_library('project', 'variant', 'libtype', 'config', 'branch_name',
                           'branch_config', 'description', True, False)

    @patch('dmx.abnrlib.flows.branchlibraries.IcmLibrary')
    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibrary')
    def test_branch_library_branchlib_branch_and_config_create_works(self,  mock_branchlibrunner, mock_icm_cli,
                                                                     mock_library_config):
        '''
        Tests the branch_library function when invoking branchlib branch and config create works
        '''
        mock_branchlib = mock_branchlibrunner.return_value
        mock_branchlib.run.return_value = 0
        mock_cli = mock_icm_cli.return_value
        mock_cli.library_exists.return_value = False
        mock_cli.config_exists.return_value = False
        mock_library_config.save.return_value = True

        project = 'project'
        variant = 'variant'
        libtype = 'libtype'
        branch_config = 'branch_config'
        original_config = 'original_config'

        branch_details = branch_library(project, variant, libtype, original_config,
                                        'branch_name', branch_config, 'description', True, False)

        self.assertEqual(branch_details['project'], project)
        self.assertEqual(branch_details['variant'], variant)
        self.assertEqual(branch_details['libtype'], libtype)
        self.assertEqual(branch_details['branch_config'], branch_config)
        self.assertEqual(branch_details['original_config'], original_config)

    @patch('dmx.abnrlib.flows.branchlibraries.ICManageCLI')
    @patch('dmx.abnrlib.flows.branchlibraries.BranchLibrary')
    def test_branch_library_branchlib_works(self,  mock_branchlibrunner, mock_icm_cli):
        '''
        Tests the branch_library function when invoking branchlib works
        '''
        mock_branchlib = mock_branchlibrunner.return_value
        mock_branchlib.run.return_value = 0
        mock_cli = mock_icm_cli.return_value
        mock_cli.library_exists.return_value = False
        mock_cli.config_exists.side_effect = [False, True]

        project = 'project'
        variant = 'variant'
        libtype = 'libtype'
        branch_config = 'branch_config'
        original_config = 'original_config'

        branch_details = branch_library(project, variant, libtype, original_config,
                                        'branch_name', branch_config, 'description', True, False)

        self.assertEqual(branch_details['project'], project)
        self.assertEqual(branch_details['variant'], variant)
        self.assertEqual(branch_details['libtype'], libtype)
        self.assertEqual(branch_details['branch_config'], branch_config)
        self.assertEqual(branch_details['original_config'], original_config)


if __name__ == '__main__':
    unittest.main()
