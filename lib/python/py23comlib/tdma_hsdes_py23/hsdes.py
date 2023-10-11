"""
Filename:      $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/tdma_hsdes_py23/hsdes.py#1 $

PSG specific interface to HSD-ES server using HSD-ES REST API

The HSD ES API file is the core to access HSD ES REST API
It is modified version for Linux Python 2 based on the original Windows Python 3 version https://wiki.ith.intel.com/display/HSDESWIKI/HSD-ES+API 
from HSD ES team The file will be called by hsdes.py to achieve specific business needs. The HSD ES REST API is https://hsdes.intel.com/rest/doc

The module is using requests_kerberos module to get HSDES authentication. The module has some dependent modules. They are all installed in
the /python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages. If you got the issue of missing modules, please installed it 
or to add the path to your own resource. There are workarounds to add path per different resources. These workarounds are in the top and 
the bottom of the file, they will be removed when our PSG python resources are cleanned.

This is based off of PSWE's REST API that was written by Jim Zhao (jim.x.zhao@intel.com) and updated to support PHE (support subject) in TDMA. All credits go to Jim Zhao
Original source depot: //depot/devenv/python_modules/main/altera/hsdes          
"""

from builtins import str
from builtins import object
__author__ = "Jim Zhao (jim.x.zhao@intel.com)"
__copyright__ = "Copyright 2018 Intel Corporation."


import os
import platform
import sys
from altera.farm import FARM_TOOLS_ROOT

### SPECIAL CHANGE TO REMOVE LIBRARY OVERLAP FROM WITHIN PROJECT BUNDLE
### The other alternative is to change interpreter and use -E to bypass using PYTHONPATH
ARC_RESOURCE_PATHS = []
for resource_path in [pythonpath for pythonpath in sys.path if 'icd_cad_pylib' in pythonpath]: 
    sys.path.remove(resource_path)
    ARC_RESOURCE_PATHS.append(resource_path)


if not 'SUSE' in platform.linux_distribution()[0]:
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/httplib2-0.7.4-py2.7.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/requests-2.18.4-py2.7.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/certifi-2017.07.27.1-py2.7.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/cffi-1.11.5-py2.7-linux-x86_64.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/cryptography-2.2.2-py2.7-linux-x86_64.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/ipaddress-1.0.22-py2.7.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/asn1crypto-0.24.0-py2.7.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/requests_kerberos-0.12.0-py2.7.egg')
    sys.path.append('/p/psg/ctools/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/pykerberos-1.2.1-py2.7-linux-x86_64.egg')
    
    #print sys.path
#=================================  workaround start =====================================================================
'''
SITE_PACKAGES_PATH = FARM_TOOLS_ROOT + "/python/altera-packages/2.7.3/1.0/linux64/lib/python2.7/site-packages/"
CORRECT_REQUESTS_PATH = SITE_PACKAGES_PATH + "requests-2.18.4-py2.7.egg"
ALL_MODULES_NEEDED = "requests-2.18.4-py2.7.egg,urllib3-1.22-py2.7.egg,chardet-3.0.4-py2.7.egg,requests_kerberos-0.12.0-py2.7.egg,six-1.11.0-py2.7.egg,cffi-1.11.5-py2.7-linux-x86_64.egg,cryptography-2.2.2-py2.7-linux-x86_64.egg,idna-2.6-py2.7.egg,ipaddress-1.0.22-py2.7.egg,pykerberos-1.2.1-py2.7-linux-x86_64.egg,certifi-2017.07.27.1-py2.7.egg,asn1crypto-0.24.0-py2.7.egg"
NEW_MODULES_NEEDED = "requests-2.18.4-py2.7.egg,urllib3-1.22-py2.7.egg,chardet-3.0.4-py2.7.egg"
DJANGO_REQUESTS_FOUND_FIRST = False
DJANGO_REQUESTS_FOUND_LATER = False
CORRECT_REQUESTS_FOUND_FIRST = False
CORRECT_REQUESTS_FOUND_LATER = False
REQUESTS_FOUND = False
REQUESTS_KERBEROS_FOUND = False

for path in sys.path:    
    if path.find("requests_kerberos-") > -1 and REQUESTS_KERBEROS_FOUND == False:
        REQUESTS_KERBEROS_FOUND = True

    if path.find("requests-") > -1 and REQUESTS_FOUND == False:
        REQUESTS_FOUND = True

    if path == CORRECT_REQUESTS_PATH : 
        if DJANGO_REQUESTS_FOUND_FIRST == False:
            CORRECT_REQUESTS_FOUND_FIRST = True
        else:
            CORRECT_REQUESTS_FOUND_LATER = True        

    if path.find("django") > -1 and path.find("requests-") > -1 :
        if CORRECT_REQUESTS_FOUND_FIRST == False:
            DJANGO_REQUESTS_FOUND_FIRST = True
        else:
            DJANGO_REQUESTS_FOUND_LATER = True
            
if DJANGO_REQUESTS_FOUND_FIRST == True and CORRECT_REQUESTS_FOUND_LATER == True and REQUESTS_KERBEROS_FOUND == True: 
    for name in NEW_MODULES_NEEDED.split(','):
        sys.path.insert(0, SITE_PACKAGES_PATH+name)

if REQUESTS_FOUND == False and REQUESTS_KERBEROS_FOUND == False: 
    sys.path.append(SITE_PACKAGES_PATH)
    for name in ALL_MODULES_NEEDED.split(','):
        sys.path.append(SITE_PACKAGES_PATH+name)
'''
#================================= workaround end =====================================================================

