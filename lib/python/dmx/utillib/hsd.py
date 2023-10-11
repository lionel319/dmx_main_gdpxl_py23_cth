'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/hsd.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to return list of DMX superusers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import re
import logging
import pprint
import sys
import datetime
import json
import requests_kerberos
# requests import must come after requests_kerberos for some reasons
import requests
HSD_PROD = 'https://hsdes-api.intel.com/ws/ESService'
HSD_PRE = 'https://hsdes-api-pre.intel.com/ws/ESService'
CA_CERT = '/etc/ssl/certs/ca-certificates.crt'
HEADERS = {"Content-type":"application/json"}

class HSDError(Exception): pass

class HSD(object):
    def __init__(self, testserver=False, preview=False):
        self.preview = preview
        self.headers = HEADERS
        self.ca_cert = CA_CERT
        self.server = HSD_PROD if not testserver else HSD_PRE

    def insert_record(self, tenant, subject, fields):
        command = 'insert_record'
        cmd_args = {
                "tenant": tenant,
                "subject": subject,
                }
        var_args = []
        for field in fields:
            var_args.append({field: fields[field]})
        results = self.post(command, cmd_args, var_args=var_args)
        return results['responses'][0]['result_params']['newId']

    def update_record(self, tenant, subject, id, fields):
        command = 'update_record'
        cmd_args = {
                "tenant": tenant,
                "subject": subject,
                "id": id
                }
        var_args = []
        for field in fields:
            var_args.append({field: fields[field]})
        results = self.post(command, cmd_args, var_args=var_args)
        return results['responses'][0]['result_params']['updated_id']

    def get_records(self, tenant, subject):
        command = 'get_records'
        cmd_args = {
                "tenant": tenant,
                "subject": subject,
                }
        results = self.post(command, cmd_args)
        dict = {}
        for result in results['responses'][0]['result_table']:
            dict[result['id']] = result
        return dict            

    def get_record_by_id(self, id):
        command = 'get_record_by_id'
        cmd_args = {
                "id": id,
                }
        results = self.post(command, cmd_args)
        return results['responses'][0]['result_table'][0]

    # args is a dictionary
    '''
        { 
     "requests": [  
      { 
       "tran_id": "1234", 
      "command": "get_records", 
       "command_args": {  "subject": "issue",
                          "tenant": "hsd-es"  
                   }, 
       "var_args" : []  
     } 
    ]  
    }
    '''
    def _generate_payload(self, command, cmd_args, var_args=[]):
        payload = {
                    "requests": [
                        { 
                           "tran_id": "1", 
                           "command": command, 
                           "command_args": cmd_args, 
                    "var_args" : var_args 
                        } 
                    ]  
                  }

        return payload
            
    def post(self, command, cmd_args, var_args=[]):
        payload = self._generate_payload(command, cmd_args, var_args=var_args)

        r = requests.post(
                url=self.server,
                headers=self.headers,
                auth=requests_kerberos.HTTPKerberosAuth(mutual_authentication=requests_kerberos.OPTIONAL),
                verify=self.ca_cert,
                json=payload
                )

        if r.status_code != 200:
            raise HSDError('Failed to retrieve data from HSD-ES: {}'.format(r.text))

        results = json.loads(r.text)
        if results['responses'][0]['status'] != 'success':
            raise HSDError('HSD post request failed: {}'.format(results))

        return results


            
