#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/waiverapproverdelete.py#1 $
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

class WaiverApproverDelete(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Delete a waiver's approver
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Delete a waiver's approver.
        
        Example
        =======
        %dmx waiver approverdelete -t <thread> -i <ip> -d <deliverable> -u <user>
        Delete a waiver's approver 
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx waiver" subcommand'''

        add_common_args(parser)
        parser.add_argument('-t','--thread', metavar='thread', required=True)
        parser.add_argument('-p','--project', metavar='project', required=True)
        parser.add_argument('-d','--deliverable', metavar='thread', required=True)
        parser.add_argument('--dev', action='store_true', required=False, help='connect to dev server')
        #parser.add_argument('-u','--user', metavar='user', required=True)
        #parser.add_argument('--yes',  required=False, default=False, action='store_true', help = 'Answers yes to any input prompt')

    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        thread = args.thread
        project = args.project
        deliverable = args.deliverable
        #user = args.user 
        dev = args.dev

        if dev:
            mongodb = 'test'
        else:
            mongodb = 'prod'

        ret = 1
        ret = DmxWaiver(mongodb).delete_waivers_approver(thread, project, deliverable)
        return ret
