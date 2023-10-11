#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_stringifycmd.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys


LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.stringifycmd import StringifyCmd as sc


class TestStringifyCmd(unittest.TestCase):

    def setUp(self):
        self.basecmd = '''echo "a'b c"'''
        self.sc = sc(basecmd = self.basecmd)

    def tearDown(self):
        os.environ.pop("DB_FAMILIES",'')


    def test_100___make_sure_DEFAULT_envvar_is_constant(self):
        with self.assertRaisesRegexp(Exception, "Can't rebind const:"):
            self.sc.DEFAULT.envvar = 'haha'
    def test_100___make_sure_DEFAULT_sshopts_is_constant(self):
        with self.assertRaisesRegexp(Exception, "Can't rebind const:"):
            self.sc.DEFAULT.sshopts = 'haha'
    def test_100___make_sure_DEFAULT_arcopts_is_constant(self):
        with self.assertRaisesRegexp(Exception, "Can't rebind const:"):
            self.sc.DEFAULT.arcopts = 'haha'
    def test_100___make_sure_DEFAULT_washopts_is_constant(self):
        with self.assertRaisesRegexp(Exception, "Can't rebind const:"):
            self.sc.DEFAULT.washopts = 'haha'
    def test_100___make_sure_DEFAULT_defkw_is_constant(self):
        with self.assertRaisesRegexp(Exception, "Can't rebind const:"):
            self.sc.DEFAULT.defkw = 'haha'
    def test_100___make_sure_DEFAULT_envkw_is_constant(self):
        with self.assertRaisesRegexp(Exception, "Can't rebind const:"):
            self.sc.DEFAULT.envkw = 'haha'

    def test_200___get_basecmd_string___default___DB_FAMILIES_not_set(self):
        s = sc(basecmd=self.basecmd, envvar='default')
        ret = s.get_basecmd_string()
        self.assertEqual(ret, self.basecmd)

    def test_201___get_basecmd_string___default_DB_FAMILIES_set(self):
        os.environ['DB_FAMILIES'] = 'falcon wharfrock'
        s = sc(basecmd=self.basecmd, envvar='default')
        ret = s.get_basecmd_string()
        self.assertEqual(ret, 'setenv DB_FAMILIES "falcon wharfrock";'+self.basecmd)

    def test_202___get_basecmd_string___with_envvar(self):
        s = sc(basecmd=self.basecmd, envvar={'a':1, 'b':"x y"})
        ret = s.get_basecmd_string()
        print(ret)
        self.assertEqual(ret, 'setenv b "x y";setenv a "1";echo "a\'b c"')

    def test_220___get_washcmd_string___default___DB_FAMILIES_not_set(self):
        s = sc(basecmd=self.basecmd, washopts='default')
        ret = s.get_washcmd_string()
        print(ret)
        self.assertRegexpMatches(ret, 'wash -n `reportwashgroups -f .*` psgda -c \'echo "a\'"\'"\'b c"\'')

    def test_221___get_washcmd_string___DB_FAMILIES_set(self):
        opts = {'DB_FAMILIES': 'falcon wharfrock'}
        s = sc(basecmd=self.basecmd, washopts=opts)
        ret = s.get_washcmd_string()
        print(ret)
        self.assertEqual(ret, 'wash -n `reportwashgroups -f falcon wharfrock` -c \'echo "a\'"\'"\'b c"\'')

    def test_222___get_washcmd_string___DB_FAMILIES_and_groups_set(self):
        opts = {'DB_FAMILIES': 'falcon gundersonrock', 'groups': 'xx yy zz'}
        s = sc(basecmd=self.basecmd, washopts=opts)
        ret = s.get_washcmd_string()
        print(ret)
        self.assertEqual(ret, 'wash -n `reportwashgroups -f falcon gundersonrock` xx yy zz -c \'echo "a\'"\'"\'b c"\'')

    def test_223___get_washcmd_string___None(self):
        s = sc(basecmd=self.basecmd)
        ret = s.get_washcmd_string()
        self.assertEqual(ret, s.get_basecmd_string())

    
    def test_250___get_arccmd_string___only_default_arcopts(self):
        s = sc(basecmd=self.basecmd, arcopts='default')
        ret = s.get_arccmd_string()
        print(ret)
        self.assertRegexpMatches(ret, 'arc submit --interactive  --local .* -- \'echo "a\'"\'"\'b c"\'')

    def test_251___get_arccmd_string___options_resources_fields_set(self):
        opts = {
            'options': {'-a': "x", "--b": "", "-c":"123"},
            'resources':'project/bundle/arc,dmx/12.34',
            'fields':{"name":"x y z", "mem": "64"}
        }
        s = sc(basecmd=self.basecmd, arcopts=opts)
        ret = s.get_arccmd_string()
        print(ret)
        self.assertRegexpMatches(ret, 'arc submit --b  -a x -c 123 project/bundle/arc,dmx/12.34 mem="64" name="x y z" -- \'echo "a\'"\'"\'b c"\'')

    def test_252___get_arccmd_string___None(self):
        s = sc(basecmd=self.basecmd, arcopts=None)
        ret = s.get_arccmd_string()
        self.assertEqual(ret, s.get_washcmd_string())


    def test_270___get_sshcmd_string___None(self):
        s = sc(basecmd=self.basecmd, sshopts=None)
        ret = s.get_sshcmd_string()
        print(ret)
        self.assertEqual(ret, s.get_arccmd_string())

    def _test_271___get_sshcmd_string___default(self):
        s = sc(basecmd=self.basecmd, sshopts='default')
        ret = s.get_sshcmd_string()
        print(ret)
        self.assertEqual(ret, 'ssh -q localhost \'echo "a\'"\'"\'b c"\'')

    def _test_271___get_sshcmd_string___host_set(self):
        host = 'abc'
        s = sc(basecmd=self.basecmd, sshopts={'host':host})
        ret = s.get_sshcmd_string()
        print(ret)
        self.assertEqual(ret, 'ssh -q abc \'echo "a\'"\'"\'b c"\'')

    def _test_271___get_sshcmd_string___site_set(self):
        site = 'png'
        s = sc(basecmd=self.basecmd, sshopts={'site':site})
        ret = s.get_sshcmd_string()
        print(ret)
        self.assertRegexpMatches(ret, 'ssh -q .+png.intel.com \'echo "a\'"\'"\'b c"\'')


    def test_500___get_finalcmd_string___default(self):
        d = 'default'
        s = sc(basecmd=self.basecmd, arcopts=d, washopts=d, sshopts=d)
        ret = s.get_finalcmd_string()
        print(ret)
        self.assertRegexpMatches(ret, 'ssh -q localhost \'.*arc submit --interactive  --local .* -- \'"\'"\'wash -n `reportwashgroups -f .*` psgda -c \'"\'"\'"\'"\'"\'"\'"\'"\'echo "a\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'"\'b c"\'"\'"\'"\'"\'"\'"\'"\'"\'\'"\'"\'\'')


    def test_600___nested_stringifycmd_arc_calls(self):
        d = {'resources':':env:', 'fields': {'name':'s1'}}
        s1 = sc(basecmd=self.basecmd, arcopts=d, washopts=None, sshopts=None)
        ret1 = s1.get_finalcmd_string()

        d = {'resources':':env:', 'fields': {'name':'s2'}}
        s2 = sc(basecmd=ret1, arcopts=d, washopts=None, sshopts=None)
        ret2 = s2.get_finalcmd_string()
        print("ret2: {}".format(ret2))
        ans = '/p/psg/ctools/arc/2019.1/bin/arc submit .+ name="s2" -- \'/p/psg/ctools/arc/2019.1/bin/arc submit .+ name="s1" -- \'"\'"\'echo "a\'"\'"\'"\'"\'"\'"\'"\'"\'b c"\'"\'"\'\''
        self.assertRegexpMatches(ret2, ans)


    def test_601___nested_stringifycmd_ssh_calls(self):
        basecmd = 'whoami; hostname'
        d1 = {'host':'ppgdacron01.png.intel.com'}
        s1 = sc(basecmd=basecmd, sshopts=d1, washopts=None, arcopts=None)
        ret1 = s1.get_finalcmd_string()

        d2 = {'host':'sjdacron.sc.intel.com'}
        s2 = sc(basecmd=ret1, sshopts=d2, washopts=None, arcopts=None)
        s2.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
        ret2 = s2.get_finalcmd_string()
        print("ret2: {}".format(ret2))
        ans = '/p/psg/da/infra/admin/setuid/tnr_ssh -q sjdacron.sc.intel.com \'ssh -q ppgdacron01.png.intel.com \'"\'"\'whoami; hostname\'"\'"\'\''
        self.assertRegexpMatches(ret2, ans)

    
    def test_700___copy_default_options(self):
        s = sc('ls')
        for opt in ['envvar', 'arcopts', 'washopts', 'sshopts']:
            ret = sc.copy_default_options(opt)
            self.assertEqual(ret, getattr(s.DEFAULT, opt))

if __name__ == '__main__':
    unittest.main()
