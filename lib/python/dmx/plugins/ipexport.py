#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/ipexport.py#1 $
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
import dmx.abnrlib.flows.ipexport
logger = logging.getLogger()

class IpExportError(Exception): pass
class IpExport(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        short help for the subcommand
        '''
        myhelp = '''\
            Export a PSG IP from DMX to Cheetah2 system
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        detailed help for ip export
        '''

        extra_help = '''\
        Export a IP from DMX to Cheetah2 environement 

        This command does the following:-
            1. Creates a temporary workspace with given project:ip@bom
            2. syncs the files(filter deliverable if --deliverables is given)
            3. Run the mapping and generator file store in DMXDATA
            4. Remove temmporary workspace

        Note: 
        You need to be in 'topsg' environment to run this commabnd.

        Example
        =======
        List all the available format name in dmx ip export.(-l|-list cannot used together with other argument) 
        $ dmx ip export -l 

        Export da_n5/iocenter_lib@dev cvrtl_constraint mapping from PSG to Cheetah
        $ dmx ip export -p da__n5 -i iocenter_lib -b dev -f cvrtl

        Export da_n5/iocenter_lib@dev cvrtl_constraint mapping from PSG to Cheetah, only rtl deliverable is exported
        $ dmx ip export -p da__n5 -i iocenter_lib -b dev -f cvrtl -d rtl
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        '''
        create source --> destination arguments
        '''
        add_common_args(parser) # TODO add
        parser.add_argument('-l', '--list', action='store_true', required=False, help='list all the available format name')
        parser.add_argument('-p', '--project', metavar='project', required=False)
        parser.add_argument('-i', '--ip', metavar='ip', required=False)
        parser.add_argument('-b', '--bom', metavar='bom', required=False)
        parser.add_argument('-d', '--deliverables', metavar='deliverables', nargs='*')
        parser.add_argument('-f', '--format', metavar='format', required=False)

    @classmethod
    def command(cls, args):
        '''
        Execute the "export" subcommand
        '''
        lists = args.list
        project = args.project
        ip = args.ip
        bom = args.bom
        deliverables = args.deliverables
        format = args.format
       
        if lists:
            if project or ip or bom or deliverables or format:
                raise IpExportError('-l|--list cannot use with other options.')
            return dmx.abnrlib.flows.ipexport.IPExport(None, None, None, None, None).get_all_format_name()    
        else:
            ipexport = dmx.abnrlib.flows.ipexport.IPExport(project, ip, bom, deliverables, format) 
            ret = ipexport.run()
        return ret
