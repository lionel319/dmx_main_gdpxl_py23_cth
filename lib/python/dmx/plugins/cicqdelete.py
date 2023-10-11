#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqdelete.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx cicq delete"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqdelete

LOGGER = logging.getLogger(__name__)
class CicqDeleteError(Exception): pass

class CicqDelete(Command):
    '''plugin for "dmx cicq delete"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Delete cicq thread with the given project, ip, bom.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx cicq thread" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=False)
        parser.add_argument('-i', '--ip', metavar='ip', required=False)
        parser.add_argument('-t', '--thread', required=False)
        parser.add_argument('-d', '--day', required=False, default=None, help='for cron only')


    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help cicq delete'''
        extra_help = '''\
            "cicq delete" is to delete unwanted thread with given project, ip, thread.
            Only admin or owner of the thread can delete it.
            For existing thread that is created before dmx/14.1, only admion can delete it due to OWNER parameter is not set properly.

            Example
            =======
            $ dmx cicq delete --project i10socfm --ip liotestfc1 --thread test3_dev 
    
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''the "bom clone" subcommand'''
        # generic arugments
        project = args.project
        ip = args.ip
        thread = args.thread
        preview = args.preview
        dryrun = args.preview
        day = args.day

        if args.day and (args.project or args.ip or args.thread):
            LOGGER.error("-d and -p|-i|-t are mutually exclusive ...")
            sys.exit(2)
        if args.day:
            ci = dmx.abnrlib.flows.cicqdelete.CicqDelete(day=day, dryrun=dryrun)
        else:
            ci = dmx.abnrlib.flows.cicqdelete.CicqDelete(project, ip, thread, day, dryrun=dryrun)
        ret = ci.run()
                    
#        return ret

