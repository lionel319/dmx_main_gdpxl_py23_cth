#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/ipunpackage.py#1 $
$Change: 7486383 $
$DateTime: 2023/02/16 01:56:06 $
$Author: lionelta $

Description: dmx "ip import" subcommand plugin

Author: Mitchell Conkin
Copyright (c) Intel Corporation 2019
All rights reserved.
'''
import sys
import logging
import textwrap
import argparse

from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 
logger = logging.getLogger()

class IpUnpackageError(Exception): pass

class IpUnpackage(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        short help for the subcommand
        '''
        myhelp = '''\
            Unpackage a 3rd party IP outside of DMX
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        create source --> destination arguments
        '''
        add_common_args(parser) # TODO add
        parser.add_argument('-p', '--project', metavar='project', required=True)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-c', '--cell', metavar='cell', required=False)
        parser.add_argument('-s', '--stage', metavar='stage', required=False)
        parser.add_argument('-b', '--bom', metavar='bom', required=True)

    @classmethod
    def extra_help(cls):
        '''
        detailed help for ip import 
        '''

        extra_help = '''\
            "ip unpackage" unpackages a 3rd party IP outside of DMX into Cheetah2. 

            --project <project>     The ICM project where the IP resides.
            --ip <ip>               The name of the IP found in ICM.
            --bom <bom>        The BOM in PSG where the data will be cloned into.
            '''

        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)

