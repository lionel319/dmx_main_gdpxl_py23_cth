from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import object
import datetime
import os
import shutil

from prettytable import PrettyTable

from .get_new_dbh import get_new_dbh
from .logger import Logger

logger = Logger()

# TODO: this should be changed when management provides an approrpriate disk
#       for now we'll use this location because it's supported for all 
#       projects when ran by psginfraadm
__AUDIT_STORE__ = '/nfs/sc/disks/swuser_work_mconkin/audits';

class DBPrinter(object):

    def store_ip(self, ip):
        pass

    def store_rel(self, rel):
        self.rel_id = rel
        
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            SELECT 
                Rel.workspace_location, ms.ms_name, 
                IP.ip_name, Rel.rel_name, IP.project_id
            FROM Rel 
            JOIN ms ON Rel.ms_id = ms.ms_id 
            JOIN IP ON Rel.ip_id = IP.ip_id
            WHERE Rel.rel_id = %s
        """, (self.rel_id,));

        row = cursor.fetchone();
        self.project_id = row[4]
        self.ip_name = row[2]
        self.rel_name = row[3]
 
        return row[0]

    def lock(self):
        dbh = get_new_dbh()
        dbh.cursor().execute("""
            UPDATE Rel
            SET is_parsed = 0
            WHERE rel_id = %s
        """, (self.rel_id,))
        dbh.commit()

    def store_owner(self, owner):
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            SELECT owner_id
            FROM user
            WHERE owner_id = %s
        """, (owner,))
        
        user_row = cursor.fetchone()
        
        # an owner may not exist, so create on if none
        if not user_row:
            cursor.execute("""
                INSERT INTO user
                SET owner_id = %s,
                email = %s
            """, (owner, 'unregistered@intel.com'))
            dbh.commit()
        
        cursor.execute("""
            UPDATE Rel
            SET owner_id = %s
            WHERE rel_id = %s
        """, (owner, self.rel_id))
        dbh.commit()

    def store_hierarchy(self, sub_ip, bom):
        cursor = get_new_dbh().cursor()
        cursor.execute("""
            SELECT rel_id
            FROM Rel
            JOIN IP on Rel.ip_id = IP.ip_id
            WHERE rel_name = %s
            AND IP.ip_name = %s
            AND project_id = %s
        """, (bom, sub_ip, self.project_id))

        # TODO: is there a case where there are duplicate rels? If that is the
        #       case, then it needs to be recorded. This suggests the need for
        #       some sort of non volatile error log as sanity checks, not just
        #       a print statement.
        #
        #       Something else is wrong if nothing gets returned, as it's
        #       assumed that the child rel must already exist in the database.
        #       For now just return if there is unexpected behavior
        if cursor.rowcount != 1:
            logger.error('there are duplicates of a release in the database')
            logger.error('or the child rel does not exist in the database')
            return

        child_rel_id = cursor.fetchone()[0]

        # add the child rel into the hierarchy table
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            INSERT INTO hierarchy
            SET rel_id = %s,
            child_rel_id = %s
        """, (self.rel_id, child_rel_id))
        dbh.commit()

    def store_deliverable(self, deliverable, not_por, bom, owner, email, waived):
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            SELECT owner_id
            FROM user
            WHERE owner_id = %s
        """, (owner,))

        user_row = cursor.fetchone()
        
        # an owner may not exist, so create on if none
        if not user_row:
            cursor.execute("""
                INSERT INTO user
                SET owner_id = %s,
                email = %s
            """, (owner, email + '@intel.com'))
            dbh.commit()

        # otherwise just set the user guid to the existing one
        else:
            user_guid = user_row[0]

        cursor.execute("""
            INSERT INTO deliverable 
            SET del_name = %s,
            rel_id = %s,
            not_por = %s,
            bom = %s,
            owner_id = %s,
            is_waived = %s
        """, (deliverable, self.rel_id, not_por, bom, owner, waived))
        dbh.commit()

        return cursor.lastrowid

    def store_cell(self, cell):
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            INSERT INTO cell
            SET cell_name = %s,
            rel_id = %s
        """, (cell, self.rel_id))
        dbh.commit()

        return cursor.lastrowid

    def store_checker(self, checker):

        # store checkers into database 
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            INSERT INTO checker
            SET cell_id = %s,
            del_id = %s,
            checker_name = %s,
            flow = %s,
            subflow = %s,
            not_por = %s
        """, (
                checker['cell_id'], 
                checker['del_id'],
                checker['ref'].checkname, 
                checker['ref'].flow, 
                checker['ref'].subflow,
                checker['not_por']
            )
        )
        dbh.commit()

        checker['checker_id'] = cursor.lastrowid

        # create the directory to store all the audit files
        audit_dir =__AUDIT_STORE__+'/'+self.ip_name +'/'+self.rel_name+'/'+checker['del_name'] 
        if not os.path.exists(audit_dir):
            os.makedirs(audit_dir)

        audit_list_id = None
        if 'audit_list' in list(checker.keys()):
            al = checker['audit_list'].split('/')[-1]
            cursor.execute("""
                INSERT INTO audit_list
                SET audit_list_name = %s,
                checker_id = %s
            """, (al, checker['checker_id']))
            dbh.commit()

            if not os.path.isfile(audit_dir+'/'+al):
                shutil.copy(checker['audit_list'], audit_dir)

            audit_list_id = cursor.lastrowid
            
        for audit in checker['audits']:
            a = audit.split('/')[-1]
            cursor.execute("""
                INSERT INTO audit
                SET audit_name = %s,
                checker_id = %s,
                audit_list_id = %s
            """, (a, checker['checker_id'], audit_list_id))
            dbh.commit()

            if not os.path.isfile(audit_dir+'/'+a):
                try:
                    shutil.copy(audit, audit_dir)
                except IOError as err:
                    logger.error(str(err))

    def store_resource(self, c, resource, used_ver, status, min_ver, crit_ver):
        dbh = get_new_dbh()
        cursor = dbh.cursor()
        cursor.execute("""
            INSERT INTO resource_used
            SET resource_name = %s,
            used_ver = %s,
            checker_id = %s,
            status = %s,
            min_version = %s,
            critical_version = %s
        """, (
                resource,
                used_ver.lstrip('/'), 
                c['checker_id'],
                status, 
                min_ver,
                crit_ver
            )    
        )
        dbh.commit()

    def unlock(self):
        # finally update Rel for successful parsing
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dbh = get_new_dbh()
        dbh.cursor().execute("""
            UPDATE Rel
            SET is_parsed = 1,
            date_parsed = %s
            WHERE rel_id = %s
        """, (now, self.rel_id,))
        dbh.commit()

