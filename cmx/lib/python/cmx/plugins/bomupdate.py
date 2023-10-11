#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/bomupdate.py#1 $
$Change: 7463577 $
$DateTime: 2023/01/31 01:08:26 $
$Author: lionelta $

Description: plugin for "dmx clonboms"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import logging
import textwrap

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

class BomUpdateError(Exception): pass

class BomUpdate(Command):
    '''plugin for "dmx bom clone"'''

    @classmethod
    def get_help(cls):
        myhelp = '''\
            Replace all sub-IPs' bom with the boms in the given syncpoint.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', required=True)
        parser.add_argument('-i', '--ip', required=True)
        parser.add_argument('-b', '--bom',  required=True)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-s', '--syncpoint',  required=False)
        group.add_argument('--file', required=False)
        parser.add_argument('--newbom',  required=False, default=False)


    @classmethod
    def extra_help(cls):
        extra_help = '''\
            Replace all sub-IPs' bom with the boms in the given syncpoint.
            the same as the one found in the WIP	no update, skipped
            <ICM-project>/<IP>:<deliverable> is found in the WIP with another BoM	            <ICM-project>/<IP>:<deliverable> is updated with the new BoM
            <ICM-project>/<IP>:<deliverable> is not found in the WIP	                        <ICM-project>/<IP>:<deliverable>@<BoM> is added
            <ICM-project>/<IP>:<deliverable>@delete	                                            <ICM-project>/<IP>:<deliverable> is removed
            <ICM-project>/<IP>:<deliverable>@remove	                                            <ICM-project>/<IP>:<deliverable> is removed
            <ICM-project>/<IP>@<BoM>	                                                        <ICM-project>/<IP>@<BoM> is not found in the WIP - Error
            <ICM-project> does not exist in ICM	                                                Error
            <ICM-project>/<IP> does not exist in ICM	                                        Error
            <ICM-project>/<IP> does not exist in the WIP	                                    Error
            <ICM-project>/<IP>:<deliverable> does not exist in ICM	                            Error
            <ICM-project>/<IP>:<deliverable>@<BoM> does not exist in ICM	                    Error

        More detail: https://wiki.ith.intel.com/display/tdmaInfra/Prism#Prism-HowtoupdateaWIP?
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        return dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
        
