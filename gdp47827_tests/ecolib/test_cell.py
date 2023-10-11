#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_cell.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
os.environ['DMXDB'] = 'DMXTEST'
from dmx.ecolib.cell import Cell, CellError
from dmx.ecolib.__init__ import LEGACY
from dmx.abnrlib.workspace import Workspace

class TestCell(unittest.TestCase):
    def setUp(self):
        pass
        
    @classmethod
    def setUpClass(self):
        self.family = 'Ratonmesa'
        self.ip = 'rtmliotest1'
        self.cell = 'rtmliotest1'
        self.Cell = Cell(self.family, self.ip, self.cell, preview=False)
        self.icmproject = 'Raton_Mesa'
        self.icmvariant = self.ip
        os.environ['DB_DEVICE'] = 'RTM'
        self.roadmap = 'RTM'
        self.bom = 'dev'
        #self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS/manual_pice_test_runner'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/wplim/icm_ws/wplim_i10socfm_liotest1_38'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_i10socfm_liotest4_10'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_6'
        self.path = self.wsroot
        self.ws = Workspace(workspacepath=self.wsroot)

    @classmethod
    def tearDownClass(self):
        pass

    def tearDown(self):
        pass

    def test_cell_properties(self):
        '''
        Tests the Cell object properties
        '''
        self.assertEqual(self.Cell.family, self.family)           
        self.assertEqual(self.Cell.ip, self.ip)
        self.assertEqual(self.Cell.cell, self.cell)
        self.assertEqual(self.Cell.icmproject, self.icmproject)
        self.assertEqual(self.Cell.icmvariant, self.icmvariant)

    def test__preload(self):
        self.Cell._preload(bom='dev')
        deliverables = [x.deliverable for x in self.Cell._deliverables]
        self.assertIn('ipspec', deliverables)

    def test__load_cell_properties(self):
        self.Cell._load_cell_properties()
        self.assertEqual(self.icmproject, self.Cell.icmproject)
        #self.assertEqual(self.roadmap, self.Cell.roadmap)

    def test_get_all_deliverables(self):
        deliverables = [x.deliverable for x in self.Cell.get_all_deliverables()]            
        self.assertIn('ipspec', deliverables)        

    def test_get_deliverables(self):
        deliverables = [x.deliverable for x in self.Cell.get_deliverables(bom='dev', local=False)]        
        self.assertIn('ipspec', deliverables)

    def test_get_deliverables_with_workspace(self):
        cell = Cell(self.family, self.ip, self.cell, workspace=self.ws, preview=False)
        deliverables = [x.deliverable for x in cell.get_deliverables()]        
        self.assertIn('ipspec', deliverables)

    def test_get_deliverables_with_workspaceroot(self):
        cell = Cell(self.family, self.ip, self.cell, workspaceroot=self.ws._workspaceroot, preview=False)
        deliverables = [x.deliverable for x in cell.get_deliverables()]        
        self.assertIn('ipspec', deliverables)
        
    def test_get_unneeded_deliverables(self):
        deliverables = [x.deliverable for x in self.Cell.get_unneeded_deliverables(bom='dev', local=False)]        
        self.assertIn('complibbcm', deliverables)

    def test_get_unneeded_deliverables_with_workspace(self):
        cell = Cell(self.family, self.ip, self.cell, workspace=self.ws, preview=False)
        deliverables = [x.deliverable for x in cell.get_unneeded_deliverables()]        
        self.assertIn('complibbcm', deliverables)

    def test_get_unneeded_deliverables_with_workspaceroot(self):
        cell = Cell(self.family, self.ip, self.cell, workspaceroot=self.ws._workspaceroot, preview=False)
        deliverables = [x.deliverable for x in cell.get_unneeded_deliverables()]        
        self.assertIn('complibbcm', deliverables)        

    def test_get_invalid_unneeded_deliverables(self):
        deliverables = [x for x in self.Cell.get_invalid_unneeded_deliverables(bom='dev', local=False)]        
        self.assertEqual([], deliverables)
        #self.assertIn('invalid_deliverable', deliverables)

    def test_get_invalid_unneeded_deliverables_with_workspace(self):
        cell = Cell(self.family, self.ip, self.cell, workspace=self.ws, preview=False)
        deliverables = [x for x in cell.get_invalid_unneeded_deliverables()]        
        self.assertEqual([], deliverables)
        #self.assertIn('invalid_deliverable', deliverables)

    def test_get_invalid_unneeded_deliverables_with_workspaceroot(self):
        cell = Cell(self.family, self.ip, self.cell, workspaceroot=self.ws._workspaceroot, preview=False)
        deliverables = [x for x in cell.get_invalid_unneeded_deliverables()]        
        self.assertEqual([], deliverables)
        #self.assertIn('invalid_deliverable', deliverables)        


if __name__ == '__main__':
    unittest.main()
