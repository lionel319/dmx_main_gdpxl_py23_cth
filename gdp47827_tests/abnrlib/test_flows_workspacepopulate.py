#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_workspacepopulate.py $
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
from mock import patch
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.abnrlib.flows.workspacepopulate
import dmx.utillib.utils

class TestFlowWorkspacePopulate(unittest.TestCase):

    def setUp(self):
        self.wp = dmx.abnrlib.flows.workspacepopulate
        self.project = 'Raton_Mesa'
        self.ip = 'rtmliotest1'
        self.bom = 'dev'
        self.wsname = 'regtestws'
        self.envvar = 'DMX_WORKSPACE'
        
        self.wsdisk = '/tmp'
        os.environ[self.envvar] = self.wsdisk
        os.environ['WASHGROUP_DBFILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'washgroups.json')

    def tearDown(self):
        self._undefine_envvar()


    def _undefine_envvar(self):
        os.environ.pop(self.envvar, None)
        os.environ.pop('DB_FAMILIES', None)
        os.environ.pop('WASHGROUP_DBFILE', None)


    def test_100___workspace_disk___not_defined(self):
        self._undefine_envvar()
        with self.assertRaisesRegexp(Exception, '.*DMX_WORKSPACE not defined.*'):
            self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname)


    def test_100___workspace_disk___defined(self):
        wp = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname)
        self.wsroot = os.path.join(self.wsdisk, self.wsname)
        self.assertEqual(self.wsroot, wp._get_wsroot())


    def test_200___is_wsroot_folder_exist___fail(self):
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname)
        self.assertFalse(w.is_ws_folder_exist())


    def test_300___write_sync_configuration_into_tmpfile___no_cfgfile_with_delivarebles(self):
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'libtypes')
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname, deliverables=['la', 'lb'])
        w._write_sync_configuration_into_tmpfile()
        cmd = 'sdiff {} {}'.format(cfgfile, w.tmpfile)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        self.assertFalse(exitcode, '\n' + cmd + '\n' + stdout + stderr)

    def test_300___write_sync_configuration_into_tmpfile___no_cfgfile_no_delivarebles(self):
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'default')
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname)
        w._write_sync_configuration_into_tmpfile()
        cmd = 'sdiff {} {}'.format(cfgfile, w.tmpfile)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        self.assertFalse(exitcode, '\n' + cmd + '\n' + stdout + stderr)

    def test_300___write_sync_configuration_into_tmpfile___with_cfgfile_no_delivarebles(self):
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'variants_libtypes')
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname, cfgfile=cfgfile)
        w._write_sync_configuration_into_tmpfile()
        cmd = 'sdiff {} {}'.format(cfgfile, w.tmpfile)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        self.assertFalse(exitcode, '\n' + cmd + '\n' + stdout + stderr)

    def test_350___get_wsroot___no_client(self):
        wsname = self.wsname
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, wsname)
        wsroot = w._get_wsroot()
        self.assertEqual(wsroot, os.path.join(w.wsdisk, wsname))

    def test_351___get_wsroot___with_client(self):
        wsname = ':icm:'
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, wsname)
        w.wsclient = 'userid.project.variant.number'
        wsroot = w._get_wsroot()
        self.assertEqual(wsroot, os.path.join(w.wsdisk, w.wsclient))

    @patch('dmx.abnrlib.icm.ICManageCLI.add_workspace')
    def test_400___create_workspace___pass(self, mock_add_workspace):
        clientname = 'liang.proA.varA.123'
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, 'aaa')
        mock_add_workspace.return_value = clientname
        w._create_workspace()
        self.assertEqual(w.wsclient, clientname)

       
    def test_502___get_dmx_cmd(self):
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname)
        ret = w._get_dmx_cmd()
        self.assertRegexpMatches(ret, '^.+dmx workspace populate -p {} -i {} -b {} -w {} .+ ; '.format(self.project, self.ip, self.bom, self.wsname))

    
    def test_503___get_final_cmd(self):
        w = self.wp.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname)
        os.environ['DB_FAMILIES'] = 'a b c'
        ret = w._get_final_cmd()
        print(ret)
        self.assertRegexpMatches(ret, '^/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost \'arc .+ -- \'"\'"\'setenv DMX_WORKSPACE .+;setenv DB_FAMILIES .+dmx workspace populate -p {} -i {} -b {} -w {}.+; \'"\'"\'\''.format(self.project, self.ip, self.bom, self.wsname))


    def test_600___get_user_missing_groups_from_pvc(self):
        #w = self.wp.WorkspacePopulate(self.project, self.ip, 'snap-liotest1-multidie1', self.wsname)
        w = self.wp.WorkspacePopulate(self.project, self.ip, 'snap-1', self.wsname)
        missing_groups = w.get_user_missing_groups_from_pvc()
        self.assertEqual(missing_groups, [u'haha'])

    def test_605___remove_arms_from_groups(self):
        groups =  ['haha', 'hahaarmhoho', 'misgdr', 'misarmsgdr', 'misrnr', 'misarmsrnr']
        ans =  ['haha', 'misgdr', 'misrnr']
        w = self.wp.WorkspacePopulate(self.project, self.ip, 'snap-liotest1-multidie1', self.wsname)
        ret = w.remove_arms_from_groups(groups)
        self.assertEqual(sorted(ans), sorted(ret))


    def test_620___is_bom_immutable___False(self):
        w = self.wp.WorkspacePopulate('p', 'v', 'c', 'wsnamw')
        ret = w._is_bom_immutable()
        self.assertEqual(ret, False)

    def test_621___is_bom_immutable___True(self):
        w = self.wp.WorkspacePopulate('p', 'v', 'snap-blablabl', 'wsnamw')
        ret = w._is_bom_immutable()
        self.assertEqual(ret, True)

    @patch('dmx.utillib.utils.check_proj_restrict', return_value=1)
    def test__1001__is_dmx_workspace_in_approved_disk(self, mock_check_proj_restrict):
        w = self.wp.WorkspacePopulate('p', 'v', 'snap-blablabl', 'wsnamw')
        self.assertTrue(w.is_dmx_workspace_in_approved_disk())


if __name__ == '__main__':
    logging.basicConfig(format="[%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(), level=logging.DEBUG)
    
    unittest.main()

