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
    cmd = """ mysql -h sjlicm03.sc.intel.com -uicmAdmin -picmAdmin information_schema -e 'select ps.id,ps.user,ps.host,ps.db,ps.command from information_schema.processlist ps join information_schema.INNODB_TRX itx on itx.trx_mysql_thread_id=ps.id and ps.command="Sleep";' """
    for i in range(100):
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        print "Running {}".format(cmd)
        os.system(cmd)
        print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
        print
        time.sleep(5)

if __name__ == '__main__':
    main()


