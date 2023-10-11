#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/utils.py#3 $
$Change: 7511149 $
$DateTime: 2023/03/06 02:01:28 $
$Author: lionelta $

Description: Utility functions that are common across ABNR but generic
enough that they don't fit in elsewhere

Author: Lee Cartwright

Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import str

import socket
import getpass
import os
import sys
import pwd
import time
import re
import threading
import subprocess
import argparse
import datetime as utildt
from contextlib import contextmanager
#from altera.decorators import memoized
import dmx.utillib.intel_dates
import dmx.utillib.admin
import logging
import json
import tempfile
import signal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import smtplib

### in-house libraries for send_email function
#from altera.email import AlteraEmailer
#from django.template import Context
#from django.utils.safestring import mark_safe

LOGGER = logging.getLogger(__name__)
#LOGGER = logging.getLogger()
ID_MAP = '/p/psg/da/infra/config/PSG_INTL_Login_Mapping.csv'

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.errorlib.exceptions import *
from dmx.utillib.decorators import memoized

ICMADMIN = 'icmanage'

def get_workspace_disk():
    '''
    Get the DMX_WORKSPACE environemnt variable
    '''
    ret = os.getenv("DMX_WORKSPACE")
    if not ret:
        raise DmxErrorICWS02("$DMX_WORKSPACE not defined. All 'dmx workspace' commands need this environment variable to be defined. This env var should store the full path to the disk area of where your workspace should-be/have-been created.")
    return ret

def get_abnr_id():
    '''
    Generates an id that is unique across all abnr instances.
    This consists of host, user, pid and timestamp

    :return: Unique id for this abnr run
    :rtype: str
    '''
    host = socket.gethostname()
    user = getpass.getuser()
    pid = os.getpid()
    timestamp = int(time.time())

    return '{0}_{1}_{2}_{3}'.format(host, user, pid, timestamp)

def minmaxsplit(line, num_wanted, sep=None, exact_count=True):
    '''
    Utility function used to break up lines of IC Manage output in a controlled
    manner

    :param line: The string being split
    :type line: str
    :param num_wanted: The number of elements wanted from the split
    :type num_wanted: int
    :param sep: Optional separator. If not specified uses the default for Python split() method
    :type sep: None or str
    :param exact_count: Boolean indicating whether or not the number of elements post-split must be exact. Defaults to True
    :type exact_count: bool
    :return: The split string
    :rtype: list
    :raises: Exception
    '''
    # Find out how many fields we have
    line_fields = line.split(sep)
    num_found = len(line_fields)

    # Throw exception if the count is either too few or too many
    if num_found < num_wanted or (exact_count and num_found != num_wanted):
        raise Exception('Expected {0} fields, got {1} in string {2}'.format(num_wanted,
            num_found, line))

    # If there are more fields than requested, re-split to the right number of fields
    if num_found > num_wanted:
        line_fields = line_fields[:num_wanted]

    # Return the list of fields
    return line_fields

def user_is_psginfraadm():
    '''
    return true is user is psginfraadm
    '''
    return os.getenv("USER") == 'psginfraadm'

def natural_sort(unsorted):
    '''
    Performs a natural sort on the list

    :param unsorted: The list to sort
    :type unsorted: list
    :return: The list sorted naturally
    :rtype: list
    '''
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(unsorted, key = alphanum_key)

@memoized
def get_thread_and_milestone_from_rel_config(config):
    '''
    Extracts the thread and milestone from the config
    Config can be either a REL or bREL configuration
    Returns (thread, milestone) tuple

    :param config: The REL configuration name
    :type config: str
    :return: Tuple consisting of (thread, milestone)
    :rtype: tuple
    '''
    thread = None
    milestone = None

    regex = re.compile("^b?REL(\d+\.\d+)(\w+)(-|_{2})")
    r = regex.search(config)
    if r:
        milestone = r.group(1)
        thread = r.group(2)

    return (thread, milestone)

def get_thread_and_milestone_from_prel_config(config, strict=False):
    '''
    Extracts the thread and milestone from the config
    Config can be either a REL or bREL configuration
    Returns (thread, milestone) tuple

    :param config: The REL configuration name
    :type config: str
    :param strict: if True, will only allow PREL, if False, will match PREL/REL
    :type strict: bool
    :return: Tuple consisting of (thread, milestone)
    :rtype: tuple
    '''
    thread = None
    milestone = None
    if not strict:
        regex = re.compile("^P?REL(\d+\.\d+)(\w+)(-|_{2})")
    else:
        regex = re.compile("^PREL(\d+\.\d+)(\w+)(-|_{2})")
    r = regex.search(config)
    if r:
        milestone = r.group(1)
        thread = r.group(2)

    return (thread, milestone)

@memoized
def is_rel_config_against_this_thread_and_milestone(rel_config, thread, milestone):
    '''
    Checks if rel_config was made against thread and milestone

    :param rel_config: THe name of the IC Manage REL config
    :type rel_config: str
    :param thread: The Altera thread
    :type thread: str
    :param milestone: The Altera milestone
    :type milestone: str
    :return: Boolean indicating whether or not rel_config was made against thread and milestone
    :type return: bool
    '''
    (config_thread, config_milestone) = get_thread_and_milestone_from_rel_config(rel_config)
    return thread == config_thread and milestone == config_milestone

@memoized
def normalize_config_name(config):
    '''
    'Normalizes' a config name, making it XML friendly

    :param config: Name of a config
    :type config: str
    :return: Normalized config
    :rtype: str
    '''
    return config.replace('--', '-').replace('__', '-')

def get_ww_details():
    '''
    Returns a tuple containing the current working week information
    THe tuple takes the form (yy, ww, d)

    :return: Tuple of the form (yy, ww, d)
    :type return: tuple
    '''
    year, ww, d = dmx.utillib.intel_dates.intel_calendar(utildt.date.today())
    return (str(year)[-2:], '{:02d}'.format(ww), str(d))

@contextmanager
def run_as_user(username):
    '''
    Context manager providing a simple way to run a series
     of commands as a different user.

    :param username: The username to run commands as
    :type username: str
    '''
    # http://pg-rdjira:8080/browse/DI-1183
    # P4USER takes precedence over $USER, so we override P4USER instead of $USER
    is_p4user_set = False
    if 'P4USER' in os.environ:
        is_p4user_set = True
        original_user = os.environ['P4USER']
        
    os.environ['P4USER'] = username
    yield
    if is_p4user_set:
        os.environ['P4USER'] = original_user
    else:
        del os.environ['P4USER']

