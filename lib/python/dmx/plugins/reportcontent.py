#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/reportcontent.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "report content" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
import sys
import logging
import textwrap
import csv
import argparse

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.printconfig import PrintConfig
from dmx.abnrlib.flows.bomdetail import BomDetail
from dmx.abnrlib.flows.file_print import Print

class ReportContentError(Exception): pass

class ReportContent(Command):
    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Print the contents of a BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help report content
        '''
        extra_help = '''\
            Report content will print the content of a BOM

            --verbose will print the Perforce path changes for the given BOM
            --file will print the content of the file in the given BOM
            --quiet can be used with --file. 
              Quiet switch suppresses printing the initial 2 lines that display
              the icmp4 command and the file name and revision

            Example
            =======
            $ dmx report content -p i10socfm -i cw_lib -b dev
            Prints content of i10socfm/cw_lib@dev including deliverables
            
            $ dmx report content -p i10socfm -i cw_lib -b dev -d rtl
            Prints content of i10socfm/cw_lib:rtl@dev 
    
            $ dmx report content -p i10socfm -i cw_lib -b dev --hier
            Prints content of i10socfm/cw_lib@dev hierarchically (IPs and deliverables)
    
            $ dmx report content -p i10socfm -i cw_lib -b dev --no-deliverables
            Prints content of i10socfm/cw_lib@dev (only IPs)
    
            $ dmx report content -p i10socfm -i cw_lib -b dev --hier --no-deliverables
            Prints content of i10socfm/cw_lib@dev hierarchically (only IPs) 
    
            $ dmx report content -p i10socfm -i cw_lib -b dev --csv test.csv
            Output results to test.csv

            $ dmx report content -p i10socfm -i cw_lib -b dev --json test.json
            Output results to test.json

            $ dmx report content -p i10socfm -i cw_lib -b dev -d rtl --verbose
            Prints list of Perforce path changes for i10socfm/cw_lib:rtl@dev 

            $dmx report content -p Falcon_Mesa -i z1574b -b dev -f cw_lib/ipspec/cell_names.txt 
            Prints content of cell_names.txt found in cw_lib:ipspec under Falcon_Mesa/z1574b@dev hierarchy.
            
            $dmx report content -p Falcon_Mesa -i z1574b -b dev -d ipspec -f z1574b/ipspec/cell_names.txt 
            Prints content of cell_names.txt found in Falcon_Mesa/z1574b/ipspec/cell_names.txt .
            
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx clonehier" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)
        parser.add_argument('-b', '--bom',  metavar='src_bom', required=True)
        parser.add_argument('--no-deliverables', required=False, action='store_false',
                            dest='show_simple', help='Displays only IP BOMs')
        parser.add_argument('--hier', action='store_false', dest='nohier', 
                            help="Display the BOMs hierachically, including all sub-BOMs")
        parser.add_argument('--csv', required=False,
                            help='Format output as CSV and write it to the specified file.')
        parser.add_argument('--json', required=False,
                            help='Format output as JSON and write it to the specified file.')
        parser.add_argument('--flat', required=False,
                            help='Format output as PRISM flatten and write it to the specified file.')

        parser.add_argument('--ip-filter', nargs='+', help="Returns only BOMs for the IPs listed in the filter") 
        parser.add_argument('--deliverable-filter', nargs='+', help="Returns only BOMs for the deliverables listed in the filter") 
        group = parser.add_mutually_exclusive_group()        
        group.add_argument('--verbose', action='store_true', help="List changes using perforce //depot/... paths") 
        group.add_argument('-f', '--file',  metavar='proj/ip/deliverable/library/path-inside-library', help='Show the current contents of a file in a configuration')
        

        ### To maintain backward compatibility, 
        ### we need to maintain --nohier and --all options
        ### These options does nothing, since they are already the default behavior.
        ### They are here just to prevent the command from error-out if user provides these options.
        ### http://pg-rdjira:8080/browse/DI-1367
        parser.add_argument('--nohier', action='store_true', help=argparse.SUPPRESS, dest='backward1')
        parser.add_argument('--all',    action='store_true', help=argparse.SUPPRESS, dest='backward2')


    @classmethod
    def command(cls, args):
        '''the "report content" subcommand'''
        project = args.project
        ip = args.ip
        deliverable = args.deliverable
        bom = args.bom
        show_simple = args.show_simple
        nohier = args.nohier
        verbose = args.verbose
        csv = args.csv
        json = args.json
        file = args.file
        quiet = args.quiet
        deliverable_filter = args.deliverable_filter
        ip_filter = args.ip_filter
        flat = args.flat

        if verbose:
            # Make it simpler for users, we always show perforce path and don't show them relpath
            # Users have no neeed to know relpath
            # Accepts only single deliverable to be in line with deliverable argument definition
            runner = BomDetail(project, ip, bom, p4=True, libtypes=deliverable_filter if deliverable_filter else None, relpath=False, libtype=deliverable)
        elif file:
            runner = Print(project, ip, bom, file, quiet, libtype=deliverable)
        else:
            runner = PrintConfig(project, ip, bom, show_simple=show_simple,
                                 nohier=nohier, csv=csv, libtype=deliverable,
                                 variant_filter=ip_filter, libtype_filter=deliverable_filter, json=json, flat=flat)

        return (runner.run())

