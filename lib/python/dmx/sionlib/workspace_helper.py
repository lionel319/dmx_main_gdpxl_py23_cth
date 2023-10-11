#!/usr/bin/env python
from __future__ import print_function
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

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.dmxlib.workspace import Workspace as DMXWorkspace
from dmx.abnrlib.flows.list import List
from dmx.abnrlib.flows.printconfig import PrintConfig
from dmx.abnrlib.flows.diffconfigs import DiffConfigs
from dmx.utillib.utils import is_pice_env
from dmx.sionlib.sion_plugins.decomposeconfig import DecomposeConfig
from joblib import Parallel, delayed
from dmx.sionlib.sion_utils import link_ws, generate_project_family_reference, process_boms, CacheResults, touch_sion_dirs, sync_ws_parallel, run_command, run_pre_populate_checks, get_headless_account, get_default_parameters, create_workspace, set_sion_logging, record_workspace_size

LOGGER = logging.getLogger()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cmd', '--command')
    parser.add_argument('-p', '--project')
    parser.add_argument('-v', '--variant')
    parser.add_argument('-l', '--libtype')
    parser.add_argument('-c', '--config')
    parser.add_argument('-dir', '--directory')
    parser.add_argument('-u', '--user')
    parser.add_argument('-cfg', '--cfgfile')
    parser.add_argument('-icmcmd', '--icm-command')
    parser.add_argument('-misc')

    args = parser.parse_args()
    command = args.command

    #preparing to run command
    if command == "populate":
        project = args.project
        variant = args.variant
        libtype = args.libtype
        config = args.config
        if args.directory == "None":
            # TODO: Throw error instead
            dir_to_populate = None
        else:
            dir_to_populate = os.path.abspath(args.directory)
        user = args.user
        if args.cfgfile == "None":
            cfgfile = None
        else:
            cfgfile = os.path.abspath(args.cfgfile)
        misc = args.misc
        misc_args = misc.split(",")
        tag = ''
        wsname = ''
        symlink_ws_dir = ''
        linkfiles = False
        params = {}
        for param in misc_args:
          keyval = param.split(":")
          if len(keyval)==2:
            params[keyval[0]] = keyval[1]

        if 'tag' in params:
          tag = params['tag']
        if 'wsname' in params:
          wsname = params['wsname']
        if 'symlink_ws_dir' in params:
          symlink_ws_dir = params['symlink_ws_dir']
        if 'linkfiles' in params:
          if params['linkfiles']=='True':
              linkfiles = True

        #tag, wsname, symlink_ws_dir = misc.split(",")
        LOGGER.info("ws_dir = %s" % symlink_ws_dir)
        LOGGER.info("wsname = %s" % wsname)
        if symlink_ws_dir is not '':
            populate_cache(project, variant, libtype, config, dir_to_populate, symlink_ws_dir, linkfiles, user, cfgfile, tag, wsname)
        else:
            populate(project, variant, libtype, config, dir_to_populate, user, cfgfile, tag, wsname)
    elif command == "delete":
        user_directory = os.path.abspath(args.directory)

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
        if owner != get_headless_account():
             LOGGER.error("It appears that .sion file in this directory is not created via sion populate. Please contact the tool administrator about this error.")
             sys.exit(1)

        # If no errors were caught, proceed to remove the directory
        os.chdir(user_directory)
        try:
            cmd = "find . -type f | xargs chmod 440"
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)
        except:
            pass
        try:
            cmd = "dmx workspace delete -y --rmfiles"
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)
            LOGGER.info("%s has been deleted." % user_directory)
        except:
            LOGGER.error("%s COULD NOT be deleted." % user_directory)
            pass
        try:
            cmd = "chmod -R 770 %s" % user_directory
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)
        except:
            pass
        try:
            cmd = "rm -rf %s" % user_directory
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)
        except:
            pass


        '''
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
        if owner != get_headless_account():
             LOGGER.error("It appears that .sion file in this directory is not created via sion populate. Please contact the tool administrator about this error.")
             sys.exit(1)

        # If no errors were caught, proceed to remove the directory
        cmd = "rm -rf %s" % user_directory
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)

        LOGGER.info("%s has been deleted." % user_directory)
        '''
    elif command == "list":
        project = None if args.project == 'None' else args.project
        variant = None if args.variant == 'None' else args.variant
        libtype = None if args.libtype == 'None' else args.libtype
        config = None if args.config == 'None' else args.config
        library = None
        props = None
        switches = None
        regex = None
        List(project, variant, libtype, library, config, switches, props, regex).run()
    elif command == "command":
        icm_command = " ".join(args.icm_command.split("=MaGiC="))

        LOGGER.info("%s" % icm_command)
        exitcode, stdout, stderr = run_command(icm_command)
        if exitcode or stderr:
            print(stderr)
        if stdout:
            print(stdout)
    elif command == "printconfig":
        project = args.project
        variant = args.variant
        config = args.config
        misc = args.misc
        show_simple_args, show_libraries_args = misc.split(',')
        show_simple = False
        if show_simple_args.split(":")[1] == 'True':
            show_simple = True
        show_libraries = False
        if show_libraries_args.split(":")[1] == 'True':
            show_libraries = True

        PrintConfig(project, variant, config, show_simple=show_simple, show_libraries=show_libraries).run()
    elif command == "diffconfigs":
        project = args.project
        variant = args.variant
        first_config = args.config
        misc = args.misc
        second_config = misc.split(":")[1]

        DiffConfigs(project, variant, first_config, second_config, None, None, True).run()

