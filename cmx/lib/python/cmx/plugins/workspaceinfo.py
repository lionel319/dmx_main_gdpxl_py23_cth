#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/workspaceinfo.py#1 $
$Change: 7482526 $
$DateTime: 2023/02/13 23:50:04 $
$Author: lionelta $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

from future import standard_library
standard_library.install_aliases()
import os
import sys
import logging
import textwrap
import argparse
import io

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

LOGGER = logging.getLogger(__name__)

class WorkspaceInfo(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Returns current workspace info
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Returns current workspace info. No arguments are needed.        
        '''
        return textwrap.dedent(myhelp)
        
    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)

    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

