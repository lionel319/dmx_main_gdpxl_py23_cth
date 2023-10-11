#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr showconfig plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_bomupdate.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import os, sys
import unittest
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.abnrlib.flows.bomupdate
from pprint import pprint

class TestBomUpdate(unittest.TestCase):

    def setUp(self):
        self.project = 'i16soc'
        self.ip = 'i16socwplimtest1'
        self.bom = 'top_hier2'
        self.syncpoint = "PHYS4.0FM6revB0"
        self.cfgfile = LIB + '/../../gdp47827_tests/abnrlib/files/bom_edit_file'
        self.cfgfile2 = LIB + '/../../gdp47827_tests/abnrlib/files/bom_edit_file_2'
        self.fail_cfgfile = LIB + '/../../gdp47827_tests/abnrlib/files/bom_edit_file_fail'
        self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate(self.project, self.ip, self.bom, self.syncpoint, preview=True, cfgfile=self.cfgfile)

    def test_001___check_conflicts_in_pvc(self):
        ret = self.bu.check_conflicts_in_pvc()
        self.assertEqual(ret, False)

    def test_002___check_conflicts_in_syncpoint(self):
        ret = self.bu.check_conflicts_in_pvc()
        self.assertEqual(ret, False)

    
    def test_010___get_rel_config_from_syncpoint___True(self):
        ret = self.bu.get_rel_config_from_syncpoint('i10socfm', 'soc_common')
        self.assertEqual(ret, 'REL5.0FM6revB0__19ww226a')

    def test_010___get_rel_config_from_syncpoint___False(self):
        ret = self.bu.get_rel_config_from_syncpoint('i10socfm', 'no_such_variant')
        self.assertEqual(ret, False)

    def test_020__read_cfgfile_pass(self):
        result = ['da_i16/dai16liotest1:ipspec@REL1.0LTMrevA0__22ww251a']
        self.assertEqual(result, self.bu.read_cfgfile())

    def test_020__read_cfgfile_fail(self):
        self.cfgfile = LIB + '/../../gdp47827_tests/abnrlib/files/b.job'
        self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate(self.project, self.ip, self.bom, self.syncpoint, preview=True, cfgfile=self.cfgfile)
        self.assertEqual([], self.bu.read_cfgfile())

    def test_030__get_flatten_configfile_dict_pass(self):
        cfgfile_info = self.bu.read_cfgfile()
        result = {('da_i16', 'dai16liotest1'): {'ipspec': 'REL1.0LTMrevA0__22ww251a'}}
        self.assertEqual(result, self.bu.get_flatten_configfile_dict(cfgfile_info))
  
    def test_030__get_flatten_configfile_dict_fail(self):
        self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate(self.project, self.ip, self.bom, self.syncpoint, preview=True, cfgfile=self.fail_cfgfile)
        self.cfgfile_info = self.bu.read_cfgfile()
        with self.assertRaises(dmx.abnrlib.flows.bomupdate.BomUpdateError):
            self.bu.get_flatten_configfile_dict(self.cfgfile_info)

    def test_040__split_pvc_in_config_pass(self):
        self.assertEqual(('i10socfm', 'liotestfc1', 'ipspec', 'test5_dev'), self.bu.split_pvc_in_config('i10socfm/liotestfc1:ipspec@test5_dev'))

    def test_040__split_pvc_in_config_fail(self):
        with self.assertRaises(AttributeError):
            self.bu.split_pvc_in_config('wrongconfigformat')

    def test_050__get_flatten_root_dict_pass(self):
        result = {('i16soc', 'i16socwplimtest1'): {'sdf': 'i16soc', 'cdl': 'i16soc', 'reldoc': 'i16soc', 'complibphys': 'i16soc', 'cvrtl': 'i16soc', 'ipxact': 'i16soc', 'circuitsim': 'i16soc', 'rtlcompchk': 'i16soc', 'gln_filelist': 'i16soc', 'complib': 'i16soc', 'rtl': 'i16soc', 'upf_rtl': 'i16soc', 'rcxt': 'i16soc', 'netlist': 'i16soc', 'dftdsm': 'i16soc', 'pvector': 'i16soc', 'lint': 'i16soc', 'cdc': 'i16soc', 'dv': 'i16soc', 'ipspec': 'i16soc', 'bcmrbc': 'i16soc'}, ('da_i16', 'dai16liotest1'): {'circuitsim': 'da_i16', 'rcxt': 'da_i16', 'upf_rtl': 'da_i16', 'dv': 'da_i16', 'complib': 'da_i16', 'gln_filelist': 'da_i16', 'rtlcompchk': 'da_i16', 'netlist': 'da_i16', 'ipxact': 'da_i16', 'cvrtl': 'da_i16', 'complibphys': 'da_i16', 'reldoc': 'da_i16', 'cdl': 'da_i16', 'sdf': 'da_i16', 'cdc': 'da_i16', 'lint': 'da_i16', 'dftdsm': 'da_i16', 'rtl': 'da_i16', 'pvector': 'da_i16', 'bcmrbc': 'da_i16'}, ('da_i16/dai16liotest1', 'ipspec'): {'dev': 'da_i16/dai16liotest1'}, ('da_i16', 'cdclib'): {'lint': 'da_i16', 'ipspec': 'da_i16', 'cdc': 'da_i16', 'dftdsm': 'da_i16', 'rdf': 'da_i16', 'cvrtl': 'da_i16', 'rtlcompchk': 'da_i16', 'rtl': 'da_i16', 'dv': 'da_i16', 'ipxact': 'da_i16', 'reldoc': 'da_i16', 'bcmrbc': 'da_i16'}}
        self.assertEqual(result, self.bu.get_flatten_root_dict())

    def test_060__get_bom_edit_file_pass(self):
        #self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate('i10socfm', 'liotestfc1', 'rel_and_dev', self.syncpoint, preview=True, cfgfile=self.cfgfile)
        self.cfgfile_info = self.bu.get_flatten_configfile_dict(self.bu.read_cfgfile())
        self.assertTrue(os.path.isfile(self.bu.get_bom_edit_file(self.cfgfile_info, self.bu.get_flatten_root_dict())))
   
    def test_060__get_bom_edit_file_fail(self):
        self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate(self.project, self.ip, self.bom, self.syncpoint, preview=True, cfgfile=self.cfgfile2)
        self.cfgfile_info = self.bu.get_flatten_configfile_dict(self.bu.read_cfgfile())
        with self.assertRaises(dmx.abnrlib.flows.bomupdate.BomUpdateError):
            self.bu.get_bom_edit_file(self.cfgfile_info, self.bu.get_flatten_root_dict())

    def test_070__update_fail(self):
        self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate(self.project, self.ip, self.bom, self.syncpoint, preview=True, cfgfile=self.fail_cfgfile)

        with self.assertRaises(dmx.abnrlib.flows.bomupdate.BomUpdateError):
            self.bu.update()

    def test_070__update_pass(self):
        self.bu = dmx.abnrlib.flows.bomupdate.BomUpdate(self.project, self.ip, self.bom, self.syncpoint, preview=True, cfgfile=self.cfgfile)
        # will print belowing info but we dont care as long as it return value is None. This is expected output 
        #ERROR: You must specify an action to perform
        #ERROR: DMX has run into errors. For more details on the command, please run 'dmx help bom edit'

        self.assertIsNone(self.bu.update())




if __name__ == '__main__':
    unittest.main()
