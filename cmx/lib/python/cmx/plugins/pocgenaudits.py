#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/pocgenaudits.py#6 $
$Change: 7688374 $
$DateTime: 2023/07/06 03:18:20 $
$Author: lionelta $
'''
import sys
import os
import logging
import textwrap
import re
import json
from pprint import pprint

sys.path.insert(0, os.getenv("DMX_LIB"))
from cmx.abnrlib.command import Command 
from dmx.utillib.utils import add_common_args
import cmx.tnrlib.test_runner
from dmx.tnrlib.audit_check import AuditFile

class Pocgenaudits(Command):
    '''plugin for "dmx login"'''

    #HIDDEN = True

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Generate mockup audit xml files
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help list
        '''
        extra_help = '''\
            Login user to dmx system.
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('--ip', '-i')
        parser.add_argument('--thread', '-t')
        parser.add_argument('--milestone', '-m')
        parser.add_argument('--deliverable', '-d')


    @classmethod
    def command(cls, args):
        thread = args.thread
        milestone = args.milestone
        deliverable = args.deliverable
        ip = args.ip
        workarea = os.getenv("WORKAREA")
        tr = cmx.tnrlib.test_runner.TestRunnerPoc(thread, milestone, deliverable, workspace_root=workarea, ipname=ip)
        checkers = tr.get_required_checkers()
        ipname = ip
        for checker in checkers:
            for cell in tr.get_cells():
                a = AuditFile(update_dashboard=False, workspace_rootdir=workarea, thread=thread, milestone=milestone)
                a.set_test_info(checker.flow, checker.subflow, 'run_dir', 'cmdline', checker.deliverable, topcell=cell, variant=ipname)
                #set_test_info(self, flow, subflow, run_dir, cmdline, libtype, topcell=None, variant=None, arc_job_id='', lsf_job_id='', subtest=''):

                ### Add one pass result
                a.add_result("pass no severity", True)

                ### Purposely add a FAILURE to 1 of the audit
                if checker.flow == 'ipxact':
                    a.add_result("This one kaput", False)

                '''
                ### Purposely skip generating one audit file, to replicate missing audit file
                if checker.flow == 'dmzintfc':
                    continue
                '''

                #a.add_requirement('{}/testfiles/dosfile'.format(wsroot), disable_rcs_filtering=False)
                
                print("Audit File Generated: {}".format(a.get_audit_file_path()))

                a.save()

        
