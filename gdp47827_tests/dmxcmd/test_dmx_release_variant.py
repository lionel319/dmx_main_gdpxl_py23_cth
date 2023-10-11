#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_release_variant.py $
# $Revision: #3 $
# $Change: 7480573 $
# $DateTime: 2023/02/12 23:02:19 $
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
import dmx.utillib.contextmgr

class TestDmxReleaseVariant(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.dmxpath = os.path.join(LIB, 'dmx', 'tnrlib', 'release_runner.py')
        self.dmxdatapath = '/p/psg/flows/common/dmxdata/14.7'
        self.setenv = 'env DB_THREAD=LTMrevA0 DB_DEVICE=LTM DB_FAMILY=Libertymesa DMXREL_DMXPATH={} DMXREL_DMXDATAPATH={} DMXDATA_ROOT={}'.format(self.dmxpath, self.dmxdatapath, self.dmxdatapath)

    def tearDown(self):
        pass
  
    def test_100___dmx_release_variant___already_released(self):
        cmd = '{} {} release -p da_i16 -i dai16liotest2 -b for_regtest_dmx_release -m 1.0 -t LTMrevA0 --debug --regmode --syncpoint LIONEL --desc testing_py23'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("da_i16/dai16liotest2@REL1.0LTMrevA0__22ww315a has already been released and has identical content to da_i16/dai16liotest2/for_regtest_dmx_release", stdout+stderr)

    def test_101___dmx_release_variant___successful(self):
        cmd = '{} {} release -p da_i16 -i dai16liotest2 -b for_regtest_dmx_release2 -m 1.0 -t LTMrevA0 --debug --regmode --syncpoint LIONEL --desc testing_py23'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertTrue(bool(re.search("Release .* created", stdout+stderr)))




if __name__ == '__main__':
    unittest.main()
