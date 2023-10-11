#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/lioneltest.py#1 $
$Change: 7465054 $
$DateTime: 2023/01/31 22:28:11 $
$Author: lionelta $

Description: dmx "owner" subcommand plugin
Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''
import sys
import logging
import textwrap
import pwd
import re
import csv

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

class LionelTest(Command):
    '''plugin for "dmx report owner"'''

    @classmethod
    def get_help(cls):
        myhelp = '''\
            This is a test service for Lionel
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        extra_help = '''\
            This is a test service for Lionel

            This module is purely meant for Lionel to do testing.
            Please do not call it.
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        '''
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)
        parser.add_argument('-b', '--bom',  metavar='bom', required=False)
        parser.add_argument('--all', required=False, action='store_true',
                            help='Show all records for bom including updaters.')
        parser.add_argument('--format', required=False, choices=['csv'], 
                            help='Format the output into the desired format.')
        parser.add_argument('--owner', required=False, action='store_true', 
                            help='Returns only the owner value.')
        parser.add_argument('--creator', required=False, action='store_true', 
                            help='Returns only the creator value.')
        parser.add_argument('--designer', required=False, action='store_true', 
                            help='Returns only the designer/last updater value.')
        parser.add_argument('--set-owner', metavar='setowner', required=False, 
                            help='When specified, given value will be used to set the Owner property value.')        
        '''
    @classmethod
    def command(cls, args):
        import os
        from pprint import pprint

        dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
        print('dmxlibdir: {}'.format(os.path.abspath(dmxlibdir)))
        sys.path.insert(0, dmxlibdir)
        import dmx.abnrlib.config_factory
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm("da_i16", "dai16liotest1", "dev")
        pprint(cfobj)
        pprint(cfobj.flatten_tree())

        #dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
