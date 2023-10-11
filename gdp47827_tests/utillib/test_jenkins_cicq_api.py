#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_jenkins_cicq_api.py $
# $Revision: #1 $
# $Change: 7437460 $
# $DateTime: 2023/01/09 18:36:07 $
# $Author: lionelta $

import os
import sys
import unittest
import logging
import re

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.jenkins_cicq_api


class TestJenkinsCicqApi(unittest.TestCase):
    
    def setUp(self):

        self.project = 'da_i16'
        self.ip = 'dai16liotest1'
        self.thread = 'py23test1'
        self.jobname = f'{self.project}.{self.ip}.{self.thread}'
        self.tc = dmx.utillib.jenkins_cicq_api.JenkinsCicqApi(self.project, self.ip, self.thread)

    def tearDown(self):
        pass

    def test_001___get_all_threads_name(self):
        ret = self.tc.get_all_threads_name()
        print(f"ret: {ret}")
        self.assertIn(self.thread, ret)

    def test_002___decompose_jobname(self):
        ret = self.tc.decompose_jobname(self.jobname)
        self.assertEqual([self.project, self.ip, self.thread], ret)

    def test_003___get_parameter(self):
        ret = self.tc.get_parameter("CICQ_IP")
        self.assertEqual(ret, self.ip)


    def test_004___get_centralize_workdir(self):
        ret = self.tc.get_centralize_workdir()
        self.assertEqual(ret, '/nfs/site/disks/psg_cicq_1/users/cicq/da_i16.dai16liotest1.py23test1')

    def test_005___get_refbom(self):
        ret = self.tc.get_refbom()
        self.assertEqual(ret, 'for_test_cicq_1')

    def test_006___get_jobname_by_thread(self):
        ret = self.tc.get_jobname_by_thread(self.thread)
        self.assertEqual(ret, self.jobname)

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

