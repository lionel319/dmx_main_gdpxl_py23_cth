#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_revision.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
os.environ['DMXDB'] = 'DMXTEST'
from dmx.ecolib.revision import Revision, RevisionError

class TestRevision(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.product = 'ND5'
        self.revision = 'revA'
        self.Revision = Revision(self.family, self.product, 'A')

    def test_revision_properties(self):
        '''
        Tests the Revision object properties
        '''
        self.assertEqual(self.Revision.family, self.family)           
        self.assertEqual(self.Revision.product, self.product)    
        self.assertEqual(self.Revision.revision, self.revision)

if __name__ == '__main__':
    unittest.main()
