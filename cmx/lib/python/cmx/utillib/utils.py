#!/usr/intel/pkgs/python3/3.9.6/bin/python3

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/utillib/utils.py#27 $
$Change: 7756464 $
$DateTime: 2023/08/25 01:53:39 $
$Author: wplim $

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
import glob
import sys
import pwd
import time
import re
import threading
import subprocess
import argparse
import datetime as utildt
from contextlib import contextmanager
import logging
import json
import tempfile
import signal
from configparser import ConfigParser
import shlex

LOGGER = logging.getLogger(__name__)

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, LIB)

def get_tools_path(tool=None):
    path = '/tools'
    if not tool:
        raise ('Please specify tool\'s type in PICE env.')
    if tool == 'eda':
        path = '/p/psg/eda'
    elif tool == 'ctools':
        path = '/p/psg/ctools'                
    elif tool == 'flows':
        path = '/p/psg/flows'
    else:
        raise ('Type {} not found in PICE env.'.format(tool))
        
    return path           

def add_common_args(parser):
    '''add --preview/--quiet/--debug options'''
    parser.add_argument('-n', '--preview', action='store_true', help='dry-run: don\'t make any icmanage changes')
    parser.add_argument('-q', '--quiet',   action='store_true', help='quiet: don\'t echo icmanage commands to stdout')
    # debug option is hidden from public
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--dmxretry', help=argparse.SUPPRESS, default='0')


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
    proc = subprocess.Popen(command, bufsize=1, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

    return (exitcode, stdout, stderr)
  

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

def get_dmx_root_from_folder(folder):
    '''
    This api tries to find the dmx root dir from a given folder
    if folder == 'abnrlib'/plugins/wrappers/utillib:
        return abspath(../../../../..)
    elif folder == 'abnrlib/flows'
        return abspath(../../../../../..)
    elif folder == 'bin'/'scripts'
        return abspath(../../)
    elif (to be added in the future ...)

    Common Usage:
        dmxrootdir = get_dmx_root_from_folder(os.path.basename(os.path.dirname(__file__)))
    '''
    if folder in ['abnrlib', 'plugins', 'wrappers', 'utillib', 'tnrlib']:
        ret = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
    elif folder in ['abnrlib/flows', 'flows']:
        ret = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', '..'))
    elif folder in ['bin', 'scripts']:
        ret = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
    return ret 

def get_old_dmx_exe_from_folder(folder):
    dmxroot = get_dmx_root_from_folder(folder)
    return os.path.abspath(os.path.join(dmxroot, 'bin', 'dmx'))

def dispatch_cmd_to_other_tool(dmx_exe_path, sysargv):
    '''
    sysargv = ['/a/b/dmx/main/cmx/bin/dmx', 'report', 'list', '-p', 'pro', '-i', 'ip', '--debug']
    dmx_exe_path = '/a/b/dmx/main/bin/dmx'

    cmd = """ /a/b/dmx/main/bin/dmx 'report' 'list' '-p' 'pro' '-i' 'ip' '--debug' """
    '''
    cmd = '{} '.format(os.path.abspath(dmx_exe_path))
    for arg in sysargv[1:]:
        cmd += quotify(arg) + ' '
    LOGGER.debug("Dispatching cmd to: {}".format(cmd))
    return os.system(cmd)
    
def is_belongs_to_arcpl_related_deliverables(deliverable):
    config_parser = ConfigParser()
    cp_dict = config_parser.read(f'{LIB}/cmx//constants/arcplwrapper.ini')
    section = 'arcpl_related_deliverables'
    key = 'list'
    flag = False
    if len(cp_dict) != 0:
        if config_parser.has_option(section, key):
            list_str = config_parser.get(section, key)
            if deliverable in list_str.split(','):
                flag = True
    return flag

def get_icm_wsroot_from_workarea_envvar(workarea=None):
    ''' get fullpath to icm_wsroot from $WORKAREA env var.
    - if no workspaces found, return None
    - if 1 workspace found, return fullpath to wsroot
    - if >1 workspace found, raise error
    '''
    if not workarea:
        envvar = os.getenv("WORKAREA", "")
    else:
        envvar = workarea

    if not os.path.exists(envvar):
        raise Exception("WORKAREA: {} does not exists.".format(envvar))

    LOGGER.debug("WORKAREA env var: {}".format(envvar))
    if not envvar:
        raise Exception('WORKAREA env var not define!')
    #founds = glob.glob(envvar+'/psg/*/'+'.icmconfig')
    founds = glob.glob(envvar+'/psg/.icmconfig')

    retlist = []
    if founds:
        for ea in founds:
            retlist.append(os.path.dirname(ea))
    if len(retlist) > 1:
        raise Exception("More than 1 workspaces found!! {}".format(retlist))
    elif len(retlist) == 1:
        return retlist[0]
    else:
        return None

def remove_prefix(string):
    if string.startswith("snap-"):
        return string.removeprefix("snap-")
    elif string.startswith("REL"):
        return string.removeprefix("REL")
    elif string.startswith("PREL"):
        return string.removeprefix("PREL")
    else:
        return string

def get_ws_from_ward(ward=None):
    ''' get workspace names from $DMX_WORKSPACE.
    - if no workspaces found, return None
    - if 1 workspace found, return fullpath to wsroot
    - if >1 workspace found, raise error
    '''
    envvar = get_dmx_workspace_env_var()
    LOGGER.debug("DMX_WORKSPACE env var: {}".format(envvar))
    if not envvar:
        raise Exception('No DMX_WORKSPACE env variable, rerun your cth_psetup_psg command.')
    founds = glob.glob(envvar+'/*/'+'.icmconfig')

    retlist = []
    if founds:
        for ea in founds:
            retlist.append(os.path.dirname(ea))
    if len(retlist) > 1:
        raise Exception("More than 1 workspaces found!! {}".format(retlist))
    elif len(retlist) == 1:
        return retlist[0]
    else:
        return None

def get_dmx_workspace_env_var():
    '''
    Get the env var 'DMX_WORKSPACE' value
    - if $DMX_WORKSPACE is not defined
        > Return ''
    - elif $DMX_WORKSPACE basename == 'cthfe':
        > this means that user runs 'cth_psetup' inside of a $WORKAREA/psg/<wsroot>/<ip>/cthfe
        > we need to massage it so that $DMX_WORKSPACE is '$WORKAREA/psg'
    - else
        > return $DMX_WORKSPACE
    '''
    val = os.getenv("DMX_WORKSPACE", "")
    if not val:
        return val
    elif os.path.basename(os.path.dirname(val)) == 'cthfe':
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(val))))
    else:
        return val

