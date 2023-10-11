#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_latestconfig.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.latestconfig import *

class TestLatestConfig(unittest.TestCase):
    '''
    Tests the abnr latest plugin
    '''

    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def setUp(self, mock_variant_exists):
        mock_variant_exists.return_value = True
        self.runner = LatestConfig('project', 'variant', 'config')

    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_000___init_variant_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests init when the project exists but the variant does not
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(LatestConfigError):
            LatestConfig('project', 'variant', 'config')

    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_001___init_project_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests init when the project does not exist
        '''
        mock_project_exists.return_value = False
        mock_variant_exists.return_value = False

        with self.assertRaises(LatestConfigError):
            LatestConfig('project', 'variant', 'config')



    def test_010___get_rel_config_info___true_with_label(self):
        ''' '''
        config = 'REL3.0ND5revA--TESTING__15ww123b'
        ret = self.runner.get_rel_config_info(config)
        self.assertEqual(ret, {
            'label': 'TESTING',
            'milestone': '3.0',
            'suffix': 'b',
            'thread': 'ND5revA',
            'wwd': '123',
            'yy': '15'})

    def test_010___get_rel_config_info___true_without_label(self):
        ''' '''
        config = 'REL3.0ND5revA__15ww123b'
        ret = self.runner.get_rel_config_info(config)
        self.assertEqual(ret, {
            'label': None,
            'milestone': '3.0',
            'suffix': 'b',
            'thread': 'ND5revA',
            'wwd': '123',
            'yy': '15'})

    def test_010___get_rel_config_info___true_with_2digit_wwd(self):
        ''' '''
        config = 'REL3.0ND5revA__15ww23b'
        ret = self.runner.get_rel_config_info(config)
        self.assertEqual(ret, {})

    def test_010___get_rel_config_info___false(self):
        ''' '''
        config = 'REL--TESTING'
        ret = self.runner.get_rel_config_info(config)
        self.assertEqual(ret, {})



    def test_020___get_thread_of_integration_from_rel_config___true_with_label(self):
        config = 'REL3.0ND5revA--TESTING__15ww123b'
        ret = self.runner.get_thread_of_integration_from_rel_config(config)
        self.assertEqual(ret, 'REL3.0ND5revA--TESTING')

    def test_020___get_thread_of_integration_from_rel_config___true_without_label(self):
        config = 'REL3.0ND5revA__15ww123b'
        ret = self.runner.get_thread_of_integration_from_rel_config(config)
        self.assertEqual(ret, 'REL3.0ND5revA')

    def test_020___get_thread_of_integration_from_rel_config___true_with_2digit_wwd(self):
        config = 'REL3.0ND5revA__15ww23b'
        ret = self.runner.get_thread_of_integration_from_rel_config(config)
        self.assertEqual(ret, '')

    def test_020___get_thread_of_integration_from_rel_config___false(self):
        config = 'REL--TESTING__15ww123'
        ret = self.runner.get_thread_of_integration_from_rel_config(config)
        self.assertEqual(ret, '')



    def test_030___sort_rel_configs___true(self):
        configs = ['non-REL-config', 'REL4.5ND1revC--test__16ww444b', 'snap-config-frozen', 'REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww432b']
        ret = self.runner.sort_rel_configs(configs)
        self.assertEqual(ret, ['REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww432b', 'REL4.5ND1revC--test__16ww444b'])



    def test_040___separate_rel_configlist_by_thread_of_integration(self):
        configs = ['non-REL-config', 'REL4.5ND1revC--test__16ww444b', 'snap-config-frozen', 'REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww432b',
            'REL4.5ND1revC__16ww123a', 'REL4.5ND1revC__16ww446c']
        ret = self.runner.separate_rel_configlist_by_thread_of_integration(configs)
        self.assertEqual(ret, {
            '': ['non-REL-config', 'snap-config-frozen'],
            'REL1.0ND5revA': ['REL1.0ND5revA__16ww123a'],
            'REL4.5ND1revC--test': ['REL4.5ND1revC--test__16ww444b',
                                   'REL4.5ND1revC--test__16ww432b'],
            'REL4.5ND1revC': ['REL4.5ND1revC__16ww123a', 'REL4.5ND1revC__16ww446c'] 
        })



    @patch.object(ICManageCLI, 'get_configs')
    def test_050___get_regex_matching_configs___true(self, mock_get_configs):
        rel_configs = ['REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww444b']
        snap_configs = ['snap-lay__17ww231a']
        nonrel_configs = ['non-REL-config', 'snap-config-frozen']
        mock_get_configs.return_value = nonrel_configs + snap_configs + rel_configs
        ret_rel_configs, ret_snap_configs, ret_nonrel_configs = self.runner.get_regex_matching_configs('project', 'variant', None, 'REL')
        self.assertEqual(ret_rel_configs, rel_configs)
        self.assertEqual(ret_snap_configs, [])
        self.assertEqual(ret_nonrel_configs, ['non-REL-config'])

    @patch.object(ICManageCLI, 'get_configs')
    def test_050___get_regex_matching_configs___true_2(self, mock_get_configs):
        rel_configs = ['REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww444b']
        snap_configs = ['snap-lay__17ww231a']
        nonrel_configs = ['non-REL-config', 'snap-config-frozen']
        mock_get_configs.return_value = nonrel_configs + snap_configs + rel_configs
        ret_rel_configs, ret_snap_configs, ret_nonrel_configs = self.runner.get_regex_matching_configs('project', 'variant', None, '^.+REL')
        self.assertEqual(ret_rel_configs, [])
        self.assertEqual(ret_snap_configs, [])
        self.assertEqual(ret_nonrel_configs, ['non-REL-config'])

    @patch.object(ICManageCLI, 'get_configs')
    def test_050___get_regex_matching_configs___true_3(self, mock_get_configs):
        rel_configs = ['REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww444b']
        snap_configs = ['snap-lay__17ww231a']
        nonrel_configs = ['non-REL-config', 'snap-config-frozen']
        mock_get_configs.return_value = nonrel_configs + snap_configs + rel_configs
        ret_rel_configs, ret_snap_configs, ret_nonrel_configs = self.runner.get_regex_matching_configs('project', 'variant', None, 'snap')
        self.assertEqual(ret_rel_configs, [])
        self.assertEqual(ret_snap_configs, snap_configs)
        self.assertEqual(ret_nonrel_configs, ['snap-config-frozen'])

    @patch.object(ICManageCLI, 'get_configs')
    def test_050___get_regex_matching_configs___true_4(self, mock_get_configs):
        rel_configs = ['REL1.0ND5revA__16ww123a', 'REL4.5ND1revC--test__16ww444b']
        snap_configs = ['snap-lay__17ww231a']
        nonrel_configs = ['non-REL-config', 'snap-config-frozen']
        mock_get_configs.return_value = nonrel_configs + snap_configs + rel_configs
        ret_rel_configs, ret_snap_configs, ret_nonrel_configs = self.runner.get_regex_matching_configs('project', 'variant', None, 'REL|snap')
        self.assertEqual(ret_rel_configs, rel_configs)
        self.assertEqual(ret_snap_configs, snap_configs)
        self.assertEqual(ret_nonrel_configs, ['non-REL-config', 'snap-config-frozen'])
    

    def test_100___get_pedantic_configs_from_configlist(self):
        configlist = [
            'bREL_3.0_SECTOR',
            'bREL4.5ND5revA-RTL-15ww391a__MPU_15ww391a_branch__dev',
            'bREL4.5ND5revA-RTL-15ww391a__HPS-R__dev',
            'bREL4.0ND5revA-SECTOR-15ww314a__branch_hseam_lib_RC1.0ND1revA__dev',
            'bREL4.0ND5revA-RTL-15ww351b__HPS-R_branch__dev',
            'bREL4.0ND5revA-RTL-15ww351b__HPS-R__dev',
            'bREL4.0ND5revA-RTL-15ww351b__HPS-R2__dev',
            'bREL4.0ND5revA-RTL-15ww322a__TMA2__dev',
            'bREL2.0ND5revA-14ww512a__hjen_REL2.0ND5revA-14ww512a_14ww514__dev',
            'bREL1.5ND5revA-UID-CLK-14ww363a__bblanc_trial__dev',
            'bREL1.5ND5revA-SECTOR-14ww335a__bblanc_trial__dev',
            'bREL1.5ND5revA-SECTOR-14ww335a__bREL1.5ND5revA-SECTOR-14ww335a-bblanc_trial-dev__dev',
        ]
        pedanticlist = [
            'bREL4.5ND5revA-RTL-15ww391a__MPU_15ww391a_branch__dev',
            'bREL4.5ND5revA-RTL-15ww391a__HPS-R__dev',
            'bREL4.0ND5revA-RTL-15ww351b__HPS-R_branch__dev',
            'bREL4.0ND5revA-RTL-15ww351b__HPS-R__dev',
            'bREL4.0ND5revA-RTL-15ww351b__HPS-R2__dev',
            'bREL4.0ND5revA-RTL-15ww322a__TMA2__dev',
            'bREL1.5ND5revA-UID-CLK-14ww363a__bblanc_trial__dev',
            'bREL1.5ND5revA-SECTOR-14ww335a__bblanc_trial__dev',
        ]
        retlist = self.runner.get_pedantic_configs_from_configlist(configlist)
        self.assertEqual(retlist, pedanticlist)



    def test_200___sort_configlist_based_on_timestamp(self):
        configlist = ['REL2.0ND5revA--SECTOR__14ww513a', 
            'REL3.0ND5revA--SECTOR__15ww141a',
            'bREL---hahaha',
            'REL4.0ND5revA--RTL__15ww392a',
            'REL4.5ND5revA--RTL__15ww442a',
            'REL3.0ND5revA__15ww141a',
            'REL4.0ND5revA--SECTOR__15ww244b',
            'bREL---hohoho',
            'REL4.5ND5revA--PHYS__15ww483a']
        answer = ['REL4.5ND5revA--PHYS__15ww483a', 
            'REL4.5ND5revA--RTL__15ww442a', 
            'REL4.0ND5revA--RTL__15ww392a', 
            'REL4.0ND5revA--SECTOR__15ww244b', 
            'REL3.0ND5revA__15ww141a', 
            'REL3.0ND5revA--SECTOR__15ww141a', 
            'REL2.0ND5revA--SECTOR__14ww513a', 
            'bREL---hahaha', 
            'bREL---hohoho']

        print(self.runner.sort_configlist_based_on_timestamp(configlist))
        retlist = self.runner.sort_configlist_based_on_timestamp(configlist)
        self.assertEqual(retlist, answer)


    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_300___no_limit_option_non_naming_scheme(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', 'snap-sdm_RC3.0_WIP2')
        mock_get_configs.return_value = [
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17WW231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17WW235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17WW233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17WW225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17WW223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17WW223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        answer = [
            'snap-sdm_RC3.0_WIP2__17WW235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17WW233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17WW231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17WW225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17WW223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17WW223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer)


    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_300___with_limit_option_non_naming_scheme(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', 'snap-sdm_RC3.0_WIP2', limit=1)
        mock_get_configs.return_value = [
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17WW231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17WW235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17WW233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17WW225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17WW223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17WW223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        answer = [
            'snap-sdm_RC3.0_WIP2__17WW235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17WW233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17WW231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17WW225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17WW223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17WW223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer[0:1])


    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_301___with_limit_option_different_milestone(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', 'REL*', limit=1)
        mock_get_configs.return_value = [
            'REL1.0RNRrevA0__19ww521a',
            'REL0.8RNRrevA0__19ww521a',
            'REL0.5RNRrevA0__19ww314a',
            'REL0.3RNRrevA0__19ww175a',
        ]
        answer = [
            'REL1.0RNRrevA0__19ww521a',
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer[0:1])


    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_400___without_pedantic_option(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', 'snap-sdm_RC3.0_WIP2', pedantic=False)
        mock_get_configs.return_value = [
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17ww231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17ww235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17ww233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17ww225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17ww223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17ww223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        answer = [
            'snap-sdm_RC3.0_WIP2__17ww235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17WW223a',
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer)


    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_400___with_pedantic_option(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', 'snap-sdm_RC3.0_WIP2', pedantic=True)
        mock_get_configs.return_value = [
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17ww231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17ww235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17ww233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17ww225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17ww223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17ww223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        answer = [
            'snap-sdm_RC3.0_WIP2__17ww235a', 
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer)



    ### test_450_*  are all for introduction of new WIP naming scheme
    ### http://pg-rdjira:8080/browse/DI-872
    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_450___with_pedantic_option(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', '*', pedantic=True)
        mock_get_configs.return_value = [
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17ww231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17ww235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17ww233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17ww225a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17ww223d',
            'a1-b2_c3__13ww345a',
            '-a1-b2_c3__12ww345a',
            'a1-b2_c3__12ww345a',
            '1-b2_c3__12ww345a',
            'a1-b2_c3__14ww345a',
            '_a1-b2_c3__12ww345a',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17ww223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        answer = [
            'snap-sdm_RC3.0_WIP2__17ww235a', 
            'a1-b2_c3__14ww345a',
            'a1-b2_c3__13ww345a',
            'a1-b2_c3__12ww345a',
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer)
    
    @patch.object(ICManageCLI, 'get_configs')
    @patch('dmx.abnrlib.flows.latestconfig.ICManageCLI.variant_exists')
    def test_450___without_pedantic_option(self, mock_variant_exists, mock_get_configs):
        runner = LatestConfig('project', 'variant', '*', pedantic=False)
        mock_get_configs.return_value = [
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17ww231a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17ww235a',
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17ww233a',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17ww225a',
            'a1-b2_c3__13ww345a',
            '-a1-b2_c3__12ww345a',
            'a1-b2_c3__12ww345a',
            '1-b2_c3__12ww345a',
            'a1-b2_c3__14ww345a',
            '_a1-b2_c3__12ww345a',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17ww223d',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17ww223b',
            'snap-sdm_RC3.0_WIP2__17WW223a'
        ]
        answer = [
            'snap-sdm_RC3.0_WIP2__17ww235a', 
            'snap-sdm_RC3.0_WIP2__17WW234a',
            'snap-sdm_RC3.0_WIP2__17WW233b',
            'snap-sdm_RC3.0_WIP2__17WW232b',
            'snap-sdm_RC3.0_WIP2__17WW232a',
            'snap-sdm_RC3.0_WIP2__17WW227b',
            'snap-sdm_RC3.0_WIP2__17WW227a',
            'snap-sdm_RC3.0_WIP2__17WW225b',
            'snap-sdm_RC3.0_WIP2__17WW224a',
            'snap-sdm_RC3.0_WIP2__17WW223c',
            'snap-sdm_RC3.0_WIP2__17WW223a',
            'a1-b2_c3__14ww345a',
            'a1-b2_c3__13ww345a',
            'a1-b2_c3__12ww345a',
            '_a1-b2_c3__12ww345a',
            '1-b2_c3__12ww345a',
            '-a1-b2_c3__12ww345a',
        ]
        runner.run()
        self.assertEqual(runner.final_retlist, answer)



if __name__ == '__main__':
    unittest.main()
