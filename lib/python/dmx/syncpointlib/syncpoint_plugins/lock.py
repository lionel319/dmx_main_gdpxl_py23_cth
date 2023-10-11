#!/usr/bin/env python
'''
Description: plugin for "syncpoint add"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import os
import textwrap
import logging
import tabulate

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, LIB)

from dmx.abnrlib.command import Command
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
from dmx.utillib.utils import get_altera_userid
import dmx.syncpointlib.syncpointlock_api

LOGGER = logging.getLogger(__name__)

class LockError(Exception):
    pass

class Lock(Command):
    '''plugin for "syncpoint lock"'''
    
    def __init__(self):
        pass


    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint lock"'''
        return 'Lock a give syncpoint. (only fclead can run this)'


    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Lock a given syncpoint. (Only fclead can run this)
                        
            Usage
            =====

                To Lock a given syncpoint
                -------------------------
                syncpoint lock --lock <syncpoint>

                To UnLock a given syncpoint
                ---------------------------
                syncpoint lock --unlock <syncpoint>

                To List all the locked syncpoints
                ---------------------------------
                syncpoint lock --list
    
                To List the lock history of all syncpoints
                ------------------------------------------
                syncpoint lock --history
            

            Note
            ====
            All the above options are exclusive (meaning the --lock/--unlock/--list/--history) will not 
            perform all in the same go with they are provided all at once.
            When more than one of the above mentioned options are provided, only one action will be carried out.
            The precedence of action to be carried out will be as follow:-
                --list, --history, --lock, --unlock.
            ...
            '''

        return textwrap.dedent(myhelp)


    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint lock" subcommand'''
        parser.add_argument('--lock', required=False,
            help='Lock the given Syncpoint.')
        parser.add_argument('--unlock', required=False,
            help='UnLock the given Syncpoint.')
        parser.add_argument('--list', required=False, action='store_true', default=False,
            help='List all the locked syncpoints.')
        parser.add_argument('--history', required=False, action='store_true', default=False,
            help='List the history of all locks.')
        parser.add_argument('--debug', default=False, action='store_true', 
            help='enable developer debugging')


    @classmethod
    def command(cls, args):
        '''syncpoint add command'''
        #get alteraid if we are in PICE env
        cls.userid = os.getenv("USER")
        cls.altera_userid = get_altera_userid(cls.userid)
        cls.sp = SyncpointWebAPI()
        

        fclead_list = cls.sp.get_users_by_role('fclead')
        admin_list = cls.sp.get_users_by_role('admin')
        LOGGER.debug("fclead_list: {}".format(fclead_list))
        LOGGER.debug("admin_list: {}".format(admin_list))
        if cls.altera_userid not in fclead_list + admin_list:
            LOGGER.error("Only fcleads can run this command. {}".format(logging.getLogger().getEffectiveLevel()))
            sys.exit(1)


        ''' 
        ### For Debugging/Testing 
        HOST = 'maria3512-us-fm-in.icloud.intel.com'
        PORT = 3306
        USERNAME = 'PSGINFRA1_so'
        PASSWORD = 'PSGINFRA1so' 
        DB = 'PSGINFRA1'
        cls.sl = dmx.syncpointlib.syncpointlock_api.SyncpointLockApi(host=HOST, port=PORT, username=USERNAME, password=PASSWORD, db=DB)
        cls.sll = dmx.syncpointlib.syncpointlock_api.SyncpointLockLogApi(host=HOST, port=PORT, username=USERNAME, password=PASSWORD, db=DB)
        '''
        cls.sl = dmx.syncpointlib.syncpointlock_api.SyncpointLockApi()
        cls.sll = dmx.syncpointlib.syncpointlock_api.SyncpointLockLogApi()

        cls.sl.connect()
        cls.sll.connect()


        if args.list:
            LOGGER.debug("--list action")
            locked_syncpoint_list = cls.sl.get_locked_syncpoints()
            LOGGER.info("Lock List\n{}".format(locked_syncpoint_list))
            sys.exit(0)

        elif args.history:
            LOGGER.debug('--history action')
            logs = cls.sll.get_logs()
            LOGGER.info("Lock History:-\n{}".format(tabulate.tabulate(logs)))
            sys.exit(0)

        elif args.lock or args.unlock:

            locked_syncpoint_list = cls.sl.get_locked_syncpoints()
            syncpoint_list = [x[0] for x in cls.sp.get_syncpoints()]

            if args.lock:
                ### Check if syncpoint exist
                if args.lock not in syncpoint_list:
                    LOGGER.debug("available syncpoints: {}".format(syncpoint_list))
                    LOGGER.error("syncpoint({}) not found.".format(args.lock))
                    sys.exit(1)

                ### Check if syncpoint is already locked 
                if args.lock in locked_syncpoint_list:
                    LOGGER.error("Syncpoint({}) was already locked previously.".format(args.lock))
                    sys.exit(1)
                        
                ### All validation passed. Now let's do the real locking.
                try:
                    cls.sl.lock(args.lock)
                    cls.sll.log(args.lock, cls.userid, 'lock')
                    LOGGER.info("Syncpoint ({}) successfully locked.".format(args.lock))
                except:
                    LOGGER.error("Command Failed!")
                    raise

            if args.unlock:
                ### Check if syncpoint is already locked 
                if args.unlock not in locked_syncpoint_list:
                    LOGGER.error("Syncpoint({}) was not locked previously.".format(args.unlock))
                    sys.exit(1)
                        
                ### All validation passed. Now let's do the real unlocking.
                try:
                    cls.sl.unlock(args.unlock)
                    cls.sll.log(args.unlock, cls.userid, 'unlock')
                    LOGGER.info("Syncpoint ({}) successfully unlocked.".format(args.unlock))
                except:
                    LOGGER.error("Command Failed!")
                    raise

        sys.exit(0)
