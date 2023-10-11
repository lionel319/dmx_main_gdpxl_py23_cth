#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/mw_hierarchy_test.py#1 $

"""
Test the mw_hierarchy class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2013 Altera Corporation"

import os
import unittest
import doctest
import shutil
import dmx.dmlib.deliverables.utils.General as General
import dmx.dmlib.mw_hierarchy
from dmx.dmlib.dmError import dmError

def load_tests(loader, tests, ignore): # unused arg pylint: disable = W0613
    '''Load the mw_hierarchy.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.mw_hierarchy))
    return tests

@unittest.skip ("broken tests")
class TestMwHierarchy(unittest.TestCase): # pylint: disable=R0904
    """Test the MwHierarchy class."""

    def setUp(self):
        '''Set up the test'''
        self._macrosFileName = 'test1.report_macros.json'
        self._referenceControlFileName = 'test1.reference_control_file.rpt'
        self._workingDirName = 'mw_hierarchy'
        self.tearDown()
        dmRoot = os.path.dirname(os.path.dirname(__file__))
        shutil.copytree(os.path.join(dmRoot, 'inputData', self._workingDirName), self._workingDirName)

    def tearDown(self):
        if os.path.exists(self._macrosFileName):
            os.remove(self._macrosFileName)
        if os.path.exists(self._referenceControlFileName):
            os.remove(self._referenceControlFileName)
        if os.path.exists(self._workingDirName):
            shutil.rmtree(self._workingDirName)
        if os.path.exists(self._workingDirName):
            shutil.rmtree(self._workingDirName, onerror=errorhandler)
            
        def errorhandler(function, path, execinfo): #unused arg pylint: disable = W0613
            os.chmod(path, 0777)
            try:
                function(path)
            except:
                raise OSError("Cannot delete temporary file '{}'".format(path))

    # Leading "0" causes empty test to run first.
    def test_0empty(self):
        '''Test initialization on empty instance'''
        with self.assertRaises(dmError):
            dmx.dmlib.mw_hierarchy.MwHierarchy('nonexistentLib', 'cell1')
        with self.assertRaises(dmError):
            dmx.dmlib.mw_hierarchy.MwHierarchy('mw_hierarchy/test1', 'nonexistentCell')

    def test_traversal(self):
        '''Test the `topDesign`, `hardMacros`, `softMacros` properties'''
        self.assertFalse(os.path.exists(self._referenceControlFileName))
        hier = dmx.dmlib.mw_hierarchy.MwHierarchy('mw_hierarchy/test1', 'test1',
                                           workingDirName=self._workingDirName,
                                           referenceControlFileName=self._referenceControlFileName)
        
        self.assertEqual(hier.topDesign, [os.path.abspath(u"mw_hierarchy/test1"),
                                          u"test1"])
        
        self.assertSetEqual(hier.hardMacros, set([u"testIP", u"testIP_2x",
                                                  u"testIP_2y", u"testIP_3y"]))
        
        self.assertSetEqual(hier.softMacros, set([u"col_w1", u"col_w1_v0",
                                                  u"cross_block_w", u"l_block_w",
                                                  u"row_w1", u"square_w"]))

    def test_writeReferenceControlFile(self):
        '''Test the `writeReferenceControlFile() class method'''
        self.assertFalse(os.path.exists(self._referenceControlFileName))
        dmx.dmlib.mw_hierarchy.MwHierarchy.writeReferenceControlFile('mw_hierarchy/test1',
                                                   self._referenceControlFileName,
                                                   workingDirName=self._workingDirName)
        # Sometimes the file does not show up immediately
        contents = General.retryReadFile(self._referenceControlFileName, 100.0)
        self.assertTrue('LIBRARY' in contents)
        self.assertTrue('REFERENCE' in contents)
        
        if os.path.exists(self._referenceControlFileName):
            os.remove(self._referenceControlFileName)
        self.assertFalse(os.path.exists(self._referenceControlFileName))
        with self.assertRaises(dmError):
            dmx.dmlib.mw_hierarchy.MwHierarchy.writeReferenceControlFile('nonexistentLib',
                                                   self._referenceControlFileName)
        self.assertFalse(os.path.exists(self._referenceControlFileName))


if __name__ == "__main__":
    unittest.main()