def format_configuration_name_for_printing(project, variant, config, libtype=None):
    '''
    Takes the specified parameters and returns a string formatted in the Altera
    standard way of printing configurations:
    Simple = project/variant:libtype@config
    Composite: project/variant@config

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param config: The IC Manage configuration name
    :type config: str
    :param libtype: The optional IC Manage libtype
    :type libtype: str
    :return: The configuration name formatted to the Altera standard
    :type return: str
    '''
    if libtype is not None:
        formatted_config = format_simple_config_for_printing(project,
                                                             variant,
                                                             libtype,
                                                             config)
    else:
        formatted_config = format_composite_config_for_printing(project,
                                                                variant,
                                                                config)

    return formatted_config

@memoized
def format_simple_config_for_printing(project, variant, libtype, config):
    '''
    Formats a simple configuration name for printing. Uses the standard
    Altera convention for simple configurations:
    project/variant:libtype@config

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param libtype: The IC Manage libtype
    :type libtype: str
    :param config: The IC Manage configuration name
    :type config: str
    :return: The formatted full configuration name
    :type return: str
    '''
    return '{0}/{1}:{2}@{3}'.format(project, variant, libtype, config)

@memoized
def format_composite_config_for_printing(project, variant, config):
    '''
    Formats a composite configuration name for printing. Uses the standard
    Altera convention for simple configurations:
    project/variant@config

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param config: The IC Manage configuration name
    :type config: str
    :return: The formatted full configuration name
    :type return: str
    '''
    return '{0}/{1}@{2}'.format(project, variant, config)

@memoized
def split_pv(pv):
    '''
    Splits a project/variant into its separate parts and returns them

    :param pv: project/variant
    :type param: str
    :return: A tuple of (project, variant)
    :type return: tuple
    '''
    (project, variant) = pv.split('/')
    return (project, variant)

@memoized
def split_pvl(pvl):
    '''
    Splits a project/variant:libtype into its separate parts

    :param pvl: project/variant:libtype to split
    :type pvl: str
    :return: A tuple of (project, variant, libtype)
    :type return: tuple
    '''
    pv, libtype = pvl.split(':')
    project, variant = split_pv(pv)
    return (project, variant, libtype)

@memoized
def split_pvlc(pvlc):
    '''
    Splits a project/variant:libtype@config into its separate parts

    :param pvlc: project/variant:libtype@config
    :type pvlc: str
    :return: A tuple containing (project, variant, libtype, config)
    :type return: tuple
    '''
    pvl, config = pvlc.split('@')
    (project, variant, libtype) = split_pvl(pvl)
    return (project, variant, libtype, config)

@memoized
def split_pvc(pvc):
    '''
    Splits a project/variant@config into its separate parts
    
    :param pvc: project/variant@config
    :type pvc: str
    :return: A tuple containing (project, variant, config)
    :type return: tuple
    '''
    pv, config = pvc.split('@')
    (project, variant) = split_pv(pv)
    return (project, variant, config)

@memoized
def split_pvll(pvll):
    '''
    Splits a project/variant:libtype/library into its separate parts
    
    :param pvlr: project/variant:libtype/library
    :type pvlr: str
    :return: A tuple containing (project, variant, libtype, library)
    :type return: tuple
    '''
    pv, ll = pvll.split(':')
    (project, variant) = split_pv(pv)
    (libtype, library) = ll.split('/')
    return (project, variant, libtype, library)    

@memoized
def split_lc(lc):
    '''
    Splits a libtype@config into its separate parts
    
    :param lc: libtype@config
    :type lc: str
    :return: A tuple containing (libtype, config)
    :type return: tuple
    '''
    libtype, config = lc.split('@')
    return (libtype, config)        

