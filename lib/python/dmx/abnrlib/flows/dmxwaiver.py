#!/usr/bin/env python

"""
Base class for DMX MySql Database. 
"""
from __future__ import print_function
from builtins import str
from builtins import object
import sys
sys.path.insert(0, '/nfs/site/disks/psg_flowscommon_1/common_info/pymongo380a')
#sys.path.insert(0, '/p/psg/da/infra/api')
import pymongo
from pymongo import MongoClient, UpdateOne, DeleteOne
from bson.objectid import ObjectId
import logging
import copy
import csv
import os
import dmx.utillib.admin
from datetime import datetime
LOGGER = logging.getLogger(__name__)
from dmx.utillib.dmxwaiverdb import DmxWaiverDb
from dmx.utillib.utils import get_waiver_data, is_user_exist
from dmx.tnrlib.waiver_file import WaiverFile
from bson.json_util import dumps, loads
#from tabulate import tabulate
import tabulate 
from tdma_hsdes import HsdesConnection
from dmx.errorlib.exceptions import *
from dmx.ecolib.ecosphere import EcoSphere
import dmx.abnrlib.flows.waiverhsdticket

class DmxWaiver(object):
    ''' Waiver Class '''
 
    def __init__(self, server_type='prod'):

        self.dmxwaiver = DmxWaiverDb(servertype=server_type)
        self.server_type = server_type

    def add_approver(self, thread, project, deliverable, approver, notify_list, waiver_type='default', subflow=None):
        LOGGER.info('Adding waiver approver/notify_list...')
        valid_thread_milestone = EcoSphere().get_valid_thread_and_milestone()
        valid_thread = list(valid_thread_milestone.keys())

        if thread not in valid_thread and thread != '*':
            raise DmxErrorRMTH01("Invalid thread {}. Please choose from : {}".format(thread, valid_thread))


        added_by = os.environ.get('USER')
        for user in notify_list:
            # check if user exists
            if not dmx.utillib.utils.is_user_exist(user) or not dmx.utillib.utils.is_user_exist(approver):
                raise DmxErrorCFEV02('User \'{}\' does not exists. Please use a valid username.'.format(user))

        approver_details = {'project' : project,
                       'deliverable' : deliverable,
                       'thread': thread,
                       'approver': approver,
                       'notify_list': notify_list,
                       'added_by' : added_by,
                       'waiver_type': waiver_type,
                       'subflow': subflow,
                       'date' : datetime.today().strftime('%Y-%m-%d %H:%M:%S') }
        query = {'project' : project,
                 'deliverable' : deliverable,
                 'thread': thread,
                 'subflow': subflow,
                 'waiver_type': waiver_type}

        result = self.dmxwaiver.update_one_approver(query, approver_details)
        if result.get('nModified')  == 0 and result.get('updatedExisting') is True:
            LOGGER.info('Approval and notify_list for {} {}:{} exists. Modifying ...'.format(thread, project, deliverable))

        LOGGER.info('{} {}:{} - Approval: {}, Notify_list: {}'.format(thread, project, deliverable, approver, notify_list))
        return 0


    def create_waiver(self, thread, milestone, waiverfile, project, waiver_type='default'):
        LOGGER.info('Adding waiver...')

        waiver = {}
        all_waiver = []
        username = os.environ.get('USER')

        wf = WaiverFile()
        wf.load_from_file(waiverfile)

        if not wf.rawdata:
            raise DmxErrorTRWV01('No waiver detected. Please check {}'.format(os.path.abspath(waiverfile)))

        for data in wf.rawdata:
            ip = data[0] 
            deliverable = data[1] 
            subflow = data[2] 
            reason = data[3] 
            if 'autogen by dmx workspace check' in reason:
                raise DmxErrorTRWV04('\'autogen by dmx workspace check\' found in waiver reason. Please amend the correct reason to ease approval process.')
            error = data[4] 

            # only global waiver allow asterik in ip
            if '*' in ip and waiver_type is not 'global':
                raise DmxErrorTRWV04('\'*\' found. Only global waiver allow asterik in IP. Please provide full ip name and try again.'.format(waiverfile))


            if 'UNWAIVABLE' in error:
                raise DmxErrorTRWV04('\'UNWAIVABLE\' keyword found in \'{}\'. Please remove all the UNWAIVABLE error.'.format(waiverfile))

            waiver = {'ip' : ip,
                      'deliverable' : deliverable,
                      'project' : project,
                      'subflow' : subflow,
                      'reason': reason,
                      'error': error,
                      'thread': thread,
                      'milestone': milestone,
                      'user': username,
                      'waiver_type': waiver_type}

            if self.dmxwaiver.find_waivers(waiver).count() > 0:
                hsdescaseid = ''
                for w in self.dmxwaiver.find_waivers(waiver):
                    hsdescaseid = w.get('hsdes_caseid')
                LOGGER.error('Waiver {} already exists in database.'.format(waiver))
                raise DmxErrorTRWV04('Please check hsdes : https://hsdes.intel.com/appstore/article/#/{}.'.format(hsdescaseid))
            waiver['status'] = 'pending'
            waiver['date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            
            all_waiver.append(waiver)

        return all_waiver


    def insert_waiver_to_db(self, all_waiver):
        all_id = []
        mongo_waiver = {}

        for waiver in all_waiver:
            obj_id = self.dmxwaiver.insert_one_waiver(waiver)
            all_id.append(obj_id)
            deliverable = waiver.get('deliverable')
            subflow = waiver.get('subflow')
            if not mongo_waiver.get(deliverable):
                mongo_waiver[deliverable] = [obj_id]
            elif mongo_waiver.get(deliverable):
                mongo_waiver[deliverable].append(obj_id)

            if not mongo_waiver.get((deliverable, subflow)):
                mongo_waiver[deliverable, subflow] = [obj_id]
            elif mongo_waiver.get((deliverable, subflow)):
                mongo_waiver[deliverable, subflow].append(obj_id)


        LOGGER.debug(all_id)
        LOGGER.info(all_waiver)

        return all_id, mongo_waiver

    def add_waivers(self, thread, milestone, waiverfile, project, attachment=None, waiver_type='default', hsdesid=None, approver=None):
        '''
        add new waiver 
        '''
        valid_thread_milestone = EcoSphere().get_valid_thread_and_milestone()
        valid_thread = list(valid_thread_milestone.keys())

        if thread not in valid_thread and thread != '*':
            raise DmxErrorRMTH01("Invalid thread {}. Please choose from : {}".format(thread, valid_thread))
        if thread !='*' and milestone not in valid_thread_milestone[thread] and waiver_type!='global' :
            if milestone == '*':
                raise DmxErrorRMRM01("Invalid milestone {}. Only global waiver allow asterik in milestone. Please choose from : {}".format(milestone, valid_thread_milestone[thread]))
            raise DmxErrorRMRM01("Invalid milestone {}. Please choose from : {}".format(milestone, valid_thread_milestone[thread]))

        # Prepare all waiver document
        all_waiver = self.create_waiver(thread, milestone, waiverfile, project, waiver_type)
        
        # Insert waiver to db

        # if there is any error when creating hsdicket, remove data from mongo
#        try:
            # Create hsd ticket for flow owner to review
            #case_id = self.create_hsd_ticket(all_waiver)
        LOGGER.info('Waiver detail:')
        print('    Waiver file: {}'.format(os.path.abspath(waiverfile)))
        waiver_hsd_ticket =  dmx.abnrlib.flows.waiverhsdticket.WaiverHsdTicket(all_waiver, server_type=self.server_type, attachment=attachment, waiver_type=waiver_type, approver=approver)
        


        if hsdesid:
            waiver_hsd_ticket.append_ticket(hsdesid)
        else:
            waiver_hsd_ticket.create_ticket()

        all_id, mongo_waiver = self.insert_waiver_to_db(all_waiver) 
        waiver_approval_ticket = waiver_hsd_ticket.approval_ticket_id
        approval_by_deliverable = waiver_hsd_ticket.approval_by_deliverable

            # link hedes case to each dmxwaiver 
            # to insert hsdescase and approver detail to waiver in mongodb
        for deliverable, ticket_id in list(waiver_approval_ticket.items()):
            self.link_hsdes_to_dmxwaiver(ticket_id, mongo_waiver[deliverable], approval_by_deliverable[deliverable] )
 #       except Exception as e:
 #           LOGGER.error(e)
 #           LOGGER.error('There is error in while creating HSD ticket. Rollback')
 #           self.delete_waivers(all_id)

        return 0 

    def print_db_data_in_csv(self, data):
        
        if data.count() == 0:
            raise DmxErrorTRWV01('Does not found any matching data in db. Please update your filter.')

        largest = 0
        header = 0
        load_data = loads(dumps(data))
        # find header 
        for load in load_data:
            load_keys = list(load.keys())
            if largest == 0:
                largest= len(load_keys)
                header = load_keys
            elif len(load_keys) > largest:
                largest = len(load_keys)
                header = load_keys

        print(",".join(header) + ',query_date')
        for ea_data in load_data:
            #for k, v in ea_data.items():
            for k in header:
                try:
                    ea_data[k] = str(ea_data[k])
                except KeyError:
                    ea_data[k] = 'NA' 
            print(",".join(list(ea_data.values())) + ',' + datetime.today().strftime('%Y-%m-%d'))
        return 0


    def get_waivers_approver(self, thread=None, project=None, deliverable=None, user=None, user_type=None ):
        '''
        get all waiver'sapprover 
        '''
        data = {}
        if thread:
            data['thread'] = thread
        if project:
            data['project'] = project 
        if deliverable:
            data['deliverable'] = deliverable
        if user:
            data['approver'] = user 
        if user_type:
            data['user_type'] = user_type
        all_waivers_approver = self.dmxwaiver.find_waivers_approver(data)
        self.print_db_data_in_csv(all_waivers_approver)

        return 0

    def get_waivers(self, thread=None, project=None, ip=None, deliverable=None, subflow=None, milestone=None, user=None, status=None):
    #def get_waivers(self, thread='*', ip='*', deliverable='*', subflow='*', milestone='*', user='*', status='*', project='*'):
        '''
        get all central waiver
        '''
        valid_thread_milestone = EcoSphere().get_valid_thread_and_milestone()
        valid_thread = list(valid_thread_milestone.keys())

        if thread and thread not in valid_thread:
            raise DmxErrorRMTH01("Invalid thread {}. Please choose from : {}".format(thread, valid_thread))
        if milestone and milestone not in valid_thread_milestone[thread]:
            raise DmxErrorRMRM01("Invalid milestone {}. Please choose from : {}".format(milestone, valid_thread_milestone[thread]))


        data = {}
        if thread is not None:
            data['thread'] = thread
        if project is not None:
            data['project'] = project
        if ip is not None:
            data['ip'] = ip
        if deliverable is not None:
            data['deliverable'] = deliverable
        if subflow is not None:
            data['subflow'] = subflow
        if milestone is not None:
            data['milestone'] = milestone
        if user is not None:
            data['user'] = user
        if status is not None:
            data['status'] = status 
        all_waiver = self.dmxwaiver.find_waivers(data)
        self.print_db_data_in_csv(all_waiver)

        return 0

    def delete_waivers_approver(self, thread, project, deliverable):
        '''
        Delete waiver's  approver 
        ''' 
        LOGGER.info('Deleting waivers approver/notify_list...')
        waiversapprover = {'thread':thread, 'project':project, 'deliverable':deliverable}
        self.dmxwaiver.delete_waivers_approver(waiversapprover)

        return 0


    def delete_waivers(self, ids):
        '''
        Delete document from collection
        ''' 
        LOGGER.info('Deleting waiver...')
        user = os.environ.get('USER')
        is_admin = dmx.utillib.admin.is_admin(user)
        if is_admin:
            LOGGER.debug('User \'{}\' is dmx admin. Can delete all id'.format(user))

        for ea_id in ids:
            if is_admin:
                waiver_id = {'_id' : ObjectId(ea_id)}
            else:
                waiver_id = {'_id' : ObjectId(ea_id), 'user':user}

            if self.dmxwaiver.find_waivers(waiver_id).count() == 1:
                self.dmxwaiver.delete_waiver_document(waiver_id)
            else:
                raise DmxErrorTRWV01('Only admin and requester of the waiver can delete this waiver.')


        LOGGER.info('Succesfully deleted : {}'.format(ids))
        return 0

           
    def link_hsdes_to_dmxwaiver(self, case_id, all_id, approver):
        '''
        Link HSDES case id to each waiver 
        '''
        LOGGER.debug('Update to caseid {} and approver {} in mongo {}'.format(case_id, approver, all_id))
        self.dmxwaiver.update_caseid(case_id, all_id, approver)


    def insert_hsdes_mapping_data(self, mapping_data):
        csv_mapping_data = copy.deepcopy(mapping_data)
        mapping_data['updated_by'] = os.environ.get('USER')
        mapping_data['date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        self.dmxwaiver.insert_to_mapping_collection(csv_mapping_data, mapping_data)

    def get_hsdes_mapping_data(self):
        return self.dmxwaiver.find_mapping_data()[0]

if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    
