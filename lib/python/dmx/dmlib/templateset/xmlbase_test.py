#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/xmlbase_test.py#1 $

"""
Test the XmlBase class.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import unittest
import doctest
import dmx.dmlib.templateset.xmlbase


def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the XmlBase doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.templateset.xmlbase))
    return tests

class TestXmlBase(unittest.TestCase): # pylint: disable=R0904
    """Test the XmlBase class."""

    def setUp(self):
        pass
    
    def tearDown(self):
        pass


#    def test_empty(self):
#        '''An empty test really does not make sense for this class.'''
#        pass

    def test_toxml(self):
        '''Test the toxml() nethod'''
        sub = dmx.dmlib.templateset.xmlbase.DeliverableSubClass('text &&entity; & < >')
        
        self.assertEqual(sub.toxml(),
                         '<?xml version="1.0" encoding="utf-8"?><top><element>text &entity; &amp; &lt; &gt;</element></top>')
        self.assertEqual(sub.toxml(fmt=None),
                         '<?xml version="1.0" encoding="utf-8"?><top><element>text &entity; &amp; &lt; &gt;</element></top>')
        self.assertEqual(sub.toxml(fmt='pretty'),
            '<?xml version="1.0" encoding="utf-8"?>\n<top>\n  <element>\n    text &entity; &amp; &lt; &gt;\n  </element>\n</top>\n')
        self.assertEqual(sub.toxml(fmt='doctest'),
                         '<?xml version="1.0" encoding="utf-8"?> <top> <element> text &entity; &amp; &lt; &gt; </element> </top> ')
        
    def test_write(self):
        '''Test the write() nethod'''
        sub = dmx.dmlib.templateset.xmlbase.DeliverableSubClass('text &&entity; & < >')
        
        sub.write('writeDefault.xml')
        f = open('writeDefault.xml')
        actual = f.read()
        f.close()
        self.assertEqual(actual,
                         '<?xml version="1.0" encoding="utf-8"?><top><element>text &entity; &amp; &lt; &gt;</element></top>')

        sub.write('writeNone.xml', fmt=None)
        f = open('writeNone.xml')
        actual = f.read()
        f.close()
        self.assertEqual(actual,
                         '<?xml version="1.0" encoding="utf-8"?><top><element>text &entity; &amp; &lt; &gt;</element></top>')

        sub.write('writePretty.xml', fmt='pretty')
        f = open('writePretty.xml')
        actual = f.read()
        f.close()
        self.assertEqual(actual,
            '<?xml version="1.0" encoding="utf-8"?>\n<top>\n  <element>\n    text &entity; &amp; &lt; &gt;\n  </element>\n</top>\n')

        sub.write('writeDoctest.xml', fmt='doctest')
        f = open('writeDoctest.xml')
        actual = f.read()
        f.close()
        self.assertEqual(actual,
                         '<?xml version="1.0" encoding="utf-8"?> <top> <element> text &entity; &amp; &lt; &gt; </element> </top> ')
        
    def test_boolToStr(self):
        # pylint: disable=C0111,W0212
        self.assertEqual(dmx.dmlib.templateset.xmlbase.DeliverableSubClass._boolToStr(True), 'yes')
        self.assertEqual(dmx.dmlib.templateset.xmlbase.DeliverableSubClass._boolToStr(False), 'no')
        
    def test_unescapeAmp(self):
        # pylint: disable=C0111,W0212
        self.assertEqual(dmx.dmlib.templateset.xmlbase.DeliverableSubClass._unescapeAmp(
            '<element> text &amp;&amp;entity; &amp; &lt; &gt; </element>'), '<element> text &entity; &amp; &lt; &gt; </element>')


if __name__ == "__main__":
    unittest.main()
