#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr createsnapshot plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_bomflatten.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
from mock import Mock, PropertyMock, patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.createconfig import *
from dmx.abnrlib.icm import ICManageCLI, convert_altera_config_name_to_icm
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.config_factory import ConfigFactory 
from dmx.abnrlib.flows.bomflatten import BomFlatten, BomFlattenError
import tempfile

class TestBomFlatten(unittest.TestCase):
    '''
    Tests the createconfig abnr command
    '''

    def setUp(self):
        self.project = 'i16soc'
        self.ip = 'i16socwplimtest1'
        self.bom = 'top_hier'
        self.dstbom= 'flatten_bom'
        self.runner = BomFlatten(self.project, self.ip, self.bom, self.dstbom)
        self.config= self.runner.get_config_tree()

    def test_010__get_config_tree(self):        
        result = ConfigFactory.create_from_icm(self.project, self.ip, self.bom) 
        self.assertEqual(result, self.runner.get_config_tree())

    def test_020__get_root_config(self):
        all_parent_config = self.runner.get_parent_config(self.config, self.dstbom) 
        result =  IcmConfig(self.dstbom, self.project, self.ip, [])
        self.assertEqual(result, self.runner.get_root_config(all_parent_config))

    @patch('dmx.abnrlib.icmconfig.IcmConfig.save', return_value=True)
    def test_030__create_config_of_flatten_bom(self, mock_save):
        self.assertEqual(None, self.runner.create_config_of_flatten_bom(self.config))

    def test_040__get_parent_config(self):
        result1 =  IcmConfig(self.dstbom, 'da_i16', 'cdclib')
        result2 =  IcmConfig(self.dstbom, 'da_i16', 'dai16liotest1')
        result3 =  IcmConfig(self.dstbom, 'i16soc', 'i16socwplimtest1')
        all_result = [result2, result3, result1]
    #    py2_result = [result1, result2, result3]

        print(self.runner.get_parent_config(self.config, self.dstbom))
        for result in all_result:
            self.assertIn(result, self.runner.get_parent_config(self.config, self.dstbom))

    def test_050__run_fail(self):
        with self.assertRaises(BomFlattenError):
            print(self.runner.run())

    @patch('dmx.abnrlib.icmconfig.IcmConfig.save', return_value=True)
    def test_050__run_pass(self, mock_save):
        self.project = 'i16soc'
        self.ip = 'i16socwplimtest1'
        self.bom = 'top_hier'
        self.dstbom= 'unittest_flatten_bom'
        self.runner = BomFlatten(self.project, self.ip, self.bom, self.dstbom)
        
        self.assertEqual(None, self.runner.run())


if __name__ == '__main__':
    unittest.main()
