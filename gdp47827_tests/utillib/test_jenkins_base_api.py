#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_jenkins_base_api.py $
# $Revision: #1 $
# $Change: 7437460 $
# $DateTime: 2023/01/09 18:36:07 $
# $Author: lionelta $

import os
import sys
import unittest
import logging
import re
import xml.etree.ElementTree as ET

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.jenkins_base_api


class TestJenkinsBaseApi(unittest.TestCase):
    
    def setUp(self):
        self.tc = dmx.utillib.jenkins_base_api.JenkinsBaseApi()

        self.parentProjectId = 'PsgCicq___Production'
        self.projectId = 'PsgCicq___i10socfm'
        self.buildtypeId = 'PsgCicq___i10socfm___liotestfc1___test3'
        self.buildtypeName = 'i10socfm.liotestfc1.test3'

    def tearDown(self):
        pass

    def test_001___list_jobs(self):
        ret = self.tc.list_jobs()
        self.assertIn('template', ret)
        self.assertIn('da_i16.dai16liotest1.py23test1', ret)


    def test_002___get_job(self):
        tree, tmpfile = self.tc.get_job('template')
        s = ET.tostring(tree.getroot())
        self.assertIn(b'<name>CICQ_IP</name>', ET.tostring(tree.getroot()))


    def test_003___get_elementtree_param(self):
        tree, tmpfile = self.tc.get_job('template')
        ret = self.tc.get_elementtree_param(tree, 'CICQ_IP')
        self.assertEqual(ret, 'jtag_common')


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

