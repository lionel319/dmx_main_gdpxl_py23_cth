#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_project.py $
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
from dmx.ecolib.project import Project, ProjectError

class TestProject(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.project = 'i14socnd'
        self.Project = Project(self.family, self.project)

    def test_project_properties(self):
        '''
        Tests the Project object properties
        '''
        self.assertEqual(self.Project.family, self.family)           
        self.assertEqual(self.Project.project, self.project)

if __name__ == '__main__':
    unittest.main()
