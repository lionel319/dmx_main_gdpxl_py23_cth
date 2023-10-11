#!/usr/bin/env python

import os
import sys
import logging
from pprint import pprint
import datetime 
import json
import dmx.utillib.teamcity_base_api

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
    a = dmx.utillib.teamcity_base_api.TeamcityBaseApi(
        host='https://teamcity01-fm.devtools.intel.com',
        token = 'eyJ0eXAiOiAiVENWMiJ9.QzBvMk9hUEZFci1XZUllRXNxVnlXcV92U2xJ.ZjhlYzE0M2YtZjk2Ny00MTgzLWJkZjUtMGFlN2I5MGI1ZDNk',   # psgcicq_tc's token
        output_format = 'json',
    )

    buildtypes = json.loads(a.get_buildtypes_by_project_id('PsgCicq'))['buildType']
    for bt in buildtypes:
   
        try:
            b = json.loads(a.get_latest_build_for_buildtype(bt['id']))
            name = b['buildType']['name']
            date = b['finishDate'][:8]  # 20210704T170108-0700
            now = datetime.datetime.now()
            last = datetime.datetime.strptime(date, '%Y%m%d')
            status = 'PASS'
            limit = datetime.timedelta(days=60)
            delta = now - last
            if delta > limit:
                status = 'FAIL'
            print '{} - {} - {} - [{}]'.format(status, name, last, delta)
        except Exception as e:
            print '{} - {}'.format(str(e), bt['name'])


if __name__ == '__main__':
    main()


