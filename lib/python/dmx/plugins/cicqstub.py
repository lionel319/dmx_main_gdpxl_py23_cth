#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqstub.py#1 $
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

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqstub

class CicqStubError(Exception): pass

class CicqStub(Command):
    '''plugin for "dmx cicq init"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Create the cicq.ini file template.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=False, default=None)
        parser.add_argument('-t', '--thread', required=False, default=None)


    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help bom clone'''
        extra_help = '''\
            Create the cicq.ini file template.

            Kindly open up this file and make the appropriate changes before running cicq.

        Usage:-
        -------

        ### Download a cicq.ini template file.
        >dmx cicq stub

        ### Download a cicq.ini config file from the centralized cicq project area.
        >dmx cicq stub -p project -i ip -t thread


        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''the "bom clone" subcommand'''
        # generic arugments
        project = args.project
        ip = args.ip
        thread = args.thread

        cs = dmx.abnrlib.flows.cicqstub.CicqStub(project=project, ip=ip, thread=thread)
        ret = cs.run()
                    
        return ret

