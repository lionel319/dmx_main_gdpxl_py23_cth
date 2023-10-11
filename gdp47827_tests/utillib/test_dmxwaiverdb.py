#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_dmxwaiverdb.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from future import standard_library
standard_library.install_aliases()
import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.utils import *
import io
from dmx.utillib.dmxwaiverdb import DmxWaiverDb
import pymongo
from bson import *
import bson
from datetime import date, datetime
from dmx.utillib.dmxmongodbbase import DmxMongoDbBase

class TestDmxWaiverDb(unittest.TestCase):
    '''
    Tests the dmx.utillib.dmxwaiverdb library
    '''
    def setUp(self):
        self.dmxwaiver = DmxWaiverDb('test')
        self.waiverdata = {'ip' : 'ip',
          'deliverable' : 'deliverable',
          'subflow' : 'subflow',
          'reason': 'reason',
          'error': 'error',
          'thread': 'thread',
          'milestone': 'milestone',
          'user': 'username',
          'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
         
    def test_010__insert_one_waiver__pass_default_waiver(self):
        waiver_id = self.dmxwaiver.insert_one_waiver(self.waiverdata)
        self.assertEqual(bson.objectid.ObjectId, type(waiver_id))
        data = {'_id':waiver_id}
        self.assertEqual(1, self.dmxwaiver.db.waivers.delete_one(data).deleted_count)

    def test_011__insert_one_waiver__pass_different_format(self):
        waiverdata = {'testing': 'test1'}
        waiver_id = self.dmxwaiver.insert_one_waiver(waiverdata)
        self.assertEqual(bson.objectid.ObjectId, type(waiver_id))
        data = {'_id':waiver_id}
        self.assertEqual(1, self.dmxwaiver.db.waivers.delete_one(data).deleted_count)

    def test_012__insert_one_waiver__fail_blank_data(self):
        waiverdata = {}
        with self.assertRaises(DmxErrorTRWV01):
            waiver_id = self.dmxwaiver.insert_one_waiver(waiverdata)

    def test_020__set_waivers_field_by_hsdes(self):
        self.dmxwaiver.set_waivers_approver_field_by_approver('junkeatt', last_approval_date=datetime.today().strftime('%Y-%m-%d %H:%M:%S'))


    def test_030__find_mapping_data__(self):
        #result = [u'DMDrevA0', u'FM7revA0', u'FM8revA0', u'FM5revA0', u'updated_by', u'GDRrevB0', u'FP6revA0', u'FP4revA0', u'FM6revA1', u'FM6revA0', u'FM3revA0', u'GDRrevA0', u'RNRrevA0', u'FM6revB0', u'RNRrevB0', u'date', u'_id', u'FP8revA0', u'KM5revA0']
        self.assertIn(u'DMDrevA0', list(self.dmxwaiver.find_mapping_data()[0].keys()))
    

if __name__ == '__main__':
    unittest.main()
