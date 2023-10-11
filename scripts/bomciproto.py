#!/usr/bin/env python

'''
SPEC
====
    https://wiki.ith.intel.com/display/tdmaInfra/dmx+bom+ci+-+Phase+1

'''
import re
import logging
import os
import urllib, urllib2
import sys
from argparse import ArgumentParser
from getpass import getpass
import csv

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import run_command
import dmx.abnrlib.workspace
import dmx.ecolib.ecosphere

def main():
    parser = ArgumentParser()
    parser.add_argument('--debug', required=False, action='store_true', default=False, help="More verbose by printing out debugging messages.")
    parser.add_argument('-n', '--dryrun', required=False, action='store_true', default=False, help="dry run.")
    parser.add_argument('-i','--ip', required=True, help="ICM Variant.")
    parser.add_argument('-m','--milestone', required=True, help="Milestone.")
    parser.add_argument('-d','--deliverables', default=None, nargs='+', help="ICM Libtypes.")
    parser.add_argument('--desc', required=True, help="Description to be used when checking-in files. (Please use single-quote to quote the description here)")
    parser.add_argument('--hook', required=False, default=None, help="An executable script.")
    parser.add_argument('--hierarchy', required=False, default=False, action='store_true', help="Run hierarchically when provided.")
    args = parser.parse_args()
   
    if args.debug:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)         


    ### Get all necessary variables from environment 
    family = os.getenv("DB_FAMILY", '')
    if not family:
        logger.error("Environment Variable (DB_FAMILY) is not defined!")
        logger.error("Please make sure you are in a correct arc project bundle.")
        sys.exit(1)
    thread = os.getenv("DB_THREAD", '')
    if not thread:
        logger.error("Environment Variable (DB_THREAD) is not defined!")
        logger.error("Please make sure you are in a correct arc project bundle.")
        sys.exit(1)

    ### Mixture between pure-libtypes + views_ are not allowed
    if args.deliverables:
        libtype_exists = False
        view_exists = False
        for d in args.deliverables:
            if d.startswith('view_'):
                view_exists = True
            else:
                libtype_exists = True
        if libtype_exists and view_exists:
            logger.error("Mixture of pure-deliverables and views are not supported.")
            logger.error("--deliverables has to be pure icm deliverables, or pure views.")
            sys.exit(1)


    eco = dmx.ecolib.ecosphere.EcoSphere()
    family = eco.get_family()
    ip = family.get_ip(args.ip)

    exitcode = 0
    
    ##########################################
    ### Running IPQC 
    logger.info("Running ipqc command ...")
    ipqccmd = 'ipqc run-all -i {} -m {} '.format(args.ip, args.milestone)
    if not args.hierarchy:
        ipqccmd += ' --no-hierarchy '
    if args.deliverables:
        ipqccmd += ' -d {} '.format( ' '.join([x for x in args.deliverables]) )
    logger.info(">>> {}".format(ipqccmd))
    if not args.dryrun:
        exitcode = os.system(ipqccmd)
    if exitcode != 0:
        logger.error("ipqc has error and exited with exitcode({}). Program terminated.".format(exitcode))
        sys.exit(exitcode)

    ##########################################
    ### Running HOOK
    if args.hook:
        logger.info("Running hook command ...")
        if not args.dryrun:
            exitcode = os.system(args.hook)
    else:
        logger.info("No hook provided. Skipping this step.")
        exitcode = 0
    if exitcode != 0:
        logger.error("hook command has error and exited with exitcode({}). Program terminated.".format(exitcode))
        sys.exit(exitcode)


    ##########################################
    ### Check-IN
    cmds = []
    cmdprefix = "icmp4 submit -d '{}' ".format(args.desc)

    if args.hierarchy:
        variantspec = '*'
    else:
        variantspec = args.ip

    if not args.deliverables:
        ### Check-in with NO --deliverables
        cmds.append("{} '{}/...'".format(cmdprefix, variantspec))

    elif args.deliverables[0].startswith("view_"):
        ### check-in with --deliverables of view_*
        dobjs = ip.get_deliverables(milestone=args.milestone, views=args.deliverables)
        for dobj in dobjs:
            cmds.append("{} '{}/{}/...'".format(cmdprefix, variantspec, dobj.name))
    else:
        ### check-in with --deliverables of pure icm-libtypes
        for d in args.deliverables:
            cmds.append("{} '{}/{}/...'".format(cmdprefix, variantspec, d))


    logger.info("Checking-in files ...")
    for cmd in cmds:
        logger.info(">>> {}".format(cmd))
        if not args.dryrun:
            os.system(cmd)




if __name__ == '__main__':
    logger = logging.getLogger()
    main()


