#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqstatus.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx clonboms"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import logging
import textwrap
import argparse

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqstatus

class CicqStatusError(Exception): pass

class CicqStatus(Command):
    '''plugin for "dmx cicq init"'''

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Get the CICQ job status of the given TeamCity Job.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', required=True)
        parser.add_argument('-i', '--ip', required=True)
        parser.add_argument('-t', '--thread', required=True)
        parser.add_argument('-f', '--infokeys', required=False, default='id,name,status', help=argparse.SUPPRESS)
        parser.add_argument('-a', '--arcjobid', required=False, default='', help=argparse.SUPPRESS)


    @classmethod
    def extra_help(cls):
        extra_help = '''\
        Get the CICQ job status of the given teamcity job.

        If the job has already completed or there is no running job:-
        - return the last job's exit status.
        
        If the job is currently running:-
        - return all the status of all the children job.

        Usage:-
        -------
        >dmx cicq status -p i10socfm -i liotestfc1 -t TestRun

        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):

        cs = dmx.abnrlib.flows.cicqstatus.CicqStatus(args.project, args.ip, args.thread, infokeys=args.infokeys, arcjobid=args.arcjobid)
        ret = cs.run()
                    
        return ret

