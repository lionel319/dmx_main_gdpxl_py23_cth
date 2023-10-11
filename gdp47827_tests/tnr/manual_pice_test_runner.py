#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import logging
import unittest
from pprint import pprint, pformat

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

os.environ['DMXDATA_ROOT'] = '/p/psg/flows/common/dmxdata/14.4'

from dmx.tnrlib.test_runner import TestRunner
from dmx.tnrlib.test_result import TestFailure

class TestTestRunner(unittest.TestCase):
    
    def setUp(self):
        self.module_path = sys.modules[TestRunner.__module__].__file__
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest1'
        self.libtype = 'complib'
        self.configuration = 'dev'
        self.milestone = '0.5'
        self.thread = 'RTMrevA0'
        self.variant_type = 'ss_arch'

        self.cell = 'rtmliotest1'
       
        '''
        self.db_project = os.environ['DB_PROJECT']
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_PROJECT'] = 'Falcon_Mesa i10socfm'
        os.environ['DB_DEVICE'] = "FM6"
        '''

        ### CD into workspace
        os.chdir(self.wsroot)

        ### TestRunner for Libtype rtl (data_check)
        self.tr = TestRunner(self.project, self.variant, 'reldoc', self.configuration, self.wsroot, self.milestone, self.thread, log_audit_validation_to_splunk=False)

        ### TestRunner for Libtype lint (context_check)
        self.trc = TestRunner(self.project, self.variant, 'complib', self.configuration, self.wsroot, '0.5', self.thread, log_audit_validation_to_splunk=False)

        ### TestRunner for variant
        self.trv = TestRunner(self.project, self.variant, None, self.configuration, self.wsroot, self.milestone, self.thread, log_audit_validation_to_splunk=False)


    def tearDown(self):
        '''
        os.environ['DB_PROJECT'] = self.db_project
        os.environ['DB_DEVICE'] = self.db_device
        '''
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, self.module_path)

    def test_010___get_variant_type(self):
        ret = self.tr.get_variant_type()
        self.assertEqual(ret, self.variant_type)

    def test_020___get_required_libtypes(self):
        ret = self.tr.get_required_libtypes()
        ans = ['complib', 'ipspec', 'reldoc']
        print(sorted(ret))
        print(sorted(ans))
        self.assertEqual(sorted(ret), sorted(ans))

    def test_030___get_required_tests(self):
        ret = self.tr.get_required_tests(self.project, self.milestone, self.thread, self.variant_type)
        ans = [['complib', 'dmzcomplib', '', 'c', 'dmz', 'jrandall', 'NA', 'NA'], ['ipspec', 'ipspec', '', 'd', 'ipspec_check', 'mconkin', 'NA', 'NA'], ['reldoc', 'reldoc', '', 'd', 'reldoc_check', 'yltan', 'NA', 'NA']]
        self.maxDiff = None
        print(pformat(sorted(ret)))
        print(pformat(sorted(ans)))
        print(sorted(ret))
        print(sorted(ans))

        self.assertEqual(sorted(ret), sorted(ans))


    def test_040___get_required_files(self):
        audit_logs, required_files = self.tr.get_required_files()
        pprint([audit_logs, required_files])
        ans = [['/rtmliotest1/reldoc/audit/audit.rtmliotest1.reldoc.xml'],['liotest1/rdf/no_such_file.txt']]
        self.assertEqual(audit_logs, ans[0])
        self.assertEqual(required_files, ans[1])


    def test_050___check_libtype_in_config_for_variant___pass(self):
        ret = self.tr.check_libtype_in_config_for_variant(self.libtype, self.configuration, self.variant)
        self.assertEqual(ret, True) 

    def test_050___check_libtype_in_config_for_variant___pass(self):
        ret = self.tr.check_libtype_in_config_for_variant('oaaa', self.configuration, self.variant)
        self.assertEqual(ret, False) 
    
    
    def test_060___get_libtype_where_all_topcells_unneeded(self):
        unneededs = self.tr.get_unneeded_deliverables()
        ret = self.tr.get_libtype_where_all_topcells_unneeded(unneededs)
        self.assertEqual(sorted(ret), sorted(['complibbcm', 'bcmrbc']))
                

    def test_060___get_unneeded_deliverable_filepaths(self):
        ret = self.tr.get_unneeded_deliverable_filepaths()
        self.assertEqual(ret, [os.path.join(self.wsroot, self.variant, 'ipspec', 'rtmliotest1.unneeded_deliverables.txt')])


    def test_070___get_unneeded_deliverables(self):
        ret = self.tr.get_unneeded_deliverables()
        pprint(ret)
        ans = [('rtmliotest1', 'bcmrbc'), ('rtmliotest1', 'complibbcm')]
        self.assertEqual(sorted(ret), sorted(ans))



    def test_100___run_tests_for_libtype_data_check___pass(self):
        ret = self.tr.run_tests()
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(ret)
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        ans = [TestFailure(variant='rtmliotest1', libtype='reldoc', topcell='rtmliotest1', flow='reldoc', subflow='', error='FAILED validation of /rtmliotest1/reldoc/audit/audit.rtmliotest1.reldoc.xml: checksum for /liotest1/rdf/no_such_file.txt failed: can not access file'), TestFailure(variant='rtmliotest1', libtype='reldoc', topcell='rtmliotest1', flow='reldoc', subflow='', error='FAILED validation of /rtmliotest1/reldoc/audit/audit.rtmliotest1.reldoc.xml: test results indicated failure: some errors found')]
        self.assertEqual(list(ret), ans)

    def test_110___run_tests_for_libtype_context_check___pass(self):
        ret = self.trc.run_tests()

        ans = [TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: test results indicated failure: some errors found')]
        ans = [TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='complib', subflow='type', error='pattern file rtmliotest1/complib/*.dmz does not exist.'), TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for /liotest1/rdf/no_such_file.txt failed: can not access file'), TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for file /rtmliotest1/ipspec/cell_names.txt (6ccdc74c1e9dfbb30a9a3d7f2db448e3) does not match audit requirement (d41d8cd98f00b204e9800998ecf8427e).Revision #1 of the file was used during checking, but an attempt was made to release revision #unknown.'), TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: test results indicated failure: some errors found')]
        
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(ret)
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(ans)
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        self.assertEqual(list(ret), ans)

    def test_120___run_tests_for_variant___pass(self):
        ret = self.trv.run_tests()
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(sorted(ret))
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXX")
        ans = [TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for /liotest1/rdf/no_such_file.txt failed: can not access file'), TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for file /rtmliotest1/ipspec/cell_names.txt (6ccdc74c1e9dfbb30a9a3d7f2db448e3) does not match audit requirement (d41d8cd98f00b204e9800998ecf8427e).Revision #1 of the file was used during checking, but an attempt was made to release revision #unknown.'), TestFailure(variant='rtmliotest1', libtype='complib', topcell='rtmliotest1', flow='dmzcomplib', subflow='', error='FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: test results indicated failure: some errors found')]

        self.assertEqual(sorted(list(ret)), sorted(ans))


    def test_200___get_required_varlibs(self):
        required_files = [
            'liotest1/rdf/no_such_file.txt',
            'liotest1/rdf/file1.txt',
            'liotest1/pv/c.txt',
            'liotest1/stamod/c.txt',
            '/a/b/c/d/e',
            'liotest2/rdf/no_such_file.txt',
            'liotest2/rdf/file1.txt',
            'liotest2/pv/c.txt',
            'liotest2/stamod/c.txt',
            '/aa/b/c/d/e'
        ]
        varlibs = [
            ('liotest1', 'rdf'),
            ('liotest1', 'pv'),
            ('liotest1', 'stamod'),
            ('liotest2', 'rdf'),
            ('liotest2', 'pv'),
            ('liotest2', 'stamod'),
        ]

        ret = self.tr.get_required_varlibs(required_files)
        self.assertEqual(sorted(ret), sorted(varlibs))




if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
