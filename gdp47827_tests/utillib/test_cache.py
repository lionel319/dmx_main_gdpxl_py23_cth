#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_cache.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
from pprint import pprint
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.cache
print(dmx.utillib.cache.__file__)

class TestUtilsCache(unittest.TestCase):
    def setUp(self):
        self.n = dmx.utillib.cache.Cache()

    def test_010___is_path_cache_path(self):
        self.assertFalse(self.n.is_path_cache_path('/nfs/site/disks/sion'))

    def test_011___is_path_cache_path(self):
        self.assertFalse(self.n.is_path_cache_path('/nfs/site/disks/f_n_sion_12'))

    def test_012___is_path_cache_path(self):
        self.assertFalse(self.n.is_path_cache_path('/nfs/site/disks/_sion_12'))

    def test_013___is_path_cache_path(self):
        self.assertTrue(self.n.is_path_cache_path('/nfs/site/disks/fln_sion_12/cache'))

    def test_014___is_path_cache_path(self):
        self.assertTrue(self.n.is_path_cache_path('/nfs/site/disks/123_sion_abc/cache'))

    def test_015___is_path_cache_path(self):
        self.assertTrue(self.n.is_path_cache_path('/nfs/site/disks/f1n_sion_2c3/cache/'))



    def test_100___get_info_from_cache_path___is_cache_path(self):
        f = '/nfs/site/disks/fln_sion_1/cache/i10socfm/liotest1/rdf/REL5.0FM8revA0--TestSyncpoint__17ww404a/audit/audit.aib_ssm.rdf.xml'
        ret = self.n.get_info_from_cache_path(f)
        pprint(ret)
        self.assertEqual(ret, {
             'disk': 'fln_sion_1',
             'filepath': 'audit/audit.aib_ssm.rdf.xml',
             'config': 'REL5.0FM8revA0--TestSyncpoint__17ww404a',
             'libtype': 'rdf',
             'project': 'i10socfm',
             'variant': 'liotest1',
             'wsrelpath': 'liotest1/rdf/audit/audit.aib_ssm.rdf.xml'
        })

    def test_101___get_info_from_cache_path___is_not_cache_path(self):
        f = '/p/psg/flows/common/dmx/9.5/run_tests.py'
        ret = self.n.get_info_from_cache_path(f)
        self.assertEqual(ret, {})


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()
