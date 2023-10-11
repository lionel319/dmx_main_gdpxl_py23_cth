#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_release_prel.py $
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

class TestDmxReleasePrel(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx')
        self.rc = dmx.utillib.utils.run_command
        self.dmxpath = os.path.join(LIB, 'dmx', 'tnrlib', 'release_runner.py')
        self.dmxdatapath = '/p/psg/flows/common/dmxdata/14.7'
        self.setenv = 'env DB_THREAD=LTMrevA0 DB_DEVICE=LTM DB_FAMILY=Libertymesa TV_MILESTONE=1.0 DMXREL_DMXPATH={} DMXREL_DMXDATAPATH={} DMXDATA_ROOT={}'.format(self.dmxpath, self.dmxdatapath, self.dmxdatapath)

    def tearDown(self):
        pass
 
    def test_000(self):
        exitcode, stdout, stderr = self.rc('{} env | grep DB_'.format(self.setenv))
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        #self.assertTrue(False)


    def test_100___dmx_release_prel___invalid_project(self):
        cmd = '{} {} release  --desc forregtest --syncpoint LIONEL -p _no_such_project_ -i dai16liotest2 -b dev -d prel_qpds'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("is not a valid project", stdout+stderr)

    def test_101___dmx_release_prel___invalid_variant(self):
        cmd = '{} {} release --desc forregtest --syncpoint LIONEL -p da_i16 -i _no_such_variant_ -b dev -d prel_qpds'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("da_i16/_no_such_variant_ is not a valid variant", stdout+stderr)

    def test_102___dmx_release_prel___invalid_bom(self):
        cmd = '{} {} release --desc forregtest --syncpoint LIONEL -p da_i16 -i dai16liotest1 -b _no_such_bom_ -d prel_qpds'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("da_i16/dai16liotest1@_no_such_bom_ does not exist", stdout+stderr)

    def test_103___dmx_release_prel___invalid_prel(self):
        cmd = '{} {} release --desc forregtest --syncpoint LIONEL -p da_i16 -i dai16liotest1 -b dev -d prel_nosuchview'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("Prel prel_nosuchview does not exist", stdout+stderr)

    def test_104___dmx_release_prel___hier_not_allow(self):
        cmd = '{} {} release -n --hier --desc forregtest --syncpoint LIONEL -p da_i16 -i dai16liotest1 -b dev -d prel_qpds'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        self.assertIn("Hierarchical release of prel are not supported", stdout+stderr)

    def test_105___dmx_release_prel___libtpye(self):
        cmd = '{} {} release --regmode --desc forregtest --syncpoint LIONEL -p da_i16 -i dai16liotest1 -b dev -d prel_qpds:ipspec -t LTMrevA0 -m 1.0'.format(self.setenv, self.dmx)
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        #self.assertTrue(bool(re.search("Release .*PREL1.0LTMrevA0--prel_qpds__.* created", stdout+stderr)))
        self.assertTrue(bool(re.search("Release .* created", stdout+stderr)))




if __name__ == '__main__':
    unittest.main()
