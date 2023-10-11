#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_icmlibrary.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
from mock import patch
from datetime import date
import os, sys
import logging
import socket
import datetime
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.loggingutils
LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
import dmx.abnrlib.icm
import dmx.abnrlib.icmlibrary

class TestIcmLibrary(unittest.TestCase):

    def setUp(self):
        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest1'
        self.libtype = 'ipspec'
        self.library = 'dev'
        self.lib_release = 'snap-fortnr_1'
        self.changenum = 2482
        self.asadmin = '--user=icmanage'

        ### Existing library/release in icm db
        self.elib = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, self.libtype, self.library, use_db=True, preview=True)
        self.erel = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, self.libtype, self.library, self.lib_release, use_db=True, preview=True)

        ### Existing library/release using defprop_from_icm method
        a = {"location":"liotest1/ipspec","uri":"p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/liotest1/ipspec/dev/...","created-by":"lionelta","laugh":"haha","id":"L1247063","type":"library","name":"dev","path":"/intel/Raton_Mesa/liotest1/ipspec/dev","created":"2020-09-23T10:06:31.322Z","modified":"2020-10-26T07:23:42.941Z","change":"@now","libtype":"ipspec"}
        b = {"uri":"p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/liotest1/ipspec/dev/...@2482","created-by":"lionelta","cry":"waaaa","id":"R2245321","type":"release","name":"snap-4","path":"/intel/Raton_Mesa/liotest1/ipspec/dev/snap-4","created":"2020-10-13T09:41:52.384Z","modified":"2020-10-26T07:31:22.695Z","change":"@2482","libtype":"ipspec"}
        self.dlib = dmx.abnrlib.icmlibrary.IcmLibrary(defprop_from_icm=a)
        self.drel = dmx.abnrlib.icmlibrary.IcmLibrary(defprop_from_icm=b)

        ### Non-existance library/release in icm db
        self.nlib = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, self.libtype, 'xlib', use_db=True, preview=True)
        self.nrel = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, self.libtype, 'xlib', 'xrel', use_db=True, preview=True)

    def t(self):
        pass
        
    ##############################################################################
    ### TEST 0** are all tests on library/release which are existing in ICM db 
    ##############################################################################
    def test_000___get_library_properties(self):
        print(self.elib._defprops)
        a = self.elib._defprops
        self.assertEqual(a['name'], 'dev')
        self.assertEqual(a['uri'], 'p4://scylicm.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...')
        self.assertEqual(a['location'], 'rtmliotest1/ipspec')
        self.assertEqual(a['path'], '/intel/Raton_Mesa/rtmliotest1/ipspec/dev')
        self.assertEqual(a['libtype'], 'ipspec')
        self.assertEqual(a['type'], 'library')
        self.assertEqual(a['change'], '@now')

    def test_000___get_release_properties(self):
        print(self.erel._defprops)
        a = self.erel._defprops
        self.assertEqual(a['name'], self.lib_release)
        self.assertEqual(a['uri'], 'p4://scylicm.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/rtmliotest1/ipspec/dev/...@15')
        self.assertEqual(a['path'], '/intel/Raton_Mesa/rtmliotest1/ipspec/dev/snap-fortnr_1')
        self.assertEqual(a['libtype'], 'ipspec')
        self.assertEqual(a['type'], 'release')
        self.assertEqual(a['change'], '@15')

    def test_001___get_user_properties___existing_library(self):
        p = self.elib.get_user_properties()
        print("==p: {}".format(p))
        self.assertEqual(p['Owner'], 'jwquah')

    def test_001___get_user_properties___existing_release(self):
        p = self.erel.get_user_properties()
        print("==p: {}".format(p))
        self.assertEqual(p['description'], "'testing'")

    def test_002___get_full_name___existing_library(self):
        self.assertEqual(self.elib.get_full_name(), 'Raton_Mesa/rtmliotest1/ipspec/dev')

    def test_002___get_full_name___existing_release(self):
        self.assertEqual(self.erel.get_full_name(), 'Raton_Mesa/rtmliotest1/ipspec/dev/snap-fortnr_1')

    def test_010___is_saved___exist_library(self):
        self.assertTrue(self.elib.is_saved())

    def test_010___is_saved___exist_release(self):
        self.assertTrue(self.erel.is_saved())

    def test_011___save_already_saved_library(self):
        self.elib.save()
        self.assertEqual(self.elib._FOR_REGTEST, 'already saved')

    def test_011___save_already_saved_release(self):
        self.erel.save()
        self.assertEqual(self.erel._FOR_REGTEST, 'already saved')

    def test_012___add_property___error(self):
        with self.assertRaisesRegexp(Exception, "add/modify system default properties is prohibited"):
            self.elib.add_property('uri', 'abcd')


    ##############################################################################
    ### TEST 3** are all tests on library/release using defprop_from_icm method
    ##############################################################################
    def test_300___get_library_properties(self):
        pprint(self.dlib._defprops)
        self.assertEqual(self.dlib._defprops, {"location":"liotest1/ipspec","uri":"p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/liotest1/ipspec/dev/...","created-by":"lionelta","laugh":"haha","id":"L1247063","type":"library","name":"dev","path":"/intel/Raton_Mesa/liotest1/ipspec/dev","created":"2020-09-23T10:06:31.322Z","modified":"2020-10-26T07:23:42.941Z","change":"@now","libtype":"ipspec"})

    def test_300___get_release_properties(self):
        print(self.drel._defprops)
        self.assertEqual(self.drel._defprops, {"uri":"p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/Raton_Mesa/liotest1/ipspec/dev/...@2482","created-by":"lionelta","cry":"waaaa","id":"R2245321","type":"release","name":"snap-4","path":"/intel/Raton_Mesa/liotest1/ipspec/dev/snap-4","created":"2020-10-13T09:41:52.384Z","modified":"2020-10-26T07:31:22.695Z","change":"@2482","libtype":"ipspec"})

    def test_301___get_user_properties___existing_library(self):
        self.assertEqual(self.dlib.get_user_properties(), {'laugh': 'haha'})

    def test_301___get_user_properties___existing_release(self):
        self.assertEqual(self.drel.get_user_properties(), {'cry': 'waaaa'})

    def test_302___get_full_name___existing_library(self):
        self.assertEqual(self.dlib.get_full_name(), 'Raton_Mesa/liotest1/ipspec/dev')

    def test_302___get_full_name___existing_release(self):
        self.assertEqual(self.drel.get_full_name(), 'Raton_Mesa/liotest1/ipspec/dev/snap-4')

    def test_310___is_saved___exist_library(self):
        self.assertTrue(self.dlib.is_saved())

    def test_310___is_saved___exist_release(self):
        self.assertTrue(self.drel.is_saved())

    def test_311___save_already_saved_library(self):
        self.dlib.save()
        self.assertEqual(self.dlib._FOR_REGTEST, 'already saved')

    def test_311___save_already_saved_release(self):
        self.drel.save()
        self.assertEqual(self.drel._FOR_REGTEST, 'already saved')

    def test_312___add_property___error(self):
        with self.assertRaisesRegexp(Exception, "add/modify system default properties is prohibited"):
            self.dlib.add_property('uri', 'abcd')





    ##############################################################################
    ### TEST 5** are all tests on library/release which are NON-EXITANCE in ICM db 
    ##############################################################################
    def test_502___get_full_name___non_existing_library(self):
        self.assertEqual(self.nlib.get_full_name(), 'Raton_Mesa/rtmliotest1/ipspec/xlib')

    def test_502___get_full_name___non_existing_release(self):
        self.assertEqual(self.nrel.get_full_name(), 'Raton_Mesa/rtmliotest1/ipspec/xlib/xrel')
    
    def test_510___is_saved___non_exist_library(self):
        self.assertFalse(self.nlib.is_saved())

    def test_510___is_saved___non_exist_release(self):
        self.assertFalse(self.nrel.is_saved())

    def test_511___save_release___invalid_release_name(self):
        self.nrel.save()
        self.assertIn('xrel is not a valid release name. It must start with (REL, PREL, snap-).', self.nrel._FOR_REGTEST)

    def test_511___save_release___libtype_not_exist(self):
        x = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, 'xlibtype', self.library, 'snap-1', use_db=True, preview=True)
        x.save()
        self.assertIn('Cannot create a release on a non-existing library', x._FOR_REGTEST)

    def test_511___save_release___library_not_exist(self):
        x = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, self.libtype, 'xxxlibrary', 'snap-1', use_db=True, preview=True)
        x.save()
        self.assertEqual('Cannot create a release on a non-existing library:Raton_Mesa/rtmliotest1/ipspec/xxxlibrary/snap-1', x._FOR_REGTEST)

    def test_520___clone_library___library2library(self):
        x = self.elib.clone('xxxlib') 
        x.save()
        print(x._icm._FOR_REGTEST)
        ans = ['gdp', self.asadmin, 'create', 'library', '/intel/Raton_Mesa/rtmliotest1/ipspec/xxxlib', '--set', 'location=rtmliotest1/ipspec', '--from', '/intel/Raton_Mesa/rtmliotest1/ipspec/dev']
        
        self.assertEqual(x._icm._FOR_REGTEST, ans)

    def test_520___clone_library___library2release(self):
        x = self.elib.clone('RELxxx') 
        x.save()
        print(x._icm._FOR_REGTEST)
        self.assertEqual(x._icm._FOR_REGTEST, ['gdp', self.asadmin, 'create', 'release', '/intel/Raton_Mesa/rtmliotest1/ipspec/dev/RELxxx'])

    def test_520___clone_library___release2library(self):
        x = self.erel.clone('xxxlib') 
        x.save()
        print(x._icm._FOR_REGTEST)
        ans = ['gdp', self.asadmin, 'create', 'library', '/intel/Raton_Mesa/rtmliotest1/ipspec/xxxlib', '--set', 'location=rtmliotest1/ipspec', '--from', '/intel/Raton_Mesa/rtmliotest1/ipspec/dev/snap-fortnr_1']
        self.assertEqual(x._icm._FOR_REGTEST, ans)

    def test_520___clone_library___release2release(self):
        x = self.erel.clone('RELxxx') 
        x.save()
        print(x._icm._FOR_REGTEST)
        self.assertEqual(x._icm._FOR_REGTEST, ['gdp', self.asadmin, 'create', 'release', '/intel/Raton_Mesa/rtmliotest1/ipspec/dev/RELxxx', '--from', '@15'])


if __name__ == '__main__':
    unittest.main()
