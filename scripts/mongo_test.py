#!/usr/bin/env python

import sys
from urllib import quote_plus
from pprint import pprint, pformat
#sys.path.insert(0, '/nfs/site/disks/psg_data_1/lionelta/pymongo/p/psg/ctools/python/2.7.13/linux64/suse/lib/python2.7/site-packages')
sys.path.insert(0, '/nfs/site/disks/psg_flowscommon_1/common_info/pymongo380a')
from pymongo import MongoClient
from bson.objectid import ObjectId

def main():
    host = '10.64.5.103'
    port = '7717'
    socket_path = '{}:{}'.format(host, port)
    username = 'DMXTEST1_so'
    password = 'y1bKz2mU924Si6h'
    database = 'DMXTEST1'
    collection = 'test1'
    authmech = 'SCRAM-SHA-1'
    uri = 'mongodb://DMXTEST1_so:y1bKz2mU924Si6h@10.64.5.102:7717,10.64.5.103:7717,10.64.168.70:7717/DMXTEST1?replicaSet=mongo7717'
    print "uri:{}".format(uri)

    client = MongoClient(uri)
    db = client[database]
    c = db[collection]
    for d in c.find({}):
        print d

    '''
    ### Insert data
    c.insert_one( {'name': 'Chun Fui', 'age': 33, 'sex': 'm'} )
    c.insert_one( {'name': 'Chee Yong', 'age': 18, 'sex': 'f'} )
    c.insert_one( {'name': 'Jun Keat', 'age': 23, 'sex': 'm'} )
    c.insert_one( {'name': 'Wei Pin', 'age': 25, 'sex': 'm'} )
    '''

    x = c.find({'_id': ObjectId('5d5e643e5951cec15b126adb')})
    print x[0]
    print type(x)



if __name__ == "__main__":
    sys.exit(main())
