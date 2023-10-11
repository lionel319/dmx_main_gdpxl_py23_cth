#!/usr/bin/env python
'''
###########################################################
###########################################################
###########################################################
# Temporory host this here, to ungate dmx migration work. #
# Once the official code is ready, this will be deleted   #
###########################################################
###########################################################
###########################################################




$Id: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/icm_trigger/icm_pre_sync.py#1 $
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/icm_trigger/icm_pre_sync.py#1 $
$Date: 2022/12/13 $
$DateTime: 2022/12/13 18:19:49 $
$Change: 7411538 $
$File: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/icm_trigger/icm_pre_sync.py $
$Revision: #1 $
$Author: lionelta $

This trigger checks if a ICManage workspace of restricted project or restricted variant
is created on the designated path.

It exits with 0 if no issue

Exits with 1 if the disk path is not aligned with the designated disk path

For example:'Nadder' project must be on '/ice_pd/tc/nadder/'


Caveats:
--------
This trigger doesn't expand particular configuration to see if it contains 
configurations from restricted projects or variants. Enhancement item.

'''
from __future__ import print_function

# Shut up pylint. Lines >80 characters make sense in some cases.
# pylint: disable=C0301

from future import standard_library
standard_library.install_aliases()
import sys
import os
import re
import subprocess

triggerbase    = '${ICM_HOME}/triggers/icmpm'

def welcome_message(icmproject,icmvariant):

    print("# Running icm_workspace_presync trigger")
    print("# ICM Project : " + icmproject)
    print("# VARIANT     : " + icmvariant)

def get_site(p4port):

    match = re.search('(\w+)\.(\w+)\.intel\.com' ,p4port)
    if match:
        site = match.group(2)
    else:
        site = 0
    return site

def get_proj_disk(site,proj):
    '''
        get a list of project work disk with given project name
        return 
            list of the disk 
        or
            0 = no restriction applicable for the project 
    '''
    filelist = triggerbase + '/pre_sync/' + site + '.' + proj
    #print filelist

    if os.path.exists(filelist):
        pathlist = []
        with open(filelist, 'rU') as fhd:
            for line in fhd:
                line = line.rstrip() 
                pathlist.append(line)
        fhd.close()
        return pathlist
        # open file and return the item as list
    else:
        return 0

def check_proj_restrict(site,icmproject,p4clientdir):
    '''
        check if the p4clientdir is comply with the project disk path restriction
        return
            0 = project not restricted
            1 = the p4clientdir is in compliance (okay to setup workspace)
            2 = the p4clientdir does not comply to the restriction (cannot setup workspace)
    '''
    status, output = subprocess.getstatusoutput("/usr/intel/bin/sitecode")
    pathlist = get_proj_disk(site,icmproject)
    if(pathlist > 1):
        allowed = False
        for path in pathlist:
            path = "^" + path.rstrip() 
            if ( re.search(path, p4clientdir) ):
                allowed = True

            if status:  # cannot get sitecode
                pass
            else:       # with sitecode available
                rplwith = "/nfs/" + output.rstrip() + "/"
                path = path.replace('/nfs/site/',rplwith)

                if ( re.search(path, p4clientdir) ):
                    allowed = True

        if allowed:
            return 1
        else:
            return 2
        
    else:
        return 0

def main():
    '''
    Check violations    
    ./icm_pre_sync_pice.py cftham.da_i10.potato.6 /nfs/site/disks/da_infra_1/users/cftham/prod da_i10 potato $P4PORT
    '''
    exitval = 0
    if len(sys.argv) < 5:
        print('Fatal Error: Missing required arguments: p4client, p4clientdir, icmproject, icmvariant, p4port', file=sys.stderr)
        exitval = 1
    else:
        p4client    = sys.argv[1]
        p4clientdir = sys.argv[2]
        icmproject  = sys.argv[3]
        icmvariant  = sys.argv[4]
        p4port      = sys.argv[5]

    welcome_message(icmproject,icmvariant)

    site = get_site(p4port)
    if not site:
        print("-F- Cannot determine site from server name " + p4port + ".")
        print("-I- Please contact da_icm_admin@intel.com if you need further help.")
        exitval = 1
    else:
        # check if project variant is restricted
        checkstat = check_proj_restrict(site,icmproject,p4clientdir)
        if checkstat == 0 :
            print(icmproject + " is not a restricted project")
            exitval = 0
        if checkstat == 1 :
            exitval = 0
        if checkstat == 2 :
            exitval = 1
            paths = get_proj_disk(site,icmproject)
            print("-E- " + p4clientdir + " is not allowed to sync files from " + icmproject)
            print("-I- These are the approved disk paths for " + icmproject)
            print(paths)
            print("-I- Please contact da_icm_admin@intel.com if you need further help")
        
    
    #print "exit status " + str(exitval)
    return exitval

if __name__ == '__main__':
    sys.exit(main())


