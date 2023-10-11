#!/usr/bin/env python

'''
This script 
- downloads the Checker xlsx file (prepared by Vandana)
- extract the infomation from the excel file
- generate the respective json file

Example of the Checkers xlsx (input) file:-
    http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/List%20of%20Checks.xlsx

Author: Lionel Tan Yoke-Liang
Date: 28 April 2016

'''


import urllib2
import logging
import tempfile
from argparse import ArgumentParser
import sys
import os
import json
from pprint import pprint
from abnrlib.icm import ICManageCLI

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
from ecolib import dataloader


def main():

    args = parse_arguments()

    ### Setting logging level 
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=loglevel)


    family = get_family_name_for_thread(args.thread)
    logging.info("Family: {}".format(family))

    projects = get_projects_from_family(family)
    logging.info("Projects: {}".format(projects))

    data = extract_variant_type_info_from_icm(projects)

    filepath = get_db_filepath(args.thread)
    logging.info("output db filepath: {}".format(filepath))
    generate_json_file(data, filepath)


def get_db_filepath(thread):
    family = get_family_name_for_thread(thread)
    return os.path.join(rootdir, 'data', family, thread, 'variantypes.json')

def get_projects_from_family(family):
    dbfile = os.path.join(rootdir, 'data', 'mappers', 'projectsmap.json')
    with open(dbfile) as f:
        data = json.load(f)
    return [project for project in data if data[project] == family]


def get_family_name_for_thread(thread):
    dbfile = os.path.join(rootdir, 'data', 'mappers', 'threadsmap.json')
    with open(dbfile) as f:
        data = json.load(f)
    return data[thread]


def extract_variant_type_info_from_icm(projects):
    '''
    '''
    logging.info("Extracting variant property from icm ...")
    data = {}
    icm = ICManageCLI()
    for project in projects:
        if not icm.project_exists(project):
            continue
        for variant in icm.get_variants(project):
            prop = icm.get_variant_properties(project, variant)
            logging.debug("{}/{}".format(project, variant))
            logging.debug("- PROP: {}".format(prop))
            if 'Variant Type' in prop:
                data[variant] = {'project': project, 'type': prop['Variant Type'], 'owner': prop.get('Owner', '')}
    return data


def generate_json_file(data, outfile):
    '''
    '''
    
    logging.info("Generating json db file ...")
    os.system('mkdir -p {}'.format(os.path.dirname(os.path.abspath(outfile))))
    with open(outfile, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
    logging.info("Successfully generated {}".format(outfile))



def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('-t', '--thread', required=True, help='The thread name')
    parser.add_argument('--debug', required=False, default=False, action='store_true', help='Turn on debugging mode for more verbose messages.')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    logger = logging.getLogger()
    main()