def setup_cache_dir(cache_dir):
  ''' Validate and prepare cache_dir for population.'''
  # Check is directory exists
  if not (os.path.isdir(os.path.abspath(cache_dir)) and os.path.exists(os.path.abspath(cache_dir))):
      LOGGER.error("Provided cache directory does not exist.")
      sys.exit(1)
  if not os.access(cache_dir, os.W_OK | os.X_OK):
      LOGGER.error("Provided cache directory is not writable by SION.")
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
      '''
      if (os.path.abspath(cache_dir) == os.path.abspath(default_cache_immutable_disk)) :
          LOGGER.error("%s does not exist" % storage_path)
          LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
          sys.exit(1)
      else :
      '''
      open(storage_path, 'a').close()

  #check .locks dir exist; Create for local cache_dir if not
  lockdir = "%s/.locks" % cache_dir
  if not os.path.exists(lockdir):
      '''
      if (os.path.abspath(cache_dir) == os.path.abspath(default_cache_immutable_disk)) :
          LOGGER.error("%s does not exist" % lockdir)
          LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
          sys.exit(1)
      else :
      '''
      LOGGER.info("%s does not exist; Creating directory ..." % lockdir)
      os.mkdir(lockdir)
      cmd = "touch %s/.sion" % lockdir
      exitcode, stdout, stderr = run_command(cmd)
      if exitcode:
          print_errors(cmd, exitcode, stdout, stderr)


