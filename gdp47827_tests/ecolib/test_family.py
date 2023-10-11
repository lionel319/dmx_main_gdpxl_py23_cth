#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the ecosphere family class
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_family.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import sys
import os

os.environ['DMX_SETTING_FILES_DIR'] = '/p/psg/flows/common/dmx/dmx_setting_files'

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.ecolib.family import *
from dmx.ecolib.roadmap import *
from dmx.ecolib.ecosphere import EcoSphereError
from dmx.utillib.utils import is_pice_env
from dmx.abnrlib.icm import ICManageCLI
from dmx.ecolib.__init__ import LEGACY

class TestFamily(unittest.TestCase):
    '''
    Tests the Family class
    '''
    def setUp(self):
        self.db_project = os.environ['DB_PROJECT']
        self.db_device = os.environ['DB_DEVICE']
        os.environ['DB_PROJECT'] = 'Raton_Mesa'
        os.environ['DB_DEVICE'] = 'RTM'

        self.family = 'Ratonmesa'
        self.Family = Family(self.family, preview=False)
        self.icmproject = 'Raton_Mesa'
        self.icmgroup = 'psgrtm'
        self.ip = 'rtmliotest1'
        self.iptype = 'ss_arch'
        self.iptype = 'asic'
        self.nisgroup = 'psgrtm'
        self.product = 'RTM'
        self.scratchpath = ''
        self.disk = 'ice_scratch_t1'
        self.cli = ICManageCLI()
        self.legacy_server = False

    def tearDown(self):
        os.environ['DB_PROJECT'] = self.db_project
        os.environ['DB_DEVICE'] = self.db_device
        if not LEGACY:
            if self.Family.has_ip('newip'):
                self.Family.delete_ip('newip')

    def test_family_properties(self):
        '''
        Tests the Family object properties
        '''
        self.assertEqual(self.Family.family, self.family)           
        self.assertEqual(self.Family.icmgroup, self.icmgroup)
        self.assertEqual(self.Family.nisgroup, self.nisgroup)
        self.assertEqual(self.Family.scratchpath, self.scratchpath)

    def test__preload(self):
        self.Family._preload()
        products = [x.product for x in self.Family._products]
        self.assertIn(self.product, products)
        icmprojects = [x.project for x in self.Family._icmprojects]
        self.assertIn(self.icmproject, icmprojects)
        iptypes = [x.iptype for x in self.Family._iptypes]
        self.assertIn(self.iptype, iptypes)
        self.assertIn(self.ip, self.Family._ips)    

    def test__get_family_properties(self):
        dict = self.Family._get_family_properties()
        self.assertEqual(self.nisgroup, dict['NIS'])        
        self.assertIn(self.icmproject, dict['icmprojects'])     

    def test__get_products(self):
        products = [x.product for x in self.Family._get_products()]        
        self.assertIn(self.product, products)

    def test_get_products(self):
        products = [x.product for x in self.Family.get_products()]        
        self.assertIn(self.product, products)

    def test_get_products_with_product_filter(self):
        products = [x.product for x in self.Family.get_products(self.product)]
        self.assertIn(self.product, products)

    def test_has_product(self):
        self.assertTrue(self.Family.has_product(self.product))        

    def test_has_no_product(self):
        self.assertFalse(self.Family.has_product('doesnotexist'))    
            
    def test_get_product(self):
        self.assertEqual(self.product, self.Family.get_product(self.product).product)            

    def test_get_non_existing_product(self):
        with self.assertRaises(FamilyError):
            self.Family.get_product('doesnotexist')

    def test_get_product_invalid_character(self):
        with self.assertRaises(FamilyError):
            self.Family.get_product('@#$')
    
    def test__get_icmprojects(self):
        icmprojects = [x.project for x in self.Family._get_icmprojects()]        
        self.assertIn(self.icmproject, icmprojects)

    def test_get_icmprojects(self):
        icmprojects = [x.project for x in self.Family.get_icmprojects()]        
        self.assertIn(self.icmproject, icmprojects)

    def test_get_icmprojects_with_icmproject_filter(self):
        icmprojects = [x.project for x in self.Family.get_icmprojects(self.icmproject)]
        self.assertIn(self.icmproject, icmprojects)

    def test_has_icmproject(self):
        self.assertTrue(self.Family.has_icmproject(self.icmproject))        

    def test_has_no_icmproject(self):
        self.assertFalse(self.Family.has_icmproject('doesnotexist'))    
            
    def test_get_icmproject(self):
        self.assertEqual(self.icmproject, self.Family.get_icmproject(self.icmproject).project)            

    def test_get_non_existing_icmproject(self):
        with self.assertRaises(FamilyError):
            self.Family.get_icmproject('doesnotexist')

    def test_get_icmproject_invalid_character(self):
        with self.assertRaises(FamilyError):
            self.Family.get_icmproject('@#$')
                
    def test__get_iptypes(self):
        iptypes = [x.iptype for x in self.Family._get_iptypes()]        
        self.assertIn(self.iptype, iptypes)

    def test_get_iptypes(self):
        iptypes = [x.iptype for x in self.Family.get_iptypes()]        
        self.assertIn(self.iptype, iptypes)

    def test_get_iptypes_with_iptype_filter(self):
        iptypes = [x.iptype for x in self.Family.get_iptypes('asic')]
        self.assertIn(self.iptype, iptypes)

    def test_has_iptype(self):
        self.assertTrue(self.Family.has_iptype('asic'))        

    def test_has_no_iptype(self):
        self.assertFalse(self.Family.has_iptype('doesnotexist'))    
            
    def test_get_iptype(self):
        self.assertEqual('asic', self.Family.get_iptype('asic').iptype)            

    def test_get_non_existing_iptype(self):
        with self.assertRaises(FamilyError):
            self.Family.get_iptype('doesnotexist')

    def test_get_iptype_invalid_character(self):
        with self.assertRaises(FamilyError):
            self.Family.get_iptype('@#$')                

    def test_get_ips(self):
        ips = [x.ip for x in self.Family.get_ips()]        
        self.assertIn(self.ip, ips)

    def test_get_ips_with_ip_filter(self):
        ips = [x.ip for x in self.Family.get_ips(self.ip)]
        self.assertIn(self.ip, ips)

    def test_get_ips_with_product_filter(self):
        ips = [x.ip for x in self.Family.get_ips(product_filter=self.product)]
        self.assertIn(self.ip, ips)
       
    def test_get_ips_names(self):
        ips = self.Family.get_ips_names()      
        self.assertIn(self.ip, ips)

    def test_get_ips_names_with_ip_filter(self):
        ips = self.Family.get_ips_names(self.ip)
        self.assertIn(self.ip, ips)

    def test_get_ips_names_with_product_filter(self):
        ips = self.Family.get_ips_names(product_filter=self.product)
        self.assertIn(self.ip, ips)        

    def test_has_ip(self):
        self.assertTrue(self.Family.has_ip(self.ip))        

    def test_has_no_ip(self):
        self.assertFalse(self.Family.has_ip('doesnotexist'))    
            
    def test_get_ip(self):
        self.assertEqual(self.ip, self.Family.get_ip(self.ip).ip)            

    def test_get_non_existing_ip(self):
        with self.assertRaises(FamilyError):
            self.Family.get_ip('doesnotexist')

    def test_get_ip_invalid_character(self):
        with self.assertRaises(FamilyError):
            self.Family.get_ip('@#$')            

    def test_add_ip(self):
        if not LEGACY:
            self.assertTrue(self.Family.add_ip('ecolib_testing', 'newip', 'asic'))
            ip = self.Family.get_ip('newip')
            self.assertEqual('ecolib_testing', ip.icmproject)
            self.assertEqual('newip', ip.ip)
            self.assertEqual('asic', ip.iptype)
            # clean up
            self.assertTrue(self.Family.delete_ip('newip'))        

    def test_add_existing_ip(self):
        if not LEGACY:
            with self.assertRaises(FamilyError):
                self.Family.add_ip('ecolib_testing', 'asic_variant', 'asic')           

    def test_delete_ip(self):
        if not LEGACY:
            self.assertTrue(self.Family.add_ip('ecolib_testing', 'newip', 'asic'))
            self.assertTrue(self.Family.has_ip('newip'))         
            self.assertTrue(self.Family.delete_ip('newip'))        
            self.assertFalse(self.Family.has_ip('newip'))         

    def test_delete_non_existing_ip(self):
        if not LEGACY:
            with self.assertRaises(FamilyError):
                self.Family.delete_ip('doesnotexist')

    def test_get_approved_disks(self):
        if not LEGACY:
            if not is_pice_env():
                self.assertIn(self.disk, self.Family.get_approved_disks())
            else:
                # PICE doesn't have disk info yet            
                pass          
        
    def test_verify_roadmap_bad_milestone(self):
        '''
        Tests the verify_roadmap thread with a bad milestone
        '''
        if is_pice_env() and not self.legacy_server:
            family = 'Falcon'        
            thread = 'FM6revA0'
        else:
            family = 'Nadder'        
            thread = 'ND5revA'
        familyobj = Family(family, preview=False)

        self.assertFalse(familyobj.verify_roadmap('this.should.not.exist', thread))

    def test_verify_roadmap_bad_thread(self):
        '''
        Tests the verify_roadmap thread with a bad thread
        '''
        if is_pice_env() and not self.legacy_server:
            family = 'Falcon'        
            thread = 'FM6revA0'
        else:
            family = 'Nadder'        
            thread = 'ND5revA'
        familyobj = Family(family, preview=False)

        self.assertFalse(familyobj.verify_roadmap('1.0', 'this.should.not.exist'))

    def test_verify_roadmap_works(self):
        '''
        Tests the verify_roadmap thread when it works
        '''
        if is_pice_env() and not self.legacy_server:
            family = 'Falcon'        
            thread = 'FM6revA0'
        else:
            family = 'Nadder'        
            thread = 'ND5revA'
        familyobj = Family(family, preview=False)

        self.assertTrue(familyobj.verify_roadmap('4.0', thread))



if __name__ == '__main__':
    unittest.main()
