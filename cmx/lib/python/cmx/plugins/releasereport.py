#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/releasereport.py#1 $
$Change: 7495740 $
$DateTime: 2023/02/23 00:04:05 $
$Author: lionelta $

Description: dmx "release library" subcommand plugin
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import sys
import logging
import textwrap
import itertools
import os

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

class ReleaseReport(Command):

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Retrieve the release status of the given arc-job-id.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)

        '''subcommand arguments'''
        parser.add_argument('-a', '--arcjobid', required=True, help='the release arc-job-id, which is reported out during "dmx release". Look for the line that says "Your release job ID is ######" ')
        
    @classmethod
    def extra_help(cls):
        extra_help = '''\
                     '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
        
