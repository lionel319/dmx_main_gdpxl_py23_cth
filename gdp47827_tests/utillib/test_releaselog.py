#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_releaselog.py $
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
import dmx.utillib.releaselog
from dmx.errorlib.exceptions import DmxErrorICCF02

class TestReleaseLog(unittest.TestCase):

    def setUp(self):
        self.filepath = '/tmp/filepath'
        self.project = 'project'
        self.variant = 'variant'
        self.libtype = 'libtype'
        self.config = 'config'
        self.releaser = 'releaser'
        self.datetime = 'datetime'
        self.arcjob = 'arcjob'
        self.relconfig = 'REL123'
        self.milestone = 'milestone'
        self.thread = 'thread'
        self.description = 'description'
        self.release_id = 'release_id'


    def test_001___relconfig_not_starting_with_REL(self):
        with self.assertRaisesRegexp(DmxErrorICCF02, 'Relconfig relconfig must begin with REL'):
            a = dmx.utillib.releaselog.ReleaseLog(self.filepath, self.project, self.variant, self.libtype, self.config, self.releaser, self.datetime, self.arcjob, 'relconfig', self.milestone, self.thread, self.description, self.release_id)

    def test_010___check_data___no_result(self):
        a = dmx.utillib.releaselog.ReleaseLog(self.filepath, self.project, self.variant, self.libtype, self.config, self.releaser, self.datetime, self.arcjob, self.relconfig, self.milestone, self.thread, self.description, self.release_id)
        print(a.json)
        ans = {'project': 'project', 'variant': 'variant', 'libtype': 'libtype', 'config': 'config', 'releaser': 'releaser', 'datetime': 'datetime', 'arcjob': 'arcjob', 'relconfig': 'REL123', 'milestone': 'milestone', 'thread': 'thread', 'description': 'description', 'release_id': 'release_id', 'runtime': 0, 'arcjob_path': 'https://psg-sc-arc.sc.intel.com/arc/dashboard/reports/show_job/arcjob', 'dmx_version': 'main_gdpxl', 'dmxdata_version': 'main/data', 'results': []}
        self.assertEqual(self._delete_inconsistent_kvp(a.json), self._delete_inconsistent_kvp(ans))

    def test_020___check_data___with_result(self):
        a = dmx.utillib.releaselog.ReleaseLog(self.filepath, self.project, self.variant, self.libtype, self.config, self.releaser, self.datetime, self.arcjob, self.relconfig, self.milestone, self.thread, self.description, self.release_id)
        a.add_result('flow', 'subflow', 'topcell', 'status', 'error', 'waiver')
        print(a.json)
        ans = {'project': 'project', 'variant': 'variant', 'libtype': 'libtype', 'config': 'config', 'releaser': 'releaser', 'datetime': 'datetime', 'arcjob': 'arcjob', 'relconfig': 'REL123', 'milestone': 'milestone', 'thread': 'thread', 'description': 'description', 'release_id': 'release_id', 'runtime': 0, 'arcjob_path': 'https://psg-sc-arc.sc.intel.com/arc/dashboard/reports/show_job/arcjob', 'dmx_version': 'main_gdpxl', 'dmxdata_version': 'main/data', 'results': []}
        ans['results'] = [{'flow': 'flow', 'subflow': 'subflow', 'topcell': 'topcell', 'status': 'status', 'error': 'error', 'waiver': 'waiver'}]
        self.assertEqual(self._delete_inconsistent_kvp(a.json), self._delete_inconsistent_kvp(ans))

    def _delete_inconsistent_kvp(self, data):
        for k in ['dmx_version', 'dmxdata_version']:
            data.pop(k)

if __name__ == '__main__':
    unittest.main()
