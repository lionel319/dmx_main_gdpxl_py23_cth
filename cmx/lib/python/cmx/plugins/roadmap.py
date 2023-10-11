#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/roadmap.py#1 $
$Change: 7449885 $
$DateTime: 2023/01/19 00:28:35 $
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

from cmx.abnrlib.command import Command
from cmx.utillib.admin import is_admin
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

class Roadmap(Command):
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Returns information related to roadmap and TNR 
            (families, products, milestones, required deliverables, etc)
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        roadmap arguments
        '''
        add_common_args(parser)
        parser.add_argument('-f', '--family',
                            metavar='family', nargs='?', required=False)
        parser.add_argument('-p', '--project', nargs='?', const=True,
                            metavar='project', required=False)
        parser.add_argument('-i', '--ip', nargs='?', const=True,
                            metavar='ip', required=False)
        parser.add_argument('-t', '--type', dest='ip_type', nargs='?', const=True,
                            metavar='ip_type', required=False)
        parser.add_argument('-d', '--deliverable', nargs='?', const=True,
                            metavar='deliverable', required=False)
        parser.add_argument('--product', nargs='?', const=True,
                            metavar='product', required=False)
        parser.add_argument('--revision', nargs='?', const=True,
                            metavar='revision', required=False)
        parser.add_argument('-m', '--milestone', nargs='?', const='99',
                            metavar='milestone', required=False)
        parser.add_argument('--check', nargs='?', const=True,
                            metavar='check', required=False)
        parser.add_argument('--cell', nargs='?', const=True,
                            metavar='cell', required=False)
        parser.add_argument('--unneeded', action='store_true',
                            required=False)
        parser.add_argument('--view', nargs='?', const=True,
                            metavar='view', required=False)
        parser.add_argument('-b', '--bom',
                            metavar='bom', required=False,
                            help='BOM must be provided when --cell, --unneeded or --deliverable is provided. If ipspec bom is provided, follow this format: ipspec@bom. If IP bom is provided, follow this format: bom (--bom must be a bom of --ip)')
        parser.add_argument('--roadmap', nargs='?', const=True,
                            metavar='roadmap', required=False)
        parser.add_argument('--thread', required=False, default=False,
                            action='store_true', help="List out all the available threads for all families.")
                       
        '''
        # Disabled at the moment
        parser.add_argument('--flow', nargs='?', const=True,
                            required=False)
        parser.add_argument('--subflow', nargs='?', const=True,
                            required=False)
        parser.add_argument('--history', action='store_true',
                            required=False)          
        '''        
        # http://pg-rdjira.altera.com:8080/browse/DI-658
        # admin only option
        if is_admin():
            parser.add_argument('--testdata', action='store_true', 
                                help='Allow roadmap to return testdata registered in dmxdata')

    @classmethod
    def extra_help(cls):
        '''
        Detailed help for roadmap
        '''
        extra_help = '''\
        dmx roadmap returns the roadmap information defined by methodology and used in TNR

        dmx roadmap does not support option to write or modify the roadmap.

        Assumption:
        * If a milestone is not given, the milestone is assumed to be 99. 
            * 99 is the notation used by roadmap to mean full list.
        * When listing list of deliverables from an IP, --bom must be provided
            * If bom is provided, command will crawl the ip@bom and look for the ipspec
              bom
            * If ipspec@bom is provided, command will look into the ip:ipspec given
            * DMX will combine all unneeded deliverables from all *.unneeded_deliverables.txt
              found in the bom
            * The final list of required deliverables is the result of substraction of 
              unneeded deliverables from the full list of deliverables from roadmap

        Example
        =======
        $ dmx roadmap --thread
        Print out all available threads for all families.
        
        $ dmx roadmap --project i10socfm --type 
        Returns all ip-types associated with i10socfm

        $ dmx roadmap --project i10socfm --type asic
        Returns asic object together will all information encapsulated within the object

        $ dmx roadmap --family Falcon --product
        Returns all products of Falcon

        $ dmx roadmap --family Falcon --product FM8 --milestone
        Returns all milestones for Falcon/FM8
           
        $ dmx roadmap --family Falcon --product FM8 --type asic --deliverable
        Returns all deliverables associated with Falcon/asic/FM8.
        Will return the full list of deliverables (milestone==99)        

        $ dmx roadmap --family Falcon --product FM8 --type asic --milestone 4.0 --deliverable
        Returns all deliverables associated with Falcon/asic/FM8/4.0

        $ dmx roadmap --project i10socfm --ip cw_lib --product FM8 --deliverable --bom dev
        Returns all required deliverables for i10socfm/cw_lib/FM8revA0 based on what is delivered
        in ipspec found in dev IP@BOM
        DMX will filter away unneeded deliverables from *.unneeded_deliverables.txt
        The final output are deliverables that are required
        * Command will read the ipspec delivered in dev ip@bom to compute the list of unneeded deliverables. 
        ** The same applies to --cell if querying for cells

        $ dmx roadmap --project i10socfm --ip cw_lib --product FM8 --deliverable --bom ipspec@dev
        Returns all required deliverables for i10socfm/cw_lib/FM8revA0 based on what is delivered
        in dev IPSPEC BOM
        DMX will filter away unneeded deliverables from *.unneeded_deliverables.txt
        The final output are deliverables that are required
        * Command will read the ipspec delivered in dev bom to compute the list of unneeded deliverables. 
        ** The same applies to --cell if querying for cell

        $ dmx roadmap --project i10socfm --product FM8 --milestone 5.0 --check
        Returns all required checks associated with i10socfm/FM8/5.0

        $ dmx roadmap --project i10socfm --product FM8 --milestone 5.0 --deliverable rtl --check --ip cw_lib
        Returns all required checks for i10socfm/cw_lib:rtl for milestone 5.0 and product FM8
        *IP or IPType need to be provided when querying for information of deliverable
        *The independency of deliverable to IP or IPType is not available in this version yet.
        *Please check back with psgicmsupport@intel.com for more help
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

