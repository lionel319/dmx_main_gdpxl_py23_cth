#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr replacetree plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_releasedeliverables.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.releasedeliverables import ReleaseDeliverables, ReleaseDeliverablesError
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icmconfig import IcmConfig

class TestReleaseDeliverables(unittest.TestCase):
    '''
    Tests the releasedeliverables abnr plugin
    '''

    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.libtype_defined')
    @patch('dmx.abnrlib.flows.releasedeliverables.validate_inputs')
    @patch('dmx.abnrlib.flows.releasedeliverables.ConfigFactory.create_from_icm')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.get_group_details')   
    def setUp(self, mock_get_group_details, mock_get_family_for_icmproject, mock_create_from_icm, mock_validate_inputs, mock_libtype_defined, mock_config_exists, mock_variant_exists, mock_project_exists):
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_create_from_icm.return_value = None
        mock_validate_inputs.return_value = None
        mock_get_group_details.return_value = {'user': [os.getenv('USER')]}
        class Family(object):
            def __init__(self, family):
                self.family = family
                self._icmgroup = 'icmgroup'
            @property                
            def icmgroup(self):
                return self._icmgroup    
        mock_get_family_for_icmproject.return_value = Family('family')
        self.runner = ReleaseDeliverables('project', 'variant', 'config', ['libtype'], 'milestone',
                                              'thread', '', '', False,
                                              preview=True)

    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.project_exists')
    def test_001___init_project_does_not_exist(self, mock_project_exists):
        '''
        Tests releasedeliverables init when the project does not exist        
        '''
        mock_project_exists.return_value = False

        with self.assertRaises(ReleaseDeliverablesError):
            ReleaseDeliverables('project', 'variant', 'config', 'milestone',
                                    'thread', '', '', False,
                                    preview=True)

    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.variant_exists')
    def test_002___init_variant_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests releasedeliverables init when the variant does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(ReleaseDeliverablesError):
             ReleaseDeliverables('project', 'variant', 'config', ['libtype'], 'milestone',
                                    'thread', '', '', False,
                                   preview=True)

    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.config_exists')
    def test_003___init_config_does_not_exist(self, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests releasedeliverables init when the config does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = False

        with self.assertRaises(ReleaseDeliverablesError):
             ReleaseDeliverables('project', 'variant', 'config', 'milestone',
                                    'thread', '', '', False,
                                   preview=True)

    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.ICManageCLI.libtype_defined')
    def test_004___init_config_does_not_exist(self, mock_libtype_defined, mock_config_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests releasedeliverables init when the libtype does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = False

        with self.assertRaises(ReleaseDeliverablesError):
             ReleaseDeliverables('project', 'variant', 'config', ['libtype'], 'milestone',
                                    'thread', '', '', False,
                                   preview=True)

    @patch('dmx.abnrlib.flows.releasedeliverables.ReleaseDeliverables.release_configs')
    @patch('dmx.abnrlib.flows.releasedeliverables.ReleaseDeliverables.filter_configs')
    @patch.object(ICManageCLI, 'config_exists')
    def test_005___release_all_simple_configs(self, mock_config_exists, mock_filter_configs,
                                        mock_release_configs):
        '''
        Tests the release_all_simple_configs method
        '''
        mock_config_exists.return_value = False
        def side_effect(unreleased_configs):
            return unreleased_configs

        mock_filter_configs.side_effect = side_effect

        # Build a simple config tree for testing
        project = 'project'
        first_ipspec = IcmLibrary(project, 'variant_one', 'ipspec', 'dev','REL1.0', preview=True, use_db=False)
        first_rtl = IcmLibrary(project, 'variant_one', 'rtl', 'dev','', preview=True, use_db=False)
        first_comp = IcmConfig('dev', project, 'variant_one', [first_ipspec, first_rtl],preview=True)
        second_ipspec = IcmLibrary(project, 'variant_two', 'ipspec', 'dev','REL1.0', preview=True, use_db=False)
        second_oa = IcmLibrary(project, 'variant_two', 'oa', 'dev','', preview=True, use_db=False)
        second_comp = IcmConfig('dev', project, 'variant_two', [second_ipspec, second_oa],preview=True)
        third_ipspec = IcmLibrary(project, 'variant_three', 'ipspec', 'dev','REL1.0', preview=True, use_db=False)
        third_rtl = IcmLibrary(project, 'variant_three', 'rtl', 'dev','REL1.0', preview=True, use_db=False)
        top_comp = IcmConfig('dev', project, 'variant_three', [third_ipspec, third_rtl,first_comp, second_comp],preview=True)

        first_rel_rtl = first_rtl.clone('REL1.0')
        second_rel_oa = second_oa.clone('REL1.0')
        self.runner.source_config = top_comp

        mock_release_configs.return_value = [first_rel_rtl, second_rel_oa]

        released_configs = self.runner.release_all_simple_configs()

        for simple_config in released_configs:
            self.assertTrue(simple_config.is_released())
                 
    @patch('dmx.abnrlib.flows.releasedeliverables.run_mp')
    def test_006___release_configs_release_fails(self, mock_run_mp):
        '''
        Tests the release_configs method when a release attempt fails
        '''
        first_ipspec = IcmLibrary('project', 'variant_one', 'ipspec', 'dev',
                                    '', preview=True, use_db=False)
        second_ipspec = IcmLibrary('project', 'variant_two', 'ipspec', 'dev',
                                     '', preview=True, use_db=False)
        first_comp = IcmConfig('dev', 'project', 'variant_one', [first_ipspec],
                                     preview=True)
        second_comp = IcmConfig('dev', 'project', 'variant_two', [second_ipspec],
                                      preview=True)
        
        mock_run_mp.return_value = [
            {
                'success' : False, 'project' : first_ipspec.project,
                'variant' : first_ipspec.variant, 'libtype' : first_ipspec.libtype,
                'original_config' : first_ipspec.name
            },
            {
                'success' : False, 'project' : second_ipspec.project,
                'variant' : second_ipspec.variant, 'libtype' : second_ipspec.libtype,
                'original_config' : second_ipspec.name
            }
        ]

        with self.assertRaises(ReleaseDeliverablesError):
            self.runner.release_configs([first_ipspec, second_ipspec])                 
             
    @patch('dmx.abnrlib.flows.releasedeliverables.ConfigFactory.create_from_icm')
    @patch.object(ICManageCLI, 'config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverables.run_mp')
    def test_007___release_configs_release_works(self, mock_run_mp, mock_config_exists,
                                           mock_create_from_icm):
        mock_config_exists.return_value = False
        first_ipspec = IcmLibrary('project', 'variant_one', 'ipspec', 'dev',
                                    '', preview=True, use_db=False)
        second_ipspec = IcmLibrary('project', 'variant_two', 'ipspec', 'dev',
                                     '', preview=True, use_db=False)
        first_rel_ipspec = first_ipspec.clone('REL1.0')
        second_rel_ipspec = second_ipspec.clone('REL1.0')
        first_comp = IcmConfig('dev', 'project', 'variant_one', [first_ipspec],
                                     preview=True)
        second_comp = IcmConfig('dev', 'project', 'variant_two', [second_ipspec],
                                      preview=True)

        mock_run_mp.return_value = [
            {
                'success' : True, 'project' : first_ipspec.project,
                'variant' : first_ipspec.variant, 'libtype' : first_ipspec.libtype,
                'original_config' : first_ipspec.name,
                'released_config' : 'REL1.0',
            },
            {
                'success' : True, 'project' : second_ipspec.project,
                'variant' : second_ipspec.variant, 'libtype' : second_ipspec.libtype,
                'original_config' : second_ipspec.name,
                'released_config' : 'REL1.0',
            }
        ]

        def side_effect(project, variant, config, libtype, preview):
            if variant == first_rel_ipspec.variant:
                return first_rel_ipspec
            else:
                return second_rel_ipspec

        mock_create_from_icm.side_effect = side_effect

        released_configs = self.runner.release_configs([first_ipspec, second_ipspec])
        self.assertIn(first_rel_ipspec, released_configs)
        self.assertIn(second_rel_ipspec, released_configs)
        self.assertEqual(len(released_configs), 2)             

    def test_008___filter_configs(self):
        '''
        Tests the filter_configs method
        '''
        all_libtypes = ['rtl', 'oa', 'ipspec']
        all_configs = []
        libtype_filter = ['rtl']

        for libtype in all_libtypes:
            all_configs.append(IcmLibrary('project', 'variant', libtype, 'dev',
                                            '', preview=True, use_db=False))

        self.runner.libtypes = libtype_filter
        filtered_configs = self.runner.filter_configs(all_configs)

        self.assertEqual(len(filtered_configs), 1)
        self.assertEqual(filtered_configs[0].libtype, libtype_filter[0])

if __name__ == '__main__':
    unittest.main()
