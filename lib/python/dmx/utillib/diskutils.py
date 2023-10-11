#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/diskutils.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class with all disk related utilities.

Usage Example:-
===============

du = dmx.utillib.diskutils.DiskUtils(site='sc')
dd = du.get_all_disks_data("r_sion_")
print dd
[{'Avail': 975298,                               
  u'Size': 1048576,                              
  u'StandardPath': u'/nfs/site/disks/gdr_sion_1',
  u'Usage': 73278},                              
 {'Avail': 663039,                               
  u'Size': 2097152,                              
  u'StandardPath': u'/nfs/site/disks/rnr_sion_1',
  u'Usage': 1434113},                            
 {'Avail': 313415,                               
  u'Size': 1572864,                              
  u'StandardPath': u'/nfs/site/disks/whr_sion_1',
  u'Usage': 1259449}]  

sdd = du.sort_disks_data_by_key(dd, key='Avail')
print sdd
[{'Avail': 663039,                               
  u'Size': 2097152,
  u'StandardPath': u'/nfs/site/disks/rnr_sion_1',
  u'Usage': 1434113},
 {'Avail': 313415,
  u'Size': 1572864,
  u'StandardPath': u'/nfs/site/disks/whr_sion_1',
  u'Usage': 1259449},
 {'Avail': 975298,
  u'Size': 1048576,
  u'StandardPath': u'/nfs/site/disks/gdr_sion_1',
  u'Usage': 73278}]

m = a.find_folder_from_disks_data(dd, r'/whr/wrpcie_top/fvsyn/snap-dev__18ww134\b', maxdepth=5, mindepth=5)
print m
'/nfs/site/disks/whr_sion_1/cache/whr/wrpcie_top/fvsyn/snap-dev__18ww134'

