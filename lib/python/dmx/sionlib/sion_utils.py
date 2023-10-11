#!/usr/bin/env python
'''
Description: utility for sion

Author: Kevin Lim Khai - Wern, Natalia Baklitskaya
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str
from past.utils import old_div
from builtins import object
import subprocess
import os
import sys
import logging
import json
import multiprocessing
import shutil
import time
import datetime
import configparser
import glob
import re 
if sys.version_info[0] > 2:
    import functools as ft
else:
    import functools32 as ft
import copy

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), '..', '..')
sys.path.insert(0, LIB)

import dmx.utillib.arcutils
import dmx.abnrlib.config_factory
from dmx.abnrlib.icm import ICManageCLI
import dmx.abnrlib.flows.workspace
import dmx.dmxlib.workspace
from dmx.utillib.utils import is_pice_env, get_ww_details, quotify, remove_quotes
from joblib import Parallel, delayed
import dmx.ecolib.ecosphere
from socket import gethostname
import dmx.utillib.washgroup
import dmx.utillib.utils
from dmx.utillib.diskutils import DiskUtils

LOGGER = logging.getLogger(__name__)
#class PopulateError(Exception): pass

# Not all libtypes follow the default workspace mapping
# Cadence/Virtuoso libtypes are a good example
# This dict defines libtype => custom mapping
NON_STANDARD_LIBTYPES = {
    'oa' : '$variant',
    'oa_sim' : '$variant_sim',
}

missing_files = []
golden_ws_path = "/nfs/site/disks/fm8_fctiming_2/users/bblanc/workspace/z1557a.snap-fm8-z1557a-stable30b__18ww131a.reference"

class SionDisk(object):
    def __init__(self):
        self.du = DiskUtils()
        self.largest_disk, self.all_proj_disk = self._get_largest_disk_and_proj_disk_sion2()
        pass

    def _get_largest_disk_and_proj_disk_sion2(self):
        sion2disks = glob.glob('/p/psg/sion2/*/*')
        all_proj_disk = {}
        largest_disk = {}
        free_space = {}

        for ea_d in sion2disks:
            match = re.search("(\S+)_sion2_(\d+)", ea_d)
            if match:
                try:
                    #Fail safe so that all sion disk is  readable
                    os.chdir(ea_d)
                    os.chdir('-')
                except:
                    pass
                proj = match.group(1).split('/')[-1]
                if not all_proj_disk.get(proj):
                    all_proj_disk[proj] = [ea_d]
                else:
                    all_proj_disk[proj].append(ea_d)
            try:
                if sys.version_info[0] < 3:
                    sys.path.insert(0, "/p/psg/ctools/python/2.7.13/linux64/suse/lib/python2.7/site-packages/")
                import psutil
                hdd = psutil.disk_usage(ea_d)
                if sys.version_info[0] < 3:
                    sys.path.pop(0)

                if not largest_disk.get(proj):
                    largest_disk[proj] = ea_d
                    free_space[proj] = hdd.free
                elif int(hdd.free) > int(free_space.get(proj)):
                    largest_disk[proj] = ea_d
                    free_space[proj] = hdd.free
            except OSError:
                LOGGER.warning('No permission to view {}'.format(ea_d))


        return largest_disk, all_proj_disk


    def _get_largest_disk_and_proj_disk(self):
        large_disk = {}
        all_proj_disk = {}
        proj_disk = []

        for proj, ea_disk in list(self.list_of_proj_disk.items()):
            dd = self.du.get_all_disks_data(ea_disk)
            sorted_disk = self.du.sort_disks_data_by_key(dd)
            largest_disk = sorted_disk[0].get('StandardPath')
            large_disk[proj] = largest_disk 
            proj_disk = [x.get('StandardPath') for x in dd]
            all_proj_disk[proj] = proj_disk

        return large_disk, all_proj_disk

    @ft.lru_cache(maxsize = 128)
    def is_pvcd_in_sion_disk(self, proj, ip, deliverable, bom):
        # check for sion and sion2
        #all_sion_disk = [self.all_proj_disk, self.sion2_all_proj_disk]
        all_sion_disk = [self.all_proj_disk]

        for ea_disk in all_sion_disk:
            for proj_disks in list(ea_disk.values()):
                for proj_disk in proj_disks:
                    #fmt = '{}/cache/{}/{}/{}/{}'.format(proj_disk, proj, ip, deliverable, bom)
                    fmt = '{}/{}/{}/{}'.format(proj_disk, ip, deliverable, bom)
                    #print fmt
                    if os.path.exists(fmt) and os.access(fmt, os.R_OK):
                        LOGGER.debug('Found {} in cache'.format(fmt))
                        return fmt

        LOGGER.debug("Can't find cache for {}, or path might be inaccessible.\nAvailable caches: {}".format([proj, ip, deliverable, bom], self.all_proj_disk.values()))
        return False


class CacheResults(object):
    def __init__(self, deferred_boms = None, mutable_boms = None, immutable_boms = None, synced_boms = None, failed_boms = None, boms_for_print = '', synced_boms_for_print = ''):
        self.deferred_boms = [] if not deferred_boms else deferred_boms
        self.mutable_boms = [] if not mutable_boms else mutable_boms
        self.immutable_boms = [] if not immutable_boms else immutable_boms
        self.synced_boms = [] if not synced_boms else synced_boms
        self.failed_boms = [] if not failed_boms else failed_boms
        self.boms_for_print = boms_for_print
        self.synced_boms_for_print = synced_boms_for_print

    def append(self, item):
        #if not isinstance(item, self.type):
        #    raise TypeError, 'item is not of type %s' % self.type
        self.deferred_boms.extend(item.deferred_boms)
        self.mutable_boms.extend(item.mutable_boms)
        self.immutable_boms.extend(item.immutable_boms)
        self.synced_boms.extend(item.synced_boms)
        self.failed_boms.extend(item.failed_boms)
        self.boms_for_print+=item.boms_for_print
        self.synced_boms_for_print+=item.synced_boms_for_print

def run_as_headless_user(project = None, variant = None, libtype = None, config = None, dir = None, command = None, user = None, cfgfile = None, icm_command = None, misc = None):
    if is_pice_env():
        ret = run_as_psginfraadm(project, variant, libtype, config, dir, command, user, cfgfile, icm_command, misc)
    else:
        ret = run_as_icmrelreader(project, variant, libtype, config, dir, command, user, cfgfile, icm_command, misc)
    return ret

def run_as_psginfraadm(project = None, variant = None, libtype = None, config = None, dir = None, command = None, user = None, cfgfile = None, icm_command = None, misc = None):
    # For testing
    if ('da/infra/dmx/main' in os.getcwd()) :
        LOGGER.info("TESTING FROM MAIN: Your request has been submitted. Please do not kill/terminate/cancel the job until it is done;\nIf you are running in production, please email psgicmsupport@intel.com with this message.")
        cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm_sion_test"
    # For production
    else :
        LOGGER.info("Your request has been submitted. Please do not kill/terminate/cancel the job until it is done.")
        cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm" # For dev work, comment below, uncomment this line
    #cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm" # For production environment, comment above, uncommment this line
    cmd = "%s %s %s %s %s %s %s %s %s %s %s" % (cmd, command, project, variant, libtype, config, dir, user, cfgfile, icm_command, misc)
    exitcode = run_command_only(cmd)
    return exitcode

def run_as_headless_user_cache_mode(command = None, project = None, ip = None, deliverable = None, bom = None, cache_dir = None, ws_dir = None, wsname = None, user = None, cache_only = False, cfgfile = None, misc = None):
    LOGGER.info("run_as_headless_user_cache_mode cfgfile: %s" % cfgfile)
    if is_pice_env():
        ret = run_as_psginfraadm_cache_mode(command, project, ip, deliverable, bom, cache_dir, ws_dir, wsname, user, cache_only, misc)
    else:
        LOGGER.error("Caching SION can only be run in PICE environment.")
        ret = 1
    return ret

def run_as_psginfraadm_cache_mode(command = None, project = None, ip = None, deliverable = None, bom = None, cache_dir = None, ws_dir = None, wsname = None, user = None, cache_only = False, misc = None):
    LOGGER.info("misc: %s" % misc)
    # For testing with nbaklits workspace
    if ('nbaklits/ICM/SION' in os.getcwd()) :
        LOGGER.info("TESTING with nbaklits ws: Your request has been submitted. Please do not kill/terminate/cancel the job until it is done.")
        cmd = "/nfs/sc/disks/da_scratch_1/users/nbaklits/workspace/da/infra/dmx/main/lib/python/dmx/sionlib/swap_to_psginfraadm_cache_nbaklits"
    # For testing
    elif ('da/infra/dmx/main' in os.getcwd()) :
        LOGGER.info("TESTING FROM MAIN: Your request has been submitted. Please do not kill/terminate/cancel the job until it is done.")
        cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm_cache_sion_test"
    # For production
    else :
        LOGGER.info("Your request has been submitted. Please do not kill/terminate/cancel the job until it is done.")
        cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm_cache" # For dev work, comment below, uncomment this line
    #cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm" # For production environment, comment above, uncommment this line
    cmd = "%s %s %s %s %s %s %s %s %s %s %s %s" % (cmd, command, project, ip, deliverable, bom, cache_dir, ws_dir, wsname, user, cache_only, misc)
    final_cmd = cmd
 
   
    ### This is needed for StandAlone dmx
    needed_envvar = ['DMXDATA_ROOT', 'DB_FAMILY']
    setenvcmd = ''
    for ev in needed_envvar:
        evval = os.getenv(ev, "")
        if not evval:
            raise("{} env var not set!".format(ev))
        setenvcmd = setenvcmd + 'setenv {} {};'.format(ev, evval)

    ### Correct sequence has to be:-
    ### tnr_ssh( arc_submit( wash( sion_populate ) ) )
    dmxsetup_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'bin', '_dmxsetupclean')
    populate_cache_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'populate_cache.py')
    populate_cache_cmd = "{} {} {} -cmd {} -p {} -i {} -d {} -b {} -cache_dir {} -ws_dir {} -w {} -u {} -cache_only {} -misc {}".format(
        setenvcmd, dmxsetup_exe, populate_cache_exe, command, project, ip, deliverable, bom, cache_dir, ws_dir, wsname, user, cache_only, misc)
    LOGGER.debug("populate_cache_cmd: {}".format(populate_cache_cmd))
  
    #wash_group_str = gen_reportwashgroups_string()
    wash_group_str = get_needed_linux_groups_by_pvc(project, ip, bom)
    wash_cmd = "wash -n {} psgda -c '{}'".format(
        wash_group_str, populate_cache_cmd)

    setenv_cmd = get_setenv_string()
    wash_cmd = setenv_cmd + wash_cmd
    LOGGER.debug("wash_cmd: {}".format(wash_cmd))

    try:
        arcres = dmx.utillib.arcutils.ArcUtils().get_arc_job()['resources']
    except:
        arcres = ''

    #arc_cmd = "arc submit --watch {} -- {} ".format(arcres, quotify(wash_cmd))
    arc_cmd = "arc submit ostype/suse12,{} ncpus=2 -- {} ".format(arcres, quotify(wash_cmd))
    LOGGER.debug("arc_cmd: {}".format(arc_cmd))

    tnrssh_cmd = "/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost {} ".format(quotify(arc_cmd))
    LOGGER.debug("tnrssh_cmd:{}".format(tnrssh_cmd))

    final_cmd = tnrssh_cmd
    LOGGER.debug("final_cmd: {}".format(final_cmd))
   
    #exitcode = run_command_only(final_cmd)
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(final_cmd)
    arcjobid = stdout.splitlines()[0]
    LOGGER.info("Arc Job {} Submitted. Waiting for job completion ...".format(arcjobid))

    # ths is to clena up .lock file if there is any crash happen so that user can rerun thier job again
    script_path = LIB + '/../scripts/remove_lock_file.py'
    cleanup_cmd = "arc wait {0}; {1} -a {0}".format(arcjobid, script_path)
 #   os.system("/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost {} ".format(quotify(cleanup_cmd)))
    cl_wash_cmd = "wash -n {} psgda -c '{}'".format(wash_group_str, cleanup_cmd)
    cl_arc_cmd = "arc submit {} -- {} ".format(arcres, quotify(cl_wash_cmd))
    cl_tnrssh_cmd = "/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost {} ".format(quotify(cl_arc_cmd))
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cl_tnrssh_cmd)
    cl_arcjobid = stdout.splitlines()[0]
    LOGGER.info("Cleanup Arc Job {} Submitted. Waiting for job completion ...".format(cl_arcjobid))


    os.system("arc wait {}".format(arcjobid))

    exitcode, stdout, stderr = dmx.utillib.utils.run_command("arc job {} return_code".format(arcjobid))
    returncode = stdout.splitlines()[0]
    LOGGER.info("Arc Job {} completed with return_code:{}".format(arcjobid, returncode)) 

    return int(returncode)

@ft.lru_cache(maxsize = 128)
def get_needed_linux_groups_by_pvc(project, ip, bom):
    wg = dmx.utillib.washgroup.WashGroup()
    group_list = wg.get_groups_by_pvc(project, ip, bom, include_eip_groups=True, include_base_groups=True)
    return ' '.join(group_list)


def get_setenv_string():
    '''
    if $DB_FAMILIES is defined:
        return 'setenv DB_FAMILIES <$DB_FAMILIES>;'
    else:
        return ''
    and 
    set DMX_GDPSITE
    '''
    val = os.getenv("DB_FAMILIES", "")
    site = os.getenv("DMX_GDPSITE", "")
    ret = ""
    if val:
        ret = 'setenv DB_FAMILIES "{}";'.format(val)
    if site:
        ret = ret + ' setenv DMX_GDPSITE "{}";'.format(site)
    return ret


def gen_reportwashgroups_string():
    '''
    if $DB_FAMILIES is defined,
        use it
    else
        use $DB_FAMILY
    '''
    families = os.getenv("DB_FAMILIES", os.getenv("DB_FAMILY", ""))
    retval = ""
    if families:
        retval = "`reportwashgroups -f {}`".format(families)
    return retval


def gen_reportwashgroups_string_from_envvar(envvar):
    '''
    if env var <envvar>  is defined, eg:-
        >setenv <envvar> "falcon reynoldsrock"

    ... the return string will be:-
        " `reportwashgroups -f falcon` `reportwashgroups -f reynoldsrock` "

    This return string can be passed into the wash command directly, eg:-
        > wash -n `reportwashgroups falcon` `reportwashgroups reynoldsrock` -c 'my_script.py'
    
    If <envvar> is not defined, return ''
    '''
    val = os.getenv(envvar, '')
    retval = ''
    cmd = "`reportwashgroups -f {} `"
    if val:
        for familyname in val.split():
            retval += cmd.format(familyname) + " "
    return retval



def run_as_icmrelreader(project = None, ip = None, deliverable = None, bom = None, dir = None, command = None, user = None, cfgfile = None, icm_command = None, misc = None):
    LOGGER.info("Your request has been submitted. Please do not kill/terminate/cancel the job until it is done.")
    cmd = "/tools/dmx/run_as_icmrelreader" 
    cmd = "%s %s %s %s %s %s %s %s %s %s %s" % (cmd, command, project, ip, deliverable, bom, dir, user, cfgfile, icm_command, misc)
    exitcode = run_command_only(cmd)
    return exitcode

def run_command_only(command, stdin=None, timeout=None):
    '''
    Run a sub-program in subprocess.
    Returns a tuple of exitcode, stdout, stderr
    '''
    proc = subprocess.Popen(command, bufsize=1, shell=True, stdin=subprocess.PIPE)
    proc.wait()
    exitcode = proc.returncode
    return exitcode

def run_command(command, stdin=None, timeout=None):
    '''
    Run a sub-program in subprocess.
    Returns a tuple of exitcode, stdout, stderr
    '''
    proc = subprocess.Popen(command, bufsize=1, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(stdin)
    exitcode = proc.returncode
    return (exitcode, stdout.decode(), stderr.decode())

def print_errors(cmd, exitcode, stdout, stderr):
    LOGGER.error("User = %s" % os.getenv('USER'))
    LOGGER.error("Hostname = %s" % os.getenv('HOSTNAME'))
    LOGGER.error("ARC Job ID = %s" % os.getenv('ARC_JOB_ID'))
    LOGGER.error("Command = %s" % cmd)
    LOGGER.error("Exitcode = %s" % exitcode)
    LOGGER.error("Stdout = %s" % stdout)
    LOGGER.error("Stderr = %s" % stderr)
    return 1

def read_sync_config_file(cfgfile):
    '''
    Read quicksync configuration file and return the config object
    Validate and make sure all sections contain these key:-
    - variants & libtypes -or-
    - specs
    '''
    error = ''
    config = configparser.RawConfigParser()
    config.read(cfgfile)
    for section in config.sections():
        if 'specs' in config.options(section):
            continue
        if 'variants' not in config.options(section):
            error += 'variants: key not found in section [{}] in cfgfile {}\n'.format(section, cfgfile)
        if 'libtypes' not in config.options(section):
            error += 'libtypes: key not found in section [{}] in cfgfile {}'.format(section, cfgfile)
    if error:
        LOGGER.error(error)
        LOGGER.error('ConfigFile provided is invalid')
    return config

def process_cfgfile(cfgfile):
    wsobj = dmx.abnrlib.flows.workspace.Workspace()
    if os.path.isfile(cfgfile):
        errmsg, config = wsobj.read_sync_config_file(cfgfile)
    else:
        LOGGER.error("Invalid cfgfile path %s provided" % cfgfile)
        return []
    #else:
    #    errmsg, config = wsobj.write_sync_config_file(cfgfile)

    if errmsg or not config:
        raise

    msg = 'Sync workspace for ...\n'
    for section in config.sections():
        msg += '[{}]\n'.format(section)
        if config.has_option(section, 'specs'):
            msg += "- specs: {}\n".format(config.get(section, 'specs'))
        else:
            for key in ['variants', 'libtypes']:
                msg += "- {}: {}\n".format(key, config.get(section, key))
    LOGGER.info(msg)

    ### Always sync ipspec libtype for all variants (fogbugz 220876)
    intsection = '__internal_section__'
    config.add_section(intsection)
    config.set(intsection, 'variants', '*')
    config.set(intsection, 'libtypes', 'ipspec')

    for section in config.sections():
        variants = []
        libtypes = []
        specs = []
        if config.has_option(section, 'specs'):
            specs = config.get(section, 'specs').split()
    return specs

def find_symlinks(filename, resultspath):
    with open(filename) as f:
        filelist = f.readlines()
    f.close()
    symlinksfile = open("%s/symlinks.txt" % resultspath, 'w')
    nonsymlinksfile = open("%s/nonsymlinks.txt" % resultspath, 'w')
    for file in filelist:
        file = file.strip()
        if os.path.islink(file):
            symlinksfile.write("%s\n" % file)
        elif os.path.realpath(file)!=file:
            symlinksfile.write("%s\n" % file)
        elif os.path.isdir(file):
            try:
                result = os.readlink(file)
                if result!=file:
                    symlinksfile.write("%s\n" % file)
            except:
                nonsymlinksfile.write("%s\n" % file)
        else:
            nonsymlinksfile.write("%s\n" % file)
    symlinksfile.close()
    nonsymlinksfile.close()


def get_simple_boms(project, ip, bom, deliverable=None):
    LOGGER.info("NEW get_simple_boms: Ignore cache_dir/project/ip/.config dir and scan thru icm instead.")

    if deliverable is None:
        cli = ICManageCLI()
        bom_list = cli.get_flattened_config_details(project, ip, bom, retkeys=['variant:parent:name', 'project:parent:name','libtype:parent:name','name'])
        bom_list = dmx.utillib.utils.replace_parent_name(bom_list)
    else:
        deliverable_config = {
            'project' : project,
            'variant' : ip,
            'libtype' : deliverable,
            'library' : '',
            'release' : '',
            'config' : bom,
            'description' : '',
        }
        bom_list = []
        bom_list.append(deliverable_config)
    LOGGER.info("bom_list: {}".format(bom_list))
    return bom_list


def link_files(src_path, sl_path, broken_link):
    # after link we need to find .icmconfig file and remove them, else there will be conflict
    # need to optimize this part, not sure if it is a FC hier, this find command might take time.
    cmd = 'cp -sfLr {0}/* {1};  find {1} -name .icmconfig -exec rm -rf {{}} \;'.format(src_path, sl_path)
    #LOGGER.info(cmd)
    exitcode, stdout, stderr = run_command(cmd)
    #if exitcode:
    #    print_errors(cmd, exitcode, stdout, stderr)
    return broken_link

def link_files2(src_path, sl_path, broken_link):
    #print "Creating symbolic links at file level"
    try:
        src_contents = os.listdir(src_path)
        #sl_contents = os.listdir(sl_path)
    except os.error as msg:
        LOGGER.error('{}: warning: cannot listdir: {}'.format(src_path, msg))
        return 1
    #print ("Contents of %s: %s" % (src_path, src_contents))
    #print ("Corresponding ws path: %s, contents: %s" % (sl_path,os.listdir(sl_path)))
    for name in src_contents :
      #print "Item: %s" % name
        if ((name!=".sion") and (name!=".icmconfig") and (name!=".icminfo")):
            src_pathname = os.path.join(src_path, name)
            #print("Source pathname: %s" % src_pathname)
            sl_pathname = os.path.join(sl_path, name)
            # all deliverables directories should already be pre-populated
            #if not name in sl_contents:
                #print "%s is not in %s" % (name, os.path.abspath(sl_path))
            if os.path.isdir(src_pathname):
                #print "This is a DIRECTORY"
                if not os.path.isdir(sl_pathname):
                    try:
                        #LOGGER.info("Making directory %s" % sl_pathname)
                        os.makedirs(sl_pathname, 0o770)
                    except:
                        #print "hit exception"
                        LOGGER.info("Could not create directory %s" % sl_pathname)
                        sys.exit(1)
                        #raise PopulateError("Could not create directory %s" % sl_pathname)
                link_files(src_pathname, sl_pathname, broken_link)
            elif not os.path.isfile(sl_pathname):
                #print "Linking %s to %s" % (sl_pathname, src_pathname)
                if not os.path.exists(os.path.dirname(sl_pathname)):
                    try:
                        #LOGGER.info("Making directory %s" % os.path.dirname(sl_pathname))
                        os.makedirs(os.path.dirname(sl_pathname))
                    except OSError as exc: # Guard against race condition
                        if exc.errno != errno.EEXIST:
                            LOGGER.info("Could not create directory %s; Directory already exists" % sl_pathname)
                try:
                    if is_symlink(src_pathname):
                        link_symlink(src_pathname, sl_pathname)
                        broken_link.append(sl_pathname)
                    else:
                        LOGGER.info('Link {} to {}'.format(src_pathname,sl_pathname))
                        os.symlink(src_pathname, sl_pathname)
                except Exception as E:
                    LOGGER.error(E)
                    LOGGER.error("Could not create symlink from %s to %s" % (sl_pathname, src_pathname))
                    sys.exit(1)
                    #raise PopulateError("Could not create symlink from %s to %s" % (sl_pathname, src_pathname))

    return broken_link

def link_symlink(path, sl_path):
    '''
    Create the symlink based on the link 
    eg. In cache area:
            cachearea/a.v -> ../rtl/a.v (broken link)
        Default:
            wsroot/variant/lint/a.v -> cachearea/a.v (broken link)

        Become:
            wsroot/variant/lint/a.v -> ../rtl/a.v (Non-Broken link)
    '''
    link_path = get_link_from_symlink(path)
    os.symlink(link_path, sl_path)
    #LOGGER.info('Symlink for symlink {} to {}'.format(link_path, sl_path))

def get_link_from_symlink(path):
    return os.readlink(path)

def is_symlink(path):
    if os.path.islink(path):
        return True
    return False

def get_disk_freespace(pathname):
    '''
    Get the free space of the filesystem containing pathname
    https://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file
    '''
    stat= os.statvfs(pathname)
    # use f_bfree for superuser, or f_bavail if filesystem
    # has reserved space for superuser
    return stat.f_bfree*stat.f_bsize


def link_deliverable(deliverable_bom, ws, variants_libtypes_specs=None, sd=None):
    SUSPECTED_BROKEN_LINK = []
    project = deliverable_bom['project']
    ip = deliverable_bom['variant']
    deliverable = deliverable_bom['libtype']
    bom = deliverable_bom['config']
    if variants_libtypes_specs is not None:
        proceed = populate_deliverable(ip, deliverable, variants_libtypes_specs)
    else:
        proceed = True


    if proceed:
        #if (bom.startswith('REL') or bom.startswith('snap')):
        if not is_mutable(bom):
            #deliverable_cache_dir = "%s/%s/%s/%s/%s" % (cache_dir, project, ip, deliverable, bom)
            deliverable_cache_dir = "{}".format(sd.is_pvcd_in_sion_disk(project, ip, deliverable, bom))

            if '*' in deliverable_cache_dir:
                LOGGER.error('{} contain asterik'.format(deliverable_cache_dir))
                #sys.exit(1)
            deliverable_ws_symlink = '%s/%s/%s' %  (ws, ip, deliverable)

            # Check if deliverable is populated in cache
            if not os.path.isdir(deliverable_cache_dir):
                LOGGER.error("Could not create workspace; %s was not populated to cache successfully." % bom)

            try :
                SUSPECTED_BROKEN_LINK = link_files(deliverable_cache_dir, deliverable_ws_symlink, [])
                LOGGER.info("Linking done: %s to %s" % (deliverable_ws_symlink, deliverable_cache_dir))
            except :
                LOGGER.error("Could not link workspace to cache; Could not create symbolic links at file level.")
        else:
            LOGGER.info("%s/%s:%s@%s is not an immutable configuration; Skipping symlinking ..." % (project, ip, deliverable, bom))
    else:
        LOGGER.info("%s/%s:%s@%s is filtered by .cfg file; Skipping symlinking ..." % (project, ip, deliverable, bom))

    return SUSPECTED_BROKEN_LINK

def auto_get_n_jobs_for_parallelism():
    n = old_div(multiprocessing.cpu_count(),2) - 4
    if n < 1:
        n = 1
    return 10
    #return n


def link_deliverable_boms(bom_list, ws, variants_libtypes_specs = None, n_jobs = None):
    SUSPECTED_BROKEN_LINK = []
    # Process list of simple configs
    if n_jobs is None:
        n_jobs = auto_get_n_jobs_for_parallelism()

    immutable_boms = [bom for bom in bom_list if not is_mutable(bom['config'])]
    filtered_immutable_boms = [bom for bom in immutable_boms if populate_deliverable(bom['variant'], bom['libtype'], variants_libtypes_specs)]
    sd = SionDisk()
    SUSPECTED_BROKEN_LINK = Parallel(n_jobs=n_jobs, backend="threading")(delayed(link_deliverable)(bom, ws, variants_libtypes_specs, sd) for bom in filtered_immutable_boms)

    return SUSPECTED_BROKEN_LINK

def report_broken_link(list_of_link):
    for link_list in list_of_link:
        for link in link_list:
            if not os.path.exists(link):
                LOGGER.warning('Broken Link: {}'.format(link))

def link_ws(ws, bom_list=None, linkfiles=True, project=None, ip=None, deliverable=None, bom=None, cfgfile=None):
    SUSPECTED_BROKEN_LINK = []
    # Create symbolic links to all deliverables@boms in cache_dir; If list is not provided, reuse .deliverables.configs that was already populated by workspace_helper.py
    if cfgfile is not None:
        variants_libtypes_specs = parse_cfgfile(project, ip, cfgfile)
    else:
        variants_libtypes_specs = None
    if bom_list:
        SUSPECTED_BROKEN_LINK = link_deliverable_boms(bom_list,  ws, variants_libtypes_specs)
    else:
        LOGGER.info("bom_list was not provided, attempting to get a list of simple configs ...")
        if (project is not None) and (ip is not None) and (bom is not None):
            bom_list = get_simple_boms(project=project, ip=ip, bom=bom, deliverable=deliverable)
            SUSPECTED_BROKEN_LINK = link_deliverable_boms(bom_list, ws, variants_libtypes_specs)
        else:
            LOGGER.error("Unable to get a list of simple configs. Project, ip and bom must be provided.")
            LOGGER.error("Could not link workspace.")

    return SUSPECTED_BROKEN_LINK

def generate_project_family_reference():
    reference_dict = {}
    e = dmx.ecolib.ecosphere.EcoSphere()
    families = e.get_families()
    for family in families:
        for project in family.get_icmprojects():
            reference_dict[project.name] = family.name
    #LOGGER.info(reference_dict)
    return reference_dict

def write_to_json(json_data, filename, filepath=None):
    if filepath is None or filepath=='':
        filepath = os.getcwd()
    if os.path.isdir(os.path.abspath(filepath)):
        # Give default filename if directory is provided instead of filepath
        filepath = os.path.join(os.path.abspath(filepath), filename)
    else:
        raise ValueError("ERROR: Provided file path does not exist or is not write-accessible.\nPlease provide an existing, write-accessible file path.")

    if not filepath.endswith('.json'):
        filepath = os.path.abspath("%s.json" % filepath)
    else:
        filepath = os.path.abspath(filepath)
    try:
        print("Writing data to %s ..." % filepath)
        with open(filepath, 'w') as f:
            json.dump(json_data, f, indent=4)
        print('Done')
    except:
        raise Exception("Could not write data to json file.")

''''''
def check_deliverable_cached(project, ip, deliverable, bom, reference_dict, default_parameters, cache_dir=None):
    family = reference_dict[project]
    default_cache_immutable_directory = default_parameters["PICE"]["immutable_directory"]["cache"][family]
    if cache_dir is None:
        cache_dir = default_cache_immutable_directory
    target_dir = "%s/%s/%s/%s/%s" % (cache_dir, project, ip, deliverable, bom)

    if os.path.isdir(target_dir):
        return True
    else:
        return False

def verify_deliverable(project, ip, deliverable, bom, reference_dict, default_parameters, full_check=False, cache_dir=None):
    family = reference_dict[project]
    default_cache_immutable_directory = default_parameters["PICE"]["immutable_directory"]["cache"][family]
    if cache_dir is None:
        cache_dir = default_cache_immutable_directory
    target_dir = "%s/%s/%s/%s/%s" % (cache_dir, project, ip, deliverable, bom)
    #base_dir = target_dir

    if deliverable in NON_STANDARD_LIBTYPES:
        clp_string = NON_STANDARD_LIBTYPES[deliverable].replace("$variant", ip)
        #target_dir = "%s/%s" % (target_dir, clp_string)

    populate_to_cache = False

    if os.path.isdir(target_dir):
        #LOGGER.info("Verifying existing %s ..." % target_dir)
        os.chdir(target_dir)
        if full_check:
            # Verify that every file in ICM exists in workspace
            # This will find partially populated directories
            cli = ICManageCLI()
            config = cli.get_simple_config_details(project, ip, deliverable, bom)
            o = cli.get_dict_of_files(project=project, variant=ip, libtype=deliverable, release=config['release'], library=config['library'])
            ICM_filenames = [f for f in o if ((not f.replace("%s/%s/%s:" % (project, ip, deliverable),"").startswith('.')) and ("delete" not in o[f]["operation"]))]
            if ICM_filenames != []:
                for filepath in ICM_filenames:
                    filepath = filepath.replace("%s:" % filepath.split(":")[0], "", 1)
                    filepath = filepath.replace("!23", "#")
                    filepath = filepath.replace("!40", "@")
                    filepath = filepath.replace("!25", "%")
                    filepath = filepath.replace("%23", "#")
                    filepath = filepath.replace("%40", "@")
                    filepath = filepath.replace("%25", "%")
                    #if not "!" in filepath:
                    #if os.path.islink(filepath):
                    #    LOGGER.error("Found symlink: %s; Symlinks cannot be cached ..." % filepath)
                    if deliverable in NON_STANDARD_LIBTYPES:
                        #golden_filepath = "%s/%s" % (golden_filepath, clp_string)
                        filepath = "%s/%s" % (clp_string, filepath)
                    cache_filepath = "%s/%s" % (target_dir, filepath)
                    #golden_filepath = "%s/%s/%s/%s" % (golden_ws_path, ip, deliverable, filepath)
                    if not os.path.exists(cache_filepath):
                            if os.path.islink(cache_filepath):
                                LOGGER.info("Found a symlink %s; Checked in symlinks are illegal." % cache_filepath)
                                cmd = "touch %s/symlinks/%s!!%s!!%s!!%s" % (cache_dir, ip, deliverable, bom, filepath.replace("/","!!"))
                                exitcode, stdout, stderr = run_command(cmd)
                                if exitcode:
                                    print_errors(cmd, exitcode, stdout, stderr)
                                #populate_to_cache = True
                            elif os.path.realpath(cache_filepath)!=cache_filepath:
                                LOGGER.info("Found a symlink %s; Checked in symlinks are illegal." % cache_filepath)
                                cmd = "touch %s/symlinks/%s!!%s!!%s!!%s" % (cache_dir, ip, deliverable, bom, filepath.replace("/","!!"))
                                exitcode, stdout, stderr = run_command(cmd)
                                if exitcode:
                                    print_errors(cmd, exitcode, stdout, stderr)
                                #populate_to_cache = True
                            else:
                                LOGGER.info("Found a missing file %s" % cache_filepath)
                                cmd = "touch %s/missing_files/%s!!%s!!%s!!%s" % (cache_dir, ip, deliverable, bom, filepath.replace("/","!!"))
                                exitcode, stdout, stderr = run_command(cmd)
                                if exitcode:
                                    print_errors(cmd, exitcode, stdout, stderr)
                                populate_to_cache = True
                                LOGGER.info("Populate %s/%s:%s@%s to cache: %s" % (project, ip, deliverable, bom, populate_to_cache))
                                return populate_to_cache
                            #return populate_to_cache #TODO: uncomment
                    elif not os.path.isfile(cache_filepath):
                        LOGGER.info("Found a missing file %s" % cache_filepath)
                        cmd = "touch %s/missing_files/%s!!%s!!%s!!%s" % (cache_dir, ip, deliverable, bom, filepath.replace("/","!!"))
                        exitcode, stdout, stderr = run_command(cmd)
                        if exitcode:
                            print_errors(cmd, exitcode, stdout, stderr)
                        populate_to_cache = True
                        LOGGER.info("Populate %s/%s:%s@%s to cache: %s" % (project, ip, deliverable, bom, populate_to_cache))
                        return populate_to_cache

                    '''
                    else:
                        cmd = "touch  %s/repairs/%s" % (cache_dir, filepath.replace("/","."))
                        exitcode, stdout, stderr = run_command(cmd)
                        if exitcode:
                            print_errors(cmd, exitcode, stdout, stderr)
                    '''
        else:
            # Verify that empty cached deliverables are meant to be empty
            # This will find any deliverables that failed to be populated at all
            filenames = [f for f in os.listdir(target_dir) if not f.startswith('.')]
            if filenames == []:
                LOGGER.info("Found empty cached deliverable at %s" % target_dir)
                #if not os.path.isfile("%s/.sion.empty" % target_dir):
                cli = ICManageCLI()
                config = cli.get_simple_config_details(project, ip, deliverable, bom)
                o = cli.get_dict_of_files(project=project, variant=ip, libtype=deliverable, release=config['release'], library=config['library'])
                ICM_filenames = [f for f in o if ((not f.replace("%s/%s/%s:" % (project, ip, deliverable),"").startswith('.')) and ("delete" not in o[f]["operation"]))]

                if ICM_filenames != []:
                    LOGGER.info("Cached deliverable directory %s must not be empty. Re-cache required ..." % target_dir)
                    cmd = "touch /nfs/site/disks/fln_sion_1/cache/repairs/%s.%s.%s.%s" % (project, ip, deliverable, bom)
                    exitcode, stdout, stderr = run_command(cmd)
                    if exitcode:
                        print_errors(cmd, exitcode, stdout, stderr)
                    '''
                    try:
                        LOGGER.info("Removing empty cached deliverable at %s" % target_dir)
                        shutil.rmtree(target_dir)
                    except:
                        LOGGER.error("Could not remove empty cached deliverable at %s" % target_dir)
                    '''
                    populate_to_cache = True
                else:
                    cmd = "touch %s/.sion.empty" % target_dir
                    exitcode, stdout, stderr = run_command(cmd)
                    if exitcode:
                        print_errors(cmd, exitcode, stdout, stderr)
    else:
        LOGGER.info("Could not find %s ..." % target_dir)
        populate_to_cache = True
        LOGGER.info("Populate %s/%s:%s@%s to cache: %s" % (project, ip, deliverable, bom, populate_to_cache))
        return populate_to_cache
    if populate_to_cache:
        LOGGER.info("Populate %s/%s:%s@%s to cache: %s" % (project, ip, deliverable, bom, populate_to_cache))
    return populate_to_cache


def process_boms(deliverable_boms, cache_dir, user, n_jobs = None):
    if n_jobs is None:
        n_jobs = auto_get_n_jobs_for_parallelism()
        #n_jobs = 1
    results = CacheResults()
    try:
        # Failsafe to make sure EcoSphere does not error out
        os.chdir("/nfs/site/disks/fln_sion_1/cache")
    except:
        LOGGER.info("Could not chdir to base cache")
    #reference_dict = generate_project_family_reference()

    sd = SionDisk()
    Parallel(n_jobs=n_jobs, backend="threading")(delayed(process_bom)(bom, results, user, cache_dir, sd=sd) for bom in deliverable_boms)
    return results


def pre_process_boms(deliverable_boms, cache_dir, user, variants_libtypes_specs = None, n_jobs = None):
    if n_jobs is None:
        n_jobs = auto_get_n_jobs_for_parallelism()

    results = CacheResults()
    try:
        # Failsafe to make sure EcoSphere does not error out
        os.chdir("/nfs/site/disks/fln_sion_1/cache")
    except:
        LOGGER.info("Could not chdir to base cache")


    # Ignored mutable bom because it will not sync cache
    # Ignore checking on filtered ip/deliverable to speed up the cache
    #    if bom['type'] == 'config':
    immutable_boms = [bom for bom in deliverable_boms if not is_mutable(bom['config'])]
    filtered_immutable_boms = immutable_boms
    mutable_boms = [bom for bom in deliverable_boms if is_mutable(bom['config'])]

    for bom in mutable_boms:
        if bom not in results.mutable_boms:
            results.mutable_boms.append(bom)
    sd = SionDisk()
    LOGGER.info('Number of parallel job: {}'.format(n_jobs))
    Parallel(n_jobs=n_jobs, backend="threading")(delayed(pre_process_bom)(bom, results, user, variants_libtypes_specs, sd=sd) for bom in filtered_immutable_boms)
    return results

def populate_deliverable(ip, deliverable, variants_libtypes_specs):
    #LOGGER.info(variants_libtypes_specs)
    for variants, libtypes, specs in variants_libtypes_specs:
        if (('*' in variants) or ('all' in variants) or (ip in variants)) and (('*' in libtypes) or ('all' in libtypes) or (deliverable in libtypes)):
            return True
    return False


def pre_process_bom(deliverable_bom, results, user, variants_libtypes_specs = None, full_check = False, sd=None):

    # Get all needed bom parameters
    project = deliverable_bom['project']
    ip = deliverable_bom['variant']
    deliverable = deliverable_bom['libtype']
    bom = deliverable_bom['config']
    LOGGER.info("Pre-processing %s/%s:%s@%s ..." % (project, ip, deliverable, bom))

    if is_mutable(bom):
        # Log and skip mutable deliverable boms
        if deliverable_bom not in results.mutable_boms:
            results.mutable_boms.append(deliverable_bom)
        LOGGER.info("Cannot cache a mutable deliverable configuration %s for %s/%s:%s\nThis deliverable will be synced to a workspace." % (bom, project, ip, deliverable));
    else:
        if variants_libtypes_specs is not None:
            proceed = populate_deliverable(ip, deliverable, variants_libtypes_specs)
        else:
            proceed = True
        if proceed is False:
            LOGGER.info("%s/%s:%s@%s is filtered by .cfg file; Skipping caching ..." % (project, ip, deliverable, bom))
        else:
            if deliverable_bom not in results.immutable_boms:
                results.immutable_boms.append(deliverable_bom)

            target_dir = "%s/%s/%s/%s" % (project, ip, deliverable, bom)
            LOGGER.info("verifying existence of %s ..." % target_dir)
            deliverable_in_cache = sd.is_pvcd_in_sion_disk(project, ip, deliverable, bom)

            if deliverable_in_cache:
                LOGGER.info("%s/%s:%s@%s is already populated in SION cache." % (project, ip, deliverable, bom))
                results.boms_for_print+="%s/%s:%s@%s\n"  % (project, ip, deliverable, bom)
            else:
                LOGGER.info("%s/%s:%s@%s needs to be populated to SION cache. Adding to list ..." % (project, ip, deliverable, bom))
                results.deferred_boms.append(deliverable_bom);


def process_bom(deliverable_bom, results, user, cache_dir=None, full_check=True, sd=None):

    # Get all needed bom parameters
    project = deliverable_bom['project']
    ip = deliverable_bom['variant']
    deliverable = deliverable_bom['libtype']
    bom = deliverable_bom['config']
    LOGGER.info("Processing %s/%s:%s@%s ..." % (project, ip, deliverable, bom))

    if cache_dir is None:
        cache_dir = sd.largest_disk.get(project)
        LOGGER.info("Checking %s ..." % cache_dir)
    try:
        os.chdir(cache_dir)
    except:
        LOGGER.error("Could not chdir to cache_dir %s" % cache_dir)

    if is_mutable(bom):
        # Log and skip mutable deliverable boms
        if deliverable_bom not in results.mutable_boms:
            results.mutable_boms.append(deliverable_bom)
        LOGGER.info("Cannot cache a mutable deliverable configuration %s for %s/%s:%s\nThis deliverable will be synced to a workspace." % (bom, project, ip, deliverable));
    else:
        if deliverable_bom not in results.immutable_boms:
            results.immutable_boms.append(deliverable_bom)
        # Get project-specific centralized paths

        # Check project permissions
        #run_pre_populate_checks(project, ip, deliverable, bom, user)

        # Set root, temporary, and final cache paths for this deliverable@bom
        (year, ww, day) = get_ww_details()
        now = datetime.datetime.now()
        date_string = "{0}ww{1}{2}_t{3}-{4}-{5}".format(year, ww, day, now.hour, now.minute, now.second)

        target_dir = "%s/%s/%s/%s" % (cache_dir, ip, deliverable, bom)
        temp_directory = "%s.TEMP%s__%s" % (target_dir, os.environ['ARC_JOB_ID'], date_string)
        deliverable_default_cache_dir = "%s/%s/%s/" % (temp_directory, ip, deliverable)

        populate_to_cache = True
        if populate_to_cache:
            # This deliverable@bom is not yet populated to cache; Populate ...
            arc_id = os.environ.get('ARC_JOB_ID')
            lockdir = "%s/.locks" % cache_dir
            try:
                if not os.path.exists(lockdir):
                    os.mkdir(lockdir)
            except:
                LOGGER.error("{} already exists.".format(lockdir))

            lockfile = "%s/%s.%s.%s.%s" % (lockdir, project, ip, deliverable, bom)
            # Check is this deliverable@bom is locked by another populate process
            if os.path.exists(lockfile):
                LOGGER.info("%s/%s:%s@%s is being populated at the moment (%s). Adding to deferred queue ..." % (project, ip, deliverable, bom, lockfile))
                # Append deliverable@bom to deferred queue
                results.deferred_boms.append(deliverable_bom)
            else:
                # Review ordering below
                with open(lockfile, 'a') as f:
                    f.write(arc_id)

                #open(lockfile, 'a').close()
                LOGGER.info("Locking %s/%s:%s@%s ..." % (project,ip,deliverable,bom))
                # Clean up the deliverable@bom ws directory
                if os.path.exists(target_dir):
                    try:
                        shutil.rmtree(target_dir)
                    except:
                        LOGGER.info("Could not clean up %s prior to populate" % target_dir)
                        pass
                # Clean up the temp deliverable@bom ws directory
                if os.path.exists(temp_directory):
                    try:
                        shutil.rmtree(temp_directory)
                    except:
                        LOGGER.info("Could not clean up %s prior to populate" % temp_directory)
                        pass
                try:
              #  if True:
                    LOGGER.info("Clear to populate %s/%s:%s@%s to %s ..." % (project, ip, deliverable, bom, temp_directory))
                    new_ws = create_workspace(project, ip, deliverable, bom, temp_directory, wsname=None, skeleton=False, saveworkspace=False)
                    results.synced_boms_for_print+="%s/%s:%s@%s\n"  % (project, ip, deliverable, bom)
    
                    os.rename(deliverable_default_cache_dir, target_dir)
                    LOGGER.info("Write-protecting cached deliverable")
                    cmd = "chmod -R 750 %s" % target_dir
                    exitcode, stdout, stderr = run_command(cmd)
                    if exitcode:
                        print_errors(cmd, exitcode, stdout, stderr)
    
                    # Remove the lock file for successfully populated deliverable@bom
                    if os.path.exists(lockfile):
                        try:
                            os.remove(lockfile)
                        except:
                            LOGGER.error("Could not remove lockfile %s for successful population to cache" % lockfile)
    
                    # Record deliverable@bom dir size in cache
                    storage_path = "%s/.storage" % cache_dir
                    record_workspace_size(target_dir, storage_path)
    
                    # Add successfully populated deliverable@bom tmp dir to removal list
                    LOGGER.info("Adding %s for cleanup ..." % temp_directory)
                    results.synced_boms.append(str(temp_directory))
                    #shutil.rmtree(temp_directory)
    
                        #Verify that deliverable was correctly populated - TODO add a switch
                    '''
                        populate_defect = verify_deliverable(project, ip, deliverable, bom, reference_dict, default_parameters, True, cache_dir)
                        if populate_defect:
                            LOGGER.error("Deliverable cache directory was not populated correctly: %s\nAdding to failed list ..." % target_dir)
                            if not deliverable_bom in results.failed_boms:
                                results.failed_boms.append(deliverable_bom)
                            # Still add to list for print for partial symlinking
                            results.boms_for_print+="%s/%s:%s@%s\n"  % (project, ip, deliverable, bom)
                            results.synced_boms.append(str(temp_directory))
                        else:
                            # Record deliverable@bom dir size in cache
                            storage_path = "%s/.storage" % cache_dir
                            record_workspace_size(target_dir, storage_path)
    
                            # Add successfully populated deliverable@bom tmp dir to removal list
                            LOGGER.info("Adding %s for cleanup ..." % temp_directory)
                            results.synced_boms.append(str(temp_directory))
                            #shutil.rmtree(temp_directory)
    
                            results.boms_for_print+="%s/%s:%s@%s\n"  % (project, ip, deliverable, bom)
                    '''
                    #try:
                    #LOGGER.info("here")
                except Exception as e:
                    LOGGER.error(e)
                    LOGGER.error("%s/%s:%s@%s population FAILED. Adding to failed boms list ..." % (project, ip, deliverable, bom))
                    # Remove the lock file if deliverable@bom population fails
                    if os.path.exists(lockfile):
                        try:
                            os.remove(lockfile)
                        except:
                            LOGGER.error("Could not remove lockfile %s for failed population to cache" % lockfile)
                    # Clean up the temp deliverable@bom ws directory
                    if os.path.exists(temp_directory):
                        try:
                            shutil.rmtree(temp_directory)
                        except:
                            LOGGER.error("Could not clean up %s for failed population to cache" % temp_directory)
                            pass
                    # Append deliverable@bom to failed boms array
                    if not deliverable_bom in results.failed_boms:
                        results.failed_boms.append(deliverable_bom)
                    '''
                    LOGGER.error("Deliverable cache directory was not populated: %s" % deliverable_default_cache_dir)
                    LOGGER.error(e)
                    results.failed_boms.append(deliverable_bom)
                    if os.path.exists(lockfile):
                        # Remove the lock file for deliverable@bom
                        LOGGER.error("Cleaning up lockfile %s ..." % lockfile)
                        try:
                            os.remove(lockfile)
                        except:
                            LOGGER.error("Could not remove lockfile %s for failed population to cache" % lockfile)
                    if os.path.exists(temp_directory):
                        try:
                            shutil.rmtree(temp_directory)
                        except:
                            LOGGER.error("Could not clean up %s for failed population to cache" % temp_directory)
                            pass
                    '''
               #try: 
                new_ws.delete()
                cli = ICManageCLI()
                configName = '__forwscreation__{}__{}'.format(deliverable, os.environ['ARC_JOB_ID'])
                LOGGER.info('{}'.format(configName))
                cli.del_libtype_config(project, ip, deliverable, configName) 
               # except Exception as e:
               #     LOGGER.info(e)
               #     LOGGER.info("Could not delete worskpace client for %s" % temp_directory)
                
        else :
            LOGGER.info("%s/%s:%s@%s is already populated in SION cache." % (project, ip, deliverable, bom))
            results.boms_for_print+="%s/%s:%s@%s\n"  % (project, ip, deliverable, bom)

''''''


def touch_sion_dir(sion_dir):
    cmd = "touch %s/.sion" % sion_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    # ensure user cannot remove .sion file (needed for sion delete to work properly)
    cmd = "chmod 750 %s/.sion" % sion_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
      print_errors(cmd, exitcode, stdout, stderr)

def touch_sion_dirs(sion_dirs, n_jobs = None):
    if n_jobs is None:
        n_jobs = auto_get_n_jobs_for_parallelism()
        #n_jobs = 1
    Parallel(n_jobs=n_jobs, backend="threading")(delayed(touch_sion_dir)(sion_dir) for sion_dir in sion_dirs)

''''''

def sync_ws(ip, ws):
    ws.sync(variants=[ip], skeleton=False)
    LOGGER.info('{} populated' .format(ip))

def sync_ws_parallel(ips, ws, n_jobs = None):
    if n_jobs is None:
        n_jobs = auto_get_n_jobs_for_parallelism()
    Parallel(n_jobs=n_jobs, backend="threading")(delayed(sync_ws)(ip, ws) for ip in ips)

@ft.lru_cache(maxsize = 128)
def get_default_parameters(pvc=None):
    ## classic is no longer used, deprecreated


    default_parameters = {
        "PICE": {
            "prot_group": "psgeng",
            "immutable_directory": {
                "standard": {
                    "Falcon": "/nfs/site/disks/fln_sion_*/classic",
                    "Nadderp": "/nfs/site/disks/nd_sion_*/classic",
                    "_Testdata": "/nfs/site/disks/fln_sion_*/classic",
                    "Diamondmesa": "/nfs/site/disks/dmd_sion_*/classic",
                    "Wharfrock": "/nfs/site/disks/whr_sion_*/classic",
                    "Gundersonrock": "/nfs/site/disks/gdr_sion_*/classic",
                    "Reynoldsrock": "/nfs/site/disks/rnr_sion_*/classic"
                }
            },
            "immutable_disk": {
                "standard": {
                    "Falcon": "/nfs/site/disks/fln_sion_*/classic",
                    "_Testdata": "/nfs/site/disks/fln_sion_*/classic",
                    "Diamondmesa": "/nfs/site/disks/dmd_sion_*/classic",
                    "Wharfrock": "/nfs/site/disks/whr_sion_*/classic",
                    "Gundersonrock": "/nfs/site/disks/gdr_sion_*/classic",
                    "Reynoldsrock": "/nfs/site/disks/rnr_sion_*/classic"
                }
            },
            "central_cache_ws_directory": {
                "Falcon": "/nfs/site/disks/fln_sion_1/cache_workspaces",
                "Nadderp": "/nfs/site/disks/nd_sion_1/cache_workspaces",
                "_Testdata": "/nfs/site/disks/fln_sion_1/cache_workspaces",
                "Diamondmesa": "/nfs/site/disks/dmd_sion_1/cache_workspaces",
                "Wharfrock": "/nfs/site/disks/whr_sion_1/cache_workspaces",
                "Gundersonrock": "/nfs/site/disks/gdr_sion_1/cache_workspaces",
                "Reynoldsrock": "/nfs/site/disks/rnr_sion_1/cache_workspaces",
            },
            "icm_groups" : {
                         "all.users" : "psgeng",
                         "i10.users" : "psgi10",
                         "t16ff.users" : "t16ffc",
                         "psgi10arm.users" : "psgi10arm",
                         "fln.users" : "psgfln",
                         "psgship.users"  : "psgship",
                         "nd.users"  : "psgnd",
                         "whr.users" : "psgwhr",
                         "gdr.users"  :"psggdr",
                         "rnr.users"  :"psgrnr"
                    },
            "headless_account": "psginfraadm"
        },
        "legacy": {
            "prot_group": "eng",
            "immutable_disk": "/ice_rel",
            "immutable_directory": "/ice_rel/readonly",
            "icm_groups" : {
                        "runda.users":"nd",
                        "tsmc.users" :"tsmc",
                        "soci.users" :"soci",
                        "hhp.users"  :"hhp",
                        "all.users"  :"eng",
                        "thasos.users":"thasos",
                        "fln.users"  :"fln",
                        "i10.users"  :"i10"
                    },
            "headless_account": "icmrelreader"
        }
    }

    return default_parameters


def split_pvc(pvc):
    '''Project/variant:libtype@config'''
    match = re.search('(\S+)/(\S+):(\S+)@(\S+)', pvc)
    if not match:
        raise('Not in expected format. Expected format: project/variant:deliverable@bom')
    proj = match.group(1)
    ip = match.group(2)
    deliverable = match.group(3)
    bom = match.group(4)

    return proj, ip, deliverable, bom


def run_pre_populate_checks(project, ip, deliverable, bom, user) :
    #icm_groups = get_icm_groups()
    #check if p/v/c exist or p/v/c/l exist
    if deliverable == 'None':
        cmd = 'pm configuration -l %s %s -n %s' % (project, ip, bom)
    else:
        cmd = 'pm configuration -l %s %s -n %s -t %s' % (project, ip, bom, deliverable)
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        if deliverable == 'None':
            LOGGER.error("%s/%s/%s does not exist" % (project, ip, bom))
            LOGGER.error("Please ensure that you have keyed in the right project, ip and configuration")
            sys.exit(1)
        else:
            LOGGER.error("%s/%s/%s/%s does not exist" % (project, ip, deliverable, bom))
            LOGGER.error("Please ensure that you have key in the right project, ip, deliverable and configuration")
            sys.exit(1)
        sys.exit(1)


def server_side_sync_cfg(target_dir, cfg):
    try:
        #Temporary disbale this
        #if cfg.is_simple() and not cfg.is_mutable():
        if not cfg.is_config() and not cfg.is_mutable():
            LOGGER.info("Locking immutable config for %s/%s" % (cfg.variant, cfg.libtype))
            os.chdir(target_dir)
            command = 'xlp4 sync -k {}/{}/{}/...'.format(target_dir, cfg.variant, cfg.libtype)
            LOGGER.debug(command)
            exitcode, stdout, stderr = run_command(command)
            #LOGGER.info("command done")
            if exitcode:
                LOGGER.info(str(exitcode))
                LOGGER.info('Error running {}'.format(command))
    except Exception as e:
        LOGGER.error(e)

def server_side_sync_cfgs(target_dir, project, ip, bom, n_jobs=None):
    cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, ip, bom)
    cfgs = cfobj.flatten_tree()
    #LOGGER.info("CONFIGS: %s" % cfgs)
    if n_jobs is None:
        n_jobs = auto_get_n_jobs_for_parallelism()
        #n_jobs = 1
    Parallel(n_jobs=n_jobs, backend="threading")(delayed(server_side_sync_cfg)(target_dir, cfg) for cfg in cfgs)

def create_workspace(project, ip, deliverable, bom, target_dir, wsname=None, skeleton=False, saveworkspace = True, boms_to_sync = None, cfgfile= None):
    LOGGER.info("Creating workspace...")
    desc = "SITE: {} ARC_JOB: {}".format(os.environ['ARC_SITE'], os.environ['ARC_JOB_ID'])
    target_dir = os.path.realpath(target_dir)

    if wsname:
        target_dir = "%s/%s" % (target_dir,wsname)

    if os.path.isdir(target_dir):
        try:
            shutil.rmtree(target_dir)
        except:
            LOGGER.info("Could not remove existing directory %s prior to re-populate" % target_dir)

    # Create workspace target directory
    if not os.path.isdir(target_dir):
        try:
            os.makedirs(target_dir)
        except Exception as e:
            LOGGER.error(e)
            LOGGER.error("Could not create ws target directory %s" % target_dir)
            #sys.exit(1)
    else:
        cmd = "chmod -R 777 %s" % target_dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)



    # Set logging to file after workspace target directory is created as logfile needs to live in workspace root
    set_sion_logging(LOGGER, target_dir)

    # Create workspace
    if (deliverable=='None') or (deliverable is None):
        LOGGER.info("Syncing IP level workspace %s ..." % target_dir)
        try:
            new_ws = dmx.dmxlib.workspace.Workspace(workspacepath=target_dir, project=project, ip=ip, bom=bom, preview=False)
            new_ws.create(ignore_clientname=True)
            clientname = str(new_ws.get_workspace_attributes()['Workspace'])
            # Create a .sion file in each directory so that sion knows this directory is created via populate command
            dirs = [x[0] for x in os.walk(target_dir)]
            touch_sion_dirs(dirs)
            if skeleton==False:
                #os.chdir(clientname)
                ips = new_ws.get_ips()
                try:
                    LOGGER.info("Populating workspace...")
                    os.chdir(target_dir)
                    new_ws.sync()
                    #sync_ws_parallel(ips, new_ws)
                except:
                    LOGGER.error("Could not populate workspace at %s" % target_dir)
                    try:
                        shutil.rmtree(target_dir)
                    except:
                        LOGGER.info("Could not remove %s" % target_dir)
            if boms_to_sync is not None:
                if len(boms_to_sync)>0:
                    os.chdir(target_dir)
                    LOGGER.info("Running server side sync for immutable libraries ...")
                    server_side_sync_cfgs(target_dir, project, ip, bom, 1)
                    '''
                    LOGGER.info("Syncing additional specified deliverables ...")
                    for deliverable_bom in boms_to_sync:
                        deliverable_bom_project = deliverable_bom['project']
                        deliverable_bom_ip = deliverable_bom['variant']
                        deliverable_bom_deliverable = deliverable_bom['libtype']
                        deliverable_bom_bom = deliverable_bom['config']
                        print("Syncing %s/%s:%s@%s to user workspace ..." % (deliverable_bom_project, deliverable_bom_ip, deliverable_bom_deliverable, deliverable_bom_bom))
                        try:
                            new_ws.sync(variants=[deliverable_bom_ip], libtypes=[deliverable_bom_deliverable])
                        except:
                            LOGGER.error("Could not sync %s/%s:%s@%s to user workspace %s" % (deliverable_bom_project, deliverable_bom_ip, deliverable_bom_deliverable, deliverable_bom_bom, target_dir))
                    '''
                    LOGGER.info("Syncing mutable configurations ...")
                    if not cfgfile:
                        cfgfile = ''
                    new_ws.sync(cfgfile=cfgfile)

            LOGGER.info("Workspace created: %s..." % target_dir)
        except:
            LOGGER.error("Could not create workspace at %s" % target_dir)
            try:
                shutil.rmtree(target_dir)
            except:
                LOGGER.error("Could not remove workspace at %s\nPlease run 'sion delete -d %s'" % (target_dir, target_dir))
    else:
        LOGGER.info("Syncing deliverable level workspace %s ..." % target_dir)
        new_ws = dmx.dmxlib.workspace.Workspace(workspacepath=target_dir, project=project, ip=ip, bom=bom, deliverable=deliverable, preview=False)
        new_ws.create(ignore_clientname=True)
        clientname = str(new_ws.get_workspace_attributes()['Workspace'])
        # Create a .sion file in each directory so that sion knows this directory is created via populate command
        dirs = [x[0] for x in os.walk(target_dir)]
        touch_sion_dirs(dirs)
        if skeleton==False:
            #os.chdir(clientname)
            try:
                LOGGER.info("Populating workspace...")
                # os.chdir is not thread safe, need to improve this code
                exitcode, stdout, stderr = run_command('cd {}'.format(target_dir))
                #os.chdir(target_dir)
                new_ws.sync()
                LOGGER.info("Workspace created: %s ..." % target_dir)
            except:
                LOGGER.error("Could not populate workspace at %s" % target_dir)
                try:
                    shutil.rmtree(target_dir)
                except:
                    LOGGER.info("Could not remove %s" % target_dir)
 
        '''
        try:
            new_ws = dmx.dmxlib.workspace.Workspace(workspacepath=target_dir, project=project, ip=ip, bom=bom, deliverable=deliverable, preview=False)
            new_ws.create(ignore_clientname=True)
            clientname = str(new_ws.get_workspace_attributes()['Workspace'])
            # Create a .sion file in each directory so that sion knows this directory is created via populate command
            dirs = [x[0] for x in os.walk(target_dir)]
            touch_sion_dirs(dirs)
            if skeleton==False:
                #os.chdir(clientname)
                try:
                    LOGGER.info("Populating workspace...")
                    os.chdir(target_dir)
                    new_ws.sync()
                    LOGGER.info("Workspace created: %s ..." % target_dir)
                except:
                    LOGGER.error("Could not populate workspace at %s" % target_dir)
                    try:
                        shutil.rmtree(target_dir)
                    except:
                        LOGGER.info("Could not remove %s" % target_dir)
        except Exception as e:
            LOGGER.debug(str(e))
            LOGGER.error("Could not create workspace at %s" % target_dir)
            try:
                shutil.rmtree(target_dir)
            except:
                LOGGER.error("Could not remove workspace at %s\nPlease run 'sion delete -d %s'" % (target_dir, target_dir))
        '''
    # Set permissions for populated workspace
  #  if default_ws_immutable_directory_realpath in target_dir:
  #      cmd = "chmod -R 750 %s" % target_dir
  #  elif default_cache_immutable_directory_realpath in target_dir:
  #      cmd = "chmod -R 750 %s" % target_dir
  #  else:
    cmd = "chmod -R 770 %s" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)

    if saveworkspace :
        # Run saveworkspace
        LOGGER.info("Running saveworkspace...")
        try:
            cmd = "saveworkspace --workspace %s" % target_dir
            exitcode, stdout, stderr = run_command(cmd)
            if deliverable == 'None':
                cmd = "saveworkspace --workspace %s --every" % target_dir
                exitcode, stdout, stderr = run_command(cmd)
        except Exception as e:
            LOGGER.debug(e)
            pass
    return new_ws

def set_sion_logging(LOGGER, target_dir):
    '''
    LOGGER.handlers=[]
    logfile = '{}/.sion.log'.format(target_dir)
    logging.basicConfig(filename=logfile,
                        filemode='w',
                        format='-%(levelname)s-[%(module)s]: %(message)s',
                        level=logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('-%(levelname)s-[%(module)s]: %(message)s')
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)
    '''
    logfile = '{}/.sion.log'.format(target_dir)
    fh = logging.FileHandler(logfile, mode='w')
    #formatter = logging.Formatter("%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s")
    formatter = logging.Formatter("%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s")
    fh.setFormatter(formatter)
    LOGGER.addHandler(fh)


def record_workspace_size(target_dir, storage_path):
    '''
    Record workspace content sizes for analysis
    '''
    cmd = "du -sh %s" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    storage_file = open(storage_path, 'a')
    storage_file.write(stdout)
    #storage_file.close()

def print_deliverable_boms(bom_list):
    for deliverable_bom in bom_list:
        project = deliverable_bom['project']
        ip = deliverable_bom['variant']
        deliverable = deliverable_bom['libtype']
        bom = deliverable_bom['config']
        LOGGER.info("%s/%s:%s@%s" % (project, ip, deliverable, bom))

def parse_cfgfile(project, ip, cfgfile):
    LOGGER.info("Processing config file ...")
    variants=['all']
    libtypes=['all']
    specs=[]
    variants_libtypes_specs = []
    if os.path.isfile(cfgfile):
        config = read_sync_config_file(cfgfile)
        for section in config.sections():
            variants = []
            libtypes = []
            specs = []
            if config.has_option(section, 'specs'):
                variants=['all']
                libtypes=['all']
                specs = []
                variants_libtypes_specs.append((variants, libtypes, specs))
            else:
                variants = config.get(section, 'variants').split()
                elements = config.get(section, 'libtypes').split()
                #LOGGER.info(".cfg variants: %s" % variants)
                #LOGGER.info(".cfg libtypes: %s" % elements)

                if '*' in variants or 'all' in variants or not variants:
                    # if *, get all ips in workspace
                    variants = ['all']

                for variant in variants:
                    if project:
                        family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
                        if not elements:
                            libtypes = ['all']
                        else:
                            libtypes = []
                        for element in elements:
                            if element.startswith('view'):
                                # Expand view into libtypes
                                libtypes = libtypes + [x.deliverable for x in family.get_view(element).get_deliverables()]
                            else:
                                libtypes.append(element)
                        libtypes = sorted(list(set(libtypes)))
                        variants_libtypes_specs.append(([variant], libtypes, specs))
    else:
        LOGGER.error("Could not find provided .cfg file %s\nPopulating all ips and deliverables ..." % cfgfile)
        variants_libtypes_specs.append((variants, libtypes, specs))
    #LOGGER.info("variants_libtypes_specs: \n{}".format(variants_libtypes_specs))
    return variants_libtypes_specs

def populate_cache_by_deliverable(project, ip, bom, cache_dir, user, deliverable=None, cfgfile=None) :
    if cfgfile is not None:
        variants_libtypes_specs = parse_cfgfile(project, ip, cfgfile)
    else:
        variants_libtypes_specs = None

    if cache_dir is not None:
        if cache_dir.endswith('/'):
            cache_dir = cache_dir[:-1]

        # Check if psginfraadm is able to write into the user directory
        if not os.access(cache_dir, os.W_OK | os.X_OK):
            LOGGER.error('%s is not writable by sion. Please chmod the directory to 777.' % cache_dir)
            sys.exit(1)

    # Generate a list of all needed deliverables boms
    try:
        LOGGER.info("Getting simple configurations for %s/%s@%s" %(project, ip, bom))
        #reference_dict = generate_project_family_reference()
        #LOGGER.info("reference_dict: {}".format(reference_dict))
        deliverable_boms = get_simple_boms(project=project, ip=ip, bom=bom, deliverable=deliverable)
    except:
        LOGGER.error("Could not decompose configuration. Please ensure that the configuration exists and the project, ip (and optionally deliverable) parameters were supplied correctly.")
        raise
        sys.exit(1)

    #Pre-process deliverable boms
    LOGGER.info("Pre-processing deliverable boms ...")
    results = pre_process_boms(deliverable_boms, cache_dir, user, variants_libtypes_specs)

    # Store results
    final_results = results

    # Populate cache from the list of all needed deliverables boms
    #LOGGER.info("Populating cache directory %s by deliverable ..." % cache_dir)
    #results = process_boms(deliverable_boms, cache_dir, user)

    # Store results
    #final_results = results

    # Check back on deferred items
    if len(results.deferred_boms)>0:
        # Populate cache from the list of all needed deliverables boms
        LOGGER.info("Populating cache directory %s by deliverable ..." % cache_dir)
        all_boms_processed = False
        while not all_boms_processed:
            LOGGER.info("Re-processing ...")
            results = process_boms(results.deferred_boms, cache_dir, user)
            # Re-set deferred_boms
            final_results.deferred_boms = []
            final_results.append(results)
            if not results.deferred_boms:
                all_boms_processed = True
            else:
                time.sleep(30)

    # Return a list of synced and all needed deliverables boms
    LOGGER.info("DONE populating cache ...")
    '''
    if len(final_results.failed_boms)>0:
        # Attempt to populate failed boms
        LOGGER.info("Attempting to populate failed deliverables %s ..." % final_results.failed_boms)
        results = process_boms(final_results.failed_boms, cache_dir, user)
        # Re-set failed_boms
        final_results.failed_boms = []
        # Check back on deferred items
        if len(results.deferred_boms)>0:
            all_boms_processed = False
            while not all_boms_processed:
                print("Re-processing ...")
                results = process_boms(results.deferred_boms, cache_dir, user)
                # Re-set deferred_boms
                final_results.deferred_boms = []
                final_results.append(results)
                if not results.deferred_boms:
                    all_boms_processed = True
                else:
                    time.sleep(30)
    '''

    # Clean up temporary directories
    #LOGGER.info("Deleting temporary directories ...")
    if len(final_results.synced_boms)>0:
        for temp_dir in final_results.synced_boms:
            LOGGER.info("Cleaning up %s ..." % temp_dir)
            try:
                shutil.rmtree(temp_dir)
            except:
                cmd = "rm -rf %s" % temp_dir
                exitcode, stdout, stderr = run_command(cmd)
                #if exitcode:
                #    print_errors_pass(cmd, exitcode, stdout, stderr)
                pass

    if len(final_results.failed_boms)>0:
        # Error out if there are still failed boms in final_results
        LOGGER.info("The following deliverables were NOT successfully populated to cache:")
        print_deliverable_boms(final_results.failed_boms)
        LOGGER.error("Could not cache all deliverables successfully. Please review the list above.")
        # Set root, temporary, and final cache paths for this deliverable@bom
    if len(missing_files)>0:
        (year, ww, day) = get_ww_details()
        now = datetime.datetime.now()
        date_string = "{0}ww{1}{2}_t{3}-{4}-{5}".format(year, ww, day, now.hour, now.minute, now.second)
        missing_files_filepath = "/nfs/site/disks/psg_sion_1/%s.%s.%s.%s.%s.txt" % (project, ip, deliverable, bom, date_string)
        with open(missing_files_filepath, 'w') as f:
            for missing_file in missing_files:
                f.write("%s\n" % missing_file)
        f.close()
        #sys.exit(1)

    return final_results


def is_mutable(cfginstr):
    '''
    Returns True if the configuration is mutable.
    Otherwise returns False.
    '''
    if cfginstr.startswith(('REL', 'snap-', 'PREL')):
        return False
    else:
        return True

