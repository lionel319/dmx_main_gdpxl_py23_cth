#!/usr/bin/env python

"""
Base class for DMX Mongo Database. 
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
import ssl
LOGGER = logging.getLogger(__name__)

class DmxMongoDbBaseError(Exception):
    pass

class DmxMongoDbBase(object):
    ''' DmxMongoDbBase Class '''
  
    def __init__(self, uri=None, database=None):
        self.uri = uri
        self.database = database

    def connect(self):
        '''
        Connect to mongodb. Fail if timeout.
        https://stackoverflow.com/questions/30539183/how-do-you-check-if-the-client-for-a-mongodb-instance-is-valid
        '''
        LOGGER.debug('Connecting to MongoDB:{}'.format(self.uri)) 
        self.client = MongoClient(self.uri)
        self.db = self.client[self.database]

        try:
            self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError:
            raise pymongo.errors.ServerSelectionTimeoutError('Connection timeout. Failed to connect to MongoDB:{}:{}'.format(self.uri, self.database)) 
        return self 

if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    
