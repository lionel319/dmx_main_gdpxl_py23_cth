#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_updatevariant.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import Mock, patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.updatevariant import *
from dmx.abnrlib.icm import ICManageCLI, ICManageError
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.ecolib.family import Family
from dmx.ecolib.iptype import IPType
from mock_ecolib import *

class TestUpdateVariant(unittest.TestCase):
    '''
    Tests the updatevariant ABNR plugin
    '''

    @patch('dmx.ecolib.family.Family.get_iptype')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.abnrlib.icm.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.variant_exists')
    def setUp(self, mock_variant_exists, mock_project_exists, mock_get_ip, mock_get_family_for_icmproject, mock_get_iptype):
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_get_family_for_icmproject.return_value = Family
        mock_get_ip.return_value = MockIP('family', 'variant')
        mock_get_ip.return_value.iptype = 'iptype'
        mock_get_iptype.return_value = MockIPType('family', 'iptype')

        self.runner = UpdateVariant('project', 'variant', None, True)
        self.runner_with_variant_type = UpdateVariant('project', 'variant', 'asic', True)

    def test_get_variant_type_works(self):
        '''
        Tests the get_variant_type method when it works
        '''
        self.assertEqual(self.runner.get_variant_type(), 'iptype')

    def test_get_variant_type_libtypes_invalid_type(self):
        '''
        Tests the get_variant_type_libtypes method with an invalid variant type
        '''
        with self.assertRaises(Exception):
            self.runner.get_variant_type_libtypes('this.should.not.exist')

    @patch('dmx.ecolib.family.Family.get_iptype')
    @patch('dmx.ecolib.iptype.IPType.get_all_deliverables')
    def test_get_variant_type_libtypes_valid_type(self, mock_get_all_deliverables, mock_get_iptype):
        '''
        Tests the get_variant_type_libtypes method with a valid variant type
        '''
        mock_get_iptype.return_value = IPType
        mock_get_all_deliverables.return_value = [MockDeliverable('foo'), MockDeliverable('bar')]
        libtypes = self.runner_with_variant_type.get_variant_type_libtypes('asic', 'roadmap')
        self.assertEqual(len(libtypes), 2)
        self.assertIn('foo', libtypes)
        self.assertIn('bar', libtypes)

    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    def test_get_missing_libtypes_no_current_libtypes(self, mock_get_libtypes):
        '''
        Tests the get_missing_libtypes method when there are no current libtypes
        '''
        mock_get_libtypes.return_value = []
        master_libtypes = ['foo', 'bar']
        missing_libtypes = self.runner.get_missing_libtypes(master_libtypes)
        self.assertEqual(master_libtypes, missing_libtypes)

    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    def test_get_missing_libtypes_no_missing_libtypes(self, mock_get_libtypes):
        '''
        Tests the get_missing_libtypes method when there are no missing libtypes
        '''
        mock_get_libtypes.return_value = ['foo', 'bar']
        master_libtypes = ['foo', 'bar']
        missing_libtypes = self.runner.get_missing_libtypes(master_libtypes)
        self.assertFalse(missing_libtypes)

    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    def test_get_missing_libtypes_with_missing_libtypes(self, mock_get_libtypes):
        '''
        Tests the get_missing_libtypes method when there are missing libtypes
        '''
        mock_get_libtypes.return_value = ['bar']
        master_libtypes = ['foo', 'bar']
        missing_libtypes = self.runner.get_missing_libtypes(master_libtypes)
        self.assertEqual(len(missing_libtypes), 1)
        self.assertIn('foo', missing_libtypes)

    @patch('dmx.abnrlib.icm.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.icmlibrary.IcmLibrary')
    @patch('dmx.abnrlib.icmconfig.IcmConfig')
    def test_add_libtypes_to_composite_config_composite_config_does_not_exist(self, mock_composite_config,
                                                                              mock_simple_config,
                                                                              mock_config_exists):
        '''
        Tests the add_libtypes_to_composite_config method when the composite config doesn't exist
        '''
        mock_config_exists.return_value = False
        mock_composite = mock_composite_config.return_value
        mock_simple = mock_simple_config.return_value

        mock_simple.in_db.return_value = False
        mock_simple.save.return_value = True
        mock_composite.save.return_value = True

        self.assertTrue(self.runner.add_libtypes_to_composite_config(['foo']))

    @patch('dmx.abnrlib.config_factory.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icm.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.icmconfig.IcmConfig')
    @patch('dmx.abnrlib.icmlibrary.IcmLibrary')
    def test_add_libtypes_to_composite_config_save_fails(self, mock_simple_config,
        mock_composite_config, mock_config_exists, mock_create_from_icm):
        '''
        Tests the add_libtypes_to_composite_config method when the save fails
        '''
        mock_config_exists.return_value = True
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_create_from_icm.return_value = mock_composite
        mock_simple.in_db.return_value = False
        mock_simple.save.return_value = False
        mock_composite.save.return_value = False

        self.assertFalse(self.runner.add_libtypes_to_composite_config(['foo']))

    @patch('dmx.abnrlib.config_factory.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icm.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.icmconfig.IcmConfig')
    @patch('dmx.abnrlib.icmlibrary.IcmLibrary')
    def test_add_libtypes_to_composite_config_save_works(self, mock_simple_config,
        mock_composite_config, mock_config_exists, mock_create_from_icm):
        '''
        Tests the add_libtypes_to_composite_config method when the save works
        '''
        mock_config_exists.return_value = True
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_create_from_icm.return_value = mock_composite
        mock_simple.in_db.return_value = False
        mock_simple.save.return_value = True
        mock_composite.save.return_value = True

        self.assertTrue(self.runner.add_libtypes_to_composite_config(['foo']))

    @patch('dmx.abnrlib.icm.ICManageCLI.add_libtypes_to_variant')
    def test_add_missing_libtypes_works(self, mock_add_libtypes_to_variant):
        '''
        Tests the add_missing_libtypes function when it works
        '''
        mock_add_libtypes_to_variant.return_value = 0
        
        self.assertTrue(self.runner.add_missing_libtypes(['libtypes']))

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.update_the_variant')
    def test_run_failure(self, mock_update_the_variant):
        '''
        Tests the run method when there is a failure
        '''
        mock_update_the_variant.return_value = False
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.update_the_variant')
    def test_run_works(self, mock_update_the_variant):
        '''
        Tests the run method when there it works
        '''
        mock_update_the_variant.return_value = True
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.update_the_variant')
    def test_run_exception_raised(self, mock_update_the_variant):
        '''
        Tests the run method when an exception is raised
        '''
        mock_update_the_variant.side_effect = UpdateVariantError('Something went wrong')
        with self.assertRaises(UpdateVariantError):
            self.runner.run()

    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_to_composite_config')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_dev_libraries_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type')
    def test_update_the_variant_composite_update_fails(self, mock_get_variant_type,
                                            mock_get_variant_type_libtypes,
                                            mock_add_libtypes_if_needed,
                                            mock_add_dev_libraries_if_needed,
                                            mock_add_libtypes_to_composite_config,
                                            mock_get_libtypes):
        '''
        Tests the update_the_variant method when updating the composite fails
        '''
        mock_get_variant_type.return_value = 'asic'
        mock_get_variant_type_libtypes.return_value = ['libtype1', 'libtype2']
        mock_add_libtypes_if_needed.return_value = None
        mock_add_dev_libraries_if_needed.return_value = None
        mock_add_libtypes_to_composite_config.return_value = False
        mock_get_libtypes.return_value = ['libtype1', 'libtype2']

        self.assertFalse(self.runner.update_the_variant())

    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_to_composite_config')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_dev_libraries_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type')
    def test_update_the_variant_composite_update_works(self, mock_get_variant_type,
                                            mock_get_variant_type_libtypes,
                                            mock_add_libtypes_if_needed,
                                            mock_add_dev_libraries_if_needed,
                                            mock_add_libtypes_to_composite_config,
                                            mock_get_libtypes):
        '''
        Tests the update_the_variant method when updating the composite works
        '''
        mock_get_variant_type.return_value = 'asic'
        mock_get_variant_type_libtypes.return_value = ['libtype1', 'libtype2']
        mock_add_libtypes_if_needed.return_value = None
        mock_add_dev_libraries_if_needed.return_value = None
        mock_add_libtypes_to_composite_config.return_value = True
        mock_get_libtypes.return_value = ['libtype1', 'libtype2']

        self.assertTrue(self.runner.update_the_variant())

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.remove_non_roadmap_libtype_simple_configs')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.remove_non_roadmap_libtypes_from_composite_configs')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_to_composite_config')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_dev_libraries_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type')
    def test_update_the_variant_remove_from_composite_fails(self, mock_get_variant_type,
                                            mock_get_variant_type_libtypes,
                                            mock_add_libtypes_if_needed,
                                            mock_add_dev_libraries_if_needed,
                                            mock_add_libtypes_to_composite_config,
                                            mock_get_libtypes,
                                            mock_remove_from_composite,
                                            mock_remove_simple):
        '''
        Tests the update_the_variant method when removing from the composite fails
        '''
        mock_get_variant_type.return_value = 'asic'
        mock_get_variant_type_libtypes.return_value = ['libtype1', 'libtype2']
        mock_add_libtypes_if_needed.return_value = None
        mock_add_dev_libraries_if_needed.return_value = None
        mock_add_libtypes_to_composite_config.return_value = True
        mock_get_libtypes.return_value = ['libtype1', 'libtype2', 'bad_libtype']
        mock_remove_from_composite.return_value = False
        mock_remove_simple.return_value = False

        self.assertFalse(self.runner.update_the_variant())

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.remove_non_roadmap_libtype_simple_configs')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.remove_non_roadmap_libtypes_from_composite_configs')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_to_composite_config')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_dev_libraries_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type')
    def test_update_the_variant_remove_from_composite_works(self, mock_get_variant_type,
                                            mock_get_variant_type_libtypes,
                                            mock_add_libtypes_if_needed,
                                            mock_add_dev_libraries_if_needed,
                                            mock_add_libtypes_to_composite_config,
                                            mock_get_libtypes,
                                            mock_remove_from_composite,
                                            mock_remove_simple):
        '''
        Tests the update_the_variant method when removing from the composite works
        '''
        mock_get_variant_type.return_value = 'asic'
        mock_get_variant_type_libtypes.return_value = ['libtype1', 'libtype2']
        mock_add_libtypes_if_needed.return_value = None
        mock_add_dev_libraries_if_needed.return_value = None
        mock_add_libtypes_to_composite_config.return_value = True
        mock_get_libtypes.return_value = ['libtype1', 'libtype2', 'bad_libtype']
        mock_remove_from_composite.return_value = True
        mock_remove_simple.return_value = True

        self.assertTrue(self.runner.update_the_variant())

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_missing_libraries')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_missing_libraries')
    def test_add_dev_libraries_if_needed_no_missing_libraries(self, mock_get_missing_libraries,
                                                              mock_add_missing_libraries):
        '''
        Tests the add_dev_libraries_if_needed method when there are no missing libraries
        '''
        mock_get_missing_libraries.return_value = []
        self.runner.add_dev_libraries_if_needed(['libtype1'])
        self.assertEqual(mock_add_missing_libraries.call_count, 0)

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_missing_libraries')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_missing_libraries')
    def test_add_dev_libraries_if_needed_missing_libraries(self, mock_get_missing_libraries,
                                                              mock_add_missing_libraries):
        '''
        Tests the add_dev_libraries_if_needed method when there are missing libraries
        '''
        mock_get_missing_libraries.return_value = ['libtype1']
        mock_add_missing_libraries.return_value = None
        self.runner.add_dev_libraries_if_needed(['libtype1'])
        self.assertEqual(mock_add_missing_libraries.call_count, 1)

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_missing_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_missing_libtypes')
    def test_add_libtypes_if_needed_no_missing_libtypes(self, mock_get_missing_libtypes,
                                                          mock_add_missing_libtypes):
        '''
        Tests the add_libtypes_if_needed when there are no missing libtypes
        '''
        mock_get_missing_libtypes.return_value = []
        self.runner.add_libtypes_if_needed(['libtype1'])
        self.assertEqual(mock_add_missing_libtypes.call_count, 0)

    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_missing_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_missing_libtypes')
    def test_add_libtypes_if_needed_missing_libraries(self, mock_get_missing_libtypes,
                                                              mock_add_missing_libtypes):
        '''
        Tests the add_libtypes_if_needed method when there are missing libtypes
        '''
        mock_get_missing_libtypes.return_value = ['libtype1']
        mock_add_missing_libtypes.return_value = None
        self.runner.add_libtypes_if_needed(['libtype1'])
        self.assertEqual(mock_add_missing_libtypes.call_count, 1)

    def test_add_missing_libraries_no_libtypes(self):
        '''
        Tests the add_missing_libraries method when there are no missing libtypes
        '''
        self.assertTrue(self.runner.add_missing_libraries([]))

    @patch('dmx.abnrlib.icm.ICManageCLI.add_libtype_configs')
    @patch('dmx.abnrlib.icm.ICManageCLI.add_libraries')
    def _test_add_missing_libraries_add_configs_fails(self, mock_add_libraries, mock_add_libtype_configs):
        '''
        Tests the add_missing_libraries method when adding simple configs fails
        '''
        mock_add_libraries.return_value = None
        mock_add_libtype_configs.return_value = ['error']
        self.assertFalse(self.runner.add_missing_libraries(['libtype1']))

    @patch('dmx.abnrlib.icm.ICManageCLI.add_libtype_configs')
    @patch('dmx.abnrlib.icm.ICManageCLI.add_libraries')
    def _test_add_missing_libraries_add_configs_works(self, mock_add_libraries, mock_add_libtype_configs):
        '''
        Tests the add_missing_libraries method when adding simple configs works
        '''
        mock_add_libraries.return_value = None
        mock_add_libtype_configs.return_value = []
        self.assertTrue(self.runner.add_missing_libraries(['libtype1']))

    @patch('dmx.abnrlib.icm.ICManageCLI.library_exists')
    def test_get_missing_libraries_none_missing(self, mock_library_exists):
        '''
        Tests the get_missing_libraries method when there are no missing libraries
        '''
        mock_library_exists.return_value = True
        self.assertEqual(self.runner.get_missing_libraries(['libtype']), [])

    @patch('dmx.abnrlib.icm.ICManageCLI.library_exists')
    def test_get_missing_libraries_some_missing(self, mock_library_exists):
        '''
        Tests the get_missing_libraries method when there are missing libraries
        '''
        mock_library_exists.return_value = False
        self.assertEqual(self.runner.get_missing_libraries(['libtype']), ['libtype'])

    @patch('dmx.abnrlib.icm.ICManageCLI.del_config')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_configs')
    def _test_remove_non_roadmap_libtype_simple_configs_del_config_fails(self,
                                                                        mock_get_configs,
                                                                        mock_del_config):
        '''
        Tests the remove_non_roadmap_libtype_simple_configs method when deleting
        the config fails
        '''
        mock_get_configs.return_value = ['test_config']
        mock_del_config.side_effect = ICManageError('Delete error')

        self.assertFalse(self.runner.remove_non_roadmap_libtype_simple_configs(['bad_libtype']))

    @patch('dmx.abnrlib.icm.ICManageCLI.del_config')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_configs')
    def _test_remove_non_roadmap_libtype_simple_configs_del_config_works(self,
                                                                        mock_get_configs,
                                                                        mock_del_config):
        '''
        Tests the remove_non_roadmap_libtype_simple_configs method when deleting
        the config works
        '''
        mock_get_configs.return_value = ['test_config']
        mock_del_config.return_value = True

        self.assertTrue(self.runner.remove_non_roadmap_libtype_simple_configs(['bad_libtype']))

    @patch('dmx.abnrlib.config_factory.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmlibrary.IcmLibrary')
    @patch('dmx.abnrlib.icmconfig.IcmConfig')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_configs')
    def test_remove_non_roadmap_libtypes_from_composite_configs_remove_failed(self,
                                                                              mock_get_configs,
                                                                              mock_composite_config,
                                                                              mock_simple_config,
                                                                              mock_create_from_icm):
        '''
        Tests the remove_non_roadmap_libtypes_from_composite_configs method when remove
        the config fails
        '''
        libtype = 'bad_libtype'
        mock_get_configs.return_value = ['test_config']
        mock_simple = mock_simple_config.return_value
        mock_simple.is_config.return_value = False
        mock_simple.libtype = libtype

        mock_composite = mock_composite_config.return_value
        mock_composite.configurations = [mock_simple]
        mock_composite.remove_configuration.return_value = False
        mock_create_from_icm.return_value = mock_composite

        self.assertFalse(self.runner.remove_non_roadmap_libtypes_from_composite_configs([libtype]))

    @patch('dmx.abnrlib.config_factory.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmlibrary.IcmLibrary')
    @patch('dmx.abnrlib.icmconfig.IcmConfig')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_configs')
    def test_remove_non_roadmap_libtypes_from_composite_configs_save_failed(self,
                                                                            mock_get_configs,
                                                                            mock_composite_config,
                                                                            mock_simple_config,
                                                                            mock_create_from_icm):
        '''
        Tests the remove_non_roadmap_libtypes_from_composite_configs method when saving
        the changes to the composite config fails
        '''
        libtype = 'bad_libtype'
        mock_get_configs.return_value = ['test_config']
        mock_simple = mock_simple_config.return_value
        mock_simple.is_config.return_value = False
        mock_simple.libtype = libtype

        mock_composite = mock_composite_config.return_value
        mock_composite.configurations = [mock_simple]
        mock_composite.remove_configuration.return_value = True
        mock_composite.save.return_value = False
        mock_create_from_icm.return_value = mock_composite

        self.assertFalse(self.runner.remove_non_roadmap_libtypes_from_composite_configs([libtype]))

    @patch('dmx.abnrlib.config_factory.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmlibrary.IcmLibrary')
    @patch('dmx.abnrlib.icmconfig.IcmConfig')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_configs')
    def test_remove_non_roadmap_libtypes_from_composite_configs_works(self,
                                                                      mock_get_configs,
                                                                      mock_composite_config,
                                                                      mock_simple_config,
                                                                      mock_create_from_icm):
        '''
        Tests the remove_non_roadmap_libtypes_from_composite_configs method when it works
        '''
        libtype = 'bad_libtype'
        mock_get_configs.return_value = ['test_config']
        mock_simple = mock_simple_config.return_value
        mock_simple.is_simple.return_value = True
        mock_simple.libtype = libtype

        mock_composite = mock_composite_config.return_value
        mock_composite.configurations = [mock_simple]
        mock_composite.remove_configuration.return_value = True
        mock_composite.save.return_value = True
        mock_create_from_icm.return_value = mock_composite

        self.assertTrue(self.runner.remove_non_roadmap_libtypes_from_composite_configs([libtype]))

    @patch('dmx.abnrlib.icm.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.icm.ICManageCLI.variant_exists')
    def test_init_variant_type_not_exists(self, mock_variant_exists, 
                                      mock_project_exists):
        '''
        Tests init function when variant type doesn't exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        with self.assertRaises(Exception):
            runner = UpdateVariant('project', 'variant', 'custom', True)
    
    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_to_composite_config')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_dev_libraries_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.add_libtypes_if_needed')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type')
    def _test_update_the_variant_add_variant_properties_works(self, mock_get_variant_type,
                                            mock_get_variant_type_libtypes,
                                            mock_add_libtypes_if_needed,
                                            mock_add_dev_libraries_if_needed,
                                            mock_add_libtypes_to_composite_config,
                                            mock_get_libtypes,
                                            mock_add_variant_properties):
        '''
        Tests the update_the_variant method when updating the variant type works
        '''
        mock_get_variant_type.return_value = 'custom'
        mock_get_variant_type_libtypes.return_value = ['libtype1', 'libtype2']
        mock_add_libtypes_if_needed.return_value = None
        mock_add_dev_libraries_if_needed.return_value = None
        mock_add_libtypes_to_composite_config.return_value = True
        mock_get_libtypes.return_value = ['libtype1', 'libtype2']
        mock_add_variant_properties.return_value = True

        self.assertTrue(self.runner_with_variant_type.update_the_variant())

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type_libtypes')
    @patch('dmx.abnrlib.flows.updatevariant.UpdateVariant.get_variant_type')
    def _test_update_the_variant_add_variant_properties_fails(self, mock_get_variant_type, mock_get_variant_type_libtypes,
                                            mock_add_variant_properties):
        '''
        Tests the update_the_variant method when updating the variant type fails
        '''
        mock_get_variant_type.return_value = 'custom'
        mock_get_variant_type_libtypes.return_value = []
        mock_add_variant_properties.side_effect = ICManageError()
        self.assertFalse(self.runner_with_variant_type.update_the_variant())
        '''
        with self.assertRaises(ICManageError):
            self.runner_with_variant_type.update_the_variant()
        '''
if __name__ == '__main__':
    unittest.main()
