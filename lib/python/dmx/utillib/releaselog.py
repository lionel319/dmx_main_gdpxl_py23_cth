#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/releaselog.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $
'''
import sys
import logging
import os
import json
import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)
import dmx.utillib.version
from dmx.errorlib.exceptions import *

PICE_PG_ARC = 'https://psg-png-arc.png.intel.com'
PICE_SJ_ARC = 'https://psg-sc-arc.sc.intel.com'
JOB_DIR = 'arc/dashboard/reports/show_job'

class ReleaseLogError(Exception): pass

class ReleaseLog(object):
    def __init__(self, filepath, project, variant, libtype, config, releaser, datetime, arcjob, relconfig, milestone, thread, description, release_id, runtime=0, arcjob_path='', preview=False):
        '''
        Format:

        "project": "i10socfm",
        "variant": "hbmc",
        "libtype": "ippwrmod",
        "config"    : "tnr-placeholder-ippwrmod-1",
        "releaser"  : "ismailab",
        "datetime" : "2011-02-03 14:35:26",
        "arcjob"    : "https://psg-sc-arc.sc.intel.com/arc/dashboard/reports/show_job/14033463",
        "relconfig" : "REL3.0FM8revA0__18ww111a",       # "relconfig" : value has to be either a "REL***" or "N/A"
        "milestone" : "3.0",
        "thread"    : "FM8revA0",
        "description" : "comments from Lionel",
        "release_id" : "sjyli0117_lionelta_109412_1515049193
        '''
        self.project = project        
        self.filepath = filepath
        self.variant = variant
        self.libtype = libtype
        self.config = config
        self.releaser = releaser
        self.arcjob = arcjob
        self.relconfig = relconfig
        self.milestone = milestone
        self.thread = thread
        self.description = description
        self.release_id = release_id
        self.datetime = datetime
        self.runtime = runtime
        self.preview = preview
        self.arcjob_path = arcjob_path if arcjob_path else '{}/{}/{}'.format(PICE_SJ_ARC, JOB_DIR, self.arcjob)

        filedir = os.path.dirname(filepath)
        if not os.access(filedir, os.W_OK):
            raise DmxErrorCFDR02('Dir {} is not writable'.format(filedir))

        if os.path.isfile(self.filepath):
            raise DmxErrorCFFL03('File {} already exists'.format(self.filepath))

        if not (self.relconfig.startswith('REL') or self.relconfig.startswith("PREL")) and not self.relconfig.startswith('NA'):
            raise DmxErrorICCF02('Relconfig {} must begin with REL or NA or PREL.'.format(self.relconfig))

        self.json = {}
        self.json['project'] = self.project
        self.json['variant'] = self.variant
        self.json['libtype'] = self.libtype
        self.json['config'] = self.config
        self.json['releaser'] = self.releaser
        self.json['datetime'] = self.datetime
        self.json['arcjob'] = self.arcjob
        self.json['relconfig'] = self.relconfig
        self.json['milestone'] = self.milestone
        self.json['thread'] = self.thread
        self.json['description'] = self.description
        self.json['release_id'] = self.release_id
        self.json['runtime'] = self.runtime
        self.json['arcjob_path'] = self.arcjob_path

        version = dmx.utillib.version.Version()
        self.json['dmx_version'] = version.dmx_version
        self.json['dmxdata_version'] = version.dmxdata_version

        self.json['results'] = []

    def add_result(self, flow, subflow, topcell, status, error, waiver):
        '''
        Format:

        "results" : [
        {
            "flow": "ippwrmod",
            "subflow": "mustfix",
            "topcell": "hbmc_cell1",      
            "status":   "waived",
            "error": "checksum for file a failed"
        },
        {
            "flow": "ippwrmod",
            "subflow": "mustfix",
            "topcell": "hbmc_cell2",      
            "status":   "waived",
            "error": "cannot access file xyz"
        },
        {
            "flow": "ippwrmod",
            "subflow": "mustfix",
            "topcell": "hbmc_cell3",      
            "status":   "waived",
            "error": "Result fail. timing not met."
        },
        {
            "flow": "ippwrmod",
            "subflow": "review",
            "topcell": "hbmc_cell1",      
            "status":   "waived",
            "error": "No audit file found"
        }
        ]
        '''
        dict = {}
        dict['flow'] = flow
        dict['subflow'] = subflow
        dict['topcell'] = topcell
        dict['status'] = status
        dict['error'] = error
        dict['waiver'] = waiver
        self.json['results'].append(dict)

    def save(self):    
        '''
        Save into json file
        '''
        if not self.preview:
            with open(self.filepath, 'a') as f:
                json.dump(self.json, f, indent=4, sort_keys=True)

    def dump(self):
        '''
        Print json to terminal
        '''
        pprint.pprint(self.json)
