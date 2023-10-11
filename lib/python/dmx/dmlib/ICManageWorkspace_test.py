#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageWorkspace_test.py#1 $

"""
Test the ICManageWorkspace class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

import os
import unittest
import shutil

# (unused argument) pylint: disable = W0613
def load_tests(loader, tests, ignore): 
    '''Load the ICManageWorkspace.py doctest tests into unittest.'''
    if os.path.exists('test_icmanageworkspace01_copy'):
        shutil.rmtree('test_icmanageworkspace01_copy')
    shutil.copytree('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5', 
                    'test_icmanageworkspace01_copy')
    
    if os.path.exists('test_icmanageworkspace01_copyWithNoSavedData'):
        shutil.rmtree('test_icmanageworkspace01_copyWithNoSavedData')
    shutil.copytree('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5', 
                    'test_icmanageworkspace01_copyWithNoSavedData')

    if os.path.exists('test_arbitrary.save'):
        shutil.rmtree('test_arbitrary.save')

    if os.path.exists('test'):
        shutil.rmtree('test')
    os.makedirs('test/dir')
    
    # Removed due to missing test data; see http://fogbugz.altera.com/default.asp?221371
#    import doctest
#    import shutil
#    import dm.ICManageWorkspace
    # tests.addTests(doctest.DocTestSuite(dm.ICManageWorkspace))
    return tests

class TestICManageWorkspace(unittest.TestCase):
    """Test the ICManageWorkspace class."""

    def setUp(self):
        self.tearDown()
        os.makedirs('test/dir')
    
    def tearDown(self):
        if os.path.exists('test'):
            shutil.rmtree('test')


if __name__ == "__main__":
    # import cProfile
    # cProfile.run("unittest.main()", '/home/jmcgehee/workspace/dm/profile.txt')
    unittest.main()
