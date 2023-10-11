#!/usr/bin/env python

'''
This script 
- reads the templateset.xml
- generate the respective json file

Author: Kevin Lim Khai - Wern
Date: 21 June 2016

'''

import logging
from argparse import ArgumentParser
import sys
import os
import json
from xml.dom.minidom import parse
import xml.dom.minidom

ENTITY = ["<!DOCTYPE templateset [",
          "<!ENTITY ip_name \"ip_name\">",
          "<!ENTITY cell_name \"cell_name\">",
          "]>"]

def main():
    args = parse_arguments()

    ### Setting logging level 
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=loglevel)    
    
    with open('/tmp/tmp.xml', 'w') as f:
        lines = open(args.input).readlines()        
        for num, line in enumerate(lines):
            if num == 1:
                for entity in ENTITY:
                    f.write(entity)                                
            f.write(line)

    dom = xml.dom.minidom.parse('/tmp/tmp.xml')
    template = dom.documentElement

    deliverables = {}    
    for ele in template.childNodes:
        if ele.nodeName == 'template':
            description = ''
            patterns = {}
            filelists = {}
            milkyway = {}
            producers = []
            consumers = []           
            deliverable = str(ele._attrs['id'].nodeValue).lower()
            if deliverable not in deliverables:
                deliverables[deliverable] = {}
            for childele in ele.childNodes:
                if childele.nodeName == 'description':
                    description = str(childele.childNodes[0].data.strip())
                elif childele.nodeName == 'pattern':
                    try:
                        minimum = str(childele.childNodes[0].parentNode._attrs['minimum'].value)
                    except:
                        minimum = ''
                    try:
                        id = str(childele.childNodes[0].parentNode._attrs['id'].value)
                    except:
                        id = ''

                    pattern = str(childele.childNodes[0].data.strip().replace(';',''))   
                    if pattern not in patterns:
                        patterns[pattern] = {}
                    patterns[pattern]['minimum'] = minimum
                    patterns[pattern]['id'] = id
                elif childele.nodeName == 'filelist':
                    try:
                        minimum = str(childele.childNodes[0].parentNode._attrs['minimum'].value)
                    except:
                        minimum = ''
                    try:
                        id = str(childele.childNodes[0].parentNode._attrs['id'].value)
                    except:
                        id = ''

                    filelist = str(childele.childNodes[0].data.strip().replace(';',''))   
                    if filelist not in filelists:
                        filelists[filelist] = {}
                    filelists[filelist]['minimum'] = minimum
                    filelists[filelist]['id'] = id                    
                elif childele.nodeName == 'producer':  
                    producers.append(str(childele._attrs['id'].nodeValue.strip()))
                elif childele.nodeName == 'consumer':  
                    consumers.append(str(childele._attrs['id'].nodeValue.strip()))
                elif childele.nodeName == 'milkyway':
                    try:
                        id = str(childele.childNodes[0].parentNode._attrs['id'].value)
                    except:
                        id = ''

                    libpath = childele.childNodes[0].nextSibling.childNodes[0].data.strip().replace(';','')
                    lib = childele.childNodes[0].nextSibling.nextSibling.nextSibling.childNodes[0].data.strip().replace(';','')
                    milkyway[lib] = libpath
            deliverables[deliverable]['description'] = description
            deliverables[deliverable]['pattern'] = patterns
            deliverables[deliverable]['filelist'] = filelists
            deliverables[deliverable]['milkyway'] = milkyway
            deliverables[deliverable]['producer'] = producers
            deliverables[deliverable]['consumer'] = consumers
            deliverables[deliverable]['owner'] = ''
            deliverables[deliverable]['additional owners'] = []
        elif ele.nodeName == 'successor':
            predecessors = []
            successor = str(ele._attrs['id'].nodeValue).lower()
            if successor not in deliverables:
                deliverables[successor] = {}
            for childele in ele.childNodes:
                if childele.nodeName == 'predecessor':
                    predecessors.append(str(childele.childNodes[0].data.strip()).lower())
            deliverables[successor]['predecessor'] = predecessors
            if 'successor' not in deliverables[successor]:
                    deliverables[successor]['successor'] = []
            for predecessor in predecessors:
                if predecessor not in deliverables:
                    deliverables[predecessor] = {}
                if 'successor' not in deliverables[predecessor]:
                    deliverables[predecessor]['successor'] = []
                deliverables[predecessor]['successor'].append(successor)

    templatejson = '{}/template.json'.format(os.path.dirname(os.path.abspath(__file__)))
    with open(templatejson, 'w') as outfile:
        json.dump(deliverables, outfile, indent=4, sort_keys=True)

    print '{} generated'.format(templatejson)

def parse_arguments():
    parser = ArgumentParser()    
    parser.add_argument('-i', '--input', required=True, help='input templateset.xml')
    parser.add_argument('--debug', required=False, default=False, action='store_true', help='Turn on debugging mode for more verbose messages.')
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    logger = logging.getLogger()
    main()
