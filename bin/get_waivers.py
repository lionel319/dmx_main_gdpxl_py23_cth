#!/usr/bin/env python

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
from dmx.tnrlib.dashboard_query2 import DashboardQuery2
from dmx.utillib.utils import run_command

def main():
    parser = ArgumentParser()
    parser.add_argument('--debug', required=False, action='store_true', default=False, help="More verbose by printing out debugging messages.")
    parser.add_argument('-p','--project', dest='project', required=True, help="ICM Project")
    parser.add_argument('-i','--ip', dest='variant', required=True, help="ICM Variant.")
    parser.add_argument('-d','--deliverable', dest='libtype', required=False, default=None, help="ICM Libtype.")
    parser.add_argument('-b','--bom',  dest='config',  required=True, help="ICM Composite Config")
    parser.add_argument('--deliverables-filter', dest='libtypes_filter', nargs='+', help="Libtypes filter. Script will return only waivers of libtypes specified in this argument.")
    parser.add_argument('--ips-filter', dest='variants_filter', nargs='+', help="Variants filter. Script will return only waivers of variants specified in this argument.")
    parser.add_argument('--forrel', dest='forrel', required=False, default=False, action='store_true',  help="If this option is turned on, the generated waiver file will be in the format that is readily available to be used for 'abnr release*' commands.")
    args = parser.parse_args()
   
    if args.debug:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)         


    cli = ICManageCLI()
    print args.libtypes_filter
    print args.variants_filter

    global d
    global username
    global password
    username = 'guest'
    password = 'guest'

    '''
    username = get_password_from_passwordfile('.get_waivers.username')
    if not username:
        logger.info("Script needs to login to Splunk, please provide your Altera(Not PICE) username.") 
        username = raw_input("Altera UserName:")

    password = get_password_from_passwordfile('.get_waivers.password')
    if not password:
        if os.getenv("PASSWORD"):
            password = os.getenv("PASSWORD")
        else:       
            logger.info("Script needs to login to Splunk, please provide your Splunk password.") 
            password = getpass()
    '''
    d = DashboardQuery2(userid=username, password=password)      

    
    waiver_file = os.path.abspath("./{}_{}_{}_{}_waivers.csv".format(args.project, args.variant, str(args.libtype), args.config))
    with open(waiver_file, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        if args.forrel:
            writer.writerow(['#Variant', 'Flow', 'Subflow', 'Waiver-reason', 'Error'])
        else:
            writer.writerow(['Project', 'Variant', 'Libtype', 'Topcell', 'Flow-Libtype', 'Releaser','Flow','Subflow','Waiver-creator','Waiver-reason','Error'])

    if args.libtype:
        logger.info("Getting waivers for {}/{}:{}@{} ...".format(args.project, args.variant, args.libtype, args.config))
        waivers = get_waived_errors_from_pvlc(args.project, args.variant, args.libtype, args.config)
        write_to_csv(waivers, waiver_file, args.libtypes_filter, args.forrel)
    else:
        logger.info("Loading configuration tree ...")
        cf = ConfigFactory.create_from_icm(args.project, args.variant, args.config)
        for c in cf.flatten_tree():
            logger.info("Working on {} ...".format(c))
            if c.is_released():
                if c.is_composite():
                    libtype = "None"
                else:
                    libtype = c.libtype
                project = c.project
                variant = c.variant
                config = c.config
                if args.variants_filter == None or variant in args.variants_filter:
                    if args.libtypes_filter == None or libtype in args.libtypes_filter or libtype == "None":
                        try:
                            waivers = get_waived_errors_from_pvlc(project, variant, libtype, config)
                            write_to_csv(waivers, waiver_file, args.libtypes_filter, args.forrel)
                        except Exception as e:
                            logger.warning("Problem getting waived errors for {}/{}:{}@{} !".format(project, variant, libtype, config))
                            logger.warning(str(e))
                    else:
                        logger.info("- skipped.")
                else:
                    logger.info("- skipped.")

    logger.info("Output file generated at {}".format(waiver_file))


def get_password_from_passwordfile(filename='.get_waivers.password'):
    '''
    | Passing around password thru the command line is not a very wise idea (as
    | (as it will be publickly published when you do it thru ``arc submit``. :p )
    | So, to work around that, we get the password from ``/home/<user>/.password``
    | Please make sure this file is having a ``0700`` mode for security purposes. *DUH...*
    '''
    try:
        #filename = '/home/{}/.password'.format(os.getenv("USER"))
        filepath = '/nfs/site/home/{}/{}'.format(os.getenv("USER"), filename)
        line = open(filepath).read()
        return line.strip()
    except:
        return ''


def write_to_csv(waivers, waiver_file, libtypes_filter, forrel):
    '''
    waivers == 'Project', 'Variant', 'Libtype', 'Topcell', 'Flow-Libtype', 'Releaser','Flow','Subflow','Waiver-creator','Waiver-reason','Error'
    '''
    with open(waiver_file, 'a') as csvfile:
        writer = csv.writer(csvfile)
        for p, v, b, t, l, r, f, s, wc, wr, e in waivers:
            if libtypes_filter == None or str(l) in libtypes_filter or str(b) in libtypes_filter:
                if forrel:
                    if not s:
                        s = '*'
                    writer.writerow([v, f, s, wr, e])
                else:
                    writer.writerow([p, v, b, t, l, r, f, s, wc, wr, e])
          

def get_waived_errors_from_pvlc(project, variant, libtype, config):
    ''' Get all the waived errors for a given project/variant@config.
    Return it in a list-of-list:-
    [
        [project, variant, libtype, releaser, flow, subflow, waiver-creator, waiver-reason, error],
        [project, variant, libtype, releaser, flow, subflow, waiver-creator, waiver-reason, error],
        ...   ...   ...
    ]
    '''
    rid = d.get_request_id_from_pvlc(project, variant, libtype, config)
    search = 'search index=qa request_id={} status=waived | rename user as releaser | table project, variant, libtype, flow-topcell, flow-libtype, releaser, flow, subflow, waiver-creator, waiver-reason, error'.format(rid)    
    retlist = []
    result = d.run_query(search)
    for res in result:
        p = res['project']
        v = res['variant']
        b = res['libtype']
        t = res['flow-topcell']
        l = res['flow-libtype']
        r = res['releaser']
        f = res['flow']
        s = res['subflow']
        try:
            wc = res['waiver-creator']
        except:
            wc = ""
        try:            
            wr = res['waiver-reason']
        except:
            wr = ""
        e = res['error']
        retlist.append([p, v, b, t, l, r, f, s, wc, wr, e])

    return retlist

def get_request_id_from_pvlc(project, variant, libtype, config):
    ''' Get the request_id of a given project/variant:libtype@config.
    libtype should be set to 'None' if it is for a variant.
    Return '' if all else fail.
    '''
    try:
        d = DashboardQuery2(userid=username, password=password)      
        search = 'search index=qa project="{}" variant="{}" libtype="{}" release_configuration="{}" | table request_id, project, variant, libtype, release_configuration'.format(project, variant, libtype, config)
        result = d.run_query(search)
        logger.debug(result)
        id = result[0]['request_id']
        return id
    except Exception as e:
        logger.error("Fail finding request_id for {}/{}:{}@{}".format(project, variant, libtype, config))
        logger.error(e)
        raise
        return ''

if __name__ == '__main__':
    logger = logging.getLogger()
    main()


