#!/usr/bin/env python

"""
The Web API for accessing sw-web/syncpoint models.

Usage:-
=======
### For official production server,
s = SyncpointWebAPI()

### For dev server,
s = SyncpointWebApi(web_server='sj-webdev1')

### Get all available registered syncpoints
s.get_syncpoints()

### Register(add) a new syncpoint
s.create_syncpoint('syncpoint name', 'syncpoint_project', 'userid', 'description')

### Associate(add) a project/variant to the newly created syncpoint
s.add_syncpoint('syncpoint name', 'i14socnd', 'ar_lib', 'yltan')

### Release a configuration to the an associated project/variant for its syncpoint
s.release_syncpoint('syncpoint name', 'i14socnd', 'ar_lib', 'REL2.0ND5revA__15ww123', 'yltan')

### To get a released configuration of a released syncpoint for a particular variant
s.get_syncpoint_configuration('syncpoint name', 'ar_lib')

### Get/add/delete a user from the syncpoint_lead database.
s.add_user('yltan', 'admin')
s.add_user('yltan', 'lead')
s.add_user('yltan', 'email')

s.get_user_roles('yltan')
s.get_users_by_role('admin')

s.delete_user('yltan', 'admin')

"""

import urllib
import urllib2 
import logging
import json
from datetime import datetime
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.dmxdbbase import DmxDbBase
import dmx.mysql as mysql

class SyncpointWebAPIError(Exception):
    pass

