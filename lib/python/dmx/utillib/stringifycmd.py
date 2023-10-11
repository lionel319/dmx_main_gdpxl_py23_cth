#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/stringifycmd.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Module that stringifies a given command with correct quatations.

Copyright (c) Altera Corporation 2016
All rights reserved.


Documentation
=============
dmx finds itself a frequent need to 
- submit a job under a someone else (eg: headless:psginfraadm) 
- submit job to different sites
- submit job with different linux groups

This API aims at wrapping all the technical details of generating the correct final command-line,
and returns the string which is properly and correctly quotified.

The strings-of-commands must strictly follow the following sequence in oder for everything to 
work correctly:-
    > sshcmd( arccmd( washcmd( basecmd ) ) )

All the inputs to StringifyCmd (expect `basecmd`) accepts the a dict, None, or the 'default' keyword.
When this keyword is provided instead of a dict, it will use the dict defined 
in `*OPTS_DEFAULT` as the input.

If None is supplied to a specific inputs of the StringifyCmd(*opts), 
then the specified command will not be run, eg:-
- if washopt=None, the final cmd will be
    > sshcmd( arccmd( basecmd ) )
- if sshopt=None and washopt=None, the final cmd will be
    > arccmd( basecmd )

Some of the keys in the dict supplied to the StringifyCmd inputs do accept the ':env:' keyword.
When this keyword is used, it will get the value from the current environemt.


Input Parameters
----------------
`basecmd`:
    type: string
    desc: should be correctly quotified.
      eg: 'a.pl --desc '"'"'haha'"'"''
          'ls'


`envvar`:
    type: dict
    desc: environment variables that should be set/inherited into `cmd`
     eg1: {
            'DMX_FAMILIES': ':env:',    (accepts ':env:')
            'LAUGH': 'haha hehe',
          }
    ret1: 'setenv DMX_FAMILIES "falcon wharfrock"; setenv LAUGH "haha hehe"; `basecmd`'


`washopts`:
    type: dict/None/'default'
    desc: wash with acquiring these groups before running `basecmd`

     eg1: {
            'DB_FAMILIES': 'falcon wharfrock'   (accepts ':env:')
            'groups': 'psgda'
          }
          > uses 'reportwashgroups -f falcon wharfrock' to find the linux groups
          > append with 'psgda'
    ret1: 'wash -n psgfln psgwhr .... psgda -c '<return_string_of_`envvar`>''
    (NOTE: The behavior when 'DB_FAMILIES' is set to ':env:' is slightly special, whereby
        If the envvar of DB_FAMILIES is defined, it will be used,
        Else, DB_FAMILIES will be given the envvar value that is set in DB_FAMILY
        if both are False, it will return '')


`arcopts`:
    type: dict
    desc: arc submit command

     eg1: {
            'options': {
                '-jw': '',
                '-c': '123'
            },
            'fields':  {
                'name': 'try 1'
            },
            'resources': 'project/falcon/branch/fm6revbmain/rc,dmx/12.12'   (accepts ':env:')
          }
    ret1: 'arc submit -jw -c 123  project/falcon/branch/fm6revbmain/rc,dmx/12.12  name="try 1" -- '"'"'<return_string_of_`washcmd`> '"'"''


`sshopts`:
    type: dict
    desc: ssh command that should be run.
     eg1: {
            'host': 'sjdacron.sc.intel.com' -or- 'localhost'
          }
          -or-
          {
            'site': 'sc' / 'png'
          }
    ret1: if 'host' is given, then use it (take precedence).
          if only 'site' is given, finds a random host and use it. 
          (method to find random host is using dmx/utillib/server.py)

