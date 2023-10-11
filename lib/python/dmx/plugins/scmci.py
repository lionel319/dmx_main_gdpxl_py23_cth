#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/scmci.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''
from __future__ import print_function

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

import os
import sys
import logging
import textwrap
import argparse
from threading import Thread

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args, is_shell_bash
from dmx.utillib.admin import is_admin
from dmx.abnrlib.scm import *
from dmx.utillib.arcjob import *

LOGGER = logging.getLogger(__name__)

class SCMCI(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Checks in large data to repository
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        dmx scm ci command checks-in/submits opened files in a workspace to ICManage.

        Command will work similar to 'icmp4 add' command whereby a file pattern is provided.
        If file pattern is provided, command will crawl the file pattern for files to be checked-in.
        if --manifest option is specified, command will refer to manifest to determine which files to check-in. 
        Command will automatically check-in new files that haven't been checked in to ICManage.
        Command will also only check-in existing files that have been marked as opened via 
        scm co command.
        Command must be run in a workspace where files are supposed to be checked-in.

        If a configuration is provided (--cfg), command will process each line in the configuration as a regex pattern. Each regex pattern will be globbed in the current workspace to get list of files that would be checked in to repository. 
        Each regex pattern in the configuration must be accompanied with required/optional value. Command will ensure that a pattern with a required value has at least file in the workspace to be checked in. Otherwise, command will error out.

        NOTE:
        In the event that scm checkin fails and files are missing from the workspace, please follow these steps to restore the files manually:
        1. Look for .naa_tmp directory in <workspaceroot>/<ip>/<deliverable>/
        2. If you see multiple .naa_tmp directories, choose the directory with biggest counter (For example: Between .naa_tmp.1 and .naa_tmp.2, choose .naa_tmp.2)
        3. Copy the files back to their original location. The directory structure of the files are preserved in .naa_tmp directory.

        Examples
        ========
        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm ci filepath/... --desc "meaningful description"
        Check-in any checked-out and new files found in <workspaceroot>/ip/deliverable/filepath/... 

        $ cd <workspaceroot>
        $ dmx scm ci -i ip -d deliverable --manifest --desc "meaningful description"
        Check-in any checked-out and new files defined in manifest for deliverable

        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm ci --manifest --desc "meaningful description"
        Check-in any checked-out and new files defined in manifest for deliverable
         
        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm ci --manifest --cell c1 c2 --desc "meaningful description"
        Check-in any checked-out and new files defined in manifest for deliverable that matches cell c1 and c2

        $ cd <workspaceroot>/ip/deliverable
        $ dmx scm ci filepath/... --manifest --desc "meaningful description"
        Check-in any checked-out and new files found in <workspaceroot>/ip/deliverable/filepath/...
        Check-in any checked-out and new files defined in manifest for deliverable 
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('filespec',  metavar='file ...', nargs='*',
                            help='File pattern to indicate files to checkin. Follows Perforce pattern convention.')
        parser.add_argument('--desc',  required=True,
                            help='Reason for checkin')
        parser.add_argument('--manifest',  required=False, action='store_true',
                            help='Check-in files defined in manifest')
        parser.add_argument('-i', '--ip',  metavar='ip', required=False,
                            help='IP to checkin. If not provided, IP will be extracted from current working directory.')
        parser.add_argument('-d', '--deliverable',  metavar='deliverable', required=False,
                            help='Deliverable to checkin. If not provided, deliverable will be extracted from current working directory')
        parser.add_argument('--cell',  metavar='cell', required=False, nargs='+', default=[],
                            help='Cell to checkin. If not provided, every cell will be checkin.')
        parser.add_argument('--workspace',  metavar='workspace', required=False, 
                            help='Workspace to perform checkin from. If not provided, workspace will be assumed as the current working directory. Workspace must be provided with fullpath.')
        parser.add_argument('--cfg',  metavar='config', required=False, 
                            help='')
                        
        # http://pg-rdjira:8080/browse/DI-1107
        '''
        if is_admin():
            parser.add_argument('--noarc',  required=False, action='store_true', help='Admin switch to run checkin locally instead of submitting to ARC. For debugging purpose. Only visible to admins.')
        '''
    @classmethod
    def command(cls, args):
        '''the "workspace" subcommand'''
        filespec = args.filespec
        desc = args.desc
        ip = args.ip
        deliverable = args.deliverable
        manifest = args.manifest
        cell = args.cell
        workspace = args.workspace if args.workspace else os.getcwd()
        config = args.cfg

        preview = args.preview        
        debug = args.debug

        ret = 1
        scm = SCM(preview)
        arcjob = ArcJob()

        # http://pg-rdjira:8080/browse/DI-1107
        # Always run locally
        noarc = True

        if noarc:
            # Disallow control-c because it will leave files in an incomplete state
            # Should we also catch KeyboardInterrupt?
            LOGGER.info('CAUTION: PLEASE DO NOT TERMINATE, KILL OR SUSPEND (CTRL-C/CTRL-Z) COMMAND UNTIL IT HAS FINISHED.')
            safety_thread = Thread(target=scm.checkin_action, args=(workspace, filespec, manifest, ip, deliverable, cell, desc, config))
            safety_thread.start()
            safety_thread.join()
        else:                   
            if is_shell_bash():
                command = 'export DMXDATA_ROOT={}; python {} checkin --cwd {} --desc \'{}\''.format(os.getenv('DMXDATA_ROOT'), scm.scm_path, workspace, desc)
            else:                
                command = 'setenv DMXDATA_ROOT {}; python {} checkin --cwd {} --desc \'{}\''.format(os.getenv('DMXDATA_ROOT'), scm.scm_path, workspace, desc)
            if ip:
                command = '{} --ip \'{}\''.format(command, ip)
            if deliverable:
                command = '{} --deliverable \'{}\''.format(command, deliverable)
            if cell:
                command = '{} --cell {}'.format(command, ' '.join(cell))
            if filespec:
                command = '{} --file \'{}\''.format(command, filespec) 
            if debug:
                command = '{} --debug'.format(command)
            if preview:
                command = '{} --preview'.format(command)
            
            LOGGER.info('Preparing to submit check-in job to ARC. Please do not modify the workspace until after the job is completed.')
            jobid = arcjob.submit_job(command)
            jobpage = arcjob.get_job_page(jobid)
            LOGGER.info('Check-in job has been submitted to ARC. Please check {} for the job progress.'.format(jobpage))
            arcjob.wait_for_completion(jobid)                    
            exitcode, stdout, stderr = arcjob.get_job_output(jobid)
            # Ignore stty error that is always present whenever we submit an arc job
            if stderr:
                for line in stderr:
                    if 'stty: standard input: Inappropriate ioctl for device' in line:
                        stderr.remove(line)                        
            if exitcode or (stderr and 'stty: standard input: Inappropriate ioctl for device' not in stderr):
                for line in stderr:
                    print(line)
                raise Exception('Job {} has failed. Please check {} for full job details.'.format(jobid, jobpage))
            # Print stdout to terminal
            if stdout:                
                for line in stdout:
                    if 'INFO' in line or 'DEBUG' in line:
                        print(line)
        ret = 0
                 
        return ret
