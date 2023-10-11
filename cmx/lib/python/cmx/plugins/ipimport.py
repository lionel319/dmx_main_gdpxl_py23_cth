#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/ipimport.py#1 $
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

class IpImportError(Exception): pass

class IpImport(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        short help for the subcommand
        '''
        myhelp = '''\
            Import a 3rd party IP into the DMX system
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        create source --> destination arguments
        '''
        add_common_args(parser) # TODO add
        lister = parser.add_argument_group('list', 'lists avaliable format names')
        lister.add_argument('-l', '--list', action='store_true', required=False, help='list all the available format name')
        
        mainargs = parser.add_argument_group('import', 'runs the import operation') 
        mainargs.add_argument('-p', '--project', metavar='project', required=False)
        mainargs.add_argument('-i', '--ip', metavar='ip', required=False)
        mainargs.add_argument('-d', '--deliverables', metavar='deliverables', nargs='*')
        mainargs.add_argument('-f', '--format', metavar='format', required=False)
        mainargs.add_argument('--source-bom', metavar='source_bom', required=False)
        mainargs.add_argument('--dest-bom', metavar='dest_bom', required=False)

    @classmethod
    def extra_help(cls):
        '''
        detailed help for ip import 
        '''

        extra_help = '''\
            "ip import" migrates a 3rd party IP into DMX. 

            --project <project>
            --ip <ip>
            --deliverables <deliverable-1, deliverable-2, ...>
            --format <ip-format>
            --source-bom <bom>
            --dest-bom <bom>

            Example
            =======
            List all the available format name in dmx ip import.(-l|-list cannot used together with other argument)
            $ dmx ip import -l
    
            '''

        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
