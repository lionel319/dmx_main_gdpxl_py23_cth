'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/icm.py#10 $
$Change: 7730228 $
$DateTime: 2023/08/07 01:17:50 $
$Author: lionelta $

Description:  Altera Build 'N Release
              dmx.abnrlib.icm : utility functions for interfacing with ICManage commands

Author: Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''

## @addtogroup dmxlib
## @{

from builtins import chr
from builtins import map
from builtins import str
from builtins import object
import re
import subprocess
from getpass import getuser
from datetime import datetime
import logging
import threading
import os
import signal
import inspect
from datetime import date, timedelta
import functools
import re
import marshal
import sys
'''
if sys.version_info[0] > 2:
    from past.translation import autotranslate
    autotranslate(['which'])
import which
'''
from multiprocessing import Lock
import time
import json
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

from dmx.utillib.decorators import memoized
from dmx.abnrlib.command import Command
from dmx.utillib.utils import *
from dmx.abnrlib.namevalidator import ICMName
import dmx.utillib.utils
import dmx.utillib.contextmgr

# Disable line too long message
# pylint: disable=C0301,E1103

LOGGER = logging.getLogger(__name__)

class Error(Exception): pass
class UnparsableOutputError(Error): pass
class UnreleasedLibraryError(Error): pass
class ICManageError(Exception): pass
class BadNameError(Exception): pass
class LibraryAlreadyExistsError(Error): pass
class ConfigDoesNotExistError(Exception): pass
class LoginError(Exception): pass
class AllRevisionsAlreadyIntegratedError(Exception): pass
class UndefinedLibtypeError(Exception): pass
class InvalidConfigNameError(Exception): pass


# Due to the user switching and login/logout required when creating
# snaps we need to protect the final process of creating the snap
# when running with multiple processes
SNAP_SAVE_LOCK = Lock()

#TODO
@memoized
def is_armored(version):
    '''
    Returns True if version is an IC Manage version where
    armor is used

    :param version: The IC Manage client tool version
    :type version: int
    :return: Boolean indicating whether or not this is an armored version
    :rtype: bool
    '''
    ret = False

    if version > 28507:
        ret = True

    return ret

#TODO
@memoized
def translate_release(release):
    '''
    In their infinite wisdom IC Manage decided to use the term #ActiveDev/#ActiveRel
    everywhere EXCEPT for the pm command, which throws an error if you
    use #ActiveDev or #ActiveRel. The pm equivalent is #dev and #rel.

    This function translates releases into a pm friendly format.

    :param release: The IC Manage library release name
    :type release: str
    :return: The pm friendly translation of release
    :rtype: str
    '''
    if release == '#ActiveDev':
        release = '#dev'
    elif release == '#ActiveRel':
        release = '#rel'

    return release

#TODO
@memoized
def convert_altera_config_name_to_icm(altera_name):
    '''
    Converts an Altera style configuration name into a 
    dict describing the IC Manage objects
    Altera naming convention: <project>/<variant>[:libtype]@<config>

    :param altera_name: The Altera formatted configuration name
    :type altera_name: str
    :return: Dictionary of the components of the Altera formatted name (project, variant, config and optional libtype)
    :rtype: dict
    :raises: BadNameError
    '''
    ret = dict()

    if not re.search('^(\w+)/(\w+)@([\w\.-])+$', altera_name) and not re.search('^(\w+)/(\w+):(\w+)@([\w\.-]+)$', altera_name):
        raise BadNameError("{0} is in an invalid format. Valid formats are: <project>/<variant>@<config> or <project>/<variant>:<libtype>@<config>".format(
            altera_name
        ))

    # First get the config name
    (tree, config) = altera_name.split('@')
    ret['config'] = config

    # Now split the project and variant
    (project, remainder) = tree.split('/')
    ret['project'] = project

    # Finally we need to figure out if this is a simple or
    # composite configuration. If there's a : it's simple
    if ':' in remainder:
        (variant, libtype) = remainder.split(':')
        ret['variant'] = variant
        ret['libtype'] = libtype
    else:
        ret['variant'] = remainder

    return ret

#TODO
def get_rel_config_regex_start(milestone='', thread=''):
    '''
    Builds a regex that will match a REL config just by the start of its name
    REL[milestone][thread]

    :param milestone: Optional - The Altera milestone
    :type milestone: str
    :param thread: Optional - The Altera thread
    :type thread: str
    :return: A regex
    :type return: str
    '''
    base_regex_str = '^REL'
    if milestone:
        base_regex_str += '{}'.format(milestone)
    else:
        base_regex_str += '\d\.\d'

    if thread:
        base_regex_str += '{}'.format(thread)
    else:
        base_regex_str += '\w+'

    return base_regex_str

#TODO
def get_rel_config_regex_end():
    '''
    Builds a regex to match the date/work week section at the end
    of a REL config

    :return: regex str
    :type return: str
    '''
    return '__([\d]{2})ww([\d]{3})([a-z])'

#TODO
def get_last_REL_from_matches(matches):
    '''
    Searches a list of regex matches and returns the name of the newest configuration
    The match must have three groups matching the year, ww and letter information
    from a REL configuration: eg. 14ww123a

    :param matches: List of regex match objects
    :type matches: list
    :return: The name of the newest configuration
    :type return: str
    '''
    # We have three points of comparison for REL configurations
    # The year, the working week plus working day, and a one letter
    # suffix
    # We want to store the latest REL as we iterate but we don't
    # want to be constantly decomposing these parts from the REL
    # so they have their own latest trackers
    latest_rel = ''
    latest_year = 0
    latest_ww = 0
    latest_letter = ''

    for match in matches:
        update_latest = False
        year = match.group(1)
        ww = match.group(2)
        letter = match.group(3)

        # First we only want to consider RELs whose year
        # is greater than or equal to the latest
        if year > latest_year:
            # If the year is greater we always update
            update_latest = True
        elif year == latest_year:
            # The year is equal, what about the work week?
            if ww > latest_ww:
                # If the ww is greater then we always update
                update_latest = True
            elif ww == latest_ww and letter > latest_letter:
                # If everything else is equal only update if the letter is greater
                update_latest = True

        if update_latest:
            latest_rel = match.string
            latest_year = year
            latest_ww = ww
            latest_letter = letter

    return latest_rel

