#!/usr/bin/env python
'''
Description: plugin for sion "populate"

Author (classic sion): Kevin Lim Khai - Wern
Author (caching sion): Natalia Baklitskaya
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import os
import textwrap
import logging
import getpass
import datetime
import shutil
import json

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, ROOTDIR)

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args, is_pice_env, get_ww_details, run_command
from dmx.sionlib.sion_utils import run_as_headless_user_cache_mode
    
LOGGER = logging.getLogger(__name__)

class PopulateError(Exception): pass

class PopulateRunner(Runner):

    def __init__(self, project, variant, libtype, config, dir, cfgfile, yes_to_all, wsname):
        self.user = os.getenv('USER')
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.config = config
        self.dir = dir
        self.cfgfile = cfgfile
        self.yes_to_all = yes_to_all
        self.wsname = wsname

        #replace spaces with underscores
        if self.wsname:
            self.wsname = self.wsname.replace(" ","_")
        self.command = 'populate'

        # Temporary measure to enable sionlib in legacy env
        # To avoid collision of dmx/sionlib with altera_sion
        if not is_pice_env():
            if not self.dir:
                raise PopulateError('User local directory (-d) must be provided')

        if self.wsname and not self.dir:
            raise PopulateError("User local directory must be given together with wsname.")

        if self.dir:
            #path must be a directory
            if not os.path.isdir(self.dir):
                raise PopulateError("%s is not a directory. Please provide an empty local directory path for sion to populate the data to" % self.dir)
            else:
                if self.dir.endswith("/"):
                    self.dir = self.dir[:-1]
                #directory must be empty - Adjust - already populated directory will be skipped for REL/snap type boms
                #if self.cfgfile and self.centralized_cache :
                #    raise PopulateError("quicksync.cfg files are not allowed in the centralized cache area. Please provide a cache path using --cache_path argument, or remove the quicksync.cfg file argument and try again.")
                if not self.cfgfile:
                    #raise PopulateError("quicksync.cfg files are not allowed in for caching SION. Please remove the quicksync.cfg file argument and try again.")
                    if not self.yes_to_all:
                        LOGGER.warning("You have not given a quick config file to sion.")
                        LOGGER.warning("Do you want sion to perform a full population on everything defined in %s/%s/%s?" % (self.project, self.variant, self.config))
                        ans = ""
                        while ans != 'y' and ans != 'n':
                            ans = raw_input("(y/n)?")
                        if ans.lower() == 'n':
                            raise PopulateError("Populate aborted")

    def run(self):
        ret = 1
        #misc = "tag:%s,wsname:%s," % (self.tag, self.wsname)
        misc = "cfgfile:%s" % (self.cfgfile)
        ret = run_as_headless_user_cache_mode(command =  self.command, project = self.project, ip = self.variant, deliverable = self.libtype, bom = self.config, cache_dir = None, ws_dir = self.dir, wsname = self.wsname, user = self.user, misc = misc)
        return ret

class Populate(Command):
    '''plugin for "sion populate"'''

    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "sion populate"'''
        return 'Populates ICM data into a local directory'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Description
        ===========
        Sion populate allows user to populate ICM data based on ICM project/variant/configuration to a local directory.

        Immutable ICM libtype configurations included in top level config will be populated to centralized cache, or local cache (if specified).
        This data is read-only and will be locked with appropriate UNIX group according to ICM protect table.
        Symlinks will be created from user's ws directory to the files in the centralized cache for immutable libtype configs.

        Mutable ICM libtype configurations included in top level config will be synced directly to user's ws directory.

        Sion will allow a user to choose which variant and libtype combinations to sync for all libtype-level sub-configurations.
        Sion will allow a user to choose which variant/libtype/file to sync for libtype-level mutable sub-configurations. Sion will make use of quick tool to do so, specifically using quicksync.cfg.
        To understand more about quick config file, please read the bottom section of this help menu.

        For more information, https://wiki.ith.intel.com/display/tdmaInfra/SION+-+Creating+a+read-only+workspace

        Usage
        =====
        sion populate -p <project> -v <variant> -c <immutable composite configuration> -d <user's local path>
          All libtype configurations are immutable and will be populated to centralized cache.
          A user workspace will be created and symlinks will be created within it to files in centralized cache.

        sion populate -p <project> -v <variant> -c <mutable configuration> -d <user's local path>
          All immutable libtype configurations will be populated to centralized cache.
          A user workspace will be created and symlinks will be created within it to files in centralized cache.
          All mutable libtype configurations will be populated directly to user's workspace.

        sion populate -p <project> -v <variant> -c <immutable composite configuration> -d <user's local path> -cfg <quicksync.cfg file>
          All libtype configurations are immutable and will be populated to centralized cache.
          A user workspace will be created and symlinks will be created within it to files in centralized cache for immutable libtype configurations.
          Quick cfg file will be used to filter which variant and libtype configurations will be cached and symlinked for user's workspace.

        sion populate -p <project> -v <variant> -c <mutable configuration> -d <user's local path> -cfg <quicksync.cfg file>
          All immutable libtype configurations will be populated to centralized cache.
          A user workspace will be created and symlinks will be created within it to files in centralized cache for immutable libtype configurations.
          Quick cfg file will be used to filter which variant and libtype configurations will be cached and symlinked for user's workspace.
          All mutable libtype configurations will be filtered according to quick cfg file, including at file level, and populated directly to user's workspace.



        QUICK CONFIG HELP DESCRIPTION
        =============================
        Below are the help descriptions extracted from quick tool:
        '''
        from dmx.plugins.workspacesync import WorkspaceSync
        help = WorkspaceSync.extra_help()
        myhelp = myhelp + help
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "sion populate" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=True,
            help='ICM project')
        parser.add_argument('-v', '--variant', metavar='variant', required=True,
            help='ICM variant')
        parser.add_argument('-l', '--libtype', metavar='libtype',
            help='DEPRECATED\nAll workspaces must be created at ICM variant level.\nTo limit your workspace to a single libtype:\n  1. Create an ICM variant level configuration\n  2. Use this configuration and variant name to create your workspace')
        parser.add_argument('-c', '--config', metavar='config', required=True,
            help='ICM variant/IP-level configuration')
        parser.add_argument('-d', '--dir', metavar='user\'s local directory', required=True,
            help='User\'s local directory path for a SION workspace. This argument is required.')
        parser.add_argument('-cfg', '--cfgfile', metavar='quick config file',
            help='Quick config file to facilitate in partial population of mutable data;\nNOTE: File-level filtering will only be applied to mutable libtype configuration/bom, such as dev or WIP.')
        parser.add_argument('-y', '--yes-to-all', action='store_true',
            help='Yes to all options')
        parser.add_argument('--cache', action='store_true',
            help='DEPRECATED')
        parser.add_argument('--linkfiles', action='store_true',
            help='DEPRECATED')
        parser.add_argument('--wsname', metavar='workspace-name',
            help='Allows user to rename the workspace as they like. If no wsname is provided, SION will populate the workspace to user_dir_path/project/variant/configuration/.\nBy setting this variable, workspace would be in the form of user_dir_path/wsname.')
        parser.add_argument('--cache_path', metavar='cache-path',
            help='DEPRECATED')

    @classmethod
    def command(cls, args):
        '''sion populate command'''

        project = args.project
        variant = args.variant
        libtype = args.libtype
        config = args.config
        dir = args.dir
        if args.cfgfile:
            cfgfile = os.path.abspath(args.cfgfile)
        else:
            cfgfile = args.cfgfile
        yes_to_all = args.yes_to_all
        wsname = args.wsname

        ret = 1

        print("--- RUNNING IN CACHE MODE ---")
        print("!!! CAUTION: Work In Progress; Automatic garbage collection is not in place. Please exercise caution when caching very large workspaces. !!!")
        print("Provided workspace directory: %s" % dir)


        if dir is None:
            raise PopulateError("Please use the -d/--dir argument to provide an empty directory path for sion to create your workspace in.")
        elif not (os.path.isdir(dir) and os.path.exists(dir)):
            raise PopulateError("%s is not a directory. Please provide a directory path for sion to create your workspace in." % dir)

        if dir.endswith("/"):
            dir = dir[:-1]

        if not os.access(dir, os.W_OK):
            print("%s is not writeable; Attempting to change permissions ..." % dir)
            try:
                os.chmod(dir, 0o770)
            except:
                raise PopulateError("%s is not writeable by SION.\nPlease run 'chmod 770 %s' to populate your worskspace to this location." % dir, dir)

        # Define complete workspace root path
        if wsname is not None:
            ws = '%s/%s' %  (dir, wsname)
        else:
            if libtype is not None:
                raise PopulateError("All workspaces must be created at IP/Variant level.\nTo limit your workspace to a single libtype:\n  1. Create an IP/Variant level configuration/bom\n  2. Use this configuration/bom and IP name to create your workspace")
            ws = "%s/%s/%s/%s" % (dir, project, variant, config)
            print("Creating workspace directory prior to populate ...")
            if not os.path.isdir("%s/%s" % (dir, project)):
                os.mkdir("%s/%s" % (dir, project))
            if not ((os.stat("%s/%s" % (dir, project)).st_mode & 0777) == 0777):
                try:
                    os.chmod("%s/%s" % (dir, project), 0o777)
                except:
                    print("Could not change permissions of %s/%s" %  (dir, project))
                    pass
            if not os.path.isdir("%s/%s/%s" % (dir, project, variant)):
                os.mkdir("%s/%s/%s" % (dir, project, variant))
            try:
                os.chmod("%s/%s/%s" % (dir, project, variant), 0o777)
            except:
                pass
            print("Workspace name not provided; Workspace will be populated to %s ..." % ws)

        # Check if workspace already exists; Abort if yes.
        LOGGER.info("Checking if workspace dir already exists: {}".format(ws))
        ws = os.path.abspath(ws)
        if os.path.isdir(ws) :
            raise PopulateError("%s workspace already exists.\nPlease provide an new workspace name or use the 'sion delete' command to delete the existing workspace." % ws)


        # Populate workspace
        runner = PopulateRunner(project, variant, libtype, config, dir, cfgfile, yes_to_all, wsname)
        ret = runner.run()
        if ret!=1:
            print('...')
            print("READ-ONLY workspace created at: %s" % ws)
        else:
            print('...')
            print("Could not create workspace %s. Please see errors above." % ws)

        sys.exit(ret)
