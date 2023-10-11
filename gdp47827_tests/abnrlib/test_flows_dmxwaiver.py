#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the quick icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_dmxwaiver.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import sys
import os
import re
#from bson.objectid import ObjectId
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.abnrlib.flows.workspace as workspace
from dmx.utillib.utils import run_command
from dmx.utillib.dmxmongodbbase import DmxMongoDbBase
from dmx.abnrlib.flows.dmxwaiver import DmxWaiver
from mock import patch
from dmx.errorlib.exceptions import *
from bson import *
import bson
from datetime import datetime

class MockInsertOne():
    inserted_id = '0'

class TestDmxWaiver(unittest.TestCase):
    '''
    Tests the SimpleConfig class
    '''

    def setUp(self):
        ''' Generic test setup '''

        # Create a temporary collection for testing
        self.dmxwaiver = DmxWaiver('prod')
        #self.db.create_collection('unit_tests')
        self.thread = 'FM6revA0'
        self.ms = '4.0'
        self.username = 'wplim'
        self.fakewaiver = {'ip' : 'ip',
          'deliverable' : 'deliverable',
          'subflow' : 'subflow',
          'reason': 'reason',
          'error': 'error',
          'thread': 'thread',
          'milestone': 'milestone',
          'user': 'username',
          'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
 
        self.fakewaiver2 = {'ip' : 'ip',
          'deliverable' : 'deliverable',
          'subflow' : 'subflow',
          'reason': 'reason',
          'error': 'error',
          'thread': 'thread',
          'milestone': 'milestone',
          'user': 'username',
          'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
 
        fo = open('tnrwaivers_test.csv','w+')
        fo.write('"*","sta","*","autogen by dmx workspace check","FAILED validation of /liotest1/sta/audit/audit.aib_ssm.sta.xml: checksum for /liotest1/rdf/file2 failed: can not access file"')
        fo.close()

        fo = open('tnrwaivers_test_wrong_format.csv','w+')
        fo.write('"sta","*","autogen by dmx workspace check","FAILED validation of /liotest1/sta/audit/audit.aib_ssm.sta.xml: checksum for /liotest1/rdf/file2 failed: can not access file"')
        fo.close()

        fo = open('tnrwaivers_test_blank.csv','w+')
        fo.close()

        self.tnrwaiver_wrg_format = 'tnrwaivers_test_wrong_format.csv'
        self.tnrwaiver_file = 'tnrwaivers_test.csv'
        self.tnrwaiver_blank = 'tnrwaivers_test_blank.csv'

    def tearDown(self):
        # Drop temporary collection
        #self.db.drop_collection('unit_tests')
        os.remove(self.tnrwaiver_file)
        os.remove(self.tnrwaiver_wrg_format)

        
    def test_060__get_waivers__pass(self):
        ip = '*' 
        thread = 'GDRrevB0'
        self.assertEqual(0, self.dmxwaiver.get_waivers(ip=ip, thread=thread))
         
    def test_061__get_waivers__fail_no_ip(self):
        ip = 'fakeip' 
        thread = 'FM6revA0'
        with self.assertRaises(DmxErrorTRWV01):
            self.dmxwaiver.get_waivers(ip=ip, thread=thread)
             
    def test_062__get_waivers__fail_no_thread(self):
        ip = 'liotest1' 
        thread = 'fakethread'
        with self.assertRaises(DmxErrorRMTH01):
            self.dmxwaiver.get_waivers(ip=ip, thread=thread)

    def test_063__get_waivers__fail_no_thread_no_ip(self):
        ip = 'fakeip' 
        thread = 'fakethread'
        with self.assertRaises(DmxErrorRMTH01):
            self.dmxwaiver.get_waivers(ip=ip, thread=thread)
            
    def test_064__get_waivers__pass_data_none(self):
        # if none then print all
        self.assertEqual(0, self.dmxwaiver.get_waivers())
  
    def test_070__delete_waivers_pass_one_id(self):
        db_id = self.dmxwaiver.dmxwaiver.insert_one_waiver(self.fakewaiver)
        self.assertEqual(0, self.dmxwaiver.delete_waivers([str(db_id)]))

    def test_071__delete_waivers_pass_multiple_id(self):
        # not sure why use same fakewaiver will create duplicated key error, currently use different first
        db_id = self.dmxwaiver.dmxwaiver.insert_one_waiver(self.fakewaiver)
        db_id2 = self.dmxwaiver.dmxwaiver.insert_one_waiver(self.fakewaiver2)
        self.assertEqual(0, self.dmxwaiver.delete_waivers([str(db_id), str(db_id2)]))

    def test_072__delete_waivers_fail_no_such_id(self):
        #self.assertEqual(1, self.dmxwaiver.delete_waivers([]))
        with self.assertRaises(bson.errors.InvalidId):
            self.dmxwaiver.delete_waivers(['123'])

    def test_080__get_hsdes_mapping(self):
        self.assertIn(u'DMDrevA0', self.dmxwaiver.get_hsdes_mapping_data().keys())

if __name__ == '__main__':
    unittest.main(verbosity=2)

    #suite = unittest.TestLoader().loadTestsFromTestCase(FastTest)
    #unittest.TextTestRunner(verbosity=2).run(suite)
