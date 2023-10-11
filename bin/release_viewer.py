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
import dmx.utillib.diskutils
import dmx.utillib.utils

LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)

def main():
    arcjobid = sys.argv[1]
    filepattern = '/nfs/site/disks/fln_tnr_1/splunk/qa_data/tnr_{}_*'.format(arcjobid)

    ### get input file
    cmd = 'ls {}'.format(filepattern)
    print('Running: {}'.format(cmd))
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    if exitcode:
        print("ERROR: Can not find inputfile for arcjobid:{}".format(arcjobid))
        return
    inputfile = stdout.strip()
    print("File found: {}".format(inputfile))

    header = ['count', 'status', 'flow', 'subflow', 'topcell', 'error']
    data = []
    count = 1
    with open(inputfile) as f:
        for line in f:
            if line:
                d = json.loads(line)
                try:
                    tmp = [count, d['status'], d['flow'], d['subflow'], d['flow-topcell'], d['error']]
                    data.append(tmp)
                    count += 1
                except:
                    pass

    print('=========================')
    print(tabulate(data, headers=header, tablefmt='orgtbl'))
    print('=========================')


    ### Finding tnrerrors.csv and reporting 
    with open(inputfile) as f:
        for line in f:
            if line:
                d = json.loads(line)
                if "status" in d and d['status'] == "Created workspace":
                    wsroot = d['workspace_rootdir']
                    break
    filepath = os.path.join(wsroot, 'tnrerrors.csv')
    cmd = '/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost "cat {}"'.format(filepath)
    cmd = '/p/psg/da/infra/admin/setuid/run_as_psginfraadm.sh "cat {}"'.format(filepath)
    print() 
    print('=========================')
    print('tnrerrors.csv')
    print('=========================')
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    print(stdout + stderr)

if __name__ == '__main__':
    main()


