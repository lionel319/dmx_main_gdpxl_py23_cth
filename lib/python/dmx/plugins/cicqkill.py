#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqkill.py#1 $
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

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqkill

class CicqKillError(Exception): pass

class CicqKill(Command):

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Forcefully kill the current running cicq TeamCity Job.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', required=True)
        parser.add_argument('-i', '--ip', required=True)
        parser.add_argument('-t', '--thread', required=True)


    @classmethod
    def extra_help(cls):
        extra_help = '''\
            "cicq kill" kills the current running Cicq TeamCity Job Immediately.
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        # generic arugments
        project = args.project
        ip = args.ip
        thread = args.thread
        dryrun = args.preview

        ci = dmx.abnrlib.flows.cicqkill.CicqKill(project, ip, thread, dryrun=dryrun)
        ret = ci.run()
                    
        return ret

