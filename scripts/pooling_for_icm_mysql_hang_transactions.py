#!/usr/bin/env python

import os
import sys
import logging
from pprint import pprint
from datetime import datetime
import json
import time


rootdir = '/nfs/site/disks/da_infra_1/users/yltan/depot/da/infra/dmx/main/lib/python'
#rootdir = '/p/psg/flows/common/dmx/13.0/lib/python'
sys.path.insert(0, rootdir)

rootdir = '/nfs/site/disks/da_infra_1/users/yltan/depot/da/infra/cicq/main/lib'
#rootdir = '/p/psg/flows/common/dmx/13.0/lib/python'
sys.path.insert(0, rootdir)

import dmx.utillib.utils
import dmx.utillib.loggingutils
import dmx.utillib.diskutils

LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)

def main():
    cmd1 = """ mysql -h sjlicm03.sc.intel.com -uicmAdmin -picmAdmin bugs -e 'show processlist' | grep 'Waiting for table metadata lock' """
    cmd2 = """ mysql -h sjlicm03.sc.intel.com -uicmAdmin -picmAdmin bugs -e 'show processlist' """
    for i in range(100):
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        print "Running {}".format(cmd1)
        os.system(cmd1)
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        print
        time.sleep(5)

if __name__ == '__main__':
    main()


