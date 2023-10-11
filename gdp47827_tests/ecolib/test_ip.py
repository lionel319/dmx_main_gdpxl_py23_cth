#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_ip.py $
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
from dmx.ecolib.ip import IP, IPError
from dmx.utillib.utils import is_pice_env
from dmx.ecolib.__init__ import LEGACY
from dmx.abnrlib.workspace import Workspace

class TestIP(unittest.TestCase):
    def setUp(self):
        pass
        
    @classmethod
    def setUpClass(self):
        self.family = 'Ratonmesa'
        self.ip = 'rtmliotest1'
        self.IP = IP(self.family, self.ip, preview=False)
        self.icmproject = 'Raton_Mesa'
        self.icmvariant = self.ip
        self.cell = 'rtmliotest1'
        self.iptype = 'ss_arch'
        self.roadmap = 'RTM'
        self.owner = 'jwquah'
        self.milestone = '1.0'
        self.deliverable = 'reldoc'
        self.bom = 'dev'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_i10socfm_liotest4_10'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_6'
        self.path = self.wsroot
        self.ws = Workspace(workspacepath=self.wsroot)


    @classmethod
    def tearDownClass(self):
        pass

    def tearDown(self):
        pass

    def test_ip_properties(self):
        '''
        Tests the IP object properties
        '''
        self.assertEqual(self.IP.family, self.family)           
        self.assertEqual(self.IP.ip, self.ip)
        self.assertEqual(self.IP.icmproject, self.icmproject)
        self.assertEqual(self.IP.icmvariant, self.icmvariant)
        self.assertEqual(self.IP.iptype, self.iptype)

    def test__preload(self):
        self.IP._preload()
        self.assertIn(self.roadmap, self.IP._deliverables)
        self.assertIn(self.milestone, self.IP._deliverables[self.roadmap])
        self.assertIn(self.deliverable, [x.deliverable for x in self.IP._deliverables[self.roadmap][self.milestone]])

    def test_get_unneeded_deliverables(self):
        deliverables = [x.deliverable for x in self.IP.get_unneeded_deliverables(roadmap=self.roadmap, bom='dev', local=False)]        
        self.assertIn('complibbcm', deliverables)

    def test_get_unneeded_deliverables_with_workspace(self):
        ip = IP(self.family, self.ip, preview=False, workspace=self.ws)
        deliverables = [x.deliverable for x in ip.get_unneeded_deliverables(roadmap=self.roadmap)]        
        self.assertIn('complibbcm', deliverables)

    def test_get_unneeded_deliverables_with_workspaceroot(self):
        ip = IP(self.family, self.ip, preview=False, workspaceroot=self.ws._workspaceroot)
        deliverables = [x.deliverable for x in ip.get_unneeded_deliverables(roadmap=self.roadmap)]        
        self.assertIn('complibbcm', deliverables)

    def test_get_cells_names(self):
        cells = self.IP.get_cells_names(bom='dev', local=False)        
        self.assertIn(self.cell, cells)

    def test_get_cells_names_with_product_filter(self):
        cells = self.IP.get_cells_names(product_filter='ND5', bom='dev', local=False)        
        self.assertIn(self.cell, cells)
         
    def test_get_cells_names_with_cell_filter(self):
        cells = self.IP.get_cells_names(cell_filter=self.cell, bom='dev', local=False)        
        self.assertIn(self.cell, cells)

    def test_get_cells(self):
        cells = [x.cell for x in self.IP.get_cells(bom='dev', local=False)]
        self.assertIn(self.cell, cells)

    def test_get_cells_with_product_filter(self):
        cells = [x.cell for x in self.IP.get_cells(product_filter='ND5', bom='dev', local=False)]
        self.assertIn(self.cell, cells)
         
    def test_get_cells_with_cell_filter(self):
        cells = [x.cell for x in self.IP.get_cells(cell_filter=self.cell, bom='dev', local=False)]
        self.assertIn(self.cell, cells)

    def test_get_cell(self):
        self.assertEqual(self.cell, self.IP.get_cell(self.cell, bom='dev', local=False).cell)

    def test_get_non_existing_cell(self):
        with self.assertRaises(IPError):
            self.IP.get_cell('doesnotexist', bom='dev', local=False)        

    def test_get_cell_invalid_character(self):
        with self.assertRaises(IPError):
            self.IP.get_cell('$')            

    def test_load_ip_properties(self):
        self.IP._load_ip_properties()
        self.assertEqual(self.IP.icmproject, self.icmproject)
        self.assertEqual(self.IP.iptype, self.iptype)
        #self.assertEqual(self.IP.roadmap, self.roadmap)

    def test__get_iptypes(self):
        iptypes = self.IP._get_iptypes()
        self.assertIn(self.iptype, iptypes)        

    def test_500___get_iptype___no_override(self):
        props = {
            'iptype': 'asic',
        }
        ret = self.IP.get_iptype(props)
        self.assertEqual(ret, 'asic')

    def test_501___get_iptype___with_override_1(self):
        props = {
            'iptype': 'asic',
            'iptype_override': 'Wharfrock:custom'
        }
        ret = self.IP.get_iptype(props)
        self.assertEqual(ret, 'asic')

    def test_502___get_iptype___with_override_2(self):
        props = {
            'iptype': 'asic',
            'iptype_override': 'Wharfrock:custom Ratonmesa:softip'
        }
        ret = self.IP.get_iptype(props)
        self.assertEqual(ret, 'softip')

    def test_503___get_iptype___no_iptype(self):
        props = {}
        ret = self.IP.get_iptype(props)
        self.assertEqual(ret, None)

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_variant_properties')
    def test_510___set_iptype___no_iptype_no_override(self, mget, madd):
        mget.return_value = {}
        madd.return_value = False
        self.IP.set_iptype('abc')
        ans = {'iptype': 'abc'}
        self.assertEqual(self.IP._FOR_REGTEST, ans)

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_variant_properties')
    def test_511___set_iptype___same_iptype_no_override(self, mget, madd):
        mget.return_value = {'iptype': 'abc'}
        madd.return_value = False
        self.IP.set_iptype('abc')
        ans = {}
        self.assertEqual(self.IP._FOR_REGTEST, ans)

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_variant_properties')
    def test_512___set_iptype___diff_iptype_no_override(self, mget, madd):
        mget.return_value = {'iptype': 'abc'}
        madd.return_value = False
        self.IP.set_iptype('xxx')
        ans = {'iptype_override': 'Ratonmesa:xxx'}
        self.assertEqual(self.IP._FOR_REGTEST, ans)

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_variant_properties')
    def test_513___set_iptype___diff_iptype_same_override(self, mget, madd):
        mget.return_value = {'iptype': 'abc', 'iptype_override': 'Ratonmesa:xxx Wharfrock:yyy'}
        madd.return_value = False
        self.IP.set_iptype('xxx')
        ans = {}
        self.assertEqual(self.IP._FOR_REGTEST, ans)

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_variant_properties')
    def test_514___set_iptype___diff_iptype_diff_override(self, mget, madd):
        mget.return_value = {'iptype': 'abc', 'iptype_override': 'Ratonmesa:zzz Wharfrock:yyy'}
        madd.return_value = False
        self.IP.set_iptype('xxx')
        ans = {'iptype_override': 'Ratonmesa:xxx Wharfrock:yyy'}
        self.assertEqual(self.IP._FOR_REGTEST, ans)

    @patch('dmx.abnrlib.icm.ICManageCLI.add_variant_properties')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_variant_properties')
    def test_515___set_iptype___same_iptype_diff_override(self, mget, madd):
        mget.return_value = {'iptype': 'xxx', 'iptype_override': 'Ratonmesa:zzz Wharfrock:yyy'}
        madd.return_value = False
        self.IP.set_iptype('xxx')
        ans = {'iptype_override': 'Ratonmesa:xxx Wharfrock:yyy'}
        self.assertEqual(self.IP._FOR_REGTEST, ans)


if __name__ == '__main__':
    unittest.main()
