#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/bomlatest.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx bomlatest subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import sys
import logging
import textwrap
import re
import os

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.latestconfig import LatestConfig

class BomLatestError(Exception): pass

class BomLatest(Command):
    '''
    The dmx bomlatest command

    Identifies the latest bom created for a project/ip
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Identify the latest BOM created for a project/ip(or deliverable)
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        bomlatest arguments
        '''
        add_common_args(parser)
        parser.add_argument('-p', '--project',
                            metavar='project', required=False,
                            default=None,
                            help='Project')
        parser.add_argument('-i', '--ip',
                            metavar='ip', required=True,
                            help='IP')
        parser.add_argument('-b', '--bom',
                            metavar='bom', required=True,
                            help='BOM pattern to search for')
        parser.add_argument('-d', '--deliverable',
                            metavar='deliverable', required=False,
                            default=None,
                            help='Deliverable. Only required when searching for deliverable')
        parser.add_argument('--limit',
                            metavar='limit', required=False, default='-1',
                            help='Only prints the latest boms of the given limit. If only the last latest bom is needed, then use --limit 1')
        parser.add_argument('--pedantic',
                            required=False, default=False, action='store_true',
                            help='By default, reports all matched boms. Turning on this option will only reports well-formed released boms.')

    @classmethod
    def extra_help(cls):
        '''
        Detailed help for latest
        '''
        extra_help = '''\
        List the latest bom for a project/ip [deliverable]

        The --bom argument should be a regular expression.

        Example
        =======
        $dmx bom latest -p i10socfm -i cw_lib -b 'REL' --pedantic
        Report all latest released boms for cw_lib, having REL as sub-string
        
        $dmx bom latest -p i10socfm -i cw_lib -b 'REL'
        Report all latest boms for cw_lib (including non-released ones), 
        having REL as sub-string,

        $dmx bom latest -p i10socfm -i cw_lib -b 'REL.+FM8revA0' --pedantic
        Report all latest released boms for cw_lib for thread(FM8revA0) only

        $dmx bom latest -p i10socfm -i cw_lib -b 'REL2.0FM8revA0' --pedantic
        Report all latest released boms for cw_lib for thread(FM8revA0) and 
        milestone(4.5) only

        $dmx bom latest -p i10socfm -i cw_lib -b 'REL' --limit 1 --pedantic
        Report latest released valid well-formed bom for cw_lib

        $dmx bom latest -p i10socfm -i cw_lib -b 'REL' -d ipspec --limit 1 --pedantic
        Report the latest Released valid well-formed bom for IPSPEC deliverable 
        for cw_lib

        $dmx bom latest -p i10socfm -i cw_lib -b 'REL' -d ipspec
        Report all latest boms for IPSPEC for cw_lib, for every thread, having 
        'REL' as sub-string
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the subcommand
        '''
        project = args.project
        ip = args.ip
        bom = args.bom
        deliverable = args.deliverable
        pedantic = args.pedantic
        limit = int(args.limit)

        ret = 1
        latest = LatestConfig(project, ip, bom, libtype=deliverable, pedantic=pedantic, limit=limit)
        ret = latest.run()

        return (ret)