def run_command(command, stdin=None, timeout=None, retried=0, maxtry=5, delay_in_sec=10, regex_list=None, retry=False, regex_list2=None):
    '''
    Run a sub-program in subprocess.Popen, pass it the input data,
    kill it if the specified timeout has passed.
    returns a tuple of exitcode, stdout, stderr
    exitcode is None if process was killed because of the timeout
    Note: This routine shamelessly copied code from
    http://betabug.ch/blogs/ch-athens/1093

    :param command: full command string
    :type command: str
    :param timeout: in seconds. If the command runs longer than this time, it will be killed, and return None.
    :type timeout: int
    :param retried: Defined how many times have this same command has been ran. Normally users should not touch this param. It is used internally. 
    :type retried: int
    :param maxtry: How many times should the same command be repeated when the QoS condition is met. Set to 0 if retry is not desired.
    :type maxtry: int
    :param delay_in_sec: How long, in seconds, should it wait before retrying again.
    :type delay_in_sec: int


    Test that the timeout works
    >>> run_command(command='sleep 60', stdin=None, timeout=5)
    (None, '', '')
    >>> run_command('echo foo')
    (0, 'foo\\n', '')
    >>> run_command('ls /foo/bar')
    (2, '', 'ls: /foo/bar: No such file or directory\\n')
    '''
    kill_flag = threading.Event()
    def _kill_process_after_a_timeout(pid):
        '''helper for killing the process'''
        os.kill(pid, signal.SIGTERM)
        kill_flag.set() # tell the main routine that we had to kill
        return
    proc = subprocess.Popen(command, bufsize=1, shell=True,
              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if regex_list is None:
        regex_list = get_icm_error_list()
    if regex_list2 is None:
        regex_list2 = ['.*']

    if timeout is not None:
        pid = proc.pid
        watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
        watchdog.start()
        (stdout, stderr) = proc.communicate(stdin)
        watchdog.cancel() # if it's still waiting to run
        success = not kill_flag.isSet()
        kill_flag.clear()
        exitcode = None
        if success:
            exitcode = proc.returncode
    else:
        (stdout, stderr) = proc.communicate(stdin)
        exitcode = proc.returncode

    ### This is needed for python 3
    if sys.version_info[0] > 2:
        stdout = stdout.decode()
        stderr = stderr.decode()

    # There are some error messages on stderr that are harmless
    # Let's filter them out here
    if stderr:
        # Database snap backup warning
        db_snap_warning = "Warning: pmsnap of Mysql database has not been executed within 30 days. Please refer to ICM_Backup.pdf in the documentation tree for important information on creating snapshots to backup your IC Manage service"
        # ARC/LSF session manager errors - really should be fixed by ARC
        arc_session_manager1 = "_IceTransSocketUNIXConnect: Cannot connect to non-local host"
        arc_session_manager2 = "Session management error: Could not open network socket"
        filtered_stderr = ""
        for line in stderr.splitlines():
            if db_snap_warning in line:
                LOGGER.debug("Removing database snap warning message")
                continue
            if arc_session_manager1 in line:
                LOGGER.debug("Removing first ARC session manager error")
                continue
            if arc_session_manager2 in line:
                LOGGER.debug("Removing second ARC session manager error")
                continue

            filtered_stderr += "{}\n".format(line)

        stderr = filtered_stderr

    if (is_string_icm_command(command) and does_result_meet_retry_condition(exitcode, stdout, stderr,  regex_list)) or (retry is True and exitcode !=0 and does_result_meet_retry_condition(exitcode, stdout, stderr, regex_list2)):
        LOGGER.debug("run_command met retry condition:\n=exitcode=:{}\n=stdout=:{}\n=stderr=:{}".format(exitcode, stdout, stderr))
        if retried < maxtry:
            LOGGER.info("Tried {} times, {} more times for retry ...".format(retried, maxtry-retried))
            LOGGER.debug("Check for corrective action ...")
            run_corrective_action_before_retry(stdout=stdout, stderr=stderr)
            LOGGER.debug("command: {}".format(command))
            time.sleep(delay_in_sec)
            return run_command(command, stdin=stdin, timeout=timeout, retried=retried+1, maxtry=maxtry, delay_in_sec=delay_in_sec, regex_list=regex_list, retry=retry)

    rephrase_messages_in_layman_terms(stdout, stderr)

    return (exitcode, stdout, stderr)
  

def rephrase_messages_in_layman_terms(stdout='', stderr=''):
    '''
    Printout extra layman-term messages based on the native tool error message, so that users know what to do/expect.
    Eg:-

        Tool message:
            Couldn't initialize local site permission tables:            
            chialinh@sjicm.sc.intel.com:1666 Perforce password (P4PASSWD) invalid or unset. 

        Rephrased Message:
            Please run 'icm_login' and try again.

    '''
    ### Eventually, there will be more rephrase message API.
    ### For readability-wise, we should wrap each rephrase function with a 
    ### meaningful function name, and put the function here to be run sequencially.
    _rephrase_message_for_icm_login(stdout=stdout, stderr=stderr)
    _rephrase_message_for_icm_login2(stdout=stdout, stderr=stderr)
    _rephrase_message_for_icm_license(stdout=stdout, stderr=stderr)
    # _rephrase_2(stdout=stdout, stderr=stderr)
    # _rephrase_3(stdout=stdout, stderr=stderr)
    # _rephrase_nth(stdout=stdout, stderr=stderr)
    # ... ... ...


def _rephrase_message_for_icm_login(stdout, stderr):
    regex = "Couldn't initialize local site permission tables:.*Perforce password \(P4PASSWD\) invalid or unset."
    msg = "Your icmp4 ticket invalid/expired. Kindly run 'icm_login', and then retry again."
    return _rephrase_message_base_function(stdout, stderr, regex, msg, terminate=True)

def _rephrase_message_for_icm_login2(stdout, stderr):
    regex = "Couldn't initialize local site permission tables:.*Your session has expired, please login again"
    msg = "Your icmp4 ticket invalid/expired. Kindly run 'icm_login', and then retry again."
    return _rephrase_message_base_function(stdout, stderr, regex, msg, terminate=True)


def _rephrase_message_for_icm_license(stdout, stderr):
    regex = "Couldn't initialize local site permission tables:.*User .* doesn't exist."
    msg = "You do not have icm-license. Kindly goto http://goto/psg_onboarding to request."
    return _rephrase_message_base_function(stdout, stderr, regex, msg)

def _rephrase_message_base_function(stdout, stderr, regex, msg, terminate=False):
    output = stdout + stderr
    m = re.search(regex, output, re.MULTILINE|re.DOTALL)
    finalmsg = ''
    if m:
        finalmsg = msg
        LOGGER.warning(finalmsg)
    
        if terminate == True:
            raise DmxErrorICLC01(finalmsg)
    return finalmsg


def is_string_icm_command(txt):
    pattern = '^(icmp4|_icmp4|pm|gdp|ggg|xlp4) '
    if re.search(pattern, txt):
        return True
    else:
        return False


def run_command_get_arc_job_id(command):
    '''
    This is a wrapper of run_command.
    Returns a list of 4 strings = (arc_job_id, exitcode, stdout, stderr)
    if failed to get arc_job_id, set arc_job_id=0
    '''
    exitcode, stdout, stderr = run_command(command)
    arc_job_id = 0
    if not exitcode and stdout:
        lines = stdout.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('Job') and 'is submitted to' in line:
                if lines[i-1].isdigit():
                    arc_job_id = lines[i-1]
                else:
                    arc_job_id = '0'
    return (arc_job_id, exitcode, stdout, stderr)


def add_common_args(parser):
    '''add --preview/--quiet/--debug options'''
    parser.add_argument('-n', '--preview', action='store_true', help='dry-run: don\'t make any icmanage changes')
    parser.add_argument('-q', '--quiet',   action='store_true', help='quiet: don\'t echo icmanage commands to stdout')
    # debug option is hidden from public
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--dmxretry', help=argparse.SUPPRESS, default='0')

def add_pvl_args(parser):
    '''add --project/--variant/--libtype options'''
    parser.add_argument('-p', '--project', metavar='project', required=True)
    parser.add_argument('-v', '--variant', metavar='variant', required=True)
    parser.add_argument('-l', '--libtype', metavar='libype',  required=True, nargs='+', action='append')    

@contextmanager        
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
    
def _pypattern(value, isregex):
    # if value is None return [^/]+ otherwise try to compile the pattern
    if value is None:
        return '[^/]+'
    if '\\' in value:
        raise Error("names cannot contain '\\'")
    if '/' in value:
        raise Error("names cannot contain '/'")
    if isregex:
        newvalue = value
    else:
        newvalue = value.replace('.', '\\.').replace('?', '.').replace('*', '[^/]*')
    # try to compile it as a python regular expression
    try:
        re.compile(newvalue)
    except:
        raise Error("bad name/pattern: '%s'" % value)

    ### Fix for Fogbugz: 375707
    if not newvalue.startswith("^"):
        newvalue = "^" + newvalue

    return newvalue    

def list_of_dict_to_csv(mylist):
    '''
    Given a list of dict and return a list of csv string with first dict keys as header
     -> input: [{'Project':'i10socfm', 'IP': 'liotest1'}, {'Project':'i10socfm', 'IP': 'liotest2'}]
     -> output: ['Project,IP', 'i10socfm,liotest1', 'i10socfm,liotest2']
    '''
    result = []

    for index, ea_dict in enumerate(mylist):
        keys_string = ','.join(list(ea_dict.keys()))
        values_string = ','.join(str(v) for v in list(ea_dict.values()))
        if index == 0:
            result.append(keys_string)
        result.append(values_string)
    return result


def is_pice_env():
    ret = False
    try:
        site = os.environ['ARC_SITE']
        if 'png' in site or 'sc' in site:
            ret = True
    except:
        pass            
    return ret

def get_tools_path(tool=None):
    path = '/tools'
    if is_pice_env():
        if not tool:
            raise DmxErrorCFEV01('Please specify tool\'s type in PICE env.')

        if tool == 'eda':
            path = '/p/psg/eda'
        elif tool == 'ctools':
            path = '/p/psg/ctools'                
        elif tool == 'flows':
            path = '/p/psg/flows'
        else:
            raise DmxErrorCFEV01('Type {} not found in PICE env.'.format(tool))
        
    return path           

def get_icmanage_path():
    path = '/tools/ic_manage_gdp'    
    if is_pice_env():
        path = '/p/psg/eda/icmanage/gdp'
    return path                    

### After the process of Altera UserId merged with Intel UserId, we no longer need
### get_altera_userid() function. Thus, we moved the origianl function to 
### get_altera_userid___old2() and create a new get_altera_userid() which blindly
### just return the same user.
def get_altera_userid(user):
    return user

def get_altera_userid___old2(user):
    if not is_pice_env():
        return user
    else:
        cmd = '/p/psg/ctools/arc/bin/psg_id_search -u {} --to-altera'.format(user)
        exitcode, stdout, stderr = run_command(cmd)

        if stdout and not stdout.isspace():
            LOGGER.debug("user returned by psg_id_search for {} = {}".format(user, stdout))
            tmp = stdout.strip()
            if tmp.startswith("zz_"):
                retval = tmp[3:]
            else:
                retval = tmp
            return retval
        else:
            raise Exception('Could not find ALTR->INTC mapping for userid:{}. Please contact psgicmsupport@intel.com for help.'.format(user))

def get_altera_userid___old(user):
    if not is_pice_env():
        return user
    if os.path.exists(ID_MAP):
        with open(ID_MAP, 'r') as f:
            lines = f.readlines()
            for line in lines:
                intelid = line.split(',')[1].strip('"').lower()
                alteraid = line.split(',')[0].strip('"').lower()
                if intelid == user:
                    return alteraid
    raise Exception('{} does not have ID mapping in {}'.format(user, ID_MAP))

def user_exists(user):
    try:
        pwd.getpwnam(user)
    except KeyError:
        return False
    return True            

def run_once(func):
    '''
    Wrapper function to ensure the header is only printed if there are differences
    and only printed once

    :param func: The name of the function to only run once
    '''
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper    

            
def get_class_filepath(cls):
    '''
    given the class, returns the fullpath of the physical file.
    '''
    return os.path.abspath(sys.modules[cls.__module__].__file__)
    

def get_release_ver_map(thread, milestone):
    '''
    Return the dmx+dmxdata version that should be used for the backend release system.

    If found:
        return [str(dmx_version), str(dmxdata_version)]
    else:
        return []
    '''
    try:
        data = load_release_ver_map()
        if thread in data and milestone in data[thread]:
            retlist = [data[thread][milestone]['dmx'], data[thread][milestone]['dmxdata']]
        else:
            retlist = []
    except:
        retlist = []

    return retlist


## Loads the dmx_setting_files/release_ver_map.json into dictionary
##
def load_release_ver_map():
    filename = os.path.join(get_dmx_setting_files_dir(), 'release_ver_map.json')
    LOGGER.debug("Loading {}".format(filename))
    
    try:
        with open(filename, 'r') as f:
            ret = json.load(f)
    except Exception as e:
        LOGGER.error(str(e))
        raise DmxErrorCFFL01("Fail loading {}".format(filename))
    return ret

def load_dmx_generic_settings_json():
    filename = os.path.join(get_dmx_setting_files_dir(), 'dmx_generic_settings.json')
    LOGGER.debug("Loading {}".format(filename))
    
    try:
        with open(filename, 'r') as f:
            ret = json.load(f)
    except Exception as e:
        LOGGER.error(str(e))
        raise DmxErrorCFFL01("Fail loading {}".format(filename))

    return ret

def get_p4port_from_dmx_generic_settings(site):
    return load_dmx_generic_settings_json()['P4PORT'][site]

def get_dmx_setting_files_dir():
    ret = os.getenv("DMX_SETTING_FILES_DIR", '/p/psg/flows/common/dmx/dmx_setting_files')
    return os.path.realpath(ret)

def get_approved_disks(project):
    '''
    Return a list of approved disks for a project
    '''
    p4port = os.getenv("P4PORT", '')
    if not p4port:
        raise DmxErrorICEV01("Your current environment doesn't have P4PORT set. Please make sure that you are in the correct arc shell.")

    # We purposely fail the pre-sync check to get the list of approved disks
    # icm_pre_sync.py does not care what variant is
    variant = 'variant'
    # /tmp is definitely not an approved path      
    dirname = '/tmp'

    cmd = '{} dummy {} {} {} {}'.format(get_icm_pre_sync_path(), dirname, project, variant, p4port)
    (exitcode, stdout, stderr) = run_command(cmd)
    disks = stdout.splitlines()[-2].replace('[','').replace(']','').replace('\'','').split(',')
    disks = [x.strip() for x in disks]

    return sorted(disks)

def is_workspace_path_allowed(project, variant, dirname):
    ''' 
    Check and make sure that the dirname path is an allowable path to create workspace 
    for the specific project/variant.
    '''
    p4port = os.getenv("P4PORT", '')
    if not p4port:
        raise DmxErrorICEV01("Your current environment doesn't have P4PORT set. Please make sure that you are in the correct arc shell.")

    cmd = '{} dummy {} {} {} {}'.format(get_icm_pre_sync_path(), dirname, project, variant, p4port)
    (exitcode, stdout, stderr) = run_command(cmd)
    return not exitcode

def get_icm_pre_sync_path():
    if sys.version_info[0] < 3:
        ret = '{}/triggers/icmpm/icm_pre_sync.py dummy {} {} {} {}'.format(get_icmanage_path(), dirname, project, variant, p4port)
    else:
        ret = os.path.join(LIB, 'py23comlib', 'icm_trigger', 'icm_pre_sync.py')
    return ret

def is_local_pg():
    ret = False
    if 'png' in os.getenv('HOSTNAME'):
        ret = True
    return ret
    
def is_local_sj():
    return not is_local_pg()            

def is_shell_bash():
    ret = False
    if 'bash' in os.environ['SHELL']:
        ret = True
    return ret        

def quotify(txt):
    '''
    Handles the quoting sorcery of a string/command so that 
    it can be safely passed into another command.

    Example Of Usage:-
    ------------------
    a = """ wash -n psgeng intelall -c 'echo "a b"; groups; date' """
    b = 'arc submit -- {}'.format(quotify(a))
    c = 'arc submit -- {}'.format(quotify(b))
    os.system(c)
    '''
    new = txt.replace("'", "'\"'\"'")
    return "'{}'".format(new)

def remove_quotes(txt):
    '''
    Remove all quotes (single and double) from the string
    '''
    return txt.replace("'", '').replace('"', '')


def create_tempfile_that_is_readable_by_everyone(prefix='', suffix=''):
    username = os.getenv("USER")
    hostname = os.getenv("HOST")
    suffix = '_{}{}'.format(hostname, suffix) # we need hostname in suffix to make sure the tempfile is unique

    userhotel = '/p/psg/data/{}/job'.format(username)

    tmpfile = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=userhotel)[1]
    LOGGER.debug("tmpfile created: {}".format(tmpfile))
    os.system("chmod -R 777 {}".format(tmpfile))
    return tmpfile


