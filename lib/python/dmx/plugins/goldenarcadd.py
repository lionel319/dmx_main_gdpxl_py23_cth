#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/goldenarcadd.py#1 $
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
import dmx.abnrlib.flows.goldenarcadd


class GoldenarcAddError(Exception): pass

class GoldenarcAdd(Command):
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
            Add an arc resource to the goldenarc db.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        create ip arguments
        '''
        add_common_args(parser)
        parser.add_argument('-f', '--flow', required=True)
        parser.add_argument('-s', '--subflow', required=False, default='')
        parser.add_argument('-t', '--thread', required=True)
        parser.add_argument('-m', '--milestone', required=True)
        parser.add_argument('-a', '--arc', required=True)
        parser.add_argument('--source', choices=['proddb', 'devdb'], default='proddb')


    @classmethod
    def extra_help(cls):
        '''
        Detailed help for goldenarc add. 
        '''
        if is_admin():
            admin_help = ''
        else:
            admin_help = ''            
                    
        extra_help = '''\
        Allow flow/check owners to add in their arc resource version that is compatible with a given thread/milestone.


        {0}    
        Example
        =======
        Add dmx/9.5 to be the allowable version for FM8revA0/3.0 release for reldoc check(flow:reldoc, subflow: )
            $ dmx goldenarc add --thread FM8revA0 --milestone 3.0 --flow reldoc --arc dmx/9.5       
        
        Add atrenta_sgmaster/2.1_fm4_1.4 to be the allowable version for FM8revA0/3.0,4.0 release for lint check(flow:lint, subflow:mustfix / flow:lint, subflow:review)
            $ dmx goldenarc add --thread FM8revA0 --milestone 3.0 --flow lint --subflow mustfix --arc atrenta_sgmaster/2.1_fm4_1.4
            $ dmx goldenarc add --thread FM8revA0 --milestone 4.0 --flow lint --subflow mustfix --arc atrenta_sgmaster/2.1_fm4_1.4
            $ dmx goldenarc add --thread FM8revA0 --milestone 3.0 --flow lint --subflow review  --arc atrenta_sgmaster/2.1_fm4_1.4
            $ dmx goldenarc add --thread FM8revA0 --milestone 4.0 --flow lint --subflow review  --arc atrenta_sgmaster/2.1_fm4_1.4

        If your flow/subflow is agnostic and is not supposed to be gated by any arc resource, it needs to be defined with (--arc skipgoldenarc/0), eg:-
            $ dmx goldenarc add --thread FM8revA0 --milestone 4.0 --flow lint --subflow review  --arc skipgoldenarc/0
            

        '''.format(admin_help)

        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the subcommand
        '''
        g = dmx.abnrlib.flows.goldenarcadd.GoldenarcAdd(args.thread, args.milestone, args.flow, args.arc, args.subflow, source=args.source, preview=args.preview)
        g.run()

        return 0
