#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/waiverapproveradd.py#1 $
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
from dmx.errorlib.exceptions import *

LOGGER = logging.getLogger(__name__)

class WaiverApproverAdd(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Add a new approver for dmx waiver system
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Add a approver for dmx waiver 

        Example
        =======
        %dmx waiver approveradd -t <thread> -d <deliverable> --approver <approver idsid> --notify_list <notify_list>
        Add a approver for dmx waiver 
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx waiverapprover" subcommand'''

        add_common_args(parser)
        parser.add_argument('-t', '--thread', metavar='thread', required=True)
        parser.add_argument('-p', '--project', metavar='project', default='*', required=False)
        parser.add_argument('-d', '--deliverable', metavar='deliverable', default='*', required=True)
        parser.add_argument('-s', '--subflow', metavar='subflow', default='*', required=False)
        #parser.add_argument('--user_type', metavar='user_type', choices=['approval','notify_list'])
        #parser.add_argument('-u', '--user', metavar='user', nargs='+', required=True)
        parser.add_argument('--approver', metavar='approver', required=True)
        parser.add_argument('--notify_list', metavar='notify_list', nargs='+', required=True)
        parser.add_argument('-g', '--globalwaiver', action='store_true', required=False)
        parser.add_argument('--dev', action='store_true', required=False)




    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        thread = args.thread
        project = args.project
        deliverable = args.deliverable
        approver = args.approver
        notify_list = args.notify_list
        globalwaiver = args.globalwaiver
        dev = args.dev
        subflow = args.subflow
        ret = 1
      #  if user_type == 'approval' and len(user) > 1:
      #      raise DmxErrorTRWV02('Waiver approval cannot be more than one person.')

        if globalwaiver:
            waiver_type = 'global'
        else:
            waiver_type = 'default'

        if dev:
            mongodb = 'test'
        else:
            mongodb = 'prod'

     #   ret = DmxWaiver().add_vip(thread, ip, deliverable, user, user_type)
        ret = DmxWaiver(mongodb).add_approver(thread, project, deliverable, approver, notify_list, waiver_type, subflow=subflow)
        return ret

