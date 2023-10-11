#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/ecosphere/test_family.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os, sys
DMX_LIB = os.getenv('DMX_LIB')
if DMX_LIB and 'main' in DMX_LIB:
    LIB = DMX_LIB
else:
    LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.ecolib.family import Family, FamilyError

class TestFamily(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        os.environ['DMX_FAMILY_LOADER'] = 'family_systest.json'

    def test_object_instantiation(self):
        family = Family(self.family)
        self.assertIsInstance(family, Family)            

    def test_function_existence(self):
        family = Family(self.family)
        self.assertIsNotNone(family._preload)         
        self.assertIsNotNone(family._get_family_properties)                
        self.assertIsNotNone(family._get_products)     
        self.assertIsNotNone(family.get_products)      
        self.assertIsNotNone(family.has_product)
        self.assertIsNotNone(family.get_product)  
        self.assertIsNotNone(family._get_icmprojects)
        self.assertIsNotNone(family.get_icmprojects)
        self.assertIsNotNone(family.has_icmproject)
        self.assertIsNotNone(family.get_icmproject)
        self.assertIsNotNone(family._get_iptypes)
        self.assertIsNotNone(family.get_iptypes)
        self.assertIsNotNone(family.has_iptype)
        self.assertIsNotNone(family.get_iptype)
        self.assertIsNotNone(family.get_ips_names)
        self.assertIsNotNone(family.get_ips)
        self.assertIsNotNone(family.has_ip)
        self.assertIsNotNone(family.get_ip)
        self.assertIsNotNone(family.add_ip)
        self.assertIsNotNone(family.delete_ip)
        self.assertIsNotNone(family.get_approved_disks)

if __name__ == '__main__':
    unittest.main()
