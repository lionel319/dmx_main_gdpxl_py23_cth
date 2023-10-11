#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/goldenarc_db.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

This class provides API that communicates with goldenarc table database used for recertification.
For further details, https://wiki.ith.intel.com/display/tdmaInfra/Release+Configuration+Re-Certification.

Author: Lionel Tan Yoke Liang
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

## @addtogroup dmxlib
## @{

import os
import sys
import socket
import re
import logging
import argparse
import getpass
import time
from pprint import pprint
#import MySQLdb
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.ecolib.ecosphere
import dmx.utillib.utils
import dmx.abnrlib.icm
import dmx.utillib.arcutils
import dmx.ecolib.checker
import dmx.utillib.dmxmongodbbase


class GoldenarcDbError(Exception): pass

class GoldenarcDb(object):
    def __init__(self, uri=None, database=None, prod=False):
        self.logger = logging.getLogger(__name__)

        self.uri = uri
        self.database = database

        if not self.uri:
            if prod:
                self.uri = 'mongodb://GOLDENARC_so:lMbS1PiFqBiKaVe@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/GOLDENARC?replicaSet=mongo8150'
            else:
                self.uri = 'mongodb://GOLDENARC_TEST_so:zXqZm7b05UkFfZg@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/GOLDENARC_TEST?replicaSet=mongo8150'

        if not self.database:
            if not prod:
                self.database = 'GOLDENARC_TEST'
            else:
                self.database = 'GOLDENARC'

        self.db = dmx.utillib.dmxmongodbbase.DmxMongoDbBase(uri=self.uri, database=self.database)
        
        self.eco = dmx.ecolib.ecosphere.EcoSphere()
        self.family = self.eco.get_family(family=os.getenv("DB_FAMILY"))

        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.arc = dmx.utillib.arcutils.ArcUtils()

    def connect(self):
        self.db.connect()
        self.set_collection('GoldenArc')

    def set_collection(self, collectionname):
        self.col = self.db.db[collectionname]
        return self.col

    def verify_thread_milestone(self, thread, milestone):
        if (milestone, thread) not in self.family.get_valid_milestones_threads():
            raise GoldenarcDbError("Milestone/Thread ({}/{}) is not valid in family:{}!".format(
                milestone, thread, self.family.name))
        return True


    def verify_arc_resource(self, arcres):
        ''' verify and make sure the given arcres is valid and defined. '''
        if not self.arc.is_resource_defined(arcres):
            raise GoldenarcDbError("arc res ({}) is not defined!".format(arcres))
        return True


    def verify_flow_subflow(self, flow, subflow):
        ''' verify and make sure the given flow/subflow is a valid check in the roadmap '''
        try:
            checker = dmx.ecolib.checker.Checker(self.family.name, flow, subflow)
            info = checker.get_check_info()
            if not info[0]:
                raise GoldenarcDbError("Checker(flow:{}, subflow:{}) is not valid!".format(flow, subflow))
        except Exception as e:
            self.logger.error(str(e))
            raise GoldenarcDbError("Checker(flow:{}, subflow:{}) is not valid!".format(flow, subflow))

        return True

    
    def get_tools_by_checker(self, thread, milestone, flow, subflow):
        '''
        return all the tool(arc type) names 
        return = [
            ['python', '/2.7.1'],
            ['dmx', '/13.12']
        ]
        '''

        data = self.get_goldenarc_list(thread=thread, milestone=milestone, flow=flow, subflow=subflow)
        ret = []
        for d in data:
            ret.append([d['tool'], d['version']])
        return ret


    def add_goldenarc_list(self, thread, milestone, flow, subflow, tool, version):
        '''
        thread = 'FM8revA0'
        milestone = '3.0'
        flow = 'rtl'
        subflow = 'name'
        tool = 'dmx'
        version = '/9.4'

        if (thread, milestone, flow, subflow, tool) exists:
            update existing data
        else:
            add new data
        '''
      
        if tool == 'skipgoldenarc' and version == '/0':
            pass
        else:
            self.verify_arc_resource('{}{}'.format(tool, version))
        self.verify_thread_milestone(thread, milestone)
        self.verify_flow_subflow(flow, subflow)
        return self.add_or_update_goldenarc(thread, milestone, flow, subflow, tool, version)

    def delete_goldenarc_list(self, thread, milestone, flow, subflow, tool, version=None):
        info = {'thread': thread, 'milestone': milestone, 'flow': flow, 'subflow': subflow, 'tool': tool}
        if version:
            info['version'] = version
        data = self.col.delete_one(info)
        return data

    def is_goldenarc_exist(self, thread, milestone, flow, subflow, tool, version=None):
        info = {'thread': thread, 'milestone': milestone, 'flow': flow, 'subflow': subflow, 'tool': tool}
        if version:
            info['version'] = version
        data = self.col.find_one(info)
        return data

    def add_or_update_goldenarc(self, thread, milestone, flow, subflow, tool, version):
        '''
        if (thread, milestone, flow, subflow, tool) exist:
            update it 
        else:
            add new document
        '''
        info = {'thread': thread, 'milestone': milestone, 'flow': flow, 'subflow': subflow, 'tool': tool}
        update = {'$set': {'version': version}}
        data = self.col.find_one_and_update(info, update, return_document=dmx.utillib.dmxmongodbbase.pymongo.collection.ReturnDocument.AFTER, upsert=True)
        return data
    

    def get_goldenarc_list(self, thread=None, milestone=None, flow=None, subflow=None, tool=None, version=None):
        info = {}
        for key in ['thread', 'milestone', 'flow', 'subflow', 'tool', 'version']:
            if locals()[key] != None:
                info[key] = locals()[key]
        self.logger.debug("Finding data for: {}".format(info))
        data = self.col.find(info)

        ### Make pymongo returned data into list-of-dicts
        ret = []
        for d in data:
            ret.append(d)
        return ret


    def _debug(self, exitcode, stdout, stderr):
        self.logger.debug("exitcode: {}".format(exitcode))
        self.logger.debug("stdout: {}".format(stdout))
        self.logger.debug("stderr: {}".format(stderr))


    def __del__(self):
        try:
            self.logger.debug("Desctructor: closing db ...")
            self.db.close()
        except:
            pass


if __name__ == "__main__":

    ### For Debugging
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)




## @}
