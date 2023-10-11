#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/reportdiff.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: "report diff" plugin for abnr
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import os
import logging
import textwrap

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.diffconfigs import DiffConfigs

class ReportDiff(Command):
    '''dmx subcommand plugin class"'''

    @classmethod
    def get_help(cls):
        '''short subcommand description'''
        myhelp = '''\
            Compare and display differences between 2 BOMs
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''subcommand arguments'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom1',  metavar='bom1',  required=True)
        parser.add_argument('-p2', '--project2', metavar='project2', required=False)
        parser.add_argument('-i2', '--ip2', metavar='ip2', required=False)
        parser.add_argument('-b2', '--bom2',  metavar='bom2',  required=True)
        parser.add_argument('-d', '--deliverable',  metavar='deliverable',  required=False)
        parser.add_argument('--tkdiff',  action='store_true', help="show differences with tkdiff")
        parser.add_argument('--include-files', action='store_true', help="show files' differences") 
        parser.add_argument('--html', action='store_true', 
                            help="show differences with html, run together --include-files switch.")
        parser.add_argument('--sort-by-deliverables', action='store_true', 
                            help="sort report diff output by deliverables instead of ips. Diffboms be default sort output by ips.") 
        parser.add_argument('--filter-ips', nargs='*',
                            help="filter away unneeded ips from results output. Diffboms will only display provided ips in this argument.") 
        parser.add_argument('--filter-deliverables', nargs='*',
                            help="filter away unneeded deliverables from results output. Diffboms will only display provided deliverables in this argument.") 
        ''' No Longer Applicable as we don't have libtype-configs anymore
        parser.add_argument('--ignore-bom-names', action='store_true', required=False,
                            help='Ignore bom names when determining if two boms differ.')
        '''

    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help report diff'''
        extra_help = '''\
            "report diff" compares two bom and displays the differences. 
            Note that 2 BOMs can show up as different even when they contain the same data. 
            This command compares the names of the BOMs, not the contents.

            The --ignore-bom-names flag can be used to make report diff ignore the bom names 
            and only compare at the release name level.

            "report diff" will only compare two bom of the same ip specified with 
            "-p/--project", "-i/--ip", "-b/--bom1", and "--bom2"
            
            The default behavior is to show the differences to stdout, unless the "--tkdiff"
            option is used - in which case it displays the differences using tkdiff.

            If --html is provided, results are shown in a browser popup.

            --sort-by-deliverables, --filter-ips and --filter-deliverables provide options 
            to customize the output returned.

            Example
            =======
            $ dmx report diff -p project1 -i zz1 --bom1 dev --bom2 foobar
            # Project/Variant/Libtype Library/Release/Configuration
            - project1/zz1/irem     zz1/#ActiveDev/dev   
            ! project1/zz1/rtl      zz1/#ActiveDev/dev    => zz1/#ActiveRel/foobar
            ! project1/zz1/vpd      zz1/#ActiveDev/dev    => zz1/#ActiveDev/foobar
            - project1/zz2/irem     zz2/#ActiveDev/dev   
            - project1/zz2/rtl      zz2/#ActiveDev/dev   
            - project1/zz2/vpd      zz2/#ActiveDev/dev   
            - project1/zz3/irem     zz3/#ActiveDev/dev   
            - project1/zz3/rtl      zz3/#ActiveDev/dev   
            - project1/zz3/vpd      zz3/#ActiveDev/dev   
            - project1/zz4/irem     zz4/#ActiveDev/dev   
            ! project1/zz4/oa       zz4/#ActiveDev/dev    => zz4/OLDREL2/foobar   
            - project1/zz4/rtl      zz4/#ActiveDev/dev   
            - project1/zz4/spyglass zz4/#ActiveDev/dev   
            - project1/zz4/vpd      zz4/#ActiveDev/dev   
            - project1/zz5/oa       zz5/#ActiveDev/dev   
            - project1/zz5/rtl      zz5/#ActiveDev/dev   

            * lines marked with "-" are only in bom1
            * lines marked with "+" are only in bom2
            * lines marked with "!" are different in the two boms and both are shown


            Known Problems:
            ===============
            (1) for LDD (Large Data Deliverables), only the simplest option works. The --tkdiff/--html options will not work.
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''execute the subcommand'''
        project = args.project
        ip = args.ip
        bom1  = args.bom1
        project2 = args.project2
        ip2 = args.ip2
        bom2  = args.bom2
        deliverable  = args.deliverable
        use_tkdiff = args.tkdiff
        ignore_bom_names = False
        include_files = args.include_files
        html = args.html
        sort_by_deliverables = args.sort_by_deliverables
        filter_ips = args.filter_ips
        filter_deliverables = args.filter_deliverables
        preview = args.preview        
    
        diff = DiffConfigs(project, ip, bom1, bom2, 
                                   project2, ip2, use_tkdiff,
                                   ignore_bom_names, include_files, html, 
                                   sort_by_deliverables, 
                                   filter_ips, filter_deliverables,
                                   preview, deliverable)
        return diff.run()
