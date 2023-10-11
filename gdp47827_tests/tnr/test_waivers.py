#!/usr/bin/env python

import sys
import os
import logging
import unittest

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

from dmx.tnrlib.waivers import Waivers
from dmx.tnrlib.waiver_file import WaiverFile

class TestWaivers(unittest.TestCase):
    
    def setUp(self):
        self.module_path = sys.modules[Waivers.__module__].__file__
        self.wsroot = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fake_workspace')
        self.flow = 'reldoc'
        self.subflow = ''
        self.variant = 'variant_a'
        self.libtype = 'reldoc'
        self.cell = 'variant_a_cell_2'
        self.waiverfile = os.path.join(self.wsroot, self.variant, self.libtype, 'tnrwaivers.csv')
        self.wf = WaiverFile()
        self.wf.load_from_file(self.waiverfile)
        self.w = Waivers()
        self.w.add_waiver_file(self.wf)


    def tearDown(self):
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, self.module_path)

    def test_010___find_matching_error___cant_file(self):
        ret = self.w.find_matching_waiver(self.variant, self.flow, self.subflow, 'xxx')
        self.assertEqual(ret, None)

    def test_010___find_matching_error___match_whole_sentance(self):
        ret = self.w.find_matching_waiver(self.variant, self.flow, self.subflow, 'Match Exact Error Sentance.')
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[2], self.waiverfile)

    def test_010___find_matching_error___match_wildcard(self):
        ret = self.w.find_matching_waiver(self.variant, self.flow, self.subflow, 'Match With (some nonsense here) Wildcard.')
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[2], self.waiverfile)

    def test_010___find_matching_error___match_diff_revision(self):
        ''' The revision here is #8888 and #9999. 
        The revision in the tnrwaivers.csv file is not #8888 and #9999.
        But that should not matter. 
        When matching errors, the revision should be wildcarded
        '''
        error = 'FAILED validation of /iosubsysleftnd5/cvsignoff/audit/audit.iosubsysleftnd5.cvsignoff.xml: checksum for file /iosubsysleftnd5/pnr/results/iosubsysleftnd5.pnr.pt.v (888eb90b53096765d250306a9be796f0) does not match audit requirement (992e93e8ec0e04e847fd17925d061b08).Revision #8888 of the file was used during checking, but an attempt was made to release revision #9999.'
        ret = self.w.find_matching_waiver(self.variant, self.flow, self.subflow, error)
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[2], self.waiverfile)


if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
