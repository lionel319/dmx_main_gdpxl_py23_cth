#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/verifier_test.py#1 $

"""
Test the dmx.dmlib.templateset.verifier.Verifier class.
"""

import unittest
import dmx.dmlib.pyfakefs.fake_filesystem_unittest

from dmx.dmlib.templateset.templateset import Templateset
import dmx.dmlib.templateset.verifier

def load_tests(loader, tests, ignore):
    '''Load the Verifier.py doctest tests into unittest.'''
    return dmx.dmlib.pyfakefs.fake_filesystem_unittest.load_doctests(loader, tests, ignore,
                                                           dmx.dmlib.templateset.verifier)

class TestVerifier(dmx.dmlib.pyfakefs.fake_filesystem_unittest.TestCase): # pylint: disable=R0904
    """Test the Verifier class."""
    _expectedAliasNames = (
        'FAKE',)

    _expectedDeliverableNames = (
        'BCMRBC',
        'CDC',
        'CDL',
        'CIRCUITSIM',
        'COMPLIB',
        'COMPLIBPHYS',
        'CVIMPL',
        'CVRTL',
        'CVSIGNOFF',
        'DFTDSM',
        'DV',
        'FCPWRMOD',
        'FV',
        'FVPNR',
        'FVSYN',
        'GP',
        'INTERRBA',
        'INTFC',
        'IPFLOORPLAN',
        'IPPWRMOD',
        'IPSPEC',
        'IPXACT',
        'LAYMISC',
        'LINT',
        'MW',
        'NETLIST',
        'OA',
        'OASIS',
        'OA_SIM',
        'PERIODICTST',
        'PINTABLE',
        'PKGDE',
        'PKGEE',
        'PNR',
        'PORTLIST',
        'PV',
        'R2G2',
        'RCXT',
        'RDF',
        'RELDOC',
        'RTL',
        'RTLCOMPCHK',
        'RV',
        'SCHMISC',
        'SDF',
        'STA',
        'STAMOD',
        'SYN',
        'TIMEMOD',
        'TRACKPHYS',
        'UPF',
        'UPFFC',
        'YX2GLN',
    )

    def setUp(self):
        self.maxDiff = None
        deliverableSet = Templateset('Full', '2.0')
        self._fullXml =  deliverableSet.toxml()
        
    def tearDown(self):
        pass


    def test_empty(self):
        '''Test the initial state'''
        verifier = dmx.dmlib.templateset.verifier.Verifier('')
        self.assertEqual(verifier.errors,
                         ["The deliverable templateset has parsing "
                          "errors: no element found: line 1, column 0"])
        self.assertFalse(verifier.isCorrect)

    def test_allAliasNames(self):
        '''Check the list of all alias names.'''
        self.assertEqual(dmx.dmlib.templateset.verifier.Verifier.allAliasNames, 
                         self._expectedAliasNames)
        
    def test_allDeliverableNames(self):
        ''' Check the list of all deliverable names.'''
        self.assertEqual(dmx.dmlib.templateset.verifier.Verifier.allDeliverableNames, 
                         self._expectedDeliverableNames)
        
    def test_isVerifyRoot(self):
        '''Check the verification of the `<templatset>` root element.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
            <pattern id="file">
              file.txt
            </pattern>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <WRONG_ROOT>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
            <pattern id="file">
              file.txt
            </pattern>
          </template>
        </WRONG_ROOT>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, ["The root XML element name is 'WRONG_ROOT', "
                                           "but it should be 'templateset'."])
        self.assertFalse(verifier.isCorrect)

    def test_verifyTemplates_noTemplates(self):
        '''Check the verification of the minimum requirements for a templateset.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
          <pattern id="file">
              file.txt
            </pattern>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <!-- no templates -->
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, 
                         ["The templateset contains no deliverable templates."])
        self.assertFalse(verifier.isCorrect)

    def test_verifyUnique(self):
        '''Check the verification of uniqueness of <alias> and <template>.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <alias id="UNIQUE1"/>
          <alias id="UNIQUE2"/>
          <template caseid="100" id="UNIQUE3">
            <description> Desc.</description>
          </template>
          <template caseid="101" id="UNIQUE4">
            <description> Desc.</description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <alias id="SAME1"/>
          <alias id="SAME1"/>
          
          <template caseid="100" id="SAME2">
            <description> Desc.</description>
          </template>
          <template caseid="101" id="SAME2">
            <description> Desc.</description>
          </template>
          
          <alias id="SAME3"/>
          <template caseid="102" id="SAME3">
            <description> Desc.</description>
          </template>

        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "The deliverable '<alias> and/or <template>' name 'SAME1' is not unique.",
            "The deliverable '<alias> and/or <template>' name 'SAME2' is not unique.",
            "The deliverable '<alias> and/or <template>' name 'SAME3' is not unique."])

    def test_verifyNamesLegal(self):
        '''Check the verification of <alias> and <template> names.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <alias id="LEGAL1"/>
          <alias id="LEGAL_2"/>
          <template caseid="100" id="LEGAL3">
            <description> Desc.</description>
          </template>
          <template caseid="101" id="LEGAL_4">
            <description> Desc.</description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="ILLEGAL_BECAUSE_EXCEEDS_32_MAX___">
            <description> Desc.</description>
          </template>
          <template caseid="101" id="ILLEGAL.1">
            <description> Desc.</description>
          </template>
          <template caseid="102" id="Illegal_2">
            <description> Desc.</description>
          </template>
          <template caseid="103" id="3ILLEGAL">
            <description> Desc.</description>
          </template>
          <alias id="ILLEGAL.4"/>
          <alias id="Illegal_5"/>
          <alias id="6ILLEGAL"/>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        regex = r'^[A-Z][A-Z0-9_]*$'
        self.assertItemsEqual(verifier.errors, [
            "Alias and/or deliverable name '3ILLEGAL' is illegal because it does not match '{}'.".format(regex),
            "Alias and/or deliverable name '6ILLEGAL' is illegal because it does not match '{}'.".format(regex),
            "Alias and/or deliverable name 'ILLEGAL.1' is illegal because it does not match '{}'.".format(regex),
            "Alias and/or deliverable name 'ILLEGAL.4' is illegal because it does not match '{}'.".format(regex),
            "Alias and/or deliverable name 'ILLEGAL_BECAUSE_EXCEEDS_32_MAX___' is illegal because it contains more than 32 characters.",
            "Alias and/or deliverable name 'Illegal_2' is illegal because it does not match '{}'.".format(regex),
            "Alias and/or deliverable name 'Illegal_5' is illegal because it does not match '{}'.".format(regex)])

    def test_verifyAliases_doVerifyEveryAliasPresent(self):
        '''Check that all aliases are present.
        The error,
            self.assertEqual(actual, expected)
            AssertionError: 'TESTPINS' != 'TIMING'
        means one of two things:
            - TESTPINS is defined when it should not be
            - TIMING is not defined when it should be
        '''
        verifier = dmx.dmlib.templateset.verifier.Verifier(self._fullXml, 
                                                    doVerifyEveryTemplatePresent=True)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        # One too many aliases
        aliasList = list(self._expectedAliasNames)
        aliasList.append('fakeExcessAliasForTesting')
        self.assertEqual(len(self._expectedAliasNames) + 1, len(aliasList))
        
        deliverableSet = Templateset('Extra', '2.0', aliasNames=aliasList)
        verifier = dmx.dmlib.templateset.verifier.Verifier(deliverableSet.toxml(), 
                                                    doVerifyEveryTemplatePresent=True)
        
        self.assertEqual(len(verifier.errors), 2)
        regex = r'^[A-Z][A-Z0-9_]*$'
        self.assertEqual(verifier.errors[0],
                         "Alias and/or deliverable name 'fakeExcessAliasForTesting' is illegal "
                         "because it does not match '{}'.".format(regex))
        self.assertEqual(verifier.errors[1],
                         "Extra, unknown deliverable '<alias>' present: ['fakeExcessAliasForTesting']")
        self.assertFalse(verifier.isCorrect)

        # One too few aliases
        aliasList = list(self._expectedAliasNames)
        aliasList.remove('FAKE')
        deliverableSet = Templateset('Missing', '2.0', aliasNames=aliasList)
        verifier = dmx.dmlib.templateset.verifier.Verifier(deliverableSet.toxml(), 
                                                    doVerifyEveryTemplatePresent=True)
        self.assertItemsEqual(verifier.errors, [
            "All deliverable '<alias>' are not defined.  These are missing: ['FAKE']",])
        self.assertFalse(verifier.isCorrect)

    def test_verifyAlias(self):
        '''Check the <alias> verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <alias id="EMPTYALIAS"/>

          <alias id="GOOD">
            <member>MEM1</member>
            <member>EMPTYALIAS</member>
            <member>MEM2</member>
          </alias>

          <template caseid="100" id="MEM1">
            <description> Desc.</description>
          </template>
          <template caseid="101" id="MEM2">
            <description> Desc.</description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <!-- empty id attr -->
          <alias id="">
            <member>MEM1</member>
          </alias>
          
          <!-- no id attr -->
          <alias>
            <member>MEM2</member>
          </alias>

          <template caseid="100" id="MEM1">
            <description> Desc.</description>
          </template>
          <template caseid="101" id="MEM2">
            <description> Desc.</description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "There is a deliverable '<alias>' whose id attribute is undefined or is empty.",
            "There is a deliverable '<alias>' whose id attribute is undefined or is empty."])

    def test_verifyTemplates_doVerifyEveryTemplatePresent(self):
        '''Check that all templates are present.
        The error,
            self.assertEqual(actual, expected)
            AssertionError: 'TESTPINS' != 'TIMING'
        means one of two things:
            - TESTPINS is defined when it should not be
            - TIMING is not defined when it should be
        '''
        verifier = dmx.dmlib.templateset.verifier.Verifier(self._fullXml, doVerifyEveryTemplatePresent=True)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        # One too many deliverables
        deliverableList = list(self._expectedDeliverableNames)
        deliverableList.append('fakeExcessTemplateForTesting')
        self.assertEqual(len(self._expectedDeliverableNames) + 1, len(deliverableList))
        
        deliverableSet = Templateset('Extra', '2.0', deliverableNames=deliverableList)
        verifier = dmx.dmlib.templateset.verifier.Verifier(deliverableSet.toxml(), doVerifyEveryTemplatePresent=True)
        
        regex = r'^[A-Z][A-Z0-9_]*$'
        self.assertItemsEqual(verifier.errors, [
            "Alias and/or deliverable name 'fakeExcessTemplateForTesting' is illegal "
                         "because it does not match '{}'.".format(regex),
            "Extra, unknown deliverable '<template>' present: ['fakeExcessTemplateForTesting']"])
        self.assertFalse(verifier.isCorrect)

        # One too few deliverables
        deliverableList = list(self._expectedDeliverableNames)
        deliverableList.remove('LINT')
        deliverableSet = Templateset('Missing', '2.0', deliverableNames=deliverableList)
        verifier = dmx.dmlib.templateset.verifier.Verifier(deliverableSet.toxml(), doVerifyEveryTemplatePresent=True)
        self.assertItemsEqual(verifier.errors, [
            "All deliverable '<template>' are not defined.  These are missing: ['LINT']",
            "In alias 'FAKE', '<member>' 'LINT' is not a defined '<alias>' nor '<template>'."
            ])
        self.assertFalse(verifier.isCorrect)

    def test_verifyTemplate(self):
        '''Check the <template> verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
            <pattern id="pattern">
              fileName
            </pattern>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <!-- empty id attr -->
          <template caseid="100" id="">
            <description> Desc.</description>
            <pattern id="pattern">
              fileName1
            </pattern>
          </template>
          
          <!-- no id attr -->
          <template caseid="101">
            <description> Desc.</description>
            <pattern id="pattern">
              fileName2
            </pattern>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "There is a deliverable '<template>' whose id attribute is undefined or is empty.",
            "There is a deliverable '<template>' whose id attribute is undefined or is empty."])


    def test_verifyCaseId(self):
        '''Check the <template caseid> verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="PROPER_CASEID">
            <description> Desc.</description>
          </template>
          <template caseid=" 200 " id="UNSTRIPPED_CASEID">
            <description> Desc.</description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="   " id="WHITESPACE_CASEID">
            <description> Desc.</description>
          </template>
          <template caseid="3da" id="HEXADECIMAL_CASEID">
            <description> Desc.</description>
          </template>
          <template caseid=""    id="EMPTY_CASEID">
            <description> Desc.</description>
          </template>
          <template              id="NO_CASEID">
            <description> Desc.</description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            'In deliverable \'EMPTY_CASEID\', the <template caseid=""> case number attribute is not a decimal integer.',
            'In deliverable \'HEXADECIMAL_CASEID\', the <template caseid="3da"> case number attribute is not a decimal integer.',
            "In deliverable 'NO_CASEID', the <template caseid> case number attribute is missing.",
            'In deliverable \'WHITESPACE_CASEID\', the <template caseid="   "> case number attribute is not a decimal integer.'])

    def test_verifyDescription(self):
        '''Check the <description> verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="PROPER_DESCRIPTION">
            <description>
              This deliverable is used
              to test the getDeliverableDescription() method.
            </description>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="DUPLICATE_DESCRIPTION">
            <description>
              This description is the first of two.
            </description>
            <description>
              This description is the second of two.
            </description>
          </template>
          <template caseid="101" id="WHITESPACE_DESCRIPTION">
            <description>    </description>
          </template>
          <template caseid="102" id="EMPTY_DESCRIPTION">
            <description />
          </template>
            <template caseid="103" id="NO_DESCRIPTION">
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
                    "In deliverable 'DUPLICATE_DESCRIPTION', there are multiple '<description>' elements.  Exactly one is required.",
                    "In deliverable 'EMPTY_DESCRIPTION', '<description>' is empty.",
                    "In deliverable 'NO_DESCRIPTION', '<description>' is missing.",
                    "In deliverable 'WHITESPACE_DESCRIPTION', '<description>' contains only white space."])

    def test_verifyProducerConsumer(self):
        '''Check the <producer> and <consumer> verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="TEST">
            <description> The description. </description>
            <producer id="IP-ICD-ANALOG"/>
            <producer id="IP-ICD-ASIC"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id="LAYOUT"/>
            <consumer id="SOFTWARE-IPD"/>
            <consumer id="SVT"/>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="DUPLICATE_PRODUCER">
            <description> The description. </description>
            <producer id="IP-ICD-ANALOG"/>
            <producer id="IP-ICD-ANALOG"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id="LAYOUT"/>
            <consumer id="SOFTWARE-IPD"/>
            <consumer id="SVT"/>
          </template>
          <template caseid="101" id="DUPLICATE_CONSUMER">
            <description> The description. </description>
            <producer id="IP-ICD-ANALOG"/>
            <producer id="IP-ICD-ASIC"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id="LAYOUT"/>
            <consumer id="LAYOUT"/>
            <consumer id="SVT"/>
          </template>
          <template caseid="102" id="NO_PRODUCER_ID">
            <description> The description. </description>
            <producer />
            <producer id="IP-ICD-ASIC"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id="LAYOUT"/>
            <consumer id="SOFTWARE-IPD"/>
            <consumer id="SVT"/>
          </template>
          <template caseid="103" id="NO_CONSUMER_ID">
            <description> The description. </description>
            <producer id="IP-ICD-ANALOG"/>
            <producer id="IP-ICD-ASIC"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id="LAYOUT"/>
            <consumer/>
            <consumer id="SVT"/>
          </template>
          <template caseid="104" id="ILLEGAL_PRODUCER">
            <description> The description. </description>
            <producer id=""/>
            <producer id="ILLEGAL"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id="LAYOUT"/>
            <consumer id="SOFTWARE-IPD"/>
            <consumer id="SVT"/>
          </template>
          <template caseid="105" id="ILLEGAL_CONSUMER">
            <description> The description. </description>
            <producer id="IP-ICD-ANALOG"/>
            <producer id="IP-ICD-ASIC"/>
            <producer id="IP-ICD-DIGITAL"/>
            <consumer id=""/>
            <consumer id="ILLEGAL"/>
            <consumer id="SVT"/>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            'In deliverable \'DUPLICATE_CONSUMER\', there are duplicate \'<consumer id="LAYOUT">\'.',
            'In deliverable \'DUPLICATE_PRODUCER\', there are duplicate \'<producer id="IP-ICD-ANALOG">\'.',
            'In deliverable \'ILLEGAL_CONSUMER\', \'<consumer id="">\' has an illegal team name.',
            'In deliverable \'ILLEGAL_CONSUMER\', \'<consumer id="ILLEGAL">\' has an illegal team name.',
            'In deliverable \'ILLEGAL_PRODUCER\', \'<producer id="">\' has an illegal team name.',
            'In deliverable \'ILLEGAL_PRODUCER\', \'<producer id="ILLEGAL">\' has an illegal team name.',
            "In deliverable 'NO_CONSUMER_ID', there is a '<consumer>' with no 'id' attribute.",
            "In deliverable 'NO_PRODUCER_ID', there is a '<producer>' with no 'id' attribute."])

    def test_verifyPattern(self):
        '''Check the <pattern> deliverable item verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
            <pattern id="lef">
              &ip_name;/icc/&ip_name;.lef
            </pattern>
            <pattern id="def">
              &ip_name;/icc/&ip_name;.def
            </pattern>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="NO_FILE_PATTERN">
            <description> Desc.</description>
          
            <pattern id="file1">
              <!-- nothing but white space -->
            </pattern>
            
            <pattern id="file2"/>   <!-- empty -->
            
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
                    "In deliverable 'NO_FILE_PATTERN', '<pattern id='file1'>' is empty.",
                    "In deliverable 'NO_FILE_PATTERN', '<pattern id='file2'>' is empty."])

        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
            <pattern id="good">
              &ip_name;/rtl/....v
            </pattern>
          </template>
          <template caseid="100" id="BAD">
            <description> Desc.</description>
            <pattern id="mixed1">
              &ip_name;/*/....v
            </pattern>
            <pattern id="mixed2">
              &ip_name;/???/....v
            </pattern>
            <pattern id="dotsInDir">
              &ip_name;/.../x.v
            </pattern>
            <pattern id="multipleDotsInFile">
              &ip_name;/rtl/...x....v
            </pattern>
            <pattern id="dotsNotAtBeginningOfFile">
              &ip_name;/rtl/x....v
            </pattern>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors,
            ["In deliverable 'BAD', '<pattern> ipNameValue/*/....v' combines glob wild cards '*' or '?' with Perforce '...'.  This is unsupported.",
             "In deliverable 'BAD', '<pattern> ipNameValue/.../x.v' contains '...' wild card in the directory.  '...' is only supported at the beginning of the file name.",
             "In deliverable 'BAD', '<pattern> ipNameValue/???/....v' combines glob wild cards '*' or '?' with Perforce '...'.  This is unsupported.",
             "In deliverable 'BAD', '<pattern> ipNameValue/rtl/...x....v' contains multiple '...' wild cards in the file name.  '...' is supported only at the beginning of the file name.",
             "In deliverable 'BAD', '<pattern> ipNameValue/rtl/x....v' contains a '...' not at the beginning of the file name.  '...' is supported only at the beginning of the file name."])

    def test_verifyFilelist(self):
        '''Check the <filelist> deliverable item verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
            <filelist id="verilog">
              &ip_name;/icc/&ip_name;.v.filelist
            </filelist>
            <filelist id="spice">
              &ip_name;/icc/&ip_name;.sp.filelist
            </filelist>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="NO_FILELIST">
            <description> Desc.</description>
          
            <filelist id="filelist1">
              <!-- empty -->
            </filelist>
            
            <filelist id="filelist2"/>   <!-- empty -->
            
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'NO_FILELIST', '<filelist id='filelist1'>' is empty.",
            "In deliverable 'NO_FILELIST', '<filelist id='filelist2'>' is empty."])

    def test_verifyOpenAccess(self):
        '''Check the <openaccess> deliverable item verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD_OPENACCESS">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="OAVIEWTYPE">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view>
                layout
              </view>
            </openaccess>
            <openaccess id="abstract" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;2
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacWrongViewType">
                abstract
              </view>
            </openaccess>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'OAVIEWTYPE', the OpenAccess '<view viewtype>' attribute is not specified.",
            "In deliverable 'OAVIEWTYPE', '<view viewtype='oacWrongViewType'>' is not a valid OpenAccess view type."])

        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="LIBPATH_LIB">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                <!-- empty -->
              </libpath>
              <lib>
                <!-- empty -->
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>
            <openaccess id="abstract" mimetype="application/octet-stream">
              <!-- libpath missing -->
              <!-- lib missing -->
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                abstract
              </view>
            </openaccess>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'LIBPATH_LIB', OpenAccess library path <libpath> is empty.",
            "In deliverable 'LIBPATH_LIB', OpenAccess library name <lib> is empty.",
            "In deliverable 'LIBPATH_LIB', OpenAccess library path <libpath> is missing.",
            "In deliverable 'LIBPATH_LIB', OpenAccess library name <lib> is missing."])

        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="CELL">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                path/to/libName1
              </libpath>
              <lib>
                libName1
              </lib>
              <cell>
                <!-- empty -->
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>
            <openaccess id="abstract" mimetype="application/octet-stream">
              <libpath>
                path/to/libName2
              </libpath>
              <lib>
                libName2
              </lib>
              <!-- cell missing -->
              <view viewtype="oacMaskLayout">
                abstract
              </view>
            </openaccess>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'CELL', OpenAccess cell name <cell> is empty."
        ])

        # Test the uniqueness verification
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="UNIQUE">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lcv/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                unique
              </view>
            </openaccess>
          </template>

          <template caseid="101" id="LCV1">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lcv/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>
          </template>
          <template caseid="102" id="LCV2">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lcv/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>
          </template>

          <template caseid="103" id="LC1">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lc/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <!-- No view -->
            </openaccess>
          </template>
          <template caseid="104" id="LC2">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lc/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <!-- No view -->
            </openaccess>
          </template>

          <template caseid="105" id="L1">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lcv/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <!-- No cell or view -->
            </openaccess>
          </template>
          <template caseid="106" id="L2">
            <description> Desc.</description>
            <openaccess id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/lcv/&ip_name;1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <!-- No cell or view -->
            </openaccess>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "Item 'ipNameValue/lcv/ipNameValue1/ipNameValue/layout' appears in both deliverables 'LCV2' and 'LCV1', but the shared attribute is not defined or is empty in '<openaccess>' within deliverable 'LCV2'.",
            "Item 'ipNameValue/lc/ipNameValue1/ipNameValue' appears in both deliverables 'LC2' and 'LC1', but the shared attribute is not defined or is empty in '<openaccess>' within deliverable 'LC2'.",
            "Item 'ipNameValue/lcv/ipNameValue1' appears in both deliverables 'L2' and 'L1', but the shared attribute is not defined or is empty in '<openaccess>' within deliverable 'L2'."])

    def test_verifyMilkyway(self):
        '''Check the parts of the <milkyway> deliverable item verification that are different from <openaccess>.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD_MILKYWAY">
            <description> Desc.</description>
            <milkyway id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="Layout">
                layout
              </view>
            </milkyway>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="NOVIEWTYPEISOK">
            <description> Desc.</description>
            <milkyway id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;1
              </libpath>
              <lib>
                &ip_name;1
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view> <!-- No view type is okay for Milkyway-->
                layout
              </view>
            </milkyway>
          </template>
          <template caseid="100" id="NONEXISTENTVIEWTYPE">
            <description> Desc.</description>
            <milkyway id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;2
              </libpath>
              <lib>
                &ip_name;2
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="NonexistentViewType">
                abstract
              </view>
            </milkyway>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'NONEXISTENTVIEWTYPE', '<view viewtype='NonexistentViewType'>' is not a valid Milkyway view type."])

        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="LIBPATH_LIB_MISMATCH">
            <description> Desc.</description>
            <milkyway id="layout" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                doesNotMatchPath
              </lib>
            </milkyway>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'LIBPATH_LIB_MISMATCH', Milkyway library name 'doesNotMatchPath' does not match the library path 'ipNameValue/icc/ipNameValue'."])

    def test_verifyDeliverableItemCommon(self):
        '''Check the deliverable item common verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD">
            <description> Desc.</description>
          
            <pattern id="pattern">
              fileName
            </pattern>

            <filelist id="filelist">
              file.filelist
            </filelist>

            <milkyway id="milkyway" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
            </milkyway>

            <openaccess id="openaccess" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/virtuoso/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>

          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="NO_ID_ATTR">
            <description> Desc.</description>
          
            <pattern id="">
              fileName1
            </pattern>

            <pattern>
              fileName2
            </pattern>

            <filelist id="">
              file1.filelist
            </filelist>

            <filelist>
              file2.filelist
            </filelist>

            <milkyway id="" mimetype="application/octet-stream">
              <libpath>
                mwLib1
              </libpath>
              <lib>
                mwLib1
              </lib>
            </milkyway>

            <milkyway mimetype="application/octet-stream">
              <libpath>
                mwLib2
              </libpath>
              <lib>
                mwLib2
              </lib>
            </milkyway>

            <openaccess id="" mimetype="application/octet-stream">
              <libpath>
                oaPath1
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>

            <openaccess mimetype="application/octet-stream">
              <libpath>
                oaPath2
              </libpath>
              <lib>
                &ip_name;
              </lib>
              <cell>
                &ip_name;
              </cell>
              <view viewtype="oacMaskLayout">
                layout
              </view>
            </openaccess>

          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'NO_ID_ATTR', item '<pattern>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<pattern>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<filelist>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<filelist>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<openaccess>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<openaccess>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<milkyway>', the id attribute is not defined or is empty.",
            "In deliverable 'NO_ID_ATTR', item '<milkyway>', the id attribute is not defined or is empty."])


    def test_verifyShared(self):
        '''Check the shared deliverable item attribute verification.'''
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="OA">
            <description> Desc.</description>
            <openaccess id="oaDesign" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib> &ip_name; </lib>
              <cell> &ip_name; </cell>
              <view viewtype="oacMaskLayout"> layout </view>
            </openaccess>
          </template>
          <template caseid="101" id="MW">
            <description> Desc.</description>
            <milkyway id="mwLib" mimetype="application/octet-stream" shared="OA">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
            </milkyway>
          </template>
          <template caseid="100" id="PATTERN">
            <description> Desc.</description>
            <pattern id="file1" shared="OA">
              &ip_name;/icc/&ip_name;
            </pattern>
            <pattern id="file2">
              uniquePatternName
            </pattern>
          </template>
          <template caseid="102" id="FILELIST">
            <description> Desc.</description>
            <filelist id="filelist1" shared="OA">
              &ip_name;/icc/&ip_name;
            </filelist>
            <filelist id="filelist2">
              uniqueFilelistName
            </filelist>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        # Test all shared missing
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="OA">
            <description> Desc.</description>
            <openaccess id="oaDesign" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib> &ip_name; </lib>
            </openaccess>
          </template>
          <template caseid="101" id="MW">
            <description> Desc.</description>
            <milkyway id="mwLib" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
            </milkyway>
          </template>
          <template caseid="102" id="PATTERN">
            <description> Desc.</description>
            <pattern id="file1">
              &ip_name;/icc/&ip_name;
            </pattern>
            <pattern id="file2">
              uniquePatternName
            </pattern>
          </template>
          <template caseid="103" id="FILELIST">
            <description> Desc.</description>
            <filelist id="filelist1">
              &ip_name;/icc/&ip_name;
            </filelist>
            <filelist id="filelist2">
              uniqueFilelistName
            </filelist>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "Item 'ipNameValue/icc/ipNameValue' appears in both deliverables 'MW' and 'OA', but the shared attribute is not defined or is empty in '<milkyway>' within deliverable 'MW'.",
            "Item 'ipNameValue/icc/ipNameValue' appears in both deliverables 'PATTERN' and 'OA', but the shared attribute is not defined or is empty in '<pattern>' within deliverable 'PATTERN'.",
            "Item 'ipNameValue/icc/ipNameValue' appears in both deliverables 'FILELIST' and 'OA', but the shared attribute is not defined or is empty in '<filelist>' within deliverable 'FILELIST'."
        ])

        # Test same file shared, but shared in a "chained" fashion which is illegal
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="OA">
            <description> Desc.</description>
            <openaccess id="oaDesign" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib> &ip_name; </lib>
              <cell> &ip_name; </cell>
              <view viewtype="oacMaskLayout"> layout </view>
            </openaccess>
          </template>
          <template caseid="101" id="MW">
            <description> Desc.</description>
            <milkyway id="mwLib" mimetype="application/octet-stream" shared="OA">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
            </milkyway>
          </template>
          <template caseid="102" id="PATTERN">
            <description> Desc.</description>
            <pattern id="file1" shared="MW">
              &ip_name;/icc/&ip_name;
            </pattern>
            <pattern id="file2">
              uniquePatternName
            </pattern>
          </template>
          <template caseid="103" id="FILELIST">
            <description> Desc.</description>
            <filelist id="filelist1" shared="PATTERN">
              &ip_name;/icc/&ip_name;
            </filelist>
            <filelist id="filelist2">
              uniqueFilelistName
            </filelist>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "Item 'ipNameValue/icc/ipNameValue' appears in both deliverables 'PATTERN' and 'OA', but the shared attribute 'MW' in '<pattern>' within deliverable 'PATTERN' does not match.",
            "Item 'ipNameValue/icc/ipNameValue' appears in both deliverables 'FILELIST' and 'OA', but the shared attribute 'PATTERN' in '<filelist>' within deliverable 'FILELIST' does not match."])

        # Test implicit sharing within a single deliverable
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="GOOD_SCH">
            <description> Desc.</description>
            <openaccess id="schematic" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib> &ip_name; </lib>
              <cell> &ip_name; </cell>
              <view viewtype="oacSchematic"> schematic </view>
            </openaccess>
            <openaccess id="symbol" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib> &ip_name; </lib>
              <cell> &ip_name; </cell>
              <view viewtype="oacSchematicSymbol"> symbol </view>
            </openaccess>
          </template>
          <template caseid="101" id="SHARED_IS_MISSING">
            <description> Desc.</description>
            <openaccess id="schematic" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;
              </libpath>
              <lib> &ip_name; </lib>
              <cell> &ip_name; </cell>
              <view viewtype="oacSchematic"> schematic </view>
            </openaccess>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "Item 'ipNameValue/icc/ipNameValue/ipNameValue/schematic' appears in both deliverables "
                "'SHARED_IS_MISSING' and 'GOOD_SCH', but the shared attribute is not defined or is "
                "empty in '<openaccess>' within deliverable 'SHARED_IS_MISSING'."])

