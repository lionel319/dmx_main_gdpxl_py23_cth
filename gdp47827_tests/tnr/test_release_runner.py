#!/usr/bin/env python

from __future__ import print_function
from builtins import object
import sys
import os
import logging
import unittest

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

from dmx.tnrlib.release_runner import ReleaseRunner
from dmx.utillib.utils import is_pice_env
import dmx.tnrlib.release_runner as dtrr

class TestReleaseRunner(unittest.TestCase):
    '''
    i10socfm/liotest1/REL4.0FM6revA0__21ww473a
            i10socfm/liotest1/ipspec/fmx_dev/REL4.0FM6revA0__21ww473g
            i10socfm/liotest1/reldoc/fmx_dev/REL4.0FM6revA0__21ww473b
    '''
    

    def setUp(self):
        self.module_path = sys.modules[ReleaseRunner.__module__].__file__
        class dummy(object): pass
        self.args = dummy
        self.args.work_dir = '/tmp'
        self.args.project = 'Raton_Mesa'
        self.args.variant = 'rtmliotest1'
        self.args.libtype = 'reldoc'
        self.args.cconfig = 'REL1.0RTMrevA0__22ww135a'
        self.args.sconfig = 'REL1.0RTMrevA0__22ww135d'
        self.args.configuration = self.args.cconfig
        self.args.snapshot_config = self.args.cconfig
        self.args.milestone = '1.0'
        self.args.thread = 'RTMrevA0'
        self.ipspec_config = 'REL1.0RTMrevA0__22ww135a'
        self.args.label = ''
        self.args.dont_create_rel = False
        self.rr = ReleaseRunner(self.args)


    def tearDown(self):
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, self.module_path)


    def test_010___get_snapshot_config_for_abnr_rerun___variant_release(self):
        ret = self.rr.get_snapshot_config_for_abnr_rerun(
            self.args.project, self.args.variant, None, self.args.cconfig)
        self.assertEqual(ret, self.args.cconfig)

    def test_020___get_snapshot_config_for_abnr_rerun___libtype_release(self):
        ret = self.rr.get_snapshot_config_for_abnr_rerun(
            self.args.project, self.args.variant, self.args.libtype, self.args.cconfig)
        self.assertEqual(ret, self.args.sconfig)

    def test_030___get_ipspec_config(self):
        ret = self.rr.get_ipspec_config(
            self.args.project, self.args.variant, self.args.cconfig)
        self.assertEqual(ret, self.ipspec_config)

    def test_040___extract_subconfig_for_libtype(self):
        ret = self.rr.get_snapshot_config_for_abnr_rerun(
            self.args.project, self.args.variant, self.args.libtype, self.args.cconfig)
        self.assertEqual(ret, self.args.sconfig)

    def test_050___get_configuration_to_test_and_release___variant_release(self):
        self.args.libtype = None
        rr = ReleaseRunner(self.args)
        ret = rr.get_configuration_to_test_and_release()
        self.assertEqual(ret, self.args.cconfig)

    def test_060___get_configuration_to_test_and_release___libtype_release(self):
        ret = self.rr.get_configuration_to_test_and_release()
        self.assertEqual(ret, self.args.sconfig)


    def test_070___get_rel_config_name___with_label(self):
        ret = self.rr.get_rel_config_name(self.args.project, self.args.variant, self.args.libtype,
            self.args.milestone, self.args.thread, 'HAHA')
        print(ret)
        self.assertTrue(ret.startswith('REL1.0RTMrevA0--HAHA__'))

    def test_071___get_rel_config_name___no_label(self):
        ret = self.rr.get_rel_config_name(self.args.project, self.args.variant, self.args.libtype,
            self.args.milestone, self.args.thread, None)
        self.assertTrue(ret.startswith('REL1.0RTMrevA0__'))

    def test_072___get_rel_config_name___with_prel_and_label(self):
        ret = self.rr.get_rel_config_name(self.args.project, self.args.variant, self.args.libtype,
            self.args.milestone, self.args.thread, 'HAHA', prel='prel_4')
        print(ret)
        self.assertTrue(ret.startswith('PREL1.0RTMrevA0--prel_4-HAHA__'))

    def test_073___get_rel_config_name___with_prel(self):
        ret = self.rr.get_rel_config_name(self.args.project, self.args.variant, self.args.libtype,
            self.args.milestone, self.args.thread, None, prel='prel_4')
        print(ret)
        self.assertTrue(ret.startswith('PREL1.0RTMrevA0--prel_4__'))

    def test_080___get_yyyy_ww_dow_for_today(self):
        ret = self.rr.get_yyyy_ww_dow_for_today()
        ### Just make sure it returns 3-element-tuple, ie:-
        ### (yyyy, ww, dow)
        self.assertEqual(len(ret), 3)

    def test_090___get_config_timestamp_info(self):
        ret = self.rr.get_config_timestamp_info()
        ### Just make sure it returns 3-element-tuple, ie:-
        ### (2-digi-yy, 2-digit-ww, 1-digit-dow)
        self.assertEqual(len(ret[0]), 2)
        self.assertEqual(len(ret[1]), 2)
        self.assertEqual(len(ret[2]), 1)

    def test_100___get_tnrwaivers_files(self):
        ret = self.rr.get_tnrwaivers_files()
        self.assertEqual(ret, [])

    def test_110___send_completion_notification___ok(self):
        self.rr.send_completion_notification('success', 'message', 'rel_config')

    def test_120___workspace_size(self):
        ret = self.rr.workspace_size('.')
        self.assertTrue(type(ret) == int)

    def test_130___extract_sync_patterns___with_dot(self):
        ret = self.rr.extract_sync_patterns(['dummy_file.txt'])
        self.assertEqual(ret, set(['.../*.txt']))

    def test_130___extract_sync_patterns___no_dot(self):
        ret = self.rr.extract_sync_patterns(['dummy_file'])
        self.assertEqual(ret, set(['dummy_file']))

    def test_140___test_setup_logging(self):
        ret = dtrr.setup_logging()


    def test_200___get_rel_config_name___no_view_no_label(self):
        ret = self.rr.get_rel_config_name('i14socnd', 'ar_lib', 'rtl', '5.0', 'ND5revA0', None, None)
        self.assertTrue(ret.startswith("REL5.0ND5revA0__"))

    def test_200___get_rel_config_name___single_view_no_label(self):
        ret = self.rr.get_rel_config_name('i14socnd', 'ar_lib', 'rtl', '5.0', 'ND5revA0', None, ['view_phys'])
        self.assertTrue(ret.startswith("REL5.0ND5revA0--PHYS__"))

    def test_200___get_rel_config_name___no_view_with_label(self):
        ret = self.rr.get_rel_config_name('i14socnd', 'ar_lib', 'rtl', '5.0', 'ND5revA0', 'TheLabel', None)
        self.assertTrue(ret.startswith("REL5.0ND5revA0--TheLabel__"))

    def test_200___get_rel_config_name___single_view_with_label(self):
        ret = self.rr.get_rel_config_name('i14socnd', 'ar_lib', 'rtl', '5.0', 'ND5revA0', 'TheLabel', ['view_rtl'])
        self.assertTrue(ret.startswith("REL5.0ND5revA0--RTL-TheLabel__"))

    def test_200___get_rel_config_name___multi_view_with_label(self):
        ret = self.rr.get_rel_config_name('i14socnd', 'ar_lib', 'rtl', '5.0', 'ND5revA0', 'TheLabel', ['view_rtl', 'view_phys'])
        self.assertTrue(ret.startswith("REL5.0ND5revA0--RTL-PHYS-TheLabel__"))

    def test_200___get_rel_config_name___multi_view_no_label(self):
        ret = self.rr.get_rel_config_name('i14socnd', 'ar_lib', 'rtl', '5.0', 'ND5revA0', None, ['view_rtl', 'view_phys'])
        self.assertTrue(ret.startswith("REL5.0ND5revA0--RTL-PHYS__"))



if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
