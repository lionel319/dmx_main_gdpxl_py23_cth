#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_edittree.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.edittree import EditTree, EditTreeError
#from dmx.abnrlib.icmicmconfig import IcmConfig
#from dmx.abnrlib.icmsimpleconfig import IcmConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactoryError


class TestEdittree(unittest.TestCase):
    '''
    Tests the abnr edittree plugin
    '''

    def test_init_no_inplace_or_newconfig(self):
        '''
        Tests init when neither inplace or newconfig are set
        '''
        with self.assertRaises(EditTreeError):
            EditTree('project', 'variant', 'config')

    def test_init_immutable_newconfig(self):
        '''
        Tests init when newconfig is immutable
        '''
        with self.assertRaises(EditTreeError):
            EditTree('project', 'variant', 'config', new_config='REL--foo')

    def test_init_immutable_source_config_without_newconfig(self):
        '''
        Tests init when the source config is immutable and newconfig hasn't been specified
        '''
        with self.assertRaises(EditTreeError):
            EditTree('project', 'variant', 'snap-config', inplace=True)

    def test_init_no_operations_to_perform(self):
        '''
        Tests init when no changes have been specified
        '''
        with self.assertRaises(EditTreeError):
            EditTree('project', 'variant', 'config', inplace=True)

    def test_100___init_cannot_modify_dev_config_inplace(self):
        with self.assertRaises(EditTreeError):
            EditTree('project', 'variant', 'dev', inplace=True)

    def test_101___init_cannot_create_new_dev_config(self):
        with self.assertRaises(EditTreeError):
            EditTree('project', 'variant', 'dev', inplace=False, new_config='dev')

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'release_exists')    
    @patch.object(ICManageCLI, 'library_exists')   
    @patch.object(ICManageCLI, 'libtype_exists')        
    @patch.object(ICManageCLI, 'variant_exists')    
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_init_arguments_wrong_format(self, mock_create_from_icm, mock_config_exists, 
                                    mock_variant_exists, mock_libtype_exists, 
                                    mock_library_exists, mock_release_exists,
                                    mock_project_exists):
        '''
        Tests init when given arguments are in an incorrect format
        '''
        mock_project_exists.return_value = True
        mock_release_exists.return_value = True
        mock_library_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_create_from_icm.return_value = True

        wrong_add_config_arg = [['abc/def@dev', 'def@dev']]
        wrong_add_config_arg2 = [['abc/def/dev', 'def@dev']]
        correct_add_config_arg = [['abc/def@dev', 'def/dev']]
        wrong_del_config_arg = [['abc/def', 'abc']]
        wrong_del_config_arg2 = [['abcdef', 'abc']]
        wrong_del_config_arg3 = [['abcdef']]
        correct_del_config_arg = [['abc/def', 'abc/def']]
        wrong_rep_config_arg = [['abc', 'abc']]
        correct_rep_config_arg = [['abc/def', 'abc']]
        wrong_add_libtype_arg = [['abc/def/ghi@jkl']]
        correct_add_libtype_arg = [['abc/def:ghi@jkl']]
        wrong_del_libtype_arg = [['abc/def/ghi']]
        correct_del_libtype_arg = [['abc/def:ghi']]
        wrong_rep_libtype_arg = [['abc/def/ghi', 'abc']]
        correct_rep_libtype_arg = [['abc/def:ghi', 'abc']]

        self.assertTrue(EditTree('abc', 'def', 'devv', inplace=True, 
                                        add_configs=correct_add_config_arg, preview=True))
        self.assertTrue(EditTree('abc', 'def', 'devv', inplace=True, 
                                        del_configs=correct_del_config_arg, preview=True))
        self.assertTrue(EditTree('abc', 'def', 'devv', inplace=True, 
                                        rep_configs=correct_rep_config_arg, preview=True))
        self.assertTrue(EditTree('abc', 'def', 'devv', inplace=True, 
                                        add_libtype=correct_add_libtype_arg, preview=True))
        self.assertTrue(EditTree('abc', 'def', 'devv', inplace=True, 
                                        del_libtype=correct_del_libtype_arg, preview=True))
        self.assertTrue(EditTree('abc', 'def', 'devv', inplace=True, 
                                        rep_libtype=correct_rep_libtype_arg, preview=True))

        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             add_configs=wrong_add_config_arg, preview=True)
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             add_configs=wrong_add_config_arg2, preview=True)            
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             del_configs=wrong_del_config_arg, preview=True)
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             del_configs=wrong_del_config_arg2, preview=True)   
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             del_configs=wrong_del_config_arg3, preview=True)                       
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             rep_configs=wrong_rep_config_arg, preview=True)
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             add_libtype=wrong_add_libtype_arg, preview=True)
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             del_libtype=wrong_del_libtype_arg, preview=True)
        with self.assertRaises(EditTreeError):
            EditTree('abc', 'def', 'devv', inplace=True, 
                             rep_libtype=wrong_rep_libtype_arg, preview=True)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_init_config_does_not_exist(self, mock_create_from_icm,    
                                        mock_variant_exists, 
                                        mock_project_exists):
        '''
        Tests init method when config does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.side_effect = ConfigFactoryError('bad config')
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant)]]

        mock_create_from_icm.return_value = root_config

        with self.assertRaises(ConfigFactoryError):
            runner = EditTree(root_config.project, root_config.variant, root_config.config,
                              inplace=True, del_configs=del_config_arg, preview=True)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_init_variant_does_not_exist(self, mock_variant_exists, 
                                         mock_project_exists):
        '''
        Tests init method when variant does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant)]]

        with self.assertRaises(EditTreeError):
            runner = EditTree(root_config.project, root_config.variant, root_config.config,
                              inplace=True, del_configs=del_config_arg, preview=True)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_init_project_does_not_exist(self, mock_variant_exists,
                                         mock_project_exists):
        '''
        Tests init method when project does not exist
        '''
        mock_project_exists.return_value = False
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant)]]

        with self.assertRaises(EditTreeError):
            runner = EditTree(root_config.project, root_config.variant, root_config.config,
                              inplace=True, del_configs=del_config_arg, preview=True)
        

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_project_variant')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_icm_configs_no_parents_fails(self, mock_create_from_icm,
                                                       mock_delete_project_variant,
                                                       mock_variant_exists, 
                                                       mock_project_exists):
        '''
        Tests the delete_icm_configs method when no parents are specified
        and there is a failure
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_delete_project_variant.return_value = False
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_arg, preview=True)

        self.assertFalse(runner.delete_icm_configs())

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_project_variant')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_icm_configs_no_parents_works(self, mock_create_from_icm,
                                                       mock_delete_project_variant,
                                                       mock_variant_exists, 
                                                       mock_project_exists):
        '''
        Tests the delete_icm_configs method when no parents are specified
        and it works
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True        
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_delete_project_variant.return_value = True
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_arg, preview=True)

        self.assertTrue(runner.delete_icm_configs())

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_project_variant_from_parent')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_icm_configs_with_parents_fails(self, mock_create_from_icm,
                                                         mock_delete_project_variant_from_parent,
                                                         mock_variant_exists, 
                                                         mock_project_exists):
        '''
        Tests the delete_icm_configs method with parents and it fails
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_delete_project_variant_from_parent.return_value = False
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant),
                           '{0}/{1}'.format(root_config.project, root_config.variant)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_arg, preview=True)

        self.assertFalse(runner.delete_icm_configs())

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_project_variant_from_parent')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_icm_configs_with_parents_works(self, mock_create_from_icm,
                                                         mock_delete_project_variant_from_parent,
                                                         mock_variant_exists, 
                                                         mock_project_exists):
        '''
        Tests the delete_icm_configs method with parents and it works
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_delete_project_variant_from_parent.return_value = True
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant),
                           '{0}/{1}'.format(root_config.project, root_config.variant)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_arg, preview=True)

        self.assertTrue(runner.delete_icm_configs())

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_icm_configs_with_parents_no_config_found(self, mock_create_from_icm,
                                                      mock_variant_exists, 
                                                      mock_project_exists):
        '''
        Tests the delete_icm_config method with parents and no config found in config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant),
                           '{0}/{1}'.format(root_config.project, root_config.variant)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_arg, preview=True)
        with self.assertRaises(EditTreeError):
            runner.delete_icm_configs()

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_icm_configs_without_parents_no_config_found(self, mock_create_from_icm,
                                                      mock_variant_exists, 
                                                      mock_project_exists):
        '''
        Tests the delete_icm_config method without parents and no config found in config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_arg = [['{0}/{1}'.format(to_del.project, to_del.variant)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_arg, preview=True)
        with self.assertRaises(EditTreeError):
            runner.delete_icm_configs()
            

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.flows.edittree.IcmConfig.remove_configuration')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_project_variant_from_parent_remove_fails(self, mock_create_from_icm,
                                                             mock_variant_exists,
                                                             mock_remove_configuration, 
                                                             mock_project_exists):
        '''
        Tests the delete_project_variant_from_parent method when deleting a config fails
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_remove_configuration.return_value = False
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_args = [
            ['{0}/{1}'.format(to_del.project, to_del.variant),
              '{0}/{1}'.format(root_config.project, root_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_args, preview=True)

        self.assertFalse(runner.delete_project_variant_from_parent([(root_config.project, root_config.variant)],
                                                                   to_del.project, to_del.variant))

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_project_variant_from_parent_remove_works(self, mock_create_from_icm,
                                                             mock_variant_exists, 
                                                             mock_project_exists):
        '''
        Tests the delete_project_variant_from_parent method when deleting a config works
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_args = [
            ['{0}/{1}'.format(to_del.project, to_del.variant),
              '{0}/{1}'.format(root_config.project, root_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_args, preview=True)

        self.assertTrue(runner.delete_project_variant_from_parent([(root_config.project, root_config.variant)],
                                                                   to_del.project, to_del.variant))

        self.assertNotIn(to_del, root_config.configurations)
        self.assertIn(to_del, not_to_del.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_project_variant_from_parent_immutable_configs(self, mock_create_from_icm,
                                                                  mock_variant_exists, 
                                                                  mock_project_exists):
        '''
        Tests the delete_project_variant_from_parent method when deleting a config works
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        new_config = 'new_config'
        # Create a basic config tree
        to_del = IcmConfig('REL--to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('REL--not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_args = [
            ['{0}/{1}'.format(to_del.project, to_del.variant),
              '{0}/{1}'.format(root_config.project, root_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config=new_config, del_configs=del_config_args, preview=True)

        self.assertTrue(runner.delete_project_variant_from_parent([(root_config.project, root_config.variant)],
                                                                   to_del.project, to_del.variant))

        self.assertNotIn(to_del, root_config.configurations)
        self.assertIn(to_del, not_to_del.configurations)
        self.assertIn(root_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_project_variant_remove_mutable_configs(self, mock_create_from_icm,
                                                           mock_variant_exists, 
                                                           mock_project_exists):
        '''
        Tests the delete_project_variant method with mutable configs
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_args = [
            ['{0}/{1}'.format(to_del.project, to_del.variant),
              '{0}/{1}'.format(root_config.project, root_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_configs=del_config_args, preview=True)

        self.assertTrue(runner.delete_project_variant(to_del.project, to_del.variant))

        self.assertNotIn(to_del, root_config.configurations)
        self.assertNotIn(to_del, not_to_del.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_project_variant_remove_immutable_configs(self, mock_create_from_icm,
                                                             mock_variant_exists, 
                                                             mock_project_exists):
        '''
        Tests the delete_project_variant method with immutable configs
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create a basic config tree
        to_del = IcmConfig('REL--to_del_config', 'to_del_project', 'to_del_variant',
                                 [], preview=True)
        not_to_del = IcmConfig('REL--not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_config_args = [
            ['{0}/{1}'.format(to_del.project, to_del.variant),
              '{0}/{1}'.format(root_config.project, root_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', del_configs=del_config_args, preview=True)

        self.assertTrue(runner.delete_project_variant(to_del.project, to_del.variant))

        self.assertNotIn(to_del, root_config.configurations)
        self.assertNotIn(to_del, not_to_del.configurations)
        self.assertEqual(len(set(runner.modified_configs)), 2)
        self.assertIn(root_config, runner.modified_configs)
        self.assertIn(not_to_del, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'libtype_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_libtype_configs_mutable_configs(self, mock_create_from_icm,
                                                   mock_libtype_exists, 
                                                   mock_variant_exists,
                                                   mock_project_exists):
        '''
        Tests the delete_libtype_configs method with a tree of mutable configs
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        # Create the config tree, bottom up
        to_del_libtype = IcmLibrary(project='to_del_project', variant='to_del_variant',
                                     libtype='to_del_libtype', library='to_del_library', changenum='#ActiveDev',
                                     preview=True, use_db=False)
        not_to_del_libtype = IcmLibrary(project='not_to_del_project', variant='not_to_del_variant',
                                         libtype='not_to_del_libtype', library='not_to_del_library', changenum='#ActiveDev',
                                         preview=True, use_db=False)
        to_del = IcmConfig('to_del_config', 'to_del_project', 'to_del_variant',
                                 [to_del_libtype], preview=True)
        not_to_del = IcmConfig('not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del, not_to_del_libtype], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_libtype_args = [
            ['{0}/{1}:{2}'.format(to_del_libtype.project, to_del_libtype.variant,
                                  to_del_libtype.libtype)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, del_libtype=del_libtype_args, preview=True)

        runner.delete_libtype_configs()

        self.assertNotIn(to_del_libtype, to_del.configurations)
        self.assertIn(not_to_del_libtype, not_to_del.configurations)
        self.assertIn(to_del, not_to_del.configurations)
        self.assertIn(to_del, root_config.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'libtype_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_libtype_configs_immutable_configs(self, mock_create_from_icm,
                                                   mock_libtype_exists, 
                                                   mock_variant_exists, 
                                                   mock_project_exists):
        '''
        Tests the delete_libtype_configs method with a tree of immutable configs
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        # Create the config tree, bottom up
        to_del_libtype = IcmLibrary(project='to_del_project', variant='to_del_variant',
                                     libtype='to_del_libtype', library='to_del_library', changenum='#ActiveDev',
                                     preview=True, use_db=False)
        not_to_del_libtype = IcmLibrary(project='not_to_del_project', variant='not_to_del_variant',
                                         libtype='not_to_del_libtype', library='not_to_del_library', changenum='#ActiveDev',
                                         preview=True, use_db=False)
 
        to_del = IcmConfig('REL--to_del_config', 'to_del_project', 'to_del_variant',
                                 [to_del_libtype], preview=True)
        not_to_del = IcmConfig('REL--not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [to_del, not_to_del_libtype], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [to_del, not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_libtype_args = [
            ['{0}/{1}:{2}'.format(to_del_libtype.project, to_del_libtype.variant,
                                  to_del_libtype.libtype)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', del_libtype=del_libtype_args, preview=True)

        runner.delete_libtype_configs()

        self.assertNotIn(to_del_libtype, to_del.configurations)
        self.assertIn(not_to_del_libtype, not_to_del.configurations)
        self.assertIn(to_del, not_to_del.configurations)
        self.assertIn(to_del, root_config.configurations)
        self.assertEqual(len(set(runner.modified_configs)), 3)
        self.assertIn(to_del, runner.modified_configs)
        self.assertIn(not_to_del, runner.modified_configs)
        self.assertIn(root_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'libtype_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_delete_libtype_configs_with_config_not_found(self, mock_create_from_icm,
                                                         mock_libtype_exists, 
                                                         mock_variant_exists, 
                                                         mock_project_exists):
        '''
        Tests the delete_libtype_configs method with config not found in config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        # Create the config tree, bottom up
        to_del_libtype = IcmLibrary(project='to_del_project', variant='to_del_variant',
                                     libtype='to_del_libtype', library='to_del_library', changenum='#ActiveDev',
                                     preview=True, use_db=False)
        not_to_del_libtype = IcmLibrary(project='not_to_del_project', variant='not_to_del_variant',
                                         libtype='not_to_del_libtype', library='not_to_del_library', changenum='#ActiveDev',
                                         preview=True, use_db=False)

        not_to_del = IcmConfig('REL--not_to_del_config', 'not_to_del_project',
                                     'not_to_del_variant', [not_to_del_libtype], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [not_to_del], preview=True)

        mock_create_from_icm.return_value = root_config
        del_libtype_args = [
            ['{0}/{1}:{2}'.format(to_del_libtype.project, to_del_libtype.variant,
                                  to_del_libtype.libtype)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', del_libtype=del_libtype_args, preview=True)

        with self.assertRaises(EditTreeError): 
            runner.delete_libtype_configs()


    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_config_from_full_name')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_add_icm_configs_parent_not_in_tree(self, mock_create_from_icm,
                                                      mock_create_config_from_full_name,
                                                      mock_variant_exists,
                                                      mock_config_exists, 
                                                      mock_project_exists):
        '''
        Tests the add_icm_configs method when the parent project/variant aren't
        in the tree
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create the config tree, bottom up
        sub_config = IcmConfig('sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [sub_config], preview=True)
        config_to_add = IcmConfig('add_config', 'add_project', 'add_variant',
                                        [], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_create_config_from_full_name.return_value = config_to_add

        add_args = [
            ['{0}/{1}@{2}'.format(root_config.project, root_config.variant, root_config.config),
             'not_in_tree_project/not_in_tree_variant']
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, add_configs=add_args, preview=True)

        with self.assertRaises(EditTreeError):
            runner.add_icm_configs()

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_config_from_full_name')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_add_icm_configs_mutable_tree(self, mock_create_from_icm,
                                                mock_create_config_from_full_name,
                                                mock_variant_exists,
                                                mock_config_exists, 
                                                mock_project_exists):
        '''
        Tests the add_icm_configs method with a mutable tree
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create the config tree, bottom up
        sub_config = IcmConfig('sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [sub_config], preview=True)
        config_to_add = IcmConfig('add_config', 'add_project', 'add_variant',
                                        [], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_create_config_from_full_name.return_value = config_to_add

        add_args = [
            ['{0}/{1}@{2}'.format(root_config.project, root_config.variant, root_config.config),
             '{0}/{1}'.format(sub_config.project, sub_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, add_configs=add_args, preview=True)

        runner.add_icm_configs()

        self.assertIn(config_to_add, sub_config.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_config_from_full_name')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_add_icm_configs_immutable_tree(self, mock_create_from_icm,
                                                  mock_create_config_from_full_name,
                                                  mock_variant_exists,
                                                  mock_config_exists, 
                                                  mock_project_exists):
        '''
        Tests the add_icm_configs method with an immutable tree
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create the config tree, bottom up
        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config], preview=True)
        config_to_add = IcmConfig('REL--add_config', 'add_project', 'add_variant',
                                        [], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_create_config_from_full_name.return_value = config_to_add

        add_args = [
            ['{0}/{1}@{2}'.format(root_config.project, root_config.variant, root_config.config),
             '{0}/{1}'.format(sub_config.project, sub_config.variant)]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', add_configs=add_args, preview=True)

        runner.add_icm_configs()

        self.assertIn(config_to_add, sub_config.configurations)
        self.assertEqual(len(set(runner.modified_configs)), 2)
        self.assertIn(sub_config, runner.modified_configs)
        self.assertIn(root_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_config_from_full_name')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_add_icm_configs_with_pv_not_found(self, mock_create_from_icm,
                                                     mock_create_config_from_full_name,
                                                     mock_variant_exists,
                                                     mock_config_exists, 
                                                     mock_project_exists):
        '''
        Tests the add_icm_configs method with the target project/variant not found in config tree
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        # Create the config tree, bottom up        
        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config], preview=True)
        config_to_add = IcmConfig('REL--add_config', 'add_project', 'add_variant',
                                        [], preview=True)

        mock_create_from_icm.return_value = root_config
        mock_create_config_from_full_name.return_value = config_to_add

        add_args = [
            ['{0}/{1}@{2}'.format(root_config.project, root_config.variant, root_config.config),
             '{0}/{1}'.format(sub_config.project, 'unknown_variant')]
        ]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', add_configs=add_args, preview=True)

        with self.assertRaises(EditTreeError): 
            runner.add_icm_configs()

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_add_libtype_configs_mutable_tree(self, mock_create_from_icm,
                                             mock_config_exists, 
                                             mock_variant_exists, 
                                             mock_project_exists):
        '''
        Tests the add_libtype_configs method with a mutable config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up
        sub_config = IcmConfig('sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [sub_config], preview=True)
        config_to_add = IcmLibrary(project='sub_project', variant='sub_variant',
                                     libtype='sub_libtype', library='sub_library', changenum='sub_release',
                                     preview=True, use_db=False)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            else:
                return config_to_add

        mock_create_from_icm.side_effect = side_effect
        config_name = 'test'

        add_args = [['{0}/{1}:{2}@{3} {4}'.format(config_to_add.project, config_to_add.variant,
                                             config_to_add.libtype, config_to_add.library, config_name)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, add_libtype=add_args, preview=True)
        runner.add_libtype_configs()

        self.assertIn(config_to_add, sub_config.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_add_libtype_configs_immutable_tree(self, mock_create_from_icm,
                                             mock_config_exists, 
                                             mock_variant_exists, 
                                             mock_project_exists):
        '''
        Tests the add_libtype_configs method with an immutable config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up
        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config], preview=True)
        config_to_add = IcmLibrary(project='sub_project', variant='sub_variant',
                                     libtype='sub_libtype', library='sub_library', changenum='sub_release',
                                     preview=True, use_db=False)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            else:
                return config_to_add

        mock_create_from_icm.side_effect = side_effect
        config_name = "test"

        add_args = [['{0}/{1}:{2}@{3} {4}'.format(config_to_add.project, config_to_add.variant,
                                             config_to_add.libtype, config_to_add.library, config_name)]]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', add_libtype=add_args, preview=True)
        runner.add_libtype_configs()

        self.assertIn(config_to_add, sub_config.configurations)
        self.assertEqual(len(set(runner.modified_configs)), 2)
        self.assertIn(sub_config, runner.modified_configs)
        self.assertIn(root_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_include_libtype_mutable_tree(self, mock_create_from_icm,
                                                mock_config_exists, 
                                                mock_variant_exists, 
                                                mock_project_exists):
        '''
        Tests the delete_all_except_included_libtypes method with a mutable config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up        
        sub_simple_config = IcmLibrary(project='sub_project', variant='sub_variant',
                                         libtype='libtype1', library='sub_library', changenum='sub_release',
                                         preview=True, use_db=False)
        sub_simple_config2 = IcmLibrary(project='sub_project', variant='sub_variant',
                                          libtype='libtype2', library='sub_library', changenum='sub_release',
                                          preview=True, use_db=False)
        root_simple_config = IcmLibrary(project='root_project', variant='root_variant',
                                          libtype='libtype1', library='root_library', changenum='root_release',
                                          preview=True, use_db=False)

        sub_config = IcmConfig('sub_config', 'sub_project', 'sub_variant',
                                     [sub_simple_config, sub_simple_config2], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [sub_config, root_simple_config], preview=True)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            elif libtype=="libtype1" and variant=="sub_variant":
                return sub_simple_config
            elif libtype=="libtype2" and variant=="sub_variant":
                return sub_simple_config2
            elif libtype=="libtype1" and variant=="root_variant":
                return root_simple_config
                
        mock_create_from_icm.side_effect = side_effect
        config_name = 'test'

        include_args = [['libtype1']]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, include_libtypes=include_args, preview=True)

        runner.delete_all_except_included_libtypes()

        self.assertIn(sub_simple_config, sub_config.configurations)
        self.assertIn(root_simple_config, root_config.configurations)
        self.assertNotIn(sub_simple_config2, sub_config.configurations)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_include_libtype_immutable_tree(self, mock_create_from_icm,
                                                  mock_config_exists, 
                                                  mock_variant_exists, 
                                                  mock_project_exists):
        '''
        Tests the delete_all_except_included_libtypes method with immutable config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up
        sub_simple_config = IcmLibrary(project='sub_project', variant='sub_variant',
                                         libtype='libtype1', library='sub_library', changenum='sub_release',
                                         preview=True, use_db=False)
        sub_simple_config2 = IcmLibrary(project='sub_project', variant='sub_variant',
                                          libtype='libtype2', library='sub_library', changenum='sub_release',
                                          preview=True, use_db=False)
        root_simple_config = IcmLibrary(project='root_project', variant='root_variant',
                                          libtype='libtype1', library='root_library', changenum='root_release',
                                          preview=True, use_db=False)
        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [sub_simple_config, sub_simple_config2], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config, root_simple_config], preview=True)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            elif libtype=="libtype1" and variant=="sub_variant":
                return sub_simple_config
            elif libtype=="libtype2" and variant=="sub_variant":
                return sub_simple_config2
            elif libtype=="libtype1" and variant=="root_variant":
                return root_simple_config

        mock_create_from_icm.side_effect = side_effect
        config_name = "test"

        include_args = [['libtype1']]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', include_libtypes=include_args, preview=True)

        runner.delete_all_except_included_libtypes()

        self.assertIn(sub_simple_config, sub_config.configurations)
        self.assertIn(root_simple_config, root_config.configurations)
        self.assertNotIn(sub_simple_config2, sub_config.configurations)
        self.assertEqual(len(set(runner.modified_configs)), 2)
        self.assertIn(sub_config, runner.modified_configs)
        self.assertIn(root_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_include_libtype_with_config_not_found(self, mock_create_from_icm,
                                                         mock_config_exists, 
                                                         mock_variant_exists, 
                                                         mock_project_exists):
        '''
        Tests the delete_all_except_included_libtypes method with config not found in config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up
        sub_simple_config = IcmLibrary(project='sub_project', variant='sub_variant',
                                         libtype='libtype1', library='sub_library', changenum='sub_release',
                                         preview=True, use_db=False)
        root_simple_config = IcmLibrary(project='root_project', variant='root_variant',
                                          libtype='libtype1', library='root_library', changenum='root_release',
                                          preview=True, use_db=False)
        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [sub_simple_config], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config, root_simple_config], preview=True)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            elif libtype=="libtype1" and variant=="sub_variant":
                return sub_simple_config
            elif libtype=="libtype1" and variant=="root_variant":
                return root_simple_config

        mock_create_from_icm.side_effect = side_effect
        config_name = "test"

        include_args = [['libtype1']]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', include_libtypes=include_args, preview=True)
        with self.assertRaises(EditTreeError):
            runner.delete_all_except_included_libtypes()
   
    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_exclude_libtype_mutable_tree(self, mock_create_from_icm,
                                                mock_config_exists, 
                                                mock_variant_exists, 
                                                mock_project_exists):
        '''
        Tests the delete_excluded_libtypes method with a mutable config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up        
        sub_simple_config = IcmLibrary(project='sub_project', variant='sub_variant',
                                         libtype='libtype1', library='sub_library', changenum='sub_release',
                                         preview=True, use_db=False)
        sub_simple_config2 = IcmLibrary(project='sub_project', variant='sub_variant',
                                          libtype='libtype2', library='sub_library', changenum='sub_release',
                                          preview=True, use_db=False)
        root_simple_config = IcmLibrary(project='root_project', variant='root_variant',
                                          libtype='libtype1', library='root_library', changenum='root_release',
                                          preview=True, use_db=False)


        sub_config = IcmConfig('sub_config', 'sub_project', 'sub_variant',
                                     [sub_simple_config, sub_simple_config2], preview=True)
        root_config = IcmConfig('root_config', 'root_project', 'root_variant',
                                      [sub_config, root_simple_config], preview=True)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            elif libtype=="libtype1" and variant=="sub_variant":
                return sub_simple_config
            elif libtype=="libtype2" and variant=="sub_variant":
                return sub_simple_config2
            elif libtype=="libtype1" and variant=="root_variant":
                return root_simple_config
                
        mock_create_from_icm.side_effect = side_effect
        config_name = 'test'

        exclude_args = [['libtype2']]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 inplace=True, exclude_libtypes=exclude_args, preview=True)

        runner.delete_excluded_libtypes()

        self.assertIn(sub_simple_config, sub_config.configurations)
        self.assertIn(root_simple_config, root_config.configurations)
        self.assertNotIn(sub_simple_config2, sub_config.configurations)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_exclude_libtype_immutable_tree(self, mock_create_from_icm,
                                                  mock_config_exists, 
                                                  mock_variant_exists,
                                                  mock_project_exists):
        '''
        Tests the delete_excluded_libtypes method with immutable config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up
        sub_simple_config = IcmLibrary(project='sub_project', variant='sub_variant',
                                         libtype='libtype1', library='sub_library', changenum='sub_release',
                                         preview=True, use_db=False)
        sub_simple_config2 = IcmLibrary(project='sub_project', variant='sub_variant',
                                          libtype='libtype2', library='sub_library', changenum='sub_release',
                                          preview=True, use_db=False)
        root_simple_config = IcmLibrary(project='root_project', variant='root_variant',
                                          libtype='libtype1', library='root_library', changenum='root_release',
                                          preview=True, use_db=False)

        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [sub_simple_config, sub_simple_config2], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config, root_simple_config], preview=True)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            elif libtype=="libtype1" and variant=="sub_variant":
                return sub_simple_config
            elif libtype=="libtype2" and variant=="sub_variant":
                return sub_simple_config2
            elif libtype=="libtype1" and variant=="root_variant":
                return root_simple_config

        mock_create_from_icm.side_effect = side_effect
        config_name = "test"

        exclude_args = [['libtype2']]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', exclude_libtypes=exclude_args, preview=True)

        runner.delete_excluded_libtypes()

        self.assertIn(sub_simple_config, sub_config.configurations)
        self.assertIn(root_simple_config, root_config.configurations)
        self.assertNotIn(sub_simple_config2, sub_config.configurations)
        self.assertEqual(len(set(runner.modified_configs)), 2)
        self.assertIn(sub_config, runner.modified_configs)
        self.assertIn(root_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    def test_exclude_libtype_with_config_not_found(self, mock_create_from_icm,
                                                         mock_config_exists, 
                                                         mock_variant_exists, 
                                                         mock_project_exists):
        '''
        Tests the delete_excluded_libtypes method with config not found in config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        # Create the config tree, bottom up
        sub_simple_config = IcmLibrary(project='sub_project', variant='sub_variant',
                                         libtype='libtype1', library='sub_library', changenum='sub_release',
                                         preview=True, use_db=False)
        root_simple_config = IcmLibrary(project='root_project', variant='root_variant',
                                          libtype='libtype1', library='root_library', changenum='root_release',
                                          preview=True, use_db=False)
 
        sub_config = IcmConfig('REL--sub_config', 'sub_project', 'sub_variant',
                                     [sub_simple_config], preview=True)
        root_config = IcmConfig('REL--root_config', 'root_project', 'root_variant',
                                      [sub_config, root_simple_config], preview=True)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if not libtype:
                return root_config
            elif libtype=="libtype1" and variant=="sub_variant":
                return sub_simple_config
            elif libtype=="libtype1" and variant=="root_variant":
                return root_simple_config

        mock_create_from_icm.side_effect = side_effect
        config_name = "test"

        exclude_args = [['libtype2']]

        runner = EditTree(root_config.project, root_config.variant, root_config.config,
                                 new_config='new_config', exclude_libtypes=exclude_args, preview=True)
        with self.assertRaises(EditTreeError):
            runner.delete_excluded_libtypes()

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    def test_replace_icm_configs_mutable_tree(self, mock_config_exists,
                                                    mock_create_from_icm, 
                                                    mock_variant_exists, 
                                                    mock_project_exists):
        '''
        Tests the replace_icm_configs method with a mutable tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True

        # Build the configuration tree bottom up
        bottom_config = IcmConfig('bottom_config', 'bottom_project',
                                        'bottom_variant', [], preview=True)
        middle_config = IcmConfig('middle_config', 'middle_project',
                                        'middle_variant', [bottom_config],
                                        preview=True)
        top_config = IcmConfig('top_config', 'top_project',
                                     'top_variant', [middle_config],
                                     preview=True)

        # Create the replacement config
        replacement_config = IcmConfig('replacement_config', bottom_config.project,
                                             bottom_config.variant, [], preview=True)

        create_from_icm_configs = [top_config, replacement_config]
        def side_effect(project, variant, config, libtype=None, preview=True):
            return create_from_icm_configs.pop(0)

        mock_create_from_icm.side_effect = side_effect

        repc_args = [['{0}/{1}'.format(bottom_config.project, bottom_config.variant),
                     '{}'.format(replacement_config.config)]]

        runner = EditTree(top_config.project, top_config.variant, top_config.config,
                                 rep_configs=repc_args, inplace=True, preview=True)

        runner.replace_icm_configs()
        self.assertNotIn(bottom_config, top_config.flatten_tree())
        self.assertIn(replacement_config, middle_config.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    def test_replace_icm_configs_immutable_tree(self, mock_config_exists,
                                                      mock_create_from_icm, 
                                                      mock_variant_exists, 
                                                      mock_project_exists):
        '''
        Tests the replace_icm_configs method with an immutable tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True

        # Build the configuration tree bottom up
        bottom_config = IcmConfig('REL--bottom_config', 'bottom_project',
                                        'bottom_variant', [], preview=True)
        middle_config = IcmConfig('REL--middle_config', 'middle_project',
                                        'middle_variant', [bottom_config],
                                        preview=True)
        top_config = IcmConfig('snap-top_config', 'top_project',
                                     'top_variant', [middle_config],
                                     preview=True)

        # Create the replacement config
        replacement_config = IcmConfig('snap-replacement_config', bottom_config.project,
                                             bottom_config.variant, [], preview=True)

        create_from_icm_configs = [top_config, replacement_config]
        def side_effect(project, variant, config, libtype=None, preview=True):
            return create_from_icm_configs.pop(0)

        mock_create_from_icm.side_effect = side_effect

        repc_args = [['{0}/{1}'.format(bottom_config.project, bottom_config.variant),
                     '{}'.format(replacement_config.config)]]

        runner = EditTree(top_config.project, top_config.variant, top_config.config,
                                 rep_configs=repc_args, new_config='new_config', preview=True)

        runner.replace_icm_configs()
        self.assertNotIn(bottom_config, top_config.flatten_tree())
        self.assertIn(replacement_config, middle_config.configurations)
        self.assertEqual(len(runner.modified_configs), 2)
        self.assertIn(middle_config, runner.modified_configs)
        self.assertIn(top_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    def test_replace_icm_configs_with_config_not_found(self, mock_config_exists,
                                                             mock_create_from_icm, 
                                                             mock_variant_exists, 
                                                             mock_project_exists):
        '''
        Tests the replace_icm_configs method with config not found in config tree.
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True

        # Build the configuration tree bottom up
        bottom_config = IcmConfig('REL--bottom_config', 'bottom_project',
                                        'bottom_variant', [], preview=True)
        middle_config = IcmConfig('REL--middle_config', 'middle_project',
                                        'middle_variant', [bottom_config],
                                        preview=True)
        top_config = IcmConfig('snap-top_config', 'top_project',
                                     'top_variant', [middle_config],
                                     preview=True)

        # Create the replacement config
        replacement_config = IcmConfig('snap-replacement_config', bottom_config.project,
                                             'unknown_variant', [], preview=True)

        create_from_icm_configs = [top_config, replacement_config]
        def side_effect(project, variant, config, libtype=None, preview=True):
            return create_from_icm_configs.pop(0)

        mock_create_from_icm.side_effect = side_effect

        repc_args = [['{0}/{1}'.format(replacement_config.project, replacement_config.variant),
                     '{}'.format(replacement_config.config)]]

        runner = EditTree(top_config.project, top_config.variant, top_config.config,
                                 rep_configs=repc_args, new_config='new_config', preview=True)
        
        with self.assertRaises(EditTreeError):
            runner.replace_icm_configs()

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_update_modified_config_tree_new_config_not_set(self, mock_variant_exists,
                                                            mock_config_exists,
                                                            mock_create_from_icm, 
                                                            mock_project_exists):
        '''
        Tests the updated_modified_config_tree method when new_config is not set
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        source_config = IcmConfig('config', 'project', 'variant', [],
                                        preview=True)
        mock_create_from_icm.return_value = source_config

        runner = EditTree(source_config.project, source_config.variant,
                                 source_config.config, add_configs=[['foo/foo@foo', 'foo/foo']],
                                 inplace=True, preview=True)

        with self.assertRaises(EditTreeError):
            runner.update_modified_config_tree()

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_update_modified_config_tree_works(self, mock_variant_exists, 
                                                mock_config_exists,
                                               mock_create_from_icm, 
                                               mock_project_exists):
        '''
        Tests the updated_modified_config_tree method when it works
        '''
        def side_effect(project, variant, config, libtype=None, preview=True):
            if config=="new_config":
                return False
            else:
                return True

        mock_project_exists.return_value = True
        mock_config_exists.side_effect = side_effect
        mock_variant_exists.return_value = True
        sub_config = IcmConfig('sub_config', 'sub_project', 'sub_variant',
                                     [], preview=True)
        source_config = IcmConfig('config', 'project', 'variant', [sub_config],
                                        preview=True)
        mock_create_from_icm.return_value = source_config

        runner = EditTree(source_config.project, source_config.variant,
                                 source_config.config, add_configs=[['foo/foo@foo', 'foo/foo']],
                                 new_config='new_config', preview=True)
        runner.modified_configs = [sub_config]

        runner.update_modified_config_tree()
        for config in runner.source_config.configurations:
            self.assertEqual(config.config, runner.new_config)

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.replace_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.add_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_operate_on_icm_configs_fails(self, mock_variant_exists,
                                                mock_config_exists,
                                                mock_create_from_icm,
                                                mock_delete_icm_configs,
                                                mock_add_icm_configs,
                                                mock_replace_icm_configs, 
                                                mock_project_exists):
        '''
        Tests the operate_on_icm_configs method when there's a failure
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_delete_icm_configs.return_value = False
        mock_add_icm_configs.return_value = False
        mock_replace_icm_configs.return_value = False

        source_config = IcmConfig('config', 'project', 'variant', [],
                                        preview=True)
        mock_create_from_icm.return_value = source_config

        runner = EditTree(source_config.project, source_config.variant,
                                 source_config.config, add_configs=[['foo/foo@foo', 'foo/foo']],
                                 del_configs=[['foo/foo']], rep_configs=[['foo/foo', 'foo']],
                                 inplace=True, preview=True)

        self.assertEqual(runner.operate_on_icm_configs(), 1)

    @patch.object(ICManageCLI, 'project_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.replace_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.add_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_operate_on_icm_configs_works(self, mock_variant_exists,
                                                mock_config_exists,
                                                mock_create_from_icm,
                                                mock_delete_icm_configs,
                                                mock_add_icm_configs,
                                                mock_replace_icm_configs, 
                                                mock_project_exists):
        '''
        Tests the operate_on_icm_configs method when it works
        '''
        mock_project_exists.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_delete_icm_configs.return_value = True
        mock_add_icm_configs.return_value = True
        mock_replace_icm_configs.return_value = True

        source_config = IcmConfig('config', 'project', 'variant', [],
                                        preview=True)
        mock_create_from_icm.return_value = source_config

        runner = EditTree(source_config.project, source_config.variant,
                                source_config.config, add_configs=[['foo/foo@foo', 'foo/foo']],
                                 del_configs=[['foo/foo']], rep_configs=[['foo/foo', 'foo']],
                                 inplace=True, preview=True)

        self.assertEqual(runner.operate_on_icm_configs(), 0)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    def test_replace_libtype_configs_mutable_tree(self, mock_config_exists,
                                                 mock_create_from_icm, 
                                                 mock_variant_exists, 
                                                 mock_project_exists):
        '''
        Tests the replace_libtype_configs method with a mutable tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True

        # Build the configuration tree bottom up
        bottom_simple = IcmLibrary('bottom_simple', 'bottom_project', 'bottom_variant',
                                     'rtl', 'bottom_library', '#ActiveDev', preview=True,
                                     use_db=False)
        bottom_config = IcmConfig('bottom_config', bottom_simple.project,
                                        bottom_simple.variant, [bottom_simple], preview=True)
        top_simple = IcmLibrary('top_simple', 'top_project', 'top_variant', 'rtl',
                                  'top_library', '#ActiveDev', preview=True, use_db=False)
        top_config = IcmConfig('top_config', top_simple.project, top_simple.variant,
                                     [top_simple, bottom_config], preview=True)

        # Create the replacement config
        #replacement_config = IcmLibrary('replacement_config', project=bottom_simple.project,
        replacement_config = IcmLibrary(project=bottom_simple.project,
                                          variant=bottom_simple.variant, libtype=bottom_simple.libtype,
                                          library=bottom_simple.library, changenum='8', preview=True,
                                          use_db=False)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if libtype:
                return replacement_config
            else:
                return top_config

        mock_create_from_icm.side_effect = side_effect

        reps_args = [['{0}/{1}:{2}'.format(bottom_simple.project, bottom_simple.variant,
                                           bottom_simple.libtype),
                     '{}'.format(replacement_config.library)]]

        runner = EditTree(top_config.project, top_config.variant, top_config.config,
                                 rep_libtype=reps_args, inplace=True, preview=True)

        runner.replace_libtype_configs()
        self.assertNotIn(bottom_simple, top_config.flatten_tree())
        self.assertIn(replacement_config, bottom_config.configurations)
        self.assertFalse(runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    def test_replace_libtype_configs_immutable_tree(self, mock_config_exists,
                                                   mock_create_from_icm, 
                                                   mock_variant_exists, 
                                                   mock_project_exists):
        '''
        Tests the replace_libtype_configs method with an immutable tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True

        # Build the configuration tree bottom up
        bottom_simple = IcmLibrary('REL--bottom_simple', 'bottom_project', 'bottom_variant',
                                     'rtl', 'bottom_library', '#ActiveDev', preview=True,
                                     use_db=False)
        bottom_config = IcmConfig('REL--bottom_config', bottom_simple.project,
                                        bottom_simple.variant, [bottom_simple], preview=True)
        top_simple = IcmLibrary('REL--top_simple', 'top_project', 'top_variant', 'rtl',
                                  'top_library', '#ActiveDev', preview=True, use_db=False)
        top_config = IcmConfig('snap-top_config', top_simple.project, top_simple.variant,
                                     [top_simple, bottom_config], preview=True)

        # Create the replacement config
        replacement_config = IcmLibrary(project=bottom_simple.project,
                                          variant=bottom_simple.variant, libtype=bottom_simple.libtype,
                                          library=bottom_simple.library, changenum='8', preview=True,
                                          use_db=False)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if libtype:
                return replacement_config
            else:
                return top_config

        mock_create_from_icm.side_effect = side_effect

        reps_args = [['{0}/{1}:{2}'.format(bottom_simple.project, bottom_simple.variant,
                                           bottom_simple.libtype),
                     '{}'.format(replacement_config.library)]]

        runner = EditTree(top_config.project, top_config.variant, top_config.config,
                                 rep_libtype=reps_args, new_config='new_config', preview=True)

        runner.replace_libtype_configs()
        self.assertNotIn(bottom_simple, top_config.flatten_tree())
        self.assertIn(replacement_config, bottom_config.configurations)
        self.assertEqual(len(runner.modified_configs), 2)
        self.assertIn(bottom_config, runner.modified_configs)
        self.assertIn(top_config, runner.modified_configs)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    def test_replace_libtype_configs_with_config_not_found(self, mock_config_exists,
                                                          mock_create_from_icm, 
                                                          mock_variant_exists, 
                                                          mock_project_exists):
        '''
        Tests the replace_libtype_configs method with config not found in config tree
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True

        # Build the configuration tree bottom up
        bottom_simple = IcmLibrary('REL--bottom_simple', 'bottom_project', 'bottom_variant',
                                     'rtl', 'bottom_library', '#ActiveDev', preview=True,
                                     use_db=False)
        bottom_config = IcmConfig('REL--bottom_config', bottom_simple.project,
                                        bottom_simple.variant, [bottom_simple], preview=True)
        top_simple = IcmLibrary('REL--top_simple', 'top_project', 'top_variant', 'rtl',
                                  'top_library', '#ActiveDev', preview=True, use_db=False)
        top_config = IcmConfig('snap-top_config', top_simple.project, top_simple.variant,
                                     [top_simple, bottom_config], preview=True)

        # Create the replacement config
        replacement_config = IcmLibrary('REL--replacement_config', bottom_simple.project,
                                          bottom_simple.variant, 'unknown_libtype',
                                          bottom_simple.library, '8', preview=True,
                                          use_db=False)

        def side_effect(project, variant, config, libtype=None, preview=True):
            if libtype:
                return replacement_config
            else:
                return top_config

        mock_create_from_icm.side_effect = side_effect

        reps_args = [['{0}/{1}:{2}'.format(replacement_config.project, 
                                           replacement_config.variant,
                                           replacement_config.libtype),
                     '{}'.format(replacement_config.library)]]

        runner = EditTree(top_config.project, top_config.variant, top_config.config,
                                 rep_libtype=reps_args, new_config='new_config', preview=True)

        with self.assertRaises(EditTreeError):
            runner.replace_libtype_configs()

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.replace_libtype_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.add_libtype_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_libtype_configs')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'libtype_exists')
    def test_operate_on_simple_configs_fails(self, mock_libtype_exists,
                                             mock_config_exists,
                                             mock_create_from_icm,
                                             mock_delete_libtype_configs,
                                             mock_add_libtype_configs,
                                             mock_replace_libtype_configs, 
                                             mock_variant_exists, 
                                             mock_project_exists):
        '''
        Tests the iperate_on_simple_configs method when there's a failure
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_delete_libtype_configs.return_value = False
        mock_add_libtype_configs.return_value = False
        mock_replace_libtype_configs.return_value = False

        source_config = IcmConfig('config', 'project', 'variant', [],
                                        preview=True)
        mock_create_from_icm.return_value = source_config

        runner = EditTree(source_config.project, source_config.variant,
                                 source_config.config, add_libtype=[['foo/foo:foo@foo']],
                                 del_libtype=[['foo/foo:foo']], rep_libtype=[['foo/foo:foo', 'foo']],
                                 inplace=True, preview=True)

        self.assertEqual(runner.operate_on_simple_configs(), 1)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    @patch('dmx.abnrlib.flows.edittree.EditTree.replace_libtype_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.add_libtype_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.delete_libtype_configs')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'libtype_exists')
    def test_operate_on_simple_configs_works(self, mock_libtype_exists,
                                            mock_config_exists,
                                             mock_create_from_icm,
                                             mock_delete_libtype_configs,
                                             mock_add_libtype_configs,
                                             mock_replace_libtype_configs, 
                                             mock_variant_exists, 
                                             mock_project_exists):
        '''
        Tests the operate_on_simple_configs method when it works
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_delete_libtype_configs.return_value = True
        mock_add_libtype_configs.return_value = True
        mock_replace_libtype_configs.return_value = True

        source_config = IcmConfig('config', 'project', 'variant', [],
                                        preview=True)
        mock_create_from_icm.return_value = source_config

        runner = EditTree(source_config.project, source_config.variant,
                                source_config.config, add_libtype=[['foo/foo:foo@foo']],
                                 del_libtype=[['foo/foo:foo']], rep_libtype=[['foo/foo:foo', 'foo']],
                                 inplace=True, preview=True)

        self.assertEqual(runner.operate_on_simple_configs(), 0)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(IcmConfig, 'validate')
    @patch.object(IcmConfig, 'remove_empty_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.update_modified_config_tree')
    @patch('dmx.abnrlib.flows.edittree.EditTree.operate_on_simple_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.operate_on_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_run_no_errors(self, mock_variant_exists, mock_config_exists, 
                           mock_create_from_icm,
                           mock_operate_on_icm_configs,
                           mock_operate_on_simple_configs,
                           mock_update_modified_config_tree, 
                           mock_remove_empty_configs,
                           mock_validate, 
                           mock_project_exists):

        '''
        Tests the run method when there are no errors
        '''
        mock_project_exists.return_value = True
        mock_remove_empty_configs.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_operate_on_icm_configs.return_value = 0
        mock_operate_on_simple_configs.return_value = 0
        mock_update_modified_config_tree.return_value = 0
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant',
                                                            [], preview=True)
        mock_validate.return_value = []

        runner = EditTree('project', 'variant', 'config',
                                 add_configs=[['foo/foo@foo', 'foo/foo']], del_configs=[['foo/foo']],
                                 rep_configs=[['foo/foo', 'foo']],
                                 inplace=True, preview=True)

        self.assertEqual(runner.run(), 0)

    @patch.object(ICManageCLI, 'project_exists')
    @patch.object(IcmConfig, 'validate')
    @patch.object(IcmConfig, 'remove_empty_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.update_modified_config_tree')
    @patch('dmx.abnrlib.flows.edittree.EditTree.operate_on_simple_configs')
    @patch('dmx.abnrlib.flows.edittree.EditTree.operate_on_icm_configs')
    @patch('dmx.abnrlib.flows.edittree.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch.object(ICManageCLI, 'variant_exists')
    def test_run_with_errors(self, mock_variant_exists, mock_config_exists, 
                           mock_create_from_icm,
                           mock_operate_on_icm_configs,
                           mock_operate_on_simple_configs,
                           mock_update_modified_config_tree, 
                           mock_remove_empty_configs, 
                           mock_validate,
                           mock_project_exists):
        '''
        Tests the run method when there are errors
        '''
        mock_project_exists.return_value = True
        mock_remove_empty_configs.return_value = True
        mock_config_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_operate_on_icm_configs.return_value = 0
        mock_operate_on_simple_configs.return_value = 0
        mock_update_modified_config_tree.return_value = 0
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant',
                                                            [], preview=True)
        mock_validate.return_value = ['error one']

        runner = EditTree('project', 'variant', 'config',
                                 add_configs=[['foo/foo@foo', 'foo/foo']], del_configs=[['foo/foo']],
                                 rep_configs=[['foo/foo', 'foo']],
                                 inplace=True, preview=True)
        with self.assertRaises(EditTreeError):
            runner.run()

if __name__ == '__main__':
    unittest.main()
