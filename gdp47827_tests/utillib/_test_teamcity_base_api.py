#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/_test_teamcity_base_api.py $
# $Revision: #1 $
# $Change: 7692801 $
# $DateTime: 2023/07/10 20:10:49 $
# $Author: lionelta $

import os
import sys
import unittest
import logging
import re

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.teamcity_base_api


class TestTeamcityBaseApi(unittest.TestCase):
    
    def setUp(self):
        self.host = 'https://teamcity01-fm.devtools.intel.com'
        self.token = 'eyJ0eXAiOiAiVENWMiJ9.aTBEYmNvV3pKUUphakNjdUF4aUk0Sml2dkNn.NGRmYjk1NWYtOGNkZC00YTE3LWE5ODItZmM0ZDdkOTAyZjkx'
        self.tc = dmx.utillib.teamcity_base_api.TeamcityBaseApi(host=self.host, token=self.token)

        self.parentProjectId = 'PsgCicq___Production'
        self.projectId = 'PsgCicq___i10socfm'
        self.buildtypeId = 'PsgCicq___i10socfm___liotestfc1___test3'
        self.buildtypeName = 'i10socfm.liotestfc1.test3'

    def tearDown(self):
        pass

    def test_001___get_projects(self):
        ret = self.tc.get_projects()
        self.assertIn(self.parentProjectId, ret)

    def test_002___get_project(self):
        ret = self.tc.get_project(self.projectId)
        self.assertIn('parentProjectId="{}"'.format(self.parentProjectId), ret)

    def test_010___get_buildtypes(self):
        ret = self.tc.get_buildtypes()
        self.assertIn(self.buildtypeId, ret)

    def test_011___get_buildtype(self):
        ret = self.tc.get_buildtype(self.buildtypeId)
        self.assertIn('name="{}"'.format(self.buildtypeName), ret)

    def test_020___get_parameters_for_buildtype(self):
        ret = self.tc.get_parameters_for_buildtype(self.buildtypeId)
        self.assertIn('ARC_RESOURCES', ret)

    def test_021___get_parameter_for_buildtype(self):
        ret = self.tc.get_parameter_for_buildtype(self.buildtypeId, 'THREAD')
        self.assertIn('test3', ret)

    def test_030___get_latest_build_for_buildtype(self):
        btid = 'Dmx_Main_DmxCommandTests'
        ret = self.tc.get_latest_build_for_buildtype(btid)
        self.assertIn('number="68"', ret)
        self.assertIn('<startDate>20200430T060012-0700</startDate>', ret)

    def test_040___get_curl_command___normal(self):
        request = 'a/bb/ccc'
        ret = self.tc.get_curl_cmd(request)
        self.assertTrue(re.search('/app/rest/', ret))

    def test_040___get_curl_command___raw_request(self):
        request = 'a/bb/ccc'
        ret = self.tc.get_curl_cmd(request, raw_request=True)
        self.assertFalse(re.search('/app/rest/', ret))

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

