#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaseinputvalidation library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_releaseinputvalidation.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.ecolib.family import Family
from dmx.abnrlib.releaseinputvalidation import *

class TestReleaseInputValidation(unittest.TestCase):
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.verify_roadmap')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    def test_validate_roadmap_bad_roadmap(self, mock_get_family_for_thread, mock_verify_roadmap, mock_get_family_for_icmproject):
        '''
        Tests the validate_roadmap function when the roadmap is bad
        '''
        mock_verify_roadmap.return_value = False
        mock_get_family_for_icmproject.return_value = Family
        mock_get_family_for_thread.return_value = Family

        with self.assertRaises(RoadmapValidationError):
            validate_roadmap('project', 'milestone', 'thread')

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.verify_roadmap')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    def test_validate_roadmap_good_roadmap(self, mock_get_family_for_thread, mock_verify_roadmap, mock_get_family_for_icmproject):
        '''
        Tests the validate_roadmap function when the roadmap is good
        '''
        mock_verify_roadmap.return_value = True
        mock_get_family_for_icmproject.return_value = Family
        mock_get_family_for_thread.return_value = Family

        validate_roadmap('project', 'milestone', 'thread')

    @patch('dmx.abnrlib.releaseinputvalidation.AlteraName.is_label_valid')
    def test_validate_label_bad_label(self, mock_is_label_valid):
        '''
        Tests the validate_label function when the label is bad
        '''
        mock_is_label_valid.return_value = False

        with self.assertRaises(LabelValidationError):
            validate_label('label')

    @patch('dmx.abnrlib.releaseinputvalidation.AlteraName.is_label_valid')
    def test_validate_label_good_label(self, mock_is_label_valid):
        '''
        Tests the validate_label function when the label is good
        '''
        mock_is_label_valid.return_value = True
        validate_label('label')

    @patch('dmx.abnrlib.releaseinputvalidation.os.path.exists')
    def test_validate_waiver_files_do_not_exist(self, mock_exists):
        '''
        Tests the validate_waiver_files method when the waiver file path doesn't exist
        '''
        mock_exists.return_value = False

        with self.assertRaises(WaiverFileValidationError):
            validate_waiver_files(['waiver_file'])

    @patch('dmx.abnrlib.releaseinputvalidation.os.path.exists')
    def test_validate_waiver_files_do_exist(self, mock_exists):
        '''
        Tests the validate_waiver_files method when the waiver file path does exist
        '''
        mock_exists.return_value = True
        validate_waiver_files(['waiver_file'])

if __name__ == '__main__':
    unittest.main()



if __name__ == '__main__':
    unittest.main()
