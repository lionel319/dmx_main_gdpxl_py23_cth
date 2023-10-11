#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/ippackage.py#1 $
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

class IpPackageError(Exception): pass

class IpPackage(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        short help for the subcommand
        '''
        myhelp = '''\
            Package a 3rd party IP into the DMX
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        create source --> destination arguments
        '''
        add_common_args(parser) # TODO add
        lister = parser.add_argument_group('list', 'lists avaliable formats')
        lister.add_argument('-l', '--list', action='store_true', required=False, help='list all the available formats')
    
        mainargs = parser.add_argument_group('package', 'runs the package operation')
        mainargs.add_argument('-p', '--project', metavar='project', required=False)
        mainargs.add_argument('-i', '--ip', metavar='ip', required=False)
        mainargs.add_argument('-b', '--bom', metavar='bom', required=False)
        mainargs.add_argument('-f', '--format', metavar='format', required=False)

    @classmethod
    def extra_help(cls):
        '''
        detailed help for ip import 
        '''

        extra_help = '''\
            "ip package" packages a 3rd party IP into DMX for release purposes. 

            --project <project>     The ICM project where the IP resides.
            --ip <ip>               The name of the IP found in ICM.
            --bom <bom>             The BOM in PSG where the data will be cloned into.
            --format <format>         The format which the archiver will archive to.
            '''

        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the "package" subcommand
        '''
        ip = IP()
        if args.list:
            if args.project or args.ip or args.bom or args.format:
                raise IpImportError('-l|--list cannot use with other options.')
            return ip.get_all_stage_name()

        else:
            if not args.project:
                raise IpImportError('-p|--project is required')
            if not args.ip:
                raise IpImportError('-i|--ip is required')
            if not args.bom:
                raise IpImportError('-b|--bom is required')
            if not args.format:
                raise IpImportError('-f|--format is required')

        ip.package_for_release(args.project, args.ip, args.bom, args.format)

        return

if __name__ == '__main__':
    IpImport.command(IpImport.add_args(argparse.ArgumentParser()))