class StdoutPrinter(object):
    def __init__(self, override_file=None, output_file=None):
        self._cwd = os.getcwd()
        if output_file: 
            self.out_file = output_file
        
        self._overrides = None
        if not override_file: 
            return

        self._overrides = []
        with open(override_file, 'r') as rows:
            for row in rows:
                resource, version = row.strip().split('/', 1)
                self._overrides.append({'name': resource, 'version': version})
                
    def store_ip(self, ip):
        self.ip = ip
        
    def store_rel(self, rel):
        return os.getcwd() 

    def lock(self):
        try:
            self.out_file = open(self.out_file, 'w')
        except AttributeError: 
            now = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            self.out_file = open(os.getcwd() + '/minarc-results_' + self.ip + '_' + now + '.txt', 'w')
        self.table = PrettyTable()
        self.table.field_names = ['IP', 'Deliverable', 'Audit File', 'Resource', 'Last Important Version', 'Minimum Version', 'Used Version', 'Status']
        print('-'*176)
        print('|{:^27}|{:^13}|{:^50}|{:^17}|{:^17}|{:^17}|{:^17}|{:^10}|'.format(' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '))
        print('|{:^27}|{:^13}|{:^50}|{:^17}|{:^17}|{:^17}|{:^17}|{:^10}|'.format('IP', 'Deliverable', 'Audit File', 'Resource', 'Last Important Version', 'Minimum Version', 'Used Version', 'Status'))
        print('|{:^27}|{:^13}|{:^50}|{:^17}|{:^17}|{:^17}|{:^17}|{:^10}|'.format(' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '))
        print('-'*176)

    def store_owner(self, owner):
        pass   

    def store_hierarchy(self, sub_ip, bom):
        pass

    def store_deliverable(self, deliverable, not_por, bom, owner, email, waived):
        return 0

    def store_cell(self, cell):
        return 0

    def store_checker(self, checker):
        audit_pretty = None
        if 'audit_list' in list(checker.keys()):
            audit_pretty = checker['audit_list'].split('/')[-1]
        
        for audit in checker['audits']:
            a = audit.split('/')[-1]
            if not audit_pretty:
                audit_pretty = a

        self.deliverable = checker['del_name']
        self.cell = checker['cell_name']
        self.checker = checker['ref'].checkname
        self.audit = audit_pretty

    def store_resource(self, c, resource, used_ver, status, min_ver, crit_ver):
        
        if self._overrides:
            for overriden_resource in self._overrides:
                if overriden_resource['name'] == resource:
                    if overriden_resource['version'] == used_ver.lstrip('/'):
                        status = 'Not Met'

        self.table.add_row([    
            self.ip, 
            self.deliverable, 
            self.audit , 
            resource,
            min_ver, 
            crit_ver, 
            used_ver.lstrip('/'), 
            status
        ])

        print('|{:^27}|{:^13}|{:^50}|{:^17}|{:^17}|{:^17}|{:^17}|{:^10}|'.format(
            self.ip, 
            self.deliverable, 
            self.audit , 
            resource,
            min_ver, 
            crit_ver, 
            used_ver.lstrip('/'), 
            status
        ))

    def unlock(self):
        self.out_file.write(self.table.get_string())
        self.out_file.close()
        
        print('-'*176) 
