#!/usr/bin/env python

from __future__ import print_function
from builtins import object
import sys
import os
import logging
import unittest

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

import dmx.tnrlib.audit_check 

class TestAuditCheck(unittest.TestCase):
    

    def setUp(self):
        self.infile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'audit_check.txt')
        self.non_ascii_infile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'audit_check_non_ascii.txt')
        self.a = dmx.tnrlib.audit_check.AuditFile(workspace_rootdir=os.path.join(os.path.dirname(self.infile)))

    def tearDown(self):
        pass

    def test_001___get_checksum___no_filter_no_rcs_disable(self):
        ret = self.a.get_checksum(self.infile,  '', '')
        self.assertEqual(ret, '9e214b874b19faae71407990b45212f0')

    def test_002___get_checksum___no_filter_yes_rcs_disable(self):
        ret = self.a.get_checksum(self.infile,  '', 'yes')
        self.assertEqual(ret, 'dfdd7fb2c11addb82a0c47c36654ab02')

    def test_003___get_checksum___yes_filter_no_rcs_disable(self):
        ret = self.a.get_checksum(self.infile,  '.*bbb.*', '')
        self.assertEqual(ret, '12d3e89461041ca06866c2bc97a8eeac')

    def test_004___get_checksum___yes_filter_yes_rcs_disable(self):
        ret = self.a.get_checksum(self.infile,  '.*bbb.*', 'yes')
        self.assertEqual(ret, '04d0db8da2fbeaa9f6cc1779e6889bdb')

    def test_005___get_checksum___file_contain_non_ascii(self):
        ret = self.a.get_checksum(self.non_ascii_infile,  '', '')
        self.assertEqual(ret, '7fa9e64c5a40057fb9c25e31ae16a076')



if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
