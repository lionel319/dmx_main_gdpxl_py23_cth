#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/ipunpackage.py#1 $
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
        '''
        Execute the "import" subcommand
        '''
        ip = IP()
        ip.unpackage(args.project, args.ip, args.cell, args.bom, args.stage)

        return

if __name__ == '__main__':
    IpImport.command(IpImport.add_args(argparse.ArgumentParser()))
