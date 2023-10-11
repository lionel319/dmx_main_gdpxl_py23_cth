#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqrun.py#1 $
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
import dmx.abnrlib.flows.cicqrun

class CicqRunError(Exception): pass

class CicqRun(Command):

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Forcefully run a cicq TeamCity Job.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', required=True)
        parser.add_argument('-i', '--ip', required=True)
        parser.add_argument('-t', '--thread', required=True)
        parser.add_argument('-f', '--force', required=False, default=False, action='store_true')


    @classmethod
    def extra_help(cls):
        extra_help = '''\
            "cicq run" triggers a Cicq TeamCity Job Immediately.

        However, only one single job is allowed to be running at one time. 
        Thus, when this command is triggered when 
        - a job is currently still runnning, and there are no other jobs in queue:-
            > a new job will be submitted to queue, 
            > and the queued job will immediately runs once the existing running job completed.
        - a job is currently still running, and there is already a job in queue:-
            > nothing happens.
        - no job is currently running,
            > a new job will be run immediately.
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        # generic arugments
        project = args.project
        ip = args.ip
        thread = args.thread
        dryrun = args.preview
        force = args.force

        ci = dmx.abnrlib.flows.cicqrun.CicqRun(project, ip, thread, dryrun=dryrun, force=force)
        ret = ci.run()
                    
        return ret

