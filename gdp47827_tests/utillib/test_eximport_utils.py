#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_eximport_utils.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import os
import sys
import unittest
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.utillib.utils import run_command
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.eximport_utils
import dmx.utillib.contextmgr
import filecmp


class TestUser(unittest.TestCase):
    
    def setUp(self):
        self.a = dmx.utillib.eximport_utils
        self.setenv = dmx.utillib.contextmgr.setenv
        self.env = {
            "DMXDATA_ROOT": '/p/psg/flows/common/dmxdata/14.5',
            "DB_FAMILY": "Acomarock",
        }

    def tearDown(self):
        pass

    def test_001___get_format_name___import(self):
        with self.setenv(self.env):
            ret = self.a.get_format_name('import')
        print(ret)
        ans = ['cthcdl', 'cthgln_filelist', 'cthipfloorplan', 'cthoasis', 'cthpvlm', 'cthrcxt', 'cthsdf', 'cthsta', 'cthstamod', 'cthyx2gln', 'ipdepv', 'r2gpv']
        self.assertEqual(ret, ans)

    def test_002___get_format_name___export(self):
        with self.setenv(self.env):
            ret = self.a.get_format_name('export')
        print(ret)
        ans = ['demo']
        self.assertEqual(ret, ans)

    def test_003___get_format_name___fail(self):
        with self.assertRaises(Exception):
            ret = self.a.get_format_name('xxxxx')

    def test_010___get_config_file___fail(self):
        with self.assertRaises(Exception):
            ret = self.a.get_config_file('import', 'feonly', 'rtl', 'mapping')

    def test_011___get_config_file___import_cthcdl_cdl_mapping(self):
        with self.setenv(self.env):
            ret = self.a.get_config_file('import', 'cthcdl', 'cdl', 'mapping')
        ans = '/p/psg/flows/common/dmxdata/14.5/Acomarock/import/cthcdl/cdl.mapping.tcsh'
        self.assertEqual(ret, ans)

    def test_012___get_config_file___import_cthcdl_rules_conf(self):
        with self.setenv(self.env):
            ret = self.a.get_config_file('import', 'cthcdl', 'rules', 'conf')
        ans = '/p/psg/flows/common/dmxdata/14.5/Acomarock/import/cthcdl/rules.conf'
        self.assertEqual(ret, ans)

    def test_020___parse_rules_file(self):
        with self.setenv(self.env):
            rulesfile = self.a.get_config_file('import', 'cthcdl', 'rules', 'conf')
            ret = self.a.parse_rules_file(rulesfile)
        ans = {'MAPPING': ['cdl'], 'GENERATORS': ['cdl']}
        self.assertEqual(ret, ans)

    def test_030___expand_file___no_expand(self):
        with self.setenv(self.env):
            infile = self.a.get_config_file('import', 'cthcdl', 'cdl', 'mapping')
            outfile = self.a.expand_file(infile, {})
        self.assertTrue(filecmp.cmp(infile, outfile))

    def test_031___expand_file___got_expand(self):
        with self.setenv(self.env):
            infile = self.a.get_config_file('import', 'cthcdl', 'cdl', 'mapping')
            outfile = self.a.expand_file(infile, {"${DEST}":"aaa", "${SOURCE}":"bbb"})
        print("outfile: {}".format(outfile))
        ansfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'test_031___expand_file___got_expand')
        self.assertTrue(filecmp.cmp(ansfile, outfile))

    def test_040___run_excutable_file(self):
        with self.setenv(self.env):
            ret = self.a.run_excutable_file('import', 'cthsta', ['sta'], {}, 'generator')
        ### Just to confirm No Exception raised 
        self.assertFalse(ret)
        

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    unittest.main()

