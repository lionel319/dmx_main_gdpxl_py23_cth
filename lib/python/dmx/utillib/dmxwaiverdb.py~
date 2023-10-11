#!/usr/bin/env python

"""
Base class for DMX MySql Database. 
"""
import sys
sys.path.insert(0, '/nfs/site/disks/psg_flowscommon_1/common_info/pymongo380a')
import pymongo
from pymongo import MongoClient, UpdateOne, DeleteOne
from bson.objectid import ObjectId
import logging
import copy
import csv
import dmx.utillib.admin
import datetime
LOGGER = logging.getLogger(__name__)
from dmx.utillib.dmxmongodbbase import DmxMongoDbBase
from dmx.errorlib.exceptions import *

import os

class DmxWaiverDb(Exception):
    pass

class DmxWaiverDb(DmxMongoDbBase):
    ''' DmxWaiverDb Class '''
 
    SERVER = {'prod':{}, 'test':{} }
    SERVER['prod']['URI'] = 'mongodb://DMX_so:b73ZgG2Jq03Fv1i@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/DMX?replicaSet=mongo8150'
    SERVER['test']['URI'] = 'mongodb://DMX_TEST_so:tA5Y4Zf80H9YxT8@p1fm1mon152.amr.corp.intel.com:8150,p2fm1mon152.amr.corp.intel.com:8150,dr1ormon152fm1.amr.corp.intel.com:8150/DMX_TEST?replicaSet=mongo8150'

    def __init__(self, servertype='prod'):
        self.servertype = servertype
        self.uri = self.SERVER[servertype]['URI']
        if self.servertype == 'prod':
            self.database = 'DMX'
        if self.servertype == 'test':
            self.database = 'DMX_TEST'

        DmxMongoDbBase.__init__(self, self.uri, self.database)
        self.connect() 
        LOGGER.debug('Succesfully connect to mongo db')

    
    def insert_one_approver(self, data):
        '''
        add new approver 
        '''
        if not data:
            raise DmxErrorTRWV01('Cannot insert blank data to db.')
        ObjId = self.db.waivers_approver.insert_one(data).inserted_id

        return ObjId 

    def update_one_approver(self, query, data):
        '''
        add new approver 
        '''
        if not data:
            raise DmxErrorTRWV01('Cannot insert blank data to db.')
        cursor = self.db.waivers_approver.update(query,  {'$set':data}, upsert=True)
        #cursor = self.db.waivers_approver.update(query,  {'$setOnInsert':data}, upsert=True)

        return cursor



    def insert_one_waiver(self, data):
        '''
        add new waiver 
        '''
        if not data:
            raise DmxErrorTRWV01('Cannot insert blank data to db.')
        ObjId = self.db.waivers.insert_one(data).inserted_id

        return ObjId 

    def find_waivers_approver(self, data):
        '''
        find all matched waivers_approver 
        '''
        return self.db.waivers_approver.find(data)
 
    def find_waivers(self, data):
        '''
        find all matched waiver 
        '''
        return self.db.waivers.find(data)

    def delete_waivers_approver(self, data):
        '''
        Delete one waiver approver 
        '''
        thread = data.get('thread')
        project = data.get('project')
        deliverable = data.get('deliverable')

        deleted_count = self.db.waivers_approver.delete_many(data).deleted_count

        if deleted_count:
            LOGGER.info('Approval and notify list for {} {}:{} deleted'.format(thread, project, deliverable))
        else:
            LOGGER.info('Approval and notify list for {} {}:{} not found. Nothing has been deleted.'.format(thread, project, deliverable))
        
    def delete_waiver_document(self, data):
        '''
        Delete one waiver document
        ''' 
        deleted_count = self.db.waivers.delete_one(data).deleted_count
        if deleted_count:
            LOGGER.info('id : \'{}\' found and deleted'.format(data.get('_id')))
        else:
            LOGGER.info('id : \'{}\' not found.'.format(data.get('_id')))
        
    def delete_rejected_collection(self, ids, status, collection=''):
        '''
        Delete rejected collection from dmx waiver mongodb
        '''
        LOGGER.info('Delete rejected dmx waiver in mongodb')
        request = []

        for hsd_id in ids:
            LOGGER.debug('Drop collection from db - HSD-Case: {} Status: {} '.format(hsd_id, status))
            for ea_collection in self.db.waivers.find({ 'hsdes_caseid': int(hsd_id) }):
                LOGGER.debug('Delete ObjectId(\'{}\').'.format(str(ea_collection.get('_id'))))
                request.append(DeleteOne({ '_id':ea_collection.get('_id') }))

        if request:
            result = self.db.waivers.bulk_write(request)
            self.db.waivers.execute
            LOGGER.debug('Drop collection done.')
        else:
            LOGGER.debug('No rejected case found.')

    def update_approval_status(self, ids, status, collection=''):
        '''
        Update approval status of dmx waiver
        '''
        request = []

        LOGGER.info('Update status of dmx waiver that get approved.')
        for hsd_id in ids:
            LOGGER.debug('Update approval status - HSD-Case: {} Status: {} '.format(hsd_id, status))
            for ea_collection in self.db.waivers.find({ 'hsdes_caseid': int(hsd_id) }):
                LOGGER.debug('Update ObjectId(\'{}\'). Set status to {}'.format(str(ea_collection.get('_id')), status))
                request.append(UpdateOne({ '_id':ea_collection.get('_id') }, {'$set': { 'status': status } }))

        if request:
            LOGGER.debug('Update status in db...')
            result = self.db.waivers.bulk_write(request)
            self.db.waivers.execute
            LOGGER.debug('Update status done.')
        else:
            LOGGER.debug('No approval case found.')

    def set_waivers_approver_field_by_approver(self, approver, **kwargs):
        '''
        set field for waiver document 
        '''
        request = []
        for ea_collection in self.db.waivers_approver.find({ 'approver': approver }):
            for k, v in kwargs.items():
                 LOGGER.debug('Appending ObjectId(\'{}\'), set {} to {}'.format(str(ea_collection.get('_id')), k, v))
            request.append(UpdateOne({ '_id':ea_collection.get('_id') }, {'$set': kwargs }))

        if request:
            LOGGER.debug('Updating db...')
            result = self.db.waivers_approver.bulk_write(request)
            self.db.waivers_approver.execute
            LOGGER.debug('Update done.')
        else:
            LOGGER.debug('No hsd case found.')

           
    def update_caseid(self, case_id, object_ids, approver):
        '''
        Update case id in collection
        '''
        # Copy from https://stackoverflow.com/questions/35480660/bulk-update-in-pymongo-using-multiple-objectid

        LOGGER.debug('Update case id')
        bulk =  self.db.waivers.initialize_unordered_bulk_op()
        counter = 0
        for ea_id in object_ids:
            # process in bulk
            bulk.find({ '_id': ea_id }).update({ '$set': { 'hsdes_caseid': case_id, 'approver': approver } })
            counter += 1

            if (counter % 500 == 0):
                bulk.execute()
                bulk = db.testdata.initialize_ordered_bulk_op()

        
        if (counter % 500 != 0):
            bulk.execute()
        LOGGER.debug('Update case id done')


    def insert_to_mapping_collection(self, csv_mapping_data, mapping_data):
        if not mapping_data:
            raise DmxErrorTRWV01('Cannot insert blank data to db.')
        #Delete then add
        self.db.hsdes_mapping.delete_many({})
        self.db.hsdes_mapping.update(csv_mapping_data,  {'$set':mapping_data}, upsert=True)


    def find_mapping_data(self):
        return self.db.hsdes_mapping.find()




if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    
