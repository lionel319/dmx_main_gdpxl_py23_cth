#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr showconfig plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_printsize.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from future import standard_library
standard_library.install_aliases()
import os, sys
import unittest
from mock import patch
from io import StringIO
from tempfile import NamedTemporaryFile
import csv

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.printsize import PrintSize
from dmx.abnrlib.icmconfig import IcmConfig 
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.utillib.utils import run_command

class TestPrintSize(unittest.TestCase):

    def setUp(self):
        self.bundle_object = PrintSize('i10socfm', 'jtag_common', 'lint', 'REL5.0FM6revA0__18ww283a')
        self.bundle_object_no_deliverable = PrintSize('i10socfm', 'jtag_common','', 'REL5.0FM6revA0__18ww283a')
        self.dict_of_file = {'i10socfm/jtag_common/lint:filelist/jtag_common_base_stap.lint.f': {'changelist': '13401192', 'variant': 'jtag_common', 'library': 'dev', 'filename': 'jtag_common_base_stap.lint.f', 'project': 'i10socfm', 'release': '16', 'version': '10', 'directory': '//depot/icm/proj/i10socfm/jtag_common/lint/dev/filelist', 'operation': 'edit', 'type': 'text', 'libtype': 'lint'},'i10socfm/jtag_common/lint:jtag_common_base_stap.review_results/console.log': {'changelist': '13401192', 'variant': 'jtag_common', 'library': 'dev', 'filename': 'console.log', 'project': 'i10socfm', 'release': '16', 'version': '12', 'directory': '//depot/icm/proj/i10socfm/jtag_common/lint/dev/jtag_common_base_stap.review_results', 'operation': 'edit', 'type': 'text', 'libtype': 'lint'}}

    def test_calc_size_result_match(self):
        '''
        Tests the calc size when result is match icmp4 size result
        '''
        result = '//depot/da/infra/dmx/main/lib/python/dmx/abnrlib/flows/printconfig.py#11 12483 bytes '
        self.assertEqual(self.bundle_object.calc_size(result),12483)


    def test_calc_size_result_not_match(self):
        '''
        Tests the calc size when result does not match icmp4 size result
        '''
        result = 'xzcxz'
        with self.assertRaises(IndexError):
            self.bundle_object.calc_size(result),12483


    def test_calc_size_result_empty(self):
        '''
        Tests the calc size when result is ''
        '''
        result = ''
        self.assertEqual(self.bundle_object.calc_size(result),0)


    @patch('dmx.abnrlib.flows.printsize.PrintSize.calc_size')
    @patch('dmx.abnrlib.flows.printsize.run_command')
    def _test_run(self,mock_run_command,mock_calc_size):
        '''
        Tests the run with deliverable correct input''
        '''

        # Mock run_command
        mock_run_command.side_effect = [('0',"//depot/icm/proj/i10socfm/fmesram/lint/dev/run_fmesram_pls.csh#2 333 bytes\n//depot/icm/proj/i10socfm/fmesram/lint/dev/tnrwaivers.csv#31 1165 bytes",''),(0,'//depot/icm/proj/i10socfm/jtag_common/lint/dev/jtag_common_base_stap.review_results/console.log#12 133803 bytes','')]

        # Mock calc size
        # different output when calling calc_size multiple time
        mock_calc_size.side_effect = [4070,133803]

        self.assertEqual(self.bundle_object.run(),(137873,2))




if __name__ == '__main__':
    unittest.main()
