#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmlib/test_ICManageWorkspace.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
from builtins import str
import unittest
from mock import patch
from datetime import date
import os, sys
import logging
import socket
import datetime
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.loggingutils
LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)
import dmx.abnrlib.icm
import dmx.dmlib.ICManageWorkspace
import dmx.dmlib.ICManageConfiguration
import dmx.dmlib.dmError


class TestICManageWorkspace(unittest.TestCase):

    def setUp(self):
        self.project = 'Raton_Mesa'
        self.ip = 'rtmliotest1'
        self.bom= 'dev'
        self.workspacename = 'lionelta_Raton_Mesa_rtmliotest1_6'
        self.cwd = os.getcwd()
        self.path = '/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_i10socfm_liotestfc1_14'
        self.path = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_6'
        self.icmw = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(workspacePath=self.path)
        self.icmconfig = dmx.dmlib.ICManageConfiguration.ICManageConfiguration(self.project, self.ip, self.bom) 

    def test_000__repr(self):
        result = "ICManageWorkspace(workspacePath='/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_i10socfm_liotestfc1_14', ipName='liotestfc1', libType='None')"
        result = "ICManageWorkspace(workspacePath='/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_6', ipName='rtmliotest1', libType='None')"
        self.assertEqual(result, repr(self.icmw))

    def test_001____str(self):
        result = '{}, variant {}'.format(self.path, self.ip)
        self.assertEqual(result, str(self.icmw))

    def test_002____path(self):
        self.assertEqual(self.path, self.icmw.path)

    def test_003____workspaceName(self):
        self.assertEqual(self.workspacename, self.icmw.workspaceName)


    def test_005____getWorkspaceAttribute_project(self):
        self.assertEqual(self.project, self.icmw.getWorkspaceAttribute('Project'))

    def test_006____getWorkspaceAttribute_variant(self):
        self.assertEqual(self.ip, self.icmw.getWorkspaceAttribute('Variant'))

    def test_007____getWorkspaceAttribute_fail(self):
        with self.assertRaises(KeyError):
            self.icmw.getWorkspaceAttribute('unknown')

    def test_008___workspaceAttributeNames(self):
        result = [u'p4-client-options', 'variant', 'project', u'rootDir', 'libtype', 'config']
        result = ['Loc', 'Attr', 'ConfType', 'Variant', 'Project', 'User', 'Workspace', 'LibType', 'Config', 'Mount', 'Dir', 'Desc']
        self.assertEqual(sorted(result), sorted(self.icmw.workspaceAttributeNames))

    def test_009____infoNames(self):
        print("RET:{}".format(self.icmw.infoNames))
        result = ['Client name', 'Client root', 'Server version', 'Client address', 'Server root', 'Server uptime', 'Server address', 'User name', 'Server license', 'Case Handling', 'Current directory', 'Client host', 'Peer address', 'Server date', 'Server license-ip']
        result = ['Client name', 'Client root', 'Server version', 'Client address', 'Server root', 'Server uptime', 'Server address', 'User name', 'Server license', 'Case Handling', 'Current directory', 'Client host', 'Server license-ip', 'Peer address', 'Server date', 'ServerID', 'Server services']
        self.assertEqual(sorted(result), sorted(self.icmw.infoNames))

    def test_010____getInfo(self):
        result = ['Client name', 'Client root', 'Server version', 'Client address', 'Server root', 'Server uptime', 'Server address', 'User name', 'Server license', 'Case Handling', 'Current directory', 'Client host', 'Peer address', 'Server date', 'Server license-ip']
        print("RET:{}".format(self.icmw.getInfo("Client name")))
        self.assertEqual(self.workspacename, self.icmw.getInfo('Client name'))

    def test_011____getInfo_fail(self):
        with self.assertRaises(KeyError):
            print(self.icmw.getInfo('wrg info'))

    def test_012_____getInfo_pass(self):
        self.assertEqual(self.workspacename, self.icmw._getInfo(self.path)['Client name'])

    def test_013_____getInfo_fail_not_icmworksapce(self):
        with self.assertRaises(dmx.dmlib.dmError.dmError):
            self.icmw._getInfo(self.path+'/../../')

    def test_014_____isIcmconfigFileInPath_true(self):
        self.assertTrue(self.icmw._isIcmconfigFileInPath(self.path))

    def test_015_____isIcmconfigFileInPath_false(self):
        self.assertFalse(self.icmw._isIcmconfigFileInPath(self.path+'../../../'))

    def test_016_____findWorkspace_subiplevel(self):
        self.assertEqual(self.path, self.icmw.findWorkspace(self.path+'/rtmliotest1'))

    def test_017_____findWorkspace(self):
        self.assertEqual(self.path, self.icmw.findWorkspace(self.path))

    def test_018_____findWorkspace_fail_path_not_exists(self):
        with self.assertRaises(dmx.dmlib.dmError.dmError):
            self.icmw.findWorkspace('None existience')

    def test_019_____getAbsPathOrCwd_pass(self):
        self.assertEqual(self.path, self.icmw.getAbsPathOrCwd(self.path))

    def test_020_____getAbsPathOrCwd_none(self):
        os.chdir(self.path)
        self.assertEqual(self.path, self.icmw.getAbsPathOrCwd(self.path))
        os.chdir(self.cwd)

    def test_021_____getAbsPathOrCwd_fail(self):
        with self.assertRaises(dmx.dmlib.dmError.dmError):
             self.icmw.getAbsPathOrCwd('Not exists')

    def test_022_____isWorksapace_false(self):
        self.assertFalse(self.icmw.isWorkspace('Not exists'))

    def test_023_____isWorkspace_true(self):
        self.assertTrue(self.icmw.isWorkspace(self.path))

    def test_024_____isWorkspace_false2(self):
        self.assertFalse(self.icmw.isWorkspace(self.path+'/jtag_common'))

    def test_025______getCellListFileName_pass(self):
        result = self.path + '/rtmliotest1/ipspec/cell_names.txt'
        self.assertEqual(result, self.icmw._getCellListFileName(self.ip, 'rtmliotest1', 'cell_names'))

    def test_026______getCellListFileName_pass_nonexist(self):
        self.assertEqual('', self.icmw._getCellListFileName(self.ip, 'testingcell1', 'non_exists'))

    def test_027______getCellListFileName_pass_atom_notexist(self):
        self.assertEqual('', self.icmw._getCellListFileName(self.ip, 'testingcell1', 'atoms'))

    def test_028______isCellListFileReadable_fail(self):
        self.assertFalse(self.icmw.isCellListFileReadable(self.ip, 'cell_names'))

    def test_029______isCellListFileReadable_pass(self):
        self.assertTrue(self.icmw.isCellListFileReadable('rtmliotest1', 'cell_names', 'testingcell1'))
