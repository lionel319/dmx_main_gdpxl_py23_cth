#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/workspacecheck.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx workspace check"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''
from __future__ import print_function

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511

import sys
import os
import textwrap
import logging
from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.workspace import Workspace

class WorkspaceCheck(Command):
    LOGGER = logging.getLogger(__name__)
    @classmethod
    def get_help(cls):
        '''one-line description for "dmx workspace check"'''
        myhelp = '''\
            Performs Gated Release checks on local workspace
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            The purpose of dmx workspace check is to help engineers prepare for a gated release.
            It runs all the same tests that a release would run, but does it in the user's 
            own IC Manage workspace.
            The tests must all succeed (and users have to submit everything to IC Manage)
            for the release to succeed.
            For a complete list of available milestone/thread, please refer to
            dmx roadmap command for an overview of the available roadmap for this project.
            If the deliverable option (-d) is not given, then it will run ip-level checks.
            If deliverable options is given, then it will run deliverable-level checks.
            
            For deliverable check, it will automatically read the tnrwaivers.csv file 
            if the waiver file exist (is checked in) inside its deliverable.
            eg: workspaceroot/ar_lib/rtl/tnrwaivers.csv will be used as the waiver file
            For  IP check, it will automatically read the tnrwaivers.csv waiver files
            from all deliverables of its IP.
            eg: workspaceroot/ar_lib/*/tnrwaivers.csv will be used as the waiver file
            
            From dmx/9.5 onwards, --bom/-b will no longer be needed. This is because workspace
            BOM should always be used when checking the content of workspace, instead of using
            the BOM provided by users. 
            If --bom/-b is provided, it will be ignored and workspace check will use the 
            workspace BOM instead.

            Usage
            =====
            %cd /your/ic/manage/workspace
            %dmx workspace check -m milestone -t thread -p project -i ip [-d deliverable]

            ### Run library-level gated release test on deliverable bcmrbc
            %dmx workspace check -p i10socfm -i cw_lib -m 1.0 -t FM8revA0 -d bcmrbc

            ### Run ip-level gated release test on the entire ip level
            %dmx workspace check -p i10socfm -i cw_lib -m 1.0 -t FM8revA0

            ### Run a prel-libtype check on libtype:sta and prel:prel_4
            %dmx workspace check ... -d prel_4:sta ...

            ### Run a prel-variant level check on prel:prel_4
            %dmx workspace check ... -d prel_4 ...

            Example
            =======
            If you plan to run:
            %dmx release -p i10socfm -i cw_lib -d rtl -m 1.0 -t FM8revA0

            then test it using:
            %dmx workspace check -p i10socfm -i cw_lib -d rtl -m 1.0 -t FM8revA0
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace check" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None) 
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom', metavar='bom')
        parser.add_argument('-m', '--milestone', metavar='milestone', required=False, default=None,
            help='Milestone to check against')
        parser.add_argument('-t', '--thread', metavar='thread', required=False, default=None,
            help='Thread to check against')
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False, default=None, nargs='+', 
            help='Deliverable(deliverable) to check. By default, test will run on ip-level.')
        parser.add_argument( '--logfile', required=False,
            help='Provide a logfile which logs all output to it.')
        parser.add_argument('--dashboard', choices=['prod', 'dev'],
            help='Log all test errors to the dashboard area.')
        parser.add_argument('--celllist-file', required=False, 
            help='Provides a way to only run dmx workspace check on a list of given cells, with celllist_file containing one topcell per line.')
        parser.add_argument('--nowarnings', required=False, action='store_true', default=False,
            help='Disable warnings. This will not print out the out-of-sync files in your workspace.')


        ### add switches to 'dmx workspace check' for turning off specific checks
        ### https://jira01.devtools.intel.com/browse/PSGDMX-1515
        parser.add_argument('--disable_type_check',     required=False, action='store_true', default=False,
            help='Any type-check error will not be reported.')
        parser.add_argument('--disable_checksum_check', required=False, action='store_true', default=False,
            help='Any "checksum" error will not be reported.')
        parser.add_argument('--disable_result_check', required=False, action='store_true', default=False,
            help='Any "result" error will not be reported.')
        parser.add_argument('--disable_deliverable_check', required=False, action='store_true', default=False,
            help='Any "deliverable existence" error will not be reported.')

        parser.add_argument('--source', choices=['proddb', 'devdb'], default='proddb',
            help='Force GoldenArc Check to user proddb/devdb. Default: proddb')
        parser.add_argument('--disable_goldenarc_check', required=False, action='store_true', default=False,
            help='Any GoldenArc Check error will not be reported.')
        

    @classmethod
    def command(cls, args):
        ret = 1

        project = args.project
        ip = args.ip
        bom = args.bom
        milestone = args.milestone
        thread = args.thread
        deliverable = args.deliverable
        logfile = args.logfile
        dashboard = args.dashboard
        celllist_file = args.celllist_file
        nowarnings = args.nowarnings

        waiver_file = []

        ### To support view feature.
        ### http://pg-rdjira.altera.com:8080/browse/DI-672
        views = []
        if not deliverable:
            libtype = None
            views = None
        elif len(deliverable) == 1:
            if deliverable[0].startswith("view_"):
                views = deliverable
                libtype = None
            else:
                views = None
                libtype = deliverable[0]
        else:
            ### if --deliverable has multiple values, then this should be only views.
            ### Mixture of views and libtype in --deliverable option is not allowed
            views = deliverable
            libtype = None

        ### views should have all prefixed with view_*
        if views:
            for v in views:
                if not v.startswith("view_"):
                    print("ERROR: Mixture of views and deliverables in --deliverable option is not allowed.")
                    print("       If multiple value is given, all of them should be views.")
                    return 1

        ### Remove this line once golden arc is ready for production !
        #args.disable_goldenarc_check = True

        ret = Workspace.check_action(project, ip, bom, milestone, thread, libtype, logfile, dashboard, celllist_file, nowarnings, waiver_file, views=views,
            validate_deliverable_existence_check=not args.disable_deliverable_check, validate_type_check=not args.disable_type_check, 
            validate_checksum_check=not args.disable_checksum_check, validate_result_check=not args.disable_result_check, validate_goldenarc_check=not args.disable_goldenarc_check,
            source=args.source)
        
        return ret
