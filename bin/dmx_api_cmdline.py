#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/dmx_api_cmdline.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

In many cases, there is a need to run a dmx internal API/library/function with a cmdline call.
For example, when we want to run a 
    - check if icm project exist

this is easily achieved by running a 
    - dmx.abnrlib.icm.ICManageCLI().project_exist()

However, when we want to let a user which doesn't have icm-license run it, this won't make the cut.
He needs to be able to run this as a cmdline (so that the setuid can kick in)
He needs to be able to do something like this:-
    > ssh_setuid_as_psginfraadm -q localhost 'dmx_api_cmdline project_exist -p i10socfm'

This 'dmx_api_cmdline.py' is meant to address this issue.
All api/function/method calls that needs to be made into a cmdline can be placed into here.

However, in order to make it a more standardize way, we lay out a few guidelines.

1. INPUT Format
    > dmx_api_cmdline <subcommand> <options>

2. <subcommand> should have the same function name, eg:-
    > dmx_api_cmdline project_exist -p i10socfm
    > def project_exist(projectname):

3. OUTPUT Format
    > It should be a string which is printout out to stdout in the following format:-
        - DMXAPIJSON: <serialized_json_string>
        eg:-
        - blablabla ... DMXAPIJSON: {'name': 'Lionel Tan', 'age': 16}
    > Use this api to print out the jsonstring:-
        - dmx.utillib.dmxapicmdlineutils.print_output('json_string')

4. How to parse Output
    > <python dict> = dmx.utillib.dmxapicmdlineutils.parse_output_to_dict(stdout + stderr)

'''

import sys
import os
import argparse
import logging
import re
import textwrap
import json
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.abnrlib.icm
import dmx.utillib.washgroup
import dmx.utillib.dmxapicmdlineutils as utils

LOGGER = logging.getLogger()


def main():
    parser = argparse.ArgumentParser(prog='dmx_api_cmdline')
    subparser = parser.add_subparsers(help='sub-command')

    parser_a = subparser.add_parser('project_exists')
    parser_a.add_argument('--project', '-p', required=True)
    _add_debug_option(parser_a)
    parser_a.set_defaults(func=project_exists)

    parser_b = subparser.add_parser('get_user_missing_groups_from_accessing_pvc')
    parser_b.add_argument('--userid', required=True)
    parser_b.add_argument('--project', '-p', required=True)
    parser_b.add_argument('--ip', '-i', required=True)
    parser_b.add_argument('--bom', '-b', required=True)
    _add_debug_option(parser_b)
    parser_b.set_defaults(func=get_user_missing_groups_from_accessing_pvc)

    parser_c = subparser.add_parser('get_groups_by_pvc')
    parser_c.add_argument('--project', '-p', required=True)
    parser_c.add_argument('--ip', '-i', required=True)
    parser_c.add_argument('--bom', '-b', required=True)
    parser_c.add_argument('--include_eip_groups', required=False, default=False, action='store_true')
    parser_c.add_argument('--include_base_groups', required=False, default=False, action='store_true')
    _add_debug_option(parser_c)
    parser_c.set_defaults(func=get_groups_by_pvc)

    args = parser.parse_args()
    _setup_logger(args)
    args.func(args)

def get_groups_by_pvc(args):
    wg = dmx.utillib.washgroup.WashGroup()
    ret = wg.get_groups_by_pvc(args.project, args.ip, args.bom, args.include_eip_groups, args.include_base_groups)
    utils.print_output(ret)

def get_user_missing_groups_from_accessing_pvc(args):
    wg = dmx.utillib.washgroup.WashGroup()
    ret = wg.get_user_missing_groups_from_accessing_pvc(args.userid, args.project, args.ip, args.bom)
    utils.print_output(ret)


def project_exists(args):
    icm = dmx.abnrlib.icm.ICManageCLI()
    ret = icm.project_exists(args.project)
    utils.print_output(ret)


def _setup_logger(args):
    if args.debug:
        logging.basicConfig(format="%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s")
        LOGGER.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")
        LOGGER.setLevel(logging.INFO)


def _add_debug_option(parser):
    parser.add_argument('--debug', default=False, action='store_true')


if __name__ == '__main__':
    sys.exit(main())
