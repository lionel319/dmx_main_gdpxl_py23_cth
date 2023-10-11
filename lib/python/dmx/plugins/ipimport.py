#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/ipimport.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
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

from dmx.abnrlib.flows.ip import IP
from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
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
        '''
        Execute the "import" subcommand
        '''
        ip = IP()
        if args.list:
            if args.project or args.ip or args.dest_bom or args.deliverables or args.format:
                raise IpImportError('-l|--list cannot use with other options.')
            return ip.get_all_format_name()

        else:
            if not args.project:
                raise IpImportError('-p|--project is required')
            if not args.ip:
                raise IpImportError('-i|--ip is required')
            if not args.deliverables:
                raise IpImportError('-d|--deliverables is required')
            if not args.format:
                raise IpImportError('-f|--format is required')
            
            ip.migrate_to_dmx(
                args.project,
                args.ip,
                args.deliverables,
                args.format,
                args.source_bom,
                args.dest_bom
            )

if __name__ == '__main__':
    IpImport.command(IpImport.add_args(argparse.ArgumentParser()))
