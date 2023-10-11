#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/releasereport.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "release library" subcommand plugin
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import sys
import logging
import textwrap
import itertools
import os

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
import dmx.utillib.arcutils

class ReleaseReport(Command):

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Retrieve the release status of the given arc-job-id.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)

        '''subcommand arguments'''
        parser.add_argument('-a', '--arcjobid', required=True, help='the release arc-job-id, which is reported out during "dmx release". Look for the line that says "Your release job ID is ######" ')
        
    @classmethod
    def extra_help(cls):
        extra_help = '''\
                     '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        arcjobid = args.arcjobid
        arcsite = os.getenv("ARC_SITE")
        exe = 'release_viewer'
        
        if arcsite == 'sc':
            cmd = '{} {}'.format(exe, arcjobid)
        else:
            sjhost = dmx.utillib.server.Server(site='sc').get_working_server()
            arcres = dmx.utillib.arcutils.ArcUtils().get_arc_job()['resources']
            cmd = """ /p/psg/da/infra/admin/setuid/tnr_ssh -q {} 'arc shell {} -- {} {}' """.format(sjhost, arcres, exe, arcjobid)
        return os.system(cmd)

