#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/CheckerDmzBase_test.py#1 $

"""
Test the dmx.dmlib.CheckerDmzBase.Checker class.
"""


__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2013 Altera Corporation"

import unittest
import doctest
#import os
#import shutil
import subprocess

import dmx.dmlib.CheckerDmzBase
#from dmx.dmlib.VpMock import VpMock # @UnusedImport

def load_tests(loader, tests, ignore): #pylint:disable = W0613
    '''Load the ICManageChecklist.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.CheckerDmzBase))
    return tests

class CheckVsIntermapTest(unittest.TestCase):
    """Test the dmx.dmlib.CheckerDmzBase.Checker class."""

    def setUp(self):
        pass

    def tearDown(self):
        pass
   
    def test_cksum(self):
        """Compare the result of the cksum method against the result of UNIX cksum"""
        sumActual = dmx.dmlib.CheckerDmzBase.cksum('/bin/ls')
        sumExpectedRaw = str(subprocess.check_output(['cksum', '/bin/ls']))
        sumExpectedList = sumExpectedRaw.split()
        sumExpectedTuple = (int(sumExpectedList[0]), int(sumExpectedList[1]), sumExpectedList[2],)
        self.assertEqual(sumActual, tuple(sumExpectedTuple))
        
        sumActual = dmx.dmlib.CheckerDmzBase.cksum('/bin/cat')
        sumExpectedRaw = str(subprocess.check_output(['cksum', '/bin/cat']))
        sumExpectedList = sumExpectedRaw.split()
        sumExpectedTuple = (int(sumExpectedList[0]), int(sumExpectedList[1]), sumExpectedList[2],)
        self.assertEqual(sumActual, tuple(sumExpectedTuple))
        
        sumActual = dmx.dmlib.CheckerDmzBase.cksum('/bin/bash')
        sumExpectedRaw = str(subprocess.check_output(['cksum', '/bin/bash']))
        sumExpectedList = sumExpectedRaw.split()
        sumExpectedTuple = (int(sumExpectedList[0]), int(sumExpectedList[1]), sumExpectedList[2],)
        self.assertEqual(sumActual, tuple(sumExpectedTuple))
        
        sumActual = dmx.dmlib.CheckerDmzBase.cksum('/bin/chmod')
        sumExpectedRaw = str(subprocess.check_output(['cksum', '/bin/chmod']))
        sumExpectedList = sumExpectedRaw.split()
        sumExpectedTuple = (int(sumExpectedList[0]), int(sumExpectedList[1]), sumExpectedList[2],)
        self.assertEqual(sumActual, tuple(sumExpectedTuple))
        
if __name__ == "__main__":
    # import cProfile
    # cProfile.run("unittest.main()", '/home/jmcgehee/workspace/dm/profile.txt')
    unittest.main()
