#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/size.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $
'''
import sys
import logging
import textwrap
import re

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.printsize import PrintSize


class Size(Command):
    '''plugin for "dmx list"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            List total number of files and total file size 
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help list
        '''
        extra_help = '''\
            List total number of files and total file size in specific project/ip@bom or project/ip:deliverable@bom
            
            Example
            =======
            List total number of files and filesize per ip
            $ dmx size -p i10socfm -i cw_lib -b dev

            List total number of files per ip and filesize per deliverable
            $ dmx size -p i10socfm -i cw_lib -d lint -b dev
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)
        parser.add_argument('-b', '--bom',  metavar='src_bom', required=True)


    @classmethod
    def command(cls, args):
        '''the "size" command'''
        project = args.project
        ip = args.ip
        deliverable = args.deliverable
        bom  = args.bom

        printsize = PrintSize(project, ip, deliverable, bom)

        printsize.run()
