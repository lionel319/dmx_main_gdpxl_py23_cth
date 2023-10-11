#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/bomparents.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: bom parent dmx subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2013
All rights reserved.
'''

import sys
import logging
import textwrap
import itertools
import os

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.parentsbom import ParentsBom

class BomParentsError(Exception): pass

class BomParents(Command):
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Get parents for given bom
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        bom parents arguments
        '''
        add_common_args(parser)
        parser.add_argument('-p', '--project',
                            metavar='project', required=False, default=None,
                            help='The name of the project')
        parser.add_argument('-i', '--ip',
                            metavar='IP', required=True,
                            help='The name of the ip')
        parser.add_argument('-b', '--bom',
                            metavar='bom', required=True,
                            help='The name of the bom')
        parser.add_argument('-d', '--deliverable',
                            metavar='deliverable', required=False, default=None,
                            help='The name of the deliverable')
        parser.add_argument('--report-all', action='store_true',
                            required=False,
                            help='report all parents ')
        parser.add_argument('--hierarchy', action='store_true',
                            required=False,
                            help='report parents in full hierarchy.')

    @classmethod
    def extra_help(cls):
        '''
        Detailed help for bom parents 
        '''
        extra_help = '''\
        "bom parents" return all the parent associated to the given bom

        Example
        =======
        $dmx bom parents -p i10socfm -i liotest1 -b dev
        Report all parents that has child i10socfm/liotest1@dev

        $dmx bom parents -p i10socfm -i liotest1 -b dev --report-all
        Report all parents that has child i10socfm/liotest1@dev including tnr-placeholder*
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the subcommand
        '''
        bom = args.bom
        project = args.project
        ip = args.ip
        deliverable = args.deliverable
        reportall = args.report_all
        hierarchy = args.hierarchy

        ret = ParentsBom(project, ip, bom, deliverable, reportall, hierarchy).run()

        return ret
