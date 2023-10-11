#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/reportgraph.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx reportgraph"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import subprocess
import logging
import textwrap
import os

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.graphconfig import GraphConfig

class ReportGraphError(Exception): pass

class ReportGraph(Command):
    '''plugin for "dmx reportgraph"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help reportgraph"'''
        myhelp = '''\
            Generate a gif representation of a BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx reportgraph" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom',  metavar='src_bom', required=True)
        parser.add_argument('-f', '--file', metavar='file', required=True,
                            help='The name of the files to be generated. The .dot and .gif extensions will be automatically added')

    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help reportgraph'''
        extra_help = '''\
            Generates a graphical representation of a bom. 
            Produces two files  as output: <file>.dot and <file>.gif. 
            The .gif file is generated from the .dot file.    
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''the "dmx reportgraph" subcommand'''
        project = args.project
        ip = args.ip
        bom = args.bom
        file_name = args.file

        graph = GraphConfig(project, ip, bom, file_name)
        ret = graph.run()

        return ret
