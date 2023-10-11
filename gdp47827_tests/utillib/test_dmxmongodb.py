#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_dmxmongodb.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from future import standard_library
standard_library.install_aliases()
import unittest
from mock import patch
from datetime import date
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.utils import *
import io
from dmx.utillib.dmxmongodbbase import DmxMongoDbBase
import pymongo
class TestDmxMongoDbbase(unittest.TestCase):
    '''
    Tests the dmx.utillib.dmxmongodbbase library
    '''

    def setUp(self):
        self.uri = 'mongodb://DMX_TEST_so:tA5Y4Zf80H9YxT8@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/DMX_TEST?replicaSet=mongo8150'
        self.database = 'DMX_TEST'
        self.dmxmongodb = DmxMongoDbBase(self.uri, self.database)

    def test_010__connect__pass_valid_uri(self):
        self.assertEqual(dmx.utillib.dmxmongodbbase.DmxMongoDbBase, type(self.dmxmongodb.connect()))

    def test_011__connect__fail_invalid_uri(self):
        self.dmxmongodb = DmxMongoDbBase('invalid uri', self.database)
        with self.assertRaises(pymongo.errors.ServerSelectionTimeoutError):
            self.dmxmongodb.connect()

if __name__ == '__main__':
    unittest.main()
