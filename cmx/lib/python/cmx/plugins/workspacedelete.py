#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/workspacedelete.py#4 $
$Change: 7744897 $
$DateTime: 2023/08/17 02:03:13 $
$Author: wplim $

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

from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

LOGGER = logging.getLogger(__name__)

class WorkspaceDelete(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Deletes an ICM workspace (Equivalent to pm workspace -x)
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Delete an existing IC Manage workspace.

        If -w/--workspacename is specified, will delete the workspace from IC Manage. 
        (files in the workspace path will NOT be deleted)
        If -w/--workspacename is NOT specified, and current directory is within an IC Manage
        workspace, then delete the current IC Manage workspace.
        If -r option is used, files and folders will be deleted altogether.
        If --older_than option is specified, will delete all of your workspace that have not been accessed 
        in the last specified days.
        If -y/--yes_to_all option is used, skip confirmation and force all (y/n) to y.
        
        Example:
        $cd /icd_da/da/DA/yltan/yltan.project1.ar_lib.23/ar_lib/oa
        $dmx workspace delete
        Delete the current workspace (for this case, it is yltan.project1.ar_lib.23)
        but don't delete the files/directories in it.

        $dmx workspace delete -w yltan.project1.ar_lib.23 yltan.project1.ar_lib.45 -r
        Delete workspace yltan.project1.ar_lib.23 and yltan.project1.ar_lib.45 all it's 
        files/directories.

        $dmx workspace delete --older_than 30
        To delete all your workspaces that have not been accessed in 30 days, but don't 
        delete the files:

        $dmx workspace delete --older_than 60 --rmfiles
        To delete all your workspaces that have not been accessed in 60 days, and all it's 
        files
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('-y', '--yes-to-all', action='store_true', required=False, help='answer "yes" to all y/n question.', default=False)

    @classmethod
    def command(cls, args):
        workarea = os.environ.get("WORKAREA")
        #cmd = f'chmod 777 {workarea} -R; rm -rf -- {workarea}/..?* .[!.]* *;'
        cmd = f'chmod 777 {workarea} -R; rm -rf {workarea}/*; rm -rf {workarea}/.git*; rm -rf {workarea}/.created_at'
        LOGGER.debug(cmd)
        if args.yes_to_all:
            ans = 'y'
        else:
            print(f"Are you sure you want to delete {workarea}?")
            ans = input("(y/n)? ")
        if ans.lower() == 'y':
            os.system(cmd)
        #dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
  
