#!/usr/bin/env python
import sys
import os
import fcntl
import re
import pwd
import argparse
import logging
import shutil
import json
import time
import datetime

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, LIB)

import dmx.abnrlib.flows.workspace
from dmx.abnrlib.flows.list import List
from dmx.abnrlib.flows.printconfig import PrintConfig
from dmx.abnrlib.flows.diffconfigs import DiffConfigs
from dmx.utillib.utils import is_pice_env, get_ww_details
from dmx.sionlib.sion_utils import link_ws, generate_project_family_reference, run_command, get_default_parameters, create_workspace, populate_cache_by_deliverable, write_to_json


LOGGER = logging.getLogger()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cmd', '--command')
    parser.add_argument('-p', '--project')
    parser.add_argument('-i', '--ip')
    parser.add_argument('-d', '--deliverable')
    parser.add_argument('-b', '--bom')
    parser.add_argument('-cache_dir', '--cache_directory')
    parser.add_argument('-ws_dir', '--ws_directory')
    parser.add_argument('-w', '--wsname')
    parser.add_argument('-u', '--user')
    parser.add_argument('-cfg', '--cfgfile')
    parser.add_argument('-cache_only')
    parser.add_argument('-misc')

    args = parser.parse_args()
    command = args.command

    #preparing to run command
    if command == "populate":
        project = args.project
        ip = args.ip
        if args.deliverable=='None':
            deliverable=None
        else:
            deliverable = args.deliverable
        bom = args.bom
        if (args.cache_directory=="None") or (args.cache_directory is None):
            cache_dir = None
        else:
            cache_dir = os.path.abspath(args.cache_directory)
        if (args.ws_directory=="None") or (args.ws_directory is None):
            ws_dir = None
        else:
            ws_dir = os.path.abspath(args.ws_directory)
        if args.wsname=="None":
            wsname = None
        else:
            wsname = args.wsname
        '''
        if (not args.cfgfile) or (args.cfgfile=="None"):
            cfgfile = None
        else:
            cfgfile = args.cfgfile
        '''
        user = args.user
        #print("args = %s" % args)
        if (args.cache_only=='True') or (args.cache_only is True):
            cache_only = True
        else:
            cache_only = False
        if args.misc is not None:
            misc = args.misc
            misc_args = misc.split(",")
            params = {}
            for param in misc_args:
              keyval = param.split(":")
              if len(keyval)==2:
                params[keyval[0]] = keyval[1]
        if "cfgfile" in params:
            cfgfile = params["cfgfile"]
            if cfgfile=='None':
                cfgfile = None
        else:
            cfgfile = None
        LOGGER.info("Populating with cfgfile %s" % cfgfile)
        if cache_only:
            populate_cache(project, ip, bom, user, cache_dir, deliverable, cfgfile=cfgfile)
        else:
            populate_ws(project, ip, bom, user, ws_dir, wsname, cache_dir, deliverable, cfgfile=cfgfile)

    elif command == "delete":
        user_directory = args.directory

        #fail-safe to ensure sion doesn't accidentally delete stuff in release directory
        default_parameters = get_default_parameters()
        if is_pice_env():
            for family in default_parameters["PICE"]["immutable_disk"]["standard"]:
              default_immutable_disk = default_parameters["PICE"]["immutable_disk"]["standard"][family]

              if default_immutable_disk in os.path.abspath(user_directory):
                LOGGER.error("Sion cannot remove a directory from the official centralized directory.")
                sys.exit(1)

            for family in default_parameters["PICE"]["immutable_disk"]["cache"]:
              default_immutable_disk = default_parameters["PICE"]["immutable_disk"]["cache"][family]

              if default_immutable_disk in os.path.abspath(user_directory):
                LOGGER.error("Sion cannot remove a directory from the official centralized directory.")
                sys.exit(1)

        #can only delete directories with .sion file
        #ensure that sion can delete only directory created by sion
        sion_file = "%s/.sion" % user_directory
        sion_cache_file = "%s/.sion.cache" % user_directory
        if not (os.path.exists(sion_file) or os.path.exists(sion_cache_file)):
            LOGGER.error("Please ensure the given path is a directory created via sion populate command")
            sys.exit(1)
        if os.path.exists(sion_cache_file) :
            stat_info = os.stat(sion_cache_file)
        else :
            stat_info = os.stat(sion_file)
        uid = stat_info.st_uid
        owner = pwd.getpwuid(uid)[0]
        if owner != 'psginfraadm':
             LOGGER.error("It appears that .sion file in this directory is not created via sion populate. Please contact the tool administrator about this error.")
             sys.exit(1)

        # If no errors were caught, proceed to remove the directory
        os.chdir(user_directory)
        try:
            cmd = "chmod -R 440 *"
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)
            cmd = "dmx workspace delete -y --rmfiles"
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)
        except:
            cmd = "rm -rf %s" % user_directory
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)

        cmd = "rm -rf %s" % user_directory
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)

        LOGGER.info("%s has been deleted." % user_directory)

