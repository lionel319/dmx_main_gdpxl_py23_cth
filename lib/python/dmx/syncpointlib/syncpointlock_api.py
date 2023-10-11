#!/usr/bin/env python

"""
The Mysql API for syncpoint_lock and syncpoint_lock_log.


"""

import logging
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, LIB)
import dmx.utillib.dmxdbbase


LOGGER = logging.getLogger(__name__)


########################################################
############## SYNCPOINT LOCK LOG API ##################
########################################################
class SyncpointLockLogApiError(Exception):
    pass
class SyncpointLockLogApi(dmx.utillib.dmxdbbase.DmxDbBase):

    def __init__(self, host='', port='', username='', password='', db='', servertype='prod'):
        super(SyncpointLockLogApi, self).__init__(host=host, port=port, username=username, password=password, db=db, servertype=servertype)
        self.table = 'SYNCPOINTLOCKLOG'


    def log(self, syncpoint, userid, action):
        ''' insert new log entry '''
        sql = ''' INSERT INTO {} (syncpoint, userid, action)
            VALUES ('{}', '{}', '{}') '''.format(self.table, syncpoint, userid, action)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            LOGGER.debug("Logged {}/{}/{}".format(syncpoint, userid, action))
        except:
            self.conn.rollback()
            LOGGER.error("Failed logging {}/{}/{}".format(syncpoint, userid, action))
            raise


    def get_logs_by_user(self, userid):
        ''' return a list of all (raw) log entries by a given userid 
        
        retlist = (
            (2L, 'tan', 'lionelta', 'lock', datetime.datetime(2018, 8, 8, 0, 59, 13)), 
            (5L, 'yoke', 'lionelta', 'lock', datetime.datetime(2018, 8, 8, 0, 59, 14)), 
            (8L, 'liang', 'lionelta', 'unlock', datetime.datetime(2018, 8, 8, 0, 59, 14)), 
            ...   ...   ...
        )
        '''
        sql = ''' SELECT * FROM {} WHERE userid = '{}' '''.format(self.table, userid)
        return self.fetchall_raw_data(sql)


    def get_logs_by_syncpoint(self, syncpoint):
        ''' return a list of all (raw) log entries by a given syncpoint 
        
        retlist = (
            (2L, 'tan', 'lionelta', 'lock', datetime.datetime(2018, 8, 8, 0, 59, 13)), 
            (5L, 'yoke', 'lionelta', 'lock', datetime.datetime(2018, 8, 8, 0, 59, 14)), 
            (8L, 'liang', 'lionelta', 'unlock', datetime.datetime(2018, 8, 8, 0, 59, 14)), 
            ...   ...   ...
        )
        '''
        sql = ''' SELECT * FROM {} WHERE syncpoint = '{}' '''.format(self.table, syncpoint)
        return self.fetchall_raw_data(sql)


    def get_logs(self):
        ''' return a list of all (raw) log entries by a given syncpoint 
        
        retlist = (
            (2L, 'tan', 'lionelta', 'lock', datetime.datetime(2018, 8, 8, 0, 59, 13)), 
            (5L, 'yoke', 'lionelta', 'lock', datetime.datetime(2018, 8, 8, 0, 59, 14)), 
            (8L, 'liang', 'lionelta', 'unlock', datetime.datetime(2018, 8, 8, 0, 59, 14)), 
            ...   ...   ...
        )
        '''
        sql = ''' SELECT * FROM {}  '''.format(self.table)
        return self.fetchall_raw_data(sql)


    def create_table(self):
        sql = """ CREATE TABLE {} (
            ID int NOT NULL AUTO_INCREMENT,
            syncpoint CHAR(200) NOT NULL,
            userid CHAR(20) NOT NULL,
            action CHAR(10) NOT NULL,
            dt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (ID)
            ) """.format(self.table)
        LOGGER.debug("Creating table {} ...".format(self.table))
        self.cursor.execute(sql)


    def __X_DROP_TABLE_X__(self):
        super(SyncpointLockLogApi, self).__DROP_TABLE(table=self.table)




########################################################
############## SYNCPOINT LOCK API ######################
########################################################
class SyncpointLockApiError(Exception):
    pass
class SyncpointLockApi(dmx.utillib.dmxdbbase.DmxDbBase):
   
    def __init__(self, host='', port='', username='', password='', db='', servertype='prod'):
        super(SyncpointLockApi, self).__init__(host=host, port=port, username=username, password=password, db=db, servertype=servertype)
        self.table = 'SYNCPOINTLOCK'

    def lock(self, syncpoint):
        ''' lock a given syncpoint 
        
        return 0 upon success, else return 1
        '''
        if not syncpoint:
            raise SyncpointLockApiError("Please provide a syncpoint for lock. syncpoint can not be empty.")

        sql = """ INSERT INTO {} (syncpoint)
            VALUES ('{}') """.format(self.table, syncpoint)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            LOGGER.debug("Locked {}".format(syncpoint))
        except:
            self.conn.rollback()
            LOGGER.error("Failed to Lock {}".format(syncpoint))
            raise
        return 0



    def unlock(self, syncpoint):
        ''' unlock a given syncpoint 
        
        return 0 upon success, else return 1
        '''
        if not syncpoint:
            raise SyncpointLockApiError("Please provide a syncpoint for unlock. syncpoint can not be empty.")

        sql = """ DELETE FROM {} WHERE syncpoint = '{}' """.format(self.table, syncpoint)

        try:
            self.cursor.execute(sql)
            self.conn.commit()
            LOGGER.debug("Unlocked {}".format(syncpoint))
        except:
            self.conn.rollback()
            LOGGER.error("Failed to UnLock {}".format(syncpoint))
            raise
        return 0


    def get_locked_syncpoints(self):
        ''' return the list of locked syncpoints 
       
       retlist = [syncpoint, syncpoint, ...]
        '''
        sql = """ select * from {} """.format(self.table)
        rawdata = self.fetchall_raw_data(sql)
        return [x[1] for x in rawdata]


    def is_syncpoint_locked(self, syncpoint):
        ''' return non-zero is syncpoint is locked, else return 0 '''
        sql = ''' SELECT * FROM {} WHERE syncpoint = '{}' '''.format(self.table, syncpoint)
        LOGGER.debug("Running mysql command: {}".format(sql))
        try:
            self.cursor.execute(sql)
            return self.cursor.rowcount
        except:
            LOGGER.error("Failed fetching data: {}".format(sql))
            raise

    
    def raise_error_if_syncpoint_is_locked(self, syncpoint):
        ''' raise error if syncpoint is locked, else return 0 '''
        if self.is_syncpoint_locked(syncpoint):
            raise SyncpointLockApiError("Syncpoint is locked. Please run 'syncpoint lock --unlock {}' to unlock it.".format(syncpoint))
        return 0


    def create_table(self):
        sql = """ CREATE TABLE {} (
            ID int NOT NULL AUTO_INCREMENT,
            syncpoint CHAR(200) NOT NULL,
            PRIMARY KEY (ID)
            ) """.format(self.table)
        LOGGER.debug("Creating table {} ...".format(self.table))
        self.cursor.execute(sql)

    def __X_DROP_TABLE_X__(self):
        super(SyncpointLockApi, self).__DROP_TABLE(table=self.table)




if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)


