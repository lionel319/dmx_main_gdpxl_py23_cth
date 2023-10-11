#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_snap.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxSnap(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setsite = 'env DMX_GDPSITE=intel DB_DEVICE=FM6 '
        self.setsite = 'env DB_FAMILY=Ratonmesa DB_DEVICE=RTM DB_THREAD=RTMrevA0 '
        
    def tearDown(self):
        pass
    
    def test_001___dmx_snap___not_valid_project(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p iiiiiiii  -i liotest1 -d ipspec -b snap-2 -n '.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        self.assertIn('is not a valid project', stderr)

    def test_002___dmx_snap___not_valid_variant(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -i xxxxxxx -d ipspec -b snap-2 -n '.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        self.assertIn('is not a valid variant', stderr)

    def test_003___dmx_snap___not_valid_libtype(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -d xxxxxxx -i rtmliotest1 -b snap-xxx -n '.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        self.assertIn('is not a valid libtype', stderr)

    def test_004___dmx_snap___not_valid_config_libtype(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -d ipspec -i rtmliotest1 -b xxx -n '.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        self.assertIn('Configuration xxx does not exist', stderr)

    def test_005___dmx_snap___not_valid_config_variant(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -i rtmliotest1 -b xxx -n '.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        self.assertIn('Raton_Mesa/rtmliotest1@xxx does not exist', stderr)

    def test_100___dmx_snap_tree___original(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -i rtmliotest1 -b dev -n --snapshot snap-xxx'.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        ans = 'Raton_Mesa/rtmliotest1/snap-xxx\n\tRaton_Mesa/rtmliotest1/bcmrbc/dev/snap-xxx dev@snap-xxx[@now]\n\tRaton_Mesa/rtmliotest1/complib/dev/snap-xxx dev@snap-xxx[@now]\n\tRaton_Mesa/rtmliotest1/complibbcm/dev/snap-xxx dev@snap-xxx[@now]\n\tRaton_Mesa/rtmliotest1/ipspec/dev/snap-xxx dev@snap-xxx[@now]\n\tRaton_Mesa/rtmliotest1/reldoc/dev/snap-xxx dev@snap-xxx[@now]\n\n'
        self.assertIn(ans, stdout)

    def test_101___dmx_snap_tree___ip_filter(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -i rtmliotest2 -b for_regtest_1 -n --snapshot snap-xxx --ip-filter rtmliotest1'.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        ans = 'Raton_Mesa/rtmliotest2/snap-xxx\n\tRaton_Mesa/rtmliotest1/snap-xxx\n\t\tRaton_Mesa/rtmliotest1/bcmrbc/dev/snap-xxx dev@snap-xxx[@now]\n\t\tRaton_Mesa/rtmliotest1/complib/dev/snap-xxx dev@snap-xxx[@now]\n\t\tRaton_Mesa/rtmliotest1/complibbcm/dev/snap-xxx dev@snap-xxx[@now]\n\t\tRaton_Mesa/rtmliotest1/ipspec/dev/snap-xxx dev@snap-xxx[@now]\n\t\tRaton_Mesa/rtmliotest1/reldoc/dev/snap-xxx dev@snap-xxx[@now]\n\n'
        self.assertIn(ans, stdout)

    def test_102___dmx_snap_tree___libtype_filter(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -i rtmliotest1 -b dev -n --snapshot snap-xxx --deliverable-filter ipspec reldoc'.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        ans = 'Raton_Mesa/rtmliotest1/snap-xxx\n\tRaton_Mesa/rtmliotest1/ipspec/dev/snap-xxx dev@snap-xxx[@now]\n\tRaton_Mesa/rtmliotest1/reldoc/dev/snap-xxx dev@snap-xxx[@now]\n\n'
        self.assertIn(ans, stdout)

    def test_103___dmx_snap_tree___view_filter(self):
        exitcode, stdout, stderr = self.rc('{} {} snap -p Raton_Mesa -i rtmliotest1 -b dev -n --snapshot snap-xxx --deliverable-filter view_testchip'.format(self.setsite, self.dmx), maxtry=1)
        print('stdout: {}\nstderr: {}\n'.format(stdout, stderr))
        ans = 'Raton_Mesa/rtmliotest1/snap-xxx\n\tRaton_Mesa/rtmliotest1/ipspec/dev/snap-xxx dev@snap-xxx[@now]\n\tRaton_Mesa/rtmliotest1/reldoc/dev/snap-xxx dev@snap-xxx[@now]\n\n'
        self.assertIn(ans, stdout)

if __name__ == '__main__':
    unittest.main()
