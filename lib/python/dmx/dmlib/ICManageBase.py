#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012, 2013, 2014 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageBase.py#1 $

"""
ICManageBase is the base class for interfaces to IC Manage.
"""

from past.builtins import basestring
from builtins import object
import os
import json
import subprocess
import sys
from dmx.dmlib.dmError import dmError

def which (program):
    '''
    Find the executable in the user's path, like UNIX `which`.
    
    Copied from
    `Stack Overflow <http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python>`_.
    '''
    assert type (program) is str
    
    def isExe(fpath):
        '''Return true if `fpath` is an executable file.'''
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    #fpath, fname = os.path.split(program); 
    fpath = os.path.split(program) [0] 
    if fpath:
        if isExe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exeFile = os.path.join(path, program)
            if isExe(exeFile):
                return exeFile

    return None


def isUserLoggedIn():
    '''
    Check if the user is logged in to ICManage.
    Returns: 
        True/False if yes/no 
        raises exception if icmp4 is not available, or if behaves strangely.
    '''
    if which('xlp4') is None:
        raise dmError(
            "IC Manage is not available because the 'icmp4' command is not "
            "available.")

    if which('gdp') is None:
        raise dmError(
            "IC Manage is not available because the 'gdp' command is not "
            "available.")
        
    commandOutput = ''
    command = ['gdp', 'login', '--check']
    
    try:
        commandOutput = subprocess.check_output(command)
        commandOutput = commandOutput.decode()
    except subprocess.CalledProcessError as error:
        commandOutput = error.output
   
    if 'is logged in' in commandOutput:
        return True
    
    return False

#As per: http://fogbugz.altera.com/default.asp?245583
#   
#Hard-code exception if current user is not logged in
# ...moving the check in vp.py (main)
#if not isUserLoggedIn():
#    msg = ("ICM account not authenticated for the current user!\n"
#           "Please use the 'icmp4 login -a' command to authenticate "
#               "with your Windows password!\n")
#    print 'msg'
#    sys.exit (1)    


