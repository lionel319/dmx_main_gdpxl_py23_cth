'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/cache.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Utility Class that interacts with cache 

Copyright (c) Altera Corporation 2018
All rights reserved.
'''

import os
import re
import logging
import sys
import datetime
import dmx.utillib.utils
from dmx.utillib.utils import is_pice_env, run_command


class CacheError(Exception): pass

class Cache(object):
    def __init__(self, preview=False):
        self.preview = preview
        self.logger = logging.getLogger(__name__)
        
        ### CACHE path: /nfs/site/disks/fln_sion_1/cache/i10socfm/liotest1/rdf/REL5.0FM8revA0--TestSyncpoint__17ww404a/audit/audit.aib_ssm.rdf.xml
        self.cachedisk_regex = '^/nfs/[^/]+/disks/(?P<disk>[^_]+_sion(2)?_[^/]+)(/cache)?'
        self.cachepath_regex = self.cachedisk_regex + '/(?P<project>[^/]+)/(?P<variant>[^/]+)/(?P<libtype>[^/]+)/(?P<config>[^/]+)/(?P<filepath>.+)$'


    def is_path_cache_path(self, filepath):
        '''
        Check if given path is coming from cache path.
        Cache realpath follows strictly with this convention
            /nfs/site/disks/*_sion_

        http://pg-rdjira:8080/browse/DI-1373
        '''
        if re.search(self.cachedisk_regex, os.path.realpath(filepath)):
            return True
        return False


    def get_info_from_cache_path(self, filepath):
        '''
        given a fullpath to an NAA file,
        returns the info in a dictionary.

        Example:-
            filepath = /nfs/site/disks/fln_sion_1/cache/i10socfm/liotest1/rdf/REL5.0FM8revA0--TestSyncpoint__17ww404a/audit/audit.aib_ssm.rdf.xml
            return   = {
                'disk' : 'fln_sion_1',
                'project' : 'i10socfm',
                'variant' : 'liotest1',
                'libtype' : 'rdf',
                'config' : 'REL5.0FM8revA0--TestSyncpoint__17ww404a',
                'filepath' : 'audit/audit.aib_ssm.rdf.xml',
                'wsrelpath' : 'liotest1/rdf/audit/audit.aib_ssm.rdf.xml'
            }

            if does not match, return {}
        '''
        match = re.search(self.cachepath_regex, os.path.realpath(filepath))
        self.logger.debug("regex:{}".format(self.cachepath_regex))
        self.logger.debug('filepath:{}'.format(os.path.realpath(filepath)))
        if match == None:
            return {}
        else:
            ret = match.groupdict()
            ret['wsrelpath'] = '{}/{}/{}'.format(ret['variant'], ret['libtype'], ret['filepath'])
            return ret




