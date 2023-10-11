#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_derive_bom.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
import re

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxDeriveBom(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.env = 'env DB_FAMILY=Libertymesa DB_DEVICE=LTM DB_THREAD=LTMrevA0 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.7 '
        self.rc = dmx.utillib.utils.run_command
        self.asadmin = '--user=icmanage'
        
    def tearDown(self):
        pass

    def test_001___dmx_derive_bom___successful_dryrun(self):
        cmd = ' derive bom -p da_i16 -i dai16liotest1 -b REL1.0LTMrevA0__22ww315b --exact --thread __for_system_regression__ --hier -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        
        ans = 'Created BOM da_i16/dai16liotest1/__for_system_regression__'
        self.assertIn(ans, stdout+stderr)

    def test_002___dmx_derive_bom___already_exist(self):
        cmd = ' derive bom -p da_i16 -i dai16liotest1 -d ipspec -b REL1.0LTMrevA0__22ww315b --exact --thread testbranch_220823a -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        
        ans = 'Target library da_i16/dai16liotest1:ipspec/testbranch_220823a already exists'
        self.assertIn(ans, stdout+stderr)

    def test_003___dmx_derive_bom___from_non_immutable(self):
        cmd = ' derive bom -p da_i16 -i dai16liotest1 -d ipspec -b dev --exact --thread __for_system_tests__ -n'
        exitcode, stdout, stderr = self.rc('{} USER=xxxxx {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        
        ans = 'Source BOM must be immutable'
        self.assertIn(ans, stdout+stderr)



    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
