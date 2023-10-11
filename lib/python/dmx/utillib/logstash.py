#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/logstash.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: LogStash interface for abnr logging 

Author: Lee Cartwright

Copyright (c) Altera Corporation 2014
All rights reserved.
'''

from builtins import str
from builtins import object
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
import json
from socket import create_connection
DEV_SERVER = 'sjdacron01.sc.intel.com'
DEV_PORT = '6789'
PROD_SERVER = 'sjlogstash02.sc.intel.com'
PROD_PORT = '6789'

class LogStash(object):
    '''
    Class to manage logging abnr data to LogStash
    '''
    def __init__(self, subcommand, abnr_id=None, testserver=False):
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
        if testserver:
            self.server = DEV_SERVER
            self.port = DEV_PORT
        else:
            self.server = PROD_SERVER
            self.port = PROD_PORT
        self.testserver = testserver            

        self.logger = logging.getLogger(__name__)

        # Create the basic attributes applicable to all abnr logs
        if not abnr_id:
            self.abnr_id = get_abnr_id()
        else:
            self.abnr_id = abnr_id
        
        version = Version()
        self.attributes = {
            "abnr_index" : self.abnr_id,
            "host" : self.host,
            "pid" : self.pid,
            "start_time" : self.start_time,
            "user" : self.user,
            "dmx_version" : "dmx/{}".format(version.dmx),
            "dmxdata_version": "dmxdata/{}".format(version.dmxdata),
            "subcommand" : self.subcommand,
            "command_line" : self.command_line,
            "p4server" : os.getenv('P4PORT', ''),
            "arc_job_id" : self.arc_job,
            "options" : [x for x in sys.argv[:] if x.startswith('-')]
        }

    def add_attribute(self, key, value):
        '''
        Add or update a key:value that will be logged to logstash.

        :param key: The key to use when logging to logstash
        :type key: str
        :param value: The value to associate with the key
        :type value: str
        '''
        self.attributes[key] = value

    def add_attributes(self, attributes):
        '''
        Adds a group of key:value pairs to the attributes that will be logged
        to logstash.

        :param attributes: Dictionary containing the data to add.
        :type attributes: dict
        '''
        self.attributes.update(attributes)
    
    def logstash_log(self, data):
        '''
        Sends data to logstash in our standard format
        data is a dict
        '''
        ret = True
        # Combine the standard attributes with data
        # We do it like this to ensure that the standard attributes win
        # if there's a key clash
        combined = dict(list(data.items()) + list(self.attributes.items()))
        try:
            with LogStashTCP(self.server, self.port) as stcp:
                stcp.send_line(combined)
        except socket_error as serr:
            # Only warn if we are on production server
            if not self.testserver:
                self.logger.warn('Unable to connect to LogStash server at {0}:{1}'.format(self.server, self.port))
                self.logger.warn(str(serr))
                ret = False

        return ret

    def initial_log(self):
        '''
        Logs initial abnr startup data to LogStash
        '''
        ret = False

        ret = self.logstash_log({})
        self.logger.debug('Initial LogStash log sent')

        return ret

    def final_log(self, exitcode, exit_message=None):
        '''
        Logs final data to logstash
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
            message = dict(list(message.items()) + list(exit_message.items()))
        ret = self.logstash_log(message)
        self.logger.debug('Final LogStash log sent')

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
        self.logger.debug('Exception LogStash log sent')

        return ret

    def add_timestamp_attribute(self, attribute_name):
        '''
        Adds an attribute with name attribute_name to the list of attributes we'll log.
        The value is the time since epoch.

        :param attribute_name: The LogStash attribute name or key in the key:value pair
        :type attribute_name: str
        '''
        self.add_attribute(attribute_name, time.time())

class LogStashTCP(object):
    '''
    LogStashTCP is set up to be a context manager - that is, it should
    be used with the python 'with' statement, e.g.:

        with LogStashTCP(host, port) as mytcp:
            mytcp.send_line(attr_dict)

    That way the tcp connection is guaranteed to be closed even if
    there is an exception.

    Currently the only method is send_line (see below).
    '''

    def __init__(self, logstash_host, logstash_port):
        self.logstash_host = logstash_host
        self.logstash_port = logstash_port
        self.sock = None

    def __repr__(self):
        return 'LogStashTCP(\'{0}\', {1})'.format(self.logstash_host, self.logstash_port)

    def __enter__(self):
        self.sock = create_connection((self.logstash_host, self.logstash_port))
        return self

    def __exit__(self, etype, evalue, etrace):
        self.sock.close()

    def send_line(self, logstash_entry):
        '''
        Send a json line containing the key:value pairs from attr_dict
        to tcp port on tcp_host.

        Returns: None
        '''

        sline = json.dumps(logstash_entry)
        msg = sline + '\n'
        self.sock.send(msg.encode(errors='ignore'))        
