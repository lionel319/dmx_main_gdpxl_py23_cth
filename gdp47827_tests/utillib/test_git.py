#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_git.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys
import re
import logging
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.contextmgr
import dmx.utillib.git


class TestGit(unittest.TestCase):
    def setUp(self):
        self.gu = dmx.utillib.git.Git()

    def test_020___get_id_from_pvll___got(self):
        ret = self.gu.get_id_from_pvll('da_i18a', 'dai18aliotest1', 'cthfe', 'dev')
        self.assertEqual(u"L7371246", ret)

    def test_021___get_id_from_pvll___none(self):
        ret = self.gu.get_id_from_pvll('da_i18a', 'dai18aliotest1', 'cthfe', 'devxxxxx')
        self.assertEqual(None, ret)
    
    def test_025___get_pvll_from_id___got(self):
        ret = self.gu.get_pvll_from_id("L7371246")
        ans = {u'project:parent:name': u'da_i18a', u'variant:parent:name': u'dai18aliotest1', u'name': u'dev', u'libtype:parent:name': u'cthfe'}
        self.assertEqual(ans, ret)

    def test_026___get_pvll_from_id___none(self):
        ret = self.gu.get_pvll_from_id("xxxxxxx")
        self.assertEqual(None, ret)

    def test_050___get_master_git_repo_path(self):
        ret = self.gu.get_master_git_repo_path(idtag='lionel')
        ans = '/nfs/site/disks/psg.git.001/git_repos/lionel-a0'
        self.assertEqual(ret, ans)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
