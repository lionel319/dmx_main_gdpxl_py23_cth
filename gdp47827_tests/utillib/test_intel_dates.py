#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_intel_dates.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys
from datetime import date, timedelta

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.intel_dates


class TestIntelDates(unittest.TestCase):

    def setUp(self):
        self.a = dmx.utillib.intel_dates
        self.dd = date(2022, 6, 30)

    def test_001___intel_weekday(self):
        ret = self.a.intel_weekday(self.dd)
        self.assertEqual(ret, 4)

    def test_002___intel_ww1_start_date(self):
        ret = self.a.intel_ww1_start_date(2022)
        self.assertEqual(ret, date(2021, 12, 26))

    def test_003___intel_calendar(self):
        ret = self.a.intel_calendar(self.dd)
        self.assertEqual(ret, (2022, 27, 4))

    def test_004___intel_ww_string_to_date(self):
        ret = self.a.intel_ww_string_to_date('2022WW27.4')
        self.assertEqual(ret, date(2022, 6, 30))

    def test_005___date_to_intel_ww_string(self):
        ret = self.a.date_to_intel_ww_string(self.dd)
        self.assertEqual(ret, '2022WW27.4')

if __name__ == '__main__':
    unittest.main()
