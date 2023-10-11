#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_arcutils.py $
# $Revision: #3 $
# $Change: 7444498 $
# $DateTime: 2023/01/15 19:15:53 $
# $Author: lionelta $

from __future__ import print_function
import os
import sys
import unittest
import logging
import datetime 
import time

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.utillib.utils import run_command
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.arcutils


class TestArcUtils(unittest.TestCase):
    
    def setUp(self):
        self.a = dmx.utillib.arcutils.ArcUtils()

    def tearDown(self):
        pass

    def test_001___split_type_address_from_resource_name___single_level(self):
        self.assertEqual(self.a._split_type_address_from_resource_name('dmx/main'),
            ['dmx', '/main'])
    
    def test_002___split_type_address_from_resource_name___multi_level(self):
        self.assertEqual(self.a._split_type_address_from_resource_name('project/falcon/fm8dot2/4.0/phys/2018WW01'),
            ['project', '/falcon/fm8dot2/4.0/phys/2018WW01'])


    def test_010___convert_string_to_kvp(self):
        self.assertEqual(self.a._convert_string_to_kvp(''' 
                id : 12796762               \n                                                         
                type : interactive          \n                                            
              status : done                 \n                                          
                user : lionelta             \n
                name :                      \n
             command : /usr/intel/bin/tcsh  \n  '''), 
            {'command': '/usr/intel/bin/tcsh',
            'id': '12796762',
            'name': '',
            'status': 'done',
            'type': 'interactive',
            'user': 'lionelta'})

    def _test_020___get_kvp_from_resource(self):
        data = self.a.get_kvp_from_resource('dmx/9.2')
        self.assertEqual(data['type'], 'dmx')
        self.assertEqual(data['version'], '9.2')

    def test_030___get_arc_job(self):
        data = self.a.get_arc_job()
        self.assertTrue('user' in data)
        time.sleep(1)

    def test_040___get_resolved_list_from_resources___single_resource(self):
        data = self.a.get_resolved_list_from_resources('dmx/9.4')
        self.assertEqual(data, {'dmx': '/9.4'})
        time.sleep(1)

    def _test_041___get_resolved_list_from_resources___single_bundle(self):
        data = self.a.get_resolved_list_from_resources('project/falcon/fm8dot2/4.0/phys/2018WW01')
        self.assertEqual(data['dmx'], '/9.3')
        time.sleep(1)

    def _test_042___get_resolved_list_from_resources___mixture(self):
        data = self.a.get_resolved_list_from_resources('project/falcon/fm8dot2/4.0/phys/2018WW01, dmx/1.0')
        self.assertEqual(data['dmx'], '/1.0')
        time.sleep(1)

    def _test_051___get_resolved_list_from_resources___lego_single_bundle(self):
        data = self.a.get_resolved_list_from_resources('project/falcon/fm10/5.0/phys/2020WW26')
        from pprint import pprint
        pprint(data)
        self.assertEqual(data['dmx'], '/12.13a')

    def _test_052___get_resolved_list_from_resources___lego_mixture(self):
        data = self.a.get_resolved_list_from_resources('project/falcon/fm10/5.0/phys/2020WW26, dmx/1.0')
        self.assertEqual(data['dmx'], '/1.0')

    def _test_140___get_resolved_list_from_resources_2___single_resource(self):
        data = self.a.get_resolved_list_from_resources_2('dmx/9.4')
        self.assertEqual(data, {'dmx': '/9.4'})

    def _test_141___get_resolved_list_from_resources_2___single_bundle(self):
        data = self.a.get_resolved_list_from_resources_2('project/falcon/fm8dot2/4.0/phys/2018WW01')
        self.assertEqual(data['dmx'], '/9.3')

    def _test_142___get_resolved_list_from_resources_2___mixture(self):
        data = self.a.get_resolved_list_from_resources_2('project/falcon/fm8dot2/4.0/phys/2018WW01, dmx/1.0')
        self.assertEqual(data['dmx'], '/1.0')

    def _test_151___get_resolved_list_from_resources_2___lego_single_bundle(self):
        data = self.a.get_resolved_list_from_resources_2('project/falcon/fm10/5.0/phys/2020WW26')
        self.assertEqual(data['dmx'], '/12.13a')

    def _test_152___get_resolved_list_from_resources_2___lego_mixture(self):
        data = self.a.get_resolved_list_from_resources_2('project/falcon/fm10/5.0/phys/2020WW26, dmx/1.0')
        self.assertEqual(data['dmx'], '/1.0')



    def test_060___sort_resource_string___1(self):
        data = self.a.sort_resource_string('project/falcon/branch/fp8main/0.8/phys/rc,dmx/latestdev,dmxdata/latestdev,cicq/latestdev')
        self.assertEqual(data, 'project/falcon/branch/fp8main/0.8/phys/rc,dmx/latestdev,dmxdata/latestdev,cicq/latestdev')

    def test_060___sort_resource_string___2(self):
        data = self.a.sort_resource_string('dmxdata/latestdev,dmx/latestdev,project/falcon/branch/fp8main/0.8/phys/rc,cicq/latestdev')
        self.assertEqual(data, 'project/falcon/branch/fp8main/0.8/phys/rc,dmxdata/latestdev,dmx/latestdev,cicq/latestdev')


    def _test_200___get_datetime_object___from_resource(self):
        data = self.a.get_kvp_from_resource('dmxdata/13.11')
        ret = self.a.get_datetime_object(data['created_at'])
        print(ret)
        site = os.getenv("ARC_SITE")
        if site == 'png':
            gol = datetime.datetime(2021, 4, 11, 21, 44, 28)
        else:
            gol = datetime.datetime(2021, 4, 11, 21, 45, 13)
        self.assertEqual(gol, ret)

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

