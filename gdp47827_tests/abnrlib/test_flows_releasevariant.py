#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_releasevariant.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
from mock import Mock, PropertyMock, patch
import os, sys
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.releasevariant import *
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.tnrlib.waiver_file import WaiverFile
from dmx.ecolib.family import Family
from dmx.ecolib.ip import IP
from dmx.ecolib.product import Product
from mock_ecolib import *

class TestReleaseVariant(unittest.TestCase):
    '''
    Tests the releasevariant ABNR plugin
    '''
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def setUp(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_config_exists, mock_validate_inputs, mock_variant_exists, mock_project_exists, mock_get_roadmap, mock_get_ip, mock_get_product, mock_get_family_for_icmproject):    
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_roadmap.return_value = MockRoadmap('family', 'roadmap')
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        self.runner = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                     'thread', 'description', 'label', True,
                                     preview=True)
        self.runner_prel = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                     'thread', 'description', 'label', True,
                                     preview=True, prel='prel_a')

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.project_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_001___init_project_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_project_exists):
        '''
        Tests releasevariant init when the project does not exist        
        '''
        mock_project_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseVariantError):
            ReleaseVariant('project', 'variant', 'config', 'milestone',
                                           'thread', 'description', 'label', True,
                                           preview=True)

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.variant_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_002___init_variant_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_variant_exists, mock_project_exists):
        '''
        Tests releasevariant init when the variant does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseVariantError):
            ReleaseVariant('project', 'variant', 'config', 'milestone',
                                           'thread', 'description', 'label', True,
                                           preview=True)

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_003___init_config_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_config_exists):
        '''
        Tests init when the config does not exist
        '''
        mock_config_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        with self.assertRaises(ReleaseVariantError):
            ReleaseVariant('project', 'variant', 'config', 'milestone',
                                 'thread', 'description', 'label', preview=True)

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_004___init_config_already_rel(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_config_exists):
        '''
        Tests init when the config is already REL
        '''
        mock_config_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        with self.assertRaises(ReleaseVariantError):
            ReleaseVariant('project', 'variant', 'REL2.0ND5revA__14ww123a', 'milestone',
                                 'thread', 'description', 'label', preview=True)
    
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.convert_waiver_files')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_005___init_waiver_files_do_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_config_exists, mock_validate_inputs,
                                        mock_convert_waiver_files, mock_variant_exists, 
                                        mock_project_exists, mock_get_roadmap, 
                                        mock_get_ip, mock_get_product, 
                                        mock_get_family_for_icmproject):
        '''
        Tests init when a waiver file does exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        wf = WaiverFile()
        mock_convert_waiver_files.return_value = wf
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        runner = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                      'thread', 'description', 'label', 
                                      waiver_files=['file1'],
                                      preview=True)
        self.assertEqual(runner.waivers, wf)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_006___create_snap_cfg_invalid_snap_number(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_composite_config, 
                                                 mock_icm_cli, mock_validate_inputs,
                                                 mock_get_roadmap, 
                                                 mock_get_ip, mock_get_product, 
                                                 mock_get_family_for_icmproject):
        '''
        Tests the create_snap_cfg function when it gets an invalid snap number
        '''
        mock_validate_inputs.return_value = None
        mock_config = mock_composite_config.return_value
        mock_cli = mock_icm_cli.return_value
        mock_cli.get_next_snap_number.return_value = 'foo'
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                      'thread', 'description', 'label', preview=True)
        with self.assertRaises(ValueError):
            runner.create_snap_cfg(mock_config)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_007___create_snap_cfg_clone_fails(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_composite_config, mock_icm_cli,
                                         mock_validate_inputs, mock_get_roadmap, 
                                         mock_get_ip, mock_get_product, 
                                         mock_get_family_for_icmproject):
        '''
        Tests the create_snap_cfg function when the clone fails
        '''
        mock_validate_inputs.return_value = None
        mock_config = mock_composite_config.return_value
        mock_config.clone.return_value = None
        mock_cli = mock_icm_cli.return_value
        mock_cli.get_next_snap_number.return_value = 10
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                'thread', 'description', 'label', preview=True)
        self.assertIsNone(runner.create_snap_cfg(mock_config))

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_008___create_snap_cfg_save_fails(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_composite_config, mock_icm_cli,
                                        mock_validate_inputs, mock_get_roadmap, 
                                        mock_get_ip, mock_get_product, 
                                        mock_get_family_for_icmproject):
        '''
        Tests the create_snap_cfg function when the save fails
        '''
        mock_validate_inputs.return_value = None
        mock_config = mock_composite_config.return_value
        mock_config.save.return_value = False
        mock_config.clone.return_value = mock_config
        mock_cli = mock_icm_cli.return_value
        mock_cli.get_next_snap_number.return_value = 10
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                      'thread', 'description', 'label', preview=True)
        self.assertFalse(runner.create_snap_cfg(mock_config))

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_009___create_snap_cfg_all_works(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_composite_config, mock_icm_cli,
                                       mock_validate_inputs, mock_get_roadmap, 
                                       mock_get_ip, mock_get_product, 
                                       mock_get_family_for_icmproject):
        '''
        Tests the create_snap_cfg function when everything works
        '''
        mock_validate_inputs.return_value = None
        mock_config = mock_composite_config.return_value
        mock_config.save.return_value = True
        mock_config.clone.return_value = mock_config
        mock_cli = mock_icm_cli.return_value
        mock_cli.get_next_snap_number.return_value = 10
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', 'milestone',
                                'thread', 'description', 'label', preview=True)
        self.assertTrue(runner.create_snap_cfg(mock_config))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.get_variant_properties')
    def test_010___verify_variant_no_type(self, mock_get_variant_properties):
        '''
        Tests the verify_variant method when the variant has no type
        '''
        mock_get_variant_properties.return_value = {
            'Owner' : 'me',
            'Created at' : '2014-07-24'
        }
        self.assertFalse(self.runner.verify_variant())

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.get_variant_properties')
    def test_011___verify_variant_type_is_set(self, mock_get_variant_properties):
        '''
        Tests the verify_variant method when the variant has a type
        '''
        mock_get_variant_properties.return_value = {
            'Owner' : 'me',
            'Created at' : '2014-07-24',
            'iptype' : 'asic',
        }
        self.assertTrue(self.runner.verify_variant())

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_011a___verify_config_not_released(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have not been released
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_sub_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL--testing', preview=True)
        unrel_sub_config = IcmLibrary('project', 'variant', 'libtype',
                                        'library', '', preview=True)
        composite.add_configuration(rel_sub_config)
        composite.add_configuration(unrel_sub_config)

        self.assertFalse(self.runner.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_012___verify_config_not_released___prel(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have not been released
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_sub_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL--testing', preview=True)
        unrel_sub_config = IcmLibrary('project', 'variant', 'libtype',
                                        'library', '', preview=True)
        composite.add_configuration(rel_sub_config)
        composite.add_configuration(unrel_sub_config)

        self.assertFalse(self.runner_prel.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_013___verify_config_is_REL___prel(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have not been released
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_sub_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL--testing', preview=True)
        rel2_sub_config = IcmLibrary('project', 'variant', 'libtype',
                                        'library', 'REL111', preview=True)
        composite.add_configuration(rel_sub_config)
        composite.add_configuration(rel2_sub_config)

        self.assertTrue(self.runner_prel.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_014___verify_config_is_PREL_n_REL___prel(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have not been released
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        prel_sub_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'PREL--testing', preview=True)
        rel_sub_config = IcmLibrary('project', 'variant', 'libtype',
                                        'library', 'RELxxx', preview=True)
        composite.add_configuration(rel_sub_config)
        composite.add_configuration(prel_sub_config)

        self.assertTrue(self.runner_prel.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_015___verify_config_is_PREL___non_prel(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have not been released
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_sub_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL--testing', preview=True)
        prel_sub_config = IcmLibrary('project', 'variant', 'libtype',
                                        'library', 'PRELxxx', preview=True)
        composite.add_configuration(rel_sub_config)
        composite.add_configuration(prel_sub_config)
        self.assertFalse(self.runner.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_016___verify_config_is_released_no_ipspsec(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have all been released but does not contain an ipspec
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_oa_config = IcmLibrary('project', 'variant', 'oa', 'library',
                                      'REL--oa', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL--rtl', preview=True)
        composite.add_configuration(rel_oa_config)
        composite.add_configuration(rel_rtl_config)

        self.assertFalse(self.runner.verify_config(composite))
        self.assertFalse(self.runner_prel.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_017___verify_config_is_released_no_local_ipspsec(self, mock_verify, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have all been released but does not contain a local ipspec
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_oa_config = IcmLibrary('project', 'variant', 'oa', 'library',
                                      'REL--oa', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL--rtl', preview=True)
        composite.add_configuration(rel_oa_config)
        composite.add_configuration(rel_rtl_config)

        # Now create another composite config that references a foreign ipspec
        foreign_composite = IcmConfig('foreign_composite', 'project', 'other_variant', [], preview=True)
        rel_foreign_ipspec = IcmLibrary('project', 'other_variant', 'ipspec', 'library',
                                      'REL--ipspec', preview=True)
        foreign_composite.add_configuration(rel_foreign_ipspec)
        composite.add_configuration(foreign_composite)

        self.assertFalse(self.runner.verify_config(composite))
        self.assertFalse(self.runner_prel.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_018___verify_config_is_released_contains_ipspec(self, mock_verify_release_matching_milestones, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have all been released and it contains ipspec
        '''
        mock_verify_release_matching_milestones.return_value = True
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL--ipspec', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL--rtl', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        self.assertTrue(self.runner.verify_config(composite))
        self.assertTrue(self.runner_prel.verify_config(composite))

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_release_matching_milestones')
    def test_019___verify_config_is_preleased_contains_ipspec___prel_mode(self, mock_verify_release_matching_milestones, mock_config_exists):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have all been released and it contains ipspec
        '''
        mock_verify_release_matching_milestones.return_value = True
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'PREL--ipspec', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL--rtl', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        self.assertTrue(self.runner_prel.verify_config(composite))

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_020___verify_release_matching_milestones_contains_matching_milestone(self, mock_get_roadmap_for_thread, mock_get_family_for_thread,
        mock_config_exists, mock_validate_inputs, mock_variant_exists,
        mock_project_exists,  mock_get_roadmap, mock_get_ip, mock_get_product, 
        mock_get_family_for_icmproject):
        '''
         Tests the verify_release_matching_milestones method when the config contains sub-configs
        that have milestone equal to the milestone to release for
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL3.0FM8revA0__YYwwZ', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL3.0FM8revA0__YYwwZ', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', '3.0',
                                'thread', 'description', 'label', True,
                                preview=True)

        self.assertTrue(runner.verify_release_matching_milestones(composite))        
    
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_021___verify_release_matching_milestones_contains_matching_milestone___prel(self, mock_get_roadmap_for_thread, mock_get_family_for_thread,
        mock_config_exists, mock_validate_inputs, mock_variant_exists,
        mock_project_exists,  mock_get_roadmap, mock_get_ip, mock_get_product, 
        mock_get_family_for_icmproject):
        '''
         Tests the verify_release_matching_milestones method when the config contains sub-configs
        that have milestone equal to the milestone to release for
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL3.0FM8revA0__YYwwZ', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'PREL3.0FM8revA0__YYwwZ', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', '3.0',
                                'thread', 'description', 'label', True,
                                preview=True, prel='prel_a')

        self.assertTrue(runner.verify_release_matching_milestones(composite))        

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_022___verify_release_matching_milestones_contains_greater_milestone(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, 
        mock_config_exists, mock_validate_inputs, mock_variant_exists, 
        mock_project_exists, mock_get_roadmap, mock_get_ip, mock_get_product, 
        mock_get_family_for_icmproject):
        '''
        Tests the verify_release_matching_milestones method when the config contains sub-configs
        that have milestone greater than the milestone to release for
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL3.0FM8revA0__YYwwZ', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL4.0FM8revA0__YYwwZ', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', '3.0',
                                'thread', 'description', 'label', True,
                                preview=True)

        self.assertTrue(runner.verify_release_matching_milestones(composite))  
        
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_023___verify_release_matching_milestones_contains_greater_milestone___prel(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, 
        mock_config_exists, mock_validate_inputs, mock_variant_exists, 
        mock_project_exists, mock_get_roadmap, mock_get_ip, mock_get_product, 
        mock_get_family_for_icmproject):
        '''
        Tests the verify_release_matching_milestones method when the config contains sub-configs
        that have milestone greater than the milestone to release for
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'PREL3.0FM8revA0__YYwwZ', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'PREL4.0FM8revA0__YYwwZ', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', '3.0',
                                'thread', 'description', 'label', True,
                                preview=True, prel='prel_4')
        print('prel:{}'.format(runner.prel))
        self.assertTrue(runner.verify_release_matching_milestones(composite))  
        
    # test disabled due to http://pg-rdjira:8080/browse/DI-787                
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')        
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_024___verify_release_matching_milestones_contains_lesser_milestone(self, mock_get_roadmap_for_thread, mock_get_family_for_thread,
        mock_config_exists, mock_validate_inputs, mock_variant_exists, 
        mock_project_exists, mock_get_roadmap, mock_get_ip, mock_get_product, 
        mock_get_family_for_icmproject):
        '''
        Tests the verify_release_matching_milestones method when the config contains sub-configs
        that have milestone lesser than the milestone to release for
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'REL3.0FM8revA0__YYwwZ', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'REL2.0FM8revA0__YYwwZ', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', '3.0',
                                'thread', 'description', 'label', True,
                                preview=True)

        with self.assertRaisesRegexp(ReleaseVariantError, "contains the following BOMs that don't match milestone"):
            runner.verify_release_matching_milestones(composite)                   

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.family.Family.get_roadmap')        
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releaselibrary.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasevariant.validate_inputs')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_025___verify_release_matching_milestones_contains_lesser_milestone___prel(self, mock_get_roadmap_for_thread, mock_get_family_for_thread,
        mock_config_exists, mock_validate_inputs, mock_variant_exists, 
        mock_project_exists, mock_get_roadmap, mock_get_ip, mock_get_product, 
        mock_get_family_for_icmproject):
        '''
        Tests the verify_release_matching_milestones method when the config contains sub-configs
        that have milestone lesser than the milestone to release for
        '''
        mock_config_exists.return_value = False
        composite = IcmConfig('test_composite', 'project', 'variant', [], preview=True)
        rel_ipspec_config = IcmLibrary('project', 'variant', 'ipspec', 'library',
                                      'PREL3.0FM8revA0__YYwwZ', preview=True)
        rel_rtl_config = IcmLibrary('project', 'variant', 'rtl',
                                        'library', 'PREL2.0FM8revA0__YYwwZ', preview=True)
        composite.add_configuration(rel_ipspec_config)
        composite.add_configuration(rel_rtl_config)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        runner = ReleaseVariant('project', 'variant', 'config', '3.0',
                                'thread', 'description', 'label', True,
                                preview=True, prel='prel_1')

        with self.assertRaisesRegexp(ReleaseVariantError, "contains the following BOMs that don't match milestone"):
            runner.verify_release_matching_milestones(composite)                   

    @patch('dmx.abnrlib.flows.releasevariant.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    def test_026___verify_config_is_released(self, mock_composite_config, mock_simple_config):
        '''
        Tests the verify_config method when the config contains sub-configs
        that have all been released but it does not contain ipspec
        '''
        mock_config = mock_composite_config.return_value
        sub_config = mock_composite_config.return_value
        sub_config.is_released.return_value = True
        mock_config.configurations.return_value = [sub_config]
        mock_simple = mock_simple_config.return_value
        mock_simple.libtype = 'rtl'
        mock_config.search.return_value = []

        self.assertFalse(self.runner.verify_config(mock_config))

    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.abnrlib.flows.releasevariant.submit_release')
    def test_027___send_to_queue_submit_release_fails(self, mock_submit_release, mock_composite_config):
        '''
        Tests the send_to_queue method when the queue release fails
        '''
        mock_submit_release.return_value = (False, None)
        mock_composite = mock_composite_config.return_value
        self.assertFalse(self.runner.send_to_queue(mock_composite))

    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.abnrlib.flows.releasevariant.submit_release')
    def test_028___send_to_queue_submit_release_works(self, mock_submit_release, mock_composite_config):
        '''
        Tests the send_to_queue method when the queue release works
        '''
        mock_submit_release.return_value = (True, None)
        mock_composite = mock_composite_config.return_value
        self.assertTrue(self.runner.send_to_queue(mock_composite))

    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.abnrlib.flows.releasevariant.submit_release')
    def test_029___send_to_queue_with_waiver_files(self, mock_submit_release, mock_composite_config):
        '''
        Tests the send_to_queue method with waiver files
        '''
        mock_submit_release.return_value = (True, None)
        mock_composite = mock_composite_config.return_value
        self.runner.waivers = WaiverFile()
        self.assertTrue(self.runner.send_to_queue(mock_composite))

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseJobHandler')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.abnrlib.flows.releasevariant.submit_release')
    def test_030___send_to_queue_wait_release_fails(self, mock_submit_release, mock_composite_config,
                                              mock_release_queue_handler):
        '''
        Tests the send_to_queue method when waiting and the release fails
        '''
        mock_submit_release.return_value = (True, None)
        mock_composite = mock_composite_config.return_value
        mock_queue_handler = mock_release_queue_handler.return_value
        mock_queue_handler.register_callback.return_value = None
        mock_queue_handler.rel_config = None
        self.runner.wait = True
        self.runner.preview = False
        self.assertFalse(self.runner.send_to_queue(mock_composite))
        self.assertIsNone(self.runner.rel_config)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseJobHandler')
    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.abnrlib.flows.releasevariant.submit_release')
    def test_031___send_to_queue_wait_release_works(self, mock_submit_release, mock_composite_config,
                                              mock_release_queue_handler):
        '''
        Tests the send_to_queue method when waiting and the release works
        '''
        rel_config = 'REL1.0'
        mock_submit_release.return_value = (True, None)
        mock_composite = mock_composite_config.return_value
        mock_queue_handler = mock_release_queue_handler.return_value
        mock_queue_handler.register_callback.return_value = None
        mock_queue_handler.rel_config = rel_config
        self.runner.wait = True
        self.runner.preview = False
        self.assertTrue(self.runner.send_to_queue(mock_composite))
        self.assertEqual(self.runner.rel_config, rel_config)


    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test_032___run_bad_variant(self, mock_verify_variant):
        '''
        Tests the run method when the variant is bad
        '''
        mock_verify_variant.return_value = False
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test__033___run_bad_config(self, mock_verify_variant,
                            mock_verify_config, mock_get_config,
                            ):
        '''
        Tests the run method when the config is bad
        '''
        mock_verify_variant.return_value = True
        mock_get_config.return_value = IcmConfig('config', 'project', 'variant', [], preview=True)
        mock_verify_config.return_value = False
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_config_already_released')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test_034___run_content_already_released(self, mock_verify_variant,
                               mock_verify_config, mock_get_config, mock_is_config_already_released,
                               ):
        '''
        Tests the run method when the config has already been released
        '''
        mock_verify_variant.return_value = True
        mock_get_config.return_value = IcmConfig('config', 'project', 'variant', [], preview=True)
        mock_verify_config.return_value = True
        mock_is_config_already_released.return_value = True
        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_config_already_released')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.create_snap_cfg')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test_035___run_create_snap_error(self, mock_verify_variant,
                                   mock_verify_config, mock_get_config, mock_create_snap_cfg,
                                   mock_is_config_already_released):
        '''
        Tests the run method when there is an error creating the snap
        '''
        mock_verify_variant.return_value = True
        mock_get_config.return_value = IcmConfig('config', 'project', 'variant', [], preview=True)
        mock_verify_config.return_value = True
        mock_is_config_already_released.return_value = False
        mock_create_snap_cfg.return_value = None
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_config_already_released')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.send_to_queue')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.create_snap_cfg')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test_036___run_queue_fails(self, mock_verify_variant,
                           mock_verify_config, mock_get_config, mock_create_snap_cfg,
                           mock_send_to_queue, mock_is_config_already_released,
                           ):
        '''
        Tests the run method when sending to queue fails
        '''
        mock_verify_variant.return_value = True
        mock_get_config.return_value = IcmConfig('config', 'project', 'variant', [], preview=True)
        mock_verify_config.return_value = True
        mock_is_config_already_released.return_value = False
        mock_create_snap_cfg.return_value = IcmConfig('snap-config', 'project', 'variant', [], preview=True)
        mock_send_to_queue.return_value = False
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_config_already_released')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.send_to_queue')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.create_snap_cfg')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test_037___run_works(self, mock_verify_variant,
                       mock_verify_config, mock_get_config, mock_create_snap_cfg,
                       mock_send_to_queue, mock_is_config_already_released,
                       ):
        '''
        Tests the run method when it works
        '''
        mock_verify_variant.return_value = True
        mock_get_config.return_value = IcmConfig('config', 'project', 'variant', [], preview=True)
        mock_verify_config.return_value = True
        mock_is_config_already_released.return_value = False
        mock_create_snap_cfg.return_value = IcmConfig('snap-config', 'project', 'variant', [], preview=True)
        mock_send_to_queue.return_value = True
        self.assertEqual(self.runner.run(), 0)
        self.assertEqual(mock_create_snap_cfg.call_count, 1)

    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_config_already_released')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.send_to_queue')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.create_snap_cfg')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.verify_variant')
    def test_038___run_with_immutable_config_does_not_create_new_snap(self, mock_verify_variant,
                                                                       mock_verify_config,
                                                                       mock_get_config,
                                                                       mock_create_snap_cfg,
                                                                       mock_send_to_queue,
                                                                       mock_is_config_already_released,
                                                                       ):
        '''
        Tests the run method when the input config is immutable
        '''
        mock_verify_variant.return_value = True
        self.runner.config = 'snap-this.should.not.exist'
        mock_get_config.return_value = IcmConfig(self.runner.config, 'project', 'variant',
                                                       [], preview=True)
        mock_verify_config.return_value = True
        mock_is_config_already_released.return_value = False
        mock_send_to_queue.return_value = True
        self.assertEqual(self.runner.run(), 0)
        self.assertEqual(mock_create_snap_cfg.call_count, 0)

    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.get_rel_configs')
    def test_039___get_rels_for_milestone_and_thread(self, mock_get_rel_configs):
        '''
        Tests the get_rels_for_milestone_and_thread method
        '''
        matching_rels = [
            'REL{0}{1}__14ww123a'.format(self.runner.milestone, self.runner.thread),
            'REL{0}{1}--TESTING__15ww234b'.format(self.runner.milestone, self.runner.thread)
        ]

        all_rels = [
            'REL9.9ND9revZ__14ww123a',
            'REL0.0ND0revA__15ww234b'
        ]

        all_rels.extend(matching_rels)
        mock_get_rel_configs.return_value = all_rels

        returned_rels = self.runner.get_rels_for_milestone_and_thread()
        self.assertEqual(len(matching_rels), len(returned_rels))
        for rel in matching_rels:
            self.assertIn(rel, returned_rels)

    @patch('dmx.abnrlib.flows.releasevariant.IcmConfig')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_rels_for_milestone_and_thread')
    def test_040___is_config_already_released_no_previous_rels(self, mock_get_rels_for_m_and_t,
                                                         mock_composite_config):
        '''
        Tests the is_config_already_released method when there are no previous
        REL configs
        '''
        mock_get_rels_for_m_and_t.return_value = []
        src_config = mock_composite_config.return_value

        self.assertFalse(self.runner.is_config_already_released(src_config))

    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_rels_for_milestone_and_thread')
    def test_041___is_config_already_released_no_matches(self, mock_get_rels_for_m_and_t, mock_get_config, mock_config_exists):
        mock_get_rels_for_m_and_t.return_value = ['anything']
        mock_config_exists.return_value = False
        simple_config = IcmLibrary(self.runner.project, self.runner.variant,
                                     'ipspec', 'dev', 'REL1.1', preview=True, use_db=False)
        src_config = IcmConfig('snap-foo', self.runner.project, self.runner.variant,
                                     [simple_config], preview=True)
        
        mock_get_config.side_effect = [
            ### This is for 'goldref
            [{
                  u'libtype:parent:name': u'reldoc',
                  u'name': u'REL4.0FM6revA0__21ww473b',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            },
            {
                  u'libtype:parent:name': u'ipspec',
                  u'name': u'REL4.0FM6revA0__21ww473g',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            }],

            ### This is for 'ref
            [{
                  u'libtype:parent:name': u'reldoc',
                  u'name': u'REL4.0FM6revA0__21ww473b___xxx',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            },
            {
                  u'libtype:parent:name': u'ipspec',
                  u'name': u'REL4.0FM6revA0__21ww473g',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            }],

        ]

        self.assertFalse(self.runner.is_config_already_released(src_config))

    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_rels_for_milestone_and_thread')
    def test_042___is_config_already_released_matches(self, mock_get_rels_for_m_and_t, mock_get_config, mock_config_exists):
        mock_get_rels_for_m_and_t.return_value = ['anything']
        mock_config_exists.return_value = False
        simple_config = IcmLibrary(self.runner.project, self.runner.variant,
                                     'ipspec', 'dev', 'REL1.1', preview=True, use_db=False)
        src_config = IcmConfig('snap-foo', self.runner.project, self.runner.variant,
                                     [simple_config], preview=True)
        
        mock_get_config.side_effect = [
            ### This is for 'goldref
            [{
                  u'libtype:parent:name': u'reldoc',
                  u'name': u'REL4.0FM6revA0__21ww473b',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            },
            {
                  u'libtype:parent:name': u'ipspec',
                  u'name': u'REL4.0FM6revA0__21ww473g',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            }],

            ### This is for 'ref
            [{
                  u'libtype:parent:name': u'reldoc',
                  u'name': u'REL4.0FM6revA0__21ww473b',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            },
            {
                  u'libtype:parent:name': u'ipspec',
                  u'name': u'REL4.0FM6revA0__21ww473g',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            }],

        ]

        self.assertTrue(self.runner.is_config_already_released(src_config))

    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.get_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.get_rels_for_milestone_and_thread')
    def test_043___is_config_already_released_matches_but_force_mode(self, mock_get_rels_for_m_and_t, mock_get_config, mock_config_exists):
        mock_get_rels_for_m_and_t.return_value = ['anything']
        mock_config_exists.return_value = False
        simple_config = IcmLibrary(self.runner.project, self.runner.variant,
                                     'ipspec', 'dev', 'REL1.1', preview=True, use_db=False)
        src_config = IcmConfig('snap-foo', self.runner.project, self.runner.variant,
                                     [simple_config], preview=True)
        
        mock_get_config.side_effect = [
            ### This is for 'goldref
            [{
                  u'libtype:parent:name': u'reldoc',
                  u'name': u'REL4.0FM6revA0__21ww473b',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            },
            {
                  u'libtype:parent:name': u'ipspec',
                  u'name': u'REL4.0FM6revA0__21ww473g',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            }],

            ### This is for 'ref
            [{
                  u'libtype:parent:name': u'reldoc',
                  u'name': u'REL4.0FM6revA0__21ww473b',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            },
            {
                  u'libtype:parent:name': u'ipspec',
                  u'name': u'REL4.0FM6revA0__21ww473g',
                  u'project:parent:name': u'i10socfm',
                  u'variant:parent:name': u'liotest1'
            }],

        ]
        self.runner.force = True
        self.assertFalse(self.runner.is_config_already_released(src_config))


    @patch('dmx.abnrlib.flows.releasevariant.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.should_release_config')
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_unneeded')
    def test_045___filter_tree_works(self, mock_is_unneeded, mock_should_release_config, mock_config_exists):
        '''
        Tests that the filter_tree method correctly filters the tree.
        '''
        project = 'test_project'
        variant = 'test_variant'
        library = 'test_library'
        release = ''

        required_libtypes = ['ipspec', 'rtl', 'oa']
        unneeded_libtypes = ['mw', 'complib']
        all_libtypes = required_libtypes + unneeded_libtypes

        # We need a configuration tree containing a mixture of simple configs
        # Some will be included, some not
        all_simple_configs = []
        for libtype in all_libtypes:
            all_simple_configs.append(IcmLibrary(project, variant, libtype,
                                                   library, release, preview=True,
                                                   use_db=False))
        root_config = IcmConfig('dev', project, variant, all_simple_configs,
                                      preview=True)

        def side_effect(simple_config):
            return simple_config.libtype in required_libtypes

        mock_should_release_config.side_effect = side_effect
        mock_config_exists.return_value = False
        mock_is_unneeded.return_value = False

        self.runner.filter_tree(root_config)
        for simple_config in all_simple_configs:
            if simple_config.libtype in required_libtypes:
                self.assertIn(simple_config, root_config.configurations)
            else:
                self.assertNotIn(simple_config, root_config.configurations)

    
    @patch('dmx.abnrlib.flows.releasevariant.ReleaseVariant.is_libtype_required_by_milestone_and_thread')
    @patch('dmx.abnrlib.flows.releasevariant.IcmLibrary')
    def test_046___should_release_config_not_in_roadmap(self, mock_simple_config,
                                                  mock_is_libtype_required_by_milestone_and_thread):
        '''
        Tests the should_release_config method when there are no filters
        '''
        mock_simple = mock_simple_config.return_value
        self.runner.required_only = True
        mock_is_libtype_required_by_milestone_and_thread.return_value = False
        self.assertFalse(self.runner.should_release_config(mock_simple))
                
    @patch('dmx.ecolib.family.Family.get_product')                
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_all_deliverables')
    @patch('dmx.abnrlib.flows.releasevariant.IcmLibrary')
    def test_047___is_libtype_required_by_milestone_and_thread_not_required(self, mock_simple_config,
        mock_get_all_deliverables, mock_get_ip, mock_get_family_for_icmproject,
        mock_get_product):
        '''
        Tests the is_libtype_required_by_milestone_and_thread method when the
        libtype is not required
        '''
        mock_simple = mock_simple_config.return_value
        mock_simple.libtype.return_value = 'libtype'
        mock_get_ip.return_value = IP
        mock_get_family_for_icmproject.return_value = Family
        mock_get_product.return_value = Product
        mock_get_all_deliverables.return_value = [MockDeliverable('rtl'), MockDeliverable('oa')]
        self.assertFalse(self.runner.is_libtype_required_by_milestone_and_thread(mock_simple))

    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_all_deliverables')
    @patch('dmx.abnrlib.flows.releasevariant.IcmLibrary')    
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_048___is_libtype_required_by_milestone_and_thread_is_required(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_simple_config,
                mock_get_all_deliverables, mock_get_ip, mock_get_family_for_icmproject,
                mock_get_product):
        '''
        Tests the is_libtype_required_by_milestone_and_thread method when the
        libtype is required
        '''
        mock_simple = mock_simple_config.return_value
        mock_simple.libtype = 'Deliverable'
        mock_get_ip.return_value = IP
        mock_get_family_for_icmproject.return_value = Family
        mock_get_product.return_value = Product
        mock_get_all_deliverables.return_value = [MockDeliverable('Deliverable')]
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        self.assertTrue(self.runner.is_libtype_required_by_milestone_and_thread(mock_simple))
                


if __name__ == '__main__':
    logging.basicConfig(format="[%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(), level=logging.DEBUG)
    unittest.main()