def print_errors(cmd, exitcode, stdout, stderr, exit=True):
    print("Command: {}".format(cmd))
    print("Exitcode: {}".format(exitcode))
    print("Stdout: {}".format(stdout))
    print("Stderr: {}".format(stderr))
    if exit:
        sys.exit(1)

def get_psg_id_search_idsid_by_wwid(wwid):
    '''
    Get user idsid thorugh wwid
    '''
    command = '/p/psg/ctools/arc/bin/psg_id_search -w {}'.format(wwid)
    exitcode, stdout, stderr = run_command(command)
    if exitcode:
        print_errors(command, exitcode, stdout, stderr)

    idsid = stdout.strip().split(':')[-1].strip()
    return idsid


def get_psg_id_search_info_by_userid(user, server=None):
    '''
    Get psg_id_search infro from idsid
    '''
    if server:
        #command = 'ssh -q {} "psg_id_search -u {} --get-intel-details"'.format(server, user)
        command = 'ssh -q {} "/p/psg/ctools/arc/bin/psg_id_search -u {} --get-intel-details"'.format(server, user)
    else:
        #command = 'psg_id_search -u {} --get-intel-details'.format(user)
        command = '/p/psg/ctools/arc/bin/psg_id_search -u {} --get-intel-details'.format(user)
    exitcode, stdout, stderr = run_command(command)
    if exitcode:
        print_errors(command, exitcode, stdout, stderr)

    if 'No matches to your query' in stdout:
        raise

    dict = {}
    lines = stdout.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':')
            if key not in dict:
                dict[key.strip()] = value.strip()
    if not dict:
        raise Exception('Could not get {} info with psg_id_search'.format(user))
    return dict

