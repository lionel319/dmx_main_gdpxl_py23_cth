#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_report_diff.py $
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
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxReportDiff(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setsite = 'env DMX_GDPSITE=intel'
        self.setsite = ''
        
    def tearDown(self):
        '''
        snap-dev__22ww132a
        REL1.0RTMrevA0__22ww135a
        '''
        pass

    def test_001___report_diff___libtype___no_diff(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -d ipspec -b snap-fortnr_1 -b2 snap-cicq__rtmliotest1__gdpxltest4__22ww134a'.format(self.setsite, self.dmx), maxtry=1)
        print([exitcode, stdout, stderr])
        self.assertIn('Both bom are identical', stdout)

    def test_002___report_diff___libtype___got_diff(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -d ipspec -b snap-fortnr_1 -b2 snap-fortnr_2'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertIn('==== //depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/rtmliotest1.unneeded_deliverables.txt#1 (text) - //depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/rtmliotest1.unneeded_deliverables.txt#2 (text) ==== content', stdout)

    def test_003___report_diff___variant___got_diff(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -b snap-cicq__rtmliotest1__gdpxltest4__22ww134a -b2 REL1.0RTMrevA0__22ww135a'.format(self.setsite, self.dmx), maxtry=1)
        pprint([exitcode, stdout, stderr])
        ans = '# Project/IP                      BOM 1                                                                                                             BOM 2\n# Raton_Mesa/rtmliotest1          snap-cicq__rtmliotest1__gdpxltest4__22ww134a                                                                      REL1.0RTMrevA0__22ww135a\n# Project/IP/Deliverable          Lib/Rel/BOM                                                                                                       Lib/Rel/BOM\n! Raton_Mesa/rtmliotest1/ipspec   always_clean_gdpxltest4/snap-cicq__rtmliotest1__gdpxltest4__22ww134a/snap-cicq__rtmliotest1__gdpxltest4__22ww134a dev/REL1.0RTMrevA0__22ww135a/REL1.0RTMrevA0__22ww135a\n! Raton_Mesa/rtmliotest1/reldoc   always_clean_gdpxltest4/snap-cicq__rtmliotest1__gdpxltest4__22ww134a/snap-cicq__rtmliotest1__gdpxltest4__22ww134a dev/REL1.0RTMrevA0__22ww135d/REL1.0RTMrevA0__22ww135d\n'
        self.assertEqual(stdout, ans)

    def test_004___report_diff___libtype___include_files(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -d ipspec -p Raton_Mesa -i rtmliotest1 -b snap-fortnr_1 -b2 snap-cicq__rtmliotest1__gdpxltest4__22ww134a --include-files'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = '# Project/IP                      BOM 1                                                                                                             BOM 2\n# Raton_Mesa/rtmliotest1          snap-fortnr_1                                                                                                     snap-cicq__rtmliotest1__gdpxltest4__22ww134a\n# Project/IP/Deliverable          Lib/Rel/BOM                                                                                                       Lib/Rel/BOM\n! Raton_Mesa/rtmliotest1/ipspec   dev/snap-fortnr_1/snap-fortnr_1                                                                                   always_clean_gdpxltest4/snap-cicq__rtmliotest1__gdpxltest4__22ww134a/snap-cicq__rtmliotest1__gdpxltest4__22ww134a\nTo see the differences between files, run the following ICM command:\n  > xlp4 diff2 file#ver1 file#ver2\nFor example:\n  > xlp4 diff2 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#4 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#5\n'
        self.assertEqual(stdout, ans)

    def test_005___report_diff___html(self):
        '''
        Tested manually with the following command
        > env DMX_GDPSITE=intel ./bin/dmx.py report diff -p Raton_Mesa -i liotest1 -b snap-21ww062b -b2 snap-21ww062a --include-files --html
        ''' 
        pass

    def test_006___report_diff___tkdiff(self):
        '''
        Tested manually with the following command
        > env DMX_GDPSITE=intel ./bin/dmx.py report diff -p Raton_Mesa -i liotest1 -b snap-21ww062b -b2 snap-21ww062a --include-files --tkdiff
        ''' 
        pass

    def test_007___report_diff___filter_ips(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -b snap-fmx_dev__21ww321a -b2 snap-fmx_dev__21ww321b --filter-ips xxx'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        self.assertEqual(stdout, '')


    def test_008___report_diff___filter_deliverables___no_diff(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -b snap-1 -b2 REL1.0RTMrevA0__22ww135a --filter-deliverables ipspec --include-files'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = '# Project/IP                      BOM 1                                                 BOM 2\n# Raton_Mesa/rtmliotest1          snap-1                                                REL1.0RTMrevA0__22ww135a\n# Project/IP/Deliverable          Lib/Rel/BOM                                           Lib/Rel/BOM\nTo see the differences between files, run the following ICM command:\n  > xlp4 diff2 file#ver1 file#ver2\nFor example:\n  > xlp4 diff2 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#4 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#5\n'
        self.assertEqual(stdout, ans)
    
    def test_009___report_diff___filter_deliverables___got_diff(self):
        exitcode, stdout, stderr = self.rc('{} {} report diff -p Raton_Mesa -i rtmliotest1 -b snap-dev__22ww132a -b2 REL1.0RTMrevA0__22ww135a --filter-deliverables ipspec --include-files'.format(self.setsite, self.dmx), maxtry=1)
        print(stdout)
        ans = '# Project/IP                      BOM 1                                                 BOM 2\n# Raton_Mesa/rtmliotest1          snap-dev__22ww132a                                    REL1.0RTMrevA0__22ww135a\n# Project/IP/Deliverable          Lib/Rel/BOM                                           Lib/Rel/BOM\n! Raton_Mesa/rtmliotest1/ipspec   dev/snap-dev__22ww132a/snap-dev__22ww132a             dev/REL1.0RTMrevA0__22ww135a/REL1.0RTMrevA0__22ww135a\n+ Raton_Mesa/rtmliotest1/ipspec:rtmliotest1.unneeded_deliverables.txt\n+ Library                                                                               dev\n+ Version                                                                               2\nTo see the differences between files, run the following ICM command:\n  > xlp4 diff2 file#ver1 file#ver2\nFor example:\n  > xlp4 diff2 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#4 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#5\n'
        self.assertEqual(stdout, ans)
    


if __name__ == '__main__':
    unittest.main()