def populate_cache(project, variant, libtype, config, cache_dir, ws_dir, linkfiles, user, cfgfile, tag, wsname) :
    LOGGER.info("Populating cache ...")
    default_parameters = get_default_parameters()

    # Get project-specific centralized paths
    if not os.path.isdir(os.getcwd()):
      os.chdir(cache_dir)
    reference_dict = generate_project_family_reference()
    family = reference_dict[project]
    default_cache_immutable_disk = default_parameters["PICE"]["immutable_disk"]["cache"][family]
    default_cache_immutable_directory = default_parameters["PICE"]["immutable_directory"]["cache"][family]
    default_ws_immutable_directory = default_parameters["PICE"]["central_cache_ws_directory"][family]

    # Validate, set up and populate cache_dir
    setup_cache_dir(cache_dir)
    populate_result = populate_cache_by_deliverable(project, variant, libtype, config, cache_dir, user, cfgfile)

    # Set user ws path for symlinking (this is not the cache)
    ws_dir = os.path.abspath(ws_dir)
    if wsname != 'None':
      # Skeleton sync the user ws dir
      if (os.path.abspath(ws_dir) != os.path.abspath(default_ws_immutable_directory)):
        wsname = "%s.TMP%s" % (wsname, os.environ['ARC_JOB_ID'])
      skeleton_ws_dir = '%s/%s' % (ws_dir, wsname)
    else:
      LOGGER.error("Workspace name was not provided OR failed to be generated.")

    # Skeleton sync the user ws dir
    LOGGER.info("Skeleton syncing user ws directory %s/%s ..." % (ws_dir, wsname))
    os.chdir(ws_dir)
    create_workspace(project, variant, libtype, config, ws_dir, get_headless_account(), cfgfile, wsname, reference_dict, skeleton=True, saveworkspace=False)
    # Mark ws dir
    LOGGER.info("Marking workspace directory %s ..." % skeleton_ws_dir)
    cmd = "touch %s/.sion" % skeleton_ws_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    cmd = "touch %s/.ws.sion" % skeleton_ws_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    os.chmod("%s/.ws.sion" % skeleton_ws_dir, 0o770)

    if (os.path.abspath(ws_dir) != os.path.abspath(default_ws_immutable_directory)):
        try:
            os.rename(skeleton_ws_dir, "%s.TMP" % skeleton_ws_dir.split('.TMP')[0])
        except:
            LOGGER.error("Could not rename internal temporary workspace %s to %s.\nPlease ensure that %s does not exists, and remove using sion delete if it does." % (skeleton_ws_dir, skeleton_ws_dir.split('.TMP')[0], skeleton_ws_dir.split('.TMP')[0]))
        try:
            skeleton_ws_dir = "%s.TMP" % skeleton_ws_dir.split('.TMP')[0]
        except:
            LOGGER.error("Could not rename temporary user workspace %s" % skeleton_ws_dir)

    os.chmod(skeleton_ws_dir, 0o770)
    LOGGER.info("Record of deliverables configs written to %s ..." % skeleton_ws_dir)

    # Record the complete list of deliverables@configs and what was populated
    deliverables_configs_filepath = "%s/.deliverables.configs" % (skeleton_ws_dir)
    synced_deliverables_configs_filepath = "%s/.deliverables.configs.synced" % (skeleton_ws_dir)
    with open(deliverables_configs_filepath, 'w') as f:
        f.write(populate_result.boms_for_print)
    with open(synced_deliverables_configs_filepath, 'w') as f:
        f.write(populate_result.synced_boms_for_print)

    if (os.path.abspath(ws_dir) == os.path.abspath(default_ws_immutable_directory)):
      # Create symbolic links to all deliverables@boms in cache_dir for non-local/centralized ws
      print("Linking %s to %s" % (skeleton_ws_dir, cache_dir))
      link_ws(cache_dir, skeleton_ws_dir, linkfiles)

    # Write protect centralized ws only; Prep local ws TMP dir for copy
    if (os.path.abspath(ws_dir) != os.path.abspath(default_ws_immutable_directory)):
      cmd = "chmod -R 770 %s" % skeleton_ws_dir
    else:
      cmd = "chmod -R 750 %s" % skeleton_ws_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)


def populate_cache_by_deliverable(project, variant, libtype, config, cache_dir, user, cfgfile) :
    final_results = CacheResults()

    if cache_dir.endswith('/'):
        cache_dir = cache_dir[:-1]

    # Check if psginfraadm is able to write into the user directory
    if not os.access(cache_dir, os.W_OK | os.X_OK):
        LOGGER.error('%s is not writable by sion. Please chmod the directory to 777.' % cache_dir)
        sys.exit(1)

    # Generate a list of all needed deliverables configs
    try:
       if libtype == 'None' :
         LOGGER.info("Decomposing configuration for %s/%s@%s" %(project, variant, config))
         decompose_deliverables_configs = DecomposeConfig(project = project, variant = variant, config = config, show_simple=True, show_composite=False)
       else :
         #TODO: This is unnecessary - to be removed;
         LOGGER.info("Decomposing configuration for %s/%s:%s@%s" %(project, variant, libtype, config))
         decompose_deliverables_configs = DecomposeConfig(project = project, variant = variant, config = config, libtype = libtype, show_simple=True, show_composite=False)
       deliverable_boms = decompose_deliverables_configs.run()
    except:
        LOGGER.error("Could not decompose configuration. Please ensure that the configuration exists and the project, variant (and optionally deliverable) parameters were supplied correctly.")
        sys.exit(1)

    # Populate cache from the list of all needed deliverables configs
    LOGGER.info("Populating cache directory by deliverable %s ..." % cache_dir)
    results = process_boms(deliverable_boms, cache_dir, user)

    # Append results
    final_results.boms_for_print+=results.boms_for_print
    final_results.synced_boms_for_print+=results.synced_boms_for_print
    final_results.dirs_to_remove.extend(results.dirs_to_remove)
    final_results.mutable_boms.extend(results.mutable_boms)

    # Check back on deferred items
    if results.deferred_boms :
        all_boms_processed = False
        while not all_boms_processed :
            results = process_boms(results.deferred_boms, cache_dir, user)
            final_results.boms_for_print+=results.boms_for_print
            final_results.synced_boms_for_print+=results.synced_boms_for_print
            final_results.dirs_to_remove.extend(results.dirs_to_remove)
            final_results.mutable_boms.extend(results.mutable_boms)
            if not results.deferred_boms:
                all_boms_processed = True
            else:
                time.sleep(30)

    # Clean up temporary directories
    #print("Deleting temporary directories:")
    #print(results.dirs_to_remove)
    for temp_dir in final_results.dirs_to_remove :
        print(("Cleaning up %s ...") % temp_dir)
        try:
            shutil.rmtree(temp_dir)
        except:
            cmd = "rm -rf %s" % temp_dir
            exitcode, stdout, stderr = run_command(cmd)
            #if exitcode:
            #    print_errors_pass(cmd, exitcode, stdout, stderr)
            pass

    # Return a list of synced and all needed deliverables configs
    return final_results

