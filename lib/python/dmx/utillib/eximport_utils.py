#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/eximport_utils.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Utility functions that are common across dmx ip iport/export but generic
enough that they don't fit in elsewhere

Author: Lee Cartwright

Copyright (c) Altera Corporation 2014
All rights reserved.
'''

from builtins import next
import socket
import getpass
import os
import sys
import pwd
import time
import re
import threading
import subprocess
import argparse
import datetime as utildt
from contextlib import contextmanager
from altera.decorators import memoized
import dmx.utillib.intel_dates
import dmx.utillib.admin
import logging
import json
import tempfile
import signal
from functools import reduce

logger = logging.getLogger(__name__)

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.errorlib.exceptions import *
import dmx.utillib.utils



def set_dmx_workspace(stagingws):
    os.environ['DMX_WORKSPACE'] = stagingws
    return True 

def get_format_name(service):
    '''
    service = export/import
    '''
    if service != 'export' and service != 'import':
        raise Exception('Services \'{}\' not supportd'.format(service))
    DMXDATA_ROOT = os.environ.get('DMXDATA_ROOT')
    DB_FAMILY = os.environ.get('DB_FAMILY').capitalize()
    path = '{}/{}/{}/'.format(DMXDATA_ROOT, DB_FAMILY, service)
    if not os.path.exists(path):
        raise Exception('{} does not exists. Please contact psgicmsupport@intel.com for more information.'.format(path))
    format_name = next(os.walk(path))[1]
    return format_name

def get_config_file(service, format, name, ext):
    '''
    get_config_file('import', 'feonly', 'rtl', 'mapping')
    >>> '/p/psg/flows/common/dmxdata/Falcon/import/feonly/rtl.mapping.tcsh'
    get_config_file('export', 'backend', 'rules', 'conf')
    >>> '/p/psg/flows/common/dmxdata/Falcon/export/backend/rules.conf"
    '''
    DMXDATA_ROOT = os.environ.get('DMXDATA_ROOT')
    DB_FAMILY = os.environ.get('DB_FAMILY').capitalize()
    if name == 'rules':
        config_path = '{}/{}/{}/{}/{}.{}'.format(DMXDATA_ROOT, DB_FAMILY, service, format, name, ext)
    else:
        config_path = '{}/{}/{}/{}/{}.{}.tcsh'.format(DMXDATA_ROOT, DB_FAMILY, service, format, name, ext)
    if not os.path.exists(config_path):
        raise Exception('Config file {} does not exists.'.format(config_path)) 
    return config_path

def parse_rules_file(rulesfile):
    '''
    ./rules.conf content
    ======================
    MAPPINGS=rtl lint reldoc
    GENERATORS=rtl lint
    XXX=a b c
     
    parse_rules_file('./default.conf')
    >>> {
        "MAPPINGS": ["rtl", "lint", "reldoc"],
        "GENERATORS": ["rtl", "lint"],
        "XXX": ["a", "b", "c"]
    }
    '''
    mappings = []
    generators = []
    source = ''
    config_data = {}

    for line in open(rulesfile):
        key = line.strip().split('=', 1)[0]
        value = line.strip().split('=', 1)[1]
        if key == 'MAPPINGS':
            config_data['MAPPING'] = value.split()
        elif key == 'GENERATORS':
            config_data['GENERATORS'] = value.split()

    return config_data

def expand_file(file, expand_str):
    '''
    Create a temporary file which replace the expandable variable from file
    Copy from https://stackoverflow.com/questions/6116978/how-to-replace-multiple-substrings-of-a-string
    '''
    fd, path =tempfile.mkstemp() 
    with os.fdopen(fd, 'w+') as tmp:
        for line in open(file):
            tmp.write(reduce(lambda a, kv: a.replace(*kv), iter(expand_str.items()), line))

    return path

def run_mapper_and_generator_file(service, format, deliverables, expandstr):
    '''
    Given service(import/export), format, deliverable
    Run mapper and geenrator file if exists
    '''

    ruleconf_file = get_config_file(service, format, 'rules', 'conf')
    logger.info('Rules config file : {}'.format(ruleconf_file))
    rulefile_data = parse_rules_file(ruleconf_file)

    # filter only deliverable in rule file 
    if deliverables:
        mapping_deliverables = [x for x in deliverables if x in rulefile_data.get('MAPPING')]
        generator_deliverables = [x for x in deliverables if x in rulefile_data.get('GENERATORS')]
    else:
        mapping_deliverables = rulefile_data.get('MAPPING')
        generator_deliverables = rulefile_data.get('GENERATORS')

    if not mapping_deliverables:
        logger.warning('No valid deliverable exist in {}. Abort.'.format(format))

    # Run mapping file
    run_excutable_file(service, format, mapping_deliverables, expandstr, 'mapping')
    # Run generator file
    run_excutable_file(service, format, generator_deliverables, expandstr, 'generator')


def run_excutable_file(service, format, deliverables, expandstr, filetype):
    '''
    filetype = mapping/generators
    Run file if exists
    '''

    for deliverable in deliverables:
        deliverable_file = get_config_file(service, format, deliverable, filetype)
        expanded_file = expand_file(deliverable_file, expandstr)
        logger.debug('Expanded file name: {}'.format(expanded_file))
        logger.info('Deliverable {} {} file : {}'.format(deliverable, filetype, deliverable_file))
        #Modify file to executable
        os.chmod(expanded_file, 0o755)

        logger.info('Running : {}'.format(deliverable_file))
        logger.debug('Running : {}'.format(expanded_file))
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(expanded_file)
        if exitcode:
            logger.error('Exitcode: {}. Stderr: {}'.format(exitcode, stderr))
            raise Exception('Error running \'{}\''.format(expanded_file))

        #logger.info(stdout)

