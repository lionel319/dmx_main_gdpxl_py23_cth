#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/splunk.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Splunk interface for abnr logging 

Author: Lee Cartwright

Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import getpass
import socket
import os
import time
import datetime
import sys
import logging
import traceback
# Do this so we can properly catch connection issues
from socket import error as socket_error

from dmx.utillib.utils import *
from dmx.utillib.version import Version
from altera_splunk import SplunkTCP

DEV_SERVER = 'dashboard-dev'
DEV_PORT = 1236

class Splunk(object):
    '''
    Class to manage logging abnr data to Splunk
    '''
    def __init__(self, subcommand, abnr_id=None, server='dashboard.altera.com', port='1236'):
        '''
        Initialiser
        '''
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.pid = os.getpid()
        self.subcommand = subcommand
        self.command_line = " ".join(sys.argv[:])
        self.arc_job = os.getenv('ARC_JOB_ID', 0)
        self.start_time = time.time()
        self.server = server
        self.port = port
        self.logger = logging.getLogger(__name__)

        # Create the basic attributes applicable to all abnr logs
        if not abnr_id:
            self.abnr_id = get_abnr_id()
        else:
            self.abnr_id = abnr_id

        version = Version()
        self.attributes = {
            'abnr_index' : self.abnr_id,
            'host' : self.host,
            'pid' : self.pid,
            'start_time' : self.start_time,
            'user' : self.user,
            'dmx_version' : 'dmx/{}'.format(version.dmx),
            'dmxdata_version': 'dmxdata/{}'.format(version.dmxdata),
            'subcommand' : self.subcommand,
            'command_line' : self.command_line,
            'p4server' : os.getenv('P4PORT', ''),
            'arc_job_id' : self.arc_job,
        }

    def add_attribute(self, key, value):
        '''
        Add or update a key:value that will be logged to splunk.

        :param key: The key to use when logging to splunk
        :type key: str
        :param value: The value to associate with the key
        :type value: str
        '''
        self.attributes[key] = value

    def add_attributes(self, attributes):
        '''
        Adds a group of key:value pairs to the attributes that will be logged
        to splunk.

        :param attributes: Dictionary containing the data to add.
        :type attributes: dict
        '''
        self.attributes.update(attributes)
    
    def splunk_log(self, data):
        '''
        Sends data to splunk in our standard format
        data is a dict
        '''
        ret = True
        # Combine the standard attributes with data
        # We do it like this to ensure that the standard attributes win
        # if there's a key clash
        combined = dict(data.items() + self.attributes.items())
        try:
            with SplunkTCP(self.server, self.port) as stcp:
                stcp.send_line(combined)
        except socket_error as serr:
            self.logger.warn('Unable to connect to Splunk server at {0}:{1}'.format(self.server, self.port))
            self.logger.warn(str(serr))
            ret = False

        return ret

    def initial_log(self):
        '''
        Logs initial abnr startup data to Splunk
        '''
        ret = False

        ret = self.splunk_log({})
        self.logger.debug('Initial Splunk log sent')

        return ret

    def final_log(self, exitcode, exit_message=None):
        '''
        Logs final data to splunk
        If exit_message is a dict adds it to what is logged
        '''
        ret = False
        # Add the end time
        self.add_timestamp_attribute('end_time')

        message = dict()
        message['exitcode'] = exitcode
        start_date = datetime.datetime.fromtimestamp(self.start_time)
        end_date = datetime.datetime.fromtimestamp(self.attributes['end_time'])
        delta = end_date - start_date
        message['run_time'] = str(delta)
        if exit_message:
            message = dict(message.items() + exit_message.items())
        ret = self.splunk_log(message)
        self.logger.debug('Final Splunk log sent')

        return ret

    def exception_log(self):
        '''
        Logs an exception as the final part of a script
        '''
        ret = False

        # Get the exception information
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = dict()
        message['exception_type'] = str(exc_type)
        message['message'] = str(exc_value)
        message['traceback'] = traceback.format_exc()
        ret = self.final_log(1, exit_message=message)
        self.logger.debug('Exception Splunk log sent')

        return ret

    def add_timestamp_attribute(self, attribute_name):
        '''
        Adds an attribute with name attribute_name to the list of attributes we'll log.
        The value is the time since epoch.

        :param attribute_name: The Splunk attribute name or key in the key:value pair
        :type attribute_name: str
        '''
        self.add_attribute(attribute_name, time.time())
