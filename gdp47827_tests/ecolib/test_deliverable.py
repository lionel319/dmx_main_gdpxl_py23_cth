#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_deliverable.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
from builtins import str
from builtins import range
import unittest
import inspect
import os
import sys
from mock import patch
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.ecolib.deliverable import Deliverable, DeliverableError
import dmx.ecolib.checker

class TestDeliverable(unittest.TestCase):
    def setUp(self):
        self.family = 'Falcon'
        self.deliverable = 'rtl'
        self.producer = 'IP'
        self.consumer = 'FCI'
        self.successor = 'lint'
        self.pattern = 'ip_name/rtl/block_function/....v'
        self.filelist = 'ip_name/rtl/filelists/syn/cell_name.f'
        self.roadmap = 'FM6'
        self.milestone = '3.0'
        self.Deliverable = Deliverable(self.family, self.deliverable, roadmap=self.roadmap)


    def test_deliverable_properties(self):
        '''
        Tests the Deliverable object properties
        '''
        self.assertEqual(self.Deliverable.family, self.family)           
        self.assertEqual(self.Deliverable.deliverable, self.deliverable)
        self.assertIn(self.producer, self.Deliverable.producer)
        self.assertIn(self.consumer, self.Deliverable.consumer)
        self.assertIn(self.successor, self.Deliverable.successor)
        self.assertIn(self.pattern, list(self.Deliverable.pattern.keys()))

    def test__preload(self):
        self.Deliverable._preload()
        print(self.Deliverable._checkers)
        checkers = [x.checkname for x in self.Deliverable._checkers]
        self.assertIn('rtl_name_check', checkers)        

    def test_get_patterns(self):
        patterns = list(self.Deliverable.get_patterns().keys())
        self.assertIn(self.pattern, patterns)

    def test_get_filelists(self):
        filelists = list(self.Deliverable.get_filelists().keys())
        self.assertIn(self.filelist, filelists)

    def test_get_milkyway(self):
        milkyway = list(self.Deliverable.get_milkyway().keys())
        self.assertEqual([], milkyway)

    def test_get_manifest(self):
        manifest = self.Deliverable.get_manifest()
        self.assertIn(self.successor, manifest[0])
        self.assertIn(self.producer, manifest[2])
        self.assertIn(self.consumer, manifest[3])
        self.assertIn(self.pattern, list(manifest[7].keys()))
        self.assertIn(self.filelist, list(manifest[8].keys()))

    def test__get_checkers(self):
        checkers = [x.checkname for x in self.Deliverable._get_checkers()[self.roadmap][self.milestone]]
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers(self):
        checkers = [x.checkname for x in self.Deliverable.get_checkers()]        
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_regex_cannot_compile(self):
        with self.assertRaises(DeliverableError):
            self.Deliverable.get_checkers(flow_filter='!@#$%^&*(')        
        with self.assertRaises(DeliverableError):
            self.Deliverable.get_checkers(subflow_filter='!@#$%^&*(')     
        with self.assertRaises(DeliverableError):
            self.Deliverable.get_checkers(checker_filter='!@#$%^&*(')                                 
    def test_get_checkers_with_flow(self):
        checkers = [x.checkname for x in self.Deliverable.get_checkers(flow_filter='rtl')]  
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_with_subflow(self):
        checkers = [x.checkname for x in self.Deliverable.get_checkers(subflow_filter='name')]  
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_with_checkname(self):
        checkers = [x.checkname for x in self.Deliverable.get_checkers(checker_filter='rtl_name_check')]  
        self.assertIn('rtl_name_check', checkers)

    def test_get_checkers_with_prel(self):
        checkers = [x.checkname for x in self.Deliverable.get_checkers(prel_filter='prel_stamod')]  
        self.assertIn('rtl_name_check', checkers)

    def test_has_checker(self):
        self.assertTrue(self.Deliverable.has_checker('rtl', 'name', 'rtl_name_check'))

    def test_has_no_checker(self):
        self.assertFalse(self.Deliverable.has_checker('does', 'not', 'exist'))

    def test_get_checker(self):
        checker = self.Deliverable.get_checker('rtl', 'name', 'rtl_name_check')        
        self.assertEqual('rtl_name_check', checker.checkname)

    def test_get_non_existing_checker(self):
        with self.assertRaises(DeliverableError):
            self.Deliverable.get_checker('does', 'not', 'exist')        
       
    def test_get_checker_invalid_character(self):
        with self.assertRaises(DeliverableError):
            self.Deliverable.get_checker('@#', '@#', '#$')        

    def test_get_short_description(self):
        self.Deliverable._description = 'Description (ShortDescription: testing short description) test'
        desc = self.Deliverable.get_short_description()
        self.assertEqual(desc, "testing short description")

        self.Deliverable._description = 'Description (ShortDescription: testing (short) description) test'
        desc = self.Deliverable.get_short_description()
        self.assertEqual(desc, "testing (short) description")

        self.Deliverable._description = 'Description (ShortDescription: testing (short) (desc)ription) test'
        desc = self.Deliverable.get_short_description()
        self.assertEqual(desc, "testing (short) (desc)ription")


    ################################################################################
    ### For PREL/Iptypes tests
    @patch('dmx.ecolib.checker.Checker.get_check_info')
    def _mock_checkers(self, mock):
        milestone = {self.roadmap:[self.milestone,99]}
        mock.side_effect = [
            #(checkname, deliverable, wrapper_name, documentation, dependencies, type, user, checker_execution, audit_verification, milestones, iptypes, prels)
            ['rtl_0', 'rtl', 'rtl_1', 'doc', 'dep', 'c', 'yltan', True, True, milestone, ['custom', 'asic'], ['prel_1', 'prel_4'], 'cell'],
            ['rtl_1', 'rtl', 'rtl_2', 'doc', 'dep', 'c', 'yltan', True, True, milestone, ['custom'], ['prel_2'], 'cell'],
            ['rtl_2', 'rtl', 'rtl_3', 'doc', 'dep', 'c', 'yltan', True, True, milestone, ['asic'], ['prel_3'], 'cell'],
            ['rtl_3', 'rtl', 'rtl_4', 'doc', 'dep', 'c', 'yltan', True, True, milestone, [], ['prel_1', 'prel_2'], 'cell'],
            ['rtl_4', 'rtl', 'rtl_5', 'doc', 'dep', 'c', 'yltan', True, True, milestone, ['asic'], [], 'cell'],
            ['rtl_5', 'rtl', 'rtl_6', 'doc', 'dep', 'c', 'yltan', True, True, milestone, ['asic'], None, 'cell'],
        ]
        self.checkers = []
        for i in range(6):
            c = dmx.ecolib.checker.Checker(self.family, "rtl", str(i), roadmap=self.roadmap)
            self.checkers.append(c)
        self.Deliverable._checkers = {
            self.roadmap: {self.milestone: self.checkers, '99': self.checkers}
        }

    def test_get_checkers___no_filter(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers()
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_0', 'rtl_1', 'rtl_2', 'rtl_3', 'rtl_4', 'rtl_5']
        self.assertEqual(ref, ans)

    def test_get_checkers___prel_filter_prel_4(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers(prel_filter='^prel_4$')
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_0', 'rtl_5']
        self.assertEqual(ref, ans)

    def test_get_checkers___prel_filter_prel_1(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers(prel_filter='^prel_1$')
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_0', 'rtl_3', 'rtl_5']
        self.assertEqual(ref, ans)

    def test_get_checkers___iptype_filter_asic(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers(iptype_filter='^asic$')
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_0', 'rtl_2', 'rtl_3', 'rtl_4', 'rtl_5']
        self.assertEqual(ref, ans)

    def test_get_checkers___iptype_filter_custom(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers(iptype_filter='^custom$')
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_0', 'rtl_1', 'rtl_3']
        self.assertEqual(ref, ans)

    def test_get_checkers___iptype_n_prel_filter_custom_prel_2(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers(iptype_filter='^custom$', prel_filter='^prel_2$')
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_1', 'rtl_3']
        self.assertEqual(ref, ans)

    def test_get_checkers___iptype_n_prel_filter_asic_prel_2(self):
        self._mock_checkers()
        ret = self.Deliverable.get_checkers(iptype_filter='^asic$', prel_filter='^prel_2$')
        ref = sorted([c.checkname for c in ret])
        ans = ['rtl_3', 'rtl_5']
        self.assertEqual(ref, ans)

    ################################################################################
    ### For PREL/Iptypes tests
    def _mock_patterns(self):
        self.Deliverable._pattern = {
            '0.txt':{'iptypes':['custom', 'asic'], 'prels':['prel_1', 'prel_4']},
            '1.txt':{'iptypes':['custom'], 'prels':['prel_2']},
            '2.txt':{'iptypes':['asic'], 'prels':['prel_3']},
            '3.txt':{'iptypes':[], 'prels':['prel_1', 'prel_2']},
            '4.txt':{'iptypes':['asic'], 'prels':[]},
            '5.txt':{'iptypes':['asic'] },
        }

    def test_get_patterns___no_filter(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns()
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['0.txt', '1.txt', '2.txt', '3.txt', '4.txt', '5.txt'])

    def test_get_patterns___prel_filter_prel_4(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns(prel_filter="^prel_4$")
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['0.txt', '5.txt'])

    def test_get_patterns___prel_filter_prel_1(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns(prel_filter="^prel_1$")
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['0.txt', '3.txt', '5.txt'])

    def test_get_patterns___iptype_filter_asic(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns(iptype_filter="^asic$")
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['0.txt', '2.txt', '3.txt', '4.txt', '5.txt'])

    def test_get_patterns___iptype_filter_custom(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns(iptype_filter="^custom$")
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['0.txt', '1.txt', '3.txt'])

    def test_get_patterns___iptype_n_prel_filter_custom_prel_2(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns(iptype_filter="^custom$", prel_filter='^prel_2$')
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['1.txt', '3.txt'])

    def test_get_patterns___iptype_n_prel_filter_asic_prel_2(self):
        self._mock_patterns()
        ret = self.Deliverable.get_patterns(iptype_filter="^asic$", prel_filter='^prel_2$')
        ref = sorted(ret.keys())
        self.assertEqual(ref, ['3.txt', '5.txt'])



if __name__ == '__main__':
    logging.basicConfig(format="%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s", level=logging.DEBUG)
    unittest.main()