import os
import json
import weakref
import requests
from requests_kerberos import HTTPKerberosAuth
import urllib3
from altera import Error
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.poolmanager import PoolManager
import ssl

# this is to ignore the ssl insecure warning as we are passing in 'verify=false'
urllib3.disable_warnings()

#===============================================================================================================
class HsdEsError(Error):
    """
    Exception raised when receiving error code in Hsdes's response.
    """
    #---------------------------------------------------------------------------------------
    def __init__(self, message, code, url='unknown'):
        super(HsdEsError, self).__init__(message, logger=None)
        self.code = code #HTTP status code
        self.url = url
        
    #---------------------------------------------------------------------------------------
    def __str__(self):
        err = super(HsdEsError, self).__str__()
        if self.code:
            err += "; Error Code: %s" % self.code
        if self.url:
            err += "; URL: %s" % self.url
        return err 

#===============================================================================================================
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)
                                       
#===============================================================================================================
class EsApi(object):

    #---------------------------------------------------------------------------------------
    def __init__(self, env, username, password): 
        if env in ('PREPRODUCTION', 'PRODUCTION'):
            self.env = env
        else:
            err = 'Env must be "PRODUCTION" or "PREPRODUCTION"'
            raise TypeError(err)
        
        self.username = username
        self.password = password
        self.authkb = HTTPKerberosAuth() 
        self.authbs = HTTPBasicAuth(username, password)
        self.klist_cmd = "/usr/bin/klist -s"
        self.kinit_cmd = "/usr/intel/bin/kinit"

                
        if self.env == 'PRODUCTION':
            self.base_url = 'https://hsdes-api.intel.com/rest/'
        else:
            self.base_url = 'https://hsdes-api-pre.intel.com/rest/'

    #---------------------------------------------------------------------------------------
    def Query(self):
        return Query(self)

    #---------------------------------------------------------------------------------------
    def Article(self):
        return Article(self)
    
    #---------------------------------------------------------------------------------------
    def Lookup(self):
        return Lookup(self)

    #---------------------------------------------------------------------------------------
    def send_request(self, method, args, data, func = ''):

        if self.username:
            authMethod = self.authbs
        else:
            authMethod = self.authkb
        url = self.base_url + args

        app = 'Python API 0.2 ' + func
        headers = {'Content-type': 'application/json', 'APP': app}
        
        try:
            s = requests.Session()            
            s.mount('https://', SSLAdapter())    
            isKinitRan = False
            httpStatusCode = 0

            while not httpStatusCode:
                if method == 'post':
                    response = s.post(url=url, verify=False, auth=authMethod, headers=headers, json=data)
                elif method == 'upload_post':
                    response = s.post(url=url, verify=False, auth=authMethod, data=data['data_dict'], files=data['file_dict'])
                elif method == 'get':
                    response = s.get(url=url, verify=False, auth=authMethod, headers=headers)
                elif method == 'put':
                    response = s.put(url=url, verify=False, auth=authMethod, headers=headers, json=data)
                else:
                    raise Exception('Invalid/unsupported rest method')
                
                httpStatusCode = response.status_code           
                
                if httpStatusCode == 200:
                    return response.json()
                else: 
                    if not isKinitRan and httpStatusCode == 401:
                        os.system(self.kinit_cmd)
                        isKinitRan = True
                        httpStatusCode = 0
                    else:
                        raise HsdEsError(response.text, response.status_code,url)
                
        except HsdEsError:
            raise             
        except requests.exceptions.HTTPError as errh:
            raise HsdEsError('Http Error Message=%s' % (errh), "990", url )
        except requests.exceptions.ConnectionError as errc:
            raise HsdEsError('Error Connecting Message= %s' % ( errc), "991", url )
        except requests.exceptions.Timeout as errt:
            raise HsdEsError('Timeout Error Message= %s' % (errt), "992", url )
        except requests.exceptions.RequestException as err:
            raise HsdEsError('RequestException Error Message= %s' % (err), "993", url )     
        except Exception as exc:
            raise HsdEsError('Exception Error Message= %s' % (exc), "994", url )   
       
    def send_request_raw(self, method, args, data, func = '', file=None, data_is_json=True):
        url = self.base_url + args
        app = 'Python API 0.2 ' + func
        headers = {'Content-type': 'application/json', 'APP': app}
        json_data = data

        # determines whether "json" or "data" will be used for input data
        if data_is_json != True:
            json_data = None
            headers = None
        else:
            data = None
       
        try:
            exec_times = 0
            s = requests.Session()            
            s.mount('https://', SSLAdapter())    
            isKinitRan = False
            httpStatusCode = 0
            MAX_TRIES = 2
            while exec_times < MAX_TRIES:
                exec_times += 1
                if method == 'post':
                    response = s.post(url=url, verify=False, auth=self.authkb, headers=headers, json=json_data, data=data, files = file)
                elif method == 'get':
                    response = s.get(url=url, verify=False, auth=self.authkb, headers=headers)
                elif method == 'put':
                    response = s.put(url=url, verify=False, auth=self.authkb, headers=headers, json=json_data)
                else:
                    raise Exception('Invalid/unsupported rest method')

                httpStatusCode = response.status_code

                if httpStatusCode == 200:
                    return response
                else:
                    if not isKinitRan and httpStatusCode == 401:
                        # On PICE ARC Machines, the 'kinit' tool is not part of the OS. So we need
                        # to explicitly use the copy from /usr/intel/bin
                        if FARM_JOB_ID and farm_is_pice():
                            use_intel_kinit = True
                        elif os.environ.get('HSDES_USE_INTEL_KINIT'):
                            # Override used by p4sip tests which need to unset ARC_JOB_ID from env
                            use_intel_kinit = True
                        else:
                            use_intel_kinit = False
                        
                        if use_intel_kinit:
                            import pexpect
                            cmd = "/usr/intel/bin/kinit {0}".format(self.principal)
                            expected = "Password for {0}".format(self.principal)
                            pass_input = self.password+"\n"
                            child = pexpect.spawn(cmd)
                            child.expect(expected)
                            child.sendline(pass_input)
                            child.wait()
                        else:
                            os.system(self.cmd)
                        isKinitRan = True
                        httpStatusCode = 0
                    else:
                        if exec_times >= MAX_TRIES:
                            raise HsdEsError(response.text, response.status_code,url)
                
        except HsdEsError:
            raise             
        except requests.exceptions.HTTPError as errh:
            raise HsdEsError('Http Error Message=%s' % (errh), "990", url )
        except requests.exceptions.ConnectionError as errc:
            raise HsdEsError('Error Connecting Message= %s' % ( errc), "991", url )
        except requests.exceptions.Timeout as errt:
            raise HsdEsError('Timeout Error Message= %s' % (errt), "992", url )
        except requests.exceptions.RequestException as err:
            raise HsdEsError('RequestException Error Message= %s' % (err), "993", url )     
        except Exception as exc:
            raise HsdEsError('Exception Error Message= %s' % (exc), "994", url )
       
