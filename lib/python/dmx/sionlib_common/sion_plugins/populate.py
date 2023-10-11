#!/usr/bin/env python
'''
Description: plugin for sion "populate"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import os
import textwrap
import logging
import getpass
from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.sionlib.sion_utils import run_as_psginfraadm
default_immutable_disk = "/p/psg/falcon/sion"
default_immutable_directory = "/p/psg/falcon/sion"

class PopulateError(Exception): pass

class PopulateRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, project, variant, libtype, config, dir, cfgfile, yes_to_all, tag, wsname):
        self.user = os.getenv('USER')
        self.project = project
        self.variant = variant   
        self.libtype = libtype     
        self.config = config
        self.dir = dir
        self.cfgfile = cfgfile
        self.yes_to_all = yes_to_all
        self.tag = tag
        self.wsname = wsname
        #replace spaces with underscores
        if self.wsname:
            self.wsname = self.wsname.replace(" ","_")
        #tag must not have spaces, replace all spaces with underscores
        if self.tag:
            self.tag = self.tag.replace(" ","_")                 
        self.command = 'populate'

        if self.wsname and not self.dir:
            raise PopulateError("User local directory must be given together with wsname.")

        if self.dir:
            if default_immutable_disk in self.dir:
                self.dir = None

        if "REL" not in self.config and "snap" not in self.config:
            if self.dir:
                #path must be a directory
                if not os.path.isdir(self.dir):
                    raise PopulateError("%s is not a directory. Please provide an empty local directory path for sion to populate the data to" % self.dir)
                else:
                    if self.dir.endswith("/"):
                        self.dir = self.dir[:-1]
                    #if simple config, path is different                        
                    if self.libtype:
                        target_dir = "%s/%s/%s/%s/%s" % (self.dir, self.project, self.variant, self.libtype, self.config)
                    else:                                                
                        target_dir = "%s/%s/%s/%s" % (self.dir, self.project, self.variant, self.config)
            else:  
                raise PopulateError('Directory must be provided for sion to populate mutable configuration to.')
            
            #if tag is given, append tag behind the directory path
            if self.tag:
                target_dir = "%s_%s" % (target_dir, tag)

            #directory must be empty
            if os.path.isdir(target_dir):
                if os.listdir(target_dir):
                    if not self.yes_to_all:
                        self.LOGGER.warning("Directory %s is not empty, are you sure you want to overwrite the directory?" % target_dir)
                        ans = ""
                        while ans != 'y' and ans != 'n':
                            ans = raw_input("(y/n)?")
                        if ans.lower() == 'n':
                            raise PopulateError("Populate aborted")
                
            if not self.cfgfile:
                if not self.yes_to_all:
                    self.LOGGER.warning("You have not given a quick config file to sion.")
                    self.LOGGER.warning("Do you want sion to perform a full population on everything defined in %s/%s/%s?" % (self.project, self.variant, self.config))
                    ans = ""
                    while ans != 'y' and ans != 'n':
                        ans = raw_input("(y/n)?")
                    if ans.lower() == 'n':
                        raise PopulateError("Populate aborted")
        else:
            if self.tag:
                raise PopulateError("Population of immutable (REL/snap) configuration cannot be given a tag.")

            if self.dir:
                #path must be a directory
                if not os.path.isdir(self.dir):
                    raise PopulateError("%s is not a directory. Please provide an empty local directory path for sion to populate the data to" % self.dir)
                else:
                    if self.dir.endswith("/"):
                        self.dir = self.dir[:-1]
                    #if simple config, path is different                        
                    if self.libtype:
                        target_dir = "%s/%s/%s/%s/%s" % (self.dir, self.project, self.variant, self.libtype, self.config)
                    else:                                                
                        target_dir = "%s/%s/%s/%s" % (self.dir, self.project, self.variant, self.config)

                    #directory must be empty
                    if os.path.isdir(target_dir):
                        if os.listdir(target_dir):
                            if not self.yes_to_all:
                                self.LOGGER.warning("Directory %s is not empty, are you sure you want to overwrite the directory?" % target_dir)
                                ans = ""
                                while ans != 'y' and ans != 'n':
                                    ans = raw_input("(y/n)?")
                                if ans.lower() == 'n':
                                    raise PopulateError("Populate aborted")
                
                    if not self.cfgfile:
                        if not self.yes_to_all:
                            self.LOGGER.warning("You have not given a quick config file to sion.")
                            self.LOGGER.warning("Do you want sion to perform a full population on everything defined in %s/%s/%s?" % (self.project, self.variant, self.config))
                            ans = ""
                            while ans != 'y' and ans != 'n':
                                ans = raw_input("(y/n)?")
                            if ans.lower() == 'n':
                                raise PopulateError("Populate aborted")
            else:
                if self.libtype:
                    target_dir = "%s/%s/%s/%s/%s" % (default_immutable_directory,self.project,self.variant,self.libtype,self.config)
                else:
                    target_dir = "%s/%s/%s/%s" % (default_immutable_directory,self.project,self.variant,self.config)

                if os.path.exists(target_dir):
                    self.LOGGER.info("%s is already populated." % (target_dir))
                    sys.exit(0)
                                            
    def run(self):
        ret = 1

        misc = "tag:%s,wsname:%s" % (self.tag, self.wsname)
        ret = run_as_psginfraadm(project = self.project, variant = self.variant, libtype = self.libtype, config = self.config, dir = self.dir, command = self.command, user = self.user, cfgfile = self.cfgfile, misc = misc)

        return ret

class Populate(Command):
    '''plugin for "sion populate"'''
    
    LOGGER = logging.getLogger(__name__)
        
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
        Sion populate allows user to populate ICM data based on project/variant/configuration to a local directory.
        This data is read-only and will be locked with appropriate UNIX group according to ICM protect table.
        There are 2 types of configurations:
        1. Immutable configuration
           Sion will populate data based on immutable configuration to a shared local directory defined by sion.
        2. Mutable configuration
           Sion will populate data based on mutable configuration to a shared local directory defined by sion. User may also provide an empty local directory path for sion to populate the data to.

        For more information, https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/SynchronizingICMDataOnNetwork.
        Sion will allow user to choose which variant/libtype/file to sync. Sion will make use of quick tool to do so, specifically using quicksync.cfg. To understand more about quick config file, please read the bottom section of this help menu.
                        
        Usage
        =====
        sion populate -p <project> -v <variant> -c <immutable composite configuration>
        Populates immutable ICM data based on project/variant/configuration to shared local directory defined by sion

        sion populate -p <project> -v <variant> -c <mutable configuration>
        Populates mutable ICM data based on project/variant/configuration to shared local directory defined by sion
                            
        sion populate -p <project> -v <variant> -c <mutable configuration> -d <user's local path>
        Populates mutable ICM data based on project/variant/configuration to user's local path

        sion populate -p <project> -v <variant> -l <libtype> -c <immutable simple configuration>
        Populates immutable ICM data based on project/variant/libtype/configuration to release directory defined by sion

        sion populate -p <project> -v <variant> -l <libtype> -c <mutable simple configuration>
        Populates mutable ICM data based on project/variant/libtype/configuration to shared local directory defined by sion

        sion populate -p <project> -v <variant> -l <libtype> -c <mutable simple configuration> -d <user's local path>
        Populates mutable ICM data based on project/variant/libtype/configuration to user's local path
    
        sion populate -p <project> -v <variant> -l <libtype> -c <immutable simple configuration> -d <user's local path> -cfg <quick cfg file>
        Populates immutable ICM data based on project/variant/libtype/configuration to user's defined directory, will consult quick cfg file to decide which dirs/files to sync 

        sion populate -p <project> -v <variant> -l <libtype> -c <mutable simple configuration> -d <user's local path> -cfg <quick cfg file>
        Populates mutable ICM data based on project/variant/libtype/configuration to shared local directory defined by sion, will consult quick cfg file to decide which dirs/files to sync 
    
        sion populate -p <project> -v <variant> -l <libtype> -c <mutable simple configuration> -d <user's local path> -cfg <quick cfg file>
        Populates mutable ICM data based on project/variant/libtype/configuration to user's local path, will consult quick cfg file to decide which dirs/files to sync               

        Example
        =======
        $sion populate -p i14socnd -v ar_lib -c REL3.0 
        Sion will populate the content to /ice_rel/readonly/i14socnd/ar_lib/REL3.0.

        $sion populate -p i14socnd -v ar_lib -c REL3.0 -l rtl
        This command will populate the simple configuration REL3.0 for the libtype rtl to /ice_rel/readonly/i14socnd/ar_lib/rtl/REL3.0.

        $sion populate -p i14socnd -v ar_lib -c dev
        The command above will populate dev configuration content to /ice_dev/readonly/$USER/i14socnd/ar_lib/dev
        Data populated by sion will not be able to be removed by user, user has to run delete command to remove the data

        $sion populate -p i14socnd -v ar_lib -c dev -dir /home/$USER/test
        In order to populate a mutable configuration, user needs to give his/her own local directory path for sion to copy the data to. 
        The command above will populate dev configuration content to /home/$USER/test/i14socnd/ar_lib/dev. 
        Data populated by sion will not be able to be removed by user, user has to run delete command to remove the data.

        $sion populate -p i14socnd -v ar_lib -c dev -l rtl
        Similar to the previous command, except this command populates rtl simple configuration to /ice_dev/readonly/$USER/i14socnd/ar_lib/rtl/dev.

        $sion populate -p i14socnd -v ar_lib -c dev -l rtl -dir /home/$USER/test
        Similar to the previous command, except this command populates rtl simple configuration.
        
        $sion populate -p i14socnd -v ar_lib -c REL4.0ND5revA--SECTOR__15ww455a -d /home/$USER/test -cfg /home/$USER/quicksync.cfg
        This command populates i14socnd/ar_lib/REL4.0ND5revA--SECTOR__15ww455a based on the rules defined in quicksync.cfg to /home/$USER/test/i14socnd/ar_lib/rtl/REL4.0ND5revA--SECTOR__15ww455a.

        $sion populate -p i14socnd -v ar_lib -c dev -l rtl -cfg /home/$USER/quicksync.cfg
        This command populates i14socnd/ar_lib/dev based on the rules defined in quicksync.cfg.

        $sion populate -p i14socnd -v ar_lib -c dev -dir /home/$USER/test -cfg /home/$USER/quicksync.cfg
        This command populates i14socnd/ar_lib/dev based on the rules defined in quicksync.cfg.
         
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
            help='ICM Project')
        parser.add_argument('-v', '--variant', metavar='variant', required=True,
            help='ICM Variant')
        parser.add_argument('-l', '--libtype', metavar='libtype',
            help='ICM Libtype')
        parser.add_argument('-c', '--config', metavar='config', required=True,
            help='ICM Configuration')
        parser.add_argument('-d', '--dir', metavar='user\'s local directory',
            help='User\'s local directory')
        parser.add_argument('-cfg', '--cfgfile', metavar='quick config file',
            help='Quick config file to facilitate in partial population of read-only data')
        parser.add_argument('-y', '--yes-to-all', action='store_true',
            help='Yes to all options')
        parser.add_argument('--tag', metavar='tag', 
            help='Adds a tag as suffix to the directory being populated. Only mutable configuration can be given a tag.')
        parser.add_argument('--wsname', metavar='workspace-name',
            help='Allow user to rename the workspace as they like. By default workspace would be in the form of user_local_directory/project/variant/config or user_local_directory/project/variant/libtype/config. By setting this variable, workspace would be in the form of user_local_directory/wsname. Argument -d needs to be given together with --wsname.')

    @classmethod
    def command(cls, args):
        '''sion populate command'''
        
        project = args.project
        variant = args.variant
        libtype = args.libtype
        config = args.config
        dir = args.dir
        cfgfile = args.cfgfile
        yes_to_all = args.yes_to_all
        tag = args.tag
        wsname = args.wsname
        
        ret = 1
        runner = PopulateRunner(project, variant, libtype, config, dir, cfgfile, yes_to_all, tag, wsname)
        ret = runner.run()
                 
        sys.exit(ret)
        
