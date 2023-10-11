#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/pocrmwsfromwa.py#2 $
$Change: 7688374 $
$DateTime: 2023/07/06 03:18:20 $
$Author: lionelta $
'''
import sys
import os
import logging
import textwrap
import re
import json
from pprint import pprint

sys.path.insert(0, os.getenv("DMX_LIB"))
from cmx.abnrlib.command import Command 
from dmx.utillib.utils import add_common_args

class Pocrmwsfromwa(Command):
    '''plugin for "dmx login"'''

    #HIDDEN = True

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Delete icmws from $WORKAREA
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        extra_help = '''\
            Delete icmws from $WORKAREA
           
            Example:-
            =========
            >dmx poc rmwsfromwa 
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('--rmfiles', '-r', default=False, action='store_true')


    @classmethod
    def command(cls, args):
        workarea = os.getenv("WORKAREA")
        if not workarea:
            raise Exception("$WORKAREA env var not defined. Program Terminated")

        ### Create psg folder
        wsdir = os.path.join(os.path.abspath(workarea), 'psg')
        
        cmd = 'delete-workspace --workspace {} '.format(wsdir)
        if not args.rmfiles:
            cmd += ' --leave-files'
        return os.system(cmd)
