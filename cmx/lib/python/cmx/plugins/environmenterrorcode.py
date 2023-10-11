#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/environmenterrorcode.py#1 $
$Change: 7449889 $
$DateTime: 2023/01/19 00:34:15 $
$Author: lionelta $

Description: dmx roadmap
Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import sys
import logging
import textwrap
import getpass
import time
import re

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 


class EnvironmentErrorcode(Command):
    @classmethod
    def get_help(cls):
        myhelp = '''\
            List out DMX errorcode with detail info.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('--list', '-l', required=False, default='', help='Specify a syntax to filter errorcodes to be displayed')

    @classmethod
    def extra_help(cls):
        extra_help = '''\

        'dmx environment errorcode' is a command that let users list out the DMX internal errorcode information.

        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
    
