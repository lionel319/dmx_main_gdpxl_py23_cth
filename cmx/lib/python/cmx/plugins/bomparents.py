#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/bomparents.py#1 $
$Change: 7463577 $
$DateTime: 2023/01/31 01:08:26 $
$Author: lionelta $

Description: bom parent dmx subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2013
All rights reserved.
'''

import sys
import logging
import textwrap
import itertools
import os

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

class BomParentsError(Exception): pass

class BomParents(Command):
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Get parents for given bom
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        bom parents arguments
        '''
        add_common_args(parser)
        parser.add_argument('-p', '--project',
                            metavar='project', required=False, default=None,
                            help='The name of the project')
        parser.add_argument('-i', '--ip',
                            metavar='IP', required=True,
                            help='The name of the ip')
        parser.add_argument('-b', '--bom',
                            metavar='bom', required=True,
                            help='The name of the bom')
        parser.add_argument('-d', '--deliverable',
                            metavar='deliverable', required=False, default=None,
                            help='The name of the deliverable')
        parser.add_argument('--report-all', action='store_true',
                            required=False,
                            help='report all parents ')
        parser.add_argument('--hierarchy', action='store_true',
                            required=False,
                            help='report parents in full hierarchy.')

    @classmethod
    def extra_help(cls):
        '''
        Detailed help for bom parents 
        '''
        extra_help = '''\
        "bom parents" return all the parent associated to the given bom

        Example
        =======
        $dmx bom parents -p i10socfm -i liotest1 -b dev
        Report all parents that has child i10socfm/liotest1@dev

        $dmx bom parents -p i10socfm -i liotest1 -b dev --report-all
        Report all parents that has child i10socfm/liotest1@dev including tnr-placeholder*
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        return dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