#
    def test_030_______getCellsInListFile_true(self):
        result = set(['rtmliotest1'])
        self.assertEqual(result, self.icmw._getCellsInListFile(self.ip, 'rtmliotest1', 'cell_names', True))

    def test_031_______getCellsInListFile_false(self):
        result = set(['rtmliotest1'])
        print("RET:{}".format(self.icmw._getCellsInListFile(self.ip, 'asdasd', 'cell_names', False)))
        self.assertEqual(result, self.icmw._getCellsInListFile(self.ip, 'asdasd', 'cell_names', False))

    def test_032_______getCellsInList_nocellname(self):
        result = set(['rtmliotest1'])
        self.assertEqual(result, self.icmw.getCellsInList(self.ip, 'cell_names'))

    def test_033_______getCellsInList_unkwowncellname(self):
        result = set([])
        self.assertEqual(result, self.icmw.getCellsInList(self.ip, 'nonexistent'))

    def test_034__getCellNamesForIPName(self):
        result = set(['rtmliotest1'])
        self.assertEqual(result, self.icmw.getCellNamesForIPName(self.ip))

    def test_035___ipNamesForCellNames(self):
        result = {'liotest4': 'liotest4', 'liotestfc1': 'liotestfc1', 'liotest1': 'liotest1', 'liotest2': 'liotest2'}
        result = {'rtmliotest1': 'rtmliotest1'}
        print("ret:{}".format(self.icmw._ipNamesForCellNames))
        self.assertEqual(result, self.icmw._ipNamesForCellNames)

    def test_036___getIPNameForCellName(self):
        result = 'rtmliotest1'
        self.assertEqual(result, self.icmw.getIPNameForCellName('rtmliotest1'))

    def test_037___getCellNamesForIPNameAndPath(self):
        result = set(['rtmliotest1'])
        self.assertEqual(result, self.icmw.getCellNamesForIPNameAndPath(self.ip, self.path, False))

    def test_038____getConfigurationTripletFromWorkspace(self):
        result = (u'Raton_Mesa', u'rtmliotest1', u'dev')
        self.assertEqual(result, self.icmw._getConfigurationTripletFromWorkspace(self.ip))

    def test_039__get_project_of_ip(self):
        self.assertEqual(self.project, self.icmw.get_project_of_ip(self.ip))

    def test_040__get_ips(self):
        result = ['liotest1', 'liotest2', 'liotest4', 'liotestfc1']
        result = ['rtmliotest1']
        self.assertEqual(result, self.icmw.get_ips())

    def test_041__get_ips_with_project(self):
        print("RET:{}".format(self.icmw.get_ips_with_project()))
        result = [('i10socfm', 'liotest1'), ('i10socfm', 'liotest2'), ('i10socfm', 'liotest4'), ('i10socfm', 'liotestfc1')]
        result = [('Raton_Mesa', 'rtmliotest1')]
        self.assertEqual(result, self.icmw.get_ips_with_project())

    def test_042__get_projects(self):
        self.assertEqual([self.project], self.icmw.get_projects())

    def test_043__get_deliverable(self):
        result = ['ipspec', 'reldoc']
        ds = self.icmw.get_deliverables(self.ip)
        self.assertIn('ipspec', ds)
        self.assertIn('reldoc', ds)

    def test_044__get_cells(self):
        result = ['rtmliotest1'] 
        self.assertEqual(result, self.icmw.get_cells(self.ip))

    def test_045__get_cells_2(self):
        result = ['rtmliotest1'] 
        self.assertEqual(result, self.icmw.get_cells('rtmliotest1'))

    def test_046__get_unneeded_deliverables_for_ip(self):
        result = ['invalid_deliverable', 'reldoc']
        #self.assertEqual(result, self.icmw.get_unneeded_deliverables_for_ip(self.ip))
        self.assertIn('complibbcm', self.icmw.get_unneeded_deliverables_for_ip(self.ip))

    def test_047__get_unneeded_deliverables_for_cell(self):
        result = ['invalid_deliverable', 'reldoc']
        #self.assertEqual(result, self.icmw.get_unneeded_deliverables_for_cell(self.ip, 'testingcell1'))
        self.assertIn('complibbcm', self.icmw.get_unneeded_deliverables_for_ip(self.ip))







if __name__ == '__main__':
    unittest.main()

