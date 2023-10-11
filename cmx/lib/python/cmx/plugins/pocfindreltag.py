#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/pocfindreltag.py#5 $
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
import cmx.tnrlib.release_runner_cthfe

class Pocfindreltag(Command):
    '''plugin for "dmx login"'''

    #HIDDEN = True

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Given an IP_MODEL tagname, find the equivalent icm REL tag
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help list
        '''
        extra_help = '''\
            Given an IP_MODEL tagname, find the equivalent icm REL tag
           
            Example:-
            =========
            >dmx poc findreltag --tagname liotest1-a0-23ww20b
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('--tagname', '-t', required=True)
        parser.add_argument('--full', action='store_true', default=False, help='output full details')


    @classmethod
    def command(cls, args):
        rr = cmx.tnrlib.release_runner_cthfe.ReleaseRunnerCthfe(None, None, None, None, None, None)
        foundlist = rr.find_mapping_reltag(args.tagname)
        if args.full:
            pprint(foundlist)
        else:
            for e in foundlist:
                print(e['name'])
        return 0
