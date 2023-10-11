#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/workspaceupdate.py#1 $
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
from pprint import pprint

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, lib)

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.workspace import Workspace
import dmx.abnrlib.flows.workspaceupdate

LOGGER = logging.getLogger(__name__)

class WorkspaceUpdate(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Update an ICM workspace
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Syncs an ICM workspace and utilizes cache for immutable BOM
        
        This command does the following:-
            1. Syncs files (based on given --cfgfile/--deliverables options)
            2. Files from immutable-boms will be symlinked from a cache area if is not localedit
            3. Files from mutable-boms will be physically populates 


        Work Flow
        =============
        Enginner setenv DMX_WORKSPACE to their workspace disk, eg:-
            > setenv DMX_WORKSPACE /nfs/site/disks/da_infra_1/users/yltan/
        Engineer runs the command:-
            > dmx workspace update -w <workspace to update> 
        This will 
            - Re-symlink immutable deliverable from cache 
            - icmp4 sync ... for mutable deliverable

        Sync only a few deliverables (--deliverables)
        =============================================
        To sync only a selective deliverables, use the --deliverables options. Eg:-
            > dmx workspace update -w 'my_ws' -d ipspec rtl lint

        This will only update all (ipspec, rtl, lint) deliverables into the workspace.


        Foce Sync only (--force)
        =============================================
        To force sync even you have a localedit or checkout file
        or you have modified the bom of your workspace, use the --force options. Eg:-
            > dmx workspace update -w 'my_ws' -f

        This will
            - Re-symlink immutable deliverable from cache even you have localedit(physical) file
            - icmp4 sync -f ... for mutable deliverable
        Note that this will overwrite any non check-in file. Use with cautious. 


        Update different ip/deliverable combination (--cfgfile)
        =====================================================
        To update a further fine-tuned set of ip/deliverable, use the --cfgfile
            > dmx workspace update -w 'my_ws'  --cfgfile /full/path/to/file
        (kindly refer to next section for format of the cfgfile)


        Example: cfgfile
        ================
        The following examples shows 
        - the content of the cfgfile
        - the outcome of running $dmx workspace update

        Example 1
        ~~~~~~~~~
        [1]
        variants: ip1 ip2 ip3
        libtypes: rtl oa
        [2]
        variants: ip4 ip5
        libtypes: cdl bds

        Explanation 1
        ~~~~~~~~~~~~~
        This will sync
        - libtype rtl and oa for variants ip1, ip2 and ip3
        - libtype cdl and bds for variants ip4 and ip5

        -------------------------------------------------------------------------------

        Example 2
        ~~~~~~~~~
        [1]
        variants: *
        libtypes: rtl 
        [2]
        variants: ip4 
        libtypes: cdl 

        Explanation 2
        ~~~~~~~~~~~~~
        This will sync
        - libtype rtl for all variants 
        - libtype cdl for variant ip4
        (variant ip4 will have libtype cdl and rtl sync'ed to the workspace)

        -------------------------------------------------------------------------------

        Example 3
        ~~~~~~~~~
        [1]
        variants: *
        libtypes: *

        Explanation 3
        ~~~~~~~~~~~~~
        This will sync
        - everything (all libtypes for all the available variants) into the workspace.

        -------------------------------------------------------------------------------

        Example 4
        ~~~~~~~~~
        [1]
        variants: sa_*
        libtypes: netlist
        [2]
        variants: *
        libtypes: rtl
        
        Explanation 4
        ~~~~~~~~~~~~~
        This will sync
        - the netlist libtype for all sub-assemblies( sa_*) variants
        - the rtl libtype for all available variants.

        -------------------------------------------------------------------------------

        Example 5
        ~~~~~~~~~
        [1]
        variants: ar_lib
        libtypes: view_rtl viewphys ipspec
        
        Explanation 4
        ~~~~~~~~~~~~~
        This will sync
        - the libtypes defined under view_rtl  for ar_lib
        - the libtypes defiend under view_phys for ar_lib
        - the rtl libtype for ar_lib

        -------------------------------------------------------------------------------
        .
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('-w', '--wsname',  required=True, help='Workspace Name. e.g. wplim.i10socfm.liotest1.122 or workspace id \'myws\'') 
        parser.add_argument('-o', '--original_user', required=False, help=argparse.SUPPRESS) 
        parser.add_argument('-f', '--force', action='store_true', required=False, help='force update') 
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-d', '--deliverables',  required=False, default=None, nargs='+') 
        group.add_argument('-c', '--cfgfile',  required=False, default=None) 



    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''        
        ret = 1
        cfgfile = args.cfgfile

        # workspace populate will always use cache 
        cache = True
        preview = args.preview
        wu = dmx.abnrlib.flows.workspaceupdate.WorkspaceUpdate(args.wsname, cfgfile=args.cfgfile, deliverables=args.deliverables, original_user=args.original_user, preview=args.preview, force=args.force)
        ret = wu.run()

        return ret