#===============================================================================================================
class Query(object):

    #---------------------------------------------------------------------------------------
    def __init__(self, esapi):
        if not isinstance(esapi, EsApi):
            err = '''Query object must be initiated from an EsApi object.
            e.g.
            esapi = EsApi('PREPRODUCTION')
            qry = Query(esapi)'''

            raise TypeError(err)

        self.eql = None
        self.esapi = weakref.ref(esapi)

    #---------------------------------------------------------------------------------------
    def get_records(self, eql=None, start_at=0, count=100000):
        if eql:
            self.eql = eql
        try:
            if not self.eql:
                raise Exception('get_records: EQL is a required parameter. Either pass it in or set the eql property')

            arg = 'query/execution/eql?start_at=%i&max_results=%i' % (start_at, count)
            data = {'eql': self.parse_eql()}
            responseText = self.esapi().send_request('post', arg, data, 'Query->get_records')            
            r = responseText['data']
            return r

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    def parse_eql(self):
        self.eql = self.eql.replace('\n', ' ')
        
        if not self.eql:
            self.eql = "select id, title "

        if "where" not in self.eql:
            self.eql += " where id > 0"

        return self.eql

    #---------------------------------------------------------------------------------------
    def get_query(self, query_id=None, start_at=0, count=1000000):
        if query_id:
            self.query_id = query_id
        try:
            if not self.query_id:
                raise Exception('get_query: query_id is a required parameter.')

            arg = 'query/execution/%s?include_text_fields=Y&start_at=%i&max_results=%i' % (query_id,start_at, count)
            data = dict()
            responseText = self.esapi().send_request('post', arg, data, 'Query->get_query')            
            r = responseText['data']
            return r

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    def __get_fields(self, s):
        # get everything between the words 'select' and 'where'
        match = re.match(r'select(.+)where', s).groups()[0]
        # match is a string like 'id, title,...'

        # split the matched string on comma
        lst = match.split(',')

        # strip out spaces and return the result
        return [v.strip() for v in lst]


