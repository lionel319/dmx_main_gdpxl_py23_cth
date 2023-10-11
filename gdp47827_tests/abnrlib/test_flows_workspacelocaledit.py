#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_workspacelocaledit.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $


from future import standard_library
standard_library.install_aliases()
from builtins import oct
import unittest
from mock import patch
import os, sys
import datetime
import time
import tempfile
from mock import patch
if sys.version_info[0] > 2:
    from io import StringIO
else:
    from StringIO import StringIO

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.abnrlib.flows.workspacelocaledit
import dmx.utillib.utils
import dmx.abnrlib.config_factory

class TestFlowWorkspaceLocalEdit(unittest.TestCase):

    def setUp(self):
        self.wp = dmx.abnrlib.flows.workspacelocaledit
        self.wsdisk = '/tmp'
        self.ip = 'IPA'
        self.deliverables = ['D1', 'D2']
        self.files = ['F1', 'F2']
        temp = tempfile.NamedTemporaryFile()
        self.link_file = temp.name

        self.envvar = 'DMX_WORKSPACE' 
        self.wsdisk = '/tmp'
        os.environ[self.envvar] = self.wsdisk
        self.wle = self.wp.WorkspaceLocalEdit('WS1', self.ip, self.deliverables, self.files)
        self.wle.wsroot = 'mypath'

    def tearDown(self):
        self._undefine_envvar()

    def _undefine_envvar(self):
        os.environ.pop(self.envvar, None)
        os.environ.pop('DB_FAMILIES', None)


    @patch('dmx.abnrlib.flows.workspacelocaledit.glob.glob')
    @patch('dmx.abnrlib.flows.workspacelocaledit.os.path.exists')
    def test_100___get_edit_path__path_exists(self, mock_os_path_exists, mock_glob_glob):
        result = ['mypath/IPA/D1/F1', 'mypath/IPA/D1/F2', 'mypath/IPA/D2/F1', 'mypath/IPA/D2/F2']
        mock_glob_glob.return_value = result 
        mock_os_path_exists.return_value = True
        self.assertEqual(result, self.wle._get_edit_path())

    @patch('dmx.abnrlib.flows.workspacelocaledit.glob.glob')
    @patch('dmx.abnrlib.flows.workspacelocaledit.os.path.exists')
    def test_101___get_edit_path__path_not_exists(self, mock_os_path_exists, mock_glob_glob):
        result = ['mypath/IPA/D1/F1', 'mypath/IPA/D1/F2', 'mypath/IPA/D2/F1', 'mypath/IPA/D2/F2']
        mock_glob_glob.return_value = result
        mock_os_path_exists.return_value = False 
        with self.assertRaises(dmx.abnrlib.flows.workspacelocaledit.WorkspaceLocalEditError):
            self.wle._get_edit_path()

    @patch('dmx.abnrlib.flows.workspacelocaledit.os.chmod')
    def test_200___make_editable_by_chmod__symlink_true(self, mock_os_chmod):
        mock_os_chmod.return_value = True 

        linkfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'link', 'link_file')

        path = [self.link_file, 'path/file2']
        #Create sylink to test symlink
        os.symlink(linkfile, self.link_file)

        # Copied from https://stackoverflow.com/questions/33767627/python-write-unittest-for-console-print
        capturedOutput = StringIO()          # Create StringIO object
        sys.stdout = capturedOutput                   #  and redirect stdout.
        self.wle.make_editable_by_chmod(path, preview=False)
        sys.stdout = sys.__stdout__ 
        result = '{} is locally editable\n'.format(self.link_file)
        self.assertIn(result, capturedOutput.getvalue())
        os.remove(self.link_file)


    def test_201___make_editable_by_chmod__stat_770(self):
        linkfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'link', 'link_file')

        path = [self.link_file]
        #Create sylink to test symlink
        os.symlink(linkfile, self.link_file)

        # Copied from https://stackoverflow.com/questions/33767627/python-write-unittest-for-console-print
        capturedOutput = StringIO()          # Create StringIO object
        sys.stdout = capturedOutput                   #  and redirect stdout.
        self.wle.make_editable_by_chmod(path, preview=False)
        sys.stdout = sys.__stdout__ 
        st = os.stat(self.link_file)
        self.assertIn('0770' ,oct(st.st_mode))
        os.remove(self.link_file)



if __name__ == '__main__':
    unittest.main()

