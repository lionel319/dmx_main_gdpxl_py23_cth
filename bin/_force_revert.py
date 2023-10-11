#!/usr/bin/env python

'''
when kibana dashboard is down, you can use this script for temporary workaround,
to view errors/status of a release.

Usage:-
    > release_viewer.py  <arcjobid>
'''
from __future__ import print_function

import os
import sys
import logging
from pprint import pprint
from datetime import datetime
import json

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, ROOTDIR)

import json
from pprint import pprint
from tabulate import tabulate

import dmx.utillib.utils
import dmx.utillib.loggingutils


def main():
    if len(sys.argv) < 2 or '-h' in sys.argv or '--help' in sys.argv:
        print("""
        This script helps to forcefully revert all opened files from both sites.
        This script works on any users. 
        Thus, this script has to be kept to only the admins.

        Usage:-
        =======
        > _force_revert.py <filespec>
        > _force_revert.py '//depot/icm/proj/i10socfm/liotest1/*/landing_zone_test/...'

        """)
        return 0

    if '--debug' in sys.argv:
        LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
    else:
        LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)

    filespec = sys.argv[1]
    #dmx.utillib.utils.login_to_icmAdmin(filespec, site='png')
    #dmx.utillib.utils.force_revert_files_by_filespec(filespec, site='png')
    dmx.utillib.utils.login_to_icmAdmin(filespec, site='sc_gdpxl')
    dmx.utillib.utils.force_revert_files_by_filespec(filespec, site='sc_gdpxl')


if __name__ == '__main__':
    main()


