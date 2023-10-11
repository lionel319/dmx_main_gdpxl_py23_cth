#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_releasetree.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.releasetree import *
from dmx.ecolib.family import Family
from dmx.ecolib.ip import IP
from dmx.ecolib.product import Product
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icmconfig import IcmConfig
from mock_ecolib import *

class TestReleaseTree(unittest.TestCase):
    '''
    Tests the releasetree abnr plugin
    '''

    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasetree.validate_inputs')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasetree.ConfigFactory.create_from_icm')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.get_group_details')   
    def setUp(self, mock_get_group_details, mock_get_family_for_icmproject, mock_create_from_icm, mock_config_exists, mock_validate_inputs, mock_variant_exists, mock_project_exists):
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_config_exists.return_value = True
        mock_validate_inputs.return_value = None
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant', [IcmLibrary('project', 'variant', 'ipspec', 'dev', '', preview=True, use_db=False)])
        mock_get_group_details.return_value = {'user': [os.getenv('USER')]}
        class Family(object):
            def __init__(self, family):
                self.family = family
                self._icmgroup = 'icmgroup'
            @property                
            def icmgroup(self):
                return self._icmgroup    
        mock_get_family_for_icmproject.return_value = Family('family')

        self.runner = ReleaseTree('project', 'variant', 'config', 'milestone',
                                         'thread', 'description',
                                         'label', False, False, 
                                         [], False, True)

    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.project_exists')
    def test_001___init_project_does_not_exist(self, mock_project_exists):
        '''
        Tests releasetree init when the project does not exist        
        '''
        mock_project_exists.return_value = False

        with self.assertRaises(ReleaseTreeError):
            ReleaseTree('project', 'variant', 'config', 'milestone',
                                         'thread', 'description',
                                         'label', False, False, 
                                         [], False, True)

    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.variant_exists')
    def test_003___init_variant_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests releasetree init when the variant does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(ReleaseTreeError):
            ReleaseTree('project', 'variant', 'config', 'milestone',
                                         'thread', 'description',
                                         'label', False, False, 
                                         [], False, True)

    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_004___init_config_does_not_exist(self, mock_config_exists):
        '''
        Tests the init method when the config does not exist
        '''
        mock_config_exists.return_value = False
        with self.assertRaises(ReleaseTreeError):
            ReleaseTree('project', 'variant', 'config', 'milestone',
                              'thread', 'description', 'label', False,
                              False, [], False, True)


    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.filter_tree')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_all_composite_configs')
    @patch('dmx.abnrlib.flows.releasetree.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_ipspecs_in_tree')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_simple_configs')
    def test_005___run_rel_tree_not_built(self, mock_release_simple_configs, mock_release_ipspecs_in_tree,
                                    mock_composite_config, mock_create_from_icm,
                                    mock_release_all_composite_configs, mock_filter_tree,
                                    ):
        '''
        Tests the run method when building the release tree fails
        '''
        mock_create_from_icm.return_value = mock_composite_config.return_value
        mock_filter_tree.return_value = None
        mock_release_ipspecs_in_tree.return_value = None
        mock_release_simple_configs.return_value = None
        mock_release_all_composite_configs.return_value = None

        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.filter_tree')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_simple_configs')
    @patch('dmx.abnrlib.flows.releasetree.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_ipspecs_in_tree')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_all_composite_configs')
    def test_006___run_rel_tree_built(self, mock_release_all_composite_configs, mock_release_ipspecs_in_tree,
                                mock_composite_config, mock_create_from_icm,
                                mock_release_simple_configs, mock_filter_tree,
                                ):
        '''
        Tests the run method when building the release tree works
        '''
        mock_create_from_icm.return_value = mock_composite_config.return_value
        mock_filter_tree.return_value = None
        mock_release_ipspecs_in_tree.return_value = None
        mock_release_simple_configs.return_value = None
        mock_release_all_composite_configs.return_value = mock_composite_config.return_value

        self.assertEqual(self.runner.run(), 0)

    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.filter_tree')
    @patch('dmx.abnrlib.flows.releasetree.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_ipspecs_in_tree')
    def _test_007___run_rel_exception(self, mock_release_ipspecs_in_tree, mock_composite_config,
                               mock_create_from_icm, mock_filter_tree):
        '''
        Note: Test no longer valid as we no longer release ipspec first
        Tests the run method when there is an exception
        '''
        mock_create_from_icm.return_value = mock_composite_config.return_value
        mock_filter_tree.return_value = None
        mock_release_ipspecs_in_tree.side_effect = ReleaseTreeError('There was an error')

        with self.assertRaises(ReleaseTreeError):
            self.runner.run()

    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    def test_008___find_ipspecs_no_ipspecs(self, mock_composite_config):
        '''
        Tests the find_ipspecs method when there are no ipspecs
        '''
        mock_composite = mock_composite_config.return_value
        mock_composite.search.return_value = []
        self.assertFalse(self.runner.find_ipspecs(mock_composite))

    @patch('dmx.abnrlib.flows.releasetree.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    def test_009___find_ipspecs_with_ipspecs(self, mock_composite_config, mock_simple_config):
        '''
        Tests the find_ipspecs method when there are ipspecs
        '''
        mock_composite = mock_composite_config.return_value
        ipspecs = [mock_simple_config.return_value]
        mock_composite.search.return_value = ipspecs
        self.assertEqual(self.runner.find_ipspecs(mock_composite), ipspecs)

    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.release_simple_configs')
    @patch('dmx.abnrlib.flows.releasetree.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.find_ipspecs')
    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    def test_release_ipspecs_in_tree_release_works(self, mock_compposite_config, mock_find_ipspecs,
                                                   mock_simple_config, mock_release_simple_configs):
        '''
        Tests the release_ipspecs_in_tree method when it works
        '''
        ipspec = mock_simple_config.return_value
        ipspec.is_released.return_value = False
        mock_find_ipspecs.return_value = [ipspec]
        mock_composite = mock_compposite_config.return_value
        mock_release_simple_configs.return_value = None

        self.runner.release_ipspecs_in_tree(mock_composite)
        self.assertEqual(mock_release_simple_configs.call_count, 1)

    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_deliverables')
    @patch('dmx.abnrlib.flows.releasetree.IcmLibrary')
    def test_010___is_libtype_required_by_milestone_and_thread_not_required(self, mock_simple_config,
        mock_get_all_deliverables, mock_get_ip, mock_get_family_for_icmproject, mock_get_product):
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
        self.assertFalse(self.runner.is_libtype_required_by_milestone_and_thread(mock_simple, mock_simple))

    @patch('dmx.ecolib.family.Family.get_product')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_deliverables')
    @patch('dmx.abnrlib.flows.releasetree.IcmLibrary')    
    def test_011___is_libtype_required_by_milestone_and_thread_is_required(self, mock_simple_config,
                mock_get_all_deliverables, mock_get_ip, mock_get_family_for_icmproject, mock_get_product):
        '''
        Tests the is_libtype_required_by_milestone_and_thread method when the
        libtype is required
        '''
        mock_simple = mock_simple_config.return_value
        mock_simple.libtype = 'libtype'
        mock_get_ip.return_value = IP
        mock_get_family_for_icmproject.return_value = Family
        mock_get_product.return_value = Product
        mock_get_all_deliverables.return_value = [MockDeliverable('libtype')]
        self.assertTrue(self.runner.is_libtype_required_by_milestone_and_thread(mock_simple, mock_simple))

    @patch('dmx.abnrlib.flows.releasetree.IcmLibrary')
    def test_012___should_release_config_no_filters(self, mock_simple_config):
        '''
        Tests the should_release_config method when there are no filters
        '''
        self.assertTrue(self.runner.should_release_config(mock_simple_config.return_value, 'ipspec_config'))

    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.is_libtype_required_by_milestone_and_thread')
    @patch('dmx.abnrlib.flows.releasetree.IcmLibrary')
    def test_013___should_release_config_not_in_roadmap(self, mock_simple_config,
                                                  mock_is_libtype_required_by_milestone_and_thread):
        '''
        Tests the should_release_config method when there are no filters
        '''
        mock_simple = mock_simple_config.return_value
        self.runner.required_only = True
        mock_is_libtype_required_by_milestone_and_thread.return_value = False
        self.assertFalse(self.runner.should_release_config(mock_simple, 'ipspec_config'))

    @patch('dmx.abnrlib.flows.releasetree.run_mp')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_014___release_simple_configs_raises_error_on_release_problem(self, mock_config_exists,
                                                                    mock_run_mp):
        '''
        Tests that the release_simple_configs method correctly errors out on release error
        '''
        mock_config_exists.return_value = False
        # Create a simple config tree
        project = 'test_project'
        variant = 'test_variant'
        libtypes = ['rtl', 'oa']
        # At this point all ipspecs should be released
        ipspec = IcmLibrary(project, variant, 'ipspec', 'dev', 'REL_ipspec', preview=True,
                              use_db=False)
        unreleased_simples = []
        mp_results = []
        for libtype in libtypes:
            unreleased_simples.append(IcmLibrary(project, variant, libtype,
                                                  'dev', '', preview=True,
                                                  use_db=False))

            result = {
                'project' : project,
                'variant' : variant,
                'libtype' : libtype,
                'original_config' : 'dev',
                'released_config' : 'REL{0}'.format(libtype),
                'success' : False,
            }
            mp_results.append(result)

        mock_run_mp.return_value = mp_results
        all_simples = [ipspec]
        all_simples.extend(unreleased_simples)

        root_config = IcmConfig('root', project, variant, all_simples, preview=True)

        with self.assertRaises(ReleaseTreeError):
            self.runner.release_simple_configs(root_config, unreleased_simples)

    @patch('dmx.abnrlib.flows.releasetree.run_mp')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_015___release_simple_configs_non_ipspecs(self, mock_config_exists, mock_run_mp):
        '''
        Tests that the release_simple_configs method works with non-ipspec simple configs
        '''
        mock_config_exists.return_value = False
        # Create a simple config tree
        project = 'test_project'
        variant = 'test_variant'
        libtypes = ['rtl', 'oa']
        all_libtypes = ['ipspec']
        all_libtypes.extend(libtypes)
        # At this point all ipspecs should be released
        ipspec = IcmLibrary(project, variant, 'ipspec', 'dev', 'REL_ipspec', preview=True,
                              use_db=False)
        unreleased_simples = []
        mp_results = []
        for libtype in libtypes:
            unreleased_simples.append(IcmLibrary(project, variant, libtype,
                                                  'dev', '', preview=True,
                                                  use_db=False))

            result = {
                'project' : project,
                'variant' : variant,
                'libtype' : libtype,
                'original_config' : 'dev',
                'released_config' : 'REL{0}'.format(libtype),
                'success' : True
            }
            mp_results.append(result)

        mock_run_mp.return_value = mp_results

        all_simples = [ipspec]
        all_simples.extend(unreleased_simples)

        root_config = IcmConfig('root', project, variant, all_simples, preview=True)

        self.runner.release_simple_configs(root_config, unreleased_simples)

        self.assertEqual(len(root_config.configurations), len(all_simples))
        seen_libtypes = []
        for simple_config in root_config.configurations:
            self.assertTrue(simple_config.is_released())
            seen_libtypes.append(simple_config.libtype)

        self.assertEqual(set(all_libtypes), set(seen_libtypes))

    @patch('dmx.abnrlib.flows.releasetree.run_mp')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_016___release_simple_configs_with_ipspecs(self, mock_config_exists, mock_run_mp):
        '''
        Tests that the release_simple_configs method works with ipspec simple configs
        '''
        mock_config_exists.return_value = False
        # Create a simple config tree
        project = 'test_project'
        variant = 'test_variant'
        libtypes = ['rtl', 'oa']
        all_libtypes = ['ipspec']
        all_libtypes.extend(libtypes)
        # At this point all ipspecs should be released
        ipspec = IcmLibrary(project, variant, 'ipspec', 'dev', '', preview=True,
                              use_db=False)
        unreleased_simples = []
        for libtype in libtypes:
            unreleased_simples.append(IcmLibrary(project, variant, libtype,
                                                  'dev', '', preview=True,
                                                  use_db=False))

        mock_run_mp.return_value = [
            {
                'project' : project,
                'variant' : variant,
                'libtype' : 'ipspec',
                'original_config' : 'dev',
                'released_config' : 'REL{0}'.format(ipspec.libtype),
                'success' : True
            }
        ]

        all_simples = [ipspec]
        all_simples.extend(unreleased_simples)

        root_config = IcmConfig('root', project, variant, all_simples, preview=True)

        self.runner.release_simple_configs(root_config, [ipspec])

        self.assertEqual(len(root_config.configurations), len(all_simples))
        seen_libtypes = []
        for simple_config in root_config.configurations:
            if simple_config.libtype == 'ipspec':
                self.assertTrue(simple_config.is_released())

            seen_libtypes.append(simple_config.libtype)

        self.assertEqual(set(all_libtypes), set(seen_libtypes))

    @patch('dmx.abnrlib.flows.releasetree.IcmConfig.search')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_017___release_simple_configs_fails_on_incorrect_ipspec(self, mock_config_exists, mock_search):
        '''
        Tests that the release_simple_configs method raises an error if the wrong ipspec is picked
        '''
        mock_config_exists.return_value = False
        # Create a simple config tree
        project = 'test_project'
        variant = 'test_variant'
        libtypes = ['rtl', 'oa']
        all_libtypes = ['ipspec']
        all_libtypes.extend(libtypes)
        # At this point all ipspecs should be released
        ipspec = IcmLibrary(project, variant, 'ipspec', 'dev', 'REL_ipspec', preview=True,
                              use_db=False)
        unreleased_simples = []
        mp_results = []
        for libtype in libtypes:
            unreleased_simples.append(IcmLibrary(project, variant, libtype,
                                                  'dev', '', preview=True,
                                                  use_db=False))

            result = {
                'project' : project,
                'variant' : variant,
                'libtype' : libtype,
                'original_config' : 'dev',
                'released_config' : 'REL{0}'.format(libtype),
                'success' : True
            }
            mp_results.append(result)

        all_simples = [ipspec]
        all_simples.extend(unreleased_simples)

        root_config = IcmConfig('root', project, variant, all_simples, preview=True)

        mock_search.return_value = [IcmLibrary(project, 'bad_variant', 'ipspec',
                                                 'dev', 'REL_ipspec', preview=True, use_db=False)]

        with self.assertRaises(ReleaseTreeError):
            self.runner.release_simple_configs(root_config, unreleased_simples)

    @patch('dmx.abnrlib.flows.releasetree.IcmConfig')
    @patch('dmx.abnrlib.flows.releasetree.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasetree.run_mp')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_018___release_all_composite_configs_works(self, mock_config_exists, mock_run_mp,
                                                 mock_create_from_icm, mock_composite_config):
        '''
        Tests the release_all_composite_configs method
        '''
        mock_config_exists.return_value = False
        project = 'test_project'

        # Create an unreleased config tree
        # There will be three levels, A, the top level, B, the middle level
        # and C, the bottom level
        # A -> B1, B2
        # B1 -> C1, C2
        # B2 -> C2, C3
        c1 = IcmConfig('c1', project, 'c1', [], preview=True)
        c2 = IcmConfig('c2', project, 'c2', [], preview=True)
        c3 = IcmConfig('c3', project, 'c3', [], preview=True)
        b1 = IcmConfig('b1', project, 'b1', [c1, c2], preview=True)
        b2 = IcmConfig('b2', project, 'b2', [c2, c3], preview=True)
        a = IcmConfig('a', project, 'a', [b1, b2], preview=True)

        # Create a mirror released config tree
        rel_c1 = IcmConfig('RELc1', project, 'c1', [], preview=True)
        rel_c2 = IcmConfig('RELc2', project, 'c2', [], preview=True)
        rel_c3 = IcmConfig('RELc3', project, 'c3', [], preview=True)
        rel_b1 = IcmConfig('RELb1', project, 'b1', [rel_c1, rel_c2], preview=True)
        rel_b2 = IcmConfig('RELb2', project, 'b2', [rel_c2, rel_c3], preview=True)
        rel_a = IcmConfig('RELa', project, 'a', [rel_b1, rel_b2], preview=True)

        # No longer needed
        '''
        def create_from_icm_side_effect(project, variant, config, preview):
            return {
                'c1' : rel_c1,
                'c2' : rel_c2,
                'c3' : rel_c3,
                'b1' : rel_b1,
                'b2' : rel_b2,
                'a' : rel_a
            }.get(variant, None)
        mock_create_from_icm.side_effect = create_from_icm_side_effect
        '''

        def composite_config_side_effect(config, project, variant, sub_configs, preview):
            return {
                'c1' : rel_c1,
                'c2' : rel_c2,
                'c3' : rel_c3,
                'b1' : rel_b1,
                'b2' : rel_b2,
                'a' : rel_a
            }.get(variant, None)

        mock_composite_config.side_effect = composite_config_side_effect            

        def run_mp_side_effect(func, args):
            results = []
            for arg in args:
                results.append(
                    {
                        'project' : arg[0],
                        'variant' : arg[1],
                        'original_config' : arg[2],
                        'success' : True,
                        'released_config' : 'REL{0}'.format(arg[1])
                    }
                )

            return results

        mock_run_mp.side_effect = run_mp_side_effect

        released_root = self.runner.release_all_composite_configs(a)

        self.assertTrue(released_root.is_released(shallow=False))
        # Make sure the structure of the tree is unchanged
        def _has_same_structure(unreleased, released):
            self.assertEqual(len(unreleased.configurations), len(released.configurations))
            unreleased_variants = [x.variant for x in unreleased.configurations]
            released_variants = [x.variant for x in released.configurations]
            self.assertEqual(len(unreleased_variants), len(released_variants))
            self.assertEqual(set(unreleased_variants), set(released_variants))

        for released_config in released_root.flatten_tree():
            if released_config.variant == 'a':
                _has_same_structure(a, released_config)
            elif released_config.variant == 'b1':
                _has_same_structure(b1, released_config)
            elif released_config.variant == 'b2':
                _has_same_structure(b2, released_config)

    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasetree.ReleaseTree.should_release_config')
    def test_019___filter_tree_works(self, mock_should_release_config, mock_config_exists):
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

        def side_effect(simple_config, ipspec_config):
            return simple_config.libtype in required_libtypes

        mock_should_release_config.side_effect = side_effect
        mock_config_exists.return_value = False

        self.runner.filter_tree(root_config)
        for simple_config in all_simple_configs:
            if simple_config.libtype in required_libtypes:
                self.assertIn(simple_config, root_config.configurations)
            else:
                self.assertNotIn(simple_config, root_config.configurations)

    @patch('dmx.abnrlib.flows.releasetree.IcmConfig.save')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_020___build_intermediate_tree_save_fails(self, mock_config_exists, mock_save):
        '''
        Tests the build_intermediate_tree method when saving the tree fails
        '''
        mock_config_exists.return_value = False
        mock_save.return_value = False
        root_config = IcmConfig('config', 'project', 'variant', [],
                                      preview=True)
        self.runner.intermediate = 'intermediate'

        with self.assertRaises(ReleaseTreeError):
            self.runner.build_intermediate_tree(root_config)

    @patch('dmx.abnrlib.flows.releasetree.IcmConfig.save')
    @patch('dmx.abnrlib.flows.releasetree.ICManageCLI.config_exists')
    def test_021___build_intermediate_tree_save_works(self, mock_config_exists, mock_save):
        '''
        Tests the build_intermediate_tree method when saving the tree works
        '''
        mock_config_exists.return_value = False
        mock_save.return_value = True
        project = 'project'
        snap_config = 'snap-test'

        # Build a simple tree. It needs to have some immutable configs that have
        # been edited and some which have not
        # project/variant_a@snap-test -> [project/variant_b@snap-test, project/variant_e@snap-test]
        # project/variant_b@snap-test -> [project/variant_c@REL1.0, project/variant_d@snap-test]
        # project/variant_c@REL1.0 replaced project/variant_c@snap-test so everything
        # above needs to be processed except project/variant_e@snap-test
        snap_var_e = IcmConfig(snap_config, project, 'variant_e', [], preview=True)
        snap_var_e._saved = True
        snap_var_d = IcmConfig(snap_config, project, 'variant_d', [], preview=True)
        snap_var_d._saved = True
        rel_var_c = IcmConfig('REL1.0', project, 'variant_c', [], preview=True)
        rel_var_c._saved = True
        snap_var_b = IcmConfig(snap_config, project, 'variant_b', [rel_var_c, snap_var_d],
                                     preview=True)
        # Make snap b look like it's been modified. We're pretending the REL at variant
        # c has been swapped in below it.
        snap_var_b._saved = False
        snap_var_a = IcmConfig(snap_config, project, 'variant_a', [snap_var_b, snap_var_e],
                                     preview=True)
        snap_var_a._saved = True

        self.runner.intermediate = 'intermediate'

        intermediate_tree = self.runner.build_intermediate_tree(snap_var_a)

        for config in intermediate_tree.flatten_tree():
            if config.variant == 'variant_a':
                self.assertEqual(config.config, self.runner.intermediate)
                self.assertEqual(len(snap_var_a.configurations), len(config.configurations))
            elif config.variant == 'variant_b':
                self.assertEqual(config.config, self.runner.intermediate)
                self.assertEqual(len(config.configurations), len(snap_var_b.configurations))
            elif config.variant == 'variant_c':
                self.assertEqual(config, rel_var_c)
            elif config.variant == 'variant_d':
                self.assertEqual(config, snap_var_d)
            elif config.variant == 'variant_e':
                self.assertEqual(config, snap_var_e)

if __name__ == '__main__':
    unittest.main()
