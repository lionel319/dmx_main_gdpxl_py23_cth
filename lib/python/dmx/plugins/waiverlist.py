#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/waiverlist.py#1 $
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
import dmx.utillib.admin

LOGGER = logging.getLogger(__name__)

class WaiverList(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            List all waiver
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        List all waiver.
        
        Example
        =======

        %dmx waiver list -t <thread name> -p <project name> -i <ip name> -m <milestone>
        List out all the waiver that requested.

        1. List all waiver from thread FM6revA0 
        %dmx waiver list -t FM6revA0 

        2. List all waiver from thread FM6revA0, project i10socfm 
        %dmx waiver list -t FM6revA0 -p i10socfm 

        3. List all waiver from thread FM6revA0, project i10socfm, ip liotest1 
        %dmx waiver list -t FM6revA0 -p i10socfm -i liotest1

        4. List all waiver from thread FM6revA0, project i10socfm, ip liotest1, milestone 4.0
        %dmx waiver list -t FM6revA0 -p i10socfm -i liotest1 -m 4.0

        5. List all waiver from thread FM6revA0, project i10socfm, ip liotest1, milestone 4.0, created by wplim
        %dmx waiver list -t FM6revA0 -p i10socfm -i liotest1 -m 4.0 -u wplim

        6. List all waiver from thread FM6revA0, project i10socfm, ip liotest1, milestone 4.0, status is pending 
        %dmx waiver list -t FM6revA0 -p i10socfm -i liotest1 -m 4.0 -s pending 

        7. List all waiver from thread FM6revA0, project i10socfm, ip liotest1, milestone 4.0, status is wont_do 
        %dmx waiver list -t FM6revA0 -p i10socfm -i liotest1 -m 4.0 -s wont_do 

        8. List all waiver from thread FM6revA0, project i10socfm, ip liotest1, milestone 4.0, status is sign_off 
        %dmx waiver list -t FM6revA0 -p i10socfm -i liotest1 -m 4.0 -s sign_off 
        '''
        return textwrap.dedent(myhelp)


    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx globalwaiver" subcommand'''

        add_common_args(parser)
        parser.add_argument('-t', '--thread', metavar='thread', required=False)
        parser.add_argument('-p', '--project', metavar='project', required=False)
        parser.add_argument('-i', '--ip', metavar='ip', required=False)
        parser.add_argument('-d', '--deliverable',  metavar='deliverable', required=False)
        parser.add_argument('-sb', '--subflow',  metavar='subflow', required=False)
        parser.add_argument('-m', '--milestone',  metavar='milestone', required=False)
        parser.add_argument('-u', '--user',  metavar='user name', required=False)
        parser.add_argument('--dev', action='store_true', required=False, help='connect to dev server')
        parser.add_argument('-s', '--status',  metavar='status', choices=['pending', 'sign_off', 'wont_do'], required=False)

    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        thread = args.thread
        ip = args.ip
        deliverable = args.deliverable
        subflow = args.subflow
        milestone = args.milestone
        user = args.user
        status = args.status
        project = args.project
        dev = args.dev
        ret = 1

        if dev:
            mongodb = 'test'
        else:
            mongodb = 'prod'

        current_user = os.environ.get('USER')
        if not thread and not dmx.utillib.admin.is_admin(current_user):
            LOGGER.info('Only admin can run without -t/--thread. Please provie your thread name.')

        ret = DmxWaiver(mongodb).get_waivers(thread, project, ip, deliverable, subflow, milestone, user, status)

        return ret

