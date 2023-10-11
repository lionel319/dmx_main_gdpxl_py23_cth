#!/usr/intel/pkgs/python3/3.10.8/bin/python3
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/scripts/get_checkers.py#2 $
$Change: 7612714 $
$DateTime: 2023/05/15 01:46:37 $
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

LIB = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.ecolib.ecosphere

LOGGER = logging.getLogger()

def main():
    args = get_args()
    set_logger(args)
    if args.debug:
        pprint(args)
        print(args.__dict__)
 
    os.environ['DMXDATA_ROOT'] = '/p/psg/flows/common/dmxdata/latestdev'
    eco = dmx.ecolib.ecosphere.EcoSphere(workspaceroot='dummy')
    family = eco.get_family_for_thread(args.thread)
    deliverable = family.get_deliverable(args.deliverable)
    #get_checkers(self, flow_filter = '', subflow_filter = '', checker_filter = '', milestone = '99', roadmap = '', iptype_filter='', prel_filter=''):
    checkers = deliverable.get_checkers(milestone=args.milestone, flow_filter=args.flow_filter)

    report(checkers, args)

def report(checkers, args):
    retval = []
    if args.json:
        for c in checkers:
            retval.append({'flow':c.flow, 'subflow':c.subflow})
        print(retval)
    elif args.prettyjson:
        for c in checkers:
            retval.append({'flow':c.flow, 'subflow':c.subflow})
        pprint(retval)

    else:
        pprint(checkers)

def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
   
    parser.add_argument('--thread', '-t', required=True)
    parser.add_argument('--milestone', '-m', required=True)
    parser.add_argument('--deliverable', '-d', required=True)
    parser.add_argument('--flow_filter', '-ff', default='', required=False)

    ### Output format modifier
    parser.add_argument('--json', action='store_true', default=False)
    parser.add_argument('--prettyjson', action='store_true', default=False)
    parser.add_argument('--debug', action='store_true', default=False)

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

