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
import openpyxl
from pprint import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecolib import dataloader


REQUIRED_COLUMNS = ['Check Name', 'Deliverable', 'Flow', 'SubFlow', 'Type', 'Audit Ready', 'Documentation', 'Unix Userid', 'Filelist']

def main():

    args = parse_arguments()

    ### Setting logging level 
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=loglevel)

    mapfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'mappers', 'inputsmap.json')
    try:
        with open(mapfile) as f:
            url = json.load(f)[args.thread]['checker']
    except:
        raise Exception("'checker' key for thread {} not defined in inputsmap file: {}".format(args.thread, mapfile))
    

    logging.info("Downloading checker xlsx file from {} ...".format(url))
    filepath = download_xlsx_file(url)

    logging.info("checkers files downloaded at {}".format(filepath))
    
    jsonfile = generate_json_file(filepath, args.thread)


def generate_json_file(input_xlsx_file, thread):
    '''
      {
        "pk": 1,
        "model": "ice.test",
          "fields": {
            "ice_family": "ND",
            "owner": 9529,
            "deliverable": 26,
            "check_type": "c",
            "flow": "mw",
            "subflow": "",
            "description": "floorplan_integration",
            "docs": "",
            "checker": "floorplan_integration",
            "ready": true,
            "filelist": true
            }
      },    
    '''
    
    logging.info("Reading checker file ...")
    wb = openpyxl.reader.excel.load_workbook(input_xlsx_file)
    ws = wb.get_sheet_by_name(name='List of Checks')
    data = []
    ready_checks_count = 0
    for rownum,row in enumerate(ws.rows):
        rowdata = []
        for colnum,cell in enumerate(row):
            rowdata.append(cell.value)

            ### Change all None value to empty string ''
            if rowdata[colnum] == None:
                rowdata[colnum] = ''


        ### IF it is header (first) row, 
        ### - check and make sure all required columns do exists
        ### - map the columns to their respective column number
        if rownum == 0:
            missing_list = get_missing_required_columns(rowdata, thread)
            if missing_list:
                logging.error("Missing column from checker file. {}".format(missing_list))
                logging.error("Program terminated!")
                sys.exit(1)
            else:
                keymap = map_header_name_to_column_number(rowdata, thread)
                logging.debug("Header column map: {}".format(keymap))

        ### Skip if the Flow or Milestone(thread)
        elif is_flow_or_milestones_column_empty(rowdata, keymap):
            continue

        else:
            tmpdata = {}
            for colnum,colname in keymap.items():

                
                ### For 'Audit Ready' and 'Filelist' column, change all 'yes' to 1, else 0
                if colname == 'Audit Ready':
                    if is_yes(rowdata[colnum]):
                        rowdata[colnum] = 1
                        ready_checks_count += 1
                    else:
                        rowdata[colnum] = 0

                ### For 'Filelist' column, change all 'yes' to 1, else 0
                elif colname == 'Filelist':
                    if is_yes(rowdata[colnum]):
                        rowdata[colnum] = 1
                    else:
                        rowdata[colnum] = 0

                ### For 'Type' column, Change "DC" to d(data check), and the rest to c(context check)
                elif colname == 'Type':
                    if rowdata[colnum] == 'DC':
                        rowdata[colnum] = 'd'
                    else:
                        rowdata[colnum] = 'c'

                ### For 'milestone' column, split the entry by space, and make sure all elements are \d.\d format
                elif colname == 'milestones':
                    mslist = []
                    for ms in str(rowdata[colnum]).split():
                        ### If the milestone is a single digit(eg:- 3), make it 3.0
                        if len(ms) == 1:
                            mslist.append(ms + '.0')
                        else:
                            mslist.append(ms)
                    rowdata[colnum] = mslist

                tmpdata[colname] = rowdata[colnum]
            data.append(tmpdata)

    filepath = os.path.abspath(dataloader.get_checkers_file(thread))
    os.system('mkdir -p {}'.format(os.path.dirname(filepath)))

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
    logging.info("Total audit ready checks = {}".format(ready_checks_count))
    logging.info("Successfully generated {}".format(filepath))


def is_flow_or_milestones_column_empty(data, keymap):
    ''' 
    Return True if the 'Flow' or 'milestone' column has no data
    else return False
    '''
    flow_colnum = [num for num in keymap if keymap[num] == 'Flow'][0]
    ms_colnum = [num for num in keymap if keymap[num] == 'milestones'][0]
    if not data[flow_colnum] or not data[ms_colnum]:
        return True
    return False

def is_yes(text):
    return True if text in ['YES', 'Yes', 'yes'] else False


def map_header_name_to_column_number(header_list, thread):
    '''
    map the header column names to their respective column numbers.
    Return the mapping dict::

        ret = {
            <colnum>: <header name>,
            0: 'Checker Name',
            1: 'Flow', 
            2: 'SubFlow',
            ...   ...   ...
        }

    '''
    ret = {}
    for colnum,name in enumerate(header_list):
        if name in REQUIRED_COLUMNS:
            ret[colnum] = name
        elif name == thread:
            ret[colnum] = 'milestones'
    return ret


def get_missing_required_columns(found_column_list, thread):
    '''
    Return a list of column names which are missing from the required list
    '''
    missing_list = []
    for name in REQUIRED_COLUMNS + [thread]:
        if name not in found_column_list:
            missing_list.append(name)
    return missing_list


def download_xlsx_file(url):
    a = tempfile.NamedTemporaryFile()
    a.close()
    cmd = '/usr/bin/curl -v --ntlm -u icetnr:Altera.123 {} -o {} >& /dev/null'.format(url, a.name)
    os.system(cmd)
    return a.name


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('-t', '--thread', required=True, help='The thread name.')
    parser.add_argument('--debug', required=False, default=False, action='store_true', help='Turn on debugging mode for more verbose messages.')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    logger = logging.getLogger()
    main()
