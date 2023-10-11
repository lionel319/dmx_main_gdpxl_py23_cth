#!/usr/intel/pkgs/python3/3.9.6/bin/python3

# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/gdp47827_tests/cmxcmd/test_cmx_environment.py $
# $Revision: #1 $
# $Change: 7461593 $
# $DateTime: 2023/01/29 18:57:43 $
# $Author: lionelta $

from __future__ import print_function
import UsrIntel.R1

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import cmx.utillib.utils

class TestDmxEnvironment(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'cmx.py')
        #self.env = 'env DB_FAMILY=Falcon DB_DEVICE=FM8 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/12.25'
        self.env = 'env DB_FAMILY=Ratonmesa DB_DEVICE=RTM DB_THREAD=RTMrevA0 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.4'
        #self.env = ''
        self.rc = cmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___dmx_environment___nomail(self):
        exitcode, stdout, stderr = self.rc('{} {} environment --nomail '.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        self.assertIn('DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.4', stdout)

    def test_002___dmx_environment_errorcode___list(self):
        exitcode, stdout, stderr = self.rc('{} {} environment errorcode --list ICL '.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        self.assertIn('ICLB01: ICM-LIBRARY does not exist', stdout)


    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
