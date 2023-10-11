#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/bomcreate.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: bom create dmx subcommand
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
from dmx.abnrlib.flows.createconfig import CreateConfig

class BomCreateError(Exception): pass

class BomCreate(Command):
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Create a new BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        bom create arguments
        '''
        add_common_args(parser)
        parser.add_argument('-p', '--project',
                            metavar='project', required=False, default=None,
                            help='The project within which to create the new bom')
        parser.add_argument('-i', '--ip',
                            metavar='IP', required=True,
                            help='The ip within which to create the new bom')
        parser.add_argument('-b', '--bom',
                            metavar='bom', required=True,
                            help='The name of the new bom you want to create')
        parser.add_argument('--desc',
                            metavar='description', required=False,
                            help='The bom description')
        parser.add_argument('--include',
                            metavar='include', required=False,
                            action='append', nargs='+',
                            help='The list of sub-boms to include in the new bom')
        parser.add_argument('-f', '--file',
                            metavar='file', required=False,
                            help='A file that lists which boms you want to include in the new bom')
        parser.add_argument('--include-syncpoint',
                            metavar='syncpoint', required=False,
                            action='append', nargs='+',
                            help='The list of syncpoints whose boms will be included in the new bom')
        parser.add_argument('--include-syncpoint-config',
                            metavar='syncpoint_config', required=False,
                            action='append', nargs='+',
                            help="A list of specific project/ips whose boms you'd like to inlcude, based upon a syncpoint")

    @classmethod
    def extra_help(cls):
        '''
        Detailed help for bom create
        '''
        extra_help = '''\
        "bom create" builds a new bom containing the components
        specified on the command line.

        A bom named <new_bom_name> will be built in <project>/<ip>.

        The contents of the bom can be specified using the include 
        argument or a file.

        The include argument can either be specified multiple
        times or a single time. If specified a single time the contents
        list must be space delimited.

        The include option expects input in the following format:
        --include <project>/<ip>[:<deliverable>]@<bom>

        If using a file it must be a text file that lists one bom per line.
        The boms follow the same format as for the --include argument:
        <project>/<ip>[:deliverable>]@<bom>

        Any line that begins with # is treated as a comment and ignored

        There are two options available for using syncpoints when building a bom.
        You can either include all boms associated with a syncpoint name,
        or include boms for specified project/ip associated with a syncpoint.

        If you want to include all boms associated with a syncpoint just specify
        the syncpoint name. The --include-syncpoint option can be specified multiple 
        times or a single time with a space delimited list of syncpoint names.

        If specifying specific boms by syncpoint they must be specified in the
        following format: <project>/<ip>@<syncpoint>.
        The --include-syncpoint-config option can be specified multiple times or a 
        single time with a space separated list of project/ip@syncpoint.

        Example
        =======
        $dmx bom create -p i10socfm -i cw_lib -b testing --include i10socfm/cw_lib:rtl@dev 
        Create BOM i10socfm/cw_lib@testing which references i10socfm/cw_lib:rtl@dev

        $dmx bom create -p i10socfm -i cw_lib -b testing --include i10socfm/cw_lib:rtl@dev --include i10socfm/ce_lib@dev      
        Create BOM i10socfm/cw_lib@testing which references i10socfm/cw_lib:rtl@dev and i10socfm/ce_lib@dev

        NOTE: You cannot reference a deliverable BOM outside of the IP of the BOM being created. 
              For example, this is not allowed:
              dmx bom create -p i10socfm -i cw_lib -b testing --include i10socfm/cw_lib:rtl@dev --include i10socfm/ce_lib:rtl@dev  

              This is allowed:
              dmx bom create -p i10socfm -i cw_lib -b testing --include i10socfm/cw_lib:rtl@dev --include i10socfm/ce_lib@dev  
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the subcommand
        '''
        new_bom = args.bom
        project = args.project
        ip = args.ip
        description = args.desc
        # Flatten the list of sub-includes
        if args.include:
            cmdline_includes = list(itertools.chain.from_iterable(args.include))
        else:
            cmdline_includes = []
        preview = args.preview
        bom_file = args.file
        # Flatten the list of syncpoints
        if args.include_syncpoint:
            syncpoints = list(itertools.chain.from_iterable(args.include_syncpoint))
        else:
            syncpoints = []
        # Flatten the list ofsyncpoint boms
        if args.include_syncpoint_config:
            syncpoint_configs = list(itertools.chain.from_iterable(args.include_syncpoint_config))
        else:
            syncpoint_configs = []


        ret = 1
        create = CreateConfig(project, ip, new_bom,
                              cmdline_includes, bom_file,
                              description, 
                              syncpoints=syncpoints,
                              syncpoint_configs=syncpoint_configs,
                              preview=preview)

        ret = create.run()

        return ret
