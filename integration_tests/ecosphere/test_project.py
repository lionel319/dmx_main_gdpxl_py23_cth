#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/ecosphere/test_project.py $
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
from dmx.ecolib.project import Project, ProjectError

class TestProject(unittest.TestCase):
    def setUp(self):
        self.family = '_Testdata'
        self.project = 'i10socfm'

    def test_object_instantiation(self):
        project = Project(self.family, self.project)
        self.assertIsInstance(project, Project)            

if __name__ == '__main__':
    unittest.main()
