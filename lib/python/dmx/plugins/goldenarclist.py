#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/goldenarclist.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: branch dmx subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2013
All rights reserved.
'''
import os
import sys
import logging
import textwrap
import getpass
import time
import re

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.createvariant import CreateVariant
from dmx.utillib.admin import is_admin
import dmx.ecolib.ecosphere 
import dmx.abnrlib.flows.goldenarclist


class GoldenarcListError(Exception): pass

class GoldenarcList(Command):
    '''
    dmx subcommand plugin class

    Creates an IP and all deliverables associated with the type of IP
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            List arc resources from the goldenarc db.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        create ip arguments
        '''
        add_common_args(parser)
        parser.add_argument('-f', '--flow', required=False, default=None)
        parser.add_argument('-s', '--subflow', required=False, default=None)
        parser.add_argument('-t', '--thread', required=False, default=None)
        parser.add_argument('-m', '--milestone', required=False, default=None)
        parser.add_argument('--tool', required=False, default=None)
        parser.add_argument('-v', '--version', required=False, default=None)
        parser.add_argument('--source', choices=['proddb', 'devdb'], default='proddb')


    @classmethod
    def extra_help(cls):
        if is_admin():
            admin_help = ''
        else:
            admin_help = ''            
                    
        extra_help = '''\
        List Golden arc resource versions.


        {0}    
        Example
        =======
        To list everything defined for the given thread/milestone
            $dmx goldenarc list -t FM8revA0 -m 8.0

        To list all arc versions for a given flow/subflow in a thread/milestone
            $dmx goldenarc list -f lint -s mustfix -t FM8revA0 -m 3.0

        If there is a need to query from the production database, user --source proddb
        If there is a need to query from the development database, user --source devdb

        '''.format(admin_help)

        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        g = dmx.abnrlib.flows.goldenarclist.GoldenarcList(args.thread, args.milestone, args.flow, args.subflow, args.tool, args.version, source=args.source, preview=args.preview)
        g.run()

        return 0
