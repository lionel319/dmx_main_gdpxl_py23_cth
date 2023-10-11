#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_workspace.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $


from __future__ import print_function
import unittest
from mock import patch
import os, sys
import datetime
import time
import tempfile
import re

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.abnrlib.flows.workspace
import dmx.utillib.utils

class TestFlowWorkspace(unittest.TestCase):

    ws_detail = {u'name': u'lionelta_Raton_Mesa_rtmliotest1_44', u'config:parent:name': u'dev', u'variant:parent:name': u'rtmliotest1', u'rootDir': u'/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44', u'project:parent:name': u'Raton_Mesa', u'created-by': u'lionelta'}
 
    def setUp(self):
        self.project = 'Raton_Mesa'
        self.ip = 'rtmliotest1'
        self.bom= 'dev'
        self.workspacename = 'lionelta_Raton_Mesa_rtmliotest1_44'
        self.cwd = os.getcwd()
        self.path = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        self.icmws = dmx.abnrlib.workspace.Workspace(self.path)
        self.path_not_ws = '/tmp'
        self.w = dmx.abnrlib.flows.workspace.Workspace()

        self.run_command = dmx.utillib.utils.run_command
        self.workspaces = ['lionelta_Raton_Mesa_rtmliotest1_44']
        self.tmpfile = tempfile.mkstemp()[1]
        self.goldendir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files')

    def tearDown(self):
        os.system('rm -rf {}'.format(self.tmpfile))
        pass

    def test_100___write_sync_config_file___defaults(self):
        self.w.write_sync_config_file(self.tmpfile)
        goldfile = os.path.join(self.goldendir, 'default')
        exitcode, stdout, stderr = self.run_command("sdiff {} {}".format(self.tmpfile, goldfile))
        self.assertFalse(exitcode, '\n' + stdout + stderr)

    def test_101___write_sync_config_file___customized_variants(self):
        self.w.write_sync_config_file(self.tmpfile, variants=['va', 'vb'])
        goldfile = os.path.join(self.goldendir, 'variants')
        exitcode, stdout, stderr = self.run_command("sdiff {} {}".format(self.tmpfile, goldfile))
        self.assertFalse(exitcode, '\n' + stdout + stderr)

    def test_102___write_sync_config_file___customized_libtypes(self):
        self.w.write_sync_config_file(self.tmpfile, libtypes=['la', 'lb'])
        goldfile = os.path.join(self.goldendir, 'libtypes')
        exitcode, stdout, stderr = self.run_command("sdiff {} {}".format(self.tmpfile, goldfile))
        self.assertFalse(exitcode, '\n' + stdout + stderr)

    def test_103___write_sync_config_file___customized_variants_libtypes(self):
        self.w.write_sync_config_file(self.tmpfile, variants=['va', 'vb'], libtypes=['la', 'lb'])
        goldfile = os.path.join(self.goldendir, 'variants_libtypes')
        exitcode, stdout, stderr = self.run_command("sdiff {} {}".format(self.tmpfile, goldfile))
        self.assertFalse(exitcode, '\n' + stdout + stderr)



    def test_200___read_sync_config_file___defaults(self):
        goldfile = os.path.join(self.goldendir, 'default')
        ret = self.w.read_sync_config_file(goldfile)
        self.assertFalse(ret[0])
        self.assertEqual(ret[1].get('1', 'variants'), '*')
        self.assertEqual(ret[1].get('1', 'libtypes'), '*')

    def test_201___read_sync_config_file___customized_variants(self):
        goldfile = os.path.join(self.goldendir, 'variants')
        ret = self.w.read_sync_config_file(goldfile)
        self.assertFalse(ret[0])
        self.assertEqual(ret[1].get('1', 'variants'), 'va vb')
        self.assertEqual(ret[1].get('1', 'libtypes'), '*')

    def test_202___read_sync_config_file___customized_libtypes(self):
        goldfile = os.path.join(self.goldendir, 'libtypes')
        ret = self.w.read_sync_config_file(goldfile)
        self.assertFalse(ret[0])
        self.assertEqual(ret[1].get('1', 'variants'), '*')
        self.assertEqual(ret[1].get('1', 'libtypes'), 'la lb')

    def test_203___read_sync_config_file___customized_variants_libtypes(self):
        goldfile = os.path.join(self.goldendir, 'variants_libtypes')
        ret = self.w.read_sync_config_file(goldfile)
        self.assertFalse(ret[0])
        self.assertEqual(ret[1].get('1', 'variants'), 'va vb')
        self.assertEqual(ret[1].get('1', 'libtypes'), 'la lb')


    @patch('dmx.abnrlib.icm.ICManageCLI.get_opened_files', return_value='1')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_workspace_details', return_value=ws_detail)
    def test_300___list_workspace_format___default_pass(self, workspace_detail, opened_files):
        self.assertTrue(self.w.list_workspace_format(self.workspaces, 'human'))
        self.assertTrue(self.w.list_workspace_format(self.workspaces, 'xml'))
        self.assertTrue(self.w.list_workspace_format(self.workspaces, 'json'))
        self.assertTrue(self.w.list_workspace_format(self.workspaces, 'csv'))

    @patch('dmx.abnrlib.icm.ICManageCLI.get_opened_files', return_value='1')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_workspace_details', return_value=ws_detail)
    def test_301___list_workspace_format___default_human_pass(self, workspace_detail, opened_files):
        ret = self.w.list_workspace_format(self.workspaces, 'human')
        print("ret: {}".format(ret))
        gold = ['CNT  WORKSPACE NAME                                     PROJECT                   VARIANT                        CONFIG                                   OPENED WSDIR\n', '1    lionelta_Raton_Mesa_rtmliotest1_44                 Raton_Mesa                rtmliotest1                    dev                                      1      /nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44\n']
        self.assertEqual(ret, gold)

    @patch('dmx.abnrlib.icm.ICManageCLI.get_opened_files', return_value='1')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_workspace_details', return_value=ws_detail)
    def test_302___list_workspace_format___default_xml_pass(self, workspace_detail, opened_files):
        ret = self.w.list_workspace_format(self.workspaces, 'xml')
        print("ret: {}".format(ret))
        gold = '''<?xml version="1.0" ?>\n<root>\n\t<item>\n\t\t<PROJECT>\n\t\t\tRaton_Mesa\n\t\t</PROJECT>\n\t\t<IP>\n\t\t\trtmliotest1\n\t\t</IP>\n\t\t<BOM>\n\t\t\tdev\n\t\t</BOM>\n\t\t<PATH>\n\t\t\t/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44\n\t\t</PATH>\n\t\t<WORKSPACE_NAME>\n\t\t\tlionelta_Raton_Mesa_rtmliotest1_44\n\t\t</WORKSPACE_NAME>\n\t\t<USER>\n\t\t\tlionelta\n\t\t</USER>\n\t\t<POPULATION_DATEnTIME>\n\t\t\tNone\n\t\t</POPULATION_DATEnTIME>'''
        print("--------------------------")
        print(gold)
        print("--------------------------")
        print(ret)
        print("--------------------------")
        self.assertIn(re.sub('\s', '', gold), re.sub('\s', '', ret))


    @patch('dmx.abnrlib.icm.ICManageCLI.get_opened_files', return_value='1')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_workspace_details', return_value=ws_detail)
    def test_303___list_workspace_format___default_json_pass(self, workspace_detail, opened_files):
        ret = self.w.list_workspace_format(self.workspaces, 'json')
        print("ret: {}".format(ret))
        gold = '[\n    {\n        "PROJECT": "i10socfm", \n        "IP": "liotestfc1", \n        "BOM": "two_libtypes", \n        "PATH": "/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_i10socfm_liotestfc1_14", \n        "WORKSPACE_NAME": "lionelta_i10socfm_liotestfc1_14", \n        "USER": "lionelta", \n        "POPULATION_DATEnTIME": "None", \n        "NUMBER_OF_DAYS_INACTIVE": .+\n    }\n]'
        self.assertRegexpMatches(ret, gold)

    @patch('dmx.abnrlib.icm.ICManageCLI.get_opened_files', return_value='1')
    @patch('dmx.abnrlib.icm.ICManageCLI.get_workspace_details', return_value=ws_detail)
    def test_304___list_workspace_format___default_csv_pass(self, workspace_detail, opened_files):
        self.assertIn('PROJECT,IP,BOM,PATH,WORKSPACE_NAME,USER,POPULATION_DATEnTIME,NUMBER_OF_DAYS_INACTIVE', self.w.list_workspace_format(self.workspaces, 'csv'))

    def test_305___list_action___system_test_no_argurment_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='human', project=None, ip=None, bom=None))

    def test_306___list_action___system_test_project_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='human', project='i10socfm', ip=None, bom=None))

    def test_307___list_action___system_test_project_ip_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='human', project='i10socfm', ip='wplimtest1', bom=None))

    def test_308___list_action___system_test_project_ip_bom_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='human', project='i10socfm', ip='wplimtest1', bom='REL5.0FM6revA0__19ww174a'))

    def test_309___list_action___system_test_project_ip_bom_xml_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='xml', project='i10socfm', ip='wplimtest1', bom='REL5.0FM6revA0__19ww174a'))

    def test_310___list_action___system_test_project_ip_bom_json_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='json', project='i10socfm', ip='wplimtest1', bom='REL5.0FM6revA0__19ww174a'))

    def test_311___list_action___system_test_project_ip_bom_csv_pass(self):
        self.assertIsNone(self.w.list_action(user=None, older_than=0, tabulated=False, preview=False, format='csv', project='i10socfm', ip='wplimtest1', bom='REL5.0FM6revA0__19ww174a'))

    def test_312___list_action___system_test_project_ip_bom_csv_user_pass(self):
        self.assertIsNone(self.w.list_action(user='wplim', older_than=0, tabulated=False, preview=False, format='csv', project='i10socfm', ip='wplimtest1', bom='REL5.0FM6revA0__19ww174a'))


    def test_313___list_action___system_test_wrong_user(self):
        self.assertIsNone(self.w.list_action(user='wpldasdim', older_than=0, tabulated=False, preview=False, format='csv', project='i10socfm', ip='wplimtest1', bom='REL5.0FM6revA0__19ww174a'))

    def test_314___list_action___system_test_wrong_project(self):
        self.assertIsNone(self.w.list_action(user='wplim', older_than=0, tabulated=False, preview=False, format='csv', project='i10sodsacfm', ip=None, bom=None))

    def test_315___list_action___system_test_wrong_ip(self):
        self.assertIsNone(self.w.list_action(user='wplim', older_than=0, tabulated=False, preview=False, format='csv', project='i10socfm', ip='sadsa', bom=None))

    def test_316___list_action___system_test_wrong_bom(self):
        self.assertIsNone(self.w.list_action(user='wplim', older_than=0, tabulated=False, preview=False, format='csv', project='i10socfm', ip='wplimtest1', bom='adssa'))

    @patch('os.path.exists', return_value=True)
    @patch('dmx.abnrlib.flows.workspace.Workspace.rerun_dmx_workspace_delete_as_psginfraadm_cmd', return_value='echo 0')
    @patch('dmx.abnrlib.flows.workspace.input', return_value='y')
    @patch('dmx.abnrlib.icm.ICManageCLI.user_has_icm_license', return_value=False)
    @patch('dmx.abnrlib.icm.ICManageCLI.user_has_icm_license', return_value=False)
    def test_401___delete_action___user_not_icmuser_ans_is_y_pass(self, workspace_detail, opened_files, raw_input, ret, exists):
        self.assertEqual(0, self.w.delete_action(rmfiles=False, yes_to_all=False, workspacename=['test'], older_than=False, preview=True))

    @patch('os.path.exists', return_value=True)
    @patch('dmx.abnrlib.flows.workspace.Workspace.rerun_dmx_workspace_delete_as_psginfraadm_cmd', return_value='echo 0')
    @patch('dmx.abnrlib.flows.workspace.input', return_value='n')
    @patch('dmx.abnrlib.icm.ICManageCLI.user_has_icm_license', return_value=False)
    @patch('dmx.abnrlib.icm.ICManageCLI.user_has_icm_license', return_value=False)
    def test_402___delete_action___user_not_icmuser_ans_is_n_pass(self, workspace_detail, opened_files, raw_input, ret, exists):
        with self.assertRaises(SystemExit):
            self.w.delete_action(rmfiles=False, yes_to_all=False, workspacename=['test'], older_than=False, preview=True)

    @patch('os.path.exists', return_value=False)
    @patch('dmx.abnrlib.flows.workspace.Workspace.rerun_dmx_workspace_delete_as_psginfraadm_cmd', return_value='echo 0')
    @patch('dmx.abnrlib.flows.workspace.input', return_value='n')
    @patch('dmx.abnrlib.icm.ICManageCLI.user_has_icm_license', return_value=False)
    @patch('dmx.abnrlib.icm.ICManageCLI.user_has_icm_license', return_value=False)
    def test_403___delete_action___user_not_icmuser_no_ws_input_fail(self, workspace_detail, opened_files, raw_input, ret, exists):
        with self.assertRaises(dmx.abnrlib.flows.workspace.WorkspaceError):
            self.w.delete_action(rmfiles=False, yes_to_all=False, workspacename=None, older_than=False, preview=True)


    def test_404___rerun_dmx_workspace_delete_as_psginfraadm___pass(self):
        self.assertIn('/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost', self.w.rerun_dmx_workspace_delete_as_psginfraadm_cmd(workspacename=['test_ws']))
        self.assertIn('arc submit --interactive  --local  ', self.w.rerun_dmx_workspace_delete_as_psginfraadm_cmd(workspacename=['test_ws']))
        self.assertIn('dmx workspace delete -w test_ws -y -r --debug', self.w.rerun_dmx_workspace_delete_as_psginfraadm_cmd(workspacename=['test_ws']))


    def test_501__get_workspaces(self):
        ret = self.w.get_workspaces(project='Raton_Mesa', variant='rtmliotest1', config='dev')
        print(ret)
        gold = {'project': u'Raton_Mesa', 'user': u'lionelta', 'workspace': u'lionelta_Raton_Mesa_rtmliotest1_44', 'conf_type': '', 'variant': u'rtmliotest1', 'libtype': '', 'description': '', 'config': u'dev', 'dir': u'/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/./lionelta_Raton_Mesa_rtmliotest1_44', 'location': ''}
        
        self.assertIn(gold, ret)





if __name__ == '__main__':
    unittest.main()

