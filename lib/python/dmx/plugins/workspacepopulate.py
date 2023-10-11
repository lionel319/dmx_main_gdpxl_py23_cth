#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/workspacepopulate.py#1 $
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
from pprint import pprint

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, lib)

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.workspace import Workspace
import dmx.abnrlib.flows.workspacepopulate
import dmx.utillib.admin

LOGGER = logging.getLogger(__name__)

class WorkspacePopulate(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Creates and syncs an ICM workspace and utilizes cache for immutable BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Creates and syncs an ICM workspace and utilizes cache for immutable BOM
        
        This command does the following:-
            1. Creates a workspace on <envvar:DMX_WORKSPACE>/<workspacename>
            2. syncs files (based on given --cfgfile/--deliverables options)
            3. Files from immutable-boms will be symlinked from a cache area
            4. Files from mutable-boms will be physically populates 


        Work Flow
        =============
        Enginner setenv DMX_WORKSPACE to their workspace disk, eg:-
            > setenv DMX_WORKSPACE /nfs/site/disks/da_infra_1/users/yltan/
        Engineer runs the command:-
            > dmx workspace populate -p i10socfm -i liotest1 -b rel_and_dev -w 'my_new_ws' 
        This will 
            - create a workspace at /nfs/site/disks/da_infra_1/users/yltan/my_new_ws
            - sync all mutable boms with physical files
            - sync all immutable boms with symlinks pointing from cache area.


        Sync only a few deliverables (--deliverables)
        =============================================
        To sync only a selective deliverables, use the --deliverables options. Eg:-
            > dmx workspace populate -p i10socfm -i liotest1 -b rel_and_dev -w 'my_new_ws'  --deliverables ipspec rtl lint

        This will only sync down all (ipspec, rtl, lint) deliverables into the workspace.


        Sync different ip/deliverable combination (--cfgfile)
        =====================================================
        To sync a further fine-tuned set of ip/deliverable, use the --cfgfile
            > dmx workspace populate -p i10socfm -i liotest1 -b rel_and_dev -w 'my_new_ws'  --cfgfile /full/path/to/file
        (kindly refer to next section for format of the cfgfile)


        Example: cfgfile
        ================
        The following examples shows 
        - the content of the cfgfile
        - the outcome of running $dmx workspace populate

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
        parser.add_argument('-p', '--project',  required=True) 
        parser.add_argument('-i', '--ip',  required=True) 
        parser.add_argument('-b', '--bom',  required=True)
        parser.add_argument('-f', '--force_cache', action='store_true')
        parser.add_argument('-w', '--wsname',  required=True, help='Workspace Name. If :icm: is provided, icm-client name (<user>.<project>.<variant>.<number>) will be used.') 
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-d', '--deliverables',  required=False, default=None, nargs='+') 
        group.add_argument('-c', '--cfgfile',  required=False, default='') 

    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''        
        ret = 1
        cfgfile = args.cfgfile
        force_cache = args.force_cache

        # workspace populate will always use cache 
        cache = True
        preview = args.preview
        default_path = os.getcwd()

        if os.environ.get('DMX_FAMILY_LOADER') == 'family_test.json':
            ws = Workspace()
            ret = ws.create_action(args.project, args.ip, args.bom, os.environ.get('DMX_WORKSPACE'), False, preview, True)
            if ret == 0:
                os.chdir(ws._workspacename)
                ret = Workspace.sync_action(args.cfgfile, True, False, False, preview, untar=False, untaronly=False)
                os.chdir(default_path)
                return ret
            else:
                LOGGER.error('Workspace create fail. Please check your argument.')
                return ret

        if args.force_cache and not dmx.utillib.admin.is_admin(os.environ.get('USER')):
            raise DmxErrorICWS06('Only admin can use -f/--force_cache.')


        wp = dmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(args.project, args.ip, args.bom, 
            args.wsname, cfgfile=args.cfgfile, deliverables=args.deliverables, preview=preview, debug=args.debug, force_cache=force_cache)
        ret = wp.run()

        return ret
