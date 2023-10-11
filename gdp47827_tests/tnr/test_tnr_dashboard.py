#!/usr/bin/env python

import sys
import os
import logging
import unittest

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

from dmx.tnrlib.tnr_dashboard import TNRDashboard, TNRDashboardForRelease, TNRDashboardForQuick

class TestTnrDashboard(unittest.TestCase):
    
    def setUp(self):
        self.module_path = sys.modules[TNRDashboard.__module__].__file__

        class dummyclass(): pass
        request = dummyclass()
        request.release_id = 'na'
        request.user = 'na'
        request.timestamp = 'na'
        request.project = 'na'
        request.variant = 'na'
        request.config = 'na'
        request.libtype = 'na'
        request.thread = 'na'
        request.milestone = 'na'
        request.label = 'na'
        request.description = 'na'
        request.abnr_version = 'na'
        self.t = TNRDashboard('qa')
        self.t4r = TNRDashboardForRelease('qa', '1111111', 'rerun_config', 'ipspec_config', request)
        self.t4q = TNRDashboardForQuick('qa', 'workspacename', 'ms', 'thread', 'project', 'variant', 'libtype', 'config', 'user', 'rundate')

    def tearDown(self):
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, self.module_path)

    def test_010___clean_error_message(self):
        msg = 'a'*1006
        ret = self.t.clean_error_message(msg)
        self.assertIn('error truncated', ret)



if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
