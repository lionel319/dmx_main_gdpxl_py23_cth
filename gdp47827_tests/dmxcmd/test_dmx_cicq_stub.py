#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_cicq_stub.py $
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
import dmx.utillib.contextmgr

class TestDmxScm(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setenv = 'env DB_THREAD=LTMrevA0 DB_DEVICE=LTM DB_FAMILY=Libertymesa DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.7'

    def tearDown(self):
        pass
  
    def test_100___dmx_cicq_stub___no_options(self):
        with dmx.utillib.contextmgr.cd('/tmp'):
            infile = 'cicq.ini'
            os.system("rm -rf {}".format(infile))
            cmd = '{} {} cicq stub'.format(self.setenv, self.dmx)
            exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            self.assertTrue(os.path.isfile(infile))
            self.assertIn("cicq.ini template file donwloaded to ./cicq.ini", stdout+stderr)


    def _test_101___dmx_cicq_stub___with_options(self):
        ''' This test can be turned on once cicq-py23 is done. https://jira.devtools.intel.com/browse/PSGDMX-3214 '''
        with dmx.utillib.contextmgr.cd('/tmp'):
            infile = 'i10socfm.jtag_common.liotest2.cicq.ini'
            os.system("rm -rf {}".format(infile))
            cmd = '{} {} cicq stub -p i10socfm -i jtag_common -t liotest2'.format(self.setenv, self.dmx)
            exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            self.assertTrue(os.path.isfile(infile))
            self.assertIn("Successfully downloaded cicq.ini config file from i10socfm.jtag_common.liotest2 to i10socfm.jtag_common.liotest2.cicq.ini", stdout+stderr)





if __name__ == '__main__':
    unittest.main()
