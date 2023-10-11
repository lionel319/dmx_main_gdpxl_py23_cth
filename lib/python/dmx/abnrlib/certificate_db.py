#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/certificate_db.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

This class provides API that communicates with certificate table database used for recertification.
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
import MySQLdb
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.ecolib.ecosphere
import dmx.utillib.utils
import dmx.abnrlib.icm


class CertificateDbError(Exception): pass

class CertificateDb(object):
    def __init__(self, host='pg-icesql1.altera.com', user='killim', password='killim', database='TNRTEST', table='certificate', usejson=False):
        '''
        usejson will only affect the read operation. (all write operation will still go to mysql db)
        if usejson=True, it will not get the data from MySql. 
        It will read in the json from a disk, and get the info from there.
        The json file is periodically generated by a cronjob.
        The purpose of doing this is to prevent a single-point-of-failure so that
        when the mysql db is down, things still can move on with refering to the json.

        when usejson=True, this class only works on read-only mode.
        All write mode are not-workable.        
        '''
        self.logger = logging.getLogger(__name__)

        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.table = table
        self.usejson = usejson
        self.jsondir = '/nfs/site/disks/psg_flowscommon_1/common_info/dmx'
   
        if not usejson:
            self.db = MySQLdb.connect(host=host, user=user, passwd=password, db=database)
            self.cursor = self.db.cursor()
       
        self.eco = dmx.ecolib.ecosphere.EcoSphere()
        self.family = self.eco.get_family(family=None)

        self.icm = dmx.abnrlib.icm.ICManageCLI()


    def verify_thread_milestone(self, thread, milestone):
        if (milestone, thread) not in self.family.get_valid_milestones_threads():
            raise CertificateDbError("Milestone/Thread ({}/{}) is not valid in family:{}!".format(
                milestone, thread, self.family.name))


    def get_certified_list(self, thread, milestone):
        '''
        '''
        ret = []
        if self.usejson:
            ret = self._get_certified_list_from_json(thread, milestone)
        else:
            ret = self._get_certified_list_from_mysql(thread, milestone)
        return ret


    def _get_certified_list_from_mysql(self, thread, milestone):
        sql = "select project,variant,config from {} where thread='{}' and milestone='{}'".format(
            self.table, thread, milestone)
        try:
            self.logger.debug("Running sql cmd: {}".format(sql))
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            results = [[x[0],x[1],x[2]] for x in results]    ### convert tuple ==> list
            return results
        except:
            self.logger.error("Failed running sql cmd: {}".format(sql))
        return []


    def _get_certified_list_from_json(self, thread, milestone):
        try:
            jsonfile = self._get_json_filepath(milestone=milestone, thread=thread)
            with open(jsonfile) as f:
                ret = json.load(f)
        except:
            self.logger.warning("Failed loading jsonfile: {}".format(jsonfile))
            ret = []
        return ret


    def is_certified(self, thread, milestone, project, variant, config):
        '''
        '''
        certified_list = self.get_certified_list(thread, milestone) 
        if [project, variant, config] in certified_list:
            return True
        else:
            return False


    def add_certified_list(self, thread, milestone, project, variant, config):
        
        ### Verify if project/variant@config is a valid ICM object
        self.verify_project_variant_config(project, variant, config)

        ### Verify thread/milestone is a valid roadmap
        self.verify_thread_milestone(thread, milestone)

        ### If it is already certified, don't re-certify
        if self.is_certified(thread, milestone, project, variant, config):
            self.logger.info("{}/{}@{} was already certified for {}/{}. No further action required.".format(
                project, variant, config, thread, milestone))
            return True

        sql = ''' insert into {} 
            (thread, milestone, project, variant, config)
            values ('{}', '{}', '{}', '{}', '{}') '''.format(
            self.table, thread, milestone, project, variant, config)

        try:
            self.logger.debug("Running sql cmd: {}".format(sql))
            self.cursor.execute(sql)
            self.db.commit()
            self.logger.info("Successfully insert data to db.")
        except:
            self.db.rollback()
            self.logger.error("Failed inserting data to db.")


    def get_distinct_milestone_thread(self):
        '''
        return a list of distinct milestone/thread, ie:-
        return = [
            [milestone, thread],
            [milestone, thread],
            ...   ...   ...
        ]
        '''
        ret = []
        if not self.usejson:
            ret = self._get_distinct_milestone_thread_from_mysql()
        else:
            ret = self._get_distinct_milestone_thread_from_json()
        ### Change it from tuples to  list
        retlist = [[x[0],x[1]] for x in ret]
        return retlist


    def _get_distinct_milestone_thread_from_mysql(self):
        sql = "select distinct milestone,thread from {} ".format(self.table)
        try:
            self.logger.debug("Running sql cmd: {}".format(sql))
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            return results
        except:
            self.logger.error("Failed running sql cmd: {}".format(sql))
        return []


    
    def _get_distinct_milestone_thread_from_json(self):
        with open(self._get_json_filepath()) as f:
            ret = json.load(f)
        return ret



    def _get_json_filename(self, milestone='distinct', thread=''):
        ''' '''
        if milestone == 'distinct':
            return 'certificate___{}.json'.format(milestone)
        else:
            return 'certificate___{}___{}.json'.format(milestone, thread)


    def _get_json_filepath(self, milestone='distinct', thread=''):
        ''' '''
        return os.path.join(self.jsondir, self._get_json_filename(milestone, thread))


    def verify_project_variant_config(self, project, variant, config):
        if not config.startswith("REL"):
            raise CertificateDbError("Only REL Configs are allowed.")
        if project not in self.icm.get_projects():
            raise CertificateDbError("Invalid ICM-Project: {}".format(project))
        if variant not in self.icm.get_variants(project):
            raise CertificateDbError("Invalid ICM-Variant: {}".format(variant))
        if config not in self.icm.get_configs(project, variant):
            raise CertificateDbError("Invalid ICM-Config: {}".format(config))
        
        return True


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


    def _show_rows(self):
        '''
        This method is meant for testing.
        It means nothing, and is not gonna be used for any production.
        '''
        self.cursor.execute("select * from {}".format(self.table))
        rows = self.cursor.fetchall()
        self.logger.info(rows)


    def _show_columns(self):
        '''
        This method is meant for testing.
        It means nothing, and is not gonna be used for any production.
        '''
        self.cursor.execute("show columns from {}".format(self.table))
        rows = self.cursor.fetchall()
        self.logger.info(rows)


if __name__ == "__main__":

    ### For Debugging
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)




## @}