'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/naa.py#1 $
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
import sys
import datetime
import time
from dmx.utillib.utils import is_pice_env, run_command
#NAAPATH = '/nfs/site/disks/psg_flowscommon_1/naa/wplim_dev/naa.py'
NAAPATH = '/nfs/site/disks/psg_flowscommon_1/naa/current/naa.py' if not  os.environ.get('NAAPATH') else os.environ.get('NAAPATH')
NAAROOT = '/p/psg/naa'
# The user account used by NAA. Only this account may run 'naa put' for dmx related project/intent
NAAUSER = 'dmx'

class NAAError(Exception): pass

class NAA(object):
    def __init__(self, preview=False):
        self.naa = NAAPATH
        self.naa_basepath = NAAROOT
        self.preview = preview
        self.logger = logging.getLogger(__name__)
        self.naa_user = NAAUSER
        
        ### NAA path: /nfs/site/disks/psg_naa_1/Falcon/i10socfm/liotest2/rcxt/dev/toto.1
        self.naapath_regex = '^/nfs/site/disks/(?P<disk>[^_]+_naa_[^/]+)/(?P<project>[^/]+)/(?P<variant>[^/]+)/(?P<libtype>[^/]+)/(?P<library>[^/]+)/(?P<filepath>.+\.\d+)$'

        # Check that naa tool exist
        if not os.path.exists(self.naa):
            raise NAAError('{} does not exist'.format(self.naa))

        # Check that user can run naa
        if not os.access(self.naa, os.X_OK):
            raise NAAError('{} is not allowed to run NAA'.format(os.getenv('USER')))


    def is_path_naa_path(self, filepath):
        '''
        Check if given path is coming from NAA path.
        NAA realpath follows strictly with this convention
            /nfs/site/disks/*_naa_*/

        http://pg-rdjira:8080/browse/DI-1138
        '''
        if re.search('^/nfs/site/disks/[^_]+_naa_', os.path.realpath(filepath)):
            return True
        return False


    def get_info_from_naa_path(self, filepath):
        '''
        given a fullpath to an NAA file,
        returns the info in a dictionary.

        Example:-
            filepath = /nfs/site/disks/psg_naa_1/i10socfm/liotest2/rcxt/dev/a/b/toto.1
            return   = {
                'disk' : 'psg_naa_1',
                'project' : 'i10socfm',
                'variant' : 'liotest2',
                'libtype' : 'rcxt',
                'library' : 'dev',
                'filepath' : 'a/b/toto.1',
                'wsrelpath' : 'a/b/toto'
            }

            if does not match, return {}
        '''
        match = re.search(self.naapath_regex, os.path.realpath(filepath))
        self.logger.debug("regex:{}".format(self.naapath_regex))
        self.logger.debug('filepath:{}'.format(os.path.realpath(filepath)))
        if match == None:
            return {}
        else:
            ret = match.groupdict()
            ret['wsrelpath'] = '{}/{}/{}'.format(ret['variant'], ret['libtype'], os.path.splitext(ret['filepath'])[0])
            return ret


    def get_tags(self, project, intent, variant, libtype):
        path = '{}/{}/{}/{}/{}'.format(NAAROOT, project, intent, variant, libtype)
        tags = os.listdir(path)
        return tags                

    def get_naa_path(self, project, intent, variant, libtype, tag, naa_file):
        '''
        Returns file's path in NAA
        '''
        return '{}/{}/{}/{}/{}/{}/{}'.format(NAAROOT, project, intent, variant, libtype, tag, naa_file)

    def file_exists(self, project, intent, variant, libtype, tag, naa_file):
        '''
        Returns True if file exists in NAA
        '''    
        ret = 0
        if os.path.exists(self.get_naa_path(project, intent, variant, libtype, tag, naa_file)):
            ret = 1
        return ret            

    def is_tag_immutable(self, tag):
        '''
        Returns True if tag is immutable (REL/snap)
        '''
        ret = False
        if tag.startswith('REL') or tag.startswith('snap-'):
            ret = True
        return ret            

    def is_tag_mutable(self, tag):
        '''
        Returns True if tag is mutable (non-REL/non-snap)
        '''
        return not self.is_tag_immutable(tag)              

    def push_to_naa(self, project, intent, variant, libtype, tag, source_realpath, subdir=None, incremental=True):
        '''
        Push a directory's content to NAA path
        '''
        ret = 0
        command = 'python {} put -u {} -p {} -i {} -v {} -lib {} -t {} --source {}'.format( 
                    self.naa, self.naa_user, project, intent, variant, libtype, tag, source_realpath)
        if subdir:
            command = '{} --subdir {}'.format(command, subdir)
        if incremental:
            command = '{} -inc'.format(command)

        self.logger.debug(command)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command, retry=True)
            self.logger.debug(stdout)
            self.logger.debug(stderr)
            if exitcode:
                err = 'stdout:{}\nstderr:{}'.format(stdout, stderr)
                self.logger.error(err)
                ret = 1

            # http://pg-rdjira:8080/browse/DI-1385
            # Add a delay of 1min to accommodate for NFS delay
            time.sleep(60)
                        
        return ret   

    def clone_tag(self, project, intent, variant, libtype, tag, file, target):
        '''
        Clone a NAA tag
        '''
        ret = 0
        command = 'python {} clone -u {} -p {} -i {} -v {} -lib {} -t {} -f {} -tar {}'.format( 
                    self.naa, self.naa_user, project, intent, variant, libtype, tag, file, target)

        self.logger.debug(command)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                err = 'stdout:{}\nstderr:{}'.format(stdout, stderr)
                self.logger.error(err)
                ret = 1

        # http://pg-rdjira:8080/browse/DI-1385
        # Add a delay of 1min to accommodate for NFS delay
        time.sleep(60)

        return ret          

    def create_label(self, project, intent, variant, libtype, tag):
        '''
        Create a new label in NAA
        '''
        ret = 0
        command = 'python {} label -u {} -p {} -i {} -v {} -lib {} -t {}'.format( 
                    self.naa, self.naa_user, project, intent, variant, libtype, tag)

        self.logger.debug(command)
        if not self.preview:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                err = 'stdout:{}\nstderr:{}'.format(stdout, stderr)
                self.logger.error(err)
                ret = 1
        return ret   