#===============================================================================================================
class Article(object):
    reserved_cols = ['updated_fields', 'esapi', 'data', 'id', 'subject', 'tenant']

    def __init__(self, esapi):
        self.updated_fields = []

        if not isinstance(esapi, EsApi):
            err = '''Article object must be initiated from an EsApi object.
            e.g.
            esapi = EsApi('PREPRODUCTION')
            qry = Article(esapi)'''

            raise TypeError(err)

        self.esapi = weakref.ref(esapi)

        self.id = None
        self.tenant = None
        self.subject = None

    #---------------------------------------------------------------------------------------
    def set(self, field_name, field_value):
        self.updated_fields.append({field_name: field_value})

    #---------------------------------------------------------------------------------------
    def get(self, field_name):
        return self.data[field_name]

    #---------------------------------------------------------------------------------------
    def load(self, id):
        arg = 'article/' + str(id)
        try:
            responseText = self.esapi().send_request('get', arg, 'Article->load')
                        
            self.data = responseText['data'][0]
            self.id = id
            self.tenant = self.data['tenant'] # r.tenant
            self.subject = self.data['subject'] #r.subject
            return True

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    def get_data(self, id, cols):
        #https://hsdes-pre.intel.com/rest/article/1305567483?fields=id%2Ctitle%2Ctenant
        arg = 'article/' + str(id)

        if cols is not None:     
            if type(cols) is str:
                cols = cols.split(',')

            if type(cols) is list:
                arg += '?fields='
                for col in cols:
                    arg += col+ '%2C'
        if 'tenant' not in cols:
            arg +='tenant'
        if 'subject' not in cols:
            arg +='%2Csubject'
        try:
            responseText = self.esapi().send_request('get', arg, 'Article->load')
            if responseText is not None:
                self.data = responseText['data'][0]
                self.id = id
                self.tenant = self.data['tenant'] # r.tenant
                self.subject = self.data['subject'] #r.subject
                return self.data
            else:
                return responseText

        except Exception as exc:
            raise exc
        
    #---------------------------------------------------------------------------------------
    def update(self):
        method = 'put'
        args = 'article/' + str(self.id)
        data = { "subject": self.subject , "tenant": self.tenant, "fieldValues": self.updated_fields}

        try:
            responseText = self.esapi().send_request(method, args, data, 'Article->update')

            return responseText

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    def upload(self, upload_file, title, file_name):
        method = 'upload_post'
        args = 'binary/upload/{}?verbose=true'.format(str(self.id))
        data = { 'file_dict':   { "file": open(upload_file, 'rb') },
                 'data_dict':   { "title": title, "file_name": file_name, "parent_id": str(self.id)}}

        try:
            responseText = self.esapi().send_request(method, args, data, 'Article->upload')

            return responseText

        except Exception as exc:
            raise exc            

    #---------------------------------------------------------------------------------------
    def newArticle(self, tenant, subject):
        newRec = Article(self.esapi())
        newRec.tenant = tenant
        newRec.subject = subject
        newRec.updated_fields = []

        return newRec

    #---------------------------------------------------------------------------------------
    def insert(self, newArticle):
        method = 'post'
        args = 'article?fetch=false' 
        data = { "subject": newArticle.subject , "tenant": newArticle.tenant, "fieldValues": newArticle.updated_fields}

        try:
            responseText = self.esapi().send_request(method,args,data, 'Article->insert')
                        
            if responseText is not None:
                return responseText['new_id']
            else:
                return responseText

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    def insert_comment(self, comment):
        method = 'post'
        args = 'article?fetch=false' 
        data = { "subject": "comments" , "tenant": self.tenant, "fieldValues": [{'parent_id': self.id},{'description': comment}]}

        try:
            responseText = self.esapi().send_request(method, args, data, 'Artilce->insert_comment')
            return responseText

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    # get_comments returns a list
    #---------------------------------------------------------------------------------------
    def get_comments(self):
        method = 'get'        
        args = 'article/%s/children?tenant=%s&child_subject=comment&fields=%s' % (self.id, self.tenant, "id%2Crev%2Csubmitted_date%2Cowner%2Cdescription%2Cupdated_by%2Cupdated_date")  
        #https://hsdes-pre.intel.com/rest/article/1305567483/children?tenant=fpga_sw&child_subject=comment&fields=id%2Crev%2Csubmitted_date%2Cowner%2Cdescription%2Cupdated_by%2Cupdated_date
        
        try:
            responseText = self.esapi().send_request(method, args,'Article->get_comments')

            r = responseText['data']
            return r

        except Exception as exc:
            raise exc
        
    #---------------------------------------------------------------------------------------
    # get_history returns a list
    #---------------------------------------------------------------------------------------
    def get_history(self, cols):
        method = 'get'        
        args = 'article/%s/history?fields=%s' % (self.id, cols)  
        #https://hsdes-pre.intel.com/rest/article/1306467274/history?fields=id%2Ctitle%2Cowner%2Cupdated_date
        try:
            responseText = self.esapi().send_request(method, args,'Article->get_history')

            r = responseText['data']
            return r

        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    # get_attachments_metadata returns a JSON list of attachment metadata
    #---------------------------------------------------------------------------------------
    def get_attachments_metadata(self):
        method = 'get'
        args = 'article/%s/children?tenant=%s&child_subject=%s' % (self.id, self.tenant, "attachment")
        #https://hsdes-api.intel.com/rest/article/22010577459/children?tenant=fpga_sw&child_subject=attachment

        try:
            responseText = self.esapi().send_request(method, args, 'Article->get_attachments_metadata')

            r = responseText['data']
            return r

        except Exception as exc:
            raise exc

   #---------------------------------------------------------------------------------------
    # download_attachment returns the raw binary content of the attached file
    #---------------------------------------------------------------------------------------
    def download_attachment(self, attachment_id):
        method = 'get'
        args = 'binary/%s' % (attachment_id)
        #https://hsdes-api.intel.com/rest/binary/22010577873

        try:
            response = self.esapi().send_request_raw(method, args, 'Article->get_attachment')

            r = response.content
            return r

        except Exception as exc:
            raise exc

