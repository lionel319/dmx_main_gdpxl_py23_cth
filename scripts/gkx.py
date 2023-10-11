#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/scripts/gkx.py#2 $
$Change: 7480675 $
$DateTime: 2023/02/12 23:38:21 $
$Author: lionelta $

Description: API functions which interacts with Gatekeeper
'''
from __future__ import print_function

import os
import logging
import sys
import re
import argparse
from pprint import pprint,pformat
import textwrap

LIB = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.gkutils
import dmx.utillib.git

LOGGER = logging.getLogger()

def main():
    args = get_args()
    set_logger(args)
    if args.debug:
        pprint(args)
        print(args.__dict__)
    
    gk = dmx.utillib.gkutils.GkUtils()
    git = dmx.utillib.git.Git()
    if args.func == 'mtrepo':
        ret = git.get_master_git_repo_path(project=args.project, variant=args.ip, libtype=args.deliverable, library=args.bom)
        print(ret)
    elif args.func == 'mtrel':
        ret = git.get_release_git_repo_path(project=args.project, variant=args.ip, libtype=args.deliverable, release=args.bom)
        print(ret)
    elif args.func == 'getpvll':
        ret = git.get_pvll_from_git_repo_name(reponame=args.reponame)
        print(ret)

def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subpar = parser.add_subparsers()
    
    mtrepo = subpar.add_parser('get_repo_path', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='Given the project/ip/deliverable/bom, return the git master repo fullpath.')
    mtrepo.add_argument('--debug', action='store_true', default=False)
    mtrepo.add_argument('--project', '-p', required=True, help='project')
    mtrepo.add_argument('--ip', '-i', required=True, help='ip')
    mtrepo.add_argument('--deliverable', '-d', required=True, help='deliverable')
    mtrepo.add_argument('--bom', '-b', required=True, help='bom')
    mtrepo.set_defaults(func='mtrepo')

    mtrel = subpar.add_parser('get_rel_path', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='Given the project/ip/deliverable/bom, return the git release repo fullpath.')
    mtrel.add_argument('--debug', action='store_true', default=False)
    mtrel.add_argument('--project', '-p', required=True, help='project')
    mtrel.add_argument('--ip', '-i', required=True, help='ip')
    mtrel.add_argument('--deliverable', '-d', required=True, help='deliverable')
    mtrel.add_argument('--bom', '-b', required=True, help='bom')
    mtrel.set_defaults(func='mtrel')

    getpvll = subpar.add_parser('get_pvll', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='Given the git repo name(L1234567-a0 -or- L1234566-a0-22ww40a), return the project/variant/libtype/library.')
    getpvll.add_argument('--debug', action='store_true', default=False)
    getpvll.add_argument('--reponame', '-r', required=True, help='reponame')
    getpvll.set_defaults(func='getpvll')




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

