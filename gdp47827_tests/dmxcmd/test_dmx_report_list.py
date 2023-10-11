#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_report_list.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxReportList(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setsite = 'env DMX_GDPSITE=intel'
        self.setsite = ''
        
    def tearDown(self):
        pass
    
    def test_001___report_list___p_wildcard(self):
        exitcode, stdout, stderr = self.rc('{} {} report list -p '.format(self.setsite, self.dmx), maxtry=1)
        ans = 'Raton_Mesa'
        pprint([exitcode, stdout, stderr])
        self.assertIn(ans, stdout)

    def test_001___report_list___p_i10socfm(self):
        exitcode, stdout, stderr = self.rc('{} {} report list -p Raton_Mesa'.format(self.setsite, self.dmx), maxtry=1)
        self.assertEqual(stdout, 'Category: /intel\nRaton_Mesa\n\nFound 1 match\n')

    def test_002___report_list___p_wildcard_i_liotest4(self):
        exitcode, stdout, stderr = self.rc('{} report list -p -i rtmliotest1'.format(self.dmx), maxtry=1)
        self.assertEqual(stdout, 'Project/IP:\nRaton_Mesa/rtmliotest1\nFound 1 match\n')

    def test_002___report_list___p_i10socfm_i_liotest4(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1'.format(self.dmx), maxtry=1)
        self.assertEqual(stdout, 'Project/IP:\nRaton_Mesa/rtmliotest1\nFound 1 match\n')

    def test_003___report_list___p_i10socfm_i_liotest4_b_wildcard(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1 -b'.format(self.dmx), maxtry=1)
        self.assertIn('Raton_Mesa/rtmliotest1@dev', stdout)

    def test_003___report_list___p_i10socfm_i_liotest1_b_dev(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1 -b dev'.format(self.dmx), maxtry=1)
        self.assertEqual(stdout, 'Project/IP@BOM:\nRaton_Mesa/rtmliotest1@dev\nFound 1 match\n')
    
    def test_004___report_list___p_i10socfm_i_liotest4__d_wildcard(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1 -d'.format(self.dmx), maxtry=1)
        pprint([exitcode, stdout, stderr])
        self.assertIn('Project/IP:Deliverable:', stdout)
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec', stdout)
        self.assertIn('Raton_Mesa/rtmliotest1:reldoc', stdout)

    def test_004___report_list___p_i10socfm_i_liotest4__d_ipspec(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1 -d ipspec'.format(self.dmx), maxtry=1)
        self.assertEqual(stdout, '''Project/IP:Deliverable:
Raton_Mesa/rtmliotest1:ipspec
Found 1 match
''')
    
    def test_005___report_list___p_i10socfm_i_liotest4__d_ipspec_b_wildcard(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1 -d ipspec -b '.format(self.dmx), maxtry=1)
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec@dev', stdout)
 
    
    def test_005___report_list___p_i10socfm_i_liotest4_d_ipspec_b_fmx_dev(self):
        exitcode, stdout, stderr = self.rc('{} report list -p Raton_Mesa -i rtmliotest1 -d ipspec -b dev'.format(self.dmx), maxtry=1)
        self.assertEqual(stdout, '''Project/IP:Deliverable@BOM:
Raton_Mesa/rtmliotest1:ipspec@dev
Found 1 match
''')

    def test_006___report_list___wildcards_and_props(self):
        exitcode, stdout, stderr = self.rc("{} report list -p '*ato*' -i *'liot*1' -d ipspec -b '*e*' --prop ".format(self.dmx), maxtry=1)
        print(stdout)
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec@dev\n', stdout)
       
    def test_007___report_list___wildcards_and_props_and_switches(self):
        exitcode, stdout, stderr = self.rc("{} report list -p '*ato*' -i '*liot*' -d ipspec -b '*e*' --prop ".format(self.dmx), maxtry=1)
        print(stdout)
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec@dev\n', stdout)
        
    def test_008___report_list___regex(self):
        exitcode, stdout, stderr = self.rc("{} report list -p Raton_Mesa -i 'rtmlio(test)?[0-5]' --regex".format(self.dmx), maxtry=1)
        print(exitcode, stdout, stderr)
        self.assertIn('Raton_Mesa/rtmliotest1\n', stdout)
        


if __name__ == '__main__':
    unittest.main()
