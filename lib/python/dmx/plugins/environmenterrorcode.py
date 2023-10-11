#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/environmenterrorcode.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
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

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.environmenterrorcode

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
        ret = 1
        dmxenv = dmx.abnrlib.flows.environmenterrorcode.EnvironmentErrorcode(search=args.list)
        ret = dmxenv.run()

        return (ret)
