#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_icmconfig.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

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
import dmx.abnrlib.icmconfig

class TestIcmLibrary(unittest.TestCase):

    def setUp(self):
        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest2'
        self.config = 'dev'

        ### Existing Config (normal method)
        self.econfig = dmx.abnrlib.icmconfig.IcmConfig(self.config, self.project, self.variant)

        ### Existing config (defprop_from_icm method)
        data = {"created-by":"lionelta","createdby":"lionelta","createdon":"Mon Sep 28 02:03:01 PDT 2020","testing":True,"id":"C1238336","type":"config","name":"dev","path":"/intel/Raton_Mesa/rtmliotest2/dev","created":"2020-09-23T09:54:02.923Z","modified":"2020-10-20T14:04:46.878Z"}
        data = {u'name': u'dev', u'created': u'2020-09-23T09:54:02.923Z', u'created-by': u'lionelta', u'createdon': u'Mon Sep 28 02:03:01 PDT 2020', u'testing': True, u'modified': u'2020-10-28T06:33:00.418Z', u'createdby': u'lionelta', u'path': u'/intel/Raton_Mesa/rtmliotest2/dev', u'type': u'config', u'id': u'C1238336'}
        self.dconfig = dmx.abnrlib.icmconfig.IcmConfig(defprop_from_icm=data)


        
    ##############################################################################
    ### TEST 0** are all tests on config which are existing in ICM db 
    ##############################################################################
    def test_000___get_config_properties(self):
        ret = self.econfig._defprops
        pprint(ret)
        self.assertDictContainsSubset({u'name': u'dev', u'testing': True, u'path': u'/intel/Raton_Mesa/rtmliotest2/dev', u'type': u'config'}, ret)

    def test_001___get_user_properties(self):
        ret = self.econfig.get_user_properties()
        pprint(ret)
        self.assertDictContainsSubset({"testing": True }, ret)


    ##############################################################################
    ### TEST 3** are all tests on config which uses defprop_from_icm method 
    ##############################################################################
    def test_300___get_config_properties(self):
        ret = self.dconfig._defprops
        self.assertEqual(ret, {u'name': u'dev', u'created': u'2020-09-23T09:54:02.923Z', u'created-by': u'lionelta', u'createdon': u'Mon Sep 28 02:03:01 PDT 2020', u'testing': True, u'modified': u'2020-10-28T06:33:00.418Z', u'createdby': u'lionelta', u'path': u'/intel/Raton_Mesa/rtmliotest2/dev', u'type': u'config', u'id': u'C1238336'})
                
    def test_301___get_user_properties(self):
        ret = self.dconfig.get_user_properties()
        self.assertEqual(ret, {"testing": True, 'createdby': u'lionelta', u'createdon': u'Mon Sep 28 02:03:01 PDT 2020'})

    def test_302___get_full_name(self):
        ret = self.dconfig.get_full_name()
        self.assertEqual(ret, '{}/{}/{}'.format(self.project, self.variant, self.config))


    def test_400___format_objects_for_pm___new(self):
        # current
        self.dconfig._configurations = [
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt1', 'lb1', 'rel1'),
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt2', 'lb1', 'rel1'),
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt3', 'lb1', 'rel1'),
            dmx.abnrlib.icmconfig.IcmConfig('rel1', 'pro1', 'var1')
        ]
        # saved
        self.dconfig._saved_configurations = []
        ret = self.dconfig._IcmConfig__format_objects_for_pm()
        #self.assertEqual(ret, {'add': ['pro1/var1/lt2/lb1/rel1', 'pro1/var1/rel1', 'pro1/var1/lt1/lb1/rel1', 'pro1/var1/lt3/lb1/rel1'], 'remove': []})
        ans = {'add': ['pro1/var1/lt2/lb1/rel1', 'pro1/var1/rel1', 'pro1/var1/lt1/lb1/rel1', 'pro1/var1/lt3/lb1/rel1'], 'remove': []}
        self.assertEqual(sorted(ret['add']), sorted(ans['add']))
        self.assertEqual(sorted(ret['remove']), sorted(ans['remove']))

    def test_400___format_objects_for_pm___existing(self):
        # current
        self.dconfig._configurations = [
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt1', 'lb1', 'rel1'),
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt2', 'lb1', 'rel1'),
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt3', 'lb1', 'rel1'),
            dmx.abnrlib.icmconfig.IcmConfig('rel1', 'pro1', 'var1')
        ]
        # saved
        self.dconfig._saved_configurations = [
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt1', 'lb1'),
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt2', 'lb1'),
            dmx.abnrlib.icmlibrary.IcmLibrary('pro1', 'var1', 'lt3', 'lb1'),
            dmx.abnrlib.icmconfig.IcmConfig('rel1', 'pro1', 'var1')
        ]
        ret = self.dconfig._IcmConfig__format_objects_for_pm()
        #self.assertEqual(ret, {'add': ['pro1/var1/lt2/lb1/rel1', 'pro1/var1/lt1/lb1/rel1', 'pro1/var1/lt3/lb1/rel1'], 'remove': ['pro1/var1/lt2/lb1', 'pro1/var1/lt3/lb1', 'pro1/var1/lt1/lb1']})
        ans = {'add': ['pro1/var1/lt2/lb1/rel1', 'pro1/var1/lt1/lb1/rel1', 'pro1/var1/lt3/lb1/rel1'], 'remove': ['pro1/var1/lt2/lb1', 'pro1/var1/lt3/lb1', 'pro1/var1/lt1/lb1']}
        self.assertEqual(sorted(ret['add']), sorted(ans['add']))
        self.assertEqual(sorted(ret['remove']), sorted(ans['remove']))

if __name__ == '__main__':
    unittest.main()