'''

import os
import logging
import sys
import re
from pprint import pprint
import copy

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.utillib.arcutils
import dmx.utillib.server
import dmx.utillib.const
from dmx.utillib.utils import quotify
import dmx.utillib.utils

class StringifyCmd(object):

    DEFAULT = dmx.utillib.const._const()
    DEFAULT.envvar = {
        'DB_FAMILIES': ':env:'
    }
    DEFAULT.sshopts = {
        'host': 'localhost'
    }
    DEFAULT.arcopts = {
        'options': {
            '--interactive': '',
            '--local': ''
        },
        'resources': ':env:'
    }
    DEFAULT.washopts = {
        'DB_FAMILIES': ':env:',
        'groups': 'psgda'
    }
    DEFAULT.defkw = 'default'
    DEFAULT.envkw = ':env:'

    def __init__(self, basecmd, envvar=None, sshopts=None, arcopts=None, washopts=None):
        self.logger = logging.getLogger(__name__)

        self.basecmd = basecmd
        self.envvar = envvar if envvar != self.DEFAULT.defkw else self.DEFAULT.envvar
        self.sshopts = sshopts if sshopts != self.DEFAULT.defkw else self.DEFAULT.sshopts
        self.arcopts = arcopts if arcopts != self.DEFAULT.defkw else self.DEFAULT.arcopts
        self.washopts = washopts if washopts != self.DEFAULT.defkw else self.DEFAULT.washopts

        ### These commands a assigned to these 'exposed' properties purposely
        ### This gives the caller a chance to override these exe where/when they deem fit.
        ### One good example is when sshexe's 'ssh' needs to be replaced with 'ssh_as_psginfraadm'
        self.sshexe = 'ssh'
        self.arcexe = '/p/psg/ctools/arc/2019.1/bin/arc'
        self.washexe = 'wash'
        self.reportwashgroupsexe = 'reportwashgroups'


    def get_finalcmd_string(self):
        return self.get_sshcmd_string()


    def get_sshcmd_string(self):
        arccmd = self.get_arccmd_string()
        if not self.sshopts:
            return arccmd

        sshcmd = '{} -q'.format(self.sshexe)
        if 'host' in self.sshopts:
            v = self.sshopts['host']
        elif 'site' in self.sshopts:
            v = dmx.utillib.server.Server(site=self.sshopts['site']).get_working_server()
        sshcmd += ' {}'.format(v)
        sshcmd += ' {}'.format(quotify(self.get_arccmd_string()))
        self.logger.debug("sshcmd: {}".format(sshcmd))
        return sshcmd


    def get_arccmd_string(self):
        washcmd = self.get_washcmd_string()
        if not self.arcopts:
            return washcmd

        arccmd = '{} submit'.format(self.arcexe)
        if 'options' in self.arcopts:
            for k in sorted(self.arcopts['options'].keys()):
                v = self.arcopts['options'][k]
                arccmd += ' {} {}'.format(k, v)
        if 'resources' in self.arcopts:
            v = self.arcopts['resources']
            if v == self.DEFAULT.envkw:
                v = dmx.utillib.arcutils.ArcUtils().get_arc_job()['resources']
            arccmd += ' {}'.format(v)
        if 'fields' in self.arcopts:
            for k in sorted(self.arcopts['fields'].keys()):
                v = self.arcopts['fields'][k]
                arccmd += ' {}="{}"'.format(k, v)
        arccmd += ' -- {}'.format(quotify(self.get_washcmd_string()))
        self.logger.debug("arccmd: {}".format(arccmd))
        return arccmd


    def get_washcmd_string(self):
        basecmd = self.get_basecmd_string()
        if not self.washopts:
            return basecmd

        washcmd = '{} -n'.format(self.washexe)

        v = self.washopts.get('DB_FAMILIES')
        if v == self.DEFAULT.envkw:
            v = self.get_envvar_db_families_else_db_family()
        if v:
            washcmd += ' `{} -f {}`'.format(self.reportwashgroupsexe, v)

        v = self.washopts.get('groups')
        if v:
            washcmd += ' {}'.format(v)
        
        washcmd += ' -c {}'.format(quotify(self.get_basecmd_string()))
        self.logger.debug("washcmd: {}".format(washcmd))
        return washcmd


    def get_envvar_db_families_else_db_family(self):
        v = os.getenv("DB_FAMILIES")
        if v:
            return v
        else:
            v = os.getenv("DB_FAMILY")
            return v


    def get_basecmd_string(self):
        ret = self.basecmd
        if self.envvar:
            for k in sorted(self.envvar.keys()):
                v = self.envvar[k]
                if v == self.DEFAULT.envkw:
                    v = os.getenv(k)
                    if v == None:
                        continue
                if self.get_users_shell() == 'bash':
                    ret = 'export {}="{}";'.format(k, v) + ret
                else:
                    ret = 'setenv {} "{}";'.format(k, v) + ret
        self.logger.debug("basecmd: {}".format(ret))
        return ret


    def get_users_shell(self):
        ### Always return tcsh as psginfraadm's SHELL is always tcsh
        if 'tnr_ssh' in self.sshexe or 'psginfraadm' in self.sshexe:
            return 'tcsh'

        ### this command does not do 'arc submit'. so , return the local $SHELL
        if not self.arcopts or 'options' not in self.arcopts:
            if 'bash' in os.getenv("SHELL"):
                return 'bash'
            else:
                return 'tcsh'

        ### this command does do 'arc submit', thus, we need to fund the $SHELL during 'arc submit'
        else:

            #exitcode, stdout, stderr = dmx.utillib.utils.run_command("{} submit --watch -- 'echo $SHELL'".format(self.arcexe))
            exitcode, stdout, stderr = dmx.utillib.utils.run_command("ypcat passwd | grep ^$USER:".format(self.arcexe))
            self.logger.debug("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcide, stdout, stderr))
            if '/bash' in stdout:
                return 'bash'
            else:
                return 'tcsh'

    @classmethod
    def copy_default_options(cls, opttype):
        return copy.deepcopy(getattr(cls.DEFAULT, opttype))


if __name__ == '__main__':
    pass

