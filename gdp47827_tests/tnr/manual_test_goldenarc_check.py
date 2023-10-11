#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import logging
import unittest
from pprint import pprint
import datetime

#os.environ['DMXDATA_ROOT'] = '/p/psg/flows/common/dmxdata/14.4'
rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

import dmx.abnrlib.goldenarc_db
import dmx.tnrlib.goldenarc_check
import dmx.utillib.contextmgr

class TestGoldenarcCheck(unittest.TestCase):
   
    def __restore_regression_database(self):
        '''
        If in any case the regression database(collection, to be precise) is corrupted,
        run this function to restore the database.
        '''
        import dmx.abnrlib.goldenarc_db
        a = dmx.abnrlib.goldenarc_db.GoldenarcDb(prod=False)
        collection = 'RegtestGoldenArc'
        a.db.drop_collection(collection)
        
        documents = [
            { "thread" : "FM8revA0", "milestone" : "4.0", "flow" : "lint", "subflow" : "mustfix", "tool" : "python", "version" : "/2.7.1" },
            { "thread" : "FM8revA0", "milestone" : "4.0", "flow" : "lint", "subflow" : "mustfix", "tool" : "atrenta_sgmaster", "version" : "/2020WW04" },
            { "thread" : "FM8revA0", "milestone" : "3.0", "flow" : "rdf", "subflow" : "", "tool" : "my_cshrc", "version" : "/1.0" },
            { "thread" : "FM8revA0", "milestone" : "3.0", "flow" : "reldoc", "subflow" : "", "tool" : "dmx", "version" : "/main" },
            { "thread" : "FM8revA0", "milestone" : "3.0", "flow" : "sta", "subflow" : "", "tool" : "my_cshrc", "version" : "/1.0" },
            { "thread" : "FP8revA0", "milestone" : "1.0", "flow" : "lint", "subflow" : "mustfix", "tool" : "python", "version" : "/2.7.1" },
            { "thread" : "FP8revA0", "milestone" : "1.0", "flow" : "lint", "subflow" : "mustfix", "tool" : "atrenta_sgmaster", "version" : "/2020WW04" },
            { "thread" : "FP8revA0", "milestone" : "1.0", "flow" : "reldoc", "subflow" : "", "tool" : "dmx", "version" : "/7.0" },
            { "thread" : "FP8revA0", "milestone" : "1.0", "flow" : "ipxact", "subflow" : "", "tool" : "dmx", "version" : "/9.0" },
            { "thread" : "FP8revA0", "milestone" : "1.0", "flow" : "ipxact", "subflow" : "", "tool" : "dmxdata", "version" : "/11.0" },
        ]
        a.set_collection(collection)
        a.col.insert_many(documents)


    @classmethod
    def setUpClass(cls):
        ### The whole reason why we do this setUpClass is becuase we wanna get the cls.cfobj only once, thus saving runtime.
        cls.project = 'Raton_Mesa'
        cls.variant = 'rtmliotest1'
        cls.libtype = 'reldoc'
        cls.config = 'dev'
        cls.milestone = '0.5'
        cls.thread = 'RTMrevA0'
        cls.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS/test_goldenarc_check_gdpxl' # hpsi10/soc_mpu_cortexa53@snap-test_goldenarc_check 
        cls.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        cls.site = os.getenv("ARC_SITE")

        setenv = dmx.utillib.contextmgr.setenv
        env = {"DB_FAMILY": "Ratonmesa", "DMXDATA_ROOT": "/p/psg/flows/common/dmxdata/14.4"}

        with setenv(env):
            cls.a = dmx.tnrlib.goldenarc_check.GoldenArcCheck(cls.project, cls.variant, cls.libtype, cls.config, cls.wsroot, cls.milestone, cls.thread, prod=False)
            #cls.a.db.set_collection('RegtestGoldenArc')     ### Hack to use regtest collection instead of official one.
        
        cls.cfobj = cls.a.get_config_factory_obj()

    def setUp(self):
        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest1'
        self.libtype = 'reldoc'
        self.config = 'dev'
        self.milestone = '0.5'
        self.thread = 'RTMrevA0'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS/test_goldenarc_check_gdpxl' # hpsi10/soc_mpu_cortexa53@snap-test_goldenarc_check 
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        self.site = os.getenv("ARC_SITE")
        
        self.setenv = dmx.utillib.contextmgr.setenv
        self.env = {"DB_FAMILY": "Ratonmesa", "DMXDATA_ROOT": "/p/psg/flows/common/dmxdata/14.4"}
        
        with self.setenv(self.env):
            self.a = dmx.tnrlib.goldenarc_check.GoldenArcCheck(self.project, self.variant, self.libtype, self.config, self.wsroot, self.milestone, self.thread, prod=False)
            #self.a.db.set_collection('RegtestGoldenArc')     ### Hack to use regtest collection instead of official one.
        
        self.a._cfobj = self.cfobj


    def tearDown(self):
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, dmx.abnrlib.goldenarc_db.__file__)


    def test_010___get_resources_tobe_checked_for_flow___reldoc(self):
        ret = self.a.get_resources_tobe_checked_for_flow('reldoc', '')
        ans = [['dmxdata', '/14.4']]
        print(ret)
        self.assertEqual(ans, ret)

    def test_010___get_resources_tobe_checked_for_flow___dmzcomplib(self):
        ret = self.a.get_resources_tobe_checked_for_flow('dmzcomplib', '')
        ans = [[u'atrenta_sgmaster', u'/2018WW50']] 
        print(ret)
        self.assertEqual(ans, ret)

    def test_010___get_resources_tobe_checked_for_flow___non(self):
        ret = self.a.get_resources_tobe_checked_for_flow('xxxyyyzzz', '')
        ans = []
        self.assertEqual(ans, ret)

    def _test_020___get_resource_datetime_obj___dmxdata_13_11(self):
        ret = self.a.get_resource_datetime_obj('dmxdata/13.11')
        print(ret)
        site = os.getenv("ARC_SITE")
        if site == 'png':
            gol = datetime.datetime(2021, 4, 11, 21, 44, 28)
        else:
            gol = datetime.datetime(2021, 4, 11, 21, 45, 13)
        self.assertEqual(gol, ret)

    def test_100___get_required_audit_logs_hierarchically___reldoc(self):
        self.a.libtype = 'reldoc'
        ret = self.a.get_required_audit_logs_hierarchically()
        print(ret)
        ans = {('Raton_Mesa', 'rtmliotest1'): ['rtmliotest1/reldoc/audit/audit.rtmliotest1.reldoc.xml']}
        self.assertEqual(ret, ans)

    def test_100___get_required_audit_logs_hierarchically___dmzcomplib(self):
        self.a.libtype = 'complib'
        ret = self.a.get_required_audit_logs_hierarchically()
        print(ret)
        key = ('Raton_Mesa', 'rtmliotest1')
        ans = {('Raton_Mesa', 'rtmliotest1'): ['rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml']}
        self.assertEqual(sorted(ret[key]), sorted(ans[key]))

    def test_100___get_required_audit_logs_hierarchically___variant(self):
        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest1'
        self.libtype = None
        self.config = 'dev'
        self.milestone = '0.5'
        self.thread = 'RTMrevA0'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        self.site = os.getenv("ARC_SITE")
        with self.setenv(self.env):
            a = dmx.tnrlib.goldenarc_check.GoldenArcCheck(self.project, self.variant, self.libtype, self.config, self.wsroot, self.milestone, self.thread, prod=False)

        ret = a.get_required_audit_logs_hierarchically()
        ans = {(u'Raton_Mesa', u'rtmliotest1'): [u'rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml']}
        self.assertEqual(ret, ans)

    def test_110___get_audit_logs_metadata(self):
        auditlogs = {('hpsi10', 'soc_mpu_cortexa53'): ['soc_mpu_cortexa53/ipxact/audit/audit.soc_mpu_cortexa53.ipxact.xml', 'soc_mpu_cortexa53/ipxact/audit/audit.soc_mpu_cortexa53.ipxact_rtl.xml']}
        auditlogs = {(u'Raton_Mesa', u'rtmliotest1'): [u'rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml']}
        ret = self.a.get_audit_logs_metadata(auditlogs)
        ans = 'asd'
        ans = {(u'Raton_Mesa', u'rtmliotest1'): {u'rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml': {'flow': 'dmzcomplib', 'errors': [], 'arcres': 'project/rtm/rtmeval/0.0/acds_epl/2021WW39,ic_manage_gdp/xl/47827,icmadmin/gdpxl/1.0,dmx/main_gdpxl,dmxdata/latestdev,altera_reldoc/1.7,atrenta_sgmaster/2.1_fm4_1.7a_rdc', 'subflow': ''}}}
        print(ret)
        self.assertEqual(ret, ans)

    def _test_200___run_test(self):
        self.a.run_test()
        ret = self.a.result
        ans = {('Raton_Mesa', 'rtmliotest1'): {'rtmliotest1/reldoc/audit/audit.rtmliotest1.reldoc.xml': {'flow': 'reldoc', 'errors': ['Golden(dmxdata/14.4) / Used(dmxdata/latestdev).'], 'arcres': 'project/rtm/rtmeval/0.0/acds_epl/2021WW39,ic_manage_gdp/xl/47827,icmadmin/gdpxl/1.0,dmx/main_gdpxl,dmxdata/latestdev,altera_reldoc/1.7', 'subflow': '', 'checks': {u'dmxdata': {'fail': 1, 'used': '/latestdev', 'gold': u'/14.4'}}}}}
        print(ret)
        self.assertEqual(ret, ans)

    def _remove_id(self, list_of_dicts):
        ret = []
        for d in list_of_dicts:
            d.pop('_id')
            ret.append(d)
        return ret


if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