class ICManageBase(object):
    '''ICManageBase is the base class for IC Manage APIs.
    
    Class Documentation
    ==========================
    '''

    # no more pm command pending remove
    @classmethod
    def _queryGDP(cls, gdpCommandArgs):
        '''Run the specified `gdp` command and return a Python representation
        of the command output as decoded from the `gdp` command JSON output.
        Return None if no data was found.
        
        Throw a :class:`subprocess.CalledProcessError` exception if the `gdp`
        command exits with a nonzero exit status.
        
        >>> libtypes = ICManageBase._queryGDP(('libtype', '-L')) 
        >>> 'LibType' in libtypes[0]
        True
        '''
        _gdpCommandArgs = list(gdpCommandArgs)
        _gdpCommandArgs.append('--output-format=json')
        commandOutput = cls._runGDP(_gdpCommandArgs)
        if not commandOutput:
            return None
        result = json.loads(commandOutput)
        return result['results']

    @classmethod
    def _queryGGG(cls, gdpCommandArgs):
        '''Run the specified `gdp` command and return a Python representation
        of the command output as decoded from the `gdp` command JSON output.
        Return None if no data was found.
        
        Throw a :class:`subprocess.CalledProcessError` exception if the `gdp`
        command exits with a nonzero exit status.
        
        >>> libtypes = ICManageBase._queryGDP(('libtype', '-L')) 
        >>> 'LibType' in libtypes[0]
        True
        '''
        _gdpCommandArgs = list(gdpCommandArgs)
        _gdpCommandArgs.append('--output-format=json')
        commandOutput = cls._runGGG(_gdpCommandArgs)
        if not commandOutput:
            return None
        result = json.loads(commandOutput)
        return result['results']
 
    def _queryPM(cls, pmCommandArgs):
        '''Run the specified `pm` command and return a Python representation
        of the command output as decoded from the `pm` command JSON output.
        Return None if no data was found.
        
        Throw a :class:`subprocess.CalledProcessError` exception if the `pm`
        command exits with a nonzero exit status.
        
        >>> libtypes = ICManageBase._queryPM(('libtype', '-L')) 
        >>> 'LibType' in libtypes[0]
        True
        '''
        _pmCommandArgs = list(pmCommandArgs)
        _pmCommandArgs.append('-DJ:')
        commandOutput = cls._runPM(_pmCommandArgs)
        if not commandOutput:
            return None
        result = json.loads(commandOutput)
        return result

    @classmethod
    def _runGDP(cls, gdpCommandArgs):
        '''Run the specified `gdp` command and return the command output string.

        Throw a :class:`subprocess.CalledProcessError` exception if the `gdp`
        command exits with a nonzero exit status.
        
        >>> ICManageBase._runGDP(('libtype', '-L'))    #doctest: +ELLIPSIS
        'LibType="abx2gln" ...'
        '''
        command = ['gdp']
        command.extend(gdpCommandArgs)
        commandOutput = ''
        try:
            commandOutput = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            cls.raiseError(error, 'querying')
        return commandOutput

    @classmethod
    def _runGGG(cls, gdpCommandArgs):
        '''Run the specified `ggg` command and return the command output string.

        Throw a :class:`subprocess.CalledProcessError` exception if the `gdp`
        command exits with a nonzero exit status.
        
        >>> ICManageBase._runGGG(('libtype', '-L'))    #doctest: +ELLIPSIS
        'LibType="abx2gln" ...'
        '''
        command = ['ggg']
        command = []
        command.extend(gdpCommandArgs)
        commandOutput = ''
        try:
            commandOutput = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            cls.raiseError(error, 'querying')
        return commandOutput
               
    # no more pm command pending remove
    @classmethod
    def _runPM(cls, pmCommandArgs):
        '''Run the specified `pm` command and return the command output string.

        Throw a :class:`subprocess.CalledProcessError` exception if the `pm`
        command exits with a nonzero exit status.
        
        >>> ICManageBase._runPM(('libtype', '-L'))    #doctest: +ELLIPSIS
        'LibType="abx2gln" ...'
        '''
        command = ['pm']
        command.extend(pmCommandArgs)
        commandOutput = ''
        try:
            commandOutput = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            cls.raiseError(error, 'querying')
        return commandOutput
        
    @classmethod
    def getLibType(cls, deliverableName):
        '''Get the name of the IC Manage library type corresponding to the given
        deliverable.
        
        >>> ICManageBase.getLibType('LAYMISC')
        'laymisc'
        >>> ICManageBase.getLibType('GLNPREPNR')
        'glnprepnr'
        >>> ICManageBase.getLibType('FCFLRPLN')
        'fcflrpln'
        >>> ICManageBase.getLibType('GLNPOSTPNR')
        'glnpostpnr'
        >>> ICManageBase.getLibType('FCPNETLIST')
        'fcpnetlist'
        >>> ICManageBase.getLibType('LAY')
        'oa'
        >>> ICManageBase.getLibType('SCH')
        'oa'
        >>> ICManageBase.getLibType('RTL')
        'rtl'
        >>> ICManageBase.getLibType('RDF')
        'rdf'
        '''
        if deliverableName in ['LAY', 'SCH']:
            return 'oa'
        return deliverableName.lower()
        
    @classmethod
    def getDeliverableName(cls, libType):
        '''Get the name of the deliverable that corresponds to the specified
        IC Manage library type.  Argument ``libType`` is not checked for
        correctness.
        
        Except for "oa", there is a one-to-one correspondence between library
        type and deliverable name: 
        
        >>> ICManageBase.getDeliverableName('laymisc')
        'LAYMISC'
        
        IC Manage library type "oa" contains two deliverables: "LAY" and "SCH".
        For library type "oa":

        >>> ICManageBase.getDeliverableName('oa')
        'OA'

        However, there is no deliverable "OA".  But you underestimate me,
        Mr. Bond.  "OA" is a templateset alias that contains deliverables "LAY"
        and "SCH". 
        '''
        return libType.upper()
        
    @classmethod
    def raiseError(cls, error, doing):
        '''Raise an exception of type :class:`~dm.dmError.dmError`, giving a
        message created from the specified
        :class:`subprocess.CalledProcessError` ``error`` and what was happening
        at the time, ``doing``.
        '''
        if isinstance(error.cmd, basestring):
            command = error.cmd
        else:
            command = ''
            for arg in error.cmd:
                if ' ' in arg:
                    command += ' "{}"'.format(arg)
                else:
                    command += ' {}'.format(arg)
        
        raise dmError(
                "While {} in the ICManage Project Manager, the command:\n"
                "        {}\n"
                "    exited with status '{}' and error message:\n"
                "        '{}'\n"
                "    Please try running this command on the command line, and when you\n"
                "    get it to run, try running the failed DM program again."
                "".format(doing, command, error.returncode, error.output))

    @classmethod
    def _checkICManageAvailable(cls):
        '''Check whether the IC Manage software is available.
        Raise an exception if it is not.
        '''
        try:
            p4config = os.environ['P4CONFIG']
        except:
            raise dmError(
                "IC Manage is not available because the P4CONFIG environment "
                "variable is not set.")
        if p4config != '.icmconfig':
            raise dmError(
                "IC Manage is not available because the P4CONFIG environment "
                "variable is set to '{}', not '.icmconfig'.".format(p4config))
        if which('gdp') is None or which('xlp4') is None:
            raise dmError(
                "IC Manage is not available because the 'pm' command is not "
                "available.")

#if __name__ == "__main__":
#    # Running ICManageBase_test.py is the preferred test method,
#    # but run doctest alone if the user requests.
#    import doctest
#    doctest.testmod ()