class SyncpointWebAPI(object):
   
    def __init__(self, web_server='sw-web.altera.com', base_url='syncpoint'):
        self.base_url = base_url
        self.web_server = web_server
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialize SyncpointWebAPI instaince for {} ...".format(self.base_url))
        self.icm = ICManageCLI()
        self.db = DmxDbBase(servertype='prod')
        

        self.RETRY_COUNT = 5
        self.TRIED = 0
        self.DELAY_SECONDS_BETWEEN_RETRY = 10



    def syncpoint_exists(self, syncpoint):
        ''' Check if the given syncpoint name exists
        return True if exists, False if non-exists.
        '''
        splist = [sp[0] for sp in self.get_syncpoints()]
        return syncpoint in splist

    def syncpoint_category_exists(self, category):
        ''' Check if the given syncpoint_project(category) exists
        return True if exists, False if non-exists.
        '''
        splist = [sp[1] for sp in self.get_syncpoints()]
        return category in splist

    def project_variant_exists(self, syncpoint, project, variant):
        ''' Check if the given project/variant is added to the syncpoint
        return True if exists, False if non-exists.
        '''
        pvclist = self.get_releases_from_syncpoint(syncpoint)
        for p,v,c in pvclist:
            if p == project and v == variant:
                return True
        return False

    def project_variant_released(self, syncpoint, project, variant):
        ''' Check if the given project/variant is released to the syncpoint
        return True if exists, False if non-exists.
        '''
        pvclist = self.get_releases_from_syncpoint(syncpoint)
        for p,v,c in pvclist:
            if p == project and v == variant and c:
                return True
        return False

    def create_syncpoint(self, syncpoint, category, userid, description=''):
        ''' Register a new syncpoint. 
        Error out if syncpoint by the name already exists.
        '''
        creator_id = self._extract_user_id_from_user(userid)

        self.db.connect()._add_log(
            tablename='syncpoint_syncpoint',
            name=syncpoint,
            category=category,
            creator_id=creator_id,
            description=description,
            creationDate=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return 0
         

    def add_syncpoint(self, syncpoint, project, variant, userid):
        ''' Associate the given project/variant with the given syncpoint.
        The specified variant is expected to register a release of that variant 
        against this syncpoint. 
        The project/variant here is an ICM project/variant name.
        
        Error out if either the syncpoint of the project/variant doesn't exist.
        Error out if either the project/variant is not a valid ICM data.
        '''
        if not self.icm.project_exists(project):
            raise SyncpointWebAPIError("Project {} does not exist.".format(project))
        if not self.icm.variant_exists(project, variant):
            raise SyncpointWebAPIError("variant {} does not exist in project {}.".format(variant, project))
        
        releaser_id = self._extract_user_id_from_user(userid)            
        syncpoint_id = self._extract_syncpoint_id_from_syncpoint(syncpoint)

        self.db.connect()._add_log(
            tablename='syncpoint_release',
            project=project,
            variant=variant,
            configuration='',
            syncpoint_id=syncpoint_id,
            releaser_id=releaser_id,
            updatedDate=datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        )

        return 0

    def delete_syncpoint(self, syncpoint, project='', variant=''):
        ''' Delete the association between the given project/variant and the given
        syncpoint, or to delete the entire syncpoint altogether if project/variant is not provided.

        Error out if trying to delete a syncpoint which has associated project/variants
        (safety feature -- you must delete all the project/variants then only can you delete the        syncpoint) 
        syncpoint) 
        '''
        syncpoint_id = self._extract_syncpoint_id_from_syncpoint(syncpoint)

        if project == '' and variant == '':
            if self.db.connect().fetchall_raw_data("""
                SELECT * FROM syncpoint_release
                WHERE syncpoint_id = (
                    SELECT id from syncpoint_syncpoint
                    WHERE name = '{}'
                )
            """.format(
                    syncpoint
                )
            ):
                raise SyncpointWebAPIError("project/variants exist for syncpoint")

            self.db._delete_logs(
                tablename='syncpoint_syncpoint',
                name=syncpoint
            )

            return 0

        
        self.db.connect().cursor.execute("""
            DELETE FROM syncpoint_release
            WHERE syncpoint_id = (
                SELECT id from syncpoint_syncpoint
                WHERE name = %s
            )
            AND project = %s
            AND variant = %s
        """, (
                syncpoint,
                project,
                variant
            )
        )

        self.db.conn.commit()

        return 0


    def release_syncpoint(self, syncpoint, project, variant, config, userid):
        ''' Used to indicate delivery of the required project/variant@configuration
        against the given syncpoint. After this command is run, the syncpoint variant is locked.
        The lock indicates a release was already performed, and others may already be using it 
        to build their releases. An update can only be performed by a handful of admins. (To update
        the release_configuration to a new release_configuration, run the same command again.)

        Error out if syncpoint or configuration doesn't exist.
        Error out if configuration is not 'REL*'
        Error out if an update is ran by a non-admin.
        '''
        if not self.icm.project_exists(project):
            raise SyncpointWebAPIError("Project {} does not exist.".format(project))
        if not self.icm.variant_exists(project, variant):
            raise SyncpointWebAPIError("variant {} does not exist in project {}.".format(variant, project))
        if not self.icm.config_exists(project, variant, config):
            raise SyncpointWebAPIError("config {} does not exist in project/variant {}/{}.".format(config, project, variant))

        releaser_id = self._extract_user_id_from_user(userid)            
        syncpoint_id = self._extract_syncpoint_id_from_syncpoint(syncpoint)

        self.db.cursor.execute("""
            UPDATE syncpoint_release
            SET configuration = %s,
            releaser_id = %s,
            updatedDate = %s
            WHERE syncpoint_id = %s
            AND project = %s
            AND variant = %s
        """, (
                config,
                releaser_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                syncpoint_id,
                project,
                variant
            )
        )
        self.db.conn.commit()

        return 0
   
    
    def get_syncpoints(self):
        ''' returns a list of all available syncpoints.

        retval = [ [syncpoint, project], [syncpoint, project], ... ]
        '''
        return [[row[0], row[1]] for row in self.db.connect().fetchall_raw_data("""
            SELECT name, category
            FROM syncpoint_syncpoint
        """)]


    def get_syncpoint_configuration(self, syncpoint, project, variant):
        ''' returns the sole configuration for that variant found in that syncpoint.

        Return '' if no project/variant found for that syncpoint (project/variant is not added to this syncpoint).
        Return '' if no release found. (project/variant is added for this syncpoint, but no release has been done yet)
        Return 'REL*' if release found. 
        '''
        pvclist = self.get_releases_from_syncpoint(syncpoint)
        configs = [c for p,v,c in pvclist if project==p and variant==v]
        if configs:
            ### Configuration found
            return configs[0]
        else:
            return ''


    def get_releases_from_syncpoint(self, syncpoint):
        ''' returns a list of all associated project/variant@configuration with the
        given syncpoint. project/variant that hasn't been released will have their 
        configuration as ''.

        Raise exception is syncpoint not found.
        Return an empty list if no project/variant is added to the syncpoint yet.
        
        retval = [ [project, variant, config], [project, variant, config], ... ]
        '''
        syncpoint_id = self._extract_syncpoint_id_from_syncpoint(syncpoint)

        return [[row[0], row[1], row[2]] for row in self.db.connect().fetchall_raw_data("""
            SELECT r.project, r.variant, r.configuration
            FROM syncpoint_release r
            JOIN syncpoint_syncpoint s
            ON r.syncpoint_id = s.id
            WHERE s.name = '{}'
        """.format(
                syncpoint
            )
        )]

        
    def get_syncpoint_info(self, syncpoint):
        ''' get the detail information of the registered syncpoint

        retval = [ project, creator, creationDate, description ]
        '''
        syncpoint_id = self._extract_syncpoint_id_from_syncpoint(syncpoint)

        row = self.db.connect().fetchall_raw_data("""
            SELECT s.name, e.userid, s.creationDate, s.description 
            FROM syncpoint_syncpoint s
            JOIN syncpoint_person e
            ON s.creator_id = e.id
            WHERE s.name = '{}'
        """.format(
                syncpoint
            )
        )[0]

        return [row[0], row[1], row[2].strftime("%Y-%m-%d %H:%M:%S"), row[3]] 


    def get_user_roles(self, userid):
        ''' get the list of roles this user holds.
        
        retval = ['yltan', 'kwlim']
        '''
        person_id = self._extract_user_id_from_user(userid)

        return [row[0] for row in self.db.connect().fetchall_raw_data("""
            SELECT u.role
            FROM syncpoint_user u
            WHERE person_id = '{}'
        """.format(
                person_id
            )
        )]
   
    
    def get_users_by_role(self, role):
        ''' get the list of users for a specific role

        retval = ['yltan', 'kwlim']
        '''
        self._confirm_user_role(role)
        return [row[0] for row in self.db.connect().fetchall_raw_data("""
            SELECT e.userid
            FROM syncpoint_user u
            JOIN syncpoint_person e
            ON u.person_id = e.id
            WHERE u.role = '{}'
        """.format(
                role
            )
        )]
   
  
    def add_user(self, userid, role):
        '''add a user to a specific role'''
        self._confirm_user_role(role)
        
        if not self.db.connect().fetchall_raw_data("""
            SELECT * from syncpoint_person
            WHERE userid = '{}'
        """.format(
                userid
            )
        ):
            self.db.connect()._add_log(
                tablename='syncpoint_person',
                userid=userid
            )

        person_id = self._extract_user_id_from_user(userid)
        
        try:
            cur = self.db.connect().cursor.execute("""
                INSERT INTO syncpoint_user
                set person_id = '{}',
                role = '{}'
            """.format(
                    person_id,
                    role
                )
            )
            self.db.conn.commit()
        
        except mysql.connector.IntegrityError as e:
            raise SyncpointWebAPIError("Role already exists for user {}".format(userid))

        return 0


    def delete_user(self, userid, role):
        ''' delete a user from a specific role '''
        person_id = self._extract_user_id_from_user(userid)
        self._confirm_user_role(role)

        self.db.connect()._delete_logs(
            tablename='syncpoint_user',
            person_id=person_id,
            role=role
        )

        return 0
    

    def _extract_user_id_from_user(self, userid):
        user = self.db.connect().fetchall_raw_data("""
            SELECT id 
            FROM syncpoint_person
            WHERE userid = '{}' 
        """.format(
                userid
            )
        )

        if not user:
            raise SyncpointWebAPIError("Couldn't find user {}.".format(userid))

        return str(user[0][0])


    def _extract_syncpoint_id_from_syncpoint(self, syncpoint):
        s = self.db.connect().fetchall_raw_data("""
            SELECT id 
            FROM syncpoint_syncpoint
            WHERE name = '{}'
        """.format(
                syncpoint
            )
        )
        
        if s == []:
            raise SyncpointWebAPIError("Syncpoint {} not found.".format(syncpoint))

        return str(s[0][0])


    def _confirm_user_role(self, role):
        if role not in ['admin', 'user', 'fclead', 'owner', 'sslead']:
            raise SyncpointWebAPIError("{} is not a valid role.".format(role))


if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)


