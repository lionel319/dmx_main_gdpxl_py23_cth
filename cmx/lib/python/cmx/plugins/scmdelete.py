#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/scmdelete.py#1 $
$Change: 7486171 $
$DateTime: 2023/02/15 23:50:31 $
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

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

LOGGER = logging.getLogger(__name__)

class SCMDelete(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Deletes non-opened file(s) from a workspace
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        dmx scm delete command deletes files in a workspace and the repository. 

        Command will work similar to 'icmp4 delete' command whereby a file pattern is provided.
        If file pattern is provided, command will crawl the file pattern for files to be deleted.
        if --manifest option is specified, command will refer to manifest to determine which files to delete

        Command must be run in a workspace where files are supposed to be deleted.
        Command will not delete checked-out files. 

        Examples
        ========
        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm delete filepath/... --desc "meaningful description"
        Delete files found in <workspaceroot>/ip/deliverable/filepath/... 

        $ cd <workspaceroot>
        $ dmx scm delete -i ip -d deliverable --manifest --desc "meaningful description"
        Delete files defined in manifest for deliverable

        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm delete --manifest --desc "meaningful description"
        Delete files defined in manifest for deliverable
         
        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm delete --manifest --cell c1 c2 --desc "meaningful description"
        Delete files defined in manifest for deliverable that matches cell c1 and c2

        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm delete filepath/... --manifest --desc "meaningful description"
        Delete files found in <workspaceroot>/ip/deliverable/filepath/...
        Delete files defined in manifest for deliverable 
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('filespec',  metavar='file ...', nargs='*',
                            help='File pattern to indicate files to checkout. Follows Perforce pattern convention.')
        parser.add_argument('--desc',  required=True,
                            help='Reason for deletion')
        parser.add_argument('--manifest',  required=False, action='store_true',
                            help='Check-in files defined in manifest')
        parser.add_argument('-i', '--ip',  metavar='ip', required=False,
                            help='IP to delete files from. If not provided, IP will be extracted from current working directory.')
        parser.add_argument('-d', '--deliverable',  metavar='deliverable', required=False,
                            help='Deliverable to delete files from. If not provided, deliverable will be extracted from current working directory')
        parser.add_argument('--workspace',  metavar='workspace', required=False, 
                            help='Workspace to delete files from. If not provided, workspace will be assumed as the current working directory. Workspace must be provided with fullpath.')
        parser.add_argument('--cell',  metavar='cell', required=False, nargs='+', default=[],
                            help='Cell to delete files from. If not provided, every cell will be deleted.')
        
    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