class ICMMemoizer(object):
    '''
    IC Manage specific memoizer with support
    for cache reset
    Shamelessly stolen from:
    http://stackoverflow.com/questions/4431703/python-resettable-instance-method-memoization-decorator
    '''

    def __init__(self, func):
        self.func = func
        self.cache = {}
        functools.wraps(func)(self)

    def __call__(self, *args, **kwargs):
        key = str(args) + str(kwargs)
        try:
            return self.cache[key]
        except KeyError:
            value = self.func(*args, **kwargs)
            self.cache[key] = value
            return value
        except TypeError:
            # Better to no cache than blow up
            return self.func(*args, **kwargs)

    def __repr__(self):
        '''
        Return the function's docstring
        '''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''
        Support instance methods
        '''
        fn = functools.partial(self.__call__, obj)
        fn.reset = self._reset
        return fn

    def _reset(self):
        self.cache = {}

def get_marshal_output(cmd, err_level=None):
    '''
    Get marshallable result from a shell command execution.
    Suitable commands are 'icmp4 -G ...'.
    Set err_level to override the default severity for ICMP4 record validation.
    Return list of records.
    
    Perform icmp4 help.
    >>> get_marshal_output("icmp4 -G help") #doctest: +ELLIPSIS
    [{'code': 'info', 'data':...}]
    '''
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    records = []
    try:
        while True:
            record = marshal.load(process.stdout)
            if err_level != None:
                check_record_for_icmp4_error(record, cmd, err_level)
            else:
                check_record_for_icmp4_error(record, cmd)
            records.append(record)
    except EOFError:
        return records
    finally:
        process.stdout.close()

def check_record_for_icmp4_error(record, cmd, severity=2):
    ''' 
    Checks a marshalled record from 'icmp4 -G', for potential errors and
    andle them by raising Error with embedded information from the record.
    Only checks for errors where error severity is greater than given severity.
    
    ICMP4 command issue that meets severity will raise RuntimeError.
    >>> cmd = "icmp4 -G add no_such_file"
    >>> process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    >>> check_record_for_icmp4_error(marshal.load(process.stdout), cmd, 1) #doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    RuntimeError: running icmp4 command 'icmp4 -G add no_such_file': ...
    '''
    if 'code' in record and 'severity' in record:
        rec_severity = int(record['severity'])
        if record['code'] == "error" and rec_severity > severity:
            err = record.get("data", "unknown")
            raise RuntimeError("running icmp4 command '%s': %s" % (cmd, err))

def get_profile_file_name():
    '''
    Returns the file name for the profile file
    :return: Profile file name
    :rtype: str
    '''
    return 'ICManageCLI.profiler.{0}'.format(os.getpid())

def log_runtime(command, start, end):
    '''
    Logs the runtime in seconds of command to ICManageCLI.profiler.<pid>
    in the current working directory.

    :param command: The command that was run.
    :type command: list
    :param start: The start time
    :type start: datetime
    :param end: The end time
    :type: datetime
    '''
    delta = end - start
    tmpfile = get_profile_file_name()
    with open(tmpfile, 'a') as p:
        p.write('{0}:{1}\n'.format(' '.join(command), delta.total_seconds()))
    return tmpfile

#
# The run_*_command functions are used to call out to the IC Manage
# command line
# You always want to run read-only calls
# write calls are only made if preview=False
# __run_command should not be called directly
#
def run_subcommand(command, stdin=None, timeout=None, retried=0, maxtry=5, delay_in_sec=10, regex_list=None, retry=False, env=None):
    '''
    Runs command and returns the exitcode, stdout and stderr

    :param command: The command to run in a list
    :type command: list
    :param stdin: Optional stdin - file descriptor, string, etc.
    :type stdin: None or str
    :param timeout: optional timeout for the command in seconds.
    :type timeout: None or int
    :return: Tuple of exitcode, stdout and stderr
    :rtype: tuple
    '''
    kill_flag = threading.Event()
    if regex_list is None:
        regex_list = get_icm_error_list()

    def _kill_process_after_a_timeout(pid):
        '''
        Helper for killing the process
        '''
        os.kill(pid, signal.SIGTERM)
        kill_flag.set()  # Tells the main routine we had to kill
        return

    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    if timeout is not None:
        pid = proc.pid
        watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
        watchdog.start()
        start = datetime.now()
        (stdout, stderr) = proc.communicate(stdin)
        end = datetime.now()
        watchdog.cancel()  # if it's still waiting to run
        success = not kill_flag.isSet()
        kill_flag.clear()
        exitcode = None
        if success:
            exitcode = proc.returncode
    else:
        start = datetime.now()
        (stdout, stderr) = proc.communicate(stdin)
        end = datetime.now()
        exitcode = proc.returncode

    #print("cmd:{}".format(command))
    #print("stdout:{}".format(stdout))
    #print("stderr:{}".format(stderr))
    #stdout = stdout.decode()
    #stderr = stderr.decode()
    stdout = stdout.decode(errors='ignore')
    stderr = stderr.decode(errors='ignore')
    
    # If we're profiling log the runtime of the command
    if ICManageCLI.get_profiling():
        log_runtime(command, start, end)

    # There are some error messages on stderr that are harmless
    # Let's filter them out here
    if stderr:
        # Database snap backup warning - naturally this is split across multiple lines
        # with tabs thrown in for good measure
        db_snap_warning = "Warning: pmsnap of Mysql database has not been executed within 30 days. Please refer to ICM_Backup.pdf in the documentation tree for important information on creating snapshots to backup your IC Manage service"

        db_snap_warning_lines = [
            'Warning: pmsnap of Mysql database has not been executed',
            'within 30 days. Please refer to ICM_Backup.pdf in',
            'the documentation tree for important information on',
            'creating snapshots to backup your IC Manage service',
        ]
        # ARC/LSF session manager errors - really should be fixed by ARC
        arc_session_manager1 = "_IceTransSocketUNIXConnect: Cannot connect to non-local host"
        arc_session_manager2 = "Session management error: Could not open network socket"
        gdpxl_error_1 = 'if: Expression Syntax'
        filtered_stderr = ""
        for line in stderr.splitlines():
            if line.lstrip('\t') in db_snap_warning_lines:
                LOGGER.warn("Removing database snap warning message")
                continue
            if arc_session_manager1 in line:
                LOGGER.debug("Removing first ARC session manager error")
                continue
            if arc_session_manager2 in line:
                LOGGER.debug("Removing second ARC session manager error")
                continue
            if gdpxl_error_1 in line:
                LOGGER.debug("Removing gdpxl_error_1")
                continue

            filtered_stderr += "{}\n".format(line)

        stderr = filtered_stderr
        
    if dmx.utillib.utils.does_result_meet_retry_condition(exitcode, stdout, stderr, regex_list):
        LOGGER.debug("run_subcommand met retry condition:\n=exitcode=:{}\n=stdout=:{}\n=stderr=:{}".format(exitcode, stdout, stderr))
        if retried < maxtry:
            LOGGER.info("Tried {} times, {} more times for retry ...".format(retried, maxtry-retried))
            LOGGER.debug("Check for corrective action ...")
            dmx.utillib.utils.run_corrective_action_before_retry(stdout=stdout, stderr=stderr)
            LOGGER.debug("command: {}".format(command))
            time.sleep(delay_in_sec)
            return run_subcommand(command, stdin=stdin, timeout=timeout, retried=retried+1, maxtry=maxtry, delay_in_sec=delay_in_sec, regex_list=regex_list, retry=retry)

    dmx.utillib.utils.rephrase_messages_in_layman_terms(stdout=stdout, stderr=stderr)

    return (exitcode, stdout, stderr)

@ICMMemoizer
def run_read_command(command, stdin=None, timeout=None):
    '''
    Runs the specified command regardless of preview state
    Why? Because it should only be used for read-only commands

    :param command: The command to run in a list
    :type command: list
    :param stdin: Optional stdin - file descriptor, string, etc.
    :type stdin: None or str
    :param timeout: optional timeout for the command in seconds.
    :type timeout: None or int
    :return: Tuple of exitcode, stdout and stderr
    :rtype: tuple
    '''
    _command = []
    for ele in command:
        m = re.search(r'[^\w-]', ele)
        if m:
            ele = '\'{}\''.format(ele)
        _command.append(ele)
    LOGGER.debug(' '.join(_command))
    return run_subcommand(command, stdin=stdin, timeout=timeout)

def run_write_command(command, preview, stdin=None, timeout=None, print_command=False, env=None):
    '''
    Runs the specified command if we're not in preview mode
    Why? Because it's a write command and we don't want to
    actually run it if we're in preview mode

    :param command: The command to run in a list
    :type command: list
    :param preview: Boolean indicating whether or not we're in preview mode.
    :type preview: bool
    :param stdin: Optional stdin - file descriptor, string, etc.
    :type stdin: None or str
    :param timeout: optional timeout for the command in seconds.
    :type timeout: None or int
    :param print_command: Boolean indicating whether or not to print the command being run
    :type print_command: bool
    :return: Tuple of exitcode, stdout and stderr
    :rtype: tuple
    '''
    # There are some commands that we don't ever want the user to see
    # This allows us to hide them if we want
    if print_command:
        _command = []
        for ele in command:
            m = re.search(r'[^\w-]', ele)
            if m:
                ele = '\'{}\''.format(ele)
            _command.append(ele)
        LOGGER.info(' '.join(_command))

    # Reset the cache for run_read
    # Do this no matter what so preview mode still works
    run_read_command._reset()

    if not preview:
        return run_subcommand(command, stdin=stdin, timeout=timeout, env=env)
    else:
        return (0, None, None)

class ICManageCLI(object):
    '''
    Class to wrap all interactions with the IC Manage command line
    '''

    # Add the profiling flag as a class attribute and provide getters/setters
    # We can't use the standard @property decorators because they only work for instance
    # attributes, not class attributes
    __profiling = False
    @classmethod
    def get_profiling(cls):
        '''
        Retrieves the value of the internal profiling flag.

        :return: Flag indicating whether or not profiling is enabled
        :rtype: bool
        '''
        return cls.__profiling

    @classmethod
    def set_profiling(cls, new_value):
        '''
        Sets the internal profiling flag to new_value.

        :param new_value: New value of the profiling flag. Must be boolean.
        :type new_value: bool
        :raises: ICManageError
        '''
        if not isinstance(new_value, bool):
            raise ICManageError('Tried to set profiling property to non-boolean value {0}'.format(new_value))

        cls.__profiling = new_value

    @property
    def preview(self):
        '''
        Returns the preview flag
        If preview=True no changes will be made to the system.
        Otherwise known as dry-run mode
        '''
        return self._preview

    @preview.setter
    def preview(self, new_state):
        '''
        Sets preview to new_state
        If preview=True no changes will be made to the system.
        Otherwise known as dry-run mode

        :param new_state: The new state for the preview attribute
        :type new_state: bool
        '''
        self._preview = new_state

    #TODO
    @property
    def ticket(self):
        '''
        Returns the IC Manage ticket
        '''
        if not self._ticket:
            self._ticket = self.__get_icmmgr_ticket()
        return self._ticket

    @property
    def build_number(self):
        '''
        Returns the IC Manage build number

        :return: The build number for the IC Manage client tools
        :rtype: int
        '''
        if not self._build_number:
            self._build_number = self.get_icmanage_build_number()
        return self._build_number

    def __init__(self, preview=False, logger=None, site=''):
        '''
        Class to manage all interactions with the IC Manage command line
        '''
        self._preview = preview
        # Most of the time we don't need the ticket so don't get it
        # until it's required
        self._ticket = None
        # Likewise with the build number
        self._build_number = None
        self.__logger = logger
        if not self.__logger:
            self.__logger = logging.getLogger(__name__)
            self.__logger.addHandler(logging.NullHandler())

        # Set some standard variables that are used throughout
        self.__GDP = 'gdp' 
        self.__P4 = 'xlp4'
        self.__GGG = ''
        self.__SITE = ''
        if site:
            self.__SITE = '/{}'.format(site)
        _site = os.getenv("DMX_GDPSITE", False)
        if _site:
            self.__SITE = '/{}'.format(_site)
        self.__DELIMITER = '+MaGiC+'
        self.__IMMUTABLE_USER = 'immutable'
        self.__ROOT_USER = 'psginfraadm'
        self.__PROJECT_CATEGORY = {}
        self._FOR_REGTEST = ''     # This property is meant for running regtest

    def _as_gdp_admin(self):
        return '--user=icmanage'

    def get_icmanage_info(self):
        '''
        Returns ICM info (icmp4 info) in a dictionary format
        '''
        self.check_icmanage_available()

        info = {}
        command = [self.__P4, 'info']
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode == 0 and not stderr:
            for line in stdout.splitlines():
                m = re.match('(.*?):(.*)', line)
                if m:
                    key = m.group(1).strip()
                    value = m.group(2).strip()
                    if key not in info:
                        info[key] = value
        else:
            error_msg = 'ICManageCLI.__get_icm_info: {0}'.format(' '.join(command))
            if stdout:
                error_msg += '\nSTDOUT:{0}'.format(stdout)
            if stderr:
                error_msg += '\nSTDERR:{0}'.format(stderr)

            raise ICManageError(error_msg)

        return info                        

    def __run_read_command(self, command, stdin=None, timeout=None):
        '''
        Runs the specified command regardless of preview state
        Why? Because it should only be used for read-only commands
        '''
        return run_read_command(command, stdin=stdin, timeout=timeout)

    def __run_write_command(self, command, stdin=None, timeout=None, print_command=True, env=None):
        '''
        Runs the specified command if we're not in preview mode
        Why? Because it's a write command and we don't want to 
        actually run it if we're in preview mode
        '''
        return run_write_command(command, self.preview, stdin=stdin,
                                 timeout=timeout, print_command=print_command, env=env)

    #TODO
    def __get_marshal_output(self, command):
        return get_marshal_output(command)

    #
    # Methods that consumers of the class should use
    #
    def check_icmanage_available(self):
        '''
        Makes sure the IC Manage tools are in our environment

        :return: Boolean value indicating whether or not IC Manage is available
        :type return: bool
        :raises: ICManageError
        '''
        '''
        if sys.version_info[0] > 2:
            if not os.access(self.__P4, os.X_OK):
                raise ICManageError("icmp4 is not in your path. Did you forget to load your project's ARC environment?")
        else:
            if not which.which(self.__P4):
                raise ICManageError("icmp4 is not in your path. Did you forget to load your project's ARC environment?")
        '''
        #if not which.which(self.__P4):
        if not dmx.utillib.utils.which(self.__P4):
            raise ICManageError("xlp4 is not in your path. Did you forget to load your project's ARC environment?")
        # Per fogbugz https://fogbugz.altera.com/default.asp?495554, 
        # sometimes the $HOME path is not mounted.  This is required by ICM (icmp4) and cannot
        # be customized by us (per Gary Gendel) so we need to tickle it to get it to mount.
        user_home_path = os.environ['HOME']
        try:
            os.stat(user_home_path)
        except:
            raise ICManageError('Unable to stat home directory {}.  {} commands will not work.'.format(user_home_path, self.__P4))

        command = [self.__GDP, self._as_gdp_admin(), 'info']
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode == 0 and not stderr:
            # We're looking for any instance of the string icmanage
            if 'GDP' not in stdout:
                raise ICManageError("This doesn't look like an IC Manage server. You might have the p4 ARC resource loaded over the IC Manage ARC resource")

        else:
            error_msg = 'ICManageCLI.check_icmanage_available: {0}'.format(' '.join(command))
            if stdout:
                error_msg += '\nSTDOUT:{0}'.format(stdout)
            if stderr:
                error_msg += '\nSTDERR:{0}'.format(stderr)

            raise ICManageError(error_msg)

        return True

    #TODO
    def check_user_ticket(self):
        '''
        Check that the user has a valid ticket in their .p4tickets file

        :return: True if the ticket is valid
        :type return: bool
        :raises: LoginError
        '''
        ret = False

        user_id = os.environ['USER']
        if 'P4USER' in os.environ:
            user_id = os.environ['P4USER']

        if not self.is_user_icmp4_ticket_valid(user_id):
            error_msg = "No valid IC Manage login credentials for {0}.\n".format(user_id)
            error_msg += "You must log into IC Manage using your Altera Linux/Windows password.\n"
            error_msg += "Run the following command to log in:\n"
            error_msg += "icm_login"
            raise LoginError(error_msg)
        else:
            ret = True

        return ret

    #TODO
    def check_icmadmin_ticket(self):
        '''
        Check for a valid icmAdmin login

        :return: True is the icmAdmin login is valid
        :type return: bool
        :raises: LoginError
        '''
        ret = False

        if not self.is_user_icmp4_ticket_valid('icmAdmin'):
            error_msg = "Your IC Manage environment is not setup correctly."
            error_msg += "Run the following command to setup your environment:"
            error_msg += "icm_login"
            raise LoginError(error_msg)
        else:
            ret = True

        return ret

    #TODO
    def login_as_immutable(self):
        '''
        Login as thew immutable user. Required to create snap- configs

        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: ICManageError
        '''
        ret = False

        # There is a bug in our current version of Perforce that means you cannot login
        # as another user through the Forwarding Replica without providing that user's
        # password. So, for now, we have to get the immutable password from Perforce
        immutable_passwd = self.p4_print('//depot/admin/password.immutable').rstrip('\n')
        if not immutable_passwd:
            raise ICManageError('Could not get password for immutable user.')

        command = [self.__P4, '-u', '{}'.format(self.__IMMUTABLE_USER), 'login']
        (exitcode, stdout, stderr) = self.__run_write_command(command, stdin=immutable_passwd,
                                                              print_command=False)
        if exitcode == 0 and not stderr:
            if stdout and "User immutable logged in" in stdout:
                ret = True
            else:
                # If we're in preview mode don't worry about the output as
                # we never actually ran the command
                if self.preview:
                    ret = True
                else:
                    error_msg = "ICManageCLI.login_as_user: {0} returned a bad stdout".format(
                        ' '.join(command), exitcode)
                    if stdout:
                        error_msg += "\nSTDOUT: {}".format(stdout)

                    raise ICManageError(error_msg)
        else:
            error_msg = "ICManageCLI.login_as_user: {0} returned {1}".format(
                ' '.join(command), exitcode)
            if stdout:
                error_msg += "\nSTDOUT: {}".format(stdout)
            if stderr:
                error_msg += "\nSTDERR: {}".format(stderr)
            raise ICManageError(error_msg)

        return ret

    #TODO
    def login_as_user(self, user_id, proxy=None, all_host=False):
        """
        Login as user_id through the super user account.
        Used to perform commands on behalf of user_id.

        :param user_id: The user id to log in as
        :type user_id: str
        :param proxy: Optional Perforce proxy to log in to
        :type proxy: str
        :param all_host: Optional login and create the ticket for all_host (default: False)
        :type all_host: bool
        :return: Boolean indicating whether or not the login was successful
        :type return: bool
        :raises: ICManageError
        """
        ret = False
        super_user = 'icmAdmin'

        command = [self.__P4]
        if proxy:
            command += ['-p', '{}'.format(proxy)]
        if all_host:
            command += ['-u', '{}'.format(super_user), 'login', '-a', '{}'.format(user_id)]
        else:
            command += ['-u', '{}'.format(super_user), 'login', '{}'.format(user_id)]
        (exitcode, stdout, stderr) = self.__run_write_command(command, print_command=False)
        if exitcode == 0 and not stderr:
            if stdout and "User {} logged in".format(user_id) in stdout:
                ret = True
        else:
            error_msg = "ICManageCLI.login_as_user: {0} returned {1}".format(
                ' '.join(command), exitcode)
            if stdout:
                error_msg += "\nSTDOUT: {}".format(stdout)
            if stderr:
                error_msg += "\nSTDERR: {}".format(stderr)
            raise ICManageError(error_msg)

        return ret


    #TODO
    def logout_as_user(self, user_id, proxy=None):
        '''
        Logout as user_id on this machine only

        :param user_id: The User ID to logout
        :type user_id: str
        :param proxy: The optional Perforce proxy/server to logout from
        :type proxy: str
        :return: True on success, false on failure
        :type return: bool
        :raises: ICManageError
        '''
        ret = False

        # It's Perforce bug time!
        # If you try to logout as a user who does not exist
        # Perforce gives you the 'user does not exist' error
        # message and then creates the user!
        # This means we need to check if the user exists and
        # only attempt the logout if they do
        if not self.does_icmp4_user_exist(user_id):
            raise ICManageError('User {0} does not exist in Perforce'.format(user_id))

        # If no valid login ticket is available then just return False
        if not self.is_user_icmp4_ticket_valid(user_id):
            ret = False
        else:
            command = [self.__P4]
            if proxy is not None:
                command += ['-p', '{}'.format(proxy)]
            command += ['-u', '{}'.format(user_id), 'logout']

            (exitcode, stdout, stderr) = self.__run_write_command(command, print_command=False)
            if exitcode == 0 and not stderr:
                if stdout and 'User {0} logged out'.format(user_id) in stdout:
                    ret = True
            else:
                error_msg = "ICManageCLI.logout_as_user: {0} returned {1}".format(
                ' '.join(command), exitcode)
                if stdout:
                    error_msg += "\nSTDOUT: {}".format(stdout)
                if stderr:
                    error_msg += "\nSTDERR: {}".format(stderr)
                raise ICManageError(error_msg)

        return ret

    def does_icmp4_user_exist(self, user_id):
        '''
        Checks if user_id exists in the Perforce user database

        :param user_id: The user_id we're searching for
        :type user_id: str
        :return: True if the user exists, False if not
        :type return: bool
        :raises: ICManageError
        '''
        user_found = False

        command = [self.__P4, 'users', '{}'.format(user_id)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode == 0 and not stderr:
            for line in stdout.splitlines():
                if line.startswith('{0} <'.format(user_id)):
                    user_found = True
                    break
        else:
            if stderr and 'no such user(s).' in stderr:
                user_found = False
            else:
                error_msg = "ICManageCLI.does_icmp4_user_exist: {0} returned {1}".format(
                    ' '.join(command), exitcode)
                if stdout:
                    error_msg += "\nSTDOUT: {}".format(stdout)
                if stderr:
                    error_msg += "\nSTDERR: {}".format(stderr)
                raise ICManageError(error_msg)

        return user_found

    #TODO
    def is_user_icmp4_ticket_valid(self, user_id):
        '''
        Checks if the user's icmp4 ticket is valid
        Returns True if valid, False if not

        :param user_id: The user ID to check
        :type user_id: str
        :return: True if valid, False if not
        :type return: bool
        '''
        ticket_valid = False

        # If the user doesn't exist don't check the ticket
        # because that creates the user!
        if not self.does_icmp4_user_exist(user_id):
            raise ICManageError('ICManageCLI.is_user_icmp4_ticket_valid: User {0} does not exist'.format(
                user_id
            ))

        command = [self.__P4, '-u', '{}'.format(user_id), 'login', '-s']
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode == 0 and not stderr:
            ticket_valid = True

        return ticket_valid

    #TODO
    def workspace_access(self, clientname):
        ''' 
        Check if user have the p4 protect permission to access the files in this workspace
        if no problem accessing
            return ''
        else
            return 'error message'
        '''
        command = [self.__P4, '-c', clientname, 'sync', '-n', "'//{}/*/*/a'".format(clientname)]
        (exitcode, stdout, stderr) = run_command(' '.join(command))
        LOGGER.debug(stderr)
        if '.p4lib - no such file' in stderr:
            ret = 'invalid clientname'
        elif 'protected namespace - access denied' in stderr:
            ret = 'no access'
        else:
            ret = ''
        return ret

    def get_variant_name_prefix(self, variant):
        ''' Return the prefix name of the given variant:-
        variant: ar_lib, prefix: ar
        variant: iohmc, prefix: iohmc

        :param variant: The variant name
        :type variant: str
        :return: The prefix of the variant
        :type return: str
        '''
        return variant.split('_')[0]

   
    def get_variant_name_prefix_for_whr_onwards(self, variant):
        ''' Return the prefix name of the given variant:-
        This API follows a different ruleset from get_variant_name_prefix and apply
        only from WharfRock projects onwards.
        Prefix-name definition:
        Full variant name , subtracting the '_lib' suffix.
        Example:-
        variant: a_b_c , prefix: a_b_c
        variant: a_b_lib, prefix: a_b
        variant: x_lib_y, prefix: x_lib_y
        No variants are allowed with the same prefix

        :param variant: The variant name
        :type variant: str
        :return: The prefix of the variant
        :type return: str
        '''
        if variant.endswith('_lib'):
            prefix = variant.split('_lib')[0]
        else:
            prefix = variant

        return prefix        


    def get_conflicting_variant_prefix_for_whr_onwards(self, variantname, projectlist):
        ''' 
        Given a variant name, check if the name has any conflict in prefix name
        with the variants in the given projectlist. 
        Returns the list of 'project/variant' which conflicts.
        else return []

        This API follows a different ruleset from get_conflicting_variant_prefix and apply
        only from WharfRock projects onwards.
        Prefix-name definition:
        Full variant name , subtracting the '_lib' suffix.
        Example:-
        variant: a_b_c , prefix: a_b_c
        variant: a_b_lib, prefix: a_b
        variant: x_lib_y, prefix: x_lib_y
        No variants are allowed with the same prefix        

        :param variantname: The variant name
        :type variantname: str
        :param projectlist: A list of ICM projects to check for conflicts
        :type projectlist: A list of str
        :return: a list of conflicting 'project/variant'
        :type return: list of str
        '''
        retlist = []
        newprefix = '{}_'.format(self.get_variant_name_prefix_for_whr_onwards(variantname))
        if projectlist == None:
            projectlist = UNIQ_VARIANT_PROJ_LIST
        for project in projectlist:
            for variant in self.get_variants(project):
                oldprefix = '{}_'.format(self.get_variant_name_prefix_for_whr_onwards(variant)) 
                if newprefix.startswith(oldprefix) or oldprefix.startswith(newprefix):
                    retlist.append('{}/{}'.format(project, variant))
        return retlist

    def del_workspace(self, workspacename, preserve=True, force=False):
        '''
        Delete an ic manage workspace

        :param workspacename: The name of the workspace to delete
        :type workspacename: str
        :param preserve: Boolean indicating whether or not to preserve files on disk. Defaults to True.
        :type preserve: bool
        :param force: Boolean indicating whether or not to force deletion. Defaults to False.
        :type force: bool
        :return: Boolean indicating success or failure
        :type return: bool
        :raises: ICManageError
        '''
        ret = False

        if not self.workspace_exists(workspacename):
            self.__logger.info("Workspace {} does not exist.".format(workspacename))
            return ret

        command = ['delete-workspace', '--name', workspacename]
        if preserve:
            command.append('--leave-files')
        env = None
        if force:
            command.append('--force')
            env = os.environ.copy()
            env['P4USER'] = 'icmanage'
            env['ICM_GDP_USER'] = 'icmanage'

        (exitcode, stdout, stderr) = self.__run_write_command(command, env=env)
        error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
        if stdout:
            error_msg += "\nSTDOUT: {}".format(stdout)
        if stderr:
            error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg)

        if exitcode == 0 and 'Workspace has been successfully deleted:' in stdout:
            ret = True
        else:
            raise ICManageError(error_msg)

        return ret

    #TODO
    def add_group(self, user, group):
        '''
        Add user to ICM group
        '''
        tmp_grp = "/tmp/grp.%s.list" % str(os.getpid())
        cmd = "icmp4 -uicmAdmin group -o %s > %s" % (group, tmp_grp)
        (exitcode, stdout, stderr) = run_command(cmd)
        if exitcode or stderr:
            print_errors(cmd, exitcode, stdout, stderr)
    
        with open(tmp_grp, "a") as f:
            f.write("\t" + user)
    
        cmd = "icmp4 -uicmAdmin group -i < %s" % tmp_grp
        (exitcode, stdout, stderr) = run_command(cmd)
        if exitcode or stderr:
            print_errors(cmd, exitcode, stdout, stderr)
    
        LOGGER.info(stdout.rstrip())

    def create_temp_libtype_config(self, project, variant, libtype, release):
        configName = '__forwscreation__{}__{}__{}'.format(libtype, os.getpid(), int(time.time()) )
        self.add_libtype_config(project, variant, libtype, release, configName, description='temp libtype config for EWP population')
        return configName

    def add_workspace(self, project, variant, config, username=os.environ['USER'], dirname='.', ignore_clientname=False, occupied_ok=False, libtype=None, update_without_skeleton_sync=False):
        '''
        add an ic manage workspace
        '''
        dirname = os.path.abspath(dirname)
        configpath = '{}/{}/{}/{}'.format(self.__SITE, project, variant, config)
        if libtype:
            configName = self.create_temp_libtype_config(project, variant, libtype, config)
            configpath = '{}/{}/{}/{}/{}'.format(self.__SITE, project, variant, libtype, configName)
            #self.add_libtype_configproject, variant, libtype, release, configName, description='temp libtype config for EWP population')

        command = ['create-workspace', '--config', configpath,
                '--owner', username, '--location', dirname, '--skeleton']

        if occupied_ok:
            command.append('--occupied-ok')
        if ignore_clientname:
            command += ['--exclude-workspace-name']

        (exitcode, stdout, stderr) = self.__run_write_command(command)
        # Add support for preview mode
        if self.preview:
            stdout = 'Workspace dummy.icm.workspace created.'

        error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
        error_msg += "\nSTDOUT: {}".format(stdout)
        error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg)
        ### If succeed, message == 
        ###     Workspace has been successfully created: lionelta_i10socfm_liotestfc1_10
        if exitcode == 0 and 'Workspace has been successfully created: ':
            return stdout.strip().split(":")[-1].strip()
        else:
            raise ICManageError(error_msg)


    def update_workspace(self, workspacename, config=False): 
        '''
        Update an ic manage workspace so that it's configuration is up-to-date.
        '''
        wsdict = self.get_workspace_details(workspacename)
        wsroot = wsdict['rootDir']
        command = ['rebuild-workspace', wsroot, '--skeleton']
        if config:
            command += ['--config', config]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
        error_msg += "\nSTDOUT: {}".format(stdout)
        error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg) 
        if exitcode == 0:
            return 0
        else:
            raise ICManageError(error_msg)


    def sync_workspace(self, workspacename, skeleton=True, variants=['all'], libtypes=['all'], specs=[], force=False, verbose=False, skip_update=False, only_update_server=False, update_without_skeleton_sync=False, variants_libtypes_specs=None):
        '''
        sync an ic manage workspace

        If skeleton=True, then only do a skeleton sync.
        - the variants/libtypes/specs arg will be irrelevant, even if they are used

        If specs, then sync the workspace based on the given p4 file specifications.
        - the variants/libtypes arg will be irrelevant, even if they are used

        If specs=['an/oa/...', '*/*/....def'], it's equivalent to
        - icmp4 sycn an/oa/...
        - icmp4 sunc */*/....def
        
        If variants=['ip1', 'ip3'] 
        - do a fullsync on only these 2 ip.
        
        If libtypes=['rtl', 'oa']
        - do a fullsync on all ip's rtl/oa libtype.
        
        if variants=['ip1', 'ip2'], libtypes=['rtl', 'oa']
        - do a fullsync on rtl/oa libtypes for ip1 and ip2 only.

        If force=True, then do a icmp4 sync with the -f option. From icmp4 help:-
        - The -f flag forces resynchronization even if the client already
          has the file, and overwriting any writable files.  This flag doesn't
          affect open files.

        '''

        ### Check if the workspace exists
        try:
            icmws = self.workspace_exists(workspacename)
        except ICManageError:
            error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], 'self.workspace_exists')
            raise ICManageError(error_msg)
           
        # http://pg-rdjira:8080/browse/DI-1272
        # Add a skip update switch to skip workspace update and proceed directly to sync
        if not skip_update:
            ### Do a workspace update to make sure the configuration is up-to-date
            try:
                self.update_workspace(workspacename)
            except ICManageError:
                raise

            if not update_without_skeleton_sync:
                ### Do a skeleton sync
                command = ['sync-workspace', '--workspace', workspacename, '--skeleton']
                (exitcode, stdout, stderr) = self.__run_read_command(command)
                if exitcode != 0:
                    error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
                    error_msg += "\nSTDOUT: {}".format(stdout)
                    error_msg += "\nSTDERR: {}".format(stderr)
                    ### Skip raising exception if it is a post-sync trigger on chgrp. https://jira.devtools.intel.com/browse/PSGDMX-2199
                    if 'Post-sync trigger failed, fix and re-try' in stderr and 'chgrp: changing group of' in stdout:
                        LOGGER.debug(error_msg)
                    else:
                        raise ICManageError(error_msg)
    
        if skeleton:
            return 0

        ERRSTR1 = "Can't clobber"

        if variants_libtypes_specs:
            self.run_filespec_in_file(workspacename, skeleton, force, verbose, skip_update, only_update_server, update_without_skeleton_sync, variants_libtypes_specs)
        else:
            variants_libtypes_specs = [(variants, libtypes, specs)]
            LOGGER.debug("vls: {}".format(variants_libtypes_specs))
            self.run_filespec_in_file(workspacename, skeleton, force, verbose, skip_update, only_update_server, update_without_skeleton_sync, variants_libtypes_specs)

        return 0

    def run_filespec_in_file(self, workspacename, skeleton=True, force=False, verbose=False, skip_update=False, only_update_server=False, update_without_skeleton_sync=False, variants_libtypes_specs=None):
        wsroot = self.get_client_detail(workspacename)['root']
        LOGGER.debug("wsroot: {}".format(wsroot))
        currdir = os.getcwd()
        os.chdir(wsroot)

        new_file, filename = tempfile.mkstemp()
        LOGGER.debug("filename: {}".format(filename))
        fo = open(filename, 'w+')
        sync_arg = ''

        if force:
            sync_arg += ' -f'
        if only_update_server:
            sync_arg += ' -k'

        for variants, libtypes, specs in variants_libtypes_specs :
            if specs:
                for spec in specs:
                    to_be_sync_path = '{}/{}/...'.format(wsroot, spec)
                    fo.write(to_be_sync_path+'\n')
            else:
                for ipname in variants:
                    if ipname == 'all':
                        ipname = '*'
                    for libtype in libtypes:
                        if libtype == 'all':
                            libtype = '*'

                        to_be_sync_path = '{}/{}/{}/...'.format(wsroot, ipname, libtype)
                        fo.write(to_be_sync_path+'\n')
        fo.close()
       # LOGGER.debug(os.system('cat {}'.format(filename)))
        cmd = 'cd {}; xlp4 -x {} sync {}'.format(wsroot, filename, sync_arg)
        #cmd = 'xlp4 -x {} sync {}'.format(filename, sync_arg)
        exitcode, stdout, stderr = run_command(cmd)
        LOGGER.debug('Run {}'.format(cmd))
        LOGGER.debug(stdout)
        LOGGER.debug(stderr)

        #os.chdir(currdir)
        return 0

    def get_user_linux_groups(self, username=os.environ['USER']):
        '''
        Returns a list of all the linux groups this user belongs to.
        '''
        command = ['groups', username]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode:
            error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
            error_msg += "\nSTDOUT: {}".format(stdout)
            error_msg += "\nSTDERR: {}".format(stderr)
            raise ICManageError(error_msg)
        else:
            ### stdout = 'all.users\nroots\nrunda.users\n'
            ret = stdout.split()
            if len(ret) > 2:
                return ret[2:]
            else:
                error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
                error_msg += "\nSTDOUT: {}".format(stdout)
                error_msg += "\nSTDERR: {}".format(stderr)
                raise ICManageError(error_msg)

    # TODO 
    def get_user_icm_groups(self, username=os.environ['USER']):
        '''
        Returns a list of all the icmp4 groups this user belongs to.
        '''
        command = [self.__P4, 'groups', '-u', username]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode:
            error_msg = "ICManageCLI.{}: {}".format(inspect.stack()[0][3], ' '.join(command))
            error_msg += "\nSTDOUT: {}".format(stdout)
            error_msg += "\nSTDERR: {}".format(stderr)
            raise ICManageError(error_msg)
        else:
            ### stdout = 'yltan : eng ndaltera sudoicetools_nadder cdv tsmc nd pedept software hcopy sudoicetools\n'
            ret = stdout.replace('\n', ' ').split()
            return ret

    ##############################################################
    ##############################################################
    ### START: Object Exists ###
    ##############################################################
    def _object_exists(self, path, retkeys=['path']):
        command = [self.__GDP, self._as_gdp_admin(), 'list', path, '--output-format', 'json', '--columns', ','.join(retkeys)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = "ICManageCLI._object_exists: {}".format(' '.join(command))
        error_msg += "\nSTDOUT: {}".format(stdout)
        error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg)

        try:
            d = json.loads(stdout.strip())
            return d['results']
        except Exception as e:
            error_msg = str(e) + error_msg
            raise ICManageError(error_msg)

    def project_exists(self, project):
        return self._object_exists('{}/{}:project'.format(self.__SITE, project))

    def variant_exists(self, project, variant):
        return self._object_exists('{}/{}/{}:variant'.format(self.__SITE, project, variant))

    def libtype_exists(self, project, variant, libtype):
        return self._object_exists('{}/{}/{}/{}:libtype'.format(self.__SITE, project, variant, libtype))

    def workspace_exists(self, workspacename):
        return self._object_exists('/workspace/{}'.format(workspacename))

    def config_exists(self, project, variant, config, libtype=None, is_libtype_config=False):
        '''
        is_libtype_config mean that the checking is for config created for that particular libtype only. 
        In gdpxl, the release of llibtype cannot be used to create workspace, 
        thus we create a new config that hold only that paritucly libtype release. 
        '''
        if libtype:
            if is_libtype_config:
                path = '/intel/{}/{}/{}/{}:config'.format(project, variant, libtype, config)
            else:
                config_library_release = config 
                [library, release] = self.get_library_release_from_libtype_config(project, variant, libtype, config_library_release)
                if release:
                    path = '/intel/{}/{}/{}/{}:library/{}:release'.format(project, variant, libtype, library, release)
                else:
                    path = '/intel/{}/{}/{}/{}:library'.format(project, variant, libtype, config)
            return self._object_exists('{}'.format(path))
        else:
            return self._object_exists('{}/{}/{}/{}:config'.format(self.__SITE, project, variant, config))

    def library_exists(self, project, variant, libtype, library):
        return self._object_exists('{}/{}/{}/{}/{}:library'.format(self.__SITE, project, variant, libtype, library))

    def release_exists(self, project, variant, libtype, library, release):
        return self._object_exists('{}/{}/{}/{}/{}/{}:release'.format(self.__SITE, project, variant, libtype, library, release))

    def libtype_defined(self, libtype):
        return self._object_exists("/libspec/{}".format(libtype))

    def config_exists_under_config_hierarchy(self, name, project, variant, config, stop_at_immutables=False):
        ''' given a config 'name', search and see if the named config exists in 
        any of the project/variant/config hierarchically.
        To return all configs, set name=''
        '''
        # {}/**/{}/{}/{}:config     == search for the root PVC
        # /.**::content             == return all objects, hierarchically (including self)
        # /:config                  == and filter only config objects
        # /::-child                 == return their parent (since all previous returned were configs, this should be all their variants)
        # /**/{}:config             == return all the matching configs under the variants
        ret = self._object_exists('{}/{}/{}/{}:config/.**::content/:config/::-child/**/{}:config'.format(self.__SITE, project, variant, config, name))
        return self._filter_items_from_config_hierarchy_immutables(project, variant, config, ret, 'config', stop_at_immutables=stop_at_immutables)

    def library_exists_under_config_hierarchy(self, name, project, variant, config, stop_at_immutables=False):
        ''' given a library 'name', search and see if the named library exists in 
        any of the project/variant/config hierarchically.
        To return all libraries, set name=''
        '''
        # {}/**/{}/{}/{}:config     == search for the root PVC
        # /**::content              == return all objects, hierarchically (excluding self)
        # /:library,release         == and filter only the libraries and releases
        # /**::-child               == return all their parents and ancestors (if library, then it will return libtype, variant, project, site)
        # /:libtype                 == filter only the libtypes
        # /**/{}:library            == return all the matching libraries under the libtypes
        ret = self._object_exists('{}/{}/{}/{}:config/**::content/:library,release/**::-child/:libtype/**/{}:library'.format(self.__SITE, project, variant, config, name))
        return self._filter_items_from_config_hierarchy_immutables(project, variant, config, ret, 'library', stop_at_immutables=stop_at_immutables)

    def release_exists_under_config_hierarchy(self, name, project, variant, config, stop_at_immutables=False):
        ''' given a release 'name', search and see if the named release exists in 
        any of the project/variant/config hierarchically.
        To return all releases, set name=''
        '''
        # {}/**/{}/{}/{}:config     == search for the root PVC
        # /**::content              == return all objects, hierarchically (excluding self)
        # /:library,release         == and filter only the libraries and releases
        # /**::-child               == return all their parents and ancestors, including self (if library, then it will return library, libtype, variant, project, site)
        # /:library                 == filter only the libraries
        # /**/{}:release            == return all the matching libraries under the libtypes
        ret = self._object_exists('{}/{}/{}/{}:config/**::content/:library,release/.**::-child/:library/**/{}:release'.format(self.__SITE, project, variant, config, name))
        return self._filter_items_from_config_hierarchy_immutables(project, variant, config, ret, 'release', stop_at_immutables=stop_at_immutables)

    def _filter_items_from_config_hierarchy_immutables(self, project, variant, config, datalist, datatype, stop_at_immutables=False):
        if not stop_at_immutables:
            return datalist
        
        immutables = self.get_immutable_objects_under_config_hierarchy(project, variant, config)
        if not immutables:
            return datalist

        ### /**/project/variant/config ==> /**/project/variant
        ### /**/project/variant/libtype/library ==> /**/project/variant/libtype
        ### /**/project/variant/libtype/library/release ==> /*ctual*/project/variant/libtype
        def _return_parent_path(path, pathtype):
            ret = os.path.dirname(path)
            if pathtype in ['config', 'library']:
                pass
            elif pathtype == 'release':
                ret = os.path.dirname(ret)
            return ret

        immutables_parent_path = []
        for x in immutables:
            immutables_parent_path.append(_return_parent_path(x['path'], x['type']))
        
        filtered_list = []
        for d in datalist:
            if _return_parent_path(d['path'], datatype) not in immutables_parent_path:
                filtered_list.append(d)

        return filtered_list
    ##############################################################
    ### END: Object Exists ###
    ##############################################################
    ##############################################################
  

    ##############################################################
    ##############################################################
    ### START: Find Objects ###
    ##############################################################
    def _find_objects(self, objtype, criteria, retkeys=['name']):
        '''
        Overview
        ========
            path = '/intel/*:project'
            retkey = '*'
            cmd ran = 'gdp list {path} --columns {retkeys} --output-format json'
            stdout = {
                "results": [
                    {
                        "name": "i10socfm",
                        "path": "/intel/i10socfm",
                        "id": "12345",
                        ... ... ...
                    },
                    {
                        "name": "rnr",
                        "location": "/intel/rnr",
                        "id": "45678",
                        ... ... ...
                    },
                    ... ... ...
                ],
                "success": true
            }

        return
        ======
            There are 2 return types
            - list of strings (when 'retkeys' is a single element list)
            - list of dicts (when 'retkeys' is a list of string)

        Example
        =======
            ret = self._get_objects('/intel/*', retkeys='name')
            ret = ['i10socfm', 'rnr', ...]

            ret = self._get_objects('/intel/*', retkeys='name,path')
            [{
                "name": "i10socfm",
                "path": "/intel/i10socfm",
            },
            {
                "name": "rnr",
                "location": "/intel/rnr",
            }]

            ret = self._get_objects('/intel/*', retkeys='*')
            [{
                "name": "i10socfm",
                "path": "/intel/i10socfm",
                "id": "12345",
                ... ... ...
            },
            {
                "name": "rnr",
                "location": "/intel/rnr",
                "id": "45678",
                ... ... ...
            }]
        '''
        command = [self.__GDP, self._as_gdp_admin(), 'find', '--type', objtype, criteria, '--columns', ','.join(retkeys), '--output-format', 'json']
        self.__logger.debug("cmd: {}".format(command))
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = "ICManageCLI._get_objects: {}".format(' '.join(command))
        error_msg += "\nSTDOUT: {}".format(stdout)
        error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg)
        try:
            d = json.loads(stdout.strip())
            if len(retkeys) > 1 or retkeys[0] == '*':
                return d['results']
            else:
                return [x[retkeys[0]] for x in d['results']]
        except Exception as e:
            error_msg = str(e) + error_msg
            raise ICManageError(error_msg)
    ##############################################################
    ### END: Find Object ###
    ##############################################################
    ##############################################################
   

    ##############################################################
    ##############################################################
    ### START: Get Objects ###
    ##############################################################
    def _get_objects(self, path, retkeys=['name']):
        '''
        Overview
        ========
            path = '/intel/*:project'
            retkey = '*'
            cmd ran = 'gdp list {path} --columns {retkeys} --output-format json'
            stdout = {
                "results": [
                    {
                        "name": "i10socfm",
                        "path": "/intel/i10socfm",
                        "id": "12345",
                        ... ... ...
                    },
                    {
                        "name": "rnr",
                        "location": "/intel/rnr",
                        "id": "45678",
                        ... ... ...
                    },
                    ... ... ...
                ],
                "success": true
            }

        return
        ======
            There are 2 return types
            - list of strings (when 'retkeys' is a single element list)
            - list of dicts (when 'retkeys' is a list of string)

        Example
        =======
            ret = self._get_objects('/intel/*', retkeys='name')
            ret = ['i10socfm', 'rnr', ...]

            ret = self._get_objects('/intel/*', retkeys='name,path')
            [{
                "name": "i10socfm",
                "path": "/intel/i10socfm",
            },
            {
                "name": "rnr",
                "location": "/intel/rnr",
            }]

            ret = self._get_objects('/intel/*', retkeys='*')
            [{
                "name": "i10socfm",
                "path": "/intel/i10socfm",
                "id": "12345",
                ... ... ...
            },
            {
                "name": "rnr",
                "location": "/intel/rnr",
                "id": "45678",
                ... ... ...
            }]
        '''
        command = [self.__GDP, self._as_gdp_admin(), 'list', path, '--columns', ','.join(retkeys), '--output-format', 'json']
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = "ICManageCLI._get_objects: {}".format(' '.join(command))
        error_msg += "\nSTDOUT: {}".format(stdout)
        error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg)
        try:
            d = json.loads(stdout.strip())
            if len(retkeys) > 1 or retkeys[0] == '*':
                return d['results']
            else:
                return [x[retkeys[0]] for x in d['results']]
        except Exception as e:
            error_msg = str(e) + error_msg
            raise ICManageError(error_msg)

    def get_projects(self):
        return self._get_objects('{}/:project'.format(self.__SITE))

    def _get_project_category(self):
        '''
        Generate the return the self.__PROJECT_CATEGORY dictionary table.
        Assuming we have the following projects:-
            /intel/proj1
            /intel/folder1/proj2
            /intel/folder2/folder3/proj3
        self.__PROJECT_CATEGORY == {
            proj1: '',
            proj2: 'folder1',
            proj3: 'folder2/folder3'
        }
        '''
        if not self.__PROJECT_CATEGORY:
            paths = self._get_objects('{}/**/:project'.format(self.__SITE), retkeys=['path','name'])
            for e in paths:
                self.__PROJECT_CATEGORY[e['name']] = re.sub('^/intel/?', '', os.path.dirname(e['path']))
        return self.__PROJECT_CATEGORY

    def get_category(self, project):
        d = self._get_project_category()
        return d[project]

    def get_variants(self, project):
        return self._get_objects('{}/{}/:variant'.format(self.__SITE, project))

    def get_libtypes(self, project, variant):
        return self._get_objects('{}/{}/{}/:libtype'.format(self.__SITE, project, variant))

    def get_libraries(self, project, variant, libtype):
        return self._get_objects('{}/{}/{}/{}/:library'.format(self.__SITE, project, variant, libtype))

    def get_configs(self, project, variant):
        return self._get_objects('{}/{}/{}/*:config'.format(self.__SITE, project, variant))

    def get_library_releases(self, project, variant, libtype, library='dev', retkeys=['name']):
        return self._get_objects('{}/{}/{}/{}/{}/:release'.format(self.__SITE, project, variant, libtype, library), retkeys=retkeys)

    def get_library_from_release(self, project, variant, libtype, release, retkeys=['name']):
        '''
        in PSG's methodology, there will/should be only 1 unique release name across all libraries for the same project/variant/libtype.
        - if there is only 1 release found, return the library name as a string
        - if no release found, return an empty string
        - if the named release is found from more than 1 library, return -1
        '''
        ret = self._get_objects('{}/{}/{}/{}/*/{}:release/:library:-child'.format(self.__SITE, project, variant, libtype, release), retkeys=retkeys)
        if len(ret) == 1:
            return ret[0]
        elif len(ret) == 0:
            return ''
        else:
            return -1

    def get_workspaces(self, project='*', variant='*', config='*', retkeys=['name']):
        '''
        An implementation of get_workspaces to match LEGACY gdp is done in abnrlib.flows.workspaces
        '''
        retlist = self._get_objects('{}/{}/{}/{}:config/*:workspace'.format(self.__SITE, project, variant, config), retkeys)
        return retlist

    def get_immutable_objects_under_config_hierarchy(self, project, variant, config, retkeys=['*']):
        datalist = self._get_objects("{}/{}/{}/{}:config/.**::content".format(self.__SITE, project, variant, config), retkeys=retkeys)
        immutables = ("REL", "PREL", "snap-")
        retlist = []
        for data in datalist:
            if data['type'] == 'release':
                retlist.append(data)
            elif data['type'] == 'config' and data['name'].startswith(immutables):
                retlist.append(data)
        return retlist
    ##############################################################
    ### END: Get Objects ###
    ##############################################################
    ##############################################################



    ##############################################################
    ##############################################################
    ### START: Add Objects ###
    ##############################################################
    def add_variant(self, project, variant, description=None):
        if not ICMName.is_variant_name_valid(variant):
            raise BadNameError('ICManageCLI.add_variant: {0} is not a valid variant name'.format(variant))

        if self.variant_exists(project, variant):
            self.__logger.info('Variant exists {0} already exists in project {1}'.format(variant, project))
            return False
        
        self.__logger.info('Add variant: project={0} variant={1}'.format(project, variant))
        command = [self.__GDP, self._as_gdp_admin(), 'create', 'variant', '{}/{}/{}'.format(self.__SITE, project, variant)]
        if description:
            command += ['--set', "description='{}'".format(description)]
        (exitcode, stdout, stderr) = self.__run_write_command(command)
        error_msg = "ICManageCLI.add_variant: '{0}' returned {1}".format(' '.join(command), exitcode)
        error_msg += "\nSTDOUT:{0}".format(stdout)
        error_msg += "\nSTDERR:{0}".format(stderr)
        self.__logger.debug(error_msg)

        if exitcode == 0 and not stderr:
            return True
        else:
            raise ICManageError(error_msg)
    
    def add_libtypes_to_variant(self, project, variant, libtypes):
        duplicates = 0
        if not self.project_exists(project) and not self.preview:
            raise ICManageError("ICManageCLI.add_libtypes_to_variant:Project does not exist: {0}".format(project))
        if not self.variant_exists(project, variant) and not self.preview:
            raise ICManageError("ICManageCLI.add_libtypes_to_variant:Variant {0} does not exist in project {1}".format(
                variant, project))
        for libtype in libtypes:
            if not self.libtype_defined(libtype):
                self.__logger.error('Attempted to add libtype {0} which is not defined in the system'.format(
                    libtype
                ))
                raise UndefinedLibtypeError('Please contact psgicmsupport@intel.com to get the new libtype defined in ICManage')

            if self.libtype_exists(project, variant, libtype):
                self.__logger.info('Libtype exists: project={0} variant={1} libtype={2}'.format(
                    project, variant, libtype))
                duplicates += 1
            else:
                self.__logger.info('Add libtype: project={0} variant={1} libtype={2}'.format(
                    project, variant, libtype))
                command = [self.__GDP, self._as_gdp_admin(), 'create', 'libtype', '{}/{}/{}/{}'.format(self.__SITE, project, variant, libtype)]
                (exitcode, stdout, stderr) = self.__run_write_command(command)
                error_msg = "ICManageCLI.add_libtypes_to_variant: '{0}' returned {1}".format(' '.join(command), exitcode)
                error_msg += "\nSTDOUT:{0}".format(stdout)
                error_msg += "\nSTDERR:{0}".format(stderr)
                if exitcode != 0 or stderr:
                    raise ICManageError(error_msg)
        return duplicates
    
    def add_library(self, project, variant, libtype, library='dev', description='', srclibrary='', srcrelease=''):
        '''
        if srclibrary is given:
            project/variant/libtype/library will be integrated from project/variant/libtype/srclibrary
        if srclibrary and srcrelease is given:
            project/variant/libtype/library will be integrated from project/variant/libtype/srclibrary/srcrelease
        if srclibrary and srcrelease are both not given:
            project/variant/libtype/library will be a new/empty library
        '''
        if not ICMName.is_library_name_valid(library):
            raise BadNameError('ICManageCLI.add_libraries: {0} is an invalid library name'.format(library))
           
        if self.is_name_immutable(library):
            raise ICManageError("Library name ({}) can not be an IMMUTABLE naming convention.".format(library))

        if self.library_exists(project, variant, libtype, library):
            self.__logger.info('Library exists: project={0} variant={1} libtype={2} library={3}'.format(project, variant, libtype, library))
            return False
        else:
            clp = self.get_clp(variant, libtype)

            self.__logger.info('Add library: project={0} variant={1} libtype={2} library={3} custom library path={4}'.format(project, variant, libtype, library, clp))
            command = [self.__GDP, self._as_gdp_admin(), 'create', 'library', '{}/{}/{}/{}/{}'.format(self.__SITE, project, variant, libtype, library)]
            command += ['--set', 'location={}'.format(clp)]
            if description:
                command += ['--set', "description='{}'".format(description)]

            if srclibrary and srcrelease:
                command += ['--from', '{}/{}/{}/{}/{}/{}'.format(self.__SITE, project, variant, libtype, srclibrary, srcrelease)]
            elif srclibrary:
                command += ['--from', '{}/{}/{}/{}/{}'.format(self.__SITE, project, variant, libtype, srclibrary)]

            self._FOR_REGTEST = command
            (exitcode, stdout, stderr) = self.__run_write_command(command)
            error_msg = "ICManageCLI.add_libraries: '{0}' returned {1}".format(' '.join(command), exitcode)
            error_msg += "\nSTDOUT:{0}".format(stdout)
            error_msg += "\nSTDERR:{0}".format(stderr)
            self.__logger.debug(error_msg)
            if exitcode != 0 or stderr:
                raise ICManageError(error_msg)
        return True
    
    def add_libraries(self, project, variant, libtypes, library='dev', description=''):
        duplicates = 0
        if not ICMName.is_library_name_valid(library):
            raise BadNameError('ICManageCLI.add_libraries: {0} is an invalid library name'.format(library))
        for libtype in libtypes:
            if not self.add_library(project, variant, libtype, library, description):
                duplicates += 1
        return duplicates

    def add_libtype_config(self, project, variant, libtype, release, configName, description=''):
        '''
        In GDPXL libtype release is not a configuration as in gdp 
        This api  is to create a configuration for libtype release 
        '''
        if not ICMName.is_config_name_valid(configName):
            raise InvalidConfigNameError('ICManageCLI.add_composite_config: {0} is not a valid config name'.format(config))

        if self.config_exists(project, variant, configName, libtype, is_libtype_config=True):
            self.__logger.info("Libtype config already exists: {0}".format(
                format_configuration_name_for_printing(project, variant, configName, libtype)))
            return False
        else:

            [library, release] = self.get_library_release_from_libtype_config(project, variant, libtype, release)
            configpath = '{0}/{1}/{2}/{3}/{4}'.format(self.__SITE, project, variant, libtype, configName)
            objpath = '{0}/{1}/{2}/{3}/{4}/{5}'.format(self.__SITE, project, variant, libtype, library, release)
            if not release:
                objpath = '{0}/{1}/{2}/{3}/{4}'.format(self.__SITE, project, variant, libtype, library)

            self.__logger.info("Creating configuration for libtype release: {}/{}/{}/{}".format(project, variant, libtype, configName))
            command = [self.__GDP, self._as_gdp_admin(), 'create', 'configuration', '{}'.format(configpath), '--add', '{}'.format(objpath)]
            if description:
                command += ['--set', "description='{}'".format(description)]

            self._FOR_REGTEST = command # For regression tests

            (exitcode, stdout, stderr) = self.__run_write_command(command)
            error_msg = "ICManageCLI.add_composite_config: {}".format(' '.join(command))
            error_msg += "\nSTDOUT: {0}".format(stdout)
            error_msg += "\nSTDERR: {0}".format(stderr)
            self.__logger.debug(error_msg)

            # Temporary disable stderr due to LB_LIBRARY_PATH not found complain
            #if exitcode != 0 or stderr:
            if exitcode != 0:
                raise ICManageError(error_msg)
            else:
                return True
    
    
    def add_config(self, project, variant, config, description=''):
        if not ICMName.is_config_name_valid(config):
            raise InvalidConfigNameError('ICManageCLI.add_composite_config: {0} is not a valid config name'.format(config))

        if self.config_exists(project, variant, config):
            self.__logger.info("Composite config already exists: {0}".format(
                format_configuration_name_for_printing(project, variant, config)))
            return False
        else:
            self.__logger.info("Creating configuration: {}/{}/{}".format(project, variant, config))
            command = [self.__GDP, self._as_gdp_admin(), 'create', 'configuration', '{}/{}/{}/{}'.format(self.__SITE, project, variant, config)]
            if description:
                command += ['--set', "description='{}'".format(description)]

            self._FOR_REGTEST = command # For regression tests

            (exitcode, stdout, stderr) = self.__run_write_command(command)
            error_msg = "ICManageCLI.add_composite_config: {}".format(' '.join(command))
            error_msg += "\nSTDOUT: {0}".format(stdout)
            error_msg += "\nSTDERR: {0}".format(stderr)
            self.__logger.debug(error_msg)
            if exitcode != 0:
                raise ICManageError(error_msg)
            else:
                return True
    
    def add_library_release(self, project, variant, libtype, relname, changenumber=None, description='', library='dev'):
        '''
        if wanna release from latest, then set 
            changenumber == None
        '''

        ### Make sure relname is a valid IMMUTABLE name
        if not self.is_name_immutable(relname):
            raise ICManageError("relname({}) does not conform to an IMMUTABLE naming convention.".format(relname))
        
        ### Check and make sure the same relname does not exist in other libraries, as
        ### PSG methodology only allows a unique release across the same project/variant/libtype/<libraries>/...
        matched_library = self.get_library_from_release(project, variant, libtype, relname)
        if matched_library:
            raise ICManageError("release({}) for {}/{}:{} already exist in library({}).".format(relname, project, variant, libtype, matched_library))


        path = '{}/{}/{}/{}/{}/{}'.format(self.__SITE, project, variant, libtype, library, relname)

        # Make sure changenumber is not 0
        if changenumber == 0:
            raise ICManageError('Tried to release {0}/{1}:{2}/{3} with an invalid changenumber'.format(project, variant, libtype, library))

        if self.release_exists(project, variant, libtype, library, relname):
            raise ICManageError("Release with the following name: {} already exists!".format(path))

        command = [self.__GDP, self._as_gdp_admin(), 'create', 'release', path]
        if changenumber:
            command += ['--from', '@{}'.format(changenumber)]

        if description:
            command += ['--set', "description='{}'".format(description)]

        self.__logger.info("Creating library release {0}/{1}:{2}/{3}@{4}".format(project, variant, libtype, library, relname))
        self._FOR_REGTEST = command
        (exitcode, stdout, stderr) = self.__run_write_command(command)
        error_msg = "ICManageCLI.add_library_release: '{}'".format(' '.join(command))
        error_msg += "\nSTDOUT: {0}".format(stdout)
        error_msg += "\nSTDERR: {0}".format(stderr)
        self.__logger.debug(error_msg)

        if exitcode != 0:
            raise ICManageError(error_msg)
        else:
            return relname


    def add_library_release_for_tnr(self, project, variant, libtype, library, description=''):
        '''
        The standard name for all library-release that created for 'dmx release' is as follow:-
            snap-fortnr_#
        whereby # is a running number, starting from 1
        
        if there is not release found, then snap-fortnr_1 will be created.
        if there are already snap-fortnr_#, then snap-fortnr_<#+1> will be created.
        Release will always be based on the #activedev (ie: latest)
        '''
        prefix = 'snap-fortnr_'
        retlist = self.get_library_releases(project, variant, libtype, library)
        tnrlist = [x for x in retlist if x.startswith(prefix)]
        if not tnrlist:
            relname = prefix + '1'
        else:
            ### Find the largest number
            maxnum = 0
            for num in tnrlist:
                i = int(num.split('_')[-1])
                if i > maxnum:
                    maxnum = i
            relname = prefix + str(maxnum + 1)
        ret = self.add_library_release(project, variant, libtype, relname, changenumber=None, description=description, library=library)
        return ret

    ##############################################################
    ### END: Add Objects ###
    ##############################################################
    ##############################################################

    def get_libtype_type(self, libtype):
        '''
        Returns ICManage libtype's type

        :param libtype: The name of a libtype
        :type libtype: str
        :return: ICManage libtype's type
        :rtype: str
        :raises: ICManageError
        '''
        ret = None
        command = [self.__GDP, self._as_gdp_admin(), 'list', '/libspec/{}'.format(libtype), '--columns', 'path,domain', '--output-format', 'json']
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = "ICManageCLI.libtype_defined: {}".format(' '.join(command))
        error_msg += "\nSTDOUT: {}".format(stdout)
        error_msg += "\nSTDERR: {}".format(stderr)
        self.__logger.debug(error_msg)

        try:
            d = json.loads(stdout.strip())
            return d['results'][0]['domain']
        except Exception as e:
            error_msg = str(e) + error_msg
            raise ICManageError(error_msg)

    def update_library(self, project, variant, libtype, library, description=None, clp=None):
        '''
        Updates the description and/or custom library path for the library

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param description: Optional new value for the library description.
        :type description: str or None
        :param clp: Optional new Custom Library Path value
        :type clp: str or None
        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: ICManageError
        '''
        #TODO:
        pass


    def get_library_details(self, project, variant, libtype, library):
        '''
        Retrieves the library details from IC Manage

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :return: The library details in dictionary form
        :type return: dict
        :raises: ICManageError


        ICM output
        ==========
        {'description': '',
         'libpath': '@$variant/ipspec',
         'library': 'dev',
         'libtype': 'ipspec',
         'project': 'i10socfm',
         'type': 'local',
         'variant': 'liotest1'}

        GDP output
        ==========
        {
            "location": "liotest1/ipspec",
            "uri": "p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotest1/ipspec/dev/...",
            "created-by": "lionelta",
            "id": "L1247063",
            "type": "library",
            "name": "dev",
            "path": "/intel/i10socfm/liotest1/ipspec/dev",
            "created": "2020-09-23T10:06:31.322Z",
            "modified": "2020-09-23T10:06:31.322Z",
            "change": "@now",
            "libtype": "ipspec"
        }
        '''
        return self._get_objects('{}/{}/{}/{}/{}:library'.format(self.__SITE, project, variant, libtype, library), retkeys=['*'])[0]

    def del_variant(self, project, variant):
        '''
        Delete a variant from project

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant to delete
        :type variant: str
        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: ICManageError
        '''
        self.__logger.info('Remove variant: project={0} variant={1}'.format(
            project, variant))
        command = [self.__GDP, self._as_gdp_admin(), 'delete', '{}/{}/{}'.format(self.__SITE, project, variant)]
        (exitcode, stdout, stderr) = self.__run_write_command(command)
        error_msg = "ICManageCLI.del_variant: '{0}' returned {1}".format(' '.join(command), exitcode)
        error_msg += "\nSTDOUT:{0}".format(stdout)
        error_msg += "\nSTDERR:{0}".format(stderr)
        self.__logger.debug(error_msg)
        if exitcode == 0 and not stderr:
            return True
        else:
            raise ICManageError(error_msg)

    def get_clp(self, variant, libtype):
        if libtype == 'oa':
            return '{}/{}/{}'.format(variant, libtype, variant)
        elif libtype == 'oa_sim':
            return '{}/{}/{}_sim'.format(variant, libtype, variant)
        else:
            return '{}/{}'.format(variant, libtype)

    #TODO
    def get_latest_rel_config(self, project, variant, milestone='', thread=''):
        '''
        Returns the latest REL configuration within project/variant for
        the specified milestone and thread
        Milestone and thread are optional. If not specified then the
        latest configuration regardless of milestone/thread will be returned
        Only considers REL configurations that do not have a label

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param milestone: The Altera milestone
        :type milestone: str
        :param thread: The Altera thread
        :type thread: str
        :return: The name of the latest REL configuration
        :type return: str
        '''
        # Build the regex in stages, with helper functions as necessary
        base_regex_str = get_rel_config_regex_start(milestone=milestone, thread=thread)
        rel_without_label_regex_str = base_regex_str
        rel_without_label_regex_str += get_rel_config_regex_end()
        regex = re.compile(rel_without_label_regex_str)

        # Get all matches and pass them off to the relevant function to find the last REL
        matches = [x for x in map(regex.search, self.get_configs(project, variant)) if x is not None]
        latest_rel = get_last_REL_from_matches(matches)

        return latest_rel        

    #TODO
    def get_latest_rel_config_with_label(self, project, variant, milestone='', thread='', label=''):
        '''
        Returns the latest REL configuration within project/variant for
        the specified milestone and thread
        Milestone and thread are optional. If not specified then the
        latest configuration regardless of milestone/thread will be returned
        Only considers REL configurations that have a label. If label is set
        then will only consider configs with that label. If label is not
        set will consider any configuration with any label

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param milestone: Optional - The Altera milestone
        :type milestone: str
        :param thread: Optional - The Altera thread
        :type thread: str
        :param label: Optional - The Altera label
        :type label: str
        :return: The name of the latest REL configuration with a label
        :type return: str
        '''
        # Build the regex in stages, with helper functions as necessary
        base_regex_str = get_rel_config_regex_start(milestone=milestone, thread=thread)
        if label:
            base_regex_str += '--{0}'.format(label)
        else:
            base_regex_str += '--[\w.-]+'
        rel_with_label_regex_str = base_regex_str
        rel_with_label_regex_str += get_rel_config_regex_end()
        regex = re.compile(rel_with_label_regex_str)

        # Get all matches and pass them off to the relevant function to find the last REL
        matches = [x for x in map(regex.search, self.get_configs(project, variant)) if x is not None]
        latest_rel = get_last_REL_from_matches(matches)

        return latest_rel

    def get_next_snap(self, project, variant, snap_name, libtype=None, num=0):
        '''
        Returns the next snap config name given a snap config name
        Returns the next alphabet of snap config
        For example: snap_16ww231 is provided and snap_16ww231a exists
        The next config returned would be snap_16ww231b

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param milestone: The Altera milestone
        :type milestone: str
        :param thread: The Altera thread
        :type thread: str
        :return: The name of the latest REL configuration
        :type return: str
        '''
        if libtype:
            snaps = sorted([x[-1] for x in self.get_library_releases(project, variant, libtype, library='*') if x.startswith(snap_name)])
        else:
            snaps = sorted([x[-1] for x in self.get_configs(project, variant) if x.startswith(snap_name)])
        if snaps:
            latest_alphabet = snaps[-1]
            if latest_alphabet.isalpha():
                next_alphabet = chr(ord(latest_alphabet) + 1 + num)
            else:
                next_alphabet = 'a'
        else:
            next_alphabet = 'a'
        next_snap = '{}{}'.format(snap_name, next_alphabet)
        return next_snap

    def is_name_immutable(self, name):
        if name.startswith(('snap-', 'REL', 'PREL')):
            return True
        return False

    def get_library_release_from_libtype_config(self, project, variant, libtype, config):
        '''
        In Legacy(gdp), the concept of libtype-config is provided into dmx command as such:
            dmx <command> -d ipspec -b dev
        In gdpxl, libtype-config no longer exist. The concept has been changed.
        If it is ipspec/dev (mutable):
            library = dev
            release = None
        elif it is ipspec/snap-1 (immutable):
            release = snap-1
            library = the library that contains the snap-1 release
        return = [library, release]
        '''
        if self.is_name_immutable(config):
            library = self.get_library_from_release(project, variant, libtype, config, retkeys=['name'])
            if not library:
                raise Exception("Release({}) not found for {}/{}:{}".format(config, project, variant, libtype))
            elif library == -1:
                raise Exception("Release({}) found more than once for {}/{}:{}. This is against PSG methodology.".format(config, project, variant, libtype))
            release = config
        else:
            library = config
            release = None
        return [library, release]


    def get_immutable_configs(self, project, variant):
        return [x for x in self.get_configs(project, variant) if x.startswith(('snap-', 'REL', 'PREL'))]

    def get_snap_configs(self, project, variant):
        return [x for x in self.get_configs(project, variant) if x.startswith('snap-')]

    def get_rel_configs(self, project, variant):
        return [x for x in self.get_configs(project, variant) if x.startswith('REL')]

    def get_config(self, project, variant, config, retkeys=['*']):
        '''
        Returns a dictionary representation of the configuration

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param config: The name of the config
        :type config: str
        :param libtype: Optional name of the libtype. Only required for simple configs
        :type libtype: str or None
        :return: Dictionary representation of the configuration
        :rtype: dict
        '''
        return self._get_objects('{}/{}/{}/{}:config/*::content'.format(self.__SITE, project, variant, config), retkeys=retkeys)

    def get_clr_last_modified_data(self, project, variant, clr, libtype=None):
        '''
        Obtains a clr(config/library/release) last modified information.

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param config: The IC Manage configuration
        :type config: str
        :param libtype: The optional IC Manage libtype
        :type libtype: str
        :return: A dictionary describing the date and time (on server) for last modification
        :type return: dict
        :raises: ICManageError
        '''

        if not libtype:
            data = self.get_config_details(project, variant, clr)
        else:
            if self.is_name_immutable(clr):
                library = self.get_library_from_release(project, variant, libtype, clr)
                data = self.get_release_details(project, variant, libtype, library, clr)
            else:
                data = self.get_library_details(project, variant, libtype, clr)

        return self.get_datetime_info_from_string(data['modified'])


    def get_datetime_info_from_string(self, text):
        '''
        This is the datetime string format returned from 'gdp list' commands
            '2020-09-28T11:01:58.110Z'
        Return == {
            'year'      = '2020'
            'month'     = '09'
            'day'       = '28'
            'hours'     = '11'
            'minutes'   = '01'
            'seconds'   = '58'
        }
        '''
        regex = '^(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)\w(?P<hours>\d\d):(?P<minutes>\d\d):(?P<seconds>\d\d)'
        match = re.search(regex, text)
        if match == None:
            return {}
        return match.groupdict()


    def get_release_changenum(self, project, variant, libtype, library, release):
        ret = self._get_objects("{}/{}/{}/{}/{}/{}:release".format(self.__SITE, project, variant, libtype, library, release), retkeys=['change'])
        try:
            return ret[0].lstrip("@")   # ret = "@1234"
        except:
            raise Exception("Release does not exist: {}".format([project, variant, libtype, library, release]))

    # RENAMED: get_previous_configs_with_matching_content
    def get_previous_releases_with_matching_content(self, project, variant, libtype, library, release):
        '''
        Returns a list of configs whose content matches that contained within the last
        release for library

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: List of configs with matching content
        :rtype: list
        '''
        retval = []

        all_releases = self.get_library_releases(project, variant, libtype, library, retkeys=['name', 'change'])
        relchange = self.get_release_changenum(project, variant, libtype, library, release)

        for r in all_releases:
            if r['name'] == release:
                continue
            if '@{}'.format(relchange) == r['change']:
                retval.append(r['name'])
        return retval

    def get_previous_snaps_with_matching_content(self, project, variant, libtype, library, release):
        '''
        Returns a list of snap- configurations with content that matches that contained within
        the last release for library

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: List of snap- configs with content matching the last release for library
        :rtype: list
        '''
        previous_configs = self.get_previous_releases_with_matching_content(project, variant, libtype,
            library=library, release=release)
        return [x for x in previous_configs if x.startswith('snap-')]

    def get_previous_rels_with_matching_content(self, project, variant, libtype, library, release):
        '''
        Returns a list of REL configurations with content that matches that contained within
        the last release for library

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: List of REL configs whose content matches the last release for library
        :rtype: list
        '''
        previous_configs = self.get_previous_releases_with_matching_content(project, variant, libtype,
            library=library, release=release)
        return [x for x in previous_configs if x.startswith('REL')]
            
    def get_next_snap_number(self, project, variant, libtype=None, library=None):
        '''
        Returns the next snap configuration/release number or 1 if there has never been one

        This method is basically used by the TNR system whereby the TNR needs to create a snap-(\d+).

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: Optional libtype. Required for simple configs or composite configs used to release simple configs.
        :type libtype: str or None
        :param simple: Boolean indicating whether or not the number will be used to create a simple config
        :type simple: bool
        :return: The next number to use when generating a snap- config
        :rtype: int
        :raises: ICManageError
        '''
        if libtype and not library:
            raise ICManageError('Cannot get next snap number for a libtype without a library.')
        if library and not libtype:
            raise ICManageError('Cannot get next snap number for a library without a libtype.')

        if libtype:
            retobjs = self.get_library_releases(project, variant, libtype, library)
        else:
            retobjs = self.get_configs(project, variant)

        regex_str = '^snap-(\d+)$'

        snap_regex = re.compile(regex_str)
        snapobjs = [x for x in retobjs if snap_regex.search(x)]
        self.__logger.debug("snapobjs: {}".format(snapobjs))
        if snapobjs:
            sorted_snapobjs = natural_sort(snapobjs)
            last_snap = sorted_snapobjs[-1]
            try:
                ret = int(last_snap.split('-')[1])+1
                return ret
            except ValueError as err:
                raise ICManageError("ValueError when getting next snap number from {0} - {1}".format(last_snap, str(err)))
            except TypeError as err:
                raise ICManageError("TypeError when getting next snap number from {0} - {1}".format(last_snap, str(err)))
        else:
            return 1

    def get_next_tnr_placeholder_number(self, project, variant, libtype):
        '''
        Returns the next tnr-placeholder configuration number or 1 if there has never been one

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :return: The next number to use when generating a tnr-placeholder- config
        :rtype: int
        :raises: ICManageError
        '''
        configs = self.get_configs(project, variant)

        # Filter out to just the tnr-placeholder-<number> configs
        regex_str = '^tnr-placeholder-{}-{}-(\d+)$'.format(variant, libtype)

        placeholder_regex = re.compile(regex_str)
        placeholder_configs = [x for x in configs if placeholder_regex.search(x)]
        if placeholder_configs:
            sorted_placeholder_configs = natural_sort(placeholder_configs)
            last_placeholder = sorted_placeholder_configs[-1]
            try:
                ret = int(last_placeholder.split('-')[-1])+1
                return ret
            except ValueError as err:
                raise ICManageError("ValueError when getting next placeholder number from {0} - {1}".format(last_placeholder, str(err)))
            except TypeError as err:
                raise ICManageError("TypeError when getting next placeholder number from {0} - {1}".format(last_placeholder, str(err)))
        else:
            return 1
   
    def get_cell_names(self, project, variant, library='dev'):
        ''' return all the cells defined in ipspec/cell_names.txt '''
        cellnames = []
        depot_path = '//depot/gdpxl/.../{}/{}/ipspec/{}/cell_names.txt'.format(project, variant, library)
        command = [self.__P4, 'print', '-q', '{}'.format(depot_path)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = 'ICManageCLI.get_cell_names: Error getting cell_names for {}'.format(depot_path)
        error_msg += '\nEXITCODE:{}'.format(exitcode)
        error_msg += '\nSTDOUT:{}'.format(stdout)
        error_msg += '\nSTDERR:{}'.format(stderr)
        self.__logger.debug(error_msg)
        if exitcode == 0 and not stderr:
            for line in stdout.splitlines():
                sline = line.strip()
                if sline and not sline.startswith(("#", "//")):
                    cellnames.append(sline)
        return cellnames


    def get_pvc_from_workspace(self, wspath):
        import dmx.abnrlib.workspace
        ws = dmx.abnrlib.workspace.Workspace(wspath)
        return ws.project, ws.ip, ws.bom

    def get_deliverable_bom(self, project, ip, bom, deliverable, hier='True'):
        from dmx.abnrlib.config_factory import ConfigFactory
        if hier:
            deliverable_bom = [x for x in ConfigFactory().create_config_from_full_name(
            f"{project}/{ip}/{bom}").flatten_tree() if isinstance(x, dmx.abnrlib.icmlibrary.IcmLibrary) if x.libtype == deliverable]
        else:
            deliverable_bom = [x for x in ConfigFactory().create_config_from_full_name(
            f"{project}/{ip}/{bom}").flatten_tree() if isinstance(x, dmx.abnrlib.icmlibrary.IcmLibrary) if x.libtype == deliverable if x.project == project if x.variant == ip]
        
        return deliverable_bom

    def get_cells_from_ipspec_bom(self, project, ip, bom):
        ## return dict cells[project, variant] = cell
        icm = dmx.abnrlib.icm.ICManageCLI()
        ipspec_bom = self.get_deliverable_bom(project, ip, bom, 'ipspec')
        cells = {}
        for cfg in ipspec_bom:
            cell = icm.get_cell_names(cfg.project, cfg.variant, cfg.library)
            cells[cfg.project, cfg.variant] = cell
        return cells

    def get_cells_from_project_ip_bom(self, project, ip, bom):
        icm = dmx.abnrlib.icm.ICManageCLI()
        from dmx.abnrlib.config_factory import ConfigFactory
        overlay_cell = {}
        srcbom_config = [x for x in ConfigFactory().create_config_from_full_name(
            f"{project}/{ip}/{bom}").flatten_tree() if x.is_config()]

        for srccfg in srcbom_config:
            cells = icm.get_cells_from_ipspec_bom(srccfg.project, srccfg.variant, srccfg.name)
            overlay_cell[srccfg.project, srccfg.variant] = cells[srccfg.project, srccfg.variant]
        return overlay_cell


    def get_unneeded_deliverables(self, project, variant, top_cell="*", library='dev'):
        '''
        Returns the output from icmp4 filelog for the specified path

        :param library: library name of the ipspec
        :type library: str
        '''
        uneeded_deliverables_files = []
        depot_path = "//depot/gdpxl/.../{}/{}/ipspec/{}/{}.unneeded_deliverables.txt".format(project, variant, library, top_cell)
        command = [self.__P4, 'files', '{}'.format(depot_path)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        error_msg = 'ICManageCLI.get_unneeded_deliverables: Error getting list of unneeded_deliverables.txt for {}'.format(depot_path)
        error_msg += '\nSTDOUT:{}'.format(stdout)
        error_msg += '\nSTDERR:{}'.format(stderr)
        self.__logger.debug(error_msg)
        if exitcode == 0 and not stderr:
            for line in stdout.splitlines():
                m = re.match('(.*?) - .*', line)
                if m:
                    uneeded_deliverables_files.append(m.group(1))
    
        unneeded_deliverables = []
        for uneeded_deliverables_file in uneeded_deliverables_files:
            unneeded_deliverables = unneeded_deliverables + \
                self.p4_print(uneeded_deliverables_file).splitlines()
                
        return sorted(set(unneeded_deliverables))

    def update_config(self, project, variant, config, includes, description=''):
        '''
        Updates an existing composite config

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param config: The name of the configuration to be updated
        :type config: str
        :param includes: a dictionation with 'add' and 'remove' key, of lists
        :type includes: dict
        :param description: Optional description for the new config
        :type description: str
        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: ICManageError

        Explanation
        ===========
        Making this a bit more user-friendly, the function is built-in with the intelligence to replace an object 
        without having to explicitely telling it to remove the source.

        Here's how it works.
        - the 'includes' dict has 2 keys: 'add' and 'remove'
        - available formats for the items in the $includes['add'/'remove'] list:-
          > project/variant/config
          > project/variant/libtype/library
          > project/variant/libtype/library/release

        Example of 'includes'
        =====================
        The below example will:-
        - add new config i10socfm/liotest3/dev 
        {
            "add": ['i10socfm/liotest3/dev'],
        }
        - replace config i10socfm/liotest2/dev to REL
        {
            "add": ['i10socfm/liotest2/REL'],
        }
        - add new library i10socfm/liotest1/ipspec/dev library
        {
            "add": ['i10socfm/liotest2/ipspec/dev'],
        }
        - replace release i10socfm/liotest1/rtl/dev/REL1 to REL2
        - replace release i10socfm/liotest1/reldoc/dev/REL1 to dev library (mutable)
        {
            "add": [
                'i10socfm/liotest1/rtl/dev/REL2',
                'i10socfm/liotest1/reldoc/dev'],
        }
        '''
        formatted_name = format_configuration_name_for_printing(project, variant, config)

        if not self.preview and not self.config_exists(project, variant, config):
            self.__logger.error("Cannot update {0} as it does not exist.".format(formatted_name))
            return False
        else:
            self.__logger.info("Updating configuration {0}".format(formatted_name))
         

            ### Lionel found out that when the string of the final command gets too long, 
            ### the gdp command does not seem to work. Thus, we have to chop it off into multiple
            ### 'gdp update' calls. 
            limit = 20
            clusters = []
            cluster = {'remove':[], 'add':[]}
            count = 0
            ### Remove first !! Very important
            for cat in ['remove', 'add']:
                if cat in includes:
                    for path in includes[cat]:
                        cluster[cat].append(path)
                        count += 1
                        if count == limit:
                            clusters.append(cluster)
                            cluster = {'remove':[], 'add':[]}
                            count = 0
            if count != 0:
                clusters.append(cluster)

            for includes in clusters:

                ### putting the ** wildcard after site does not work !
                command = [self.__GDP, self._as_gdp_admin(), 'update', '{}/{}/{}/{}'.format(self.__SITE, project, variant, config)]
                # command = [self.__GDP, self._as_gdp_admin(), 'update', '{}/{}/{}/{}'.format(self.__SITE, project, variant, config)]
                if description:
                    command += ['--set', "description='{}'".format(description)]
                command += ['--force']

                pathlist = self._get_objects('{}/{}/{}/{}'.format(self.__SITE, project, variant, config), retkeys=['path', 'type'])

                ### Check for conflicting items. If there are, then remove it first.
                for path in includes.get('add', []):
                    pathtype = self.determine_include_path_object(path)
                    conflict_path = self.get_conflicting_path(path, pathtype, pathlist)
                    if conflict_path:
                        command += ['--remove', conflict_path]

                ### Now that all the conflicting items are added into --remove, we can now
                ### include the user defined --add/--remove.
                for func in ['add', 'remove']:
                    for path in includes.get(func, []):
                        pathtype = self.determine_include_path_object(path)
                        ### putting the ** wildcard after site does not work !
                        command += ['--{}'.format(func), '{}/{}:{}'.format(self.__SITE, path, pathtype)]
                        # command += ['--{}'.format(func), '{}/{}:{}'.format(self.__SITE, path, pathtype)]
                
                self._FOR_REGTEST = command # For regression test
                
                (exitcode, stdout, stderr) = self.__run_write_command(command)
                error_msg = "ICManageCLI.update_config: {}".format(' '.join(command))
                error_msg += "\nSTDOUT: {0}".format(stdout)
                error_msg += "\nSTDERR: {0}".format(stderr)
                self.__logger.debug(error_msg)
                if exitcode != 0:
                    raise ICManageError(error_msg)

            return True

    def determine_include_path_object(self, path):
        if path.count('/') == 2:
            return 'config'
        elif path.count('/') == 3:
            return 'library'
        elif path.count('/') == 4:
            return 'release'
        else:
            raise Exception("Unsupported include path pattern: {}".fromat(path))

    def get_conflicting_path(self, path, pathtype, pathlist):
        '''
        Example:-
            pathlist = [
                [{u'path': u'/intel/i10socfm/liotestfc1/reldoc/dev', u'type': u'library'},
                 {u'path': u'/intel/i10socfm/liotestfc1/rdf/dev', u'type': u'library'},
                 {u'path': u'/intel/i10socfm/liotestfc1/sta/dev', u'type': u'library'},
                 {u'path': u'/intel/i10socfm/liotest1/dev', u'type': u'config'},
                 {u'path': u'/intel/i10socfm/liotest2/dev', u'type': u'config'},
                 {u'path': u'/intel/i10socfm/liotestfc1/ipspec/dev/snap-1', u'type': u'release'}]
       
            path = i10socfm/liotest1/REL123
            pathtype = config
            return =/intel/i10socfm/liotest1/dev 
            
            path = i10socfm/liotestfc1/rdf/dev2
            pathtype = library
            return =/intel/i10socfm/liotestfc1/rdf/dev 

            path = i10socfm/liotestfc1/ipspec/dev
            pathtype = library
            return =/intel/i10socfm/liotestfc1/ipspec/dev/snap-1
        '''
        decomposed_pathlist = {}
        for e in pathlist:
            info = self.decompose_gdp_path(e['path'], e['type'])
            decomposed_pathlist[e['path']] = {
                'type': e['type'],
                'info': info
            }
        pathinfo = self.decompose_gdp_path(path, pathtype)
        self.__logger.debug('pathinfo: {}'.format(pathinfo))

        ### config will only conflict with other config
        if pathtype == 'config':
            for pathlist_path, v in list(decomposed_pathlist.items()):
                if v['type'] == 'config':
                    if pathinfo['project'] == v['info']['project'] and pathinfo['variant'] == v['info']['variant']:
                        if pathinfo['config'] != v['info']['config']:
                            return pathlist_path

        ### library will conflict with other library/release
        ### release will conflict wih other library/release
        elif pathtype in ['library', 'release']:
            for pathlist_path, v in list(decomposed_pathlist.items()):
                if v['type'] in ['library', 'release']:
                    if pathinfo['project'] == v['info']['project'] and pathinfo['variant'] == v['info']['variant'] and pathinfo['libtype'] == v['info']['libtype']:
                        if pathinfo['library'] != v['info']['library']:
                            # library conflict with library
                            return pathlist_path
                        else:
                            if pathtype != v['type']:
                                # library conflict with release, or release conflict with library
                                return pathlist_path
                            if pathtype == 'release' and pathinfo['release'] != v['info']['release']:
                                # release conflict with release:
                                return pathlist_path

        else:
            raise Exception("get_conflicting_path() does not support pathtype:{}".format(pathtype))

        return False

    def decompose_gdp_path(self, path, pathtype=None):
        '''
        If you know the pathtype, it is best to provide it, because it will be faster as
        it does not hit the server for query, and of course, when pathtype is not given,
        the path needs to be an existing object in icm database.

        path = /.../a/b/c, pathtype = config
        return {project: a, variant: b, config: c}
        
        path = /.../a/b/c/d, pathtype = libtype
        return {project: a, variant: b, libtype: c}

        path = /.../a/b/c/d, pathtype = library
        return {project: a, variant: b, libtype: c, library: d}
        
        path = /.../a/b/c/d/e, pathtype = release
        return {project: a, variant: b, libtype: c, library: d, release: e}

        '''
        _type = pathtype
        m = None
        if pathtype == 'project':
            m = re.search('(?P<project>[^/]+)$', path)
        elif pathtype == 'variant':
            m = re.search('(?P<project>[^/]+)/(?P<variant>[^/]+)$', path)
        elif pathtype == 'config':
            m = re.search('(?P<project>[^/]+)/(?P<variant>[^/]+)/(?P<config>[^/]+)$', path)
        elif pathtype == 'libtype':
            m = re.search('(?P<project>[^/]+)/(?P<variant>[^/]+)/(?P<libtype>[^/]+)$', path)
        elif pathtype == 'library':
            m = re.search('(?P<project>[^/]+)/(?P<variant>[^/]+)/(?P<libtype>[^/]+)/(?P<library>[^/]+)$', path)
        elif pathtype == 'release':
            m = re.search('(?P<project>[^/]+)/(?P<variant>[^/]+)/(?P<libtype>[^/]+)/(?P<library>[^/]+)/(?P<release>[^/]+)$', path)
        elif pathtype == None:
            ### need to hit the server and query
            _keys = ['project:parent:name','variant:parent:name','libtype:parent:name', 'library:parent:name','release:parent:name','config:parent:name']
            ret = self._get_objects(path, retkeys=_keys+['type'])[0]
            # Rename keys from project:parent:name to project
            for k in _keys:
                ret[k.split(":")[0]] = ret.pop(k)
        else:
            raise Exception('pathtype:{} not supported.'.format(pathtype))
        if m:
            ret = m.groupdict()
            ret['type'] = pathtype
        return ret

    def del_libtype_config(self, project, variant, libtype, config):
        '''
        Delete a cbtypeonfig

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype 
        :type config: str
        :param config: The IC Manage config
        :type config: str
        :return: Boolan indicating success or failure
        :rtype: bool
        :raises: ICManageError
        '''
        if not self.config_exists(project, variant, config, libtype, is_libtype_config=True):
            error_msg = "Config does not exist: {}/{}/{}/{}".format(project, variant, libtype, config)
            self.__logger.info(error_msg)
            return False
        else:
            command = [self.__GDP, self._as_gdp_admin(), 'delete', '{}/{}/{}/{}/{}:config'.format(self.__SITE, project, variant, libtype, config)]
            self._FOR_REGTEST = command     # for regression test
            (exitcode, stdout, stderr) = self.__run_write_command(command)
            error_msg = "ICManageCLI.del_config: '{}'".format(' '.join(command))
            error_msg += "\nSTDOUT: {0}".format(stdout)
            error_msg += "\nSTDERR: {0}".format(stderr)
            self.__logger.debug(error_msg)
            if exitcode != 0 or stderr:
                raise ICManageError(error_msg)
            else:
                return True
    
    def del_config(self, project, variant, config):
        '''
        Delete a config

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param config: The IC Manage config
        :type config: str
        :return: Boolan indicating success or failure
        :rtype: bool
        :raises: ICManageError
        '''
        if not self.config_exists(project, variant, config):
            error_msg = "Config does not exist: {}/{}/{}".format(project, variant, config)
            self.__logger.info(error_msg)
            return False
        else:
            command = [self.__GDP, self._as_gdp_admin(), 'delete', '{}/{}/{}/{}:config'.format(self.__SITE, project, variant, config)]
            self._FOR_REGTEST = command     # for regression test
            (exitcode, stdout, stderr) = self.__run_write_command(command)
            error_msg = "ICManageCLI.del_config: '{}'".format(' '.join(command))
            error_msg += "\nSTDOUT: {0}".format(stdout)
            error_msg += "\nSTDERR: {0}".format(stderr)
            self.__logger.debug(error_msg)

            ### We can't check for stderr, because 'gdp delete' prints the following message to stderr after a successful deletion
            ###     1 object(s) deleted
            #if exitcode != 0 or stderr:
            if exitcode != 0:
                raise ICManageError(error_msg)
            else:
                return True
   
    ### PLEASE USE THIS WITH CAUTION !!! ###
    def del_release(self, project, variant, libtype, library, release, force=False):
        ''' PLEASE USE THIS WITH CAUTION !!! '''
        if not self.release_exists(project, variant, libtype, library, release):
            error_msg = "Release does not exist: {}/{}/{}/{}/{}".format(project, variant, libtype, library, release)
            self.__logger.info(error_msg)
            return False
        else:
            command = [self.__GDP, self._as_gdp_admin(), 'delete', '{}/{}/{}/{}/{}/{}:release'.format(self.__SITE, project, variant, libtype, library, release)]
            if force:
                command.append('--force')
            self._FOR_REGTEST = command     # for regression test
            (exitcode, stdout, stderr) = self.__run_write_command(command)
            error_msg = "ICManageCLI.del_config: '{}'".format(' '.join(command))
            error_msg += "\nSTDOUT: {0}".format(stdout)
            error_msg += "\nSTDERR: {0}".format(stderr)
            self.__logger.debug(error_msg)

            ### We can't check for stderr, because 'gdp delete' prints the following message to stderr after a successful deletion
            ###     1 object(s) deleted
            #if exitcode != 0 or stderr:
            if exitcode != 0:
                raise ICManageError(error_msg)
            else:
                return True


    #TODO
    def get_flattened_config_details(self, project, variant, config, retkeys=['*']):
        ret = self._get_objects('{}/{}/{}/{}:config/**::content'.format(self.__SITE, project, variant, config), retkeys=retkeys)
        return ret
       
    #TODO: Not sure if we still need this, because now we can release with any changelist number
    def get_list_of_changelists(self, project, variant, libtype, library='dev'):
        '''
        Returns a list of changelist numbers that have not been built into a release

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: List of changelist numbers
        :rtype: list
        :raises: ICManageError
        '''
        changelists = []

        # Because of a bug in IC Manage we can't use the usual delimiter here
        # Using a delimiter with pm release completely changes what it outputs
        # So, we have to handle the standard output format which would normally be hard
        # work but in this instance we only want the first field so it's not so bad
        command = [self.__PM, 'release', '-p', '{}'.format(project), '{}'.format(variant),
            '{}'.format(libtype), '{}'.format(library), '-c']
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode == 0 and not stderr:
            for line in stdout.splitlines():
                fields = minmaxsplit(line, 1, sep=' ', exact_count=False)
                if not fields[0].startswith("Change="):
                    raise ICManageError("get_list_of_changelists: Bad output from IC Manage: {}".format(stdout))

                # change_filed will now be in the format:
                # Change="123"
                # We only want the 123
                (field, value) = fields[0].split('=')
                change_num = value.translate(None, '"')
                try:
                    changelists.append(int(change_num))
                except ValueError:
                    raise ICManageError("'{0}' returned an invalid changelist in line '{1}'".format(
                        command, line) )
        else:
            error_msg = "ICManageCLI.get_list_of_changelists: {}".format(' '.join(command))
            if stdout:
                error_msg += "\nSTDOUT: {0}".format(stdout)
            if stderr:
                error_msg += "\nSTDERR: {0}".format(stderr)

            raise ICManageError(error_msg)

        return changelists

    def get_last_submitted_changelist(self, filespec=''):
        '''
        Retrieves the last submitted changelist number from the repository

        :return: Changelist number
        :type return: int
        :raises: ICManageError
        '''
        ret = 0

        command = [self.__P4, 'changes', '-m', '1', '-s', 'submitted']
        if filespec:
            command.append(filespec)
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode == 0 and not stderr:
            # Output should be one line that looks like:
            # Change 3221930 on 2014/10/13 by liyu@liyu.i14socnd.io_common_custom.9 'lvs clean '
            lines = stdout.splitlines()
            if len(lines) > 1:
                error_msg = "ICManageCLI.get_last_submitted_changelist: {}".format(' '.join(command))
                error_msg += "\nToo many lines returned by icmp4"
                if stdout:
                    error_msg += "\nSTDOUT: {0}".format(stdout)

                raise ICManageError(error_msg)
            else:
                match = re.search('^Change (\d+) on', lines[0])
                if match:
                    ret = int(match.group(1))
                else:
                    error_msg = "ICManageCLI.get_last_submitted_changelist: {}".format(' '.join(command))
                    error_msg += 'Invalid line format returned by icmp4: {0}'.format(stdout)
                    raise ICManageError(error_msg)
        else:
            error_msg = "ICManageCLI.get_last_submitted_changelist: {}".format(' '.join(command))
            if stdout:
                error_msg += "\nSTDOUT: {0}".format(stdout)

            if stderr:
                error_msg += "\nSTDERR: {0}".format(stderr)

            raise ICManageError(error_msg)

        return ret

    #TODO: not sure if we still need this
    def get_last_library_release_number(self, project, variant, libtype, library='dev'):
        '''
        Returns the last release number for the library. Library release numbers are
        sequential integers

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: The last release number for the library
        :rtype: int
        :raises: ICManageError
        '''
        ret = 0
        releases = self.get_library_releases(project, variant, libtype, library=library)
        if releases:
            # I would do this with list comprehension but we want to discard any
            # releases that may creep in that don't follow the correct naming - integers
            # It's unlikely to happen, but just in case...
            release_numbers = []
            for release in releases:
                # Make sure the formatting is correct
                if not 'release' in release:
                    raise ICManageError("ICManageCLI.get_last_library_release_number: pm release has returned data in an invalid format: {0}".format(
                        release
                    ))
                try:
                    release_numbers.append(int(release['release']))
                except ValueError:
                    self.__logger.debug("Found an IC Manage library release that is not an integer: {0}".format(release['release']))
                except TypeError:
                    self.__logger.debug("Found an IC Manage library release that is not an integer: {0}".format(release['release']))
            if release_numbers:
                try:
                    ret = int(sorted(release_numbers)[-1])
                except ValueError as err:
                    raise ICManageError("ICManageCLI.get_last_library_release_number: ValueError: Library release is not an integer - {0}".format(str(err)))
                except TypeError as err:
                    raise ICManageError("ICManageCLI.get_last_library_release_number: TypeError: Library release is not an integer - {0}".format(str(err)))
    
        return ret

    #TODO: not sure if we still need this
    def get_next_library_release_number(self, project, variant, libtype, library='dev'):
        '''
        Returns the next library release number. Library release numbers are sequential
        integers

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: The next release number for the library
        :rtype: int
        '''
        last_release_number = self.get_last_library_release_number(project, variant, libtype, library=library)
        return last_release_number + 1

    #TODO
    def get_group_details(self, groupname):
        '''
        Return a list of userid(string). Return None if group does not exist.
        Uses the 'icmp4 group -o' command to get the details.

        output of 'icmp4 -ztag group -o fln.users
        -----------------------------------------
        ... Group fln.users
        ... MaxResults unset
        ... MaxScanRows unset
        ... MaxLockTime unset
        ... Timeout 5184000
        ... PasswordTimeout unset
        ... Subgroups0 fln.contractors
        ... Owners0 vmkondap
        ... Users0 aalaniz
        ... Users1 aazaddin
        ... Users2 abbasmuh

        '''
        cmd = ('{} -ztag group -o {}'.format(self.__P4, groupname))
        LOGGER.debug(cmd)
        code, stdout, stderr = run_command(cmd)
        if code != 0 or stderr:
            LOGGER.error("'{0}' returned {1}".format(cmd, code))
            LOGGER.error(stderr)
            return None

        if not len(stdout.splitlines()): 
            return None

        details = dict()
        for line in stdout.splitlines():
            sline = line.split()
            if len(sline) >= 3:
                if sline[1].startswith('MaxResults'):
                    details['maxresults'] = sline[2]
                elif sline[1].startswith('MaxScanRows'):
                    details['maxscanrows'] = sline[2]
                elif sline[1].startswith('MaxLockTime'):
                    details['maxlocktime'] = sline[2]
                elif sline[1].startswith('Timeout'):
                    details['timeout'] = sline[2]
                elif sline[1].startswith('PasswordTimeout'):
                    details['passwordtimeout'] = sline[2]
                elif sline[1].startswith('Subgroups'):
                    if 'subgroups' not in details:
                        details['subgroups'] = []
                    details['subgroups'].append(sline[2])
                elif sline[1].startswith('Owners'):
                    if 'owners' not in details:
                        details['owners'] = []
                    details['owners'].append(sline[2])
                elif sline[1].startswith('Users'):
                    if 'users' not in details:
                        details['users'] = []
                    details['users'].append(sline[2])

        return details

    def get_client_detail(self, clientname):
        '''
        Return a dictionary of client details. Returns None if the client doesn't
        exist. Uses the 'icmp4 clients' command to get the details.

        Test with a client that should never exist 
        >>> get_client_detail('this_client_should_not_exist')

        Test with the first client returned by Perforce
        >>> code, stdout, stderr = run_command("icmp4 clients | head -1 | awk '{print $2}'")
        >>> assert(not stderr)
        >>> details = get_client_detail(stdout)
        >>> details.has_key('last_accessed')
        True
        >>> details.has_key('owner')
        True
        >>> details.has_key('root')
        True
        >>> details.has_key('client')
        True
        '''
        cmd = ('{} client -o {}'.format(self.__P4, clientname))
        LOGGER.debug(cmd)
        code, stdout, stderr = run_command(cmd)
        if code != 0 or stderr:
            LOGGER.error("'{0}' returned {1}".format(cmd, code))
            LOGGER.error(stderr)
            return None

        if not len(stdout.splitlines()): 
            return None

        details = dict()
        for line in stdout.splitlines():
            if line.startswith('Access:'):
                match = re.search('\d{4}/\d{2}/\d{2}', line)
                if match:
                    (year, month, day) = list(map(int, match.group().split('/')))
                    details['last_accessed'] = date(year, month, day)
            elif line.startswith('Owner:'):
                details['owner'] = line.split()[-1]
            elif line.startswith('Root:'):
                details['root'] = line.split()[-1]
            elif line.startswith('Client:'):
                details['client'] = line.split()[-1]

            # Bail if we have every key
            # No need to process the entire spec
            if len(details) >= 4:
                break

        # If we're missing the last_accessed field it's likely the client does not exist
        # This is a strange quirk of Perforce where it will always return a client
        # spec, even for clients that don't exist
        if 'last_accessed' not in details:
            details = None

        return details

    def get_workspaces_for_user_by_age(self, user, older_than=0):
        '''
        Get a list of workspaces associated with a particular user ID.
        Non-existent user
        >>> get_workspaces('this_user_does_not_exist')
        []
        
        Assume that the current user exists in ICM and has at least one workspace
        >>> len(get_workspaces(getpass.getuser())) > 0
        True
        
        ### TO get all workspaces for user 'yltan' which has been inactive for > 60 days
        >>> self.get_workspaces('yltan', older_than=60)
        [ ... ]
        '''
        wslist = self.get_workspaces_for_user(user)
        workspaces = self.get_workspaces_by_age(older_than, wslist)
        return workspaces

    def get_workspaces_by_age(self, older_than=0, workspaces=None):
        '''
        If a list of workspaces is specified, then return only those workspaces that are
           inactive for more than the specified days in 'older_than'.
        If workspaces is not specified, then return all available workspaces that are
           inactive for more than the specified days in 'older_than'.
        '''
        if workspaces == None:
            workspaces = self.get_workspaces_for_user()
        
        if older_than == 0:
            return workspaces

        retlist = []
        for wsname in workspaces:
            days = timedelta(days=older_than)
            clientdetails = self.get_client_detail(wsname)
            if clientdetails and 'last_accessed' in clientdetails:
                if (date.today() - days > clientdetails['last_accessed']):
                    retlist.append(wsname)
        return retlist

    def get_workspaces_for_user(self, user=None):
        '''
        Get a list of workspace for a user.
        If user is not specified, get all available workspaces for all users. 
        '''
        workspaces = self.get_workspaces(retkeys=['name', 'created-by'])
        if user:
            workspaces = [x for x in workspaces if x['created-by'] == user]
        return [x['name'] for x in workspaces]

    def get_dict_of_files(self, project, variant, libtype, release=None, library='dev', ignore_project_variant=False):
        '''
        Returns a list of dicts describing files in a library's release

        release: The gdpxl release name
        if release name is given:
            changenum == the changelist number associated to that library relase
        elif release == None:
            changenum == '@now' (latest of the library)
        '''
        
        files = dict()
              
        if not release:
            changelist = 'now'
        else:
            changelist = self.get_release_changenum(project, variant, libtype, library, release)
        depot_path = '//depot/gdpxl/.../{}/{}/{}/{}/...@{}'.format(project, variant, libtype, library, changelist)

        command = [self.__P4, 'files', '{}'.format(depot_path)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
    
        if exitcode == 0 and not stderr:
            for line in stdout.splitlines():
                filename = operation = directory = changelist = version = type = file_directory = ""
                m = re.match("^(.*)\/(.*?)\#(\d+) - (.*?) change (.*?) \((.*?)\)", line)
                if m:
                    directory = m.group(1)
                    filename = m.group(2)
                    version = m.group(3)
                    operation = m.group(4)
                    changelist = m.group(5)
                    type = m.group(6)

                # Key format: //depot/icm/proj/{project}/{variant}/{libtype}:{file}
                regex = ".*\/{}\/{}\/{}\/{}\/(.*)".format(project, variant, libtype, library)
                m = re.match(regex, directory)
                if m:
                    file_directory = m.group(1) 
                
                if ignore_project_variant:
                    if file_directory: 
                        key = "{}:{}/{}".format(libtype, file_directory, filename)
                    else:   
                        key = "{}:{}".format(libtype, filename)
                else:
                    if file_directory:
                        key = "{}/{}/{}:{}/{}".format(project, variant, libtype, file_directory, filename)
                    else:
                        key = "{}/{}/{}:{}".format(project, variant, libtype, filename)
                
                files[key] = dict()
                files[key]['operation'] = operation
                files[key]['changelist'] = changelist
                files[key]['version'] = version
                files[key]['directory'] = directory
                files[key]['filename'] = filename
                files[key]['type'] = type
                files[key]['project'] = project
                files[key]['variant'] = variant
                files[key]['libtype'] = libtype
                files[key]['library'] = library
                files[key]['release'] = release
        else:
            error_msg = "ICManageCLI.get_dict_of_files: {}".format(' '.join(command))
            if stdout:
                error_msg += "\nSTDOUT: {0}".format(stdout)
            if stderr:
                error_msg += "\nSTDERR: {0}".format(stderr)
    
            raise ICManageError(error_msg)

        return files

    #TODO: is this still needed, as now we already can release with any change num.
    def get_library_release_closest_to_changelist(self, project, variant, libtype, library, changelist):
        '''
        Find the library release that is closest to changelist. That is, the release was made against
        a changelist either before or equal to the specified changelist

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param changelist: The Perforce changelist we're interested in
        :type changelist: int
        :return: The release number of the release closest to changelist. 0 if no releases found
        :type return: int
        '''
        closest_release = 0

        for release in self.get_library_releases(project, variant, libtype, library=library):
            try:
                release_changelist = int(release['dev_change'])
            except ValueError:
                # Incremental releases will cause this error
                # We don't support incremental releases but we currently have
                # no mechanism to stop them
                # For now just ignore them
                self.__logger.debug('Skipping incremental release {0}'.format(release['release']))
                continue

            if release_changelist <= changelist and release_changelist > closest_release:
                try:
                    closest_release = int(release['release'])
                except ValueError:
                    # There are some releases in the system that were created
                    # before the Nadder methodology was locked down. These
                    # releases are not integers. We need to capture that
                    # situation and ignore it
                    continue

                # If the release was made against the changelist we're interested in
                # there's no need to continue
                if closest_release == changelist:
                    break

        return closest_release

    #TODO: is this still needed, as now we already can release with any change num.
    def add_library_release_up_to_changelist(self, project, variant, libtype, library,
                                             description, upper_changenum=0):
        '''
        Adds a new library released based upon the last changelist up to (or including)
        upper_changenum.
        Returns the name of the library release

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param description: The description for the release
        :type description: str
        :param upper_changenum: The optional upper changelist number - do not release past this. If
            no upper changelist number is specied releases up to the most recent change
        :type upper_changenum: int
        :return: The name of the IC Manage library release. 0 if no release created
        :type return: int
        '''
        ret = 0
        last_failed_changelist = 0

        # Get all outstanding changelists for the library
        all_changelists = self.get_list_of_changelists(project, variant, libtype, library)
        changelists_for_release = sorted(all_changelists)
        if upper_changenum > 0:
            changelists_for_release = [x for x in changelists_for_release if x <= upper_changenum]

        # First work through the changelists backwards, trying to create a library release
        for changenum in reversed(changelists_for_release):
            try:
                ret = self.add_library_release(project, variant, libtype, changenum,
                                               description, library=library)
                if ret > 0:
                    break
            except AllRevisionsAlreadyIntegratedError:
                msg = 'Detected all revisions already integrated error when releasing changelist {0} for {0}/{1}:{2}/{3}'.format(
                    changenum, project, variant, libtype, library
                )
                msg += '\nAttempting to release previous changelist.'
                self.__logger.info(msg)
                last_failed_changelist = changenum
                pass

        # If we managed to produce a release work forwards, starting from the last failed
        # changelist so that we get the latest content released
        if ret > 0 and last_failed_changelist > 0:
            index = changelists_for_release.index(last_failed_changelist)
            for changenum in changelists_for_release[index:]:
                ret = self.add_library_release(project, variant, libtype, changenum,
                                               description, library=library)

        return ret

    #TODO: is this still needed, as now we already can release with any change num.
    def add_library_release_from_activedev(self, project, variant, libtype, description, library='dev'):
        '''
        Creates a release of a library based upon the changelist referenced by #ActiveDev

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param description: The release description
        :type description: str
        :param library: Optional IC Manage library name. Defaults to 'dev'
        :type library: str
        :return: The number of the newly created release. 0 if there was a problem.
        :rtype: int
        '''
        ret = 0

        changelists = self.get_list_of_changelists(project, variant, libtype, library)
        if changelists:
            # Use the last changelist
            changenum = sorted(changelists)[-1]

            # Create the release
            self.__logger.info("Releasing with changelist {}".format(changenum))
            ret = self.add_library_release(project, variant, libtype, changenum, description,
                                           library=library)

        return ret


    def branch_library(self, source_project, source_variant, source_libtype, source_library, target_library,
                       target_project=None, target_variant=None, target_libtype=None, desc=None, changenum=None, relname=None, target_config=None):
        '''
        #>gdp create library /intel/RegressionTest/regtest/vartest1/sta/dev --from p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotestfc1/ipspec/dev/...@1234
        changenum and relname can not be given together.
        '''
        if not ICMName.is_library_name_valid(target_library):
            raise BadNameError('ICManageCLI.branch_library: {0} is not a valid target library name'.format(target_library))

        # If the optional targets aren't specified set them to source
        if target_project is None:
            target_project = source_project
        if target_variant is None:
            target_variant = source_variant
        if target_libtype is None:
            target_libtype = source_libtype
        if target_config is None:
            target_config = target_library
        if changenum and relname:
            raise Exception("changenum and relname can not be provided together.")
        elif changenum is None and relname is None:
            uri = self.get_library_uri(source_project, source_variant, source_libtype, source_library)
        elif changenum:
            uri = self.get_library_uri(source_project, source_variant, source_libtype, source_library)
            uri = '{}@{}'.format(uri, changenum)
        elif relname:
            uri = self.get_library_uri(source_project, source_variant, source_libtype, source_library, relname)

        if desc is None:
            desc = "Branched from {0}/{1}:{2}/{3}@{4}".format(source_project, source_variant, source_libtype, source_library, relname)

        if self.library_exists(target_project, target_variant, target_libtype, target_library):
            error_msg = "Cannot port {}/{}:{}/{} into {}/{}:{}/{} as the target already exists".format(
                source_project, source_variant, source_libtype, source_library, target_project, target_variant, target_libtype, target_library)
            raise LibraryAlreadyExistsError(error_msg)

        if not self.libtype_exists(target_project, target_variant, target_libtype):
            raise Exception("Cant branch to target_library as target_libtype does not exist. Please create target_libtype first.{}/{}/{}".format(
                target_project, target_variant, target_libtype))

        #>gdp create library /intel/RegressionTest/regtest/vartest1/sta/dev --from p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotestfc1/ipspec/dev/...@1234
        command = [self.__GDP, self._as_gdp_admin(), 'create', 'library', '{}/{}/{}/{}/{}'.format(self.__SITE, target_project, target_variant, target_libtype, target_config)]
        command += ['--from', uri]

        command += ['--set', "location={}".format(self.get_clp(target_variant, target_libtype))]

        self._FOR_REGTEST = command

        (exitcode, stdout, stderr) = self.__run_write_command(command)
        error_msg = "ICManageCLI.branch_library: '{}'".format(' '.join(command))
        error_msg += "\nSTDOUT: {0}".format(stdout)
        error_msg += "\nSTDERR: {0}".format(stderr)
        self.__logger.debug(error_msg)
        if exitcode != 0 or stderr:
            raise ICManageError(error_msg)
        else:
            return True

    def get_library_uri(self, project, variant, libtype, library, relname=None):
        '''
        if not relname:
            uri == p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotestfc1/ipspec/bsnap-1/...
        if relname:
            uri == p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotestfc1/ipspec/bsnap-1/...@1234
        '''
        if not relname:
            path = '{}/{}/{}/{}/{}:library'.format(self.__SITE, project, variant, libtype, library)
        else:
            path = '{}/{}/{}/{}/{}/{}:release'.format(self.__SITE, project, variant, libtype, library, relname)
        return self._get_objects(path, retkeys=['uri'])[0]

    def construct_library_uri(self, project, variant, libtype, library):
        '''
        uri == p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/<project>/<variant>/<libtype>/<library>/...
        '''
        uri = 'p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/{}/{}/{}/{}/...'.format(project, variant, libtype, library)
        return uri
            
    def get_library_clp(self, project, variant, libtype, library):
        return self.get_library_details(project, variant, libtype, library)['location']



    ##############################################################
    ##############################################################
    ### START: Add Properties ###
    ##############################################################
    def _update_properties(self, path, properties):
        '''
        properties: Dictionary of the key=value properties to add to the config
        '''
        command = [self.__GDP, self._as_gdp_admin(), 'update', path]
        for key, val in list(properties.items()):
            command += ['--set', "{}={}".format(key, val)]
        self._FOR_REGTEST = command # for regression tests
        (exitcode, stdout, stderr) = self.__run_write_command(command)
        error_msg = "ICManageCLI._update_properties: {}".format(' '.join(command))
        error_msg += "\nSTDOUT: {0}".format(stdout)
        error_msg += "\nSTDERR: {0}".format(stderr)
        self.__logger.debug(error_msg)
        if exitcode != 0:
            raise ICManageError(error_msg)
        return True 

    def add_config_properties(self, project, variant, config, properties):
        return self._update_properties('{}/{}/{}/{}:config'.format(self.__SITE, project, variant, config), properties)

    def add_workspace_properties(self, workspace, properties):
        return self._update_properties('/workspace/{}'.format(workspace), properties)

    def add_variant_properties(self, project, variant, properties):
        return self._update_properties('{}/{}/{}:variant'.format(self.__SITE, project, variant), properties)
    
    def add_library_properties(self, project, variant, libtype, library, properties):
        return self._update_properties('{}/{}/{}/{}/{}:library'.format(self.__SITE, project, variant, libtype, library), properties)
    
    def add_release_properties(self, project, variant, libtype, library, release, properties):
        return self._update_properties('{}/{}/{}/{}/{}/{}:release'.format(self.__SITE, project, variant, libtype, library, release), properties)
    ##############################################################
    ### END: Add Properties ###
    ##############################################################
    ##############################################################


    ##############################################################
    ##############################################################
    ### START: Get Properties/Details ###
    ##############################################################
    def get_config_details(self, project, variant, config, retkeys=['*']):
        return self._get_objects('{}/{}/{}/{}:config'.format(self.__SITE, project, variant, config), retkeys=retkeys)[0]

    def get_libtype_config_details(self, project, variant, libtype, config, retkeys=['*']):
        '''
        We expect in libtype config there is only 1 lib/relrease content.
        Multiple content in one libtype config should be prohibited
        '''
        return self._get_objects('{}/{}/{}/{}/{}:config/::content'.format(self.__SITE, project, variant, libtype, config), retkeys=retkeys)[0]

    def get_workspace_details(self, workspacename, retkeys=['*']):
        return self._get_objects('/workspace/{}'.format(workspacename), retkeys=retkeys)[0]

    def get_workspace_attributes(self, workspacename):
        data =  self._get_objects('/workspace/{}'.format(workspacename), retkeys=['project:parent:name', 'variant:parent:name', 'config:parent:name', 'libtype:parent:name', 'rootDir', 'p4-client-options'])[0]
        return data

    def get_libtype_library_and_release(self, project, variant, config, libtype):
        '''
        Given project/variant:config and libtype, get the libtype release and config
        '''
        ipspec_bom_info = {}
        config_content_detail = self.get_config_content_details(project, variant, config)
        for ea_config_content in config_content_detail:
            if ea_config_content.get('libtype') == libtype and ea_config_content['type'] == 'release':
                ipspec_bom_info['release'] = ea_config_content.get('name')
                ipspec_bom_info['library'] = self.get_library_from_release(project, variant, libtype, ipspec_bom_info['release'], retkeys=['name'])
            elif ea_config_content.get('libtype') == libtype and ea_config_content['type'] == 'library':
                ipspec_bom_info['library'] = ea_config_content.get('name')
                ipspec_bom_info['release'] = None
        return ipspec_bom_info


    def get_variant_details(self, project, variant):
        return self._get_objects('{}/{}/{}:variant'.format(self.__SITE, project, variant), retkeys=['*'])[0]

    def get_library_details(self, project, variant, libtype, library):
        return self._get_objects('{}/{}/{}/{}/{}:library'.format(self.__SITE, project, variant, libtype, library), retkeys=['*'])[0]

    def get_release_details(self, project, variant, libtype, library, release):
        return self._get_objects('{}/{}/{}/{}/{}/{}:release'.format(self.__SITE, project, variant, libtype, library, release), retkeys=['*'])[0]

    def get_libtype_details(self, project, variant, libtype):
        return self._get_objects('{}/{}/{}/{}:libtype'.format(self.__SITE, project, variant, libtype), retkeys=['*'])[0]

    def get_config_content_details(self, project, variant, config, hierarchy=False, retkeys=['*']):
        postfix = '.*::content'
        if hierarchy:
            postfix = '.**::content'
        ret = self._get_objects('{}/**/{}/{}/{}:config/{}'.format(self.__SITE, project, variant, config, postfix), retkeys=retkeys)
        return ret
    
    def get_parent_child_relationship(self, project, variant, config, hierarchy=False, retkeys=['path', 'content:link:path']):
        postfix = '.*::content'
        if hierarchy:
            postfix = '.**::content'
        return self.get_config_content_details(project, variant, config, hierarchy=hierarchy, retkeys=retkeys)
  
    def get_parent_boms(self, project, variant, config_library_release, libtype=None, hierarchy=False):
        if hierarchy:
            hsyntax = '**'
        else:
            hsyntax = '*'

        if libtype:
            config = None
            [library, release] = self.get_library_release_from_libtype_config(project, variant, libtype, config_library_release)
            if release:
                path = '/intel/{}/{}/{}/{}/{}:release/{}:config:-content'.format(project, variant, libtype, library, release, hsyntax)
            else:
                path = '/intel/{}/{}/{}/{}:library/{}:config:-content'.format(project, variant, libtype, library, hsyntax)
        else:
            library = None
            release = None
            config = config_library_release
            path = '/intel/{}/{}/{}:config/{}:config:-content'.format(project, variant, config, hsyntax)
    
        return self._get_objects(path, retkeys=['variant:parent:name', 'project:parent:name', 'config:parent:name'])
    
 
    ### Creating alias methods 
    get_config_properties = get_config_details
    get_workspace_properties = get_workspace_details
    get_variant_properties = get_variant_details
    get_library_properties = get_library_details
    get_libtype_properties = get_libtype_details
    get_release_properties = get_release_details
    ##############################################################
    ### END: Get Properties ###
    ##############################################################
    ##############################################################


    #TODO Not sure if we still need this. Is this still needed?
    def get_latest_release(self, project, variant, libtype, library='dev', relchange=False):
        '''
        Get the latest release for the library.

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: Optional IC Manage library. Defaults to 'dev'
        :type library: str
        :param relchange: Optional boolean indicating whether to use the dev_change or rel_change value for comparisons. Defaults to False.
        :type: bool
        :return: A dictionary containing information about the latest release or None if there are no releases for the library
        :rtype: dict or None
        '''
        releases = self.get_library_releases(project, variant, libtype, library)
        latest_release = None
        for release in releases:
            # Make sure if we're looking at the dev_change field it's an integer
            # If it's not just skip this release
            if not relchange:
                try:
                    int(release['dev_change'])
                except ValueError:
                    continue

            if latest_release is None:
                latest_release = release
            elif relchange and int(release['rel_change']) > int(latest_release['rel_change']):
                latest_release = release
            elif int(release['dev_change']) > int(latest_release['dev_change']):
                latest_release = release
                            
        return latest_release

    def get_activedev_changenum(self, project, variant, libtype, library):
        '''
        Returns the latest change number for a library. This will either be the
        latest change number that hasn't been released or, if there are no
        outstanding changes, the change number associated with the last release

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :return: The latest change number for a library. 0 if there was a problem
        :rtype: int
        '''
        ret = 0
        command = [self.__P4, '-ztag', '-F', '%change%', 'changes', '-m1', '//depot/gdpxl{}/...{}/{}/{}/{}/...'.format(self.__SITE, project, variant, libtype, library)]
        exitcode, stdout, stderr = self.__run_read_command(command)
        self.__logger.debug("get_activedev_changenum: {}\nstdout:{}\nstderr:{}".format(command, stdout, stderr))
        return int(stdout.strip())

    #TODO Is this still needed?
    def get_activerel_changenum(self, project, variant, libtype, library, relchange=False):
        '''
        Gets the changelist number associated with activerel

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param relchange: Boolean indicating whether or not to return the dev changelist or icmrel changelist
        :type relchange: bool
        :return: The changelist number associated with #ActiveRel
        :rtype: int
        '''
        ret = 0
        rel = self.get_latest_release(project, variant, libtype, library, relchange=relchange)
        if rel:
            if relchange:
                ret = rel['rel_change']
            else:
                ret = rel['dev_change']

        return int(ret)

   
    #TODO Not sure if we still need this, since we already have get_release_changenum()
    def get_named_release_changenum(self, project, variant, libtype, library, release, relchange=False):
        '''
        Gets the changelists number associated with the release

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param release: The IC Manage library release
        :type release: str
        :param relchange: Optional boolean indicating whether to return the dev or icmrel changelist. Defaults to False.
        :type relchange: bool
        :return: Changelist number associated with the release
        :rtype: int
        :raises: UnreleasedLibraryError
        '''
        ret = 0
        releases = self.get_library_releases(project, variant, libtype, library=library)
        if releases:
            for rel in releases:
                if rel['release'] == release:
                    if relchange:
                       ret = rel['rel_change']
                    else:
                       ret = rel['dev_change']

                    break

            if ret == 0:
                raise UnreleasedLibraryError("Couldn't find release {0}/{1}:{2}/{3}@{4}".format(
                    project, variant, libtype, library, release))
        else:
            raise UnreleasedLibraryError("Asked for the change number for {0}/{1}:{2}/{3}@{4} but no releases found".format(
                project, variant, libtype, library, release))

        return int(ret)


    #TODO Not sure if we still need this, since we already have get_release_changenum()
    def get_changenum(self, project, variant, libtype, library, release, relchange=False):
        '''
        Get the changelist number for a release.
        Release can be an actual release, #ActiveDev or #ActiveRel

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param release: The IC Manage library release number, #ActiveDev or #ActiveRel
        :type release: str
        :param relchange: Optional boolean indicating whether to return the dev or icmrel changelist. Defaults to False.
        :type relchange: bool
        :return: Changelist number associated with the release
        :rtype: int
        :raises: UnreleasedLibraryError
        '''
        ret = 0


        # Some pm commands use #ActiveDev, others use #dev so we need
        # to accomodate both
        if release == '#ActiveDev' or release == '#dev':
            if relchange:
                raise UnreleasedLibraryError("Cannot get release branch change number for activedev libraries")
            else:
                ret = self.get_activedev_changenum(project, variant, libtype, library)
        elif release == '#ActiveRel' or release == '#rel':
            ret = self.get_activerel_changenum(project, variant, libtype, library, relchange=relchange)
        else:
            ret = self.get_named_release_changenum(project, variant, libtype, library, release,
                relchange=relchange)

        return ret

    def get_icmanage_build_number(self):
        '''
        Gets the IC Manage build number

        :return: The build number for the IC Manage client tools being used
        :rtype: int
        :raises: ICManageError
        '''
        ret = 0
        command = [self.__GDP, self._as_gdp_admin(), 'info']
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        m = re.search(r'GDP XL Build (\d+)', stdout)
        if m and exitcode == 0:
        #if m and exitcode == 0 and not stderr:
            ret = int(m.group(1))
        
        if ret == 0:
            raise ICManageError("Cannot determine IC Manage build number. Please check you have the correct ARC resources.")

        return ret

    def pending_changelists_exist(self, workspace):
        changelists = []
        changelists = self.get_pending_changelists(workspace)
        if len(changelists) == 0:
            return False
        
        for change in changelists:
            LOGGER.info("Pending Changelist: " + change['change'] + " \"" + change['desc'].strip() + "\" by " + change['user'])
        return True

    def is_workspace_up_to_date(self, wsroot):
        command = 'rebuild-workspace {} --pretend'.format(wsroot)
        exitcode, stdout, stderr = run_command(command)
        if 'workspace is up-to-date' in stdout+stderr:
            return True
        else:
            return False

    def is_dir_an_icm_workspace(self, dirname):
        ''' 
        for some unknown reason, dm.ICManageWorkspace spits out an logging.warning() to stderr 
        whenever the given dirname is not within an icmanage workspace. There is no easy way to 
        suppress it. Thus this function.
        Return 1 if it is an ICM workspace, else 0.
        '''
        _stderr = sys.stderr
        null = open(os.devnull, 'wb')
        sys.stderr = null
        ret = 0
        
        import dmx.dmlib.ICManageWorkspace
        try:
            dmx.dmlib.ICManageWorkspace.ICManageWorkspace(dirname)
            ret = 1
        except dmx.dmlib.ICManageWorkspace.dmError:
            ret = 0
        except:
            ret = 0
        null.close()
        sys.stderr = _stderr
        return ret

    def get_pending_changelists(self, workspace):
        '''
        Get pending changelist in specified workspace.
        Perform parsing output of 'icmp4 -G changes' using marshal.
        Return change numbers in a list.
        Return a blank list if no pending changelist.
        Marshal object format:
        {'status': 'pending',
         'code': 'stat',
         'changeType': 'public',
         'client': 'ywoi.t20socanf.hssi_subsystem_nf5.2',
         'user': 'ywoi',
         'time': '1358767425',
         'change': '525921',
         'desc': 'Added wreal model for atb ports'}
     
        Success will get a list.
        '''
        changelists = []
        command = self.__P4 + " -G changes -s pending -c %s" % workspace
        for result in self.__get_marshal_output(command):
            if not('change' in result and 'client' in result):
                raise RuntimeError("running icmp4 command '%s': %s" %
                                  (cmd, "Invalid output format"))
            changelists.append(result)
        return changelists
   
    def opened_files_exist(self, workspace):
        opened_files = []
        opened_files = self.get_opened_files(workspace)
        if len(opened_files) == 0:
            return False
        for file in opened_files:
            LOGGER.info("Opened File: " + file['clientFile'] + " by " + file['user'])
        return True
 
    def get_opened_files(self, workspace):
        '''
	    Get files opened (for add or edit) in specified workspace
        Perform parsing output of 'icmp4 -G opened' using marshal.
        Return file/workspace pairs in a list.
        Return a blank list if no opened file.
        Marshal object format:
        {'code': 'stat',
         'haveRev': 'none',
         'rev': '1',
         'clientFile':'//ywoi.t20socanf.hssi_subsystem_nf5.2/pm_aux/oa/pm_aux/
                         pm_atb_comp/schematic_v1/data.dm',
         'client': 'ywoi.t20socanf.hssi_subsystem_nf5.2',
         'user': 'ywoi',
         'action': 'add',
         'type': 'binary+l',
         'depotFile': '//depot/icm/proj/t20socanf/pm_aux/oa/pm_aux/pm_atb_comp/
                         schematic_v1/data.dm',
         'change': 'default'}
         
        Success will get a list.
        '''
        opened_files = []
        command = self.__P4 + " -G opened -a -C %s" % workspace
        for result in self.__get_marshal_output(command):
            if not('depotFile' in result and 'client' in result):
                raise RuntimeError("running icmp4 command '%s': %s" %
                                  (cmd, "Invalid output format"))
            opened_files.append(result)
        return opened_files

    def get_filelog(self, depot_path):
        '''
        Returns the output from icmp4 filelog for the specified path

        :param depot_path: Path to file
        :type depot_path: str
        :return: filelog output
        :type return: list
        :raises: ICManageError
        '''
        output = []
        command = [self.__P4, 'filelog', '{}'.format(depot_path)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode == 0 and not stderr:
            output = stdout.splitlines()
        else:
            error_msg = 'ICManageCLI.get_filelog: Error getting filelog for {}'.format(depot_path)
            if stdout:
                error_msg += '\nSTDOUT:{}'.format(stdout)
            if stderr:
                error_msg += '\nSTDERR:{}'.format(stderr)
            raise ICManageError(error_msg)
        return output

    def get_workspace_name_from_path(self, fullpath):
        '''
        command = [self.__P4, 'info', '-s']
        with dmx.utillib.contextmgr.cd(fullpath):
            (exitcode, stdout, stderr) = self.__run_read_command(command)
        '''
        command = 'cd {}; {} info -s'.format(fullpath, self.__P4)
        exitcode, stdout, stderr = run_command(command)

        error_msg = 'ICManageCLI.get_workspace_name_from_path: fullpath: {}'.format(fullpath)
        error_msg += '\nSTDOUT:{}'.format(stdout)
        error_msg += '\nSTDERR:{}'.format(stderr)
        self.__logger.debug(error_msg)
        try:
            m = re.search("Client name: (\S+)", stdout)
            return m.group(1)
        except Exception as e:
            raise Exception(error_msg + str(e))

    # TODO we don't have 'icmp4 library' command anymore. Need to write somethine else 
    def get_workspace_library_info(self, workspace_path):
        '''
        [{'developer': 'true',                                                                                                                   
          'library': 'dev',
          'libtype': 'upf_rtl',
          'project': 'i10socfm',
          'variant': 'liotest1'},
         {'developer': 'true',
          'library': 'dev',
          'libtype': 'upf_netlist',
          'project': 'i10socfm',
          'variant': 'liotest1'},
          ...   ...   ...]
        '''
        retlist = []
        wsname = self.get_workspace_name_from_path(workspace_path)
        data = self._get_objects('/workspace/{}/**::content/:library,release'.format(wsname), retkeys=['type', 'path'])
        for d in data:
           retlist.append(self.decompose_gdp_path(d['path'], d['type']))
        return retlist

    def get_change_info(self, changelist):
        '''
        Returns the output from icmp4 describe for the specified changelist

        :param changelist: Changelist ID
        :type changelist: str
        :return: changelist info (describe)
        :type return: list
        :raises: ICManageError
        '''
        output = []
        command = [self.__P4, 'describe', '{}'.format(changelist)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode == 0 and not stderr:
            output = stdout.splitlines()
        else:
            error_msg = 'ICManageCLI.get_change_info: Error getting change info for {}'.format(changelist)
            if stdout:
                error_msg += '\nSTDOUT:{}'.format(stdout)
            if stderr:
                error_msg += '\nSTDERR:{}'.format(stderr)
            raise ICManageError(error_msg)
        return output

    def get_change_description(self, changelist):
        '''
        Returns the description of the changelist

        :param changelist: Changelist ID
        :type changelist: str
        :return: changelist description
        :type return: str
        :raises: ICManageError
        '''
        ret = ''
        keyword = '... Description '
        command = [self.__P4, '-ztag', 'change', '-o', '{}'.format(changelist)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode == 0 and not stderr:
            output = stdout.splitlines()
            start = False
            for line in output:
                if not start and line.startswith(keyword):
                    ret = line.replace(keyword, '')
                    start = True
                elif start:
                    if line.startswith('...'):
                        start = False
                    else:
                        ret += line
        else:
            error_msg = 'ICManageCLI.get_change_info: Error getting change info for {}'.format(changelist)
            if stdout:
                error_msg += '\nSTDOUT:{}'.format(stdout)
            if stderr:
                error_msg += '\nSTDERR:{}'.format(stderr)

            raise ICManageError(error_msg)
        return ret

    def get_changes(self, filespec):
        '''
        Gets a list of all changes made against filespec

        :param filespec: A Perforce files spec
        :type filespec: str
        :return: List of changes
        :type return: list
        :raises: ICManageError
        '''

        command = [self.__P4, 'changes', '{}'.format(filespec)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)
        if exitcode != 0 or stderr:
            error_msg = 'ICManageCLI.get_changes: Error getting changes for {}'.format(filespec)
            if stdout:
                error_msg += '\nSTDOUT:{}'.format(stdout)
            if stderr:
                error_msg += '\nSTDERR:{}'.format(stderr)

            raise ICManageError(error_msg)

        return stdout.splitlines()

    def p4_print(self, filespec, quiet=True):
        '''
        Runs icmp4 p4print on the filespec
        Returns the output of p4 print

        :param filespec: The Perforce filespec to print
        :type filespec: str
        :param quiet: Optional boolean indicating whether or not to print in quiet mode.
            Quiet mode only prints file contents, not meta data. Defaults to True.
        :type quiet: bool
        :return: The output from p4 print
        :rtype: str
        :raises: ICManageError
        '''
        print_output = ''

        #DI483: Use p4print instead of print as print returns error if client isn't found
        command = [self.__P4, 'p4print']
        command = [self.__P4, 'print']
        if quiet:
            command += ['-q']

        command += ['{}'.format(filespec)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        err_msg = 'Problem running {0} - returned {1}'.format(' '.join(command), exitcode)
        err_msg += '\nSTDOUT: {}'.format(stdout)
        err_msg += '\nSTDERR: {}'.format(stderr)
        self.__logger.debug(err_msg)
        if exitcode != 0 or stderr:
            raise ICManageError(err_msg)
        else:
            print_output = stdout

        return print_output

    def get_file_size(self, filespec):
        '''
        Runs icmp4 sizes on the filespec
        Returns the output of icmp4 sizes

        :param filespec: The Perforce filespec
        :type filespec: str
        :return: The output from icmp4 sizes
        :rtype: str
        :raises: ICManageError
        '''
        size = ''

        command = [self.__P4, 'sizes']

        command += ['{}'.format(filespec)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode != 0 or stderr:
            err_msg = 'Problem running {0} - returned {1}'.format(
                ' '.join(command), exitcode
            )
            if stdout:
                err_msg += '\nSTDOUT: {}'.format(stdout)
            if stderr:
                err_msg += '\nSTDERR: {}'.format(stderr)
            raise ICManageError(err_msg)
        else:
            m = re.match(r'\S*\s(.*?)\s\S*', stdout)
            if m:
                size = m.group(1)

        return int(size)

    def get_file_diff(self, first_filespec, second_filespec):
        '''
        Runs icmp4 diff2 on the filespecs
        Returns the file's differences

        :param filespec: The Perforce filespec 
        :type filespec: str
        :return: File's type
        :rtype: str
        :raises: ICManageError
        '''
        command = [self.__P4, 'diff2']

        command += ['{}'.format(first_filespec), '{}'.format(second_filespec)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode != 0 or stderr:
            err_msg = 'Problem running {0} - returned {1}'.format(
                ' '.join(command), exitcode
            )
            if stdout:
                err_msg += '\nSTDOUT: {}'.format(stdout)
            if stderr:
                err_msg += '\nSTDERR: {}'.format(stderr)
            raise ICManageError(err_msg)
        else:
            for line in stdout.split('\n'):
                m = re.search(r'==== identical', line)
                if m:
                    return ''

        return stdout
    
    def get_file_type(self, filespec):
        '''
        Runs icmp4 fstat on the filespec
        Returns the file's type

        :param filespec: The Perforce filespec 
        :type filespec: str
        :return: File's type
        :rtype: str
        :raises: ICManageError
        '''
        type = ''

        command = [self.__P4, 'fstat', '-Ol']

        command += ['{}'.format(filespec)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode != 0 or stderr:
            err_msg = 'Problem running {0} - returned {1}'.format(
                ' '.join(command), exitcode
            )
            if stdout:
                err_msg += '\nSTDOUT: {}'.format(stdout)
            if stderr:
                err_msg += '\nSTDERR: {}'.format(stderr)
            raise ICManageError(err_msg)
        else:
            for line in stdout.split('\n'):
                m = re.match(r'.*headType\s(.*?)$', line)
                if m:
                    type = m.group(1)
                    break

        return str(type)

    def get_file_digest(self, filespec):
        '''
        Runs icmp4 fstat on the filespec
        Returns the output of file's digest (MD5) using fstat

        :param filespec: The Perforce filespec 
        :type filespec: str
        :return: File's digest(MD5)
        :rtype: str
        :raises: ICManageError
        '''
        digest = ''

        command = [self.__P4, 'fstat', '-Ol']

        command += ['{}'.format(filespec)]
        (exitcode, stdout, stderr) = self.__run_read_command(command)

        if exitcode != 0 or stderr:
            err_msg = 'Problem running {0} - returned {1}'.format(
                ' '.join(command), exitcode
            )
            if stdout:
                err_msg += '\nSTDOUT: {}'.format(stdout)
            if stderr:
                err_msg += '\nSTDERR: {}'.format(stderr)
            raise ICManageError(err_msg)
        else:
            for line in stdout.split('\n'):
                m = re.match(r'.*digest\s(.*?)$', line)
                if m:
                    digest = m.group(1)
                    break

        return str(digest)

    #TODO
    def activate_user(self, users):
        '''
        Take in a list of user and activate the user license
        '''
        for user in users:
            if not self.is_user_exist(user):
                raise ICMAdminError('No such user - {}'.format(user))

            cmd = '{} user -a {}'.format(self.ACTIVATION_PM, user)
            logger.debug(cmd)
            try:
                result = subprocess.check_output([cmd], stderr=subprocess.STDOUT, shell=True)
                logger.info('User \'{}\' is activated'.format(user))
            except subprocess.CalledProcessError:
                raise ICMAdminError('User are not activated')

    #TODO
    def deactivate_user(self, users):
        '''
        Take in a list of user and deactivate the user license
        '''
        for user in users:
            if not self.is_user_exist(user):
                raise ICMAdminError('No such user - {}'.format(user))

            cmd = '{} user -d {}'.format(self.ACTIVATION_PM, user)
            logging.debug(cmd)
            try:
                result = subprocess.check_output([cmd], shell=True)
                logging.info('User \'{}\' is deactivated'.format(user))
            except subprocess.CalledProcessError:
                raise ICMAdminError('User are not deactivated.')

    def is_current_server_dev(self):
        return True if 'dev' in self._get_current_server() else False

    def _get_current_server(self):
        return self.get_icmanage_info()['Server address']
   
    #TODO
    def user_has_icm_license(self, userid=None):
        '''
        Return:
            True/False
        '''
        '''
        if not userid:
            userid = os.getenv("USER")
        if self._user_has_pm_license(userid) and self._user_has_icmp4_license(userid):
            self.__logger.debug("User has icm-license")
            return True
        self.__logger.debug("User does not have icm-license")
        return False
        '''
        ### For now, do this:-
        if not userid:
            userid = os.getenv("USER")
        cmd = 'xlp4 users {}'.format(userid)
        exitcode, stdout, stderr = run_command(cmd)
        if '({}) accessed'.format(userid) in stdout:
            self.__logger.debug("User has icm-license")
            return True
        else:
            self.__logger.debug("User does not have icm-license.\n- exitcode: {}\n- stdout: {}\n- stderr: {}\n".format(exitcode, stdout, stderr))
            return False

    #TODO
    def _user_has_pm_license(self, userid):
        '''
        Command:
            >pm user -l $USER; echo $?
        User With License:
            User="lionelta" Name="Tan, Yoke Liang" Email="yoke.liang.tan@intel.com"
            0
        User Without License:
            Couldn't initialize local site permission tables:
            User jwquah doesn't exist.
            255
        Return:
            True/False
        '''
        cmd = 'pm user -l {}'.format(userid)
        exitcode, stdout, stderr = run_command(cmd)
        self.__logger.debug("cmd: {}\n- stdout: {}\n- stderr: {}\n".format(cmd, stdout, stderr))
        if 'User=' in stdout and 'Name=' in stdout and 'Email' in stdout:
            self.__logger.debug("> YES")
            return True
        self.__logger.debug("> NO")
        return False

    #TODO
    def _user_has_icmp4_license(self, userid):
        '''
        Command:
            >icmp4 -u icmAdmin users $USER; echo $?
        User With License:
            lionelta <yoke.liang.tan@intel.com> (Tan, Yoke Liang) accessed 2019/12/09
            0
        User Without License:
            jwquah - no such user(s).
            0
        Return:
            True/False
        '''
        cmd = 'icmp4 -u icmAdmin users {}'.format(userid)
        exitcode, stdout, stderr = run_command(cmd)
        self.__logger.debug("cmd: {}\n- stdout: {}\n- stderr: {}\n".format(cmd, stdout, stderr))
        if 'accessed' in stdout:
            self.__logger.debug("> YES")
            return True
        self.__logger.debug("> NO")
        return False

    #TODO
    def __format_command_for_armor(self, command):
        '''
        Returns the command formatted for armor
        Simply, it remove the first instance of icmAdmin it finds
        Only does this if we're on an armored build
        '''
        if is_armored(self.build_number):
            if 'icmAdmin' in command:
                command.remove('icmAdmin')

    #TODO
    def __run_command_as_user(self, command, user_id):
        '''
        Runs a command as the specified user and returns the result

        :param command: The command to execute
        :type command: list
        :param user_id: The user ID to run as
        :type user_id: str
        :return: A tuple of exitcode, stdout and stderr
        :type return: tuple
        '''
        try:
            # If we're trying to be the immutable user, user the specific method
            if user_id == self.__IMMUTABLE_USER:
                self.login_as_immutable()
            else:
                self.login_as_user(user_id)

            with run_as_user(user_id):
                (exitcode, stdout, stderr) = self.__run_write_command(command)
        finally:
            self.logout_as_user(user_id)

        return (exitcode, stdout, stderr)

    #TODO
    def __get_icmmgr_ticket(self):
        '''
        Checks for and returns the icmmgr ticket
        '''
        print_output = self.p4_print('//depot/admin/ticket.icmmgr')
        if not print_output:
            raise ICManageError("Cannot read icmmgr ticket")
        ticket = print_output.strip()
        return ticket

    #TODO
    def __get_server_names(self):
        '''
        Returns a set containing the server names from IC Manage
        '''
        servers = set()

        print_output = self.p4_print('//depot/admin/ticket.servers')
        if not print_output:
            servers.add('sj-ice-icm.altera.com:1686')
        else:
            for line in print_output.strip().split('\n'):
                line = line.strip()
                if line and line[0] != '#' and re.match(r'[^:]+:\d+$', line):
                    servers.add(line)

        return servers

    #TODO
    def __get_servers_from_ticket(self, ticket, ticketpath):
        '''
        Gets the servers from the ticket
        '''
        seen_servers = set()
        regex = re.compile('(.*)=icmAdmin:{0}$'.format(ticket))
        with open(ticketpath, 'r') as f:
            for line in f:
                m = regex.match(line)
                if m:
                    server = m.group(1)
                    seen_servers.add(server)

        return seen_servers

    #TODO
    def __add_servers_to_ticket(self, servers, ticketpath, ticket):
        '''
        Adds each server in servers to the ticket at ticketpath
        '''
        # Unlock the ticket, remove obsolete entries, add current entries, relock
        self.__run_write_command(["chmod",  "600", "{}".format(ticketpath)],
            print_command=False)
        lines = []
        with open(ticketpath, 'r') as f:
            for line in f:
                m = re.match(r'(.*)=icmAdmin:', line)
                if not m:
                    lines.append(line)
                elif m.group(1) not in servers:
                    lines.append(line)
                # else skip the line

        for server in servers:
            lines.append("{0}=icmAdmin:{1}\n".format(server, ticket))
        with open(ticketpath, 'w') as f:
            for line in sorted(lines):
                f.write(line)
        self.__run_write_command(["chmod", "400", "{}".format(ticketpath)],
            print_command=False)

    def __cmp__(self, other):
        return self.__dict__ == other.__dict__

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__dict__ == other.__dict__

@memoized
def convert_config_name_to_icm(config_name):
    '''
    Converts an Altera style configuration name into a 
    dict describing the IC Manage objects
    Altera naming convention: <project>/<variant>[:libtype]@<config>

    :param altera_name: The Altera formatted configuration name
    :type altera_name: str
    :return: Dictionary of the components of the Altera formatted name (project, variant, config and optional libtype)
    :rtype: dict
    :raises: BadNameError
    '''
    ret = dict()

    if not re.search('^(\w+)/(\w+)@([\w\.-])+$', config_name) and not re.search('^(\w+)/(\w+):(\w+)@([\w\.-]+)$', config_name):
        raise BadNameError("{0} is in an invalid format. Valid formats are: <project>/<variant>@<config> or <project>/<variant>:<libtype>@<config>".format(
            config_name
        ))

    # First get the config name
    (tree, config) = config_name.split('@')
    ret['config'] = config

    # Now split the project and variant
    (project, remainder) = tree.split('/')
    ret['project'] = project

    # Finally we need to figure out if this is a simple or
    # composite configuration. If there's a : it's simple
    if ':' in remainder:
        (variant, libtype) = remainder.split(':')
        ret['variant'] = variant
        ret['libtype'] = libtype
    else:
        ret['variant'] = remainder

    return ret

def convert_gdpxl_config_name_to_icm(config_name):
    '''
    Same as convert_config_name_to_icm, except this is for gdpxl.
    The config_name is the output returned from 
    - IcmConfig.get_full_name()
    - IcmLibrary.get_full_name()

    config_name == 'a/b/c'
        ret['project'] = 'a'
        ret['variant'] = 'b'
        ret['libtype'] = ''
        ret['library'] = ''
        ret['release'] = ''
        ret['config'] = 'c'
    
    config_name == 'a/b/c/d'
        ret['project'] = 'a'
        ret['variant'] = 'b'
        ret['libtype'] = 'c'
        ret['library'] = 'd'
        ret['release'] = ''
        ret['config'] = ret['library']

    config_name == 'a/b/c/d/e'
        ret['project'] = 'a'
        ret['variant'] = 'b'
        ret['libtype'] = 'c'
        ret['library'] = 'd'
        ret['release'] = 'e'
        ret['config'] = ret['release']
    '''
    ret = {'project':'', 'variant':'', 'libtype':'', 'library':'', 'release':'', 'config':''}
    s = config_name.split('/')
    if len(s) == 3:
        ret['project'] = s[0]
        ret['variant'] = s[1]
        ret['libtype'] = ''
        ret['library'] = ''
        ret['release'] = ''
        ret['config'] = s[2]
    elif len(s) == 4:
        ret['project'] = s[0]
        ret['variant'] = s[1]
        ret['libtype'] = s[2]
        ret['library'] = s[3]
        ret['release'] = ''
        ret['config'] = ret['library']
    elif len(s) == 5:
        ret['project'] = s[0]
        ret['variant'] = s[1]
        ret['libtype'] = s[2]
        ret['library'] = s[3]
        ret['release'] = s[4]
        ret['config'] = ret['release']
        if not ret['release'].startswith(("REL", "PREL", "snap-")):
            raise BadNameError("{} is an invalid format because releasename does not start with a matching release prefix.".format(config_name))
    else:
        raise BadNameError("""{0} is in an invalid format. Valid formats are: 
            project/variant/config
            project/variant/libtype/library
            project/variant/libtype/library/release
            """.format(config_name))

    return ret

## @}