def populate(project, variant, libtype, config, user_directory, user, cfgfile, tag="", wsname="", skeleton=False, saveworkspace = True, checks = True) :
    default_headless_account = get_headless_account()
    default_parameters = get_default_parameters()
    #check if p/v/c exist or p/v/c/l exist
    if checks :
        run_pre_populate_checks(project, variant, libtype, config, user)

    #get the right directory
    if config.startswith('REL') or config.startswith('snap'):
        #for cache mode, user_directory = cache_dir ALWAYS
        if user_directory:
            user_directory = os.path.abspath(user_directory)
            if user_directory.endswith('/'):
                user_directory = user_directory[:-1]

            #check if psginfraadm is able to write into the user directory
            if not os.access(user_directory, os.W_OK | os.X_OK):
                LOGGER.error('%s is not writable by sion. Please chmod the directory to 770.' % user_directory)
                sys.exit(1)
            if wsname:
                target_directory = "%s/%s" % (user_directory,wsname)
            else:
                if libtype == 'None':
                    target_directory = "%s/%s/%s/%s" % (user_directory,project,variant,config)
                else:
                    target_directory = "%s/%s/%s/%s/%s" % (user_directory,project,variant,libtype,config)
            temp_directory = "%s.TEMP%s" % (target_directory, os.environ['ARC_JOB_ID'])

            build_workspace(project, variant, libtype, config, temp_directory, default_headless_account, cfgfile, wsname, skeleton, saveworkspace)

            #if the target directory exist, remove that directory, otherwise we cannot rename our temp dir to target dir
            if os.path.isdir(target_directory):
                cmd = "rm -rf %s" % target_directory
                exitcode, stdout, stderr = run_command(cmd)
                if exitcode:
                    print_errors(cmd, exitcode, stdout, stderr)
            LOGGER.info("Copying %s to %s" %(temp_directory, target_directory))
            os.rename(temp_directory, target_directory)
        else:
            # Get project-specific centralized paths
            reference_dict = generate_project_family_reference()
            family = reference_dict[project]
            default_immutable_disk = default_parameters["PICE"]["immutable_disk"]["standard"][family]
            default_immutable_directory = default_parameters["PICE"]["immutable_directory"]["standard"][family]
            if libtype == 'None':
                target_directory = "%s/%s/%s/%s" % (default_immutable_directory,project,variant,config)
            else:
                target_directory = "%s/%s/%s/%s/%s" % (default_immutable_directory,project,variant,libtype,config)

            temp_directory = "%s.TEMP%s" % (target_directory, os.environ['ARC_JOB_ID'])

            #Check that .storage exists
            global storage_path
            storage_path = "%s/.storage" % default_immutable_directory
            if not os.path.exists(storage_path):
                LOGGER.error("%s does not exist" % storage_path)
                LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                sys.exit(1)

            #check .locks dir exist
            lockdir = "%s/.locks" % default_immutable_directory
            if not os.path.exists(lockdir):
                LOGGER.error("%s does not exist" % lockdir)
                LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                sys.exit(1)
            if libtype == 'None':
                lockfile = "%s/%s.%s.%s" % (lockdir, project, variant, config)
            else:
                lockfile = "%s/%s.%s.%s.%s" % (lockdir, project, variant, libtype, config)
            #check if lockfile exist
            if os.path.exists(lockfile):
                if libtype == 'None':
                    LOGGER.error("%s/%s/%s is being populated at the moment. Please try again later." % (project,variant,config))
                else:
                    LOGGER.error("%s/%s/%s/%s is being populated at the moment. Please try again later." % (project,variant,libtype,config))
                sys.exit(1)
            else:
                open(lockfile, 'w')
                try:
                    build_workspace(project, variant, libtype, config, temp_directory, default_headless_account, None, None, skeleton, saveworkspace)
                except Exception as e:
                    LOGGER.error(e)
                    #if build workspace fails, remove the lock file
                    os.remove(lockfile)
                    sys.exit(1)
                try:
                    shutil.rmtree(target_directory)
                except:
                    pass
                os.rename(temp_directory, target_directory)
                record_workspace_size(target_directory, storage_path)
    else:
        if user_directory:
            if user_directory.endswith('/'):
                user_directory = user_directory[:-1]

            #check if psginfraadm is able to write into the user directory
            if not os.access(user_directory, os.W_OK | os.X_OK):
                LOGGER.error('%s is not writable by %s. Please chmod the directory to 770.' % (user_directory,default_headless_account))
                sys.exit(1)
            if wsname:
                target_directory = "%s/%s" % (user_directory,wsname)
            else:
                if libtype == 'None':
                    target_directory = "%s/%s/%s/%s" % (user_directory,project,variant,config)
                else:
                    target_directory = "%s/%s/%s/%s/%s" % (user_directory,project,variant,libtype,config)
            #LOGGER.info("target_directory = %s" % target_directory)
        else:
            LOGGER.error('Directory needs to be provided for mutable configuration')
            sys.exit(1)

        #append tag behind target directory path
        if tag!='None' and (tag is not None):
            target_directory = "%s_%s" % (target_directory, tag)

        temp_directory = "%s.TEMP%s" % (target_directory, os.environ['ARC_JOB_ID'])

        build_workspace(project, variant, libtype, config, temp_directory, default_headless_account, cfgfile, wsname, skeleton, saveworkspace)

        #if the target directory exist, remove that directory, otherwise we cannot rename our temp dir to target dir
        if os.path.isdir(target_directory):
            cmd = "rm -rf %s" % target_directory
            exitcode, stdout, stderr = run_command(cmd)
            if exitcode:
                print_errors(cmd, exitcode, stdout, stderr)

        LOGGER.info("Copying %s to %s" %(temp_directory, target_directory))
        os.rename(temp_directory, target_directory)

    #due to how altera_icm_release work to release data to /ice_rel/ by appending TEMP to workspace name
    #we have to remove TEMP away from cds.libicm since this file is created post sync trigger and takes in workspace name during creation
    fix_cds_libicm(target_directory)

    try:
        #similar to cdslib.icm, we have to fix saveworkspace json as well..
        fix_saveworkspace_json(target_directory)
    except:
        pass

    LOGGER.info("Content has been populated to: %s" % target_directory)