def sendmail(recipients, subject, body, cc_recipients=None, from_addr=None, attachment=None, texttype='plain'):
    to = list(set(recipients))  # uniqify
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject 
    msg['From'] = from_addr 
    msg['To'] = ','.join(recipients)
    #msg['Bcc'] = COMMASPACE.join(_BCC)

    ### Attached changelist.html
    if attachment and os.path.exists(attachment):
        part = MIMEBase('application', "octet-stream")
        with open(attachment, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(os.path.basename(attachment)))
        msg.attach(part)


    textPart = MIMEText(body, texttype)
    msg.attach(textPart)

    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(from_addr, recipients, msg.as_string())
    s.quit()

def send_email(recipients, subject, body, cc_recipients=None, from_addr=None, is_debug=False):
    """
    Sends email to specified recipients with specified subject and body.
    Change receipients to admin during debugging.

    Send a test email to $USER@altera.com
    >>> send_email(["%s@altera.com" % os.environ.get('USER')], "test subject", "test body <br>")
    """
    LOGGER.info("Sending email to(%s), cc(%s), from(%s), subject(%s)" %(recipients, cc_recipients, from_addr, subject))
    if is_debug:
        recipients = ["{}".format(os.environ['USER'])]
        cc_recipients = None

    EMAIL_TEMPLATES = os.path.join(LIB, 'dmx', 'tnrlib','email_templates')
    emailer = AlteraEmailer(EMAIL_TEMPLATES, from_addr)
    context = Context()
    context['debug'] = is_debug
    context['title'] = subject
    context['content'] = mark_safe(body)
    context['generator'] = "icm_helper.py"
    context['date'] = utildt.datetime.now()
    email = emailer.render_email_body("generic_email_dmx.html", context)
    emailer.send_email(email, subject, recipients, cc=cc_recipients)

