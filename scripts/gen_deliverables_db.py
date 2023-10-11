#!/usr/bin/env python

'''
This script 
- downloads the Ecosystem html file (prepared by Bertrand)
- extract the infomation from the "Deliverables" and "Deliverables by IP Types" table
- generate the respective json file

Example of the Ecosystem html (input) file:-
    http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/14nmEcosystems/14nm_ND5revA.html


Author: Lionel Tan Yoke-Liang
Date: 18 April 2016

'''


from xml.etree import ElementTree
import urllib2
import logging
import tempfile
from argparse import ArgumentParser
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecolib import dataloader


url = 'http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/14nmEcosystems/14nm_ND5revA.html'

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
            url = json.load(f)[args.thread]['roadmap']
    except:
        raise Exception("'roadmap' key for thread {} not defined in inputsmap file: {}".format(args.thread, mapfile))
    

    logging.info("Downloading deliverable html file from {} ...".format(url))
    filepath = download_html_file(url)
    logging.info("deliverable files downloaded at {}".format(filepath))
    
    jsonfile = generate_json_file(filepath, args.thread)


def generate_json_file(input_html_file, thread):
    parser = ElementTree.XMLParser(html=1)
    parser.parser.UseForeignDTD(True)
    parser.entity['copy'] = '(c)'

    ET = ElementTree.ElementTree()
    root = ET.parse(input_html_file, parser=parser)

    deliverables_tag_found = 0
    deliverables_by_ip_type_tag_found = 0
    body = root.find(nsmap('body'))
    for e in body:
        if e.tag == nsmap('h2') and e.text == "Deliverables":
            deliverables_tag_found = 1
        elif deliverables_tag_found:
            deliverables_tag_found = 0
            logging.info("- Extracting deliverables table ... ")
            json_deliverables = extract_deliverables_table(e)
        elif e.tag == nsmap('h2') and e.text == 'Deliverables by IP Types':
            deliverables_by_ip_type_tag_found = 1
        elif deliverables_by_ip_type_tag_found:
            logging.info("- Extracting deliverables_by_ip_type table ... ")
            deliverables_by_ip_type_tag_found = 0
            json_deliverables_by_ip_type = extract_deliverables_by_ip_type_table(e)

    data = {
        'deliverables' : json_deliverables,
        'deliverables_by_ip_type' : json_deliverables_by_ip_type}
    for key in data.keys():
        cmd = getattr(dataloader, 'get_{}_file'.format(key))
        filepath = os.path.abspath(cmd(thread))
        os.system('mkdir -p {}'.format(os.path.dirname(filepath)))
        with open(filepath, 'w') as f:
            json.dump(data[key], f, indent=4, sort_keys=True)
        logging.info("Successfully generated {}".format(filepath))


def extract_deliverables_by_ip_type_table(table):
    ''' 
    row 1 == variant type
    col 1 == thread_milestone
    '''

    header = [] # variant type
    data = {}
    for rownum,row in enumerate(table):
        logging.debug("R{})".format(rownum))
        for colnum,cell in enumerate(row):
            logging.debug("- C{})".format(colnum))
            if rownum == 0:
                header.append(cell.text)
                logging.debug("  > {}".format(cell.text))
                if colnum != 0:
                    data[header[colnum]] = {}
            elif rownum != 0:
                if colnum == 0:
                    thread, milestone = cell.text.split('REL')  # cell.text == ND5revAREL3.5
                    logging.debug("  > {}".format(cell.text))
                else:
                    if milestone not in data[header[colnum]]:
                        data[header[colnum]][milestone] = []
                    for atag in cell.findall(nsmap('a')):
                        libtype = "".join(atag.itertext())
                        if atag.find(nsmap("span[@class='emphasize']")) != None:
                            logging.debug("     ~ {} ()".format(libtype))
                        else:
                            logging.debug("     ~ {}".format(libtype))
                            data[header[colnum]][milestone].append(libtype)

    return data


def extract_deliverables_table(table):
    '''
    row 1 == 'ND4revAREL0.5'
    row 2 == 'description'
    row 3 == libtypes (one per line)
    '''
    header = []
    data = {}
    for rownum,row in enumerate(table):
        logging.debug("R{})".format(rownum))
        for colnum,cell in enumerate(row):
            logging.debug("- C{})".format(colnum))
            if rownum == 0:
                thread, milestone = cell.text.split('REL')  # cell.text == ND5revAREL3.5
                header.append(milestone)
                data[milestone] = {'description':'', 'libtypes':[]}
                logging.debug("   > {}".format(cell.text))
            elif rownum == 1:
                data[header[colnum]]['description'] = cell.text
                logging.debug("   > {}".format(cell.text))
            elif rownum == 2:
                for atag in cell.findall(nsmap('a')):
                    libtype = "".join(atag.itertext())
                    if atag.find(nsmap("span[@class='emphasize']")) != None:
                        logging.debug("     ~ {} (excluded)".format(libtype))
                    else:
                        logging.debug("     ~ {}".format(libtype))
                        data[header[colnum]]['libtypes'].append(libtype)

    return data
                    

def nsmap(xpath):
    '''
    Because the html file is using namespace, we can not find the tags purely using tags alone
    we need to include the namespace prefix to all the tags that we are interested
    http://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
    '''
    return '{http://www.w3.org/1999/xhtml}' + xpath



def download_html_file(url):
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
