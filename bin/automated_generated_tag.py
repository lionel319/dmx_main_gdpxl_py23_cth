#!/usr/bin/env python

# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/automated_generated_tag.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""

The goal is to have a wrapper icm configuration that holds all the latest REL libtype configuration.

With that available, we would be able to make use of that wrapper configuration to

refer to a list of latest stable design
make use of the info to do other automation.
Our intention is not to strike for 100% accuracy, but to achieve an acceptable level of accuracy so that other automation is made possible with this info.

https://wiki.ith.intel.com/pages/viewpage.action?pageId=1259093795

For more info please visit https://jira.devtools.intel.com/browse/PSGDMX-1594


"""

### std libraries
import os
import sys
import logging
import argparse
from datetime import datetime
import time
import json
import xml.etree.ElementTree as ET
import ConfigParser
import csv
import re

### in-house libraries
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.agtutils

### Global Varianbles
LOGGER = logging.getLogger()
EXE = os.path.abspath(__file__)
WEBLIB = os.path.join(LIB, 'dmx', 'tnrlib')


def main():

    args = _add_args()
    _setup_logger(args)

    return args.func(args)

def update_latest_variant(args):
    '''Update latest variant every time a libtype is release'''

    # check if pvc exists, return error if False     
    icm = ICManageCLI()
    if not icm.config_exists(args.project, args.ip, args.bom, args.deliverable):
        LOGGER.error('Project: {}, Variant: {}, Config: {} not found, Libtype: {}. Please use a correct project, ip and bom'.format(args.project,args.ip,args.bom,args.deliverable))
        return 1

    agt =  dmx.utillib.agtutils.AgtUtils()

    ### For handling agt_latest_FM4revA_1.0 (with milestone)
    tagname = agt.get_latest_tagname(args.bom)
    agt.force_update_variant_config(args.project, args.ip, args.deliverable, args.bom, tagname)

    ### For handling agt_latest_FM4revA (without milestone)
    tagname = agt.get_latest_tagname(args.bom, with_milestone=False)
    agt.force_update_variant_config(args.project, args.ip, args.deliverable, args.bom, tagname)


def update_latest_wrapper(args):
    '''Update latest wrapper when there are new variant latest_tag which is not added into the wrapper config'''

    # check if pvc exists, return error if False     
    icm = ICManageCLI()
   # if not icm.config_exists(args.project, args.ip, args.bom):
   #     LOGGER.error('Project: {}, Variant: {}, Config: {} not found. Please use a correct project, ip and bom'.format(args.project,args.ip,args.bom))
   #     sys.exit()
    
    agt =  dmx.utillib.agtutils.AgtUtils()

    # Read file to list if exists
    if args.ignore_variant_list:
        # skip '#', empty line, and space line
        lineList = [line.rstrip('\n') for line in open(args.ignore_variant_list) if not re.search('^#',line) and not re.search('^$',line) and not re.search('^\s*$',line) ]
 
    for p in args.source_project:
        variants = icm.get_variants(p)
        for ea_var in variants:
            if icm.config_exists(p, ea_var, args.bom):

                # skip if match ifself
                if p == args.project and ea_var == args.ip: 
                    LOGGER.debug('{}/{} match itself, skip... '.format(args.project, args.ip))
                    continue

                # skip if match ignore_variant_list
                if ea_var in lineList: 
                    LOGGER.debug('{} exists in ignore variant list, skip... '.format(ea_var))
                    continue

                LOGGER.debug('{}/{}@{} found. Update latest wrapper... '.format(p, ea_var, args.bom))
                agt.force_update_wrapper_config(args.project, args.ip, p, ea_var, args.bom)



    
def _add_args():
    ''' Parse the cmdline arguments '''
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='sub-command help')

    # update_latest_variant subcommand parser
    parser_update_latest_variant = subparser.add_parser('update_latest_variant', help='update_latest_variant help')
    parser_update_latest_variant.add_argument('-p', '--project', required=True, help="The icm project.")
    parser_update_latest_variant.add_argument('-i', '--ip', required=True, help="The icm ip.")
    parser_update_latest_variant.add_argument('-d', '--deliverable', required=True, help="The icm deliverable.")
    parser_update_latest_variant.add_argument('-b', '--bom', required=True, help="The icm bom.")
    parser_update_latest_variant.add_argument('--debug', required=False, default=False, action='store_true', 
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_update_latest_variant.set_defaults(func=update_latest_variant)

    # update_latest_wrapper subcommand parser
    parser_update_latest_wrapper = subparser.add_parser('update_latest_wrapper', help='update_latest_wrapper help')
    parser_update_latest_wrapper.add_argument('-p', '--project', required=True, help="The icm project.")
    parser_update_latest_wrapper.add_argument('-i', '--ip', required=True, help="The icm ip.")
    parser_update_latest_wrapper.add_argument('-b', '--bom', required=True, help="The icm bom.")
    parser_update_latest_wrapper.add_argument('--ignore_variant_list', required=False, help="Filelist of ignored variants.")
    parser_update_latest_wrapper.add_argument('--source_project', nargs='+', required=True, default=False, help='The source project')
    parser_update_latest_wrapper.add_argument('--debug', required=False, default=False, action='store_true', 
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_update_latest_wrapper.set_defaults(func=update_latest_wrapper)



    args = parser.parse_args()



    return args

def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)


if __name__ == "__main__":
    sys.exit(main())

