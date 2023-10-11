#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/environment.py#1 $
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

class Environment(Command):
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Dump out a list of useful info for debugging purposes.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        overlay arguments
        '''
        add_common_args(parser)
        parser.add_argument('--nomail', required=False, default=False, action='store_true')

    @classmethod
    def extra_help(cls):
        '''
        Detailed help.
        '''
        extra_help = '''\

        'dmx environment' is a command that will
        - dumps out a list of generic info which is useful for debugging purposes.
        - this info will be emailed to the user as attachment, which then can be forwarded to psgicmsupport@intel.com for further debugging.

        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