'''
from __future__ import print_function

from builtins import object
import os
import logging
import sys
import re
import time
from pprint import pprint, pformat
import multiprocessing
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.server
from dmx.errorlib.exceptions import *
import dmx.utillib.stringifycmd

LOGGER = logging.getLogger(__name__)

class DiskUtils(object):

    def __init__(self, site='local'):
        '''
        site = local/png/sc 

        when pg/sc,
            it will ssh to png/sc host, before running all commands.
        when local
            no ssh is performed.
        '''
        self.stodexe = 'env -i /usr/intel/bin/stodstatus'
        self.site = site


    def get_all_disks_data(self, regexstr):
        '''
        Example:-
            regexstr = 'fln_sion_'
            return = {[
                {u'Path': u'/nfs/png/disks/fln_sion_1', u'Size': 1000, u'Usage': 300, u'Avail':700},
                {u'Path': u'/nfs/png/disks/fln_sion_2', u'Size': 1000, u'Usage': 400, u'Avail':600},
                ...   ...   ...
            ]}

        *Numbers are in Mega-bypes.
        '''
        arcsite = os.getenv("ARC_SITE", '')
        cmd = '''{} area '''.format(self.stodexe)
        if self.site != 'local':
            if 'sc' in arcsite:
                cmd += ' --cell sc,zsc7 '
            else:
                cmd += ' --cell {} '.format(self.site)
        else:
            if 'sc' in arcsite:
                cmd += ' --cell sc,zsc7 '

        cmd += ''' --fi 'standardpath,size,usage' --fo json 'standardpath=~"{}"' '''.format(regexstr)
        #finalcmd = self.get_final_command(cmd)
        finalcmd = cmd

        LOGGER.debug("running finalcmd: {}".format(finalcmd))
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(finalcmd)
       
        LOGGER.debug('exitcode:{}\nstdout:{}\nstderr:{}'.format(exitcode, stdout, stderr))
        if exitcode:
            raise Exception("Error running the following command:-\n{}".format(finalcmd))

        try:
            jsondata = json.loads(stdout)
            for data in jsondata:
                if 'Size' in data and 'Usage' in data:
                    data['Avail'] = data['Size'] - data['Usage']
        except:
            raise

        return jsondata


    def sort_disks_data_by_key(self, diskdata, key='Avail'):
        '''
        diskdata == return value from get_all_disks_data()
        return = same format as `diskdict`, with the largest 'key' value first.
        '''
        return sorted(diskdata, key=lambda d: d[key], reverse=True)


    def find_folder_from_disks_data(self, diskdata, matchpath, diskpostfix='', maxdepth='99', mindepth='1'):
        '''
        *For detail difference/usage between this vs find_exact_folder_from_disks_data(), refer to docstring 
        from find_exact_folder_from_disks_data()*

        diskdata = return value from get_all_disks_data()
        matchpath = string for path matching, must be compatible with 'grep' command
        maxdepth = maxdepth option that will be passed into the 'find --maxdepth' command
        diskpostfix = if set, find will be applied to <DiskStandardPath>/<diskpostfix>/

        return = the folder's fullpath
        '''
        for d in diskdata:
            findpath = d['StandardPath']
            if diskpostfix:
                findpath = os.path.join(findpath, diskpostfix)
            cmd = '''find {} -maxdepth {} -mindepth {} -noleaf -type d | grep '{}' '''.format(findpath, maxdepth, mindepth, matchpath)
            finalcmd = self.get_final_command(cmd)
            LOGGER.debug("running finalcmd: {}".format(finalcmd))
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(finalcmd)
            LOGGER.debug('exitcode:{}\nstdout:{}\nstderr:{}'.format(exitcode, stdout, stderr))
            if not exitcode:
                return stdout.strip()
        return ''


    def find_exact_folder_from_disks_data(self, diskdata, matchpath):
        '''
        If you know exactly the fullpath that you wanna find, use this instead of find_folder_from_disks_data()
        This runs way more faster, but find_folder_from_disks_data() provides more flexibility.

        if you already know the path u are looking for, eg:-
            /nfs/site/disks/psg_cicq_1/users/cicq/aaa.bbb.ccc
        or you already have a fixed directory structure (level), eg:-
            /nfs/site/disks/psg_cicq_1/*/*/aaa.bbb.ccc
        then u can do these:-
            find_exact_folder_from_disks_data(diskdata, matchpath='users/cicq/aaa.bbb.ccc')
            find_exact_folder_from_disks_data(diskdata, matchpath='*/*/aaa.bbb.ccc')

        if you do not know the exact full path, or have no idea of the level of directory structure eg:-
            /nfs/site/disks/psg_cicq_1/xxx/yyy/???/???/aaa.bbb.ccc
        then use find_folder_from_disks_data(), eg:-
            find_folder_from_disks_data(diskdata, matchpath=r'aaa.bbb.ccc', diskpostfix='xxx/yyy', maxdepth=5, mindepth=1)

        return = the folder's fullpath
        '''
        for d in diskdata:
            findpath = os.path.join(d['StandardPath'], matchpath)
            cmd = '''/bin/tcsh -f -c 'test -d {} && glob {} ' '''.format(findpath, findpath)
            finalcmd = self.get_final_command(cmd)
            LOGGER.debug("running finalcmd: {}".format(finalcmd))
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(finalcmd)
            LOGGER.debug('exitcode:{}\nstdout:{}\nstderr:{}'.format(exitcode, stdout, stderr))
            if not exitcode:
                return stdout.strip()
        return ''


    def get_final_command(self, cmd):
        if self.site == 'local':
            return cmd
        elif self.site in ['sc', 'png']:
            s = dmx.utillib.stringifycmd.StringifyCmd(cmd, sshopts={'site':self.site})
            return s.get_finalcmd_string()
        else:
            raise Exception("Unsupported Site: {}!".format(self.site))

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

    #########################################
    site = 'sc'
    regexstr = '_cicq_'
    folder = r'i10socfm.liotestfc1.test3'
    maxdepth = mindepth = 1
    diskpostfix = 'users/cicq'
    exactpath = r'*/*/' + folder
    #########################################
    site = 'sc'
    regexstr = 'fln_naa_'
    folder = r'dev'
    maxdepth = mindepth = 1
    diskpostfix = r'i10socfm/liotest1/*'
    exactpath = diskpostfix + '/' + folder
    #########################################

    a = DiskUtils(site=site)
    print('======================================')
    dd = a.get_all_disks_data(regexstr=regexstr)
    pprint(dd)
    sys.exit()
    print('======================================')
    pprint(a.sort_disks_data_by_key(dd))
    print('======================================')
    xx = a.find_folder_from_disks_data(dd, folder, diskpostfix=diskpostfix, maxdepth=maxdepth, mindepth=mindepth)
    print("xx:{}".format(xx))
    print('======================================')
    s = a.find_exact_folder_from_disks_data(dd, exactpath)
    print("s:{}".format(s))
    print('======================================')




