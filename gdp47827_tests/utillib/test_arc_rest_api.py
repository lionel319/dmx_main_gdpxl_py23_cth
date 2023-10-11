#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_arc_rest_api.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import os
import sys
import unittest
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.utillib.utils import run_command
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.arc_rest_api


class TestArcRestApi(unittest.TestCase):
    
    def setUp(self):
        self.a = dmx.utillib.arc_rest_api.ArcRestApi()
        self.a.RETRY = 0
        self.a.WAITTIME = 0

    def tearDown(self):
        pass

    def test_001___get_request_url(self):
        request = 'a/bb/ccc'
        ret = self.a.get_request_url(request)
        self.assertEqual(ret, '{}/{}'.format(self.a.baseurl, request))

    def test_002___get_curl_command(self):
        prefix = 'env -i curl'
        request = 'a/bb/ccc'
        ret = self.a.get_curl_command(request)
        self.assertEqual(ret, '{} {}/{}'.format(prefix, self.a.baseurl, request))

    def test_003___string_to_json___is_json_string(self):
        text = '{"a": "B", "C": "D"}'
        ret = self.a.string_to_json(text)
        print(ret)
        self.assertEqual(type(ret), type({}))

    def test_003___string_to_json___not_json_string(self):
        text = '<a href="bnlablabla">helo world</a>'
        ret = self.a.string_to_json(text)
        self.assertEqual(ret, None)

    def test_004___run_command___not_json_string(self):
        text = '''<a href="bnlablabla">helo world</a>'''
        ret = self.a.run_command(''' echo {} '''.format(text))
        self.assertEqual(ret, None)

    def test_004___run_command___is_json_string(self):
        text = '''{"a": "B", "C": "D"}'''
        ret = self.a.run_command(''' echo '{}' '''.format(text))
        self.assertEqual(type(ret), type({}))



if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

