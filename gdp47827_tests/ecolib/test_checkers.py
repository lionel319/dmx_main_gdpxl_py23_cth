#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_checkers.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
#os.environ['DMXDB'] = 'DMXTEST'
#os.environ['DMXDATA_ROOT'] = '/p/psg/flows/common/dmxdata/main_gdpxl'
from dmx.ecolib.checker import Checker

class TestChecker(unittest.TestCase):
    def setUp(self):
        self.family = 'Falcon'
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_DEVICE'] = 'FM8'

        '''
        self.flow = 'rtl'
        self.subflow = 'name'
        self.Checker = Checker(self.family, self.flow, self.subflow)
        self.checkname = 'rtl_name_check'
        self.wrapper_name = 'rtl__name__dc_check'
        self.checker_execution = True
        self.deliverable = 'rtl'
        self.documentation = 'http://sw-web.altera.com/tools/icd_cad/audit/current/doc/html/'
        self.activated = {'FM6': ['2.0', '3.0', '4.0', '5.0', '99']}
        self.type = 'd'
        self.user = 'rmayr'
        self.dependencies = ''
        self.iptypes = []
        self.checkerlevel = 'cell'
        '''

    def tearDown(self):
        os.environ['DB_DEVICE'] = self.db_device

    def _get_checker(self):
        family = 'Ratonmesa'
        db_device = os.environ['DB_DEVICE']
        os.environ['DB_DEVICE'] = 'RTM'

        flow = 'cdl'
        subflow = ''
        c = Checker(family, flow, subflow)
        return c


    def test_zz_checker_properties(self):
        c = self._get_checker()
        print(c)
        self.assertEqual(c.family, 'Ratonmesa')           
        self.assertEqual(c.flow, 'cdl') 
        self.assertEqual(c.subflow, '')        
        self.assertEqual(c.checkname, 'audit_data_merge')
        self.assertEqual(c.deliverable, 'cdl')
        self.assertEqual(c.type, 'c')

    def test_zz_get_check_info(self):
        c = self._get_checker()
        info = c.get_check_info()
        self.assertEqual(13, len(info))
        checkname, deliverable, wrapper_name, documentation, dependencies, type, user, checker_execution, audit_verification, activated, iptypes, prels, checkerlevel = info
        self.assertEqual(checkname, c.checkname)
        self.assertEqual(deliverable.lower(), c.deliverable)
        self.assertEqual(wrapper_name, c.wrapper_name)
        self.assertEqual(checker_execution, c.checker_execution)
        self.assertEqual(documentation, c.documentation)
        self.assertEqual(type, c.type)
        self.assertEqual(user, c.user)
        self.assertEqual(dependencies, c.dependencies)
        self.assertEqual(iptypes, c.iptypes)
        self.assertEqual(prels, None)
        self.assertEqual(checkerlevel, c.checkerlevel)

    ############################################################
    ### Test correct behavior of prel/iptype parsing
    def _mock_loader(self):
        return {
            u'sta_1': {u'Audit Verification': True, u'Wrapper Name': u'sta__cc_check', u'Milestones': {u'FM6': [u'3.0', u'4.0', u'5.0', '99'], u'FM5': [u'4.0', u'5.0', '99'], u'FM3': [u'4.0', u'5.0', '99'], u'FM8': [u'4.0', u'5.0', '99'], u'FM6B': [u'4.0', u'5.0', '99']}, u'Documentation': u'https', u'Flow': u'sta', u'SubFlow': u'1', u'Unix Userid': u'kychng', u'Deliverable': u'sta', u'Check Name': u'r2g2', u'Owner Email': u'kok.yong.chng@intel.com', u'Prels': [u'prel_1', u'prel_4'], u'Dependencies': u'', u'Type': u'c', u'Iptypes': [u'custom', u'asic'], u'Checker Execution': False}, 
            u'sta_2': {u'Audit Verification': True, u'Wrapper Name': u'sta__cc_check', u'Milestones': {u'FM6': [u'3.0', u'4.0', u'5.0', '99'], u'FM5': [u'4.0', u'5.0', '99'], u'FM3': [u'4.0', u'5.0', '99'], u'FM8': [u'4.0', u'5.0', '99'], u'FM6B': [u'4.0', u'5.0', '99']}, u'Documentation': u'https', u'Flow': u'sta', u'SubFlow': u'2', u'Unix Userid': u'kychng', u'Deliverable': u'sta', u'Check Name': u'r2g2', u'Owner Email': u'kok.yong.chng@intel.com', u'Prels': [u'prel_2'], u'Dependencies': u'', u'Type': u'c', u'Checker Execution': False}, 
            u'sta_3': {u'Audit Verification': True, u'Wrapper Name': u'sta__cc_check', u'Milestones': {u'FM6': [u'3.0', u'4.0', u'5.0', '99'], u'FM5': [u'4.0', u'5.0', '99'], u'FM3': [u'4.0', u'5.0', '99'], u'FM8': [u'4.0', u'5.0', '99'], u'FM6B': [u'4.0', u'5.0', '99']}, u'Documentation': u'https', u'Flow': u'sta', u'SubFlow': u'3', u'Unix Userid': u'kychng', u'Deliverable': u'sta', u'Check Name': u'r2g2', u'Owner Email': u'kok.yong.chng@intel.com', u'Prels': [u'prel_3'], u'Dependencies': u'', u'Type': u'c', u'Iptypes': [u'asic'], u'Checker Execution': False}, 
            u'sta_4': {u'Audit Verification': True, u'Wrapper Name': u'sta__cc_check', u'Milestones': {u'FM6': [u'3.0', u'4.0', u'5.0', '99'], u'FM5': [u'4.0', u'5.0', '99'], u'FM3': [u'4.0', u'5.0', '99'], u'FM8': [u'4.0', u'5.0', '99'], u'FM6B': [u'4.0', u'5.0', '99']}, u'Documentation': u'https', u'Flow': u'sta', u'SubFlow': u'4', u'Unix Userid': u'kychng', u'Deliverable': u'sta', u'Check Name': u'r2g2', u'Owner Email': u'kok.yong.chng@intel.com', u'Prels': [u'prel_1', u'prel_2'], u'Dependencies': u'', u'Type': u'c', u'Iptypes': [], u'Checker Execution': False}, 
            u'sta_5': {u'Audit Verification': True, u'Wrapper Name': u'sta__cc_check', u'Milestones': {u'FM6': [u'3.0', u'4.0', u'5.0', '99'], u'FM5': [u'4.0', u'5.0', '99'], u'FM3': [u'4.0', u'5.0', '99'], u'FM8': [u'4.0', u'5.0', '99'], u'FM6B': [u'4.0', u'5.0', '99']}, u'Documentation': u'https', u'Flow': u'sta', u'SubFlow': u'5', u'Unix Userid': u'kychng', u'Deliverable': u'sta', u'Check Name': u'r2g2', u'Owner Email': u'kok.yong.chng@intel.com', u'Prels': [], u'Dependencies': u'', u'Type': u'c', u'Iptypes': [u'asic'], u'Checker Execution': False},
            u'sta_6': {u'Audit Verification': True, u'Wrapper Name': u'sta__cc_check', u'Milestones': {u'FM6': [u'3.0', u'4.0', u'5.0', '99'], u'FM5': [u'4.0', u'5.0', '99'], u'FM3': [u'4.0', u'5.0', '99'], u'FM8': [u'4.0', u'5.0', '99'], u'FM6B': [u'4.0', u'5.0', '99']}, u'Documentation': u'https', u'Flow': u'sta', u'SubFlow': u'6', u'Unix Userid': u'kychng', u'Deliverable': u'sta', u'Check Name': u'r2g2', u'Owner Email': u'kok.yong.chng@intel.com', u'Dependencies': u'', u'Type': u'c', u'Iptypes': [u'asic'], u'Checker Execution': False}, 
        }

    @patch('dmx.ecolib.loader.load_checkers')
    def test_make_sure_iptype_and_prel_are_parsed_correctly___got_iptypes_got_prels(self, mock):
        mock.return_value = self._mock_loader()
        c = Checker('Falcon', 'sta' , '1')
        self.assertEqual(c.iptypes, ['custom', 'asic'])
        self.assertEqual(c.prels, ['prel_1', 'prel_4'])

    @patch('dmx.ecolib.loader.load_checkers')
    def test_make_sure_iptype_and_prel_are_parsed_correctly___got_iptypes_no_prels(self, mock):
        mock.return_value = self._mock_loader()
        c = Checker('Falcon', 'sta' , '6')
        self.assertEqual(c.iptypes, ['asic'])
        self.assertEqual(c.prels, None)

    @patch('dmx.ecolib.loader.load_checkers')
    def test_make_sure_iptype_and_prel_are_parsed_correctly___got_iptypes_empty_prels(self, mock):
        mock.return_value = self._mock_loader()
        c = Checker('Falcon', 'sta' , '5')
        self.assertEqual(c.iptypes, ['asic'])
        self.assertEqual(c.prels, [])

    @patch('dmx.ecolib.loader.load_checkers')
    def test_make_sure_iptype_and_prel_are_parsed_correctly___no_iptypes_got_prels(self, mock):
        mock.return_value = self._mock_loader()
        c = Checker('Falcon', 'sta' , '2')
        self.assertEqual(c.iptypes, [])
        self.assertEqual(c.prels, ['prel_2'])

    @patch('dmx.ecolib.loader.load_checkers')
    def test_make_sure_iptype_and_prel_are_parsed_correctly___empty_iptypes_got_prels(self, mock):
        mock.return_value = self._mock_loader()
        c = Checker('Falcon', 'sta' , '4')
        self.assertEqual(c.iptypes, [])
        self.assertEqual(c.prels, ['prel_1', 'prel_2'])

if __name__ == '__main__':
    unittest.main()
