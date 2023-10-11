#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_report_content.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxReportContent(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setsite = 'env DMX_GDPSITE=intel'
        self.setsite = ''
        
    def tearDown(self):
        pass
    
    def test_001___report_content___library(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -d ipspec -b dev'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = 'Project: Raton_Mesa, IP: rtmliotest2, Deliverable: ipspec, BOM: dev\n\tLast modified: 2022/04/01 15:48:03 (in server timezone)\n\tLibtype: ipspec, Library: dev, Release: \n'
        self.assertEqual(stdout, ans)

    def test_002___report_content___release(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -d ipspec -b REL1.0RTMrevA0__22ww135a'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = 'Project: Raton_Mesa, IP: rtmliotest2, Deliverable: ipspec, BOM: REL1.0RTMrevA0__22ww135a\n\tLast modified: 2022/04/01 15:48:08 (in server timezone)\n\tLibtype: ipspec, Library: dev, Release: REL1.0RTMrevA0__22ww135a\n'
        self.assertEqual(stdout, ans)

    def test_010___report_content___config(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = 'Project: Raton_Mesa, IP: rtmliotest2, BOM: REL1.0RTMrevA0__22ww135a\n\tLast modified: 2022/03/25 09:15:25 (in server timezone)\nRaton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2:ipspec@REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2:reldoc@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1@REL1.0RTMrevA0__22ww135a\n\n'
        self.assertEqual(stdout, ans)

    def test_011___report_content___config_hier(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --hier'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = 'Project: Raton_Mesa, IP: rtmliotest2, BOM: REL1.0RTMrevA0__22ww135a\n\tLast modified: 2022/03/25 09:15:25 (in server timezone)\nRaton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest2:ipspec@REL1.0RTMrevA0__22ww135c\n\tRaton_Mesa/rtmliotest2:reldoc@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1@REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1:ipspec@REL1.0RTMrevA0__22ww135a\n\t\tRaton_Mesa/rtmliotest1:reldoc@REL1.0RTMrevA0__22ww135d\n\n'
        self.assertEqual(stdout, ans)


    def test_012___report_content___config_hier_nodel(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --hier --no-del'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = 'Project: Raton_Mesa, IP: rtmliotest2, BOM: REL1.0RTMrevA0__22ww135a\n\tLast modified: 2022/03/25 09:15:25 (in server timezone)\nRaton_Mesa/rtmliotest2@REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1@REL1.0RTMrevA0__22ww135a\n\n'
        self.assertEqual(stdout, ans)


    def test_101___report_content_verbose___library(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b dev -d ipspec --verbose'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertEqual(stdout, '//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/...@now\n')

    def test_102___report_content_verbose___release(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a -d ipspec --verbose'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertEqual(stdout, '//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/...@87\n')

    def test_103___report_content_verbose___config(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a  --verbose'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertEqual(stdout, '//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@89\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/reldoc/dev/...@13\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/...@87\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/reldoc/dev/...@88\n')

    def test_103___report_content_verbose___config_release(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --verbose'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertEqual(stdout, '//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@89\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/reldoc/dev/...@13\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/...@87\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/reldoc/dev/...@88\n')

    def test_103___report_content_verbose___config_hier(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --hier --verbose'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertEqual(stdout, '//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@89\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest1/reldoc/dev/...@13\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/...@87\n//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/reldoc/dev/...@88\n')

    def test_105___report_content_flat___library(self):
        os.system('rm -rf __flat.txt')
        os.system('{} {} report content -p Raton_Mesa -i rtmliotest2 -d ipspec -b dev --flat __flat.txt'.format(self.setsite, self.dmx))
        _,stdout,_ = self.rc("cat __flat.txt")
        self.assertEqual(stdout, 'Raton_Mesa/rtmliotest2/ipspec/dev\n')

    def test_105___report_content_flat___release(self):
        os.system('rm -rf __flat.txt')
        os.system('{} {} report content -p Raton_Mesa -i rtmliotest2 -d ipspec -b REL1.0RTMrevA0__22ww135a --flat __flat.txt'.format(self.setsite, self.dmx))
        _,stdout,_ = self.rc("cat __flat.txt")
        self.assertEqual(stdout, 'Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135a\n')

    def test_105___report_content_flat___config(self):
        os.system('rm -rf __flat.txt')
        os.system('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --flat __flat.txt'.format(self.setsite, self.dmx))
        _,stdout,_ = self.rc("cat __flat.txt")
        self.assertEqual(stdout, 'Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\nRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\nRaton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c\nRaton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a\n')
        
    def test_110___report_content_csv(self):
        os.system('rm -rf __flat.txt')
        os.system('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a  --csv __flat.txt'.format(self.setsite, self.dmx))
        _,stdout,_ = self.rc("cat __flat.txt")
        self.assertEqual(stdout, 'project,variant,config,libtype,library,release,sub_configs\r\nRaton_Mesa,rtmliotest2,REL1.0RTMrevA0__22ww135a,,,,Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a\r\nRaton_Mesa,rtmliotest1,REL1.0RTMrevA0__22ww135a,,,,Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\r\nRaton_Mesa,rtmliotest1,REL1.0RTMrevA0__22ww135a,ipspec,,,\r\nRaton_Mesa,rtmliotest1,REL1.0RTMrevA0__22ww135d,reldoc,,,\r\nRaton_Mesa,rtmliotest2,REL1.0RTMrevA0__22ww135c,ipspec,,,\r\nRaton_Mesa,rtmliotest2,REL1.0RTMrevA0__22ww135a,reldoc,,,\r\n')

    def test_111___report_content_json(self):
        os.system('rm -rf __flat.txt')
        os.system('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a --json __flat.txt'.format(self.setsite, self.dmx))
        ans = {
            "Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a": {
                "deliverable": [
                    "Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a", 
                    "Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d"
                ], 
                "ip": []
            }, 
            "Raton_Mesa/rtmliotest2/REL1.0RTMrevA0__22ww135a": {
                "deliverable": [
                    "Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c", 
                    "Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a"
                ], 
                "ip": [
                    "Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a"
                ]
            }
        } 
        with open("__flat.txt") as f:
            ret = json.load(f)
        self.assertEqual(ret, ans)

    def test_120___report_content_file___given_immutable_pvc(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a -f rtmliotest2/ipspec/cell_names.txt'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertIn('//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/cell_names.txt#1 - add change 87', stdout)
        
    def test_120___report_content_file___given_mutable_pvc(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b dev -f rtmliotest2/ipspec/cell_names.txt'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertIn('//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/cell_names.txt', stdout)
        
    def test_122___report_content_file___given_pvlc(self):
        exitcode, stdout, stderr = self.rc('{} {} report content -p Raton_Mesa -i rtmliotest2 -b REL1.0RTMrevA0__22ww135a -d ipspec -f rtmliotest2/ipspec/cell_names.txt'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertIn('//depot/gdpxl/intel/Raton_Mesa/rtmliotest2/ipspec/dev/cell_names.txt#1 - add change 87', stdout)
        

if __name__ == '__main__':
    unittest.main()
