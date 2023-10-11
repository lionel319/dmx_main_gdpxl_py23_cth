#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/overlay.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx roadmap
Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import sys
import logging
import textwrap
import getpass
import time
import re
import argparse

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.overlaydeliverable import OverlayDeliverable
from dmx.abnrlib.flows.overlayvariant import OverlayVariant

class Overlay(Command):
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Overlays a set of files from a source BOM to a destination BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        overlay arguments
        '''
        add_common_args(parser)
        #command_group = parser.add_mutually_exclusive_group()
        parser.add_argument('filespec',  metavar='file ...', nargs='*', help='File pattern to indicate files to overlay. Follows Perforce pattern convention.')
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        #parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)
        parser.add_argument('-sb', '--source-bom', metavar='source bom', required=False)
        parser.add_argument('-db', '--dest-bom', metavar='destination bom', required=False)
        parser.add_argument('-c', '--cells', metavar='cells', nargs='+', required=False)
        parser.add_argument('--directory', metavar='directory', required=False, 
            help = 'OPTIONAL. Directory to create workspace. Only use this option if the scratch disk for the project is not available.')
        parser.add_argument('--desc', required=False, default='',
            help='Description. No double-quotes allowed in the description.')

        ### Options for multiple-deliverables(veriant) overlay
        parser.add_argument('-df', '--deliverable-filter', nargs='+', required=False)
        parser.add_argument('--hier', default=False, action='store_true')
        parser.add_argument('--wait', required=False, default=False, action='store_true',
            help='Will return prompt only after all jobs are completed.')
         
        ### Hidden options. For ADMINS usage only.
        parser.add_argument('--forcerevert', required=False, default=False, action='store_true', help=argparse.SUPPRESS)

        ### --shared-wsroot. https://jira.devtools.intel.com/browse/PSGDMX-2843
        parser.add_argument('--shared-wsroot', '-swr', required=False, default=None, help="""A workspaceroot fullpath to a workspace which can be used as the staging workspace for overlay.
            When this option is used, dmx overlay will not create a temporary staging worksapce anymore.
            dmx overlay will also not cleanup this workspace when overlay job has completed.
            This option is only applicable when --source-bom and --dest-bom are both provided.
            This option only works with single-libtype-level-overlay. This means that if the
            overlay command needs to overlay more than 1 libtype, it will ignore this option.
            """)


    @classmethod
    def extra_help(cls):
        '''
        Detailed help for roadmap
        '''
        extra_help = '''\
        dmx overlay has 2 modes of operation.
        * Overlay source BOM to destination BOM
        * Overlay workspace to repository

        Overlay source BOM to destination BOM
        =================================================================
        dmx overlay will copy files for a deliverable a source BOM to a destination BOM.

        Overlay works by first removing every file from the destination BOM's library, then 
        copying every file from source BOM's library to destination BOM's library.
        Overlay supports deliverable, slice and cell overlay mode:
        * Deliverable overlay (when deliverable is given and --cells not given)
          Every file within ip/deliverable/... will be overlaid regardless of patterns/filelists
          defined in manifest
        * Slice overlay (when slice is given and --cells not given)
          Files corresponding to patterns/filelists defined in manifest for the slice will be overlaid
        * Cell overlay (when slice or deliverable is given and --cells given)
          Only files for the given cells that correspond to patterns/filelists defined in manifest 
          for the slice/deliverable will be overlaid

        Slice is a new object introduced for the purpose of overlay. 
        Slice will follow this naming convention: <deliverable>:<slice>
        A slice will have it's own patterns/filelists defined.
        Examples of slice: oa:sch, oa:lay, etc

        --cells argument supports a list of cells or a single filelist that contains a list of cells
        Filelist must be of .txt extension and cells must be separated by lines. 
        Filelist follows ipspec/cell_names.txt. 
        Lines that begin with # or // will be treated as comments.

        Source library and destination library must be different. 

        As of dmx/8.1, overlay arguments have been revamped:
        * -i IP -d DELIVERABLE --source-bom BOM1 --dest-bom BOM2
            * Overlays DELIVERABLE from IP@BOM1 to IP@BOM2
            * BOM1 and BOM2 are expected to be ICManage variant configuration
            * DMX will automatically look for the ICManage libtype configurations to overlay
        * -i IP:DELIVERABLE --source-bom BOM1 --dest-bom BOM2
            * Overlays DELIVERABLE from IP:DELIVERABLE@BOM1 to IP:DELIVERABLE@BOM2
            * BOM1 and BOM2 are expected to be ICManage libtype configuration
        With slice:
        * -i IP -d DELIVERABLE:SLICE --source-bom BOM1 --dest-bom BOM2
            * Overlays DELIVERABLE:SLICE from IP@BOM1 to IP@BOM2
            * BOM1 and BOM2 are expected to be ICManage variant configuration
            * DMX will automatically look for the ICManage libtype configurations to overlay
        * -i IP:DELIVERABLE -d SLICE --source-bom BOM1 --dest-bom BOM2
            * Overlays DELIVERABLE:SLICE from IP:DELIVERABLE@BOM1 to IP:DELIVERABLE@BOM2
            * BOM1 and BOM2 are expected to be ICManage libtype configuration              

        Overlay workspace to repository
        =================================================================
        dmx overlay will copy files from the workspace to the corresponding library in the repository

        There are 2 modes of overlay for different deliverable type:
        * Large Data deliverable (such as rcxt)
        ** Removes every file from the repository
        ** Check in every file in the workspace to the repository
        * Normal deliverable 
        ** Reconciles changes in the workspace
        ** Check in only changes to repository

        Note:
        - this mode only works on the --deliverable/-d option.
        =================================================================


        ---------------------------------------------------------
        Overlay Single Deliverable
        ---------------------------------------------------------
        Example
        =======
        $ dmx overlay --project i10socfm --ip cw_lib -d oa --source-bom dev --dest-bom dev2
        Overlays all files in oa from i10socfm/cw_lib@dev to i10socfm/cw_lib@dev2

        $ dmx overlay --project i10socfm --ip cw_lib -d oa --source-bom dev --dest-bom dev2 --cells cell01
        Overlays only cell01 files in oa from i10socfm/cw_lib@dev to i10socfm/cw_lib@dev2

        $ dmx overlay --project i10socfm --ip cw_lib -d oa --source-bom dev --dest-bom dev2 --cells cell01 cell02
        Overlays only cell01 and cell02 files in oa from i10socfm/cw_lib@dev to i10socfm/cw_lib@dev2

        $ dmx overlay --project i10socfm --ip cw_lib:oa --source-bom dev --dest-bom dev2
        Overlays all files in oa from i10socfm/cw_lib:oa@dev to i10socfm/cw_lib:oa@dev2

        $ dmx overlay --project i10socfm --ip cw_lib -d oa:sch --source-bom dev --dest-bom dev2
        Overlays all files defined for slice oa:sch from i10socfm/cw_lib@dev to i10socfm/cw_lib@dev2

        $ dmx overlay --project i10socfm --ip cw_lib:oa -d sch --source-bom dev --dest-bom dev2
        Overlays all files defined for slice oa:sch from i10socfm/cw_lib:oa@dev to i10socfm/cw_lib:oa@dev2

         $ dmx overlay --project i10socfm --ip cw_lib -d oa --dest-bom dev
        Overlays all files defined for cw_lib:oa in the workspace to i10socfm/cw_lib:oa@dev
         
         $ dmx overlay --project i10socfm --ip cw_lib -d oa 
        Overlays all files defined for cw_lib:oa in the workspace to the bom of i10socfm/cw_lib:oa in this local workspace. 
        The local workspace will be used as the staging area.
        
        
        
        ---------------------------------------------------------
        Overlay Multiple(variant) Deliverables
        ---------------------------------------------------------
        $ dmx overlay -p i10socfm -i cw_lib --deliverable-filter oa ipspec -sb dev -db dev2
        Overlays all files from 
            - cw_lib@dev's oa     into cw_lib:oa@dev2
            - cw_lib@dev's ipspec into cw_lib:ipspec@dev2

        $ dmx overlay -p i10socfm -i cw_lib --deliverable-filter oa ipspec -sb dev -db dev2 --hier
        Overlays all files from 
            - all oa     libtypes under cw_lib@dev tree into <respective-ip>:oa@dev2
            - all ipspec libtypes under cw_lib@dev tree into <respective-ip>:ipspec@dev2
        
        $ dmx overlay -p i10socfm -i cw_lib -sb dev -db dev2
        Overlays all files from
            - cw_lib@dev's all libtypes into cw_lib:<all-libtypes>@dev2

        $ dmx overlay -p i10socfm -i cw_lib -sb dev -db dev2 --hier
        Overlays all files from
            - all libtypes under cw_lib@dev's tree into their <respective-ip>:<respective-libtype>@dev2
        
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the subcommand
        '''
        filespec = args.filespec
        project = args.project
        ip = args.ip
        deliverable = args.deliverable
        source_bom = args.source_bom
        dest_bom = args.dest_bom
        cells = args.cells
        directory = args.directory
        preview = args.preview
        desc = args.desc
        wait = args.wait
        forcerevert = args.forcerevert

        shared_wsroot = args.shared_wsroot

        ### multi-deliverable(Variant) overlay options
        deliverable_filter = args.deliverable_filter
        hier = args.hier
        ret = 1

        ## Do not allow --deliverable and filespec together as it might have conflict
        if (deliverable and filespec) or  (deliverable_filter and filespec) or (":" in ip and filespec):
            raise Exception('--deliverable/--deliverable_filter cannot be used with filespec')

        ### variant (milti-deliverable) overlay
        if hier or deliverable_filter or (not deliverable and ":" not in ip):
            overlay = OverlayVariant(project, ip, source_bom, dest_bom, deliverables=deliverable_filter, hier=hier, cells=cells, directory=args.directory, preview=preview, desc=desc, wait=wait, forcerevert=forcerevert, filespec=filespec)
        else:
            overlay = OverlayDeliverable(project, ip, deliverable, source_bom, dest_bom, cells=cells, directory=args.directory, preview=preview, desc=desc, forcerevert=forcerevert, shared_wsroot=shared_wsroot, filespec=filespec)
        ret = overlay.run()

        return (ret)
