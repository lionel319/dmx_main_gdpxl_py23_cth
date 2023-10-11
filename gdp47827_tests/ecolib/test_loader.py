#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_loader.py $
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
from dmx.ecolib.loader import *

class TestLoader(unittest.TestCase):
    def setUp(self):
        self.family = 'Falcon'

    def test_load_roadmaps(self):
        dict = load_roadmaps(self.family)
        self.assertIn('FM6', dict.keys())
        self.assertIn('99', dict['FM6'])
        self.assertEqual(6, len(dict['FM6']))

    def test_load_roadmaps_fail(self):
        with self.assertRaises(LoaderError):
            load_roadmaps('doesnotexist')     

    def test_load_manifest(self):
        dict = load_manifest(self.family)
        self.assertIn('rtl', dict.keys())
        self.assertIn('cdc', dict['rtl']['successor'])
        self.assertIn('FCI', dict['rtl']['consumer'])

    def test_load_manifest_fail(self):
        with self.assertRaises(LoaderError):
            load_manifest('doesnotexist')                 

    def test_load_family(self):
        dict = load_family()
        f = 'Falcon'
        self.assertIn(f, dict.keys())
        self.assertIn('i10socfm', dict[f]['icmprojects'])
        self.assertEqual('fln', dict[f]['ICM'])

    @patch('dmx.ecolib.loader.get_dmxdata_path') 
    def test_cth_filelist_mapping_exists(self, mock_get_dmxdata_path):
        family=  'Kmtr'
        dmxdata_root ="/p/psg/flows/common/dmxdata/14.10"
        mock_get_dmxdata_path.return_value = dmxdata_root
        dict = load_deliverables_by_ip_type(family)
        flat_list= [item for sublist in dict.values() for item in sublist]
        if 'CTHFE' in flat_list:
            cth_filelist_mapping = "{}/{}/{}".format(dmxdata_root, family, 'cthfe_filelist_mapping.json')
            self.assertEqual(True, os.path.exists(cth_filelist_mapping))
        else:
            self.assertEqual(False, 'CTHFE' in flat_list)
    
    @patch('dmx.ecolib.loader.get_dmxdata_path') 
    def test_iptypes_in_cth_filelist_mapping(self, mock_get_dmxdata_path):
        family = 'Kmtr'
        mock_get_dmxdata_path.return_value = "/p/psg/flows/common/dmxdata/14.10"
        dict = load_deliverables_by_ip_type(family)
        cth_filelist_mapping_dict = load_cth_filelist_mapping(family)
        flag = False        
        flat_list= [item for sublist in cth_filelist_mapping_dict.values() for item in sublist]
        for key  in dict.keys():
            if 'CTHFE' in dict[key]:
                flag = key in flat_list
                if not flag:
                    break
            else:
                flag = not (key in flat_list)
                if not flag:
                    break
        self.assertEqual(True, flag)

    @patch('dmx.ecolib.loader.get_dmxdata_path') 
    def test_cth_filelist_mapping_contains_sip_hip_vip(self, mock_get_dmxdata_path):
        family = 'Kmtr'
        dmxdata_root ="/p/psg/flows/common/dmxdata/14.10"
        mock_get_dmxdata_path.return_value = dmxdata_root        
        dict = load_deliverables_by_ip_type(family)
        flat_list= [item for sublist in dict.values() for item in sublist]
        if 'CTHFE' in flat_list:
            cth_filelist_mapping = "{}/{}/{}".format(dmxdata_root, family, 'cthfe_filelist_mapping.json')
            self.assertEqual(True, os.path.exists(cth_filelist_mapping))
            cth_filelist_mapping_dict = load_cth_filelist_mapping(family)
            self.assertEqual(True, 'sip' in cth_filelist_mapping_dict.keys())
            self.assertEqual(True, 'hip' in cth_filelist_mapping_dict.keys())
            self.assertEqual(True, 'vip' in cth_filelist_mapping_dict.keys())
        else:
            self.assertEqual(False, 'CTHFE' in flat_list)

    def test_load_checkers(self):
        checkers = load_checkers(self.family)
        self.assertIn('bcmrbc', checkers.keys())
        self.assertEqual('bcmrbc_check', checkers['bcmrbc']['Check Name'])
        self.assertEqual('bcmrbc', checkers['bcmrbc']['Flow'])
        self.assertEqual('', checkers['bcmrbc']['SubFlow'])

    def test_load_checkers_fail(self):
        with self.assertRaises(LoaderError):
            load_checkers('doesnotexist')       
         
    # Function has been disabled in loader.py            
    def _test_load_deliverables_and_checkers_by_milestone(self):
        milestones = load_deliverables_and_checkers_by_milestone(self.family)
        self.assertIn('99', milestones.keys())
        self.assertIn('BCMRBC', milestones['99']['deliverables'])
        self.assertEqual(49, len(milestones['99']['deliverables']))
        self.assertIn('bcmrbc', milestones['99']['checkers'])
        self.assertEqual(54, len(milestones['99']['checkers']))
    def _test_load_deliverables_and_checkers_by_milestone_fail(self):
        with self.assertRaises(LoaderError):
            load_deliverables_and_checkers_by_milestone('doesnotexist')   

    def _test_load_deliverables_by_ip_type(self):
        dict = load_deliverables_by_ip_type(self.family)
        self.assertIn('asic', dict.keys())
        self.assertEqual(7, len(dict.keys()))
        self.assertIn('BCMRBC', dict['asic'])

    def _test_load_deliverables_by_ip_type_fail(self):
        with self.assertRaises(LoaderError):
            load_deliverables_by_ip_type('doesnotexist')       
            
    def _test_load_roadmap_and_revisions_by_product(self):
        dict = load_roadmap_and_revisions_by_product(self.family)
        self.assertIn('ND1', dict.keys())
        self.assertIn('R1', dict['ND1']['milestones'])
        self.assertIn('A', dict['ND1']['revisions'])
        self.assertEqual(5, len(dict.keys()))

    def _test_load_roadmap_and_revisions_by_product_fail(self):
        with self.assertRaises(LoaderError):
            load_roadmap_and_revisions_by_product('doesnotexist')                               

if __name__ == '__main__':
    unittest.main()
