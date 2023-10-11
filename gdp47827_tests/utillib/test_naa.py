#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_naa.py $
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
import dmx.utillib.naa
print(dmx.utillib.naa.__file__)

class TestUtilsNaa(unittest.TestCase):
    def setUp(self):
        self.n = dmx.utillib.naa.NAA()

    def test_010___is_path_naa_path(self):
        self.assertFalse(self.n.is_path_naa_path('/nfs/site/disks/naa'))

    def test_011___is_path_naa_path(self):
        self.assertFalse(self.n.is_path_naa_path('/nfs/site/disks/f_n_naa_12'))

    def test_012___is_path_naa_path(self):
        self.assertFalse(self.n.is_path_naa_path('/nfs/site/disks/_naa_12'))

    def test_013___is_path_naa_path(self):
        self.assertTrue(self.n.is_path_naa_path('/nfs/site/disks/fln_naa_12'))

    def test_014___is_path_naa_path(self):
        self.assertTrue(self.n.is_path_naa_path('/nfs/site/disks/123_naa_abc'))

    def test_015___is_path_naa_path(self):
        self.assertTrue(self.n.is_path_naa_path('/nfs/site/disks/f1n_naa_2c3'))



    def test_100___get_info_from_naa_path___is_naa_path(self):
        f = '/nfs/site/disks/fln_naa_1/i10socfm/fmgpio_reg/rcxt/dev/results/timingspef_e/fmgpio_reg/corners.smc.1'
        ret = self.n.get_info_from_naa_path(f)
        pprint(ret)
        self.assertEqual(ret, {
             'disk': 'fln_naa_1',
             'filepath': 'results/timingspef_e/fmgpio_reg/corners.smc.1',
             'library': 'dev',
             'libtype': 'rcxt',
             'project': 'i10socfm',
             'variant': 'fmgpio_reg',
             'wsrelpath': 'fmgpio_reg/rcxt/results/timingspef_e/fmgpio_reg/corners.smc'
        })

    def test_101___get_info_from_naa_path___is_not_naa_path(self):
        f = '/p/psg/flows/common/dmx/9.5/run_tests.py'
        ret = self.n.get_info_from_naa_path(f)
        self.assertEqual(ret, {})


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()