def build_workspace(project, variant, libtype, config, target_dir, user, configfile, wsname, skeleton=False, saveworkspace = True):
    #first, create workspace
    LOGGER.info("Creating workspace...")
    desc = "SITE: {} ARC_JOB: {}".format(os.environ['ARC_SITE'], os.environ['ARC_JOB_ID'])
    target_dir = os.path.realpath(target_dir)
    if libtype == 'None':
        #LOGGER.info("Libtype is None")
        cmd = 'pm workspace -c %s %s %s %s %s "%s"' % (project, variant, config, user, target_dir, desc)
    else:
        cmd = 'pm workspace -c -t %s %s %s %s %s %s "%s"' % (libtype, project, variant, config, user, target_dir, desc)
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    m = re.match(r'Workspace (\S+) created', stdout or '')
    workspace = m.group(1)

    #next, sync workspace
    LOGGER.info("Populating workspace...")
    #a little tricky for mutable config, we need to first perform skeleton sync on the workspace
    cmd = 'pm workspace -R %s' % workspace
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)

    #set logging to file after workspace is created as logfile needs to live in workspace root
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

    #create a .sion file in each directory so that sion knows this directory is created via populate command
    dirs = [x[0] for x in os.walk(target_dir)]
    #need to append directory not covered by os.walk
    if not wsname:
        if libtype:
            # for libtype
            dirs.append("{}".format(os.path.dirname(target_dir)))
        # for variant
        dirs.append("{}".format((os.path.dirname(os.path.dirname(target_dir)))))
        # for project
        dirs.append("{}".format(os.path.dirname(os.path.dirname(os.path.dirname(target_dir)))))

    for dir in dirs:
        cmd = "touch %s/.sion" % dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
    #then, to perform quick sync we need to chdir to the workspace dir
    os.chdir(target_dir)
    #now we can perform quick sync
    cfgfile = configfile
    yes_to_all = True
    force = None
    preview = None
    if not skeleton :
        # import from altera_abnr/3.4.4 as sion requires the latest update available in that resource
        from dmx.abnrlib.flows.workspace import Workspace
        sync = Workspace()
        try:
            sync.sync_action(cfgfile, yes_to_all, force, preview)
        except:
            # Due to the softlink issue with ICM, we have to perform sync twice
            if saveworkspace :
                sync.sync_action(cfgfile, yes_to_all, force, preview)
            else :
                LOGGER.info("COULD NOT SYNC DELIVERABLE DUE TO SYMLINKS.")
    reference_dict = generate_project_family_reference()
    family = reference_dict[project]
    default_parameters = get_default_parameters()
    default_immutable_disk = default_parameters["PICE"]["immutable_disk"]["standard"][family]
    default_immutable_directory = default_parameters["PICE"]["immutable_directory"]["standard"][family]

    default_immutable_directory_realpath = os.path.realpath(default_immutable_directory)
    #chmod to 770 if not rel, otherwise 750
    if default_immutable_directory_realpath in target_dir:
        cmd = "chmod -R 750 %s" % target_dir
    else:
        cmd = "chmod -R 770 %s" % target_dir
    if skeleton :
        cmd = "chmod -R 770 %s" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)

    # ensure user cannot remove .sion file (needed for sion delete to work properly)
    for dir in dirs:
        cmd = "chmod 750 %s/.sion" % dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)

    #then, run saveworkspace
    if saveworkspace :
        LOGGER.info("Running saveworkspace...")
        try:
            cmd = "saveworkspace --workspace %s" % target_dir
            exitcode, stdout, stderr = run_command(cmd)
            if libtype == 'None':
                cmd = "saveworkspace --workspace %s --every" % target_dir
                exitcode, stdout, stderr = run_command(cmd)
        except Exception as e:
            LOGGER.debug(e)
            pass

    # Do not remove workspace (DI221)
    '''
    #finally, remove workspace
    LOGGER.info("Cleaning up workspace...")
    cmd = 'pm workspace -R -x %s' % workspace
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    '''
    if not skeleton :
        # Modify workspace location to actual directory
        actual_dir = target_dir.split('.TEMP')[0]
        cmd = 'pm workspace -f %s %s' % (workspace, actual_dir)
        LOGGER.info(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)


