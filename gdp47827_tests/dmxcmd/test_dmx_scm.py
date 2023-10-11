#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_scm.py $
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
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setenv = 'env DB_THREAD=LTMrevA0 DB_DEVICE=LTM DB_FAMILY=Libertymesa DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.7'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_da_i16_dai16liotest1_2599'
        self.ip = 'dai16liotest1'
        self.del_icm = 'rtl'
        self.del_naa = 'rcxt'
        self.filename = '_for_dmx_scm_.txt'

    def tearDown(self):
        pass
   
    ### These tests are a string of tests which is interdependant, 
    ### any needs to be run sequencially in the correct order.
    ### - test_0xx ==> 'dmx scm ci' on an icm deliverable
    ### - test_1xx ==> 'dmx scm ci' on an naa deliverable

    def cleanup(self, ip, deliverable):
        indir = os.path.join(self.wsroot, ip, deliverable)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("xlp4 revert {}".format(self.filename))
            os.system("xlp4 delete {}".format(self.filename))
            os.system("xlp4 submit -d 'cleanup for dmxcmd/test_dmx_scm.py' {}".format(self.filename))
            os.system("rm -rf {}".format(self.filename))
            self.assertFalse(os.path.isfile(self.filename))


    ################################
    ### test_0xx
    ### icm deliverable
    ################################
    def test_001___cleanup___icm(self):
        self.cleanup(self.ip, self.del_icm)

    def test_002___dmx_scm_ci___icm(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_icm)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm ci --debug --desc "for regtest dmx scm ci" {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
            self.assertIn("headAction add", stdout2+stderr2)

    def test_003___dmx_scm_co___icm(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_icm)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm co --debug {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
            self.assertIn("action edit", stdout2+stderr2)

    def test_004___dmx_scm_revert___icm(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_icm)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm revert --debug {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
        self.assertIn("headAction add", stdout2+stderr2)

    def test_005___dmx_scm_delete___icm(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_icm)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm delete --desc "for regtest dmx scm ci" --debug {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
        self.assertIn("headAction delete", stdout2+stderr2)




    ################################
    ### test_1xx
    ### LD deliverable
    ################################
    def _test_101___cleanup___naa(self):
        self.cleanup(self.ip, self.del_naa)

    def _test_102___dmx_scm_ci___naa(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_naa)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm ci --debug --desc "for regtest dmx scm ci" {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
            self.assertIn("headAction add", stdout2+stderr2)

    def _test_103___dmx_scm_co___naa(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_naa)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm co --debug {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
            self.assertIn("action edit", stdout2+stderr2)

    def _test_104___dmx_scm_revert___naa(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_naa)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm revert --debug {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
        self.assertIn("headAction add", stdout2+stderr2)
    
    def _test_105___dmx_scm_delete___naa(self):
        indir = os.path.join(self.wsroot, self.ip, self.del_naa)
        with dmx.utillib.contextmgr.cd(indir):
            os.system("date > {}".format(self.filename))
            exitcode, stdout, stderr = self.rc('{} {} scm delete --desc "for regtest dmx scm ci" --debug {}'.format(self.setenv, self.dmx, self.filename), maxtry=1)
            print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat {}'.format(self.filename), maxtry=1)
        self.assertIn("headAction delete", stdout2+stderr2)


if __name__ == '__main__':
    unittest.main()
