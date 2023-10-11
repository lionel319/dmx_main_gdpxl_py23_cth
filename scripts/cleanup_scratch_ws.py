#!/usr/intel/pkgs/python3/3.9.6/bin/python3

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/scripts/cleanup_scratch_ws.py#1 $
$Change: 7511097 $
$DateTime: 2023/03/06 01:18:16 $
$Author: lionelta $

Description: API functions which interacts with Gatekeeper
'''
from __future__ import print_function
import UsrIntel.R1
import os
import logging
import sys
import re
import argparse
from pprint import pprint,pformat
import textwrap
import datetime

LIB = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.utils

LOGGER = logging.getLogger()

def main():
    args = get_args()
    set_logger(args)
    if args.debug:
        pprint(args)
        print(args.__dict__)
   
    wsnames = find_old_workspace(args)
    print("Workspaces to be deleted: {}".format(wsnames))

    delete_workspace(args, wsnames)

def delete_workspace(args, wsnames):
    for wsname in wsnames:
        print("Deleting {} ...".format(wsname))
        cmd = 'delete-workspace --name {} --force --leave-files'.format(wsname)
        if args.dryrun:
            cmd += ' --dryrun'
        print("==> cmd: {}".format(cmd))
        os.system(cmd)


def find_old_workspace(args):
    refdate = datetime.date.today() - datetime.timedelta(days=int(args.days))
    print(refdate.isoformat())
    cmd = 'gdp find --type workspace --columns name "rootDir:~{} && created:<{}"'.format(args.pathregex, refdate.isoformat())
    print("==> cmd: {}".format(cmd))
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    return stdout.split()


def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--days', default='7', help='workspace which are older than this days will be deleted.')
    parser.add_argument('--pathregex', required=True, help='Only workspaceroot path that match this regex will be removed.')
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--dryrun', action='store_true', default=False)
    args = parser.parse_args()
    return args


def set_logger(arg):
    if arg.debug:
        fmt = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
        level = logging.DEBUG
    else:
        fmt = "%(levelname)s [%(asctime)s] - [%(module)s]: %(message)s"
        level = logging.INFO
    logging.basicConfig(format=fmt)
    LOGGER.setLevel(level)


if __name__ == '__main__':
    sys.exit(main())

