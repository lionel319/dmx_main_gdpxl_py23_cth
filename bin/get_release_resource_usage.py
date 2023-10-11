#!/usr/bin/env python

# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/get_release_resource_usage.py#1 $
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
import time


### in-house libraries
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.arcutils
import dmx.utillib.utils


### Global Varianbles
LOGGER = logging.getLogger()


def main():

    args = _add_args()
    _setup_logger(args)

    upload_data(args)



def upload_data(args):
    a = dmx.utillib.arcutils.ArcUtils()
    data = a.get_resource_usage(logfile=args.logfile)
    cmd = 'friday karen_upload -project {} -ip {} -cell none -libtype {} -flow TNR -stage {} -milestone {} -memory {} -cputime {} -processes {} -threads {} -runtime {} '.format(
        args.project, args.variant, args.libtype, args.thread, args.milestone, data['memory'], data['cputime'], data['processes'], data['threads'], data['runtime'])

    LOGGER.info('Sleep for delay time = {} ...'.format(args.delay))
    time.sleep(int(args.delay))

    LOGGER.info("Running ==> {}".format(cmd))
    if not args.dryrun:
        os.system(cmd) 
    else:
        LOGGER.info("Skip execution as dryrun mode activated.")

    
def _add_args():
    ''' Parse the cmdline arguments '''
    parser = argparse.ArgumentParser()

    parser.add_argument('--logfile', required=True, help='The stdout.txt file of the arc job.')
    parser.add_argument('--project', required=True, help='Project.')
    parser.add_argument('--variant', required=True, help='Variant.')
    parser.add_argument('--libtype', required=True, help='Libtype.')
    parser.add_argument('--milestone', required=True, help='Milestone.')
    parser.add_argument('--thread', required=True, help='Thread.')
    parser.add_argument('--delay', required=False, default='0', help='Delay for specific time(sec) before extract the data. Default 0sec')

    parser.add_argument('--dryrun', required=False, default=False, action='store_true', help='Dry run.')
    parser.add_argument('--debug', required=False, default=False, action='store_true', help='Print out debugging statements.')

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