#        # Test shared with nonexistent target
#        xml = '''<?xml version="1.0" encoding="utf-8"?>
#        <templateset>
#          <template id="OA">
#            <openaccess id="oaDesign" mimetype="application/octet-stream" shared="NONEXISTENT">
#              <libpath>
#                &ip_name;/icc/&ip_name;
#              </libpath>
#              <lib> &ip_name; </lib>
#              <cell> &ip_name; </cell>
#              <view viewtype="oacMaskLayout"> layout </view>
#            </openaccess>
#          </template>
#          <template id="MW">
#            <milkyway id="mwLib" mimetype="application/octet-stream" shared="NONEXISTENT">
#              <libpath>
#                &ip_name;/icc/&ip_name;
#              </libpath>
#            </milkyway>
#          </template>
#          <template id="PATTERN">
#            <pattern id="file1" shared="NONEXISTENT">
#              &ip_name;/icc/&ip_name;
#            </pattern>
#            <pattern id="file2">
#              uniquePatternName
#            </pattern>
#          </template>
#          <template id="FILELIST">
#            <filelist id="filelist1" shared="NONEXISTENT">
#              &ip_name;/icc/&ip_name;
#            </filelist>
#            <filelist id="filelist2">
#              uniqueFilelistName
#            </filelist>
#          </template>
#        </templateset>'''
#        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
#        self.assertFalse(verifier.isCorrect)
#        self.assertEqual(len(verifier.errors), 4)
#        self.assertEqual(verifier.errors[0],
#                         "Deliverable name 'NONEXISTENT' used as a shared name within deliverable 'OA' is not defined.")
#        self.assertEqual(verifier.errors[1],
#                         "Deliverable name 'NONEXISTENT' used as a shared name within deliverable 'MW' is not defined.")
#        self.assertEqual(verifier.errors[2],
#                         "Deliverable name 'NONEXISTENT' used as a shared name within deliverable 'PATTERN' is not defined.")
#        self.assertEqual(verifier.errors[3],
#                         "Deliverable name 'NONEXISTENT' used as a shared name within deliverable 'FILELIST' is not defined.")

    def test_verifyUniqueItemNames(self):
        '''Check that all items within a deliverable have a unique id attribute.
        It is okay to reuse the same ids in another deliverable.
        '''
        # Verifies good
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="UNIQUE_ITEM_IDS">
            <description> Desc.</description>
            <openaccess id="oa1" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.oa1
              </libpath>
              <lib> &ip_name;.oa1 </lib>
            </openaccess>
            <openaccess id="oa2" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.oa2
              </libpath>
              <lib> &ip_name;.oa2 </lib>
            </openaccess>
            <milkyway id="mw1" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.mw1
              </libpath>
              <lib>
                &ip_name;.mw1
              </lib>
            </milkyway>
            <milkyway id="mw2" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.mw2
              </libpath>
              <lib>
                &ip_name;.mw2
              </lib>
            </milkyway>
            <pattern id="file1">
              &ip_name;/icc/&ip_name;.file1
            </pattern>
            <pattern id="file2">
              &ip_name;/icc/&ip_name;.file2
            </pattern>
            <filelist id="filelist1">
              &ip_name;/icc/&ip_name;.filelist1
            </filelist>
            <filelist id="filelist2">
              &ip_name;/icc/&ip_name;.filelist2
            </filelist>
          </template>
          
          <!-- Re-use the same names in another deliverable.
               The files names must still be unique. -->
          <template caseid="101" id="REUSE_ABOVE_ITEM_IDS">
            <description> Desc.</description>
            <openaccess id="oa1" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.oa1a
              </libpath>
              <lib> &ip_name;.oa1a </lib>
            </openaccess>
            <milkyway id="mw1" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.mw1a
              </libpath>
              <lib>
                &ip_name;.mw1a
              </lib>
            </milkyway>
            <pattern id="file1">
              &ip_name;/icc/&ip_name;.file1a
            </pattern>
            <filelist id="filelist1">
              &ip_name;/icc/&ip_name;.filelist1a
            </filelist>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertEqual(verifier.errors, [])
        self.assertTrue(verifier.isCorrect)
        
        # Non-unique item id for each item type 
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="100" id="REUSE_ITEM_IDS">
            <description> Desc.</description>
            <openaccess id="notUnique" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.oaNotUnique1
              </libpath>
              <lib> &ip_name;.notUnique1 </lib>
            </openaccess>
            <openaccess id="notUnique" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.oaNotUnique2
              </libpath>
              <lib> &ip_name;.oaNotUnique2 </lib>
            </openaccess>
            <milkyway id="notUnique" mimetype="application/octet-stream">
              <libpath>
                &ip_name;/icc/&ip_name;.mwNotUnique
              </libpath>
              <lib>
                &ip_name;.mwNotUnique
              </lib>
            </milkyway>
            <pattern id="notUnique">
              &ip_name;/icc/&ip_name;.fileNotUnique
            </pattern>
            <filelist id="notUnique">
              &ip_name;/icc/&ip_name;.filelistNotUnique
            </filelist>
          </template>
        </templateset>'''
        verifier = dmx.dmlib.templateset.verifier.Verifier(xml)
        self.assertFalse(verifier.isCorrect)
        self.assertItemsEqual(verifier.errors, [
            "In deliverable 'REUSE_ITEM_IDS', the '<filelist>' id attribute 'notUnique' is not unique.",
            "In deliverable 'REUSE_ITEM_IDS', the '<openaccess>' id attribute 'notUnique' is not unique.",
            "In deliverable 'REUSE_ITEM_IDS', the '<openaccess>' id attribute 'notUnique' is not unique.",
            "In deliverable 'REUSE_ITEM_IDS', the '<milkyway>' id attribute 'notUnique' is not unique."])

if __name__ == "__main__":
    unittest.main(verbosity=2,failfast=True)
