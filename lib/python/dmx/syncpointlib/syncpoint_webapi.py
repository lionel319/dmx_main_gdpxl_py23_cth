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

from future import standard_library
standard_library.install_aliases()
from builtins import object
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import logging
import json
from datetime import datetime
import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))
from dmx.abnrlib.icm import ICManageCLI


class SyncpointWebAPIError(Exception):
    pass

class SyncpointWebAPI(object):
   
    def __init__(self, web_server='sw-web.altera.com', base_url='syncpoint'):
        self.base_url = base_url
        self.web_server = web_server
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialize SyncpointWebAPI instaince for {} ...".format(self.base_url))
        self.icm = ICManageCLI()

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
        request = 'create_syncpoint'
        post_data = {
            'name': syncpoint,
            'category': category,
            'userid': userid,
            'description': description
        }
        ret = self.get_json_for(request, post_data=post_data)
        if ret and ret['status'] == 0 and ret['msg']:
            return 0
        else:
            raise SyncpointWebAPIError(ret['msg'])
        

    def add_syncpoint(self, syncpoint, project, variant, userid):
        ''' Associate the given project/variant with the given syncpoint.
        The specified variant is expected to register a release of that variant 
        against this syncpoint. 
        The project/variant here is an ICM project/variant name.
        
        Error out if either the syncpoint of the project/variant doesn't exist.
        Error out if either the project/variant is not a valid ICM data.
        '''
        request = 'add_syncpoint'
        post_data = {
            'name': syncpoint,
            'project': project,
            'variant': variant,
            'userid' : userid
        }
        if not self.icm.project_exists(project):
            raise SyncpointWebAPIError("Project {} does not exist.".format(project))
        if not self.icm.variant_exists(project, variant):
            raise SyncpointWebAPIError("variant {} does not exist in project {}.".format(variant, project))

        ret = self.get_json_for(request, post_data=post_data)
        if ret and ret['status'] == 0 and ret['msg']:
            return 0
        else:
            raise SyncpointWebAPIError(ret['msg'])


    def delete_syncpoint(self, syncpoint, project='', variant=''):
        ''' Delete the association between the given project/variant and the given
        syncpoint, or to delete the entire syncpoint altogether if project/variant is not provided.

        Error out if trying to delete a syncpoint which has associated project/variants
        (safety feature -- you must delete all the project/variants then only can you delete the
        syncpoint) 
        '''
        request = 'delete_syncpoint'
        post_data = {
            'name': syncpoint,
            'project': project,
            'variant': variant,
        }
        '''
        ### We do not check for the existance of project/variant from ICM because there might be an
        ### instance where the project/variant is already deleted from ICM, and now we want to delete
        ### the syncpoint_release model from the database, but it couldn't, due to this validation.
        if not self.icm.project_exists(project):
            raise SyncpointWebAPIError("Project {} does not exist.".format(project))
        if not self.icm.variant_exists(project, variant):
            raise SyncpointWebAPIError("variant {} does not exist in project {}.".format(variant, project))
        '''
        ret = self.get_json_for(request, post_data=post_data)
        if ret and ret['status'] == 0 and ret['msg']:
            return 0
        else:
            raise SyncpointWebAPIError(ret['msg'])


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
        request = 'add_release_to_syncpoint'
        post_data = {
            'name': syncpoint,
            'project': project,
            'variant': variant,
            'config': config,
            'userid': userid
        }
        if not self.icm.project_exists(project):
            raise SyncpointWebAPIError("Project {} does not exist.".format(project))
        if not self.icm.variant_exists(project, variant):
            raise SyncpointWebAPIError("variant {} does not exist in project {}.".format(variant, project))
        if not self.icm.config_exists(project, variant, config):
            raise SyncpointWebAPIError("config {} does not exist in project/variant {}/{}.".format(config, project, variant))

        ret = self.get_json_for(request, post_data=post_data)
        if ret and ret['status'] == 0 and ret['msg']:
            return 0
        else:
            raise SyncpointWebAPIError(ret['msg'])
    
    def get_syncpoints(self):
        ''' returns a list of all available syncpoints.

        retval = [ [syncpoint, project], [syncpoint, project], ... ]
        '''
        request = 'get_syncpoints'
        ret = self.get_json_for(request)
        if ret and ret['status'] == 0 and ret['msg']:
            return ret['msg']
        else:
            raise SyncpointWebAPIError(ret['msg'])


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
        request = 'get_releases_from_syncpoint'
        post_data = {'name': syncpoint}
        ret = self.get_json_for(request, post_data=post_data)
        if ret and ret['status'] == 0 and 'msg' in ret:
            return ret['msg']
        elif ret and 'msg' in ret:
            raise SyncpointWebAPIError(ret['msg'])
        else:
            raise SyncpointWebAPIError("Received incomplete data when calling get_releases_from_syncpoint({})".format(syncpoint))


    def get_syncpoint_info(self, syncpoint):
        ''' get the detail information of the registered syncpoint

        retval = [ project, creator, creationDate, description ]
        '''
        request = 'get_syncpoint_info'
        post_data = {'name': syncpoint}
        ret = self.get_json_for(request, post_data=post_data)

        if ret and ret['status'] == 0:
            info = ret['msg']
            return [ info['category'], info['creator'], info['creationDate'], info['description'] ]
        else:
            raise SyncpointWebAPIError(ret['msg'])


    def get_user_roles(self, userid):
        ''' get the list of roles this user holds.
        
        retval = ['yltan', 'kwlim']
        '''
        request = 'user/get_user_roles'
        post_data = {'userid': userid}
        ret = self.get_json_for(request, post_data)
        if ret and ret['status']==0:
            return ret['msg']
        else:
            raise SyncpointWebAPIError(ret['msg'])
    
    def get_users_by_role(self, role):
        ''' get the list of users for a specific role

        retval = ['yltan', 'kwlim']
        '''
        request = 'user/get_users_by_role'
        post_data = {'role': role}
        ret = self.get_json_for(request, post_data)
        if ret and ret['status']==0:
            return ret['msg']
        else:
            raise SyncpointWebAPIError(ret['msg'])
    
    def add_user(self, userid, role):
        ''' add a user to a specific role '''
        request = 'user/add'
        post_data = {'userid': userid, 'role': role}
        ret = self.get_json_for(request, post_data)
        if ret and ret['status']==0:
            return 0
        else:
            raise SyncpointWebAPIError(ret['msg'])
    
    def delete_user(self, userid, role):
        ''' delete a user from a specific role '''
        request = 'user/delete'
        post_data = {'userid': userid, 'role': role}
        ret = self.get_json_for(request, post_data)
        if ret and ret['status']==0:
            return 0
        else:
            raise SyncpointWebAPIError(ret['msg'])
    

    def get_json_for(self, request, post_data=None):
        """
        Makes an HTTP request to the url in request.
        If post_data is provided, it is passed as well.
        Assumes the results are JSON and returns the
        JSON object.
        """
        url_encoded_request = urllib.parse.quote(request)
        url = self.get_url_for(url_encoded_request)
        self.logger.debug('Fetch: %s' % url)
        full_request = None
        if post_data:
            post = urllib.parse.urlencode(post_data).encode()
            self.logger.debug('POST data: %s' % post)
            full_request = urllib.request.Request(url, post)
        else:
            full_request = url

        try:
            response = urllib.request.urlopen(full_request)
            text = response.read()
            self.logger.debug('JSON response: %s' % text)
            js = json.loads(text)
            return js
        except Exception as e:
            if self.TRIED < self.RETRY_COUNT:
                self.TRIED += 1
                self.logger.debug(e)
                self.logger.info("Tried {} times, {} more times for retry...".format(self.TRIED, self.RETRY_COUNT-self.TRIED))
                time.sleep(self.DELAY_SECONDS_BETWEEN_RETRY)
                return self.get_json_for(request, post_data=post_data)
            else:
                raise

        return xml

    def get_url_for(self, request):
        return 'http://{}/{}/{}'.format(self.web_server, self.base_url, request)


if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)


