#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_icm.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
from mock import patch
from datetime import date
import os, sys
import logging
import socket
import datetime
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.loggingutils
LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
import dmx.abnrlib.icm

class TestICManageCLI(unittest.TestCase):

    def setUp(self):
        self.cli = dmx.abnrlib.icm.ICManageCLI()
        self.asadmin = self.cli._as_gdp_admin()


    def test_000___get_icmanage_build_number(self):
        ret = self.cli.get_icmanage_build_number()
        self.assertEqual(ret, 47827)

    def test_001___build_number(self):
        self.assertEqual(self.cli.build_number, 47827)

    def test_002___get_icmanage_info(self):
        ret = self.cli.get_icmanage_info()
        self.assertIn("Peer address", ret)
        self.assertIn("Server root", ret)
        self.assertIn("Server uptime", ret)

    def test_003___check_icmanage_available(self):
        ret = self.cli.check_icmanage_available()

    def test_004___is_user_icmp4_ticket_valid___True(self):
        self.assertTrue(self.cli.is_user_icmp4_ticket_valid("lionelta"))

    def test_004___is_user_icmp4_ticket_valid___False(self):
        user = 'xxxxxxx'
        with self.assertRaisesRegexp(Exception, "User {} does not exist".format(user)):
            self.cli.is_user_icmp4_ticket_valid(user)

    def test_005___check_user_ticket(self):
        ret = self.cli.check_user_ticket()

    def test_006___does_icmp4_user_exist___True(self):
        self.assertTrue(self.cli.does_icmp4_user_exist('lionelta'))
    
    def test_006___does_icmp4_user_exist___False(self):
        self.assertFalse(self.cli.does_icmp4_user_exist('xxxxxxxxxx'))

    def test_007___check_icmadmin_ticket(self):
        pass
    def test_008___login_as_immutable(self):
        pass

    def test_010___workspace_access(self):
        pass

    def test_020___get_variant_name_prefix_for_whr_onwards___1(self):
        self.assertEqual(self.cli.get_variant_name_prefix_for_whr_onwards('abc_lib'), 'abc')

    def test_020___get_variant_name_prefix_for_whr_onwards___2(self):
        self.assertEqual(self.cli.get_variant_name_prefix_for_whr_onwards('abc_def_lib'), 'abc_def')

    def test_020___get_variant_name_prefix_for_whr_onwards___3(self):
        self.assertEqual(self.cli.get_variant_name_prefix_for_whr_onwards('abclib'), 'abclib')

    def test_020___get_variant_name_prefix_for_whr_onwards___4(self):
        self.assertEqual(self.cli.get_variant_name_prefix_for_whr_onwards('abc_lib_def'), 'abc_lib_def')

    def test_022___workspace_exists___True(self):
        self.assertTrue(self.cli.workspace_exists('lionelta_Raton_Mesa_rtmliotest1_44'))

    def test_022___workspace_exists___False(self):
        self.assertFalse(self.cli.workspace_exists('xxxxxxxx'))


    def manual_test_023___add_sync_delete_workspace(self):
        wsdir = '{}.{}.{}'.format(os.getenv("USER"), socket.gethostname(), os.getpid())
        wsroot = '/tmp/{}'.format(wsdir)
        wsname = self.cli.add_workspace('Raton_Mesa', 'liotestfc1', 'dev', dirname=wsroot, ignore_clientname=True)
        self.assertTrue(self.cli.workspace_exists(wsname))

        filepath = os.path.join(wsroot, 'liotestfc1', 'ipspec', 'cell_names.txt')
        self.assertFalse(os.path.isfile(filepath))
        self.cli.sync_workspace(wsname, libtypes=['ipspec'], skeleton=False)
        self.assertTrue(os.path.isfile(filepath))

        self.cli.del_workspace(wsname, preserve=False, force=True)
        self.assertFalse(self.cli.workspace_exists(wsname))

    def test_024___get_workspace_details(self):
        wsname = 'lionelta_Raton_Mesa_rtmliotest1_44'
        ret = self.cli.get_workspace_details(wsname)
        print(ret)
        golden = {u'name': u'lionelta_Raton_Mesa_rtmliotest1_44', u'created': u'2022-03-28T07:00:05.623Z', u'created-by': u'lionelta', u'rootDir': u'/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/./lionelta_Raton_Mesa_rtmliotest1_44', u'modified': u'2022-03-28T07:00:05.623Z', u'host': u'scc919025.sc.intel.com', u'path': u'/intel/Raton_Mesa/rtmliotest1/dev/lionelta_Raton_Mesa_rtmliotest1_44', u'type': u'workspace', u'id': u'W419930'}
        golden = {u'contents-changed': True, u'name': u'lionelta_Raton_Mesa_rtmliotest1_44', u'created': u'2022-03-28T07:00:05.623Z', u'type': u'workspace', u'rootDir': u'/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/./lionelta_Raton_Mesa_rtmliotest1_44', u'modified': u'2022-04-01T15:48:01.350Z', u'host': u'scc919025.sc.intel.com', u'path': u'/intel/Raton_Mesa/rtmliotest1/dev/lionelta_Raton_Mesa_rtmliotest1_44', u'created-by': u'lionelta', u'id': u'W419930'}
        
        self.assertEqual(ret, golden)

    def test_025___get_workspaces___None(self):
        ret = self.cli.get_workspaces('xxx')
        self.assertFalse(ret)

    def test_025___get_workspaces___project(self):
        ret = self.cli.get_workspaces('Raton_Mesa')
        self.assertTrue(ret)

    def test_025___get_workspaces___project_variant(self):
        ret = self.cli.get_workspaces('Raton_Mesa', 'rtmliotest1')
        self.assertTrue(ret)

    def test_025___get_workspaces___project_variant_config(self):
        ret = self.cli.get_workspaces('Raton_Mesa', 'rtmliotest1', 'dev')
        self.assertTrue(ret)

    def test_026___project_exists___no_category_true(self):
        self.assertTrue(self.cli.project_exists('Raton_Mesa'))

    def _test_026___project_exists___with_category_true(self):
        self.assertTrue(self.cli.project_exists('hpsi10'))

    def test_026___project_exists___false(self):
        self.assertFalse(self.cli.project_exists('xxx'))

    def test_027___variant_exists___no_cat_true(self):
        self.assertTrue(self.cli.variant_exists('Raton_Mesa', 'rtmliotest1'))

    def test_027___variant_exists___with_cat_true(self):
        self.assertTrue(self.cli.variant_exists('Raton_Mesa', 'rtmliotest1'))

    def test_027___variant_exists___false_1(self):
        self.assertFalse(self.cli.variant_exists('Raton_Mesa', 'xxx'))

    def test_027___variant_exists___false_2(self):
        self.assertFalse(self.cli.variant_exists('xxx', 'liotest1'))

    def test_028___libtype_exists___no_cat_true(self):
        self.assertTrue(self.cli.libtype_exists('Raton_Mesa', 'rtmliotest1', 'ipspec'))

    def test_028___libtype_exists___with_cat_true(self):
        self.assertTrue(self.cli.libtype_exists('Raton_Mesa', 'rtmliotest1', 'ipspec'))

    def test_028___libtype_exists___false(self):
        self.assertFalse(self.cli.libtype_exists('Raton_Mesa', 'rtmliotest1', 'xxx'))

    def test_029___libtype_defined___True(self):
        self.assertTrue(self.cli.libtype_defined('ipspec'))

    def test_029___libtype_defined___False(self):
        self.assertFalse(self.cli.libtype_defined('xxxxx'))

    def test_030___get_libtype_type(self):
        self.assertEqual(self.cli.get_libtype_type('ipspec'), 'Generic')

    def test_031___config_exists___no_cat_true(self):
        self.assertTrue(self.cli.config_exists('Raton_Mesa', 'rtmliotest1', 'dev'))

    def test_031___config_exists___with_cat_true(self):
        self.assertTrue(self.cli.config_exists('Raton_Mesa', 'rtmliotest1', 'dev'))

    def test_031___config_exists___false(self):
        self.assertFalse(self.cli.config_exists('Raton_Mesa', 'rtmliotest1', 'xxxxxxx'))

    def test_031___config_exists__libtype___true(self):
        self.assertTrue(self.cli.config_exists('Raton_Mesa', 'rtmliotest1', 'snap-fortnr_1', 'ipspec'))

    def test_031___config_exists__libtype___false(self):
        self.assertFalse(self.cli.config_exists('Raton_Mesa', 'rtmliotest1', 'devzz', 'ipsec'))

    def test_032___library_exists___no_cat_true(self):
        self.assertTrue(self.cli.library_exists('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev'))

    def test_032___library_exists___with_cat_true(self):
        self.assertTrue(self.cli.library_exists('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev'))

    def test_032___library_exists___false(self):
        self.assertFalse(self.cli.library_exists('Raton_Mesa', 'rtmliotest1', 'ipspec', 'xxxxxxxx'))

    def test_033___release_exists___no_cat_true(self):
        self.assertTrue(self.cli.release_exists('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev', 'snap-fortnr_1'))

    def test_033___release_exists___with_cat_true(self):
        self.assertTrue(self.cli.release_exists('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev', 'snap-fortnr_1'))

    def test_033___release_exists___false(self):
        self.assertFalse(self.cli.release_exists('Raton_Mesa', 'liotest1', 'ipspec', 'dev', 'xxxxx'))

    def test_034___get_projects___no_cat_true(self):
        self.assertIn('Raton_Mesa', self.cli.get_projects())

    def test_034___get_projects___with_cat_true(self):
        self.assertIn('Raton_Mesa', self.cli.get_projects())

    def test_035___get_variants___no_cat_true(self):
        self.assertIn('rtmliotest1', self.cli.get_variants('Raton_Mesa'))

    def test_035___get_variants___with_cat_true(self):
        self.assertIn('rtmliotest1', self.cli.get_variants('Raton_Mesa'))

    def test_035___get_variants___false(self):
        self.assertFalse(self.cli.get_variants('xxxxxx'))

    def test_036___get_libtypes___no_cat_true(self):
        self.assertIn('ipspec', self.cli.get_libtypes('Raton_Mesa', 'rtmliotest1'))

    def test_036___get_libtypes___with_cat_true(self):
        self.assertIn('ipspec', self.cli.get_libtypes('Raton_Mesa', 'rtmliotest1'))

    def test_036___get_libtypes___false(self):
        self.assertFalse(self.cli.get_libtypes('Raton_Mesa', 'xxxxx'))

    def test_037___get_libraries___no_cat_true(self):
        self.assertIn('dev', self.cli.get_libraries('Raton_Mesa', 'rtmliotest1', 'ipspec'))

    def test_037___get_libraries___with_cat_true(self):
        self.assertIn('dev', self.cli.get_libraries('Raton_Mesa', 'rtmliotest1', 'ipspec'))

    def test_037___get_libraries___false(self):
        self.assertFalse(self.cli.get_libraries('Raton_Mesa', 'rtmliotest1', 'xxxxx'))

    def test_037___get_library_releases___no_cat_true(self):
        self.assertIn('snap-fortnr_1', self.cli.get_library_releases('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev'))

    def test_037___get_library_releases___with_cat_true(self):
        self.assertIn('snap-fortnr_1', self.cli.get_library_releases('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev'))

    def test_037___get_library_releases___false(self):
        self.assertFalse(self.cli.get_library_releases('Raton_Mesa', 'rtmliotest1', 'ipspec', 'xxxxx'))

    def test_038___get_library_details___no_cat(self):
        a = self.cli.get_library_details('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev')
        print(a)
        self.assertEqual(a['name'], 'dev')
        self.assertEqual(a['location'], 'rtmliotest1/ipspec')
        self.assertEqual(a['path'], '/intel/Raton_Mesa/rtmliotest1/ipspec/dev')
        self.assertEqual(a['libtype'], 'ipspec')
        self.assertEqual(a['type'], 'library')


    def test_039___get_clp___oa(self):
        self.assertEqual(self.cli.get_clp('var', 'oa'), 'var/oa/var')

    def test_039___get_clp___oa_sim(self):
        self.assertEqual(self.cli.get_clp('var', 'oa_sim'), 'var/oa_sim/var_sim')

    def test_039___get_clp___others(self):
        self.assertEqual(self.cli.get_clp('var', 'rtl'), 'var/rtl')

    def manual_test_040___test_add_del_variant_libtype_library_release___no_cat(self):
        project = 'Raton_Mesa'
        variant = 'test_lionel'
        desc = 'test 4.5.6'
        libtypes = ['ipspec', 'reldoc']
        library = 'testliblionel'
        release = 'testrellionel'
        self.cli.add_variant(project, variant, desc)
        self.cli.add_libtypes_to_variant(project, variant, libtypes)
        self.cli.add_libraries(project, variant, libtypes, library=library)
        self.cli.add_library_release(project, variant, libtypes[0], release, None, desc, library)

        ### Clean up release
        os.system("gdp delete /intel/Raton_Mesa/test_lionel/ipspec/testliblionel/testrellionel")
        ### Clean up libraries
        os.system("gdp delete /intel/Raton_Mesa/test_lionel/ipspec/testliblionel")
        os.system("gdp delete /intel/Raton_Mesa/test_lionel/reldoc/testliblionel")
        ### Clean up libtypes
        os.system("gdp delete /intel/Raton_Mesa/test_lionel/ipspec")
        os.system("gdp delete /intel/Raton_Mesa/test_lionel/reldoc")
        ### Clean up variant 
        os.system("gdp delete /intel/Raton_Mesa/test_lionel")

    def manual_test_040___test_add_del_variant_libtype_library_release___with_cat(self):
        cat = 'RegressionTest'
        project = 'regtest'
        variant = 'manual_test_040'
        desc = 'manual test 040'
        libtypes = ['ipspec', 'reldoc']
        library = 'testliblionel'
        release = 'testrellionel'
        self.cli.add_variant(project, variant, desc)
        self.cli.add_libtypes_to_variant(project, variant, libtypes)
        self.cli.add_libraries(project, variant, libtypes, library=library)
        self.cli.add_library_release(project, variant, libtypes[0], release, None, desc, library)

        ### Clean up release
        os.system("gdp delete /intel/RegressionTest/regtest/manual_test_040/ipspec/testliblionel/testrellionel")
        ### Clean up libraries
        os.system("gdp delete /intel/RegressionTest/regtest/manual_test_040/ipspec/testliblionel")
        os.system("gdp delete /intel/RegressionTest/regtest/manual_test_040/reldoc/testliblionel")
        ### Clean up libtypes
        os.system("gdp delete /intel/RegressionTest/regtest/manual_test_040/ipspec")
        os.system("gdp delete /intel/RegressionTest/regtest/manual_test_040/reldoc")
        ### Clean up variant 
        os.system("gdp delete /intel/RegressionTest/regtest/manual_test_040")


    def test_041___get_category___no_cat(self):
        self.assertEqual(self.cli.get_category('Raton_Mesa'), '')


    def test_042___update_composite_config___no_config(self):
        self.assertFalse(self.cli.update_config('Raton_Mesa', 'rtmliotest1', 'xxxxxx', {}, 'descriptions'))

    def test_043___decompose_gdp_path___no_cat_project(self):
        ret = self.cli.decompose_gdp_path('/siteA/projA', 'project')
        self.assertEqual(ret, {'project': 'projA', 'type': 'project'})

    def test_043___decompose_gdp_path___with_cat_project(self):
        ret = self.cli.decompose_gdp_path('/siteA/f1/f2/projA', 'project')
        self.assertEqual(ret, {'project': 'projA', 'type': 'project'})

    def test_043___decompose_gdp_path___no_cat_variant(self):
        ret = self.cli.decompose_gdp_path('/siteA/projA/varA', 'variant')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'type': 'variant'})

    def test_043___decompose_gdp_path___with_cat_variant(self):
        ret = self.cli.decompose_gdp_path('/siteA/f1/f2/projA/varA', 'variant')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'type': 'variant'})

    def test_043___decompose_gdp_path___no_cat_config(self):
        ret = self.cli.decompose_gdp_path('/siteA/projA/varA/conA', 'config')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'config': 'conA', 'type': 'config'})

    def test_043___decompose_gdp_path___with_cat_config(self):
        ret = self.cli.decompose_gdp_path('/siteA/f1/f2/projA/varA/conA', 'config')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'config': 'conA', 'type': 'config'})

    def test_043___decompose_gdp_path___no_cat_libtype(self):
        ret = self.cli.decompose_gdp_path('/siteA/projA/varA/ltA', 'libtype')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'libtype': 'ltA', 'type': 'libtype'})

    def test_043___decompose_gdp_path___with_cat_libtype(self):
        ret = self.cli.decompose_gdp_path('/siteA/f1/f2/projA/varA/ltA', 'libtype')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'libtype': 'ltA', 'type': 'libtype'})

    def test_043___decompose_gdp_path___with_cat_library(self):
        ret = self.cli.decompose_gdp_path('/siteA/f1/f2/projA/varA/ltA/lbA', 'library')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'libtype': 'ltA', 'library': 'lbA', 'type': 'library'})

    def test_043___decompose_gdp_path___no_cat_library(self):
        ret = self.cli.decompose_gdp_path('/siteA/projA/varA/ltA/lbA', 'library')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'libtype': 'ltA', 'library': 'lbA', 'type': 'library'})

    def test_043___decompose_gdp_path___with_cat_release(self):
        ret = self.cli.decompose_gdp_path('/siteA/f1/f2/projA/varA/ltA/lbA/relA', 'release')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'libtype': 'ltA', 'library': 'lbA', 'release': 'relA', 'type': 'release'})

    def test_043___decompose_gdp_path___no_cat_release(self):
        ret = self.cli.decompose_gdp_path('/siteA/projA/varA/ltA/lbA/relA', 'release')
        self.assertEqual(ret, {'project': 'projA', 'variant': 'varA', 'libtype': 'ltA', 'library': 'lbA', 'release': 'relA', 'type': 'release'})

    def test_043___decompose_gdp_path___no_pathtype_release(self):
        ret = self.cli.decompose_gdp_path('/intel/Raton_Mesa/rtmliotest1/ipspec/dev/snap-fortnr_1')
        self.assertEqual(ret, {'project': 'Raton_Mesa', 'variant': 'rtmliotest1', 'libtype': 'ipspec', 'library': 'dev', 'release': 'snap-fortnr_1', 'config': '', 'type': 'release'})

    def test_043___decompose_gdp_path___no_pathtype_config(self):
        ret = self.cli.decompose_gdp_path('/intel/Raton_Mesa/rtmliotest1/dev')
        self.assertEqual(ret, {'project': 'Raton_Mesa', 'variant': 'rtmliotest1', 'libtype': '', 'library': '', 'release': '', 'config': 'dev', 'type': 'config'})


    def test_044___determine_include_path_object___config(self):
        self.assertEqual(self.cli.determine_include_path_object('a/b/c'), 'config')

    def test_044___determine_include_path_object___library(self):
        self.assertEqual(self.cli.determine_include_path_object('a/b/c/d'), 'library')

    def test_044___determine_include_path_object___release(self):
        self.assertEqual(self.cli.determine_include_path_object('a/b/c/d/e'), 'release')

    def test_044___determine_include_path_object___error(self):
        with self.assertRaises(Exception):
            self.cli.determine_include_path_object('a/b/c/d/e/f')

    def test_045___get_conflicting_path___no_conflict(self):
        pathlist = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        path = '/f1/f2/a/b/c'
        pathtype = 'config'
        ret = self.cli.get_conflicting_path(path, pathtype, pathlist)
        self.assertFalse(ret)

    def test_045___get_conflicting_path___config_conflict_with_config(self):
        pathlist = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        path = '/site/proA/varC/conX'
        pathtype = 'config'
        ret = self.cli.get_conflicting_path(path, pathtype, pathlist)
        self.assertEqual(ret, '/site/proA/varC/conA')

    def test_045___get_conflicting_path___library_conflict_with_library(self):
        pathlist = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        path = '/site/proA/varA/ltA/lbX'
        pathtype = 'library'
        ret = self.cli.get_conflicting_path(path, pathtype, pathlist)
        self.assertEqual(ret, '/site/proA/varA/ltA/lbA')

    def test_045___get_conflicting_path___library_conflict_with_release(self):
        pathlist = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        path = '/site/proA/varA/ltB/lbX'
        pathtype = 'library'
        ret = self.cli.get_conflicting_path(path, pathtype, pathlist)
        self.assertEqual(ret, '/site/proA/varA/ltB/lbA/rB')

    def test_045___get_conflicting_path___release_conflict_with_library(self):
        pathlist = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        path = '/site/proA/varA/ltA/lbA/rX'
        pathtype = 'release'
        ret = self.cli.get_conflicting_path(path, pathtype, pathlist)
        self.assertEqual(ret, '/site/proA/varA/ltA/lbA')

    def test_045___get_conflicting_path___release_conflict_with_library(self):
        pathlist = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        path = '/site/proA/varA/ltB/lbA/rX'
        pathtype = 'release'
        ret = self.cli.get_conflicting_path(path, pathtype, pathlist)
        self.assertEqual(ret, '/site/proA/varA/ltB/lbA/rB')

    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___replace_config(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'add':['proA/varC/xxx'], 'remove':['proA/varC/conA']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST, 
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/site/proA/varC/conA', '--add', '/intel/proA/varC/xxx:config', '--remove', '/intel/proA/varC/conA:config'])                                                              

    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___replace_library_with_release(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'add':['proA/varA/ltA/lbA/relx']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/site/proA/varA/ltA/lbA', '--add', '/intel/proA/varA/ltA/lbA/relx:release'])
            
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___replace_library_with_library(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'add':['proA/varA/ltA/lbx']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/site/proA/varA/ltA/lbA', '--add', '/intel/proA/varA/ltA/lbx:library'])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___replace_release_with_library(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'add':['proA/varA/ltB/lbX']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/site/proA/varA/ltB/lbA/rB', '--add', '/intel/proA/varA/ltB/lbX:library'])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___replace_release_with_release(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'add':['proA/varA/ltB/lbX/relX']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/site/proA/varA/ltB/lbA/rB', '--add', '/intel/proA/varA/ltB/lbX/relX:release'])                                                                                       
    
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___remove_config(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'remove':['proA/varC/conA']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/intel/proA/varC/conA:config'])
            
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___remove_library(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'remove':['proA/varA/ltA/lbA']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/intel/proA/varA/ltA/lbA:library'])
            
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "config_exists")
    @patch.object(dmx.abnrlib.icm.ICManageCLI, "_get_objects")
    def test_046___update_config___remove_release(self, ma, mb):
        ma.return_value = [
                {'path': '/site/proA/varC/conA',        'type': 'config'},
                {'path': '/site/proA/varA/ltA/lbA',     'type': 'library'},
                {'path': '/site/proA/varA/ltB/lbA/rB',  'type': 'release'}]
        mb.return_value = True
        includes = {'remove':['proA/varA/ltB/lbA/rB']}
        self.cli.preview = True
        self.cli.update_config('regtest', 'vartest1', 'xxx', includes)
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST,
            ['gdp', self.asadmin, 'update', '/intel/regtest/vartest1/xxx', '--force', '--remove', '/intel/proA/varA/ltB/lbA/rB:release'])
            
    def test_047___add_config___True(self):
        self.cli.preview = True
        self.cli.add_config('regtest', 'vartest1', 'xxxxxxxx', 'for regression testing')
        print(self.cli._FOR_REGTEST)
        self.assertEqual(self.cli._FOR_REGTEST, ['gdp', self.asadmin, 'create', 'configuration', '/intel/regtest/vartest1/xxxxxxxx', '--set', "description='for regression testing'"])

    def test_047___add_config___False(self):
        self.cli.preview = True
        self.assertFalse(self.cli.add_config('Raton_Mesa', 'rtmliotest1', 'dev', 'for regression testing'))

    def test_048___del_config___False(self):
        self.cli.preview = True
        self.assertFalse(self.cli.del_config('regtest', 'vartest1', 'xxxxxxxxaa'))
    
    def test_048___del_config___True(self):
        self.cli.preview = True
        self.cli.del_config('Raton_Mesa', 'rtmliotest1', 'for_regtest_bomdelete_1')
        print(self.cli._FOR_REGTEST)
        ans = ['gdp', self.asadmin, 'delete', '/intel/Raton_Mesa/rtmliotest1/for_regtest_bomdelete_1:config']
        self.assertEqual(self.cli._FOR_REGTEST, ans)

    def test_049___get_configs(self):
        ret = self.cli.get_configs("Raton_Mesa", "rtmliotest1")
        self.assertIn('dev', ret)
        self.assertIn('snap-1', ret)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    def test_050___get_next_snap___config_with_existing_snaps(self, m):
        m.return_value = ['snap-99ww000a', 'snap-99ww000b']
        ret = self.cli.get_next_snap('proA', 'varA', 'snap-99ww000')
        self.assertEqual(ret, 'snap-99ww000c')

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    def test_050___get_next_snap___config_without_existing_snaps(self, m):
        m.return_value = []
        ret = self.cli.get_next_snap('proA', 'varA', 'snap-99ww000')
        self.assertEqual(ret, 'snap-99ww000a')
    
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    def test_050___get_next_snap___release_with_existing_snaps(self, m):
        m.return_value = ['snap-99ww000a', 'snap-99ww000b']
        ret = self.cli.get_next_snap('proA', 'varA', 'snap-99ww000', libtype='yyy')
        self.assertEqual(ret, 'snap-99ww000c')

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    def test_050___get_next_snap___release_without_existing_snaps(self, m):
        m.return_value = []
        ret = self.cli.get_next_snap('proA', 'varA', 'snap-99ww000', libtype='yyy')
        self.assertEqual(ret, 'snap-99ww000a')

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    def test_051___get_immutable_configs(self, m):
        m.return_value = ['aaa', 'snap-1', 'REL2', 'ccc']
        ret = self.cli.get_immutable_configs('proA', 'varA')
        self.assertEqual(ret, ['snap-1', 'REL2'])

    def test_052___get_release_changenum___release_not_exists(self):
        with self.assertRaises(Exception):
            self.cli.get_release_changenum('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123a-xxxxxx')
    
    def test_052___get_release_changenum___release_exists(self):
        ret = self.cli.get_release_changenum('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev', 'snap-fortnr_1')
        self.assertEqual(ret, '15')

    def test_053___get_previous_releases_with_matching_content___release_not_exists(self):
        with self.assertRaises(Exception):
            self.cli.get_previous_releases_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'relxxxx')

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    def test_054___get_previous_releases_with_matching_content___match_found(self, ma, mb):
        ma.return_value = '1111'
        mb.return_value = [{"name":"snap-16ww123a","change":"@1111"},{"name":"snap-16ww123b","change":"@1111"},{"name":"snap-16ww123c","change":"@2222"}]
        ret = self.cli.get_previous_releases_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123a')
        self.assertEqual(ret, ['snap-16ww123b'])
        
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    def test_054___get_previous_releases_with_matching_content___match_not_found(self, ma, mb):
        ma.return_value = '2222'
        mb.return_value = [{"name":"snap-16ww123a","change":"@1111"},{"name":"snap-16ww123b","change":"@1111"},{"name":"snap-16ww123c","change":"@2222"}]
        ret = self.cli.get_previous_releases_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123c')
        self.assertEqual(ret, [])
        
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    def test_055___get_previous_snaps_with_matching_content___match_found(self, ma, mb):
        ma.return_value = '1111'
        mb.return_value = [{"name":"snap-16ww123a","change":"@1111"},{"name":"snap-16ww123b","change":"@1111"},{"name":"snap-16ww123c","change":"@2222"}]
        ret = self.cli.get_previous_snaps_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123a')
        self.assertEqual(ret, ['snap-16ww123b'])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    def test_055___get_previous_snaps_with_matching_content___match_not_found(self, ma, mb):
        ma.return_value = '1111'
        mb.return_value = [{"name":"snap-16ww123a","change":"@1111"},{"name":"REL-16ww123b","change":"@1111"},{"name":"snap-16ww123c","change":"@2222"}]
        ret = self.cli.get_previous_snaps_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123a')
        self.assertEqual(ret, [])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    def test_056___get_previous_rels_with_matching_content___match_found(self, ma, mb):
        ma.return_value = '1111'
        mb.return_value = [{"name":"snap-16ww123a","change":"@1111"},{"name":"REL-16ww123b","change":"@1111"},{"name":"snap-16ww123c","change":"@2222"}]
        ret = self.cli.get_previous_rels_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123a')
        self.assertEqual(ret, ['REL-16ww123b'])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    def test_056___get_previous_rels_with_matching_content___match_not_found(self, ma, mb):
        ma.return_value = '1111'
        mb.return_value = [{"name":"snap-16ww123a","change":"@1111"},{"name":"snap-16ww123b","change":"@1111"},{"name":"snap-16ww123c","change":"@2222"}]
        ret = self.cli.get_previous_rels_with_matching_content('regtest', 'vartest1', 'rtl', 'dev', 'snap-16ww123a')
        self.assertEqual(ret, [])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    def test_057___get_next_snap_number___config_found(self, ma, mb):
        mb.return_value = ['snap-3', 'dev', 'snap-2']
        ret = self.cli.get_next_snap_number('p', 'v')
        self.assertEqual(ret, 4)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    def test_057___get_next_snap_number___config_not_found(self, ma, mb):
        mb.return_value = ['dev']
        ret = self.cli.get_next_snap_number('p', 'v')
        self.assertEqual(ret, 1)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    def test_057___get_next_snap_number___release_found(self, ma, mb):
        ma.return_value = ['snap-3', 'dev', 'snap-2']
        ret = self.cli.get_next_snap_number('p', 'v', 'lt', 'lb')
        self.assertEqual(ret, 4)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_library_releases')
    def test_057___get_next_snap_number___release_not_found(self, ma, mb):
        ma.return_value = ['dev']
        ret = self.cli.get_next_snap_number('p', 'v', 'lt', 'lb')
        self.assertEqual(ret, 1)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    def test_058___get_next_tnr_placeholder_number___found(self, ma):
        ma.return_value = ['tnr-placeholder-v-l-3', 'dev', 'tnr-placeholder-v-l-2']
        ret = self.cli.get_next_tnr_placeholder_number('p', 'v', 'l')
        self.assertEqual(ret, 4)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_configs')
    def test_058___get_next_tnr_placeholder_number___not_found(self, ma):
        ma.return_value = ['dev']
        ret = self.cli.get_next_tnr_placeholder_number('p', 'v', 'l')
        self.assertEqual(ret, 1)

    @patch.object(dmx.abnrlib.icm.ICManageCLI, '_ICManageCLI__run_read_command')
    def test_059___get_last_submitted_changelist(self, ma):
        ma.return_value = [0, """Change 12345 on 2020/10/16 by lionelta@lionelta_regtest_vartest1_34 'test'""", '']
        ret = self.cli.get_last_submitted_changelist('//depot/gdpxl/intel/RegressionTest/regtest/vartest1/rtl/dev/...')
        self.assertEqual(ret, 12345)

    @patch.object(dmx.abnrlib.icm, 'run_command')
    def test_060___get_client_detail(self, ma):
        ma.return_value = [0, """
# A Perforce Client Specification.
#
#  Client:      The client name.
#  Update:      The date this specification was last modified.
#  Access:      The date this client was last used in any way.
#  Owner:       The Perforce user name of the user who owns the client
#               workspace. The default is the user who created the
#               client workspace.
#  Host:        If set, restricts access to the named host.
#  Description: A short description of the client (optional).
#  Root:        The base directory of the client workspace.
#  AltRoots:    Up to two alternate client workspace roots.
#  Options:     Client options:
#                      [no]allwrite [no]clobber [no]compress
#                      [un]locked [no]modtime [no]rmdir
#  SubmitOptions:
#                      submitunchanged/submitunchanged+reopen
#                      revertunchanged/revertunchanged+reopen
#                      leaveunchanged/leaveunchanged+reopen
#  LineEnd:     Text file line endings on client: local/unix/mac/win/share.
#  Type:        Type of client: writeable/readonly/graph/partitioned.
#  ServerID:    If set, restricts access to the named server.
#  View:        Lines to map depot files into the client workspace.
#  ChangeView:  Lines to restrict depot files to specific changelists.
#  Stream:      The stream to which this client's view will be dedicated.
#               (Files in stream paths can be submitted only by dedicated
#               stream clients.) When this optional field is set, the
#               View field will be automatically replaced by a stream
#               view as the client spec is saved.
#  StreamAtChange:  A changelist number that sets a back-in-time view of a
#                   stream ( Stream field is required ).
#                   Changes cannot be submitted when this field is set.
#
# Use 'p4 help client' to see more about client views and options.

Client: captain_america_7

Update: 2020/09/29 09:31:22

Access: 2020/10/09 08:32:31

Owner:  spiderman

Description:
        Created by lionelta.
        GDPBase
        GDPItem library cw_lib/reldoc   /intel/Raton_Mesa/cw_lib/reldoc/liotest3  p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/cw_lib/reldoc/liotest3/...

Root:   /nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_Raton_Mesa_cw_lib_7

Options:        noallwrite noclobber nocompress locked nomodtime normdir

SubmitOptions:  submitunchanged

LineEnd:        local

View:
        //depot/gdpxl/intel/Raton_Mesa/cw_lib/reldoc/liotest3/... //lionelta_Raton_Mesa_cw_lib_7/cw_lib/reldoc/...
        
        """, '']
        ret = self.cli.get_client_detail('lionelta_Raton_Mesa_cw_lib_7')
        pprint(ret)
        self.assertEqual(ret, {'client': 'captain_america_7',
 'last_accessed': datetime.date(2020, 10, 9),
 'owner': 'spiderman',
 'root': '/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_Raton_Mesa_cw_lib_7'})


    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_workspaces') 
    def test_061___get_workspace_for_user___found(self, ma):
        ma.return_value = [
            {"name":"ws_1","created-by":"ironman"},
            {"name":"ws_2","created-by":"thor"},
            {"name":"ws_3","created-by":"hawkeye"},
            {"name":"ws_4","created-by":"ironman"},
            {"name":"ws_5","created-by":"ironman"},
        ]
        ret = self.cli.get_workspaces_for_user('thor')
        self.assertEqual(ret, ['ws_2'])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_workspaces') 
    def test_061___get_workspace_for_user___not_found(self, ma):
        ma.return_value = [
            {"name":"ws_1","created-by":"ironman"},
            {"name":"ws_2","created-by":"thor"},
            {"name":"ws_3","created-by":"hawkeye"},
            {"name":"ws_4","created-by":"ironman"},
            {"name":"ws_5","created-by":"ironman"},
        ]
        ret = self.cli.get_workspaces_for_user('batman')
        self.assertEqual(ret, [])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_workspaces') 
    def test_061___get_workspace_for_user___all(self, ma):
        ma.return_value = [
            {"name":"ws_1","created-by":"ironman"},
            {"name":"ws_2","created-by":"thor"},
            {"name":"ws_3","created-by":"hawkeye"},
            {"name":"ws_4","created-by":"ironman"},
            {"name":"ws_5","created-by":"ironman"},
        ]
        ret = self.cli.get_workspaces_for_user()
        self.assertEqual(ret, ['ws_1', 'ws_2', 'ws_3', 'ws_4', 'ws_5'])

    @patch.object(dmx.abnrlib.icm.ICManageCLI, 'get_release_changenum')
    @patch.object(dmx.abnrlib.icm.ICManageCLI, '_ICManageCLI__run_read_command')
    def test_062___get_dict_of_files(self, ma, mb):
        mb.return_value = 'anything'
        stdout = """
//depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev/.lib.info#1 - add change 2481 (text+l)
//depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev/cell_names.txt#2 - edit change 2502 (text+l)
//depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev/liotestfc1.unneeded_deliverables.txt#1 - add change 2501 (text+l)"""
        ma.return_value = [0, stdout, '']
        ret = self.cli.get_dict_of_files('project', 'variant', 'libtype', library='library')
        self.assertEqual(ret, {'project/variant/libtype:': {'changelist': '',                                                                                                                                                                                                                             
                              'directory': '',                                                                                                                                                                                                                              
                              'filename': '',                                                                                                                                                                                                                               
                              'library': 'library',                                                                                                                                                                                                                         
                              'libtype': 'libtype',                                                                                                                                                                                                                         
                              'operation': '',                                                                                                                                                                                                                              
                              'project': 'project',                                                                                                                                                                                                                         
                              'release': None,                                                                                                                                                                                                                              
                              'type': '',                                                                                                                                                                                                                                   
                              'variant': 'variant',                                                                                                                                                                                                                         
                              'version': ''},                                                                                                                                                                                                                               
 'project/variant/libtype:.lib.info': {'changelist': '2481',                                                                                                                                                                                                                
                                       'directory': '//depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev',                                                                                                                                                                   
                                       'filename': '.lib.info',                                                                                                                                                                                                             
                                       'library': 'library',                                                                                                                                                                                                                
                                       'libtype': 'libtype',                                                                                                                                                                                                                
                                       'operation': 'add',                                                                                                                                                                                                                  
                                       'project': 'project',                                                                                                                                                                                                                
                                       'release': None,                                                                                                                                                                                                                     
                                       'type': 'text+l',                                                                                                                                                                                                                    
                                       'variant': 'variant',                                                                                                                                                                                                                
                                       'version': '1'},                                                                                                                                                                                                                     
 'project/variant/libtype:cell_names.txt': {'changelist': '2502',                                                                                                                                                                                                           
                                            'directory': '//depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev',                                                                                                                                                              
                                            'filename': 'cell_names.txt',
                                            'library': 'library',
                                            'libtype': 'libtype',
                                            'operation': 'edit',
                                            'project': 'project',
                                            'release': None,
                                            'type': 'text+l',
                                            'variant': 'variant',
                                            'version': '2'},
 'project/variant/libtype:liotestfc1.unneeded_deliverables.txt': {'changelist': '2501',
                                                                  'directory': '//depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev',
                                                                  'filename': 'liotestfc1.unneeded_deliverables.txt',
                                                                  'library': 'library',
                                                                  'libtype': 'libtype',
                                                                  'operation': 'add',
                                                                  'project': 'project',
                                                                  'release': None,
                                                                  'type': 'text+l',
                                                                  'variant': 'variant',
                                                                  'version': '1'}})


    @patch.object(dmx.abnrlib.icm.ICManageCLI, '_ICManageCLI__run_read_command')
    def test_063___get_library_uri(self, ma):
        path = 'p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/liotestfc1/ipspec/dev/...@1111'
        ma.return_value = [0, '''{"results":[{"uri":"''' + path + '''"}],"success":true}''', '']
        self.assertEqual(self.cli.get_library_uri('Raton_Mesa', 'liotestfc1', 'ipspec', 'dev', relname='snap-2'), path)

    def test_064___branch_library___no_relname(self):
        self.cli._preview = True
        sp = 'Raton_Mesa'
        sv = 'rtmliotest1'
        slt = 'ipspec'
        slb = 'dev'
        tp = 'Raton_Mesa'
        tv = 'rtmliotest2'
        tlt = 'ipspec'
        tlb = 'xxxtest'
        self.cli.branch_library(sp, sv, slt, slb, tlb, tp, tv, tlt)
        print(self.cli._FOR_REGTEST)
        ans = ['gdp', self.asadmin, 'create', 'library', '/intel/Raton_Mesa/rtmliotest2/ipspec/xxxtest', '--from', u'p4://scylicm.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...', '--set', 'location=rtmliotest2/ipspec']
        self.assertEqual(self.cli._FOR_REGTEST, ans)

    def test_064___branch_library___with_relname(self):
        self.cli._preview = True
        sp = 'Raton_Mesa'
        sv = 'rtmliotest1'
        slt = 'ipspec'
        slb = 'dev'
        tp = 'Raton_Mesa'
        tv = 'rtmliotest2'
        tlt = 'ipspec'
        tlb = 'xxxtest'
        self.cli.branch_library(sp, sv, slt, slb, tlb, tp, tv, tlt, relname='snap-fortnr_1')
        print(self.cli._FOR_REGTEST)
        ans = ['gdp', self.asadmin, 'create', 'library', '/intel/Raton_Mesa/rtmliotest2/ipspec/xxxtest', '--from', u'p4://scylicm.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@15', '--set', 'location=rtmliotest2/ipspec']
        self.assertEqual(self.cli._FOR_REGTEST, ans)

    def test_064___branch_library___with_changenum(self):
        self.cli._preview = True
        sp = 'Raton_Mesa'
        sv = 'rtmliotest1'
        slt = 'ipspec'
        slb = 'dev'
        tp = 'Raton_Mesa'
        tv = 'rtmliotest2'
        tlt = 'ipspec'
        tlb = 'xxxtest'
        self.cli.branch_library(sp, sv, slt, slb, tlb, tp, tv, tlt, changenum='11')
        print(self.cli._FOR_REGTEST)
        ans = ['gdp', self.asadmin, 'create', 'library', '/intel/Raton_Mesa/rtmliotest2/ipspec/xxxtest', '--from', 'p4://scylicm.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@11', '--set', 'location=rtmliotest2/ipspec']
        self.assertEqual(self.cli._FOR_REGTEST, ans)

    def test_065___get_library_clp(self):
        ret = self.cli.get_library_clp('Raton_Mesa', 'rtmliotest1', 'ipspec', 'dev')
        self.assertEqual(ret, '{}/{}'.format('rtmliotest1', 'ipspec'))

    def test_066___get_config_details(self):
        ret = self.cli.get_config_details('Raton_Mesa', 'rtmliotest1', 'dev')
        self.assertEqual(ret['name'], 'dev')
        self.assertEqual(ret['path'], '/intel/Raton_Mesa/rtmliotest1/dev')
        self.assertEqual(ret['type'], 'config')

    def test_067___add_config_properties(self):
        props = {'name': 'spider-man', 'really': 'true/false'}
        self.cli._preview = True
        self.cli.add_config_properties('Raton_Mesa', 'rtmliotest1', 'dev', props)
        self.assertEqual(self.cli._FOR_REGTEST, ['gdp', self.asadmin, 'update', '/intel/Raton_Mesa/rtmliotest1/dev:config', '--set', "name=spider-man", '--set', "really=true/false"])

    def test_067___add_workspace_properties(self):
        props = {'name': 'spider-man', 'really': 'true/false'}
        self.cli._preview = True
        self.cli.add_workspace_properties('lionelta_Raton_Mesa_liotestfc1_10', props)
        self.assertEqual(self.cli._FOR_REGTEST, ['gdp', self.asadmin, 'update', '/workspace/lionelta_Raton_Mesa_liotestfc1_10', '--set', "name=spider-man", '--set', "really=true/false"])

    def test_068___get_workspace_name_from_path(self):
        if os.getenv("ARC_SITE") == 'png':
            wsroot = '/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_Raton_Mesa_liotestfc1_35'
            ans = 'lionelta_Raton_Mesa_liotestfc1_35'
        else:
            wsroot = '/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_Raton_Mesa_liotestfc1_5'
            wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
            ans = 'lionelta_Raton_Mesa_rtmliotest1_44'
        cli = dmx.abnrlib.icm.ICManageCLI(site='intel')
        ret = cli.get_workspace_name_from_path(wsroot)
        self.assertEqual(ret, ans)

    def test_069___get_workspace_library_info(self):
        if os.getenv("ARC_SITE") == 'png':
            wsroot = '/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_Raton_Mesa_liotestfc1_35'
        else:
            wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        ret = self.cli.get_workspace_library_info(wsroot)
        self.assertIn({'project': u'Raton_Mesa', 'libtype': u'ipspec', 'variant': u'rtmliotest1', 'library': u'dev', 'type': 'library'}, ret)
        self.assertIn({'project': u'Raton_Mesa', 'libtype': u'reldoc', 'variant': u'rtmliotest1', 'library': u'dev', 'type': 'library'}, ret)

    def test_070___config_exists_under_config_hierarchy___true(self):
        ret = self.cli.config_exists_under_config_hierarchy('REL1.0RTMrevA0__22ww135a', 'Raton_Mesa', 'rtmliotest2', 'snap-1')
        pprint(ret)
        self.assertTrue(ret)

    def test_070___config_exists_under_config_hierarchy___false(self):
        ret = self.cli.config_exists_under_config_hierarchy('REL1.0RTMrevA0__22ww135d', 'Raton_Mesa', 'rtmliotest2', 'snap-1')
        pprint(ret)
        self.assertFalse(ret)

    def test_070___config_exists_under_config_hierarchy___stop_at_immutables(self):
        ret = self.cli.config_exists_under_config_hierarchy('', 'Raton_Mesa', 'rtmliotest2', 'for_regtest_1', stop_at_immutables=True)
        pprint(ret)
        self.assertIn({u'path': u'/intel/Raton_Mesa/rtmliotest1/dev'}, ret)

    def test_071___library_exists_under_config_hierarchy___true(self):
        ret = self.cli.library_exists_under_config_hierarchy('dev', 'Raton_Mesa', 'rtmliotest2', 'dev')
        pprint(ret)
        self.assertTrue(ret)

    def test_071___library_exists_under_config_hierarchy___false(self):
        ret = self.cli.library_exists_under_config_hierarchy('devxxx', 'Raton_Mesa', 'rtmliotest2', 'snap-1')
        pprint(ret)
        self.assertFalse(ret)

    def test_071___library_exists_under_config_hierarchy___stop_at_immutables(self):
        ret = self.cli.library_exists_under_config_hierarchy('dev', 'Raton_Mesa', 'rtmliotest2', 'for_regtest_1', stop_at_immutables=True)
        pprint(ret)
        self.assertIn({"path": '/intel/Raton_Mesa/rtmliotest1/reldoc/dev'}, ret)

    def test_072___release_exists_under_config_hierarchy___true(self):
        ret = self.cli.release_exists_under_config_hierarchy('REL1.0RTMrevA0__22ww135a', 'Raton_Mesa', 'rtmliotest2', 'snap-1')
        pprint(ret)
        self.assertTrue(ret)

    def test_072___release_exists_under_config_hierarchy___false(self):
        ret = self.cli.release_exists_under_config_hierarchy('snap-xxx', 'Raton_Mesa', 'rtmliotest2', 'snap-1')
        pprint(ret)
        self.assertFalse(ret)
        
    def test_072___release_exists_under_config_hierarchy___stop_at_immutables(self):
        ret = self.cli.release_exists_under_config_hierarchy('REL1.0RTMrevA0__22ww135a', 'Raton_Mesa', 'rtmliotest2', 'for_regtest_1', stop_at_immutables=True)
        self.assertTrue(ret)

    def test_075___get_immutable_objects_under_config_hierarchy___None(self):
        ret = self.cli.get_immutable_objects_under_config_hierarchy('Raton_Mesa', 'rtmliotest1', 'dev')
        self.assertFalse(ret)

    def test_075___get_immutable_objects_under_config_hierarchy___1(self):
        ret = self.cli.get_immutable_objects_under_config_hierarchy('Raton_Mesa', 'rtmliotest2', 'snap-1')
        rrr = [x['path'] for x in ret]
        pprint(rrr)
        ans = [u'/intel/Raton_Mesa/rtmliotest2/snap-1',
 u'/intel/Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a',
 u'/intel/Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a',
 u'/intel/Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c',
 u'/intel/Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a',
 u'/intel/Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d']
        for a in ans:
            self.assertIn(a, rrr)

    def _test_075___get_immutable_objects_under_config_hierarchy___many(self):
        ret = self.cli.get_immutable_objects_under_config_hierarchy('Raton_Mesa', 'rtmliotest2', 'devnrel')
        pprint([x['path'] for x in ret])

    def test_076___get_library_from_release___found_1a(self):
        ret = self.cli.get_library_from_release('Raton_Mesa', 'rtmliotest1', 'ipspec', 'snap-fortnr_1')
        print(ret)
        self.assertEqual(ret, 'dev')

    def test_076___get_library_from_release___found_1b(self):
        ret = self.cli.get_library_from_release('Raton_Mesa', 'rtmliotest2', 'ipspec', 'snap-fortnr_1')
        print(ret)
        self.assertEqual(ret, 'dev')

    def test_076___get_library_from_release___not_found(self):
        ret = self.cli.get_library_from_release('Raton_Mesa', 'rtmliotest1', 'ipspec', 'RELxxx')
        print(ret)
        self.assertEqual(ret, '')

    def test_077___get_datetime_info_from_string(self):
        ret = self.cli.get_datetime_info_from_string('2020-09-28T11:01:58.110Z')
        print(ret)
        self.assertEqual(ret, {'seconds': '58', 'month': '09', 'hours': '11', 'year': '2020', 'minutes': '01', 'day': '28'})

    def test_078___get_clr_last_modified_data___library(self):
        ret = self.cli.get_clr_last_modified_data('Raton_Mesa', 'rtmliotest1', 'dev', libtype='ipspec')
        print(ret)
        ans = {'seconds': u'01', 'month': u'04', 'hours': u'15', 'year': u'2022', 'minutes': u'48', 'day': u'01'}
        self.assertEqual(ret, ans)

    def test_078___get_clr_last_modified_data___release(self):
        ret = self.cli.get_clr_last_modified_data('Raton_Mesa', 'rtmliotest1', 'snap-fortnr_1', libtype='ipspec')
        print(ret)
        ans = {'seconds': u'07', 'month': u'04', 'hours': u'15', 'year': u'2022', 'minutes': u'48', 'day': u'01'}
        self.assertEqual(ret, ans)

    def test_078___get_clr_last_modified_data___config(self):
        ret = self.cli.get_clr_last_modified_data('Raton_Mesa', 'rtmliotest1', 'snap-1' )
        print(ret)
        ans = {'seconds': u'14', 'month': u'03', 'hours': u'09', 'year': u'2022', 'minutes': u'03', 'day': u'25'}
        self.assertEqual(ret, ans)


if __name__ == '__main__':
    unittest.main()
