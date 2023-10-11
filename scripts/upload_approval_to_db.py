#! /usr/bin/env python

import logging
import logging.config
import argparse
import os
import subprocess
import sys
import re
import unicodedata
import dmx.abnrlib.flows.dmxwaiver
import csv
import datetime
import copy

def main():
    '''
    This script is to upload csv mapping file (dmx to hsdes) to db.

    csv format
    ----------
    thread,family,release
    FM6revA0,hw.falcon_mesa,fm6-a0
    '''
    args = _add_args()
    logger = _setup_logger(args)
    csvfile = args.csv

    logger.info('Get data from csv.')
    mapping_data = get_data_from_csv(csvfile)  

    logger.info('Update dmx thread mapping to hsdes family and release.')
   
    if args.dev:
        mongo = dmx.abnrlib.flows.dmxwaiver.DmxWaiver('test')
    else:
        mongo = dmx.abnrlib.flows.dmxwaiver.DmxWaiver()

    mongo.insert_hsdes_mapping_data(mapping_data)

    dt =  mongo.get_hsdes_mapping_data()
 #   insert_to_mapping_collection(mapping_data)
    logger.info('Update succesfully.')



def get_data_from_csv(csvfile):
    hsdes_mapping = {}

    with open(csvfile, mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            thread = rows[0]
            family = rows[1]
            release = rows[2]
            stepping = rows[3]
            ms1 = rows[4]
            ms2 = rows[5]
            ms3 = rows[6]
            ms4 = rows[7]
            ms5 = rows[8]

            if not hsdes_mapping.get(thread):
                hsdes_mapping[thread] = {}  
            hsdes_mapping[thread]['family'] = family 
            hsdes_mapping[thread]['release'] = release
            hsdes_mapping[thread]['stepping'] = stepping
            hsdes_mapping[thread]['ms1'] = ms1
            hsdes_mapping[thread]['ms2'] = ms2
            hsdes_mapping[thread]['ms3'] = ms3
            hsdes_mapping[thread]['ms4'] = ms4
            hsdes_mapping[thread]['ms5'] = ms5

    return hsdes_mapping

def insert_to_mapping_collection(mapping_data):
    csv_mapping_data = copy.deepcopy(mapping_data)
    mapping_data['updated_by'] = os.environ.get('USER')
    mapping_data['date'] = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') 
    mongo.db.hsdes_mapping.update(csv_mapping_data,  {'$set':mapping_data}, upsert=True)


def _add_args():
    ''' Parse the cmdline arguments '''
    # Simple Parser Example
    parser = argparse.ArgumentParser(description="Desc")
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument("-d", "--debug", action='store_true', help="debug level")
    optional.add_argument("--dev", action='store_true', help="upload to dev server")
    required.add_argument("-c", "--csv", required='True', help="csv file contail dmx/hsdes mappping")
    args = parser.parse_args()
    return args

def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level, stream=sys.stdout)
    logger = logging.getLogger(__name__)
    return logger

if __name__ == '__main__':
    sys.exit(main())

   