def is_user_exist(user):
    '''
    Check is the user exists through finger command
    '''
    LOGGER.info('Check if user \'{}\' exist...'.format(user))
    cmd = 'finger {}'.format(user)
    LOGGER.debug(cmd)
    result = subprocess.check_output([cmd], stderr=subprocess.STDOUT, shell=True)
    if b'no such user' in result.rstrip():
        LOGGER.info('User \'{}\' does not exists'.format(user))
        return False
    else:
        LOGGER.info('User \'{}\' exists'.format(user))
        return True

def get_icm_error_list():
    regex_list = [
        'Could not open IC Manage database: Too many connections',
        "Can't connect to MySQL server .* Too many connections",
        "Too many connections .*:Unable to connect",
        "Connect to server failed",
        "Unable to connect to site.*QMYSQL: Unable to connect",
        "Unknown MySQL server host",
        "Found opened files in .*/icmrel/.*\nUsers should not be modifying release files. Please fix and correct\nthe files and perforce protect table\nClients with opened files:\n  .*@.*",
        "Couldn't delete client,.*:\nClient '.*' has files opened. To delete the client, revert any opened files and delete any pending changes first. An administrator may specify -f to force the delete of another user's client.",
        "immutable@.* Perforce password \(P4PASSWD\) invalid or unset.",
    ]
    return regex_list

def get_naa_error_list():
    regex_list = [
        'Could not open IC Manage database: Too many connections',
        "Can't connect to MySQL server .* Too many connections",
        "Too many connections .*:Unable to connect",
        "Connect to server failed",
        "Unable to connect to site.*QMYSQL: Unable to connect",
        "Unknown MySQL server host",
    ]
    return regex_list


def run_corrective_action_before_retry(stdout='', stderr=''):
    '''
    Some condition needs to have some corrective action in place before another retry, otherwise the retry is meaningless.
    An example would be, if in the process of finding out that there were opened files in the destination branch during an 'integrate' run, 
    we need to correct it by 'reverting' those files before another retry. Otherwise, all subsequent retries will be always getting the same
    error, and it will be meaningless.
    '''
    ### Eventually, there will be more corrective actions.
    ### For readability-wise, we should wrap each corrective action with a 
    ### meaningful function name, and put the function here to be run sequencially.
    revert_opened_files_in_icmrel_branch(stdout=stdout, stderr=stderr)
    delete_leftover_client_during_add_config_properties(stdout=stdout, stderr=stderr)
    # corrective_action_2(stdout=stdout, stderr=stderr)
    # corrective_action_3(stdout=stdout, stderr=stderr)
    # corrective_action_nth(stdout=stdout, stderr=stderr)
    # ... ... ...

def delete_leftover_client_during_add_config_properties(stdout='', stderr=''):
    output = stdout + stderr
    regex = "Couldn't delete client,.*:\nClient '(.*)' has files opened. To delete the client, revert any opened files and delete any pending changes first. An administrator may specify -f to force the delete of another user's client."
    m = re.search(regex, output, re.MULTILINE|re.DOTALL)
    if m:
        LOGGER.debug("Taking corrective action (delete_leftover_client_during_add_config_properties) ... ")
        client = m.groups()
        return delete_client_as_psginfraadm(client)


def revert_opened_files_in_icmrel_branch(stdout='', stderr=''):
    output = stdout + stderr
    regex = "Found opened files in (.*/icmrel/.*)\nUsers should not be modifying release files. Please fix and correct\nthe files and perforce protect table\nClients with opened files:\n  (.*)@(\S+)\s"
    m = re.search(regex, output, re.MULTILINE|re.DOTALL)
    if m:
        LOGGER.debug("Taking corrective action (revert_opened_files_in_icmrel_branch) ... ")
        filespec, userid, client = m.groups()
        return revert_files_as_psginfraadm(filespec, client)


def delete_client_as_psginfraadm(client):
    basecmd = '_xlp4 client -d -f {}'.format(client)
    return run_cmd_as_psginfraadm(basecmd)

def revert_files_as_psginfraadm(filespec, client):
    basecmd = '_xlp4 revert -C {} {}'.format(client, quotify(filespec))
    return run_cmd_as_psginfraadm(basecmd)

def run_cmd_as_psginfraadm(basecmd):
    ### This import somehow needs to be here.
    ### Somehow, importing this right at the beginning will create a circular-import-error
    ### https://stackabuse.com/python-circular-imports/
    import dmx.utillib.stringifycmd
    
    arcopts = dmx.utillib.stringifycmd.StringifyCmd.DEFAULT
    s = dmx.utillib.stringifycmd.StringifyCmd(basecmd, arcopts='default', sshopts='default')
    s.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
    finalcmd = s.get_finalcmd_string()
    return os.system(finalcmd)


