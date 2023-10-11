#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011-2015 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/Manifest_test.py#1 $

"""
Test the Manifest class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

import unittest
import doctest
from xml.etree.ElementTree import ParseError

from dmx.dmlib.dmError import dmError
import Manifest

def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the Manifest.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(Manifest))
    return tests


class TestManifest(unittest.TestCase): # pylint: disable=R0904
    """Test the Manifest class."""

    def test_0_empty(self):
        '''Check getting the default templateset in data/templateset.xml.'''
        manifest = Manifest.Manifest('ip1')
        elem = manifest.rootElement
        self.assertEqual(elem.tag, 'templateset')
        
    def test_1_ParseError(self):
        '''Check parse errors.'''
        with self.assertRaises(ParseError):
            Manifest.Manifest('ip1', templatesetString='')
        with self.assertRaises(ParseError):
            Manifest.Manifest('ip1', templatesetString='<badly><formed></badly></formed>')
        
    def test_2_entityValues(self):
        '''Check entity reference substitution.'''
        
        # No entity references used, no entity values specified
        manifest = Manifest.Manifest('ip1', 
                        templatesetString='<templateset>literal text</templateset>')
        self.assertEqual(manifest.rootElement.text, 'literal text')
        
        # Entity references used, entity values specified
        manifest = Manifest.Manifest(
                         'ip1',
                         templatesetString=
                            '<templateset>&entityRef1; &entityRef2;</templateset>',
                         entityValues={'entityRef1' : 'entityValue1',
                                       'entityRef2' : 'entityValue2'})
        self.assertEqual(manifest.rootElement.text, 'entityValue1 entityValue2')
        
        # Entity references used, but no entity values specified: error
        with self.assertRaises(ParseError):
            Manifest.Manifest('ip1', 
                              templatesetString
                                ='<templateset>&undefinedEntity;</templateset>')
        
    def test_3_writeManifestset(self):
        '''Check writing a manifestset.'''
        
        manifest = Manifest.Manifest('ip1', 'cell1',
            templatesetString='<templateset>IP &ip_name; cell &cell_name;</templateset>')
        manifest.writeManifestset('testmanifestset.xml')
        with open('testmanifestset.xml') as f:
            manifestsetList = f.readlines()
        self.assertEqual(manifestsetList, [
            '<?xml version="1.0" encoding="utf-8"?>\n',
            '<templateset>\n',
            '  IP ip1 cell cell1\n',
            '</templateset>\n'])
                
    def test_4_rootElement(self):
        '''Check the rootElement property.'''
        manifest = Manifest.Manifest('ip1', templatesetString='<templateset />')
        elem = manifest.rootElement
        self.assertEqual(elem.tag, 'templateset')
        
        with self.assertRaises(ParseError):
            Manifest.Manifest('ip1', 
                    templatesetString='<templateset>&undefinedEntity;</templateset>')

    def test_5_getDeliverableItem_single(self):
        '''Check the getDeliverableFile() method with a single file.'''
        manifest = Manifest.Manifest('ip1', 
            templatesetString='''<?xml version="1.0" encoding="utf-8"?>
            <templateset>
                <template id="TEST">
                    <pattern id="pattern1">
                        &ip_name;/&layoutDirName;/&ip_name;.a.txt
                    </pattern>
                    <pattern id="pattern2">
                        &ip_name;/&layoutDirName;/&ip_name;.b.txt
                    </pattern>
                    <filelist id="filelist1">
                        &ip_name;/&layoutDirName;/&ip_name;.c.filelist
                    </filelist>
                    <filelist id="filelist2">
                        &ip_name;/&layoutDirName;/&ip_name;.d.filelist
                    </filelist>
                </template>
                <template id="TEST"> <!-- Duplicates illegal, but this is a test -->
                    <pattern id="pattern1">
                        wrong.a.txt
                    </pattern>
                    <pattern id="pattern2">
                        wrong.b.txt
                    </pattern>
                    <filelist id="filelist1">
                        wrong.c.txt
                    </filelist>
                    <filelist id="filelist2">
                        wrong.d.txt
                    </filelist>
                </template>
            </templateset>''',
            entityValues={'ip_name' : 'ip1', 'layoutDirName' : 'icc'})
        self.assertEqual(manifest.getDeliverablePattern("TEST", 'pattern1'),
                         set(['ip1/icc/ip1.a.txt']))
        self.assertEqual(manifest.getDeliverablePattern("TEST", 'pattern2'),
                         set(['ip1/icc/ip1.b.txt']))
        self.assertEqual(manifest.getDeliverableFilelist("TEST", 'filelist1'),
                         set(['ip1/icc/ip1.c.filelist']))
        self.assertEqual(manifest.getDeliverableFilelist("TEST", 'filelist2'),
                        set( ['ip1/icc/ip1.d.filelist']))
        
    def test_6_getDeliverableItem_multi(self):
        '''Check the getDeliverableFile() method for multiple items with the same id.'''
        manifest = Manifest.Manifest('ip1', 
            templatesetString='''<?xml version="1.0" encoding="utf-8"?>
            <templateset>
                <template id="TEST">
                    <pattern id="pattern1">
                        &ip_name;/&layoutDirName;/&ip_name;.a.txt
                    </pattern>
                    <pattern id="pattern1">
                        &ip_name;/&layoutDirName;/&ip_name;.b.txt
                    </pattern>
                    <filelist id="filelist1">
                        &ip_name;/&layoutDirName;/&ip_name;.c.filelist
                    </filelist>
                    <filelist id="filelist1">
                        &ip_name;/&layoutDirName;/&ip_name;.d.filelist
                    </filelist>
                    <pattern id="oneOfEach">
                        &ip_name;/&layoutDirName;/&ip_name;.e.txt
                    </pattern>
                    <filelist id="oneOfEach">
                        &ip_name;/&layoutDirName;/&ip_name;.f.filelist
                    </filelist>
                </template>
            </templateset>''',
            entityValues={'ip_name' : 'ip1', 'layoutDirName' : 'icc'})
        self.assertEqual(manifest.getDeliverablePattern('TEST', 'pattern1'),
                         set(['ip1/icc/ip1.a.txt', 'ip1/icc/ip1.b.txt']))
        self.assertEqual(manifest.getDeliverableFilelist('TEST', 'filelist1'),
                         set(['ip1/icc/ip1.c.filelist', 'ip1/icc/ip1.d.filelist']))
        self.assertEqual(manifest.getDeliverablePattern('TEST', 'oneOfEach'),
                         set(['ip1/icc/ip1.e.txt']))
        self.assertEqual(manifest.getDeliverableFilelist('TEST', 'oneOfEach'),
                         set(['ip1/icc/ip1.f.filelist']))

    def test_7_getDeliverableItem_undefined(self):
        '''Check the getDeliverableFile() method.'''
        manifest = Manifest.Manifest('ip1', 
                                     templatesetString
            ='''<?xml version="1.0" encoding="utf-8"?>
            <templateset>
                <template id="TEST">
                    <pattern id="pattern1">
                        &ip_name;/&layoutDirName;/&ip_name;.txt
                    </pattern>
                    <filelist id="filelist1">
                        &ip_name;/&layoutDirName;/&ip_name;.filelist
                    </filelist>
                </template>
            </templateset>''',
            entityValues={'ip_name' : 'ip1', 'layoutDirName' : 'icc'})
        self.assertEqual(manifest.getDeliverablePattern("TEST", 'pattern1'),
                         set(['ip1/icc/ip1.txt']))
        with self.assertRaises(dmError):
            manifest.getDeliverablePattern('TEST', 'undefined')
        with self.assertRaises(dmError):
            manifest.getDeliverablePattern('UNDEFINED', 'pattern1')
            
    def test_8_toposort(self):
        '''
        Test sortDeliverablesTopologically()
        '''
        fakeManifest = Manifest.Manifest (ip_name='fakeIp')
        allDeliverables = fakeManifest.allDeliverables # Should work
        fakeManifest.sortDeliverablesTopologically (allDeliverables) # shouldn't throw
        
        actual_sec = fakeManifest.sortDeliverablesTopologically (['RTL', 'BDS', 'SCH'])
        self.assertItemsEqual(['SCH','RTL','BDS'], actual_sec)
        
        Manifest.Manifest.getAllDefaultDeliverables() # shouldn't throw
        Manifest.Manifest.getAllDefaultPredecessorSuccessorPairs() # shouldn't throw
        
    def test_9_getFileSpec(self):
        '''
        Test the API reqested by http://fogbugz/default.asp?290185
        '''
        manifest = Manifest.Manifest (ip_name='<ip>', cell_name='<cell>')
        
        expected = ['<ip>/bcmrbc/*.bcm_substitute.config', 
                    '<ip>/bcmrbc/....di.filelist', 
                    '<ip>/bcmrbc/<cell>.bcm.xml', 
                    '<ip>/bcmrbc/<cell>.rbc.sv', 
                    '<ip>/bcmrbc/addbcm.config']                    
        actual = manifest.reportDeliverableFilePatterns ('BCMRBC', 
                                                         indicateFilelists=True)
        self.assertEqual (expected, actual)
        
if __name__ == "__main__":
    unittest.main (verbosity=2, failfast=True)
