#!/usr/bin/env python

"""
The Mysql API for syncpoint_lock and syncpoint_lock_log.


"""

import logging
import sys
import os
from pprint import pprint, pformat
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)
import dmx.utillib.dmxdbbase
import dmx.abnrlib.icm


LOGGER = logging.getLogger(__name__)


########################################################
############## SYNCPOINT LOCK LOG API ##################
########################################################
class RequalDbApiError(Exception):
    pass
class RequalDbApi(dmx.utillib.dmxdbbase.DmxDbBase):
    '''
    (
        (ID, project, variant, libtype, config, userid, thread, milestone, dt, comment)
        (3L, 'i10socfm', 'liotest1', 'None', 'REL5.0FM8revA0--LioTestHier__17ww103a', 'lionelta', 'FM6revA0', '5.0', datetime.datetime(2019, 7, 12, 1, 0, 16), 'for fun only ...'), 
        (6L, 'i10socfm', 'liotest1', 'None', 'REL5.0FM8revA0--Icm36179__17ww084a', 'jwquah', 'FM6revA0', '5.0', datetime.datetime(2019, 7, 12, 1, 6, 34), 'for fun only ...')
        ...   ...   ...
    )
    '''

    def __init__(self, host='', port='', username='', password='', db='', servertype='prod'):
       
        super(RequalDbApi, self).__init__(host=host, port=port, username=username, password=password, db=db, servertype=servertype)
        self.table = 'REQUAL'
        self.icm = dmx.abnrlib.icm.ICManageCLI()


    def add_log(self, project, variant, libtype, config, thread, milestone, userid, comment):
        ''' insert new log entry '''

        ### Pre-check, to ensure data that is entered into the db is not rubbish.
        if not self.icm.config_exists(project, variant, config, None if libtype == 'None' else libtype):
            raise RequalDbApiError("{}/{}:{}@{} can not be found!".format(project, variant, libtype, config))

        data = {
            'project': project,
            'variant': variant,
            'libtype': libtype,
            'config': config,
            'thread': thread,
            'milestone': milestone,
            'userid': userid,
            'comment': comment,
        }
        return self._add_log(tablename=self.table, **data)


    def get_logs(self, **kwargs):
        return self._get_logs(tablename=self.table, **kwargs)


    def delete_logs(self, **kwargs):
        return self._delete_logs(tablename=self.table, **kwargs)


    def create_table(self):
        sql = """ CREATE TABLE {} (
            ID int NOT NULL AUTO_INCREMENT,
            project VARCHAR(50) NOT NULL,
            variant VARCHAR(50) NOT NULL,
            libtype VARCHAR(20) NOT NULL,
            config VARCHAR(50) NOT NULL,
            userid VARCHAR(20) NOT NULL,
            thread VARCHAR(20) NOT NULL,
            milestone VARCHAR(8) NOT NULL,
            dt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            comment VARCHAR(255) NOT NULL,
            PRIMARY KEY (ID)
            ) """.format(self.table)
        LOGGER.debug("Creating table {} ...".format(self.table))
        self.cursor.execute(sql)


    def __X_DROP_TABLE_X__(self):
        super(RequalDbApi, self).__DROP_TABLE(table=self.table)




if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)


