#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_bom_delete.py $
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

class TestDmxBomDelete(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.env = 'env DB_FAMILY=Falcon DMX_GDPSITE=intel'
        self.rc = dmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___dmx_bom_delete___bom_does_not_exist(self):
        cmd = 'bom delete -p i10socfm -i liotestfc1 -b __xx__  -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'does not exist'
        self.assertIn(ans, stderr)

    def test_002___dmx_bom_delete___variant_does_not_exist(self):
        cmd = 'bom delete -p i10socfm -i __xx__  -b dev -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'does not exist'
        self.assertIn(ans, stderr)

    def test_003___dmx_bom_delete___cant_delete_snap(self):
        cmd = 'bom delete -p i10socfm -i liotestfc1 -b snap-1 -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'cannot delete immutable config'
        self.assertIn(ans, stderr)

    def test_004___dmx_bom_delete___cant_delete_rel(self):
        cmd = 'bom delete -p i10socfm -i liotestfc1 -b REL-1 -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'cannot delete immutable config'
        self.assertIn(ans, stderr)

    def test_005___dmx_bom_delete___cant_delete_prel(self):
        cmd = 'bom delete -p i10socfm -i liotestfc1 -b PREL-1 -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'cannot delete immutable config'
        self.assertIn(ans, stderr)

    def test_010___dmx_bom_delete_cant_delete_used_config(self):
        cmd = 'bom delete -p Raton_Mesa -i rtmliotest1 -b for_regtest_1 '
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Cannot remove, config /intel/Raton_Mesa/rtmliotest1/for_regtest_1 is used by'
        self.assertIn(ans, stderr)
    
    def test_099___dmx_bom_delete___success(self):
        cmd = 'bom delete -p Raton_Mesa -i rtmliotest2 -b for_regtest_1 -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Deleting config'
        self.assertIn(ans, stderr)


    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
