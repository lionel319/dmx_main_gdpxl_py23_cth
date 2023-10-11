#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/reportlist.py#1 $
$Change: 7449859 $
$DateTime: 2023/01/19 00:03:41 $
$Author: lionelta $

Description: dmx "list" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
import sys
import logging
import textwrap
import re

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

class ReportListError(Exception): pass

class ReportList(Command):
    '''plugin for "dmx list"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            List existing projects/ips/deliverables objects or BOMs
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help list
        '''
        extra_help = '''\
            List existing projects/ips/deliverables objects or BOMs
            
            NOTE: Snap BOMs that follow these formats:
                  snap-<digit>
                    For example: snap-1, snap-11, snap-111, ...
                  snap-<digit>-<alphabet>
                    For example: snap-1-abc, snap-11-def, snap-111-ghi, ...
                  Will not be displayed unless --debug is given. 
                  These snap formats are reserved for TNR system and should 
                  be ignored by users.                    
    
            Example
            =======
            List all projects
            $ dmx report list -p

            List all ips in i10socfm
            $ dmx report list -p i10socfm -i

            List all ips named cw_lib 
            $dmx report list -p -i cw_lib

            List all boms in i10socfm/cw_lib
            $ dmx report list -p i10socfm -i cw_lib -b

            List all boms in i10socfm/cw_lib:rtl
            $ dmx report list -p i10socfm -i cw_lib -d rtl -b

            List all boms start with REL in i10socfm/cw_lib
            $ dmx report list -p i10socfm -i cw_lib -b 'REL*'

            List all deliverables in i10socfm/cw_lib
            $ dmx report list -p i10socfm -i cw_lib -d
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('-p', '--project', nargs='?', const='*', metavar='project', default='*')
        parser.add_argument('-i', '--ip', nargs='?', const='*', metavar='ip')
        parser.add_argument('-d', '--deliverable', nargs='?', const='*', metavar='deliverable')
        parser.add_argument('-b', '--bom',  nargs='?', const='*', metavar='bom')
        parser.add_argument('--switches',  action='store_true', 
            help = "show results as dmx command switches for pasting into other dmx commands")
        parser.add_argument('--props',  action='store_true', 
            help = "show properties stored on configs")
        parser.add_argument('--regex',  action='store_true', 
            help = "use perl style regular expressions instead of glob style regular expressions")

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
