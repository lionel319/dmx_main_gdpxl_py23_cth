#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/login.py#2 $
$Change: 7527701 $
$DateTime: 2023/03/15 23:36:50 $
$Author: lionelta $
'''
import sys
import logging
import textwrap
import re
import os

from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 


class Login(Command):
    '''plugin for "dmx list"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Login user to dmx system.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help list
        '''
        extra_help = '''\
            Login user to dmx system.
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)

    @classmethod
    def command(cls, args):
        #dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
        os.system('/p/psg/flows/common/icmadmin/gdpxl/1.2/icm_home/scripts/icm_login.py')
        