def fix_saveworkspace_json(target_dir):
    cmd = "find %s -name info.json -maxdepth 3" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    jsons = stdout.split("\n")

    cmd = "find %s -name workspace.json -maxdepth 3" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    jsons = jsons + stdout.split("\n")

    tempname = ".TEMP" + os.environ['ARC_JOB_ID']
    for json in jsons:
        if json:
            if not os.access(json,os.W_OK):
                os.chmod(json,0o750)
            r = open(json)
            lines = r.readlines()
            w = open(json, 'w')
            for line in lines:
                if tempname in line:
                    new_line = line.split(tempname)
                    w.write(''.join(new_line))
                else:
                    w.write(line)
            r.close()
            w.close()

def fix_cds_libicm(target_dir):
    cds = target_dir + "/cds.libicm"
    if not os.path.isfile(cds):
        return
    if not os.access(cds,os.W_OK):
        os.chmod(cds,0o750)
    cds_reader = open(cds)
    lines = cds_reader.readlines()
    cds_writer = open(cds, 'w')

    tempname = ".TEMP" + os.environ['ARC_JOB_ID']
    for line in lines:
        if tempname in line:
            temp = line.split(tempname)
            cds_writer.write(''.join(temp))

    cds_reader.close()
    cds_writer.close()

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
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.INFO)
    sys.exit(main())

