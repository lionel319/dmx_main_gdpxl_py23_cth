#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr bomcheck plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_checkconfigs.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.abnrlib.flows.checkconfigs
from dmx.abnrlib.config_factory import ConfigFactoryError
from dmx.abnrlib.icm import ICManageCLI
from pprint import pprint

class TestCheckConfigs(unittest.TestCase):

    @patch("dmx.abnrlib.flows.checkconfigs.ICManageCLI.project_exists")
    @patch("dmx.abnrlib.flows.checkconfigs.ICManageCLI.variant_exists")
    def setUp(self, mock_variant_exists, mock_project_exists):
        self.project = 'project'
        self.variant = 'variant'
        self.config = 'config'
        self.preview = True
        mock_variant_exists.return_value = True
        mock_project_exists.return_value = True
        self.cc = dmx.abnrlib.flows.checkconfigs.CheckConfigs(self.project, self.variant, self.config)

    def test_010___add_pvc_to_allconfigs___1(self):
        data = {'syncpoint': 'sp1', 'parent': ['pp', 'vv', 'cc']}
        self.cc.add_pvc_to_allconfigs('p1', 'v1', 'c1')
        self.cc.add_pvc_to_allconfigs('p2', 'v2', 'c2', data=data)
        pprint(self.cc.allconfigs)
        ans = {'p1': {'v1': {'c1': {}}}, 'p2': {'v2': {'c2': {'parent': ['pp', 'vv', 'cc'], 'syncpoint': 'sp1'}}}}
        self.assertEqual(self.cc.allconfigs, ans)

    def test_011___add_pvc_to_allconfigs___2(self):
        data = {'syncpoint': 'sp1', 'parent': ['pp', 'vv', 'cc']}
        self.cc.add_pvc_to_allconfigs('p1', 'v1', 'c1')
        self.cc.add_pvc_to_allconfigs('p2', 'v2', 'c2', data=data)
        self.cc.add_pvc_to_allconfigs('p3', 'v3', 'c3', data=data)
        pprint(self.cc.allconfigs)
        ans = {'p1': {'v1': {'c1': {}}},
         'p2': {'v2': {'c2': {'parent': ['pp', 'vv', 'cc'], 'syncpoint': 'sp1'}}},
         'p3': {'v3': {'c3': {'parent': ['pp', 'vv', 'cc'], 'syncpoint': 'sp1'}}}}
        self.assertEqual(self.cc.allconfigs, ans)
    
    def test_012___add_pvc_to_allconfigs___3(self):
        self.cc.add_pvc_to_allconfigs('p1', 'v1', 'c1')
        self.cc.add_pvc_to_allconfigs('p2', 'v2', 'c2')
        self.cc.add_pvc_to_allconfigs('p2', 'v3', 'c3')
        pprint(self.cc.allconfigs)
        ans = {'p1': {'v1': {'c1': {}}}, 'p2': {'v2': {'c2': {}}, 'v3': {'c3': {}}}}
        self.assertEqual(self.cc.allconfigs, ans)

    @patch('dmx.abnrlib.flows.checkconfigs.CheckConfigs.get_all_configs')
    def test_100___run___no_conflicts(self, mocka):
        mocka.return_value = []
        data = {'syncpoint': 'sp1', 'parent': ['pp', 'vv', 'cc']}
        self.cc.allconfigs = {
            'p1': 
                {'v1': 
                    {'c1': data},
                'v4': 
                    {'c4': data}
                }, 
            'p2': 
                {'v2': 
                    {'c2': data}, 
                'v3': 
                    {'c3': data}
                }
        }
        ans = self.cc.run()
        self.assertEqual(ans, {})

    @patch('dmx.abnrlib.flows.checkconfigs.CheckConfigs.get_all_configs')
    def test_101___run___got_conflicts___1(self, mocka):
        mocka.return_value = []
        data = {'syncpoint': 'sp1', 'parent': ['pp', 'vv', 'cc']}
        self.cc.allconfigs = {
            'p1': 
                {'v1': 
                    {'c1': data},
                'v4': 
                    {'c4': data}
                }, 
            'p2': 
                {'v2': 
                    {'c2': data, 'c3':data}, 
                'v3': 
                    {'c3': data}
                }
        }
        ret = self.cc.run()
        ans1 = {('p2', 'v2'): 
                [['c3', "syncpoint/pvc: sp1/['pp', 'vv', 'cc']"],
                ['c2', "syncpoint/pvc: sp1/['pp', 'vv', 'cc']"]]}
        ans2 = {('p2', 'v2'): 
                [['c2', "syncpoint/pvc: sp1/['pp', 'vv', 'cc']"],
                ['c3', "syncpoint/pvc: sp1/['pp', 'vv', 'cc']"]]}
        print
        pprint(ret)
        self.assertTrue(ret == ans1 or ret == ans2)



if __name__ == '__main__':
    unittest.main()
