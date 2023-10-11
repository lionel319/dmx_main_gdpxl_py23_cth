#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmlib/test_ICManageConfiguration.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
from builtins import str
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
import dmx.dmlib.ICManageConfiguration


class TestICManageConfiguration(unittest.TestCase):

    def setUp(self):
        self.project = 'Raton_Mesa'
        self.ip = 'rtmliotest1'
        self.bom = 'dev'
        self.libtype = 'ipspec'
        self.icmc = dmx.dmlib.ICManageConfiguration.ICManageConfiguration(self.project, self.ip, self.bom)
        self.icmcl = dmx.dmlib.ICManageConfiguration.ICManageConfiguration(self.project, self.ip, self.bom, self.libtype)
        self.icmcfg = dmx.dmlib.ICManageConfiguration

    def test_000____getConfigContent(self):
        self.assertIsNotNone(self.icmcfg._getConfigContent(self.project, self.ip, self.bom))

    def test_001____repr_nolibtype(self):
        self.assertIsInstance(self.icmc, dmx.dmlib.ICManageConfiguration.ICManageConfiguration)

    def test_002____repr_gotlibtype(self):
        self.assertIsInstance(self.icmcl, dmx.dmlib.ICManageConfiguration.ICManageConfiguration)

    def test_003____str_nolibtype(self):
        result = '{}/{}/{}'.format(self.project, self.ip, self.bom)
        self.assertEqual(result, str(self.icmc))

    def test_004____str_goptlibtype(self):
        result = '{}/{}/{} for libType {}'.format(self.project, self.ip, self.bom, self.libtype)
        self.assertEqual(result, str(self.icmcl))

    def test_005____projectName(self):
        self.assertEqual(self.project, self.icmc.projectName)

    def test_006____ipName(self):
        self.assertEqual(self.ip, self.icmc.ipName)

    def test_007____configurationName(self):
        self.assertEqual(self.bom, self.icmc.configurationName)

    def test_008____libType(self):
        self.assertEqual(self.libtype, self.icmcl.libType)

    def test_008____libType_none(self):
        self.assertEqual(None, self.icmc.libType)

    def test_009____configuration(self):
        pprint(self.icmc.configurations)
        print(self.icmc.configurations)
        gold = [{u'name': u'two_libtypes', 'config': u'two_libtypes', 'variant': u'liotest1', 'project': u'i10socfm', u'path': u'/intel/i10socfm/liotest1/two_libtypes', 'libtype': u'', u'type': u'config'}, {u'name': u'fmx_dev', 'config': u'', 'variant': u'liotest1', 'project': u'i10socfm', u'path': u'/intel/i10socfm/liotest1/ipspec/fmx_dev', 'libtype': u'ipspec', u'type': u'library'}, {u'name': u'fmx_dev', 'config': u'', 'variant': u'liotest1', 'project': u'i10socfm', u'path': u'/intel/i10socfm/liotest1/reldoc/fmx_dev', 'libtype': u'reldoc', u'type': u'library'}]
        gold = [{u'name': u'dev', 'config': u'dev', 'variant': u'rtmliotest1', 'project': u'Raton_Mesa', u'path': u'/intel/Raton_Mesa/rtmliotest1/dev', 'libtype': u'', u'type': u'config'}, {u'name': u'dev', 'config': u'', 'variant': u'rtmliotest1', 'project': u'Raton_Mesa', u'path': u'/intel/Raton_Mesa/rtmliotest1/reldoc/dev', 'libtype': u'reldoc', u'type': u'library'}, {u'name': u'dev', 'config': u'', 'variant': u'rtmliotest1', 'project': u'Raton_Mesa', u'path': u'/intel/Raton_Mesa/rtmliotest1/bcmrbc/dev', 'libtype': u'bcmrbc', u'type': u'library'}, {u'name': u'dev', 'config': u'', 'variant': u'rtmliotest1', 'project': u'Raton_Mesa', u'path': u'/intel/Raton_Mesa/rtmliotest1/complibbcm/dev', 'libtype': u'complibbcm', u'type': u'library'}, {u'name': u'dev', 'config': u'', 'variant': u'rtmliotest1', 'project': u'Raton_Mesa', u'path': u'/intel/Raton_Mesa/rtmliotest1/complib/dev', 'libtype': u'complib', u'type': u'library'}, {u'name': u'dev', 'config': u'', 'variant': u'rtmliotest1', 'project': u'Raton_Mesa', u'path': u'/intel/Raton_Mesa/rtmliotest1/ipspec/dev', 'libtype': u'ipspec', u'type': u'library'}]
        self.assertEqual(self.icmc.configurations, gold)

    def test_010____isConfiguration_true(self):
        self.assertTrue(self.icmc.isConfiguration(self.project, self.ip, self.bom))

    def test_011____isConfiguration_false(self):
        self.assertFalse(dmx.dmlib.ICManageConfiguration.ICManageConfiguration.isConfiguration('not exist', self.ip, self.bom))
        #self.assertFalse(self.icmc.isConfiguration('not exist', self.ip, self.bom))

    def test_012__getIpNames_none(self):
        result = set(['rtmliotest1'])
        print("ret: {}".format(self.icmc.getIpNames(None)))
        self.assertEqual(result, self.icmc.getIpNames(None))
        
    def test_013__getIpNames_rtl_not_exists(self):
        result = set([])
        self.assertEqual(result, self.icmc.getIpNames('rtl'))
        
    def test_014__getIpNames_ipspec(self):
        result = set(['rtmliotest1'])
        print("ret:{}".format(self.icmc.getIpNames('ipspec')))
        self.assertEqual(result, self.icmc.getIpNames('ipspec'))

    def test_015__getLibraryTypes(self):
        print("RET:{}".format(self.icmc.getLibraryTypes('rtmliotest1')))
        self.assertIn('ipspec', self.icmc.getLibraryTypes('rtmliotest1'))
        self.assertIn('reldoc', self.icmc.getLibraryTypes('rtmliotest1'))

    def test_016_____addToComposites(self):
        self.icmc._compositesAlwaysAccessViaProperty = {}
        self.assertTrue(self.icmc._addToComposites(self.project, self.ip, self.bom))

    def test_017_____addToComposites_fail(self):
        self.icmc._compositesAlwaysAccessViaProperty = {}
        self.icmc._addToComposites(self.project, self.ip, self.bom)
        self.assertFalse(self.icmc._addToComposites(self.project, self.ip, self.bom))

    def test_018____setHierarchyAndComposites___no_release(self):
        self.assertIsNone(self.icmc._setHierarchyAndComposites())

    def test_018____setHierarchyAndComposites___got_release(self):
        project = 'da_i16'
        ip = 'dai16liotest1'
        bom = 'rel_ipspec'
        icmc = dmx.dmlib.ICManageConfiguration.ICManageConfiguration(project, ip, bom)
        self.assertIsNone(icmc._setHierarchyAndComposites())

    def test_019____composites(self):
        result = {'rtmliotest1': ['Raton_Mesa', 'rtmliotest1', 'dev']}
        self.assertEqual(result, self.icmc.composites)

    def test_020____hierarchy(self):
        result = {'rtmliotest1': []}
        self.assertEqual(result, self.icmc.hierarchy)

    def test_021____isRelease(self):
        self.assertTrue(self.icmc.isRelease('RELzz'))
        self.assertFalse(self.icmc.isRelease('zzREL'))
        self.assertFalse(self.icmc.isRelease('snapzz'))

    def test_022____isSnapRelease(self):
        self.assertTrue(self.icmc.isSnapRelease('snap-zz'))
        self.assertFalse(self.icmc.isSnapRelease('zz-snap'))
        self.assertFalse(self.icmc.isSnapRelease('REL'))

    def test_023____creationTime(self):
        result = '2020-09-23T09:39:45.641Z'
        result = u'2021-08-03T04:56:12.677Z'
        result = u'2022-03-23T03:02:45.609Z'
        self.assertEqual(result, self.icmc.creationTime)

    def test_024____modificationTime(self):
        self.assertIsNotNone(self.icmc.modificationTime)

    def test_025____setTimes(self):
        self.assertIsNone(self.icmc._setTimes())

    def test_026____getConfigurationTriplet(self):
        result = ['Raton_Mesa', 'rtmliotest1', 'dev']
        self.assertEqual(result, self.icmc.getConfigurationTriplet(self.ip))

    def test_027____getIPsInHierarchy(self):
        result = set(['rtmliotest1']) 
        self.assertEqual(result, self.icmc.getIPsInHierarchy(self.ip))

    def test_028_____addToHierarchy(self):
        self.icmc._hierarchyAlwaysAccessViaProperty = {}
        self.assertIsNone(self.icmc._addToHierarchy('liotest1', 'liotest3'))

    def test_029______hasLibTypeFast_pass(self):
        self.assertTrue(self.icmc._hasLibTypeFast('liotest3'))
        self.assertTrue(self.icmc._hasLibTypeFast('liotest1'))

    def test_030______hasLibTypeFast_fail(self):
        self.assertTrue(self.icmc._hasLibTypeFast('liotest2'))

    def test_031______ipNames(self):
        result = set(['rtmliotest1'])
        self.assertEqual(result, self.icmc.ipNames)



if __name__ == '__main__':
    unittest.main()
