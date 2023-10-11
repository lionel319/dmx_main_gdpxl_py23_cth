#!/usr/bin/env python
''' 
Documentation:
==============
test test
'''


import os
import sys
import logging
from argparse import ArgumentParser
import json


rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
from datetime import datetime

from djangodata import mysql_db_connector
from djangodata.models import Unneeded

def main():

    logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         

    with open("generated_files/unneeded.json") as f:
        data = json.load(f)

    for [project, variant, cellname, libtypes] in data:
       
        for lib in libtypes:
            libtype = lib.lower()
            ret = Unneeded.objects.filter(project=project, variant=variant, cellname=cellname, libtype=libtype)

            ### Owner already exist. Update it
            if ret:
                obj = ret[0]
                logging.info("Data exist {}.".format(obj))

            ### No entry found. Create new one.
            else:
                o = Unneeded(project=project, variant=variant, cellname=cellname, libtype=libtype)
                o.save()
                logging.info("New entry created: {}".format(o))



if __name__ == '__main__':
    logger = logging.getLogger()
    main()
