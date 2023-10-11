#!/usr/bin/env python
'''
Description: utility for sion

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
import subprocess
import os
import sys
import logging
LOGGER = logging.getLogger()

def run_as_psginfraadm(project = None, variant = None, libtype = None, config = None, dir = None, command = None, user = None, cfgfile = None, icm_command = None, misc = None):
    LOGGER.info("Your request has been submitted. Please do not kill/terminate/cancel the job until it is done.")    
    workspace_helper = "/p/psg/flows/common/dmx/current/lib/python/dmx/sionlib/workspace_helper"
    cmd = "/p/psg/da/infra/admin/setuid/swap_to_psginfraadm" 
    cmd = "%s %s %s %s %s %s %s %s %s %s %s" % (cmd, command, project, variant, libtype, config, dir, user, cfgfile, icm_command, misc)
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
    return (exitcode, stdout, stderr)

def print_errors(cmd, exitcode, stdout, stderr):
    LOGGER.error("User = %s" % os.getenv('USER'))
    LOGGER.error("Hostname = %s" % os.getenv('HOSTNAME'))
    LOGGER.error("ARC Job ID = %s" % os.getenv('ARC_JOB_ID'))
    LOGGER.error("Command = %s" % cmd)
    LOGGER.error("Exitcode = %s" % exitcode)
    LOGGER.error("Stdout = %s" % stdout)
    LOGGER.error("Stderr = %s" % stderr)
    return 1

    
        
