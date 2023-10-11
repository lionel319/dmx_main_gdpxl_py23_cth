#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_bom_parents.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxBomParents(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.env = 'env DB_FAMILY=Falcon DMX_GDPSITE=intel'
        self.rc = dmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___dmx_bom_parents_libtype_dev_nohier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -d ipspec -b dev'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest1@for_regtest_1'
        self.assertIn(ans, stdout)

    def test_001___dmx_bom_parents_libtype_dev_hier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -d ipspec -b dev --hier'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest1@for_regtest_1'
        self.assertIn(ans, stdout)

    def test_002___dmx_bom_parents_libtype_snap_nohier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -d ipspec -b snap-cicq__rtmliotest1__gdpxltest4__22ww134a '.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest1@snap-cicq__rtmliotest1__gdpxltest4__22ww134a'
        self.assertIn(ans, stdout)

    def test_002___dmx_bom_parents_libtype_snap_hier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -d ipspec -b snap-cicq__rtmliotest1__gdpxltest4__22ww134a --hier'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest1@snap-cicq__rtmliotest1__gdpxltest4__22ww134a'
        self.assertIn(ans, stdout)

    def test_003___dmx_bom_parents_variant_dev_nohier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -b for_regtest_1 '.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest2@for_regtest_1'
        self.assertIn(ans, stdout)

    def test_003___dmx_bom_parents_variant_dev_hier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -b for_regtest_1 --hier'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest2@for_regtest_1'
        self.assertIn(ans, stdout)

    def test_004___dmx_bom_parents_variant_snap_nohier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -b REL1.0RTMrevA0__22ww135a '.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a'
        self.assertIn(ans, stdout)

    def test_004___dmx_bom_parents_variant_snap_hier(self):
        exitcode, stdout, stderr = self.rc('{} {} bom parents -p Raton_Mesa -i rtmliotest1 -b REL1.0RTMrevA0__22ww135a --hier'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Raton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a'
        self.assertIn(ans, stdout)



    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
