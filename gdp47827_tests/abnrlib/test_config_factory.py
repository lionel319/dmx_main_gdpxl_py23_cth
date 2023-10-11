#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_config_factory.py $
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
import dmx.abnrlib.icmlibrary
import dmx.abnrlib.icmconfig
import dmx.abnrlib.config_factory

class TestConfigFactory(unittest.TestCase):

    
    def setUp(self):
        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest2'
        self.config = 'for_regtest_1'
        self.libtype = 'ipspec'
        self.library = 'dev'
        self.release = 'REL1.0RTMrevA0__22ww135a'

        self.cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        self.cf2 = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.config, preview=True)
       

    def test_000___create_from_icm___library(self):
        ret = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.library, libtype=self.libtype)
        a = ret._defprops
        pprint(a)
        self.assertEqual(a['change'], '@now')
        self.assertEqual(a['libtype'], 'ipspec')
        self.assertEqual(a['location'], 'rtmliotest2/ipspec')
        self.assertEqual(a['name'], 'dev')
        self.assertEqual(a['path'], '/intel/Raton_Mesa/rtmliotest2/ipspec/dev')
        self.assertEqual(a['type'], 'library')

    def test_000___create_from_icm___release(self):
        ret = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.release, libtype=self.libtype)
        a = ret._defprops
        pprint(a)
        self.assertEqual(a['change'], '@87')
        self.assertEqual(a['libtype'], 'ipspec')
        self.assertEqual(a['path'], '/intel/Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135a')
        self.assertEqual(a['name'], self.release)
        self.assertEqual(a['type'], 'release')

    def test_000___create_from_icm___config(self):
        self.assertEqual(self.cf._defprops['name'], self.release)

    def test_001___report___nosimple_nohier_nolibrary(self):
        ret = self.cf.report(show_simple=False, show_libraries=False, nohier=True)
        print('\n{}'.format(ret))
        print(repr(ret))
        self.assertEqual(ret, 'Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a\n')

    def test_002___report___nosimple_hier_nolibrary(self):
        ret = self.cf.report(show_simple=False, show_libraries=False, nohier=False)
        print('\n{}'.format(ret))
        print(repr(ret))
        self.assertEqual(ret, 'Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a\n')

    def test_003___report___simple_hier_nolibrary(self):
        ret = self.cf.report(show_simple=True, show_libraries=False, nohier=False)
        print('\n{}'.format(ret))
        print(repr(ret))
        ans = 'Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n'
        self.assertEqual(ret, ans)

    def test_004___report___simple_hier_library(self):
        ret = self.cf.report(show_simple=True, show_libraries=True, nohier=False)
        print('\n{}'.format(ret))
        print(repr(ret))
        ans = 'Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c dev@REL1.0RTMrevA0__22ww135c[@87]\n\tRaton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a dev@REL1.0RTMrevA0__22ww135a[@88]\n\tRaton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a dev@REL1.0RTMrevA0__22ww135a[@89]\n\t\tRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d dev@REL1.0RTMrevA0__22ww135d[@13]\n'
        self.assertEqual(ret, ans)

    def test_005___flatten_tree(self):
        ret = self.cf.flatten_tree()
        pprint(ret)
        self.assertEqual(len(ret), 6)

    def test_006___get_local_objects(self):
        ret = self.cf.get_local_objects()
        for r in ret:
            self.assertTrue(r.project==self.cf.project and r.variant==self.cf.variant)

    def test_007___get_foreign_objects(self):
        ret = self.cf.get_foreign_objects()
        for r in ret:
            self.assertFalse(r.project==self.cf.project and r.variant==self.cf.variant)

    def test_008___search_is_object_in_tree___local_library(self):
        ret = self.cf.search(project=self.project, variant=self.variant, libtype='ipspec')
        pprint(ret)
        self.assertTrue(self.cf.is_object_in_tree(ret[0]))

    def test_009___search_is_object_in_tree___local_config(self):
        ret = self.cf.search(project=self.project, variant='^rtmliotest2$')
        pprint(ret)
        self.assertTrue(self.cf.is_object_in_tree(ret[0]))

    def test_010___search_is_object_in_tree___foreign_library(self):
        ret = self.cf.search(project=self.project, variant='^rtmliotest1$', libtype='ipspec')
        pprint(ret)
        self.assertTrue(self.cf.is_object_in_tree(ret[0]))

    def test_011___search_is_object_in_tree___foreign_config(self):
        ret = self.cf.search(project=self.project, variant='^rtmliotest1$')
        pprint(ret)
        self.assertTrue(self.cf.is_object_in_tree(ret[0]))

    def test_012___remove_object_from_tree___remove_1_config(self):
        ret = self.cf.search(project=self.project, variant='^rtmliotest1$')
        c = self.cf.remove_object_from_tree(ret[0])
        print(self.cf.report())
        self.assertEqual(c, 1)

    def _test_013___remove_object_from_tree___remove_2_config(self):
        ret = self.cf.search(project=self.project, variant='^rtmliotest1$')
        c = self.cf.remove_object_from_tree(ret[0])
        print(self.cf.report())
        self.assertEqual(c, 1)
    
    def test_014___remove_object_from_tree___remove_library(self):
        ret = self.cf.search(project=self.project, variant='^rtmliotest2$', libtype='ipspec')
        c = self.cf.remove_object_from_tree(ret[0])
        print(self.cf.report())
        self.assertEqual(c, 1)

    def test_015___replace_object_in_tree___config(self):
        sobj = self.cf.search('Raton_Mesa', 'rtmliotest1')[0]
        self.cf.replace_object_in_tree(sobj, self.cf2)
        print(self.cf.report())
        print(repr(self.cf.report()))
        ans = 'Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2/for_regtest_1\n\t\tRaton_Mesa/rtmliotest2/bcmrbc/dev\n\t\tRaton_Mesa/rtmliotest2/cdc/dev\n\t\tRaton_Mesa/rtmliotest2/cdl/dev\n\t\tRaton_Mesa/rtmliotest2/cge/dev\n\t\tRaton_Mesa/rtmliotest2/circuitsim/dev\n\t\tRaton_Mesa/rtmliotest2/complib/dev\n\t\tRaton_Mesa/rtmliotest2/complibphys/dev\n\t\tRaton_Mesa/rtmliotest2/cvimpl/dev\n\t\tRaton_Mesa/rtmliotest2/cvrtl/dev\n\t\tRaton_Mesa/rtmliotest2/cvsignoff/dev\n\t\tRaton_Mesa/rtmliotest2/dftdsm/dev\n\t\tRaton_Mesa/rtmliotest2/dfx/dev\n\t\tRaton_Mesa/rtmliotest2/dv/dev\n\t\tRaton_Mesa/rtmliotest2/fetimemod/dev\n\t\tRaton_Mesa/rtmliotest2/fvpnr/dev\n\t\tRaton_Mesa/rtmliotest2/fvsyn/dev\n\t\tRaton_Mesa/rtmliotest2/gln_filelist/dev\n\t\tRaton_Mesa/rtmliotest2/gp/dev\n\t\tRaton_Mesa/rtmliotest2/interrba/dev\n\t\tRaton_Mesa/rtmliotest2/ippwrmod/dev\n\t\tRaton_Mesa/rtmliotest2/ipspec/dev\n\t\tRaton_Mesa/rtmliotest2/ipxact/dev\n\t\tRaton_Mesa/rtmliotest2/laymisc/dev\n\t\tRaton_Mesa/rtmliotest2/lint/dev\n\t\tRaton_Mesa/rtmliotest2/oa/dev\n\t\tRaton_Mesa/rtmliotest2/oasis/dev\n\t\tRaton_Mesa/rtmliotest2/pnr/dev\n\t\tRaton_Mesa/rtmliotest2/pv/dev\n\t\tRaton_Mesa/rtmliotest2/pvector/dev\n\t\tRaton_Mesa/rtmliotest2/r2g2/dev\n\t\tRaton_Mesa/rtmliotest2/rcxt/dev\n\t\tRaton_Mesa/rtmliotest2/rdf/dev\n\t\tRaton_Mesa/rtmliotest2/reldoc/dev\n\t\tRaton_Mesa/rtmliotest2/rtl/dev\n\t\tRaton_Mesa/rtmliotest2/rtlcompchk/dev\n\t\tRaton_Mesa/rtmliotest2/rv/dev\n\t\tRaton_Mesa/rtmliotest2/schmisc/dev\n\t\tRaton_Mesa/rtmliotest2/sdf/dev\n\t\tRaton_Mesa/rtmliotest2/sta/dev\n\t\tRaton_Mesa/rtmliotest2/stamod/dev\n\t\tRaton_Mesa/rtmliotest2/syn/dev\n\t\tRaton_Mesa/rtmliotest2/timemod/dev\n\t\tRaton_Mesa/rtmliotest2/upf_netlist/dev\n\t\tRaton_Mesa/rtmliotest2/upf_rtl/dev\n\t\tRaton_Mesa/rtmliotest1/for_regtest_1\n\t\t\tRaton_Mesa/rtmliotest1/bcmrbc/dev\n\t\t\tRaton_Mesa/rtmliotest1/complib/dev\n\t\t\tRaton_Mesa/rtmliotest1/complibbcm/dev\n\t\t\tRaton_Mesa/rtmliotest1/ipspec/dev\n\t\t\tRaton_Mesa/rtmliotest1/reldoc/dev\n'
        self.assertEqual(self.cf.report(), ans)


    def test_016___get_next_mutable_config(self):
        ret = self.cf2.get_next_mutable_config()
        print(ret)
        self.assertTrue(ret.project=='Raton_Mesa' and ret.variant=='rtmliotest1' and ret.config=='for_regtest_1')

    def test_017___get_mutable_configs_ready_for_snap(self):
        ret = self.cf2.get_mutable_configs_ready_for_snap()[0]
        print(ret)
        self.assertTrue(ret.project=='Raton_Mesa' and ret.variant=='rtmliotest1' and ret.config=='for_regtest_1')

    def test_018___get_configs_ready_for_release(self):
        ret = self.cf2.get_configs_ready_for_release()
        self.assertFalse(ret)

    def test_019___get_all_configs_with_only_library_or_release(self):
        ret = self.cf2.get_all_configs_with_only_library_or_release()[0]
        print(ret)
        self.assertTrue(ret.project=='Raton_Mesa' and ret.variant=='rtmliotest1' and ret.config=='for_regtest_1')
       
    def test_020___remove_empty_configs___none(self):
        gol = len(self.cf.flatten_tree())
        self.cf.remove_empty_configs()
        ret = len(self.cf.flatten_tree())
        self.assertEqual(gol, ret)
    
    def test_021___remove_empty_configs___one(self):
        all_libtypes = self.cf2.search('Raton_Mesa', 'rtmliotest1', '')
        all_libtypes = list(set(all_libtypes))
        print('all_libtypes: {}'.format(all_libtypes))

        for x in all_libtypes:
            print("{}:{}".format(x, id(x)))
            self.cf2.remove_object_from_tree(x)
       
        print(self.cf2.report())
        self.assertTrue(self.cf2.search("Raton_Mesa", "rtmliotest1"))
        print(self.cf2.search("Raton_Mesa", "rtmliotest1"))
        self.cf2.remove_empty_configs()
        self.assertFalse(self.cf2.search("Raton_Mesa", "rtmliotest1"))

    def test_022___clone_tree___clone_simple_false(self):
        clone = self.cf.clone_tree('newxxx')
        print(self.cf.report())
        print('=====')
        print(clone.report())
        ans = 'Raton_Mesa/rtmliotest2/newxxx\n\tRaton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n'
        self.assertEqual(clone.report(), ans)


    def test_023___clone_tree___clone_simple_true(self):
        print(self.cf.report())
        clone = self.cf.clone_tree('newxxx', clone_simple=True)
        print('-------------------')
        print(self.cf.report())
        print('=====')
        print(repr(clone.report()))
        ans = 'Raton_Mesa/rtmliotest2/newxxx\n\tRaton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n'
        self.assertEqual(clone.report(), ans)

    def test_024___clone_tree___clone_simple_true_clone_immutable_true(self):
        print(self.cf.report())
        clone = self.cf.clone_tree('newxxx', clone_simple=True, clone_immutable=True)
        print('-------------------')
        print(self.cf.report())
        print('=====')
        print(clone.report())
        print('-------------------')
        x = clone.search('Raton_Mesa', 'rtmliotest1', 'ipspec')[0]
        x.save()
        print(x._icm._FOR_REGTEST)
        print('-------------------')
        ans = 'Raton_Mesa/rtmliotest2/newxxx\n\tRaton_Mesa/rtmliotest2/ipspec/newxxx\n\tRaton_Mesa/rtmliotest2/reldoc/newxxx\n\tRaton_Mesa/rtmliotest1/newxxx\n\t\tRaton_Mesa/rtmliotest1/ipspec/newxxx\n\t\tRaton_Mesa/rtmliotest1/reldoc/newxxx\n'
        self.assertEqual(clone.report(), ans)

    def test_025___clone_tree___no_problem_when_clone_immutable(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        ret = cf.clone_tree('xxx', clone_simple=False, clone_immutable=True)    
        self.assertTrue(ret)

    def test_026___clone_tree___config_exists_when_clone_immutable(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        ans = "Cannot clone to Raton_Mesa/rtmliotest2@snap-1 - it already exists"
        with self.assertRaisesRegexp(Exception, ans):
            cf.clone_tree('snap-1', clone_simple=False, clone_immutable=True)    

    def test_027___clone_tree___library_exists_when_clone_immutable_clone_simple(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        ans = "Cannot clone to Raton_Mesa/rtmliotest2@dev - it already exists"
        with self.assertRaisesRegexp(Exception, ans):
            cf.clone_tree('dev', clone_simple=True, clone_immutable=True)    

    def test_028___clone_tree___release_exists_when_clone_immutable_clone_simple(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.config, preview=True)
        ans = "Failed clone_tree because these releases already exist:.*/intel/Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d"
        with self.assertRaisesRegexp(Exception, ans):
            cf.clone_tree('REL1.0RTMrevA0__22ww135d', clone_simple=True, clone_immutable=True)    

    def test_029___clone_tree___no_problem_when_no_clone_immutable(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest1', config_or_library_or_release='snap-1', preview=True)
        ret = cf.clone_tree('snap-2222222', clone_simple=False, clone_immutable=False)    
        self.assertTrue(ret)

    def test_030___get_immutable_parents(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release='snap-1', preview=True)
        print(cf.report())
        x = cf.search('Raton_Mesa', 'rtmliotest1', libtype='reldoc')[0]
        ret = x.get_immutable_parents()
        ans = ['Raton_Mesa/rtmliotest2/snap-1', 'Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a']
        retname = [x.get_full_name() for x in ret]
        print(retname)
        self.assertEqual(retname, ans)

    def test_031___get_configs_to_clone_when_self_changes(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        print(cf.report())
        x = cf.search('Raton_Mesa', 'rtmliotest1')[0]
        ret = x.get_configs_to_clone_if_self_changes()
        retname = [x.get_full_name() for x in ret]
        print("retname: {}".format(retname))
        ans = ['Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a']
        self.assertEqual(retname, ans)
        
    def test_032___get_configs_to_clone_when_self_changes_including_mutable(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        print(cf.report())
        x = cf.search('Raton_Mesa', 'rtmliotest1')[0]
        ret = x.get_configs_to_clone_if_self_changes_including_mutable()
        retname = [x.get_full_name() for x in ret]
        print("retname: {}".format(retname))
        ans = ['Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a']
        self.assertEqual(retname, ans)
       
    def test_033___get_modified_immutable_configs(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        print(cf.report())
        x = cf.search('Raton_Mesa', 'rtmliotest1')[0]
        x.description = 'xxx'
        ret = cf.get_modified_immutable_configs()
        ans = 'Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a'
        self.assertEqual(x.get_full_name(), ans)

    def test_034___get_modified_mutable_configs(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        print(cf.report())
        x = cf.search('Raton_Mesa', 'rtmliotest1')[0]
        x.config = 'xxx'
        ret = cf.get_modified_immutable_configs()
        self.assertEqual(x.get_full_name(), 'Raton_Mesa/rtmliotest1/xxx')

    def test_035___convert_modified_immutable_configs_into_mutable(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.release, preview=True)
        print(cf.report())
        for v in ['rtmliotest2', 'rtmliotest1']:
            x = cf.search('Raton_Mesa', v)[0]
            x.description = 'xxx'
        print(cf.get_modified_immutable_configs())
        ret = cf.convert_modified_immutable_configs_into_mutable('www')
        print(cf.report())
        self.assertEqual(ret, 1)

    def test_036___rename_modified_mutable_configs(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release=self.config, preview=True)
        print(cf.report())
        for v in ['rtmliotest2', 'rtmliotest1']:
            x = cf.search('Raton_Mesa', v)[0]
            x.description = 'xxx'
        print(cf.get_modified_immutable_configs())
        ret = cf.rename_modified_mutable_configs('www')
        print(cf.report())
        self.assertEqual(ret, 1)

    def test_037___get_all_projects(self):
        ret = self.cf.get_all_projects()
        self.assertEqual(ret, ['Raton_Mesa'])

    def test_038___name_property___library(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest1', config_or_library_or_release='dev', libtype='ipspec', preview=True)
        self.assertEqual(cf.name, 'dev')

    def test_039___name_property___release(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest1', config_or_library_or_release='snap-fortnr_1', libtype='ipspec', preview=True)
        self.assertEqual(cf.name, 'snap-fortnr_1')

    def test_040___name_property___config(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release='dev', preview=True)
        self.assertEqual(cf.name, 'dev')

    def test_041___get_depot_path___library(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest2', config_or_library_or_release='dev', libtype='ipspec', preview=True)
        ans = '//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/...@'
        self.assertIn(ans, cf.get_depot_path())

    def test_042___get_depot_path___release(self):
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm('Raton_Mesa', 'rtmliotest1', config_or_library_or_release='snap-fortnr_1', libtype='ipspec', preview=True)
        ans = '//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@15'
        self.assertEqual(cf.get_depot_path(), ans)


if __name__ == '__main__':
    unittest.main()
