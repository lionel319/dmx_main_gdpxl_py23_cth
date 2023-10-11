#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_syncpointlock.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $


import unittest
from mock import patch
import os, sys
import datetime
import time
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.syncpointlib.syncpointlock_api

class TestSyncpointLock(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = dmx.syncpointlib.syncpointlock_api.SyncpointLockApi(servertype='test')
        cls.db.connect()
        cls.uniqid = 'unittest___{}'.format(time.time())
        cls.data = {
            'syncpoint': cls.uniqid
        }

   
    def test_100___is_syncpoint_locked(self):
        ret = self.db.is_syncpoint_locked('lionel')
        self.assertTrue(ret)

    def test_200___lock(self):
        ret = self.db.is_syncpoint_locked(self.uniqid)
        self.assertFalse(ret, "Checking and make sure this row is not found before lock() is called.")
        
        self.db.lock(self.uniqid)

        ret = self.db.is_syncpoint_locked(self.uniqid)
        self.assertTrue(ret, "Checking and make sure this row does exist after lock() is called.")


    def test_201___unlock(self):
        ret = self.db.is_syncpoint_locked(self.uniqid)
        self.assertTrue(ret, "Checking and make sure this row does exist before unlock() (after lock()) is called.")

        self.db.unlock(self.uniqid)

        ret = self.db.is_syncpoint_locked(self.uniqid)
        self.assertFalse(ret, "Checking and make sure this row is not found after unlock() is called.")




class TestSyncpointLockLog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = dmx.syncpointlib.syncpointlock_api.SyncpointLockLogApi(servertype='test')
        cls.db.connect()
        cls.uniqid = 'unittest___{}'.format(time.time())
        cls.data = {
            'syncpoint': cls.uniqid,
            'userid': 'unittester',
            'action': 'unittest'
        }

   
    def test_100___get_logs_by_user(self):
        ret = self.db.get_logs_by_user('lionelta')
        self.assertTrue(ret)


    def test_200___log(self):
        ret = self.db.get_logs_by_syncpoint(self.uniqid)
        self.assertFalse(ret, "Checking and make sure this row is not found before log() is called.")

        self.db.log(**self.data)

        ret = self.db.get_logs_by_syncpoint(self.uniqid)
        self.assertTrue(ret, "Checking and make sure this row does exist after log() is called.")


    def test_201___delete_logs(self):
        ret = self.db.get_logs_by_syncpoint(self.uniqid)
        self.assertTrue(ret, "Checking and make sure this row does exist before delete_logs(after log()) is called.")

        self.db._delete_logs(tablename=self.db.table, **self.data)

        ret = self.db.get_logs_by_syncpoint(self.uniqid)
        self.assertFalse(ret, "Checking and make sure this row is not found after delete_logs is called.")




if __name__ == '__main__':
    logging.basicConfig(format="[%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(), level=logging.DEBUG)
    unittest.main()
