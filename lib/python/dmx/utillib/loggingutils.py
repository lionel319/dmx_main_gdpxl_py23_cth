#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/loggingutils.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to instantiate connection to servers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
import re
from pprint import pprint
import glob
import subprocess

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.utillib.utils
from datetime import date, datetime
from dmx.utillib.utils import run_command
from logging.handlers import TimedRotatingFileHandler


def setup_logger(name=None, level=logging.INFO):
    ''' Setup the logger for the logging module.

    If this is a logger for the top level (root logger), 
        name=None
    else
        the __name__ variable from the caller should be passed into name
    
    Returns the logger instant.
    '''

    if name:
        LOGGER = logging.getLogger(name)
    else:
        LOGGER = logging.getLogger()

    if level <= logging.DEBUG:
        fmt = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
    else:
        fmt = "%(levelname)s [%(asctime)s] - [%(module)s]: %(message)s"

    logging.basicConfig(format=fmt)
    LOGGER.setLevel(level)

    return LOGGER

def get_console_handler(levelname, level):
    '''
    Create a stream handler which output to stderr(default) with specific logging level
    '''
    if level == logging.DEBUG:
        FORMATTER = logging.Formatter("{} [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(levelname))
    else:
        FORMATTER = logging.Formatter("{}: %(message)s".format(levelname))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(FORMATTER)
    return console_handler

def get_file_handler(levelname, log_location):
    '''
    Create a file handler with timed rotating feature with specific logging level
    '''
    FORMATTER = logging.Formatter("{} [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(levelname))
    if log_location == 'dmx.log':
        # this is to write log to local directory, currently we do not write file to local directory
        file_handler = logging.FileHandler(log_location, mode='w')
    else:
        file_handler = TimedRotatingFileHandler(log_location, when='D', backupCount=1000)
        file_handler.suffix = "%Y%m%d"
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FORMATTER)
    return file_handler

def get_logger(logger_name, levelname, args):
    '''
    Create a logger with consolle handler(default output to stderr)
    '''
    exclude_user_list = ['psginfraadm', 'psgdmxadm', 'psgciw']

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG) # better to have too much log than not enough
 
    # if $HOTEL is more than 95%, do not write log     
    if int(get_arc_hard_quota_used()) < int('95') and os.getenv("USER") not in exclude_user_list: 
        #logger.addHandler(get_file_handler(levelname, get_dmx_log_location()))
        try:
            clean_existing_log()
        except: 
            pass
        logger.addHandler(get_file_handler(levelname, get_dmx_log_full_path()))
   
    if '--debug' in args.options:
         logger.addHandler(get_console_handler(levelname, logging.DEBUG))
         #logger.setLevel(logging.DEBUG)
    elif '-q' in args.options or '--quiet' in args.options:
         logger.addHandler(get_console_handler(levelname, logging.WARNING))
    else:
         logger.addHandler(get_console_handler(levelname, logging.INFO))

    return logger
 
def get_arc_hard_quota_used():
    '''
    Get user HOTEL diskspace 
    '''

    cmd = "arc-data-quota -h | grep 'of hard quota used' | awk '{print $6}'"
    result = subprocess.check_output(cmd, shell=True)
    return result.rstrip().decode()


def get_today_date_as_ymd():
    '''
    Get today date format in YYYY__MM_DD
    '''
    today = date.today()
    d1 = today.strftime("%Y%m%d")
    return d1 

def get_today_date_as_ymdhms():
    '''
    Get today date format in YYYY__MM_DD
    '''
    today_datetime = datetime.now().strftime("%Y%m%d_%H%M%S") 
    return today_datetime 

def get_dmx_id():
    HOSTNAME = os.environ.get('HOSTNAME')
    PID = os.getppid()
    USER = os.environ.get('USER')
    SITE = os.environ.get('ARC_SITE')

    today_date = get_today_date_as_ymd()
    dmx_id = 'dmx_{}_{}_{}_{}_{}'.format(USER, today_date, HOSTNAME, PID, SITE)
    return dmx_id

def get_dmx_log_full_path():
    '''
    Get DMX log full path (HOTEL/.dmxlog/dmx_YYYY_MM_DD_HOSTNAME_PPID.log)
    '''
    HOTEL = os.environ.get('HOTEL')

    today_date = get_today_date_as_ymd()
    dmxlog_dir = HOTEL+'/.dmxlog/' + today_date 

    # if user do not have .dmxlog in $HOTEL, create the directory
    if not os.path.exists(dmxlog_dir):
        cmd = 'mkdir -p {}'.format(dmxlog_dir)
        exitcode, stdout, stderr = run_command(cmd)
    dmx_id = get_dmx_id()    
    dmx_log = '{}/{}.log'.format(dmxlog_dir, dmx_id)

    return dmx_log



def remove_log(all_log, max_num=None):
    '''
    Remove log given a list of file
    '''
    need_to_remove_log = all_log

    if max_num:
        if len(all_log) > max_num:
            need_to_remove_log = [sorted(all_log)[0]]
        else:
            need_to_remove_log = [] 


    for ea_log in need_to_remove_log:
        if os.path.exists(ea_log):
            cmd = 'rm -rf {}'.format(ea_log)
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode or stderr:
                raise




def clean_existing_log():
    '''
    Clean up exisiting log
        - merge existing dmx_YYYY_MM_DD_HOSTNAME_PPID.log to dmx_YYYY_MM_DD.log_all
    '''
    HOTEL = os.environ.get('HOTEL')
    all_log_folder = glob.glob(HOTEL+'/.dmxlog/*')
    all_log_folder = [x for x in all_log_folder if os.path.isdir(x)]
    all_legacy = glob.glob(HOTEL+'/.dmxlog/*.log*')

    if all_legacy:
        remove_log(all_legacy)

    remove_log(all_log_folder, 7)

if __name__ == '__main__':
    pass

