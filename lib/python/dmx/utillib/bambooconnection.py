#!/usr/bin/env python
import os, sys
import urllib
import urllib2
import types
import xml.dom.minidom
from base64 import b64encode

from xml.dom.minidom import parseString, Node
from altera.rest_base import *
from altera import Error

class ConnectionError(Exception): pass

class BambooConnection(RESTConnection):
    """
    Uses HTTP to provide an API to interact with Fogbugz server.
    """
    BAMBOO_PROD_SERVER = 'http://dashboardtnr.sc.intel.com:8085'
    
    def __init__(self, base_url, username, password):
        if base_url is None:
            base_url = self.BAMBOO_PROD_SERVER
        self.base_url = base_url            
        super(BambooConnection, self).__init__(base_url=base_url)
        self.resource = 'rest/api/latest'
        self.commands = {
            'build' : 'queue',
            'result' : 'result',

        }
        self.headers = {"Content-type": "application/xml",
                        "Authorization": "Basic "+ b64encode('{}:{}'.format(username,password))
                        }
                                 
    def _resp_is_200(self, resp):
        """
        check http response
        """
        if resp.status == 200:
            return True
        else:
            raise ConnectionError('Bamboo Connection Error', resp.status, self.base_url)

    def _is_good_content(self, resp, content):
        """
        check both http response and fogbugz's response
        """
        ret = False
        if self._resp_is_200(resp):
            ret = True            
        return ret            
              
    def build_plan(self, plan):
        resource = '{}/{}/{}?os_authType=basic'.format(self.resource, self.commands['build'], plan)
        resp, content = self.request_post(resource, None)
        self._is_good_content(resp, content)
        doc = parseString(content)
        plan = doc.childNodes[0]._attrs['buildResultKey'].nodeValue
        return plan

    def is_plan_finished(self, plan):
        resource = '{}/{}/{}'.format(self.resource, self.commands['result'], plan)
        resp, content = self.request_get(resource)
        self._is_good_content(resp, content)
        doc = parseString(content)
        if doc.childNodes[0]._attrs['finished'].nodeValue == 'true':
            status = True
        else:
            status = False            
        return status
                
    def is_plan_successful(self, plan):
        resource = '{}/{}/{}'.format(self.resource, self.commands['result'], plan)
        resp, content = self.request_get(resource)
        self._is_good_content(resp, content)
        doc = parseString(content)
        if doc.childNodes[0]._attrs['successful'].nodeValue == 'true':
            result = True
        else:
            result = False            
        return result              

    def get_plan_url(self, plan):
        # http://dashboardtnr.sc.intel.com:8085/browse/DMX-CIS-257
        url = '{}/browse/{}'.format(self.base_url, plan)
        return url

