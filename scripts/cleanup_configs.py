#!/usr/intel/pkgs/python3/3.9.6/bin/python3

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/scripts/cleanup_configs.py#2 $
$Change: 7667210 $
$DateTime: 2023/06/19 19:18:22 $
$Author: lionelta $

Description: API functions which interacts with Gatekeeper
'''
from __future__ import print_function
import UsrIntel.R1
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

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
   
    configs = find_old_configs(args)
    print("Configs to be deleted: {}".format(configs))

    delete_configs(args, configs)

def delete_configs(args, configs):
    print(configs)
    for config in configs:
        print("Deleting {} ...".format(config))
        cmd = 'gdp delete {}'.format(config)
        if args.dryrun:
            cmd += ' --pretend'
        print("==> cmd: {}".format(cmd))
        os.system(cmd)


def find_old_configs(args):
    refdate = datetime.date.today() - datetime.timedelta(days=int(args.days))
    print(refdate.isoformat())
    cmd = 'gdp find --type config --columns path "path:~{} && created:<{}"'.format(args.pathregex, refdate.isoformat())
    print("==> cmd: {}".format(cmd))
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    return stdout.split()


def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--days', default='7', help='Config (created date) which are older than this days will be deleted.')
    parser.add_argument('--pathregex', required=True, help='Only path name that match this regex will be removed.')
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

