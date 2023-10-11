#!/usr/bin/env python

import sys
import os
import logging
import unittest
import tempfile

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

from dmx.tnrlib.splunk_log import SplunkLog

class TestSplunkLog(unittest.TestCase):
    
    def setUp(self):
        self.module_path = sys.modules[SplunkLog.__module__].__file__
        tmpdir = tempfile.gettempdir()
        self.s = SplunkLog('qa', 'regtest', {'a':'b'}, splunk_data_dir=tmpdir, splunk_log_dir=tmpdir)

    def tearDown(self):
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, self.module_path)

    def test_020___split_configuration___non_rel_config(self):
        ret = self.s.split_configuration('asd')
        self.assertEqual(ret, {
            'config_milestone': '', 
            'config_year': '', 
            'config_workweek': '', 
            'config_day': '', 
            'config_suffix': ''} )


    def test_020___split_configuration___rel_config(self):
        ret = self.s.split_configuration('REL5.0__16ww123abc')
        self.assertEqual(ret, {
            'config_milestone': '5.0', 
            'config_year': '16', 
            'config_workweek': '12', 
            'config_day': '3', 
            'config_suffix': 'abc'} )

    def test_030___log(self):
        ret = self.s.log({'test':'yes'})


if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
