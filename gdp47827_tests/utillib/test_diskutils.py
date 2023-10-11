#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_diskutils.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import os
import sys
import unittest
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.utillib.utils import run_command
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.diskutils


class TestDiskUtils(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.du = dmx.utillib.diskutils.DiskUtils()
        self.dd = self.du.get_all_disks_data('psg_data_') 
        self.ddnaa = self.du.get_all_disks_data("fln_naa_")

        self.mocked_dd = [
            {u'Usage': 100, 'Avail': 900, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 1000},
            {u'Usage': 100, 'Avail': 500, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 2000},
            {u'Usage': 100, 'Avail': 700, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 3000},
        ]

    def tearDown(self):
        self.du.site = 'local'

    def test_001___get_all_disks_data(self):
        disks = [x['StandardPath'] for x in self.dd]
        self.assertIn('/nfs/site/disks/psg_data_1', disks)

    def test_002a___sort_disks_data_by_key___Avail(self):
        ret = self.du.sort_disks_data_by_key(self.mocked_dd, 'Avail')
        ans = [
            {u'Usage': 100, 'Avail': 900, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 1000},
            {u'Usage': 100, 'Avail': 700, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 3000},
            {u'Usage': 100, 'Avail': 500, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 2000},
        ]
        self.assertEqual(ans, ret)

    def test_002b___sort_disks_data_by_key___Size(self):
        ret = self.du.sort_disks_data_by_key(self.mocked_dd, 'Size')
        ans = [
            {u'Usage': 100, 'Avail': 700, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 3000},
            {u'Usage': 100, 'Avail': 500, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 2000},
            {u'Usage': 100, 'Avail': 900, u'StandardPath': u'/nfs/site/disks/psg_data_1', u'Size': 1000},
        ]
        self.assertEqual(ans, ret)

    def _test_003___find_folder_from_disks_data(self):
        ret = self.du.find_folder_from_disks_data(self.dd, r'/lionelta\b', maxdepth=1, mindepth=1)
        self.assertEqual(ret, '/nfs/site/disks/psg_data_1/lionelta')

    def _test_003a___find_folder_for_disks_data___no_wildcard(self):
        ret = self.du.find_folder_from_disks_data(self.ddnaa, 'dev', diskpostfix=r'i10socfm/liotest1/rcxt', maxdepth=1, mindepth=1)
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_003b___find_folder_for_disks_data___with_wildcard(self):
        ret = self.du.find_folder_from_disks_data(self.ddnaa, 'dev', diskpostfix=r'i10socfm/liotest1/*', maxdepth=1, mindepth=1)
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_004a___find_exact_folder_for_disks_data___no_wildcard_site_local(self):
        ret = self.du.find_exact_folder_from_disks_data(self.ddnaa, r'i10socfm/liotest1/rcxt/dev')
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_004b___find_exact_folder_for_disks_data___with_wildcard_site_local(self):
        ret = self.du.find_exact_folder_from_disks_data(self.ddnaa, r'i10socfm/liotest1/*/dev')
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_004c___find_exact_folder_for_disks_data___no_wildcard_site_png(self):
        self.du.site = 'png'
        ret = self.du.find_exact_folder_from_disks_data(self.ddnaa, r'i10socfm/liotest1/rcxt/dev')
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_004d___find_exact_folder_for_disks_data___with_wildcard_site_png(self):
        self.du.site = 'png'
        ret = self.du.find_exact_folder_from_disks_data(self.ddnaa, r'i10socfm/liotest1/*/dev')
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_004e___find_exact_folder_for_disks_data___no_wildcard_site_sc(self):
        self.du.site = 'sc'
        ret = self.du.find_exact_folder_from_disks_data(self.ddnaa, r'i10socfm/liotest1/rcxt/dev')
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')

    def _test_004f___find_exact_folder_for_disks_data___with_wildcard_site_sc(self):
        self.du.site = 'sc'
        ret = self.du.find_exact_folder_from_disks_data(self.ddnaa, r'i10socfm/liotest1/*/dev')
        self.assertEqual(ret, '/nfs/site/disks/fln_naa_2/i10socfm/liotest1/rcxt/dev')



if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

