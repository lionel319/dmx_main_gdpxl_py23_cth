#!/usr/bin/env python

import re
import logging
import os
import urllib, urllib2
import sys
from argparse import ArgumentParser
from getpass import getpass
import csv
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import run_command
from dmx.abnrlib.flows.workspace import Workspace

def main():
    parser = ArgumentParser()
    parser.add_argument('--debug', required=False, action='store_true', default=False, help="More verbose by printing out debugging messages.")
    parser.add_argument('-p','--project', dest='project', required=True, help="ICM Project")
    parser.add_argument('-i','--ip', dest='variant', required=True, help="ICM Variant.")
    parser.add_argument('-b','--bom',  dest='config',  required=True, help="ICM Composite(variant) Config")
    parser.add_argument('-m','--milestone',  dest='milestone',  required=True, help="Milestone")
    parser.add_argument('-t','--thread',  dest='thread',  required=True, help="Thread")
    parser.add_argument('-d','--deliverables',  dest='libtypes',  nargs='+', required=True, help="Deliverables to be checked (separated by space)")

    args = parser.parse_args()
   
    if args.debug:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)         

    ### Final Results 
    DATA = {}

    cf = ConfigFactory.create_from_icm(args.project, args.variant, args.config)
    all_variants = [c for c in cf.flatten_tree() if c.is_composite()]

    for c in all_variants:
        DATA[c.variant] = {}
        for l in args.libtypes:
            w = Workspace()
            w.check_action(c.project, c.variant, 'dev', args.milestone, args.thread, libtype=l, logfile=None, dashboard=None, celllist_file=None, nowarnings=True, waiver_file=[], preview=False, views=None)
            DATA[c.variant][l] = w.errors
   

    report_results(DATA)



def report_results(DATA):
    print "==============================================================="
    print "==============================================================="
    print "==============================================================="
    print "+-------------------------+"
    print "| Reporting Final Results |"
    print "+-------------------------+"
    for variant in DATA:
        for libtype in DATA[variant]:
            if not DATA[variant][libtype]['unwaived']:
                print "{}/{} : PASS".format(variant, libtype)
            else:
                print "{}/{} : FAIL".format(variant, libtype)
                pprint(DATA[variant][libtype]['unwaived'])


if __name__ == '__main__':
    logger = logging.getLogger()
    main()


