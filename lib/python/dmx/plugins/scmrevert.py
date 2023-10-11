#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/scmrevert.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
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

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.scm import *

LOGGER = logging.getLogger(__name__)

class SCMRevert(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Reverts checked-out file in a workspace
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        dmx scm revert command reverts checked-out/opened files in a workspace. This will revert the
        files back to it's original untampered state.

        Command will work similar to 'icmp4 revert' command whereby a file pattern is provided.
        If file pattern is provided, command will crawl the file pattern for files to be reverted
        if --manifest option is specified, command will refer to manifest to determine which files to revert

        Command must be run in a workspace where files are supposed to be reverted.
        --unchanged option will revert only files that have not changed since checkout.

        Examples
        ========
        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm revert filepath/... 
        Revert any checked-out files found in <workspaceroot>/ip/deliverable/filepath/... 
        
        $ cd <workspaceroot>
        $ dmx scm revert -i ip -d deliverable --manifest
        Revert any checked-out files defined in manifest for deliverable

        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm revert --manifest
        Revert any checked-out files defined in manifest for deliverable
         
        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm revert --manifest --cell c1 c2
        Revert any checked-out files defined in manifest for deliverable that matches cell c1 and c2

        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm revert filepath/... --manifest
        Revert any checked-out files found in <workspaceroot>/ip/deliverable/filepath/...
        Revert any checked-out files defined in manifest for deliverable 
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('filespec',  metavar='file ...', nargs='*',
                            help='File pattern to indicate files to checkout. Follows Perforce pattern convention.')
        parser.add_argument('--manifest',  required=False, action='store_true',
                            help='Check-in files defined in manifest')
        parser.add_argument('-i', '--ip',  metavar='ip', required=False,
                            help='IP to revert files from. If not provided, IP will be extracted from current working directory.')
        parser.add_argument('-d', '--deliverable',  metavar='deliverable', required=False,
                            help='Deliverable to revert files from. If not provided, deliverable will be extracted from current working directory')
        parser.add_argument('--workspace',  metavar='workspace', required=False, 
                            help='Workspace to revert files from. If not provided, workspace will be assumed as the current working directory. Workspace must be provided with fullpath.')
        parser.add_argument('--cell',  metavar='cell', required=False, nargs='+', default=[],
                            help='Cell to revert files from. If not provided, every cell will be reverted.')
        parser.add_argument('--unchanged', required=False, 
                            help='Revert only unchanged checked-out files.',
                            action='store_true', default=False)
        
    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        filespec = args.filespec
        manifest = args.manifest
        ip = args.ip
        deliverable = args.deliverable
        workspace = args.workspace if args.workspace else os.getcwd()
        cell = args.cell
        unchanged = args.unchanged
        preview = args.preview        

        ret = 1
        scm = SCM(preview)
        ret = scm.revert_action(workspace, filespec, manifest, ip, deliverable, cell, unchanged=unchanged)
        return ret
