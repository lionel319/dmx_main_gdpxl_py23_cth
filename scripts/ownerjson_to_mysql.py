#!/usr/bin/env python

import os
import sys
import logging
from argparse import ArgumentParser
import json


rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
from datetime import datetime

from djangodata import mysql_db_connector
from djangodata.models import Owner

def main():

    logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         

    with open("owner.json") as f:
        data = json.load(f)

    for [project, variant, owner] in data:
        
        ret = Owner.objects.filter(project=project, variant=variant)

        ### Owner already exist. Update it
        if ret:
            obj = ret[0]
            obj.datetime = datetime.now()
            original_owner = obj.owner
            obj.owner = owner
            logging.info("Updated ownership of {} from {} to {}".format(variant, original_owner, owner))

        ### No entry found. Create new one.
        else:
            o = Owner(project=project, variant=variant, owner=owner, datetime=datetime.now())
            o.save()
            logging.info("New entry created: {}".format(o))



if __name__ == '__main__':
    logger = logging.getLogger()
    main()
