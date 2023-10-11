#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/waiverapproverlist.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

import os
import sys
import logging
import textwrap
import argparse

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.dmxwaiver import DmxWaiver

LOGGER = logging.getLogger(__name__)

class WaiverApproverList(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            List all waiver approval 
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        List all waiver's approver.
        
        Example
        =======
        %dmx waiver approverlist -t FP8revA0
        List waiver's approver for thread FP8revA0
        '''
        return textwrap.dedent(myhelp)


    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx waiver aprovallist" subcommand'''

        add_common_args(parser)
        parser.add_argument('-t', '--thread', metavar='thread', required=True)
        parser.add_argument('-p', '--project', metavar='project', required=False)
        parser.add_argument('-d', '--deliverable',  metavar='deliverable', required=False)
        parser.add_argument('-u', '--user',  metavar='user name', required=False)
        parser.add_argument('--dev', action='store_true', required=False, help='connect to dev server')
        parser.add_argument('--user_type',  metavar='user_type', required=False)

    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        thread = args.thread
        project = args.project
        deliverable = args.deliverable
        user = args.user
        user_type = args.user_type
        dev = args.dev
        ret = 1
        if dev:
            mongodb = 'test'
        else:
            mongodb = 'prod'

        ret = DmxWaiver(mongodb).get_waivers_approver(thread, project, deliverable, user, user_type)

        return ret

