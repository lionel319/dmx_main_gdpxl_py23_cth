#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/workspacelocaledit.py#1 $
$Change: 7495712 $
$DateTime: 2023/02/22 23:34:12 $
$Author: lionelta $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

import os
import sys
import logging
import textwrap
import argparse
from pprint import pprint

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

LOGGER = logging.getLogger(__name__)

class WorkspaceLocalEdit(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Locally edit an DMX populated workspace
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Locally edit an DMX populated workspace
        
        This command does the following:-
            1. Files from immutable-boms will be copied and chmod 770
            2. Files from mutable-boms will be chmod 770

        This command is only meant for you to run if you only plan to make some local modification for testing, but have no plans in checking in those files. 
        If you would like to modify a files, and later on check them im then you should use 'dmx scm co/ci' instead

        Work Flow
        =============
        Enginner setenv DMX_WORKSPACE to their workspace disk, eg:-
            > setenv DMX_WORKSPACE /nfs/site/disks/da_infra_1/users/yltan/
        Engineer runs the command:-
            > dmx workspace localedit -w <workspace to update> -i <ip> -d <deliverables> -f <files>
        This will 
            - check each ip and deliverables files
            - if is symlink, copy to local and chmod 770
            - if it is a local files, chmod 770
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('-w', '--wsname',  required=True, help='Workspace Name. e.g. wplim.i10socfm.liotest1.122 or workspace id \'myws\'') 
        parser.add_argument('-i', '--ip',  required=True, default=None) 
        parser.add_argument('-d', '--deliverables',  required=True, default=None, nargs='+') 
        parser.add_argument('-f', '--files',  required=False, default=None, nargs='+') 



    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

