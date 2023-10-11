#!/usr/bin/env python

import os
import sys
import logging
import json


rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
from datetime import datetime

from djangodata import mysql_db_connector
from djangodata.models import Cellname

def main():

    logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         

    with open("generated_files/cellnames.json") as f:
        data = json.load(f)

    for [project, variant, cellname] in data:
        
        ret = Cellname.objects.filter(project=project, variant=variant, cellname=cellname)

        ### Owner already exist. Update it
        if ret:
            logging.info("Record exist: {}/{}:{}".format(project, variant, cellname))

        ### No entry found. Create new one.
        else:
            c = Cellname(project=project, variant=variant, cellname=cellname)
            c.save()
            logging.info("New entry created: {}".format(c))



if __name__ == '__main__':
    logger = logging.getLogger()
    main()
