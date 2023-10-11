#!/usr/bin/env python

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', 'python'))
from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner



loader = unittest.TestLoader()
start_dir = sys.argv[1]
suite = loader.discover(start_dir, pattern='test_*.py')

#runner = unittest.TextTestRunner()
runner = TeamcityTestRunner(verbosity=2)
runner.run(suite)
