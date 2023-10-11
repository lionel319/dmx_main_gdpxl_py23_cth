#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/workspaceinfo.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
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

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.workspace import Workspace

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

        ret = 1
        ret = Workspace.info_action()
        return ret
