#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/ecosphere/test_ip.py $
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
from dmx.ecolib.ip import IP, IPError

class TestIP(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.ip = 'ar_lib'

    def test_object_instantiation(self):
        ip = IP(self.family, self.ip)
        self.assertIsInstance(ip, IP)            

    def test_function_existence(self):
        ip = IP(self.family, self.ip)
        self.assertIsNotNone(ip._preload)         
        self.assertIsNotNone(ip.get_unneeded_deliverables)                
        self.assertIsNotNone(ip.get_ip_history)     
        self.assertIsNotNone(ip.get_cells_history)      
        self.assertIsNotNone(ip.get_cells_names)
        self.assertIsNotNone(ip.get_cells)  
        self.assertIsNotNone(ip.get_cell)
        self.assertIsNotNone(ip.add_cell)
        self.assertIsNotNone(ip.delete_cell)
        self.assertIsNotNone(ip._load_ip_properties)
        self.assertIsNotNone(ip.get_applicable_products)
        self.assertIsNotNone(ip._get_iptypes)
        self.assertIsNotNone(ip.update_owner)
        self.assertIsNotNone(ip.update_iptype)

if __name__ == '__main__':
    unittest.main()