def setup_cache_dir(cache_dir):
  ''' Validate and prepare cache_dir for population.'''
  # Check is directory exists
  if not (os.path.isdir(os.path.abspath(cache_dir)) and os.path.exists(os.path.abspath(cache_dir))):
      LOGGER.error("Provided cache directory does not exist.")
      sys.exit(1)
  if not os.access(cache_dir, os.W_OK | os.X_OK):
      LOGGER.error("Provided cache directory is not writable.")
      sys.exit(1)

  ''' FOR NON-CENTRALIZED CACHE ONLY; Validate and prepare cache_dir for population.'''
  # Mark cache_dir if it is empty or unmarked and not centralized
  if os.listdir(cache_dir) == [] or (not os.path.isfile("%s/.sion.cache" % cache_dir) and not os.path.isfile("%s/.centralized.cache" % cache_dir)):
        # Mark the cache directory
        cmd = "touch %s/.sion.cache" % cache_dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        os.chmod("%s/.sion.cache" % cache_dir, 0o750)
        cmd = "touch %s/.sion" % cache_dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        os.chmod("%s/.sion" % cache_dir, 0o750)

  #Check that .storage exists; Create for local cache_dir if not
  global storage_path
  storage_path = "%s/.storage" % cache_dir
  if not os.path.exists(storage_path):
      open(storage_path, 'a').close()

  #check .locks dir exist; Create for local cache_dir if not
  lockdir = "%s/.locks" % cache_dir
  if not os.path.exists(lockdir):
      LOGGER.info("%s does not exist; Creating directory ..." % lockdir)
      os.mkdir(lockdir)
      cmd = "touch %s/.sion" % lockdir
      exitcode, stdout, stderr = run_command(cmd)
      if exitcode:
          print_errors(cmd, exitcode, stdout, stderr)


def populate_cache(project, ip, bom, user, cache_dir=None, deliverable=None, cfgfile=None):
    LOGGER.info("Populating cache %s ..." % cache_dir)
    os.system('gdp --help > /dev/null')

#    default_parameters = get_default_parameters()
    reference_dict = generate_project_family_reference()
    family = reference_dict[project]

    #if (cache_dir is None) or (cache_dir=='None'):
    #    print("Cache directory not provided; Deliverables will be populated to centralized cache located at %s ..." % cache_dir)
    #    cache_dir = default_cache_immutable_directory

    # Validate, set up and populate cache_dir
    if cache_dir is not None:
        setup_cache_dir(cache_dir)
    populate_result = populate_cache_by_deliverable(project, ip, bom, cache_dir, user, deliverable, cfgfile)
    return populate_result


def populate_ws(project, ip, bom, user, ws_dir=None, wsname=None, cache_dir=None, deliverable=None, cfgfile=None):
    LOGGER.info("Populating ws ...")

    if (wsname != 'None') and (wsname is not None):
        ws = '%s/%s' % (ws_dir, wsname)
    else:
        ws = "%s/%s/%s/%s" % (ws_dir, project, ip, bom)

    if not os.path.isdir(ws):
        print("Creating workspace directory prior to populate ...")
        try:
            os.mkdir(ws)
            os.chmod(ws, 0o777)
        except:
            LOGGER.error("Could not create workspace due to root directory permissions issues")

    target_dir = ws
    # Mark ws dir
    LOGGER.info("Marking workspace directory %s ..." % target_dir)
    cmd = "touch %s/.sion" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    cmd = "touch %s/.ws.sion" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    os.chmod("%s/.ws.sion" % target_dir, 0o770)

    if not cfgfile or cfgfile=='None':
        cfgfile = ''

    # Sync the user ws dir
    new_ws = dmx.dmxlib.workspace.Workspace(workspacepath=target_dir, project=project, ip=ip, bom=bom, preview=False)
    new_ws.create(ignore_clientname=True)
    os.chdir(target_dir)
    clientname = str(new_ws.get_workspace_attributes()['Workspace'])
    LOGGER.info("Created client %s" % clientname)
    new_ws.populate(cfgfile=cfgfile, verbose=True)

    # Get cache path
    reference_dict = generate_project_family_reference()
    family = reference_dict[project]
    default_parameters = get_default_parameters()
    default_cache_immutable_directory = default_parameters["PICE"]["immutable_directory"]["cache"][family]
    cache_dir = default_cache_immutable_directory

    # Create a symlink to recorded configuration file to potentially run additional populate in the future
    configs_path = os.path.abspath(os.path.join(cache_dir, project, ip, ".configs/"))
    bom_file = "%s/%s" % (configs_path, bom)
    local_bom_file_sl = "%s/.%s.%s.%s.configuration_record" % (target_dir, project, ip, bom)
    os.symlink(bom_file, local_bom_file_sl)


    #os.chmod(target_dir, 0o770)

    # Make populated workspace editable
    cmd = "chmod -R 770 %s" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)


def print_errors(cmd, exitcode, stdout, stderr):
    LOGGER.error("User = %s" % os.getenv('USER'))
    LOGGER.error("Hostname = %s" % os.getenv('HOSTNAME'))
    LOGGER.error("ARC Job ID = %s" % os.getenv('ARC_JOB_ID'))
    LOGGER.error("Command = %s" % cmd)
    LOGGER.error("Exitcode = %s" % exitcode)
    LOGGER.error("Stdout = %s" % stdout)
    LOGGER.error("Stderr = %s" % stderr)
    sys.exit(1)

def print_errors_pass(cmd, exitcode, stdout, stderr):
    LOGGER.info("User = %s" % os.getenv('USER'))
    LOGGER.info("Hostname = %s" % os.getenv('HOSTNAME'))
    LOGGER.info("ARC Job ID = %s" % os.getenv('ARC_JOB_ID'))
    LOGGER.info("Command = %s" % cmd)
    LOGGER.info("Exitcode = %s" % exitcode)
    LOGGER.info("Stdout = %s" % stdout)
    LOGGER.info("Stderr = %s" % stderr)

if __name__ == "__main__":
    #fmtstr = '%(levelname)s: [%(pathname)s:%(lineno)d]: %(message)s'
    fmtstr = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
    logging.basicConfig(format=fmtstr, level=logging.DEBUG)
    sys.exit(main())

