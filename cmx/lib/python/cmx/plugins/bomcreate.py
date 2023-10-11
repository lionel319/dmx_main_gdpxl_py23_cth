#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/bomcreate.py#1 $
$Change: 7463577 $
$DateTime: 2023/01/31 01:08:26 $
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

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

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
        return dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

