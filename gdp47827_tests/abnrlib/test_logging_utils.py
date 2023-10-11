#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_logging_utils.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from future import standard_library
standard_library.install_aliases()
import unittest
from mock import patch
from datetime import date
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.loggingutils import *
import io
import logging
import logging.config


class TestLoggingUtils(unittest.TestCase):
    '''
    Tests the dmx.utillib.loggingutils library
    '''

    def test__get_arc_hard_quota_used(self):
        cmd = "arc-data-quota -h | grep 'of hard quota used' | awk '{print $6}'"
        exitcode, stdout, stderr = run_command(cmd)
        self.assertEqual(stdout.rstrip(), get_arc_hard_quota_used()) 

    def test__get_today_date_as_ymd(self):
        self.assertEqual(date.today().strftime("%Y%m%d"), get_today_date_as_ymd())

    @patch('dmx.utillib.loggingutils.os.path.exists', return_value=True)
    @patch('dmx.utillib.loggingutils.os.getppid', return_value='PPID')
    @patch.dict('dmx.utillib.loggingutils.os.environ', {'HOTEL':'HOTEL', 'HOSTNAME':'HOSTNAME'})
    @patch('dmx.utillib.loggingutils.get_today_date_as_ymdhms', return_value='20211112_HMS')
    @patch('dmx.utillib.loggingutils.get_today_date_as_ymd', return_value='20200202')
    @patch('dmx.utillib.loggingutils.run_command', return_value=(0, 'pass', 'pass'))
    def test__get_dmx_log_full_path(self, mock_run_cmd, mock_today_date, mock_today_datehms, mock_ppid, mock_path_exists):
        result = 'HOTEL/.dmxlog/20200202/dmx_{}_20200202_HOSTNAME_PPID_{}.log'.format(os.getenv("USER"), os.getenv("ARC_SITE"))
        self.assertEqual(result, get_dmx_log_full_path())
         
    def test__remove_log_max_num_equal(self):
        self.assertIsNone(remove_log(['data'],int('1')))

    def test__remove_log_max_num_bigger(self):
        self.assertIsNone(remove_log(['data'],int('3')))

    @patch('dmx.utillib.loggingutils.run_command', return_value=(0, 'pass', 'pass'))
    def test__remove_log_max_num_smaller(self, mock_run_cmd):
        self.assertIsNone(remove_log(['data'],int('0')))


if __name__ == '__main__':
    unittest.main()
