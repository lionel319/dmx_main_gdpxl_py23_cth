#!/usr/intel/pkgs/python3/3.9.6/bin/python3

# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/gdp47827_tests/cmxcmd/test_cmx_report.py $
# $Revision: #2 $
# $Change: 7464762 $
# $DateTime: 2023/01/31 17:48:52 $
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

class TestCmxReport(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'cmx.py')
        #self.env = 'env DB_FAMILY=Falcon DB_DEVICE=FM8 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/12.25'
        self.env = 'env DB_FAMILY=Ratonmesa DB_DEVICE=RTM DB_THREAD=RTMrevA0 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.4'
        #self.env = ''
        self.rc = cmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___cmx_report_content___config(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'Project: Raton_Mesa, IP: rtmliotest2, BOM: REL1.0RTMrevA0__22ww135a\n\tLast modified: 2022/03/25 09:15:25 (in server timezone)\nRaton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2:ipspec@REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2:reldoc@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1@REL1.0RTMrevA0__22ww135a\n\n'
        self.assertEqual(ans, stdout)

    def test_010___cmx_report_diff___libtype___got_diff(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -d ipspec -b snap-fortnr_1 -b2 snap-fortnr_2'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        self.assertIn('==== //depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/rtmliotest1.unneeded_deliverables.txt#1 (text) - //depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/rtmliotest1.unneeded_deliverables.txt#2 (text) ==== content', stdout)
        

    def test_020___cmx_report_list___p_wildcard(self):
        exitcode, stdout, stderr = self.rc('{} {} report list -p '.format(self.env, self.dmx), maxtry=1)
        ans = 'Raton_Mesa'
        self._print(exitcode, stdout, stderr)
        self.assertIn(ans, stdout)


    def test_030___cmx_report_owner___variant(self):
        exitcode, stdout, stderr = self.rc('{} report owner -p Raton_Mesa -i rtmliotest1'.format(self.dmx), maxtry=1)
        self.assertIn('Owner: lionelta', stdout)
        

    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
