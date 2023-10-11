#!/usr/bin/env python

import os
import sys
from dmx.ecolib.ecosphere import EcoSphere
from dmx.abnrlib.icm import ICManageCLI
import xml.etree.ElementTree as ET
from pprint import pprint
import xml.dom.minidom
import json
import collections
import dmx.ecolib.ip
import concurrent.futures
import logging


FAMILY = ['Falcon', 'Wharfrock', 'Gundersonrock', 'Reynoldsrock']
FILENAME = 'roadmap_csv_data2.csv'

class IPError(Exception): pass


def main():
    gen_csv()





#i10socfm,FM6,asic,aib_ssm,2.0,deliverable,lint
#i10socfm,FM6,asic,aib_ssm,2.0,checker,lint_check (lint:mustfix)
#i10socfm,FM6,asic,aib_ssm,2.0,checker,lint_check (lint:review)


def worker(prod, ip):
    retlist = []
    try:
        for ms in prod.get_milestones():
            LOGGER.debug("MS: {}".format(ms))
            for each_deliverable in ip.get_deliverables(bom='dev', local=False, milestone=ms.name, roadmap=prod.roadmap):
                LOGGER.debug("deliverable: {}".format(each_deliverable))
                csv_string = ip.icmproject + ',' + prod.name + ',' + str(ip.iptype) + ',' + ip.name + ',' + ms.name +',deliverable,' + each_deliverable.name + '\n'
                retlist.append(csv_string)
                for checker in each_deliverable.get_checkers(milestone=ms.name, roadmap=prod.roadmap):
                    checker_string = str(checker.checkname)+ ' (' + checker.flow
                    if checker.subflow != '' :
                        checker_string = checker_string + ':' + checker.subflow + ')'
                    else :
                        checker_string = checker_string + ')'
                    csv_string = ip.icmproject + ',' + prod.name + ',' + str(ip.iptype) + ',' + ip.name + ',' + ms.name +',checker,' + checker_string + '\n'
                    retlist.append(csv_string)
    except Exception, e:
        LOGGER.error("Exception: {}".format(str(e)))
    return retlist


def gen_csv():
    future_list = []

    e = dmx.ecolib.ecosphere.EcoSphere()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        i = 0
        for f in FAMILY:
            family = e.get_family(f)
            for prod in family.get_products():
                LOGGER.debug("PROD: {}".format(prod))
                for ip in family.get_ips():
                    LOGGER.debug("IP: {}".format(ip))
                    i += 1
                    LOGGER.debug("Submitting Thread({}): worker({}, {}) ...".format(i, prod, ip))
                    future_list.append(executor.submit(worker, prod, ip))


    ### Writing to csv file
    filepath = FILENAME
    with open(filepath, 'w') as f:
        for future in future_list:
            for line in future.result():
                f.write(line)



if __name__ == '__main__':
    logging.basicConfig(format="-%(levelname)s- [%(asctime)s] - [%(module)s]: %(message)s".format(logging.DEBUG))
    LOGGER = logging.getLogger('')
    LOGGER.setLevel(logging.DEBUG)
    sys.exit(main())