def filtered_cell_not_in_cells(cells, filtered_cells):
    needed_cell = {} 
    ipcell = []
    if not filtered_cells:
        return cells

    for projip, cell in cells.items():

        for eacell in cell:
            if eacell in filtered_cells:
                ipcell.append(eacell)
            else:
                LOGGER.info(f'Skip cell: {eacell}.')
        needed_cell[projip] = ipcell 
    return needed_cell


def get_ward():
    ward = os.environ.get("WARD")
    if not ward:
        ward = os.environ.get("WORKAREA")
    return ward

def get_ws_info(workarea):
    filename = f"{workarea}/.dmxwsinfo"
    with open(filename) as f:
        return json.load(f)


def get_psetup_psg_cmd():
    ''' 
    - find CTH_PSET_PSG in $WORKAREA/.cth.cth_query
      > CTH_PSETUP_PSG = cth_psetup_psg -proj psg/2023WW08 -cfg SZRA0P00I0S_FE_RC.cth -ward /nfs/site/disks/da_infra_1/users/psginfraadm/rubbish/febtest/test -read_only -cfg_ov rc/szra0/SZRA0P00I0S_FE_RC.ov,./override.cth -x 'setenv PSG_CTH_CFG rc ; setenv WORKAREA /nfs/site/disks/da_infra_1/users/psginfraadm/rubbish/febtest/test ; ; '
      > return: ['cth_psetup_psg', '-proj', 'psg/2023WW08', '-cfg', 'SZRA0P00I0S_FE_RC.cth', '-ward', '/nfs/site/disks/da_infra_1/users/yltan/rubbish/febtest/test', '-read_only', '-cfg_ov', 'rc/szra0/SZRA0P00I0S_FE_RC.ov,./override.cth', '-x', 'setenv PSG_CTH_CFG rc ; setenv WORKAREA /nfs/site/disks/da_infra_1/users/yltan/rubbish/febtest/test ; ; ']
    '''
    wa = os.getenv("WORKAREA")
    infile = os.path.join(wa, '.cth.cth_query')
    with open(infile) as f:
        for line in f:
            if line.startswith("CTH_PSETUP_PSG = "):
                var, cmdstr = line.split(' = ')
                retlist = shlex.split(cmdstr)
                return retlist
    return ''

def add_cmd_to_psetup_cmdlist(psetup_cmd_list, cmd_tobe_added, remove_ward=True):
    '''
    psetup_cmd_list = is the output from get_psetup_psg_cmd()
    - if -x is found in the psetup_cmd_list:
        > it will be modified to -cmd
    - if -x/-cmd is already in psetup_cmd_list:
        > added cmd_tobe_added to the existing cmd
    - if -x/-cmd does not exist in psetup_cmd_list:
        > add '-cmd "cmd_tobe_added"' to it

    Example:
    =======
        psetup_cmd_list = ['cth_psetup', '...', '-x', 'cmd1 cmd2']
        cmd_tobe_added = 'newcmd -a -b -c'
        return = ['cth_psetup', '...', '-cmd', 'cmd1 cmd2; newcmd -a -b -c']

        psetup_cmd_list = ['cth_psetup', '...', '-cmd', 'cmd1 cmd2']
        cmd_tobe_added = 'newcmd -a -b -c'
        return = ['cth_psetup', '...', '-cmd', 'cmd1 cmd2; newcmd -a -b -c']

        psetup_cmd_list = ['cth_psetup', '-p', 'psg']
        cmd_tobe_added = 'newcmd -a -b -c'
        return = ['cth_psetup', '-p', 'psg', '-cmd', 'newcmd -a -b -c']

    USAGE:
    ======
    ps = get_psetup_psg_cmd()
    cmd = add_cmd_to_psetup_cmdlist(ps, 'setenv P4PORT scylicm.sc.intel.com:1666; setenv P4CONFIG .icmconfig; dmx help')
    
    ### CTH_SETUP_CMD needs to be undefined in order to be able to run cth_psetup within an already cth_psetup'd environment.
    finalcmd = 'env CTH_SETUP_CMD= ' + cmd  
    os.system(finalcmd)
    '''
    try:
        i = psetup_cmd_list.index('-x')
        ### -x found. Replace it with -cmd
        psetup_cmd_list[i] = '-cmd'
    except:
        pass
    
    try:
        i = psetup_cmd_list.index('-cmd')
        ### -cmd found. Do nothing
    except:
        ### -cmd not found. Let's add ['-cmd', ''] to it
        psetup_cmd_list += ['-cmd', '']
        i = psetup_cmd_list.index('-cmd')
    
    psetup_cmd_list[i+1] += '; {}'.format(cmd_tobe_added)

    try:
        i = psetup_cmd_list.index('-ward')
        del(psetup_cmd_list[i])
        del(psetup_cmd_list[i])
    except:
        pass


    return psetup_cmd_list

