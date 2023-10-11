#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqpull.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx clonboms"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap
import argparse

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqpull
import dmx.utillib.arcjob


LOGGER = logging.getLogger(__name__)

class CicqPullError(Exception): pass

class CicqPull(Command):

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Pull(update + overlay/integrate) content from a reference-bom to the cicq-backend-boms(CBB) landing_zone(LZ) config.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=False, default=None)
        parser.add_argument('-b', '--bom',  metavar='ip_bom', required=False, default=None,
            help='If provided, will update the REFBOM registered in cicq. Else, will use the registered REFBOM from cicq.')
        parser.add_argument('-d', '--deliverables', required=False, nargs='+', default=None,
            help='Only push the list of deliverables. If not provided, will get the deliverables from the already uploaded cicq.ini file.')
        parser.add_argument('--hier', required=False, default=False, action='store_true',
            help='Push the content hierarchically, if option is given.')
        parser.add_argument("-t", "--thread", required=True)
        parser.add_argument('--wait', required=False, default=False, action='store_true',
            help='DEPRECATED!!! From now on, this command will always return prompt only after all jobs are completed.(this option was retained on purpose for backward compatibility)')

    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help bom clone'''
        extra_help = '''\
            "dmx cicq pull" is used to update + push (update + overlay/integrate/copy) content from the reference-bom to the cicq-backend-boms(CBB) landing_zone(LZ) config.
            (Note: By default, source-bom which are immutable will be skipped)
          
            In actual fact, it runs this 2 commands in series:-
                >dmx cicq update -p $PROJECT -i $IP -b $REFBOM -t $THREAD --debug
                >dmx cicq push -p $PROJECT, -i $IP -b $REFBOM -d $DELIVERABLES --wait --hier -t $THREAD --debug

            For a more detail of how it works, kindly refer to the detail help of the above commands by running:-
                >dmx help cicq update
                >dmx help cicq push
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        project = args.project
        ip = args.ip
        bom = args.bom
        deliverables = args.deliverables
        hier = args.hier
        thread = args.thread
        preview = args.preview
        wait = True

        ci = dmx.abnrlib.flows.cicqpull.CicqPull(thread, project=project, ip=ip, bom=bom, deliverables=deliverables, hier=hier, preview=preview, wait=wait)
        ret = ci.run()
        
        return ret