#===============================================================================================================
class Lookup(object):

    #---------------------------------------------------------------------------------------
    def __init__(self, esapi):
        if not isinstance(esapi, EsApi):
            err = '''Lookup object must be initiated from an EsApi object.
            e.g.
            esapi = EsApi('PREPRODUCTION')
            lookup = Lookup(esapi)'''

            raise TypeError(err)

        self.eql = None
        self.esapi = weakref.ref(esapi)

    #---------------------------------------------------------------------------------------
    def get_lookup_data(self, field, count=10000 ):                
        try:
            if not field:
                raise Exception('get_lookup_data: field is a required parameter. Either pass it in or set the field property')
            #https://hsdes-pre.intel.com/rest/lookup/bug.exposure
            arg = 'lookup/%s?start_at=1&max_results=%i' % (field, count)
            data = {}

            responseText = self.esapi().send_request('post', arg, data, 'Lookup->get_lookup_data')
            
            r = responseText['data']
            return r

        except Exception as exc:
            raise exc
        
#=================================  workaround start =====================================================================
'''
if DJANGO_REQUESTS_FOUND_FIRST == True and CORRECT_REQUESTS_FOUND_LATER == True and REQUESTS_KERBEROS_FOUND == True: 
    for name in NEW_MODULES_NEEDED.split(','):
        sys.path.remove(SITE_PACKAGES_PATH+name)

if REQUESTS_FOUND == False and REQUESTS_KERBEROS_FOUND == False: 
    sys.path.remove(SITE_PACKAGES_PATH)
    for name in ALL_MODULES_NEEDED.split(','):
        sys.path.remove(SITE_PACKAGES_PATH+name)
'''
for res in ARC_RESOURCE_PATHS:
    sys.path.append(res)
#================================= workaround end =====================================================================
