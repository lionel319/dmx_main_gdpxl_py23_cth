#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/waiverrequest.py#1 $
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
from dmx.ecolib.ecosphere import EcoSphere

LOGGER = logging.getLogger(__name__)

class WaiverRequest(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Request a new waiver
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Create a dmx hsdes based waiver.

        The file format is similar with tnrwaivers.csv. If you are not sure the format of the waiver file.
        You can refer following link : https://wiki.ith.intel.com/display/tdmaInfra/Waivers#Waivers-WaiverFileFormat
       
        Example
        =======
        %dmx waiver request -t <thread> -m <milstone> -p <project> -f <tnrerrors.csv> --approver <approver idsid>
        Requesting hsdes based dmx waiver 

        %dmx waiver request -t <thread> -m <milstone> -p <project> -f <tnrerrors.csv> --approver <approver idsid> --globalwaiver
        Requesting hsdes based dmx global waiver

        %dmx waiver request -t <thread> -m <milstone> -p <project> -f <tnrerrors.csv> -a <attachment if needed> --approver <approver idsid>
        Requesting hsdes based dmx waiver with attachment

        %dmx waiver request -t <thread> -m <milstone> -p <project> -f <tnrerrors.csv> -a <attachment> --hsdesid <hsdes caseid> --approver <approver idsid>
        Request a waiver and append to existing hsdes cases.


        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx waiver" subcommand'''

        add_common_args(parser)
        valid_thread_milestone = EcoSphere().get_valid_thread_and_milestone()
        valid_thread = valid_thread_milestone.keys()

        parser.add_argument('-t', '--thread', metavar='thread', required=True)
        parser.add_argument('-m', '--milestone', default='*', metavar='milestone', required='yes')
        parser.add_argument('-f', '--file',  metavar='tnrwaiver/tnrerror file', required=False)
        parser.add_argument('-p', '--project',  metavar='project', required=True)
        parser.add_argument('-a', '--attachment', nargs='+',  metavar='attachment', required=False)
        parser.add_argument('--hsdesid', metavar='hsdes case id', required=False)
        parser.add_argument('--approver', metavar='approver',help='approver idsid', required=True)
        parser.add_argument('-g', '--globalwaiver', action='store_true', help='HSD waiver is used for global waiver only', required=False)
        parser.add_argument('--dev', action='store_true', required=False, help='connect to dev server')
       # parser.add_argument('--yes',  required=False, default=False, action='store_true', help = 'Answers yes to any input prompt')


    @classmethod
    def command(cls, args):
        '''the "waiver" subcommand'''
        thread = args.thread
        milestone = args.milestone
        tnrwaiver_file = args.file
        project = args.project
        attachment = args.attachment
        globalwaiver = args.globalwaiver
        dev = args.dev
        hsdesid = args.hsdesid
        approver = args.approver

        if globalwaiver:
            waiver_type = 'global' 
        else:
            waiver_type = 'default'

        if dev:
            mongodb = 'test'
        else:
            mongodb = 'prod'

        ret = 1
        ret = DmxWaiver(mongodb).add_waivers(thread, milestone, tnrwaiver_file, project, attachment, waiver_type, hsdesid, approver) 
        return ret

