#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_overlay.py $
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
        ### Revert all opened files
        force_revert_exe = os.path.join(LIB, '..', '..', 'bin', '_force_revert.py')
        revert_cmd = "{} '//depot/gdpxl/intel/da_i16/dai16liotest1/*/for_regtest_dmx_overlay/...'  --debug".format(force_revert_exe)
        os.system(revert_cmd)
        revert_cmd = "{} '//depot/gdpxl/intel/da_i16/dai16liotest2/*/for_regtest_dmx_overlay2/...'  --debug".format(force_revert_exe)
        os.system(revert_cmd)

    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setenv = 'env DB_THREAD=LTMrevA0 DB_DEVICE=LTM DB_FAMILY=Libertymesa DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.7'

    def tearDown(self):
        pass
  
    def test_000___filespec_cant_be_used_with_deliverable___dash_d(self):
        cmd = '{} {} overlay -n -p da_i16 -i dai16liotest1 -d reldoc -sb snap-fortnr_1 -db for_regtest_dmx_overlay reldoc/tnrwaivers.csv'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn('--deliverable/--deliverable_filter cannot be used with filespec', stdout + stderr)

    def test_001___filespec_cant_be_used_with_deliverable___ip_colon(self):
        cmd = '{}; {} overlay -n -p da_i16 -i dai16liotest1:reldoc -sb snap-fortnr_1 -db for_regtest_dmx_overlay reldoc/tnrwaivers.csv'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn('--deliverable/--deliverable_filter cannot be used with filespec', stdout + stderr)


    ################################
    ### test_1xx
    ### icm deliverable
    ################################
    def test_101___overlay_icm___1(self):
        cmd = '{} {} overlay -p da_i16 -i dai16liotest1:reldoc -sb snap-fortnr_1 -db for_regtest_dmx_overlay --debug'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        exitode2, stdout2, stderr2 = self.rc('xlp4 fstat //depot/gdpxl/intel/da_i16/dai16liotest1/reldoc/for_regtest_dmx_overlay/tnrwaivers.csv', maxtry=1)
        self.assertIn("headAction delete", stdout2+stderr2)

    def test_102___overlay_icm___2(self):
        cmd = '{} {} overlay -p da_i16 -i dai16liotest1:reldoc -sb REL1.0LTMrevA0__22ww315a -db for_regtest_dmx_overlay --debug'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        exitode2, stdout2, stderr2 = self.rc('xlp4 fstat //depot/gdpxl/intel/da_i16/dai16liotest1/reldoc/for_regtest_dmx_overlay/tnrwaivers.csv', maxtry=1)
        self.assertIn("headAction branch", stdout2+stderr2)

    def test_103___overlay_icm___already_overlaid(self):
        cmd = '{} {} overlay -p da_i16 -i dai16liotest1:reldoc -sb REL1.0LTMrevA0__22ww315a -db for_regtest_dmx_overlay --debug'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("has been overlaid. Skipping", stdout+stderr)




    ################################
    ### test_2xx
    ### LD deliverable
    ################################
    def _test_201___overlay_naa___1(self):
        cmd = '{} {} overlay -p da_i16 -i dai16liotest1:reldoc -sb snap-fortnr_1 -db for_regtest_dmx_overlay --debug'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        exitode2, stdout2, stderr2 = self.rc('xlp4 fstat //depot/gdpxl/intel/da_i16/dai16liotest1/reldoc/for_regtest_dmx_overlay/tnrwaivers.csv', maxtry=1)
        self.assertIn("headAction delete", stdout2+stderr2)


    ################################
    ### test_3xx
    ### overlay Variant 
    ################################
    def test_301___overlay_variant___1(self):
        cmd = '{} {} overlay -p da_i16 -i dai16liotest2 -sb snap-2 -db for_regtest_dmx_overlay2 --hier --debug'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        for libtype in ['ipspec', 'bcmlib', 'reldoc']:
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat //depot/gdpxl/intel/da_i16/dai16liotest2/{}/for_regtest_dmx_overlay2/for_dmx_overlay_regtest.txt'.format(libtype), maxtry=1)
            self.assertIn("headAction branch", stdout2+stderr2)

    def test_302___overlay_variant___2(self):
        cmd = '{} {} overlay -p da_i16 -i dai16liotest2 -sb snap-1 -db for_regtest_dmx_overlay2 --hier --debug'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        for libtype in ['ipspec', 'bcmlib', 'reldoc']:
            exitode2, stdout2, stderr2 = self.rc('xlp4 fstat //depot/gdpxl/intel/da_i16/dai16liotest2/{}/for_regtest_dmx_overlay2/for_dmx_overlay_regtest.txt'.format(libtype), maxtry=1)
            self.assertIn("headAction delete", stdout2+stderr2)




if __name__ == '__main__':
    unittest.main()
