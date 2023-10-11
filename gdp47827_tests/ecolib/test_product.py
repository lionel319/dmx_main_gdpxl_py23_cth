#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_product.py $
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
from dmx.ecolib.product import Product, ProductError

class TestProduct(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.product = 'FM8'
        self.Product = Product(self.family, self.product)

    def test_product_properties(self):
        '''
        Tests the Product object properties
        '''
        self.assertEqual(self.Product.family, self.family)           
        self.assertEqual(self.Product.product, self.product)

    def test__preload(self):
        self.Product._preload()
        revisions = [x.revision for x in self.Product._revisions]
        self.assertIn('revA0', revisions)

    def test__get_revisions(self):
        revisions = [x.revision for x in self.Product._get_revisions()]
        self.assertIn('revA0', revisions)

    def test_get_revisions(self):
        revisions = [x.revision for x in self.Product.get_revisions()]
        self.assertIn('revA0', revisions)
        
    def test_get_revisions_with_revision_filter(self):
        revisions = [x.revision for x in self.Product.get_revisions('revA0')]
        self.assertIn('revA0', revisions)

    def test_has_revision(self):
        self.assertTrue(self.Product.has_revision('revA0'))

    def test_has_no_revision(self):
        self.assertFalse(self.Product.has_revision('doesnotexist'))
   
    def test_get_revision(self):
        self.assertEqual('revA0', self.Product.get_revision('revA0').revision)
 
    def test_get_revision_invalid_character(self):
        with self.assertRaises(ProductError):
            self.Product.get_revision('$')

if __name__ == '__main__':
    unittest.main()