def get_opened_files_by_filespec(filespec, site=''):
    '''
    if site == '', it will run locally.

    return:
    [{'action': 'edit',
      'change': 'default',
      'client': 'lionelta.i10socfm.liotest1.2065',
      'clientFile': '//lionelta.i10socfm.liotest1.2065/liotest1/dv/a',
      'depotFile': '//depot/icm/proj/i10socfm/liotest1/dv/dev/a',
      'haveRev': '4',
      'rev': '4',
      'type': 'text',
      'user': 'lionelta'},
     {'action': 'edit',
      'change': 'default',
      'client': 'psginfraadm.i10socfm.liotest1.528362',
      'clientFile': '//psginfraadm.i10socfm.liotest1.528362/liotest1/dv/a',
      'depotFile': '//depot/icm/proj/i10socfm/liotest1/dv/dev/a',
      'haveRev': '4',
      'rev': '4',
      'type': 'text',
      'user': 'psginfraadm'},
    ... ... ...
    
    NOTE:-
    ------
    As this API is running as 'icmAdmin' and cross site, we need to make sure
    the user has the icmAdmin ticket to the specific site. 
    It is the responsibility of the caller of this API to make sure login_to_icmAdmin().
    We do not want to run login_to_icmAdmin everytime this API is called because it only needs
    to be ran once per user.
    '''
    ### This import somehow needs to be here.
    ### Somehow, importing this right at the beginning will create a circular-import-error
    ### https://stackabuse.com/python-circular-imports/
    import dmx.utillib.stringifycmd

    p4port = get_p4port_from_dmx_generic_settings(site)

    ### For some reason, when u run in a workspace, and are trying to use -p{non_local_site}, 
    ### it will complain this error, and exit, which i think is an icmp4 bug.
    ###     Client 'lionelta.i10socfm.liotest1.2066' is restricted to use on server 'sjicm', not on server 'ppgicm'
    ### To workaround this, just cd to a non-icm-workspace before running icmp4 command
    cmd = "cd; xlp4 -p{} -u{} -ztag opened -a '{}'".format(p4port, ICMADMIN, filespec)
    sc = dmx.utillib.stringifycmd.StringifyCmd(cmd)
    finalcmd = sc.get_finalcmd_string()
    LOGGER.debug("Running: {}".format(finalcmd))
    exitcode, stdout, stderr = run_command(finalcmd)
    LOGGER.debug("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
    '''
    This should return something like this
    
    ... depotFile //depot/icm/proj/i10socfm/liotest1/dv/dev/b
    ... clientFile //psginfraadm.i10socfm.liotest1.528362/liotest1/dv/b
    ... rev 4
    ... haveRev 4
    ... action edit
    ... change default
    ... type text
    ... user psginfraadm
    ... client psginfraadm.i10socfm.liotest1.528362
    
    ... depotFile //depot/icm/proj/i10socfm/liotest1/dv/dev/b
    ... clientFile //psginfraadm.i10socfm.liotest1.528362/liotest1/dv/b
    ... rev 4
    ... haveRev 4
    ... action edit
    ... change default
    ... type text
    ... user psginfraadm
    ... client psginfraadm.i10socfm.liotest1.528362
    
    '''
    retlist = []
    data = {}
    for line in stdout.split('\n'):
        if not line or line.isspace():
            if data:
                retlist.append(data)
            data = {}
        elif line.startswith('... '):
            threedots, key, value = line.split(' ', 2)
            data[key] = value
    return retlist


def force_revert_files_by_filespec(filespec, unlock=True, site=''):
    '''
    Forcefully revert all the opened files.
    This API works running as anyone.

    NOTE:
    -----
    As this API is running as 'icmAdmin' and cross site, we need to make sure
    the user has the icmAdmin ticket to the specific site. 
    It is the responsibility of the caller of this API to make sure login_to_icmAdmin().
    We do not want to run login_to_icmAdmin everytime this API is called because it only needs
    to be ran once per user.
    '''
    ### This import somehow needs to be here.
    ### Somehow, importing this right at the beginning will create a circular-import-error
    ### https://stackabuse.com/python-circular-imports/
    import dmx.utillib.stringifycmd
    openedfiles = get_opened_files_by_filespec(filespec, site=site)
    
    ### Get the clients 
    tmp = {}
    for of in openedfiles:
        tmp[of['client']] = 1
    clientnames = list(tmp.keys())
    
    p4port = get_p4port_from_dmx_generic_settings(site)

    for clientname in clientnames:
        ### For some reason, when u run in a workspace, and are trying to use -p{non_local_site}, 
        ### it will complain this error, and exit, which i think is an icmp4 bug.
        ###     Client 'lionelta.i10socfm.liotest1.2066' is restricted to use on server 'sjicm', not on server 'ppgicm'
        ### To workaround this, just cd to a non-icm-workspace before running icmp4 command
        commands = ["cd; xlp4 -p{} -u{} revert -C {} -k '{}'".format(p4port, ICMADMIN, clientname, filespec)]
        if unlock:
            commands.append("cd; xlp4 -p{} -u{} -c {} unlock -f '{}'".format(p4port, ICMADMIN, clientname, filespec))
            commands.append("cd; xlp4 -p{} -u{} -c {} unlock -f -x '{}'".format(p4port, ICMADMIN, clientname, filespec))
        for cmd in commands:
            sc = dmx.utillib.stringifycmd.StringifyCmd(cmd)
            finalcmd = sc.get_finalcmd_string()
            LOGGER.debug("Running: {}".format(finalcmd))
            exitcode, stdout, stderr = run_command(finalcmd)
            LOGGER.debug("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))


def does_result_meet_retry_condition(exitcode=0, stdout='', stderr='', regex_list=''):
    '''
    This function runs a list of cross-checking from the given (exitcode, stdout, stderr),
    which is the output of an icmanage command, and then determines if the situation warrants 
    for a dmx_retry. If any of the condition met, then it means it warrants a retry, and thus,
    return True. Else return False.
    '''
    output = stdout + stderr
    for regex in regex_list:
        if re.search(regex, output, re.MULTILINE|re.DOTALL):
            return True
    return False


def dmx_retry(max_retry=5, delay_in_sec=5):
    ''' This is the QoS layer for DMX.
    What it does is that, it will rerun the same command again as to how the original dmx command was issued.

    The hidden option it uses is --dmxretry <digit>.

    Everytime dmx_retry is called, the entire cmd will be rerun with the --dmxretry value +1.

    Here's a chronological example:-

        User runs the following command from terminal:-
            >dmx report list -p abc 

        dmx_retry(max_retry=3):-
            >dmx report list -p abc --dmxretry 1
        
        dmx_retry(max_retry=3):-
            >dmx report list -p abc --dmxretry 2
        
        dmx_retry(max_retry=3):-
            >dmx report list -p abc --dmxretry 3
        
        dmx_retry(max_retry=3):-
            >dmx report list -p abc --dmxretry 4
            raise exception
    
    '''
    optname = '--dmxretry'
    ### Finding location of option in sys.argv
    try:
        index = sys.argv.index(optname)
    except:
        index = 0

    ### if --dmxretry is found, modify origianl command as --dmxretry <value +1>
    ### if --dmxretry not found, append original command with '--dmxretry 1'
    if index:
        count = '{}'.format(int(sys.argv[index+1]) + 1)
        sys.argv[index+1] = count
    else:
        count = '1'
        sys.argv.append(optname)
        sys.argv.append(count)

    if int(count) > int(max_retry):
        raise Exception("Max Retry count({}) exceeded.".format(max_retry))

    time.sleep(delay_in_sec)
    rerun_self()


def rerun_self():
    LOGGER.debug('rerun_self: {}'.format(sys.argv))
    os.execl(sys.executable, sys.executable, *sys.argv) 

def get_proj_disk(proj):
    '''
        get a list of project work disk with given project name
        return
            list of the disk
        or
            0 = no restriction applicable for the project
    '''
    p4port = os.environ.get('P4PORT')
    site = get_site(p4port)

    filelist = '/p/psg/da/infra/icm/presync/' + site + '.' + proj

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

def get_site(p4port):
    match = re.search('(\w+)\.(\w+)\.intel\.com' ,p4port)
    if match:
        site = match.group(2)
    else:
        site = 0
    return site

def check_proj_restrict(icmproject,p4clientdir):
    '''
        check if the p4clientdir is comply with the project disk path restriction
        return
            0 = project not restricted
            1 = the p4clientdir is in compliance (okay to setup workspace)
            2 = the p4clientdir does not comply to the restriction (cannot setup workspace)
    '''
    #p4port = os.environ.get('P4PORT')
    #site = get_site(p4port)

    status, output, stderr = run_command("/usr/intel/bin/sitecode")
    pathlist = get_proj_disk(icmproject)
    if pathlist:
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

def get_waiver_data(tnrwaiver_file, thread, milestone, username):
    '''
    Convert tnrwaiver format file to mongodb collection data
    '''
    data = []

    # Load tnrwaiver file and check for syntac error
    wf = WaiverFile()
    wf.load_from_file(tnrwaiver_file)

    # convert tnrwaiver file format to mongodb collection format
    for line in  wf.rawdata:
        ip = line[0]
        deliverable = line[1]
        subflow = line[2]
        reason = line[3]
        error = line[4]

        waiver_mongo_dict = {'thread':thread, 'variant':ip, 'flow':deliverable, 'subflow':subflow, 'reason':reason, \
                             'error':error, 'user':username, 'milestone':milestone, 'approval_status':'pending'}
        data.append(waiver_mongo_dict)


    return data

def get_default_dev_config(family='', thread='', icmproject=''):
    '''
    Get the default 'dev' config for a specific family/thread/icmproject.
    '''
    if family == 'Falcon' and icmproject in ['i10socfm', 'hpsi10']:
        config = 'fmx_dev'
    elif family == 'Falconpark' and icmproject in ['i10socfm', 'hpsi10']:
        config = 'fp8_dev'
    elif thread == 'GDRrevB0' and icmproject in ['gdr']:
        config = 'gdr_revB0_dev'
    elif thread == 'DPT8revA0' and icmproject in ['t16ffsocdm']:
        config = 'dpt8_dev'
    else:
        config = 'dev'
    return config

def get_all_default_dev_configs():
    return ['dev', 'gdr_revB0_dev', 'fp8_dev', 'fmx_dev', 'dpt8_dev']

def get_correct_icmproject(ip, family=''):
    '''
    https://jira.devtools.intel.com/browse/PSGDMX-2403

    Here's one of the example of the issue.
    In family=Falconpark, these 2 projects are defined under it:-
    - i10socfm
    - i10soc2
    variant cw_lib exist in both the both icmproject.

    Question, how do we know which cw_lib should dmx be using/getting?
    - i10socfm/cw_lib ?
    - i10soc2/cw_lib?

    This API provides that algorithm to make that decision.

    This should be used in conjunction with family.get_ip(), like this:-
        family.get_ip("cw_lib", project_filter=get_correct_icmproject("cw_lib", "Falconpark")

    This API should only be used if we are getting the ip without a workspace.
    If a workspace exists, the most accurate/correct way is to get the project from the workspace, like this
        family.get_ip("cw_lib, workspace.get_project_of_ip("cw_lib"))
    '''
    if not family:
        family = os.getenv("DB_FAMILY", '')
    if not family:
        raise Exception ("family input not provided, and $DB_FAMILY env var not defined.")

    ### This import needs to be here instead of at the top because it will create cyclic import error
    import dmx.abnrlib.icm
    cli = dmx.abnrlib.icm.ICManageCLI()
    if family != 'Falconpark':
        return ''
    else:
        if cli.config_exists('i10socfm', ip, 'fp8_dev'):
            return 'i10socfm'
        else:
            return 'i10soc2'

def replace_parent_name(full_data):
    '''
    Given a list of dict, find the dict keys and replace xx:parent:name to user familiar project, variant, libtype, config:
    '''
    result = []
    for data in full_data:
        if data.get('variant:parent:name'):
            data['variant'] = data.pop('variant:parent:name')
        if data.get('project:parent:name'):
            data['project'] = data.pop('project:parent:name')
        if data.get('libtype:parent:name'):
            data['libtype'] = data.pop('libtype:parent:name')
        else: continue
        if data.get('name'):
            data['config'] = data.pop('name')
    

        result.append(data)
    return result 

def set_dmx_workspace(stagingws):
    os.environ['DMX_WORKSPACE'] = stagingws
    return True

def login_to_icmAdmin(p4port='', site=''):
    '''
    if p4port is not given, site must be specified
    the p4port is then extract from the dmx_generic_settings.json
    based on the site 

    *** NOTE:
    for GDPXL, there is no need to use this login_to_icmAdmin() anymore, because we can just specify the username+password into xlp4 like this:
        > xlp4 -uicmAdmin -PicmAdmin ...
    '''
    if not p4port:
        p4port = get_p4port_from_dmx_generic_settings(site)
    #return os.system("echo icmAdmin | xlp4 -uicmAdmin -p{} login -a".format(p4port))
    LOGGER.debug("No need to login_to_icmAdmin in gdpxl as we can run as icmAdmin in xlp4/gdp command by specifying -uicmAdmin already.")
    return 0

def which(cmd):
    ''' this api is meant to replace py2's which.which command '''
    exitcode, stdout, stderr = run_command("which {}".format(cmd))
    if not exitcode and stdout:
        return stdout
    else:
        return ''

def get_dmxroot_dir(path=None):
    ''' Keep traversing up until .dmxrootdir file is found.
    return the realpath of that dir.
    If not found, return ''
    '''
    if not path:
        path = os.path.dirname(os.path.abspath(__file__))
    filename = '.dmxrootdir'
    while True:
        filepath = os.path.join(path, filename)
        print("path:{}".format(path))
        if path == '/':
            return ''
        elif os.path.isfile(filepath):
            return os.path.abspath(path)
        path = os.path.dirname(path)


