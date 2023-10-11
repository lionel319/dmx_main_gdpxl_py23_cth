#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012,2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageWorkspace.py#1 $

"""
ICManageWorkspace is the API to the IC Manage workspace.

Command Line Interface
=======================
The :meth:`~ICManageWorkspace.save` method is exposed as the
:doc:`saveworkspace`.

The :meth:`~ICManageWorkspace.getCellsInList` method is exposed as the
:doc:`celllist`.

Class Documentation
============================
"""
from __future__ import print_function


from builtins import str
import sys
import os
import json
import subprocess
import getpass
import inspect
import re

from dmx.dmlib.dmError import dmError
import dmx.dmlib.parsers
import dmx.dmlib.TopCells
from dmx.dmlib.ICManageConfiguration import ICManageConfiguration
from dmx.dmlib.ICManageBase import ICManageBase
import dmx.ecolib.loader
from dmx.utillib.decorators import memoized
import dmx.abnrlib.icm

def create(icmconfig, userName=None, dirName=None, description=None):
    '''Create a new IC Manage workspace based on IC Manage configuration
    `icmconfig`.
    
    Return an instance of :class:`dm.ICManageWorkspace.ICManageWorkspace`.
    
    If `userName` is not specified, use the current effective user.
    
    The workspace will appear in directory `dirName/workspaceName`, or if
    `dirName` is not specified, `./workspaceName`.
    
    If `description` is not specified, the description will be the empty
    string.
    
    See also :meth:`~dm.ICManageWorkspace.ICManageWorkspace.delete`.
    
    >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01',
    ...                                'NightFury_dev', libType='rtl')
    >>> ws = create(config)
    >>> ws.path == os.path.abspath(ws.workspaceName)
    True
    >>> ws.delete()
    >>> ws.workspaceName        #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    IOError: ... No such file or directory: '....icmconfig'
    
    '''
    if userName is None:
        userName = getpass.getuser()
    if dirName is None:
        dirName = '.'

    commandArgs = ['create-workspace',
                   '/intel/{}/{}/{}'.format(icmconfig.projectName, icmconfig.ipName, icmconfig.configurationName)]
        
    #(access to protected members): pylint: disable = W0212
    createMessage = ICManageBase._runPM(commandArgs)
    createMessageWords = createMessage.split()
    if len(createMessageWords) < 2:
        raise dmError("Failed to create a workspace for {}",format(icmconfig))
    workspaceName = createMessageWords[1]
    commandArgs = ['workspace',
                   '-s',
                   workspaceName]
    ICManageBase._runGGG(commandArgs)
    return dm.ICManageWorkspace.ICManageWorkspace(
                    workspacePath=os.path.join(dirName, workspaceName),
                    ipName=icmconfig.ipName,
                    libType=icmconfig.libType)
        
class ICManageWorkspace(ICManageConfiguration):
    '''Instantiate an API to the IC Manage workspace.  You can specify the path
    to an IC Manage workspace:
    
    >>> ws = ICManageWorkspace(workspacePath='/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
    >>> ws.path
    '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
    
    Or you can specify a path anywhere within an IC Manage workspace, and
    `ICManageWorkspace` will automatically find the workspace path:
    
    >>> ws = ICManageWorkspace(workspacePath='/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl')
    >>> ws.path
    '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
    
    If the current working directory is somewhere within an IC Manage workspace,
    `ICManageWorkspace` will automatically find the workspace path:
    
    >>> originalDir = os.getcwd()
    >>> os.chdir('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl')
    >>> ws = ICManageWorkspace()
    >>> ws.path
    '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
    >>> os.chdir(originalDir)

    It is an error to specify a nonexistent path:

    >>> ICManageWorkspace(workspacePath='/nonexistent/path') #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    dmError: ... is not a directory...
    
    By default, the top IP is the top IP in the IC Manage workspace:

    >>> ws = ICManageWorkspace(workspacePath='/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
    >>> ws.ipName
    u'icmanageworkspace01'
    >>> ws.ipNames
    set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02', 'icmanageworkspace01'])

    You can specify another IP in the workspace as the top, and the IC Manage
    configuration for that IP will be used.  For example, specify top IP
    `icmanageworkspace03` in a workspace where `icmanageworkspace01` is the top:
    
    >>> ws = ICManageWorkspace(workspacePath='/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5',
    ...                        ipName='icmanageworkspace03')
    >>> ws.ipName
    'icmanageworkspace03'
    >>> ws.ipNames
    set(['icmanageworkspace04', 'icmanageworkspace03'])
    
    The usage of the ``restoreDir`` argument is demonstrated along with the
    :meth:`~ICManageWorkspace.save` method.
    
    The optional argument ``libType`` limits the configuration to the contiguous
    hierarchy of IPs that contain the specified library type.  See
    `Finding a Hierarchy of a Library Type <dm.ICManageConfiguration.html#finding-a-hierarchy-of-a-library-type>`_
    for details.
    '''
    
    # Tested in the doctest for save()
    defaultSaveDirectoryName = 'ICManageWorkspace.save'
    savedWorkspaceFileName = 'workspace.json'
    savedCompositesFileName = 'composites.json'
    savedConfigurationsFileName = 'configurations.json'
    savedHierarchyFileName = 'hierarchy.json'
    savedInfoFileName = 'info.json'
    
    def __init__(self,
                 workspacePath=None,
                 ipName=None,
                 restoreDirName=None,
                 libType=None):
        # Properties have been defined for the following instance variables.
        # Always use the methods or properties exclusively, even within this
        # class.  _restore() is an exception to this rule.
        self._attributesAlwaysAccessViaMethod = None
        self._infoAlwaysAccessViaMethod = None
        self._ipNamesForCellNamesOnlyAccessViaProperty = None        
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self._isRestoredFromFiles = False

        # Due to softlink in PICE, we get the realpath 
        workspacePath = os.path.realpath(workspacePath) if workspacePath else os.path.realpath(os.getcwd())

        try:
            self._path = self.findWorkspace(workspacePath)
        except dmError as error:
            # findWorkspace() discovered that this is not an IC Manage workspace.
            # We will accept the workspacePath as specified (or the default) and try
            # to restore from previously saved files.
            print('{} is not an ICM workspace, attempting to restore from ICManageWorkspace.save'.format(workspacePath))
            # At this point, _isRestoredFromFiles means something
            # more like "_needToRestoreFromFiles"
            self._isRestoredFromFiles = True
            self._path = self.getAbsPathOrCwd(workspacePath)

        # Get project/IP/configuration names from IC Manage
        (projectName, ipName_, configurationName) = \
                    self._getConfigurationTripletFromWorkspace(ipName)
        assert (ipName is None) or (ipName == ipName_), \
            "_ipName from workspace should be as specified by ipName argument"
                
        super(ICManageWorkspace, self).__init__(projectName,
                                                ipName_,
                                                configurationName,
                                                libType=libType)
        
        # if withClient is present, the workspace root is under the workspacename (eg: user.project.variant.1)
        # otherwise, the workspace root is the directory attribute
        #if 'withClient' in self._attributesAlwaysAccessViaMethod['Attr']:   
        #    self._workspaceroot = '{}/{}'.format(self._attributesAlwaysAccessViaMethod['Dir'], self._attributesAlwaysAccessViaMethod['Workspace'])
        #else:
        self._workspaceroot = self._attributesAlwaysAccessViaMethod['Dir']

    def __repr__(self):
        '''String representation of this workspace.
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl',
        ...                        ipName='icmanageworkspace02', libType='rtl')
        >>> repr(ws)
        "ICManageWorkspace(workspacePath='/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5', ipName='icmanageworkspace02', libType='rtl')"
        '''
        return "{}(workspacePath='{}', ipName='{}', libType='{}')".format(
                                                    self.__class__.__name__,
                                                    self.path,
                                                    self.ipName,
                                                    self.libType)

    def __str__(self):
        '''String for this workspace.
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl',
        ...                        ipName='icmanageworkspace02', libType='rtl')
        >>> str(ws)
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5, variant icmanageworkspace02, libType rtl'
        '''
        result = "{}, variant {}".format(self.path,
                                          self.ipName)
        if self.libType is not None:
            result += ", libType {}".format(self.libType)
        return result
            

    @property
    def path(self):
        '''The path to this IC Manage workspace.
        
        For example:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl')
        >>> ws.path
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
        '''
        return self._path

    @property
    def workspaceName(self):
        '''The name of this IC Manage workspace.
        
        For example:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> ws.workspaceName
        'envadm.zz_dm_test.icmanageworkspace01.5'
        '''
        workspaceName = ""
        icmconfigFileName = os.path.join(self._path, ".icmconfig")
        with open(icmconfigFileName) as f:
            for line in f:
                line = line.rstrip()
                if 'P4PORT' in line:  continue
                if line.startswith('P4CLIENT='):
                    workspaceName = line[9:]
        if not workspaceName:
            raise dmError("IC Manage configuration file '{}' "
                          "    does not define 'P4CLIENT'.".format(icmconfigFileName))
        return workspaceName

    def getWorkspaceAttribute(self, name):
        '''A Python dictionary that contains all the attributes on the IC Manage
        workspace. The possible keys are:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> ws.workspaceAttributeNames
        [u'Loc', u'Attr', u'ConfType', u'Variant', u'Project', u'User', u'Workspace', u'LibType', u'Config', u'Mount', u'Dir', u'Desc']
                    
        These are the same as the attributes output by the IC Manage command::
        
          pm workspace -L -w workspaceName -DJ:
        
        All string values are Unicode strings:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> ws.getWorkspaceAttribute("Workspace")
        u'envadm.zz_dm_test.icmanageworkspace01.5'
        >>> ws.getWorkspaceAttribute("Dir")
        u'/ice_da/infra/icm/workspace/VP_ws'
        >>> # The value of the `Attr` attribute is a list.
        >>> ws.getWorkspaceAttribute("Attr") #doctest: +ELLIPSIS
        [u'withClient', u'postSync',... u'preSync']

        Note that these are attributes of the *workspace*.  Specifying an IP
        name that is not the workspace top IP does not change the workspace
        attributes:

        >>> ws = ICManageWorkspace(workspacePath='/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/',
        ...                        ipName='icmanageworkspace02')
        >>> ws.ipName    # The top IP name of the configuration, as requested
        'icmanageworkspace02'
        >>> ws.getWorkspaceAttribute("Variant")  # The top IP name of the workspace
        u'icmanageworkspace01'
        '''
        if self._attributesAlwaysAccessViaMethod is not None:
            return self._attributesAlwaysAccessViaMethod[name]


        ### We wanna maintain the same keys for this lookup table which is used in GDP
        ### so that the impact of change at the higher levels are negated.
        ### Here's the dictionary:
        '''
        {u'Attr': [u'withClient', u'postSync', u'preSync'],
         u'ConfType': u'composite',
         u'Project': u'i10soc2',
         u'Variant': u'io96',
         u'Config': u'cicq_integration_io96_FP8revA0_MS0.3_RC_RTL',
         u'Desc': u'',
         u'Dir': u'/nfs/site/disks/da_infra_1/users/yltan/rubbish',
         u'LibType': u'',
         u'Loc': u'PG-Edge',
         u'Mount': [u'native'],
         u'User': u'lionelta',
         u'Workspace': u'lionelta.i10soc2.io96.1938'}
        '''
        retkeys = ['project:parent:name', 'variant:parent:name', 'config:parent:name', 'libtype:parent:name', 'rootDir', 'path', 'name', 'host', 'created-by', 'library' ]
        data = self.icm.get_workspace_details(self.workspaceName, retkeys=retkeys)

        ### Here goes the mapping back to legacy keys
        tmp = {}
        tmp['Attr'] = ['not sure what to put here yet. This needs update in the future']
        tmp['ConfType'] = 'config'
        tmp['Project'] = data['project:parent:name']
        tmp['Variant'] = data['variant:parent:name']
        tmp['Config'] = data['config:parent:name']
        tmp['Desc'] = ''
        tmp['Dir']  = data['rootDir']
        tmp['LibType'] = data['libtype:parent:name'] 
        tmp['Loc'] = data['host']
        tmp['Mount'] = 'native'
        tmp['User'] = data['created-by']
        tmp['Workspace'] = data['name']
        self._attributesAlwaysAccessViaMethod = tmp

        return self._attributesAlwaysAccessViaMethod[name]



    @property
    def workspaceAttributeNames(self):
        '''The list of attribute names that can be passed to the
        :meth:`~ICManageWorkspace.getWorkspaceAttribute` method.
        This is chiefly for documentation.
            
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> len(ws.workspaceAttributeNames) > 5
        True
        '''
        # Initialize _attributesAlwaysAccessViaMethod
        #self.getWorkspaceAttribute('Workspace')
        
        return list(self._attributesAlwaysAccessViaMethod.keys())
    
    def getInfo(self, name):
        '''Return the specified value of the `icmp4 info` command.  The possible keys are:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> ws.infoNames
        ['Client name', 'Client root', 'Server version', 'Client address', 'Server root', 'Server uptime', 'Server address', 'User name', 'Server license', 'Case Handling', 'Current directory', 'Client host', 'Server license-ip', 'Peer address', 'Server date', 'ServerID']

        These are the same as the attributes output by the IC Manage command::
        
          icmp4 info

        Usage examples:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> ws.getInfo('Client root')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
        '''
        if self._infoAlwaysAccessViaMethod is None:
            self._infoAlwaysAccessViaMethod = self._getInfo(self._path)
        return self._infoAlwaysAccessViaMethod[name]
        
    @property
    def infoNames(self):
        '''The list of attribute names that can be passed to the
        :meth:`~ICManageWorkspace.getInfo` method.
        This is chiefly for documentation.
            
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        >>> len(ws.infoNames) > 5
        True
        '''
        # Initialize _infoAlwaysAccessViaMethod
        self.getInfo('Client root')
        
        return list(self._infoAlwaysAccessViaMethod.keys())
    
    @classmethod
    def _getInfo(cls, path):
        '''Get the results of `icmp4 info`, as executed with the specified path
        as the current working directory.
        
        This method is tested in the info property.
        '''
        if not cls._isIcmconfigFileInPath(path):
            raise dmError("The path '{}' is not within an IC Manage workspace\n"
                                       "   because there is no .icmconfig file in it or the directories above it.".format(path))

        command = "cd '{}'; xlp4 info".format(path)
        commandOutput = 'temporary initial string value'
        try:
            # The check_output(cwd) argument did not work, so I had to use 'cd' in command.
            commandOutput = subprocess.check_output(command, shell=True)
            commandOutput = commandOutput.decode()
        except subprocess.CalledProcessError as error:
            cls.raiseError(error, 'running xlp4')
        info = dict()
        for line in commandOutput.splitlines():
            keyValue = line.split(':', 1)
            if len(keyValue) != 2:
                raise dmError("'{}' output lines must all contain a ':',"
                              "but line '{}' does not".format(command, line))
            info[keyValue[0].strip()] = keyValue[1].strip()
        return info
        
    @classmethod
    def _isIcmconfigFileInPath(cls, path):
        '''Is there a .icmconfig file in this directory or one of the directories above it?
        
        This indicates that `path` is in an IC Manage workspace.
        
        >>> ICManageWorkspace._isIcmconfigFileInPath('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl')
        True
        >>> ICManageWorkspace._isIcmconfigFileInPath('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/')
        True
        >>> ICManageWorkspace._isIcmconfigFileInPath('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        True
        >>> ICManageWorkspace._isIcmconfigFileInPath('/ice_da/infra/icm/workspace/VP_ws/')
        False
        >>> ICManageWorkspace._isIcmconfigFileInPath('/ice_da/infra/icm/workspace/VP_ws')
        False
        '''
        pathComponents = (os.path.abspath(path)).split(os.path.sep)
        workspacePath = os.path.sep
        for pathComponent in pathComponents[1:]:
            workspacePath = os.path.join(workspacePath, pathComponent)
            if os.path.isfile(os.path.join(workspacePath, '.icmconfig')):
                return True
        return False

    @classmethod
    def findWorkspace(cls, path=None):
        '''Find the workspace that contains the specified path.  Determine this
        using the `icmp4 info` command.  If the `path` argument is not
        specified, the current working directory is used.
        
        `findWorkspace()` finds only real, active IC Manage workspaces.  No
        attempt is made to restore previously-saved workspace data.  If you want
        to take advantage of workspace data previously saved with
        `:meth:~ICManageWorkspace.save`, instantiate `ICManageWorkspace` and get
        the workspace path via the `path` property.
        
        For example, these test workspaces are known to exist:
        
        >>> ICManageWorkspace.findWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/rtl')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
        >>> ICManageWorkspace.findWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'
        >>> ICManageWorkspace.findWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5'

        If `path` is not in an IC Manage workspace, or is nonexistent, raise a
        `dmError`:
        
        >>> ICManageWorkspace.findWorkspace('/ice_da/infra/icm/workspace/VP_ws') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ... not within ...
        >>> ICManageWorkspace.findWorkspace('/nonexistent/path') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ... is not a directory...
        >>> ICManageWorkspace.findWorkspace('test_icmanageworkspace01_copy') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ...
        ...the workspace is in a different place...
        '''
        cls._checkICManageAvailable()
       
        absPath = cls.getAbsPathOrCwd(path)
        if not os.path.exists(absPath):
            raise dmError(
                "The specified workspace path '{}' does not exist.".format(absPath))
        info = cls._getInfo(absPath)
        clientRoot = os.path.realpath(os.path.abspath(info['Client root']))
        if not os.path.exists(clientRoot):
            raise dmError(
                "The IC Manage client (workspace) root '{}' does not exist.".format(clientRoot))

        commonPrefix = os.path.commonprefix([clientRoot, absPath])
        if not os.path.exists(commonPrefix):
            # Incredibly, os.path.commonprefix('/abc/xyz', '/abc/x') returns '/abc/x'
            commonPrefix = os.path.dirname(commonPrefix)
        if not os.path.samefile(clientRoot, commonPrefix):
            # icmp4 info probably got the info based on a copied .icmp4config file
            raise dmError(
                "Cannot find the workspace for path '{}'\n"
                "    because `icmp4 info` found the workspace is in a different place\n"
                "    '{}'.\n"
                "    This probably happened because '{}' is a copy of\n"
                "    a workspace, not a workspace created using 'icmp4 sync'"
                "".format(absPath, clientRoot, absPath))
        return clientRoot

    @classmethod
    def getAbsPathOrCwd(cls, path):
        '''Get the absolute path or the current working directory if the
        specified path is `None`.  Check to make sure that the path is a
        directory.
        
        >>> os.path.samefile(ICManageWorkspace.getAbsPathOrCwd(None), os.getcwd())
        True
        >>> os.path.samefile(ICManageWorkspace.getAbsPathOrCwd(os.getcwd()), os.getcwd())
        True
        >>> # 'test/dir' is created in setUp()
        >>> os.path.samefile(ICManageWorkspace.getAbsPathOrCwd('test/dir'), os.path.abspath('test/dir'))
        True
        >>> ICManageWorkspace.getAbsPathOrCwd('nonexistent') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ... is not a directory...
        '''
        if path is None:
            return os.path.abspath(os.getcwd())
        absPath = os.path.abspath(path)
        if not os.path.isdir(absPath):
            raise dmError(
                "The specified workspace path '{}' is not a directory.".format(absPath))
        return absPath
    
    @classmethod
    def isWorkspace(cls, path):
        '''Return `True` if the specified path is a readable IC Manage workspace.
        
        For example, this test workspace is known to exist:

        >>> ICManageWorkspace.isWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01')
        False
        >>> ICManageWorkspace.isWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/')
        True
        >>> ICManageWorkspace.isWorkspace('/ice_da/infra/icm/workspace/VP_ws')
        False
        >>> ICManageWorkspace.isWorkspace('/nonexistent/path')
        False

        This test workspace is known to exist, but the client name is not included in its path:

        >>> ICManageWorkspace.isWorkspace('/ice_da/infra/icm/workspace/VP_ws/icmanageworkspace01.without.client.name/icmanageworkspace01')
        False
        >>> ICManageWorkspace.isWorkspace('/ice_da/infra/icm/workspace/VP_ws')
        False
        >>> ICManageWorkspace.isWorkspace('/nonexistent/path')
        False
        '''
        try:
            workspacePath = cls.findWorkspace(path)
        except dmError:
            return False
        return os.path.samefile(path, workspacePath)
    
    def getCellsInList (self, 
                        ipName, 
                        listName,
                        cellName=None, 
                        isIPNameDefault=False, 
                        quiet=True):
        '''
        Return a set containing the cell names in the specified cell name
        list for the specified IP.
        
        This method is exposed as the :doc:`celllist`.

        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace01', 'cell_names')
        set(['cell03c', 'cell02b', 'cell01a'])

        The cell list name is the deliverable item name as defined in the
        templateset.  For example, for IP `ip1` cell `cella`, `listName` "molecules"
        refers to file:
        
        >>> manifest = Manifest('ip1', 'cella')
        >>> manifest.getPattern('IPSPEC', 'molecules')
        'ip1/ipspec/cella.molecules.txt'
        
        Similarly, for list name `elements`:
        
        >>> manifest = Manifest('ip1', 'cella')
        >>> manifest.getPattern('IPSPEC', 'elements')
        'ip1/ipspec/cella.elements.txt'
                
        If the specified `listName` does not exist, an exception is raised:
        
        >>> ws.getCellsInList('icmanageworkspace01', 'nonexistent') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'IPSPEC', there is no pattern named 'nonexistent'.
        
        If the specified list file does not exist or is empty, the
        `isIPNameDefault` argument controls the result.  If `isIPNameDefault`
        is `True`, a set containing just the `ipName` will be returned.  If
        `False`, the empty set is returned:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace03', 'cell_names', isIPNameDefault=True)
        set(['icmanageworkspace03'])
        >>> ws.getCellsInList('icmanageworkspace03', 'cell_names', isIPNameDefault=False)
        set([])
        
        Some types of cell list files have one list per cell, like the `molecules`
        list:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace02', 'molecules', cellName='cell02a')
        set(['atom1', 'atom2'])
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace02', 'molecules', cellName='cell02b')
        set(['atom4', 'atom3'])

        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace02', 'molecules', cellName='cell02c')
        set(['atom5', 'atom6'])
        
        For cell list files that have one list per cell (like the `molecules` list),
        a nonexistent file is the same as an empty file.  For example, IP
        `icmanageworkspace03` contains cell `icmanageworkspace03`.  It has no
        `molecules` file, and its `icmanageworkspace03.elements.txt file contains
        `icmanageworkspace03`:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace03', 'molecules')
        set([])
        >>> ws.getCellsInList('icmanageworkspace03', 'elements')
        set(['icmanageworkspace03'])

        The `cellName` you may or may not exist as top cell.
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace02', 'molecules', cellName='nonexistent') #doctest: +ELLIPSIS
        set([])
        
        If you specify no cell name for a cell list file that has one list per
        cell (such as the `molecules` list), all cells in all files for the
        specified IP will be returned:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace02', 'molecules')
        set(['atom4', 'atom5', 'atom6', 'atom1', 'atom2', 'atom3'])
         
        The `isIPNameDefault` argument works with per-cell lists like
        `molecules` and `elements`, but
        *using `isIPNameDefault=True` with per-cell lists is probably not useful*:
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace03', 'molecules', isIPNameDefault=True)
        set(['icmanageworkspace03'])
        >>> ws.getCellsInList('icmanageworkspace03', 'molecules', isIPNameDefault=False)
        set([])
        
        The `cell_names` cell list gets special handling.  When you specify this
        `listName`, the :py:func:`dm.TopCells.getCellNamesForIPNameAndPath`
        function is used:
         
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.getCellsInList('icmanageworkspace01', 'cell_names')
        set(['cell03c', 'cell02b', 'cell01a'])
        >>> ws.getCellsInList('icmanageworkspace03', 'cell_names', isIPNameDefault=True, quiet=True)
        set(['icmanageworkspace03'])
        >>> ws.getCellsInList('icmanageworkspace03', 'cell_names', isIPNameDefault=False, quiet=True)
        set([])
        
        If you are only interested in the `cell_names` list and you do not care
        to access the other kinds of lists, you may prefer to simply use
        :py:func:`dm.TopCells.getCellNamesForIPNameAndPath` directly.
        '''
        # The 'cell_names' file is more complicated so it has a special parser
        
        if listName == 'cell_names':
            # After http://fogbugz/default.asp?224608
            topCellNames = dmx.dmlib.TopCells.getCellNamesForIPNameAndPath (ipName, 
                                                                     self.path, 
                                                                     quiet,
                                                                     isIPNameDefault)
            return topCellNames

        topCellNames = dmx.dmlib.TopCells.getCellNamesForIPNameAndPath (ipName, 
                                                                 self.path, 
                                                                 quiet,
                                                                 returnIpIfEmpty = True)
        if not topCellNames:
            return set() 
        
        if cellName is None:
            cellNames = topCellNames
        # After http://fogbugz/default.asp?224619:
#        elif cellName not in allCellNames:
#            raise dmError("The specified cell '{}' is invalid because it is not "
#              "a top cell in IP '{}'.".format(cellName, ipName))
        else:
            cellNames = [cellName]

        cellNamesInFiles = set()
        for currentCellName in cellNames:
            cellNamesInFiles.update (self._getCellsInListFile (ipName, 
                                                               currentCellName,
                                                               listName, 
                                                               isIPNameDefault))
        return cellNamesInFiles

    def _getCellsInListFile(self, ipName, cellName, listName, isIPNameDefault):
        '''Return the set of cell names in the specified file.'''
        fileName = self._getCellListFileName(ipName, cellName, listName)
        if os.access(fileName, os.R_OK):
            cellNames = dmx.dmlib.parsers.parseCellNamesFile(fileName)
        else:
            cellNames = set()
            
        if cellNames:
            return set(cellNames)
        if isIPNameDefault:
            return set([ipName])
        return set()
        
    def isCellListFileReadable(self, ipName, listName, cellName=None):
        '''Return `True` if the specified cell name list for the specified IP
        exists and is readable.
        
        This is not meaningful for `listname` atoms, because atoms is composed
        of an atoms file for each top level cell.  If you use `listname` atoms,
        an assertion will fire.

        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws.isCellListFileReadable('icmanageworkspace01', 'cell_names')
        True
        >>> ws.isCellListFileReadable('icmanageworkspace03', 'cell_names')
        False
        '''
        assert listName != 'atoms', \
            "ICManageWorkspace.isCellListFileReadable('atoms') is not " \
            "meaningful because this refers to multiple files"
        fileName = self._getCellListFileName(ipName, cellName, listName)
        return os.access(fileName, os.R_OK)
        
    def _getCellListFileName(self, ipName, cellName, listName):
        '''Return the absolute path to the specified cell list file.

        An exception is thrown if the `listName` is not defined in the templateset.

        The existence of the IP or file is not checked.

        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5')
        >>> ws._getCellListFileName('icmanageworkspace01', 'cella', 'cell_names')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01/ipspec/icmanageworkspace01.cell_names.txt'
        >>> ws._getCellListFileName('arbitraryIpName', 'cella', 'cell_names')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/arbitraryIpName/ipspec/arbitraryIpName.cell_names.txt'
        >>>
        >>> ws._getCellListFileName('arbitraryIpName', 'cella', 'atoms')
        '/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/arbitraryIpName/ipspec/cella.atomlist.txt'
        >>>
        >>> ws._getCellListFileName('icmanageworkspace01', 'cella', 'nonexistent') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'IPSPEC', there is no pattern named 'nonexistent'.
        '''
        families = dmx.ecolib.loader.load_family()
        self.family = '' 
        for family in families:
            if self.projectName in families[family]['icmprojects']:
                self.family = family
                break                   

        manifest = dmx.ecolib.loader.load_manifest(self.family)
        patterns = [str(x) for x in list(manifest['ipspec']['pattern'].keys())]
        if ipName:
            patterns = [x.replace('ip_name', ipName) for x in patterns]
        newpatterns = []            
        if cellName:
            for pattern in patterns:
                if 'cell_names' not in pattern:
                    newpatterns.append(pattern.replace('cell_name', cellName))
                else:
                    newpatterns.append(pattern)                    
                    
        results = ''
        for pattern in newpatterns:
            if listName in pattern:
                results = os.path.join(self.path, pattern)
                break
        return results                

    def getIPNameForCellName(self, cellName):
        '''Return the name of the IP that contains the specified cell.

        The :meth:`~ICManageWorkspace.getCellNamesForIPName` method performs the
        inverse operation.
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01')
        >>> ws.getIPNameForCellName('cell01a')
        'icmanageworkspace01'
        >>> ws.getIPNameForCellName('cell02a')
        'icmanageworkspace02'
        '''
        ipName = self._ipNamesForCellNames.get(cellName)
        if ipName is None:
            raise dmError("There is no cell (or IP) named '{}' in any of the IPs in the workspace"
                  "".format(cellName))
        return ipName
    
    @property
    def _ipNamesForCellNames(self):
        '''A dictionary whose keys are cell names.  The value is the
        corresponding IP name.
        
        Tested in `getIPNameForCellName()`.
        '''
        if self._ipNamesForCellNamesOnlyAccessViaProperty is None:
            self._ipNamesForCellNamesOnlyAccessViaProperty = {}
            for ipName in list(self.hierarchy.keys()):
                for cellName in self.getCellNamesForIPName(ipName, 
                                                           quiet=False, 
                                                           returnIpIfEmpty=False):
                    self._ipNamesForCellNamesOnlyAccessViaProperty[cellName] = ipName
        return self._ipNamesForCellNamesOnlyAccessViaProperty

    def getCellNamesForIPName(self, ipName, quiet=False, returnIpIfEmpty=True):
        '''
        The set of TOP cell names from the IPSPEC deliverable for the specified
        IP.  If there are no cell names defined in IPSPEC, the IP itself is the
        only cell, so return `set([ipName])`.
        
        The :meth:`~ICManageWorkspace.getIPNameForCellName` method performs the
        inverse operation.
        
        The `quiet` argument suppresses some (info) messages. It is useful for testing
        and when you do not care about the details of each IP while examining
        multiple IPs.
        
        The 'returnIpIfEmpty' arg causes returning of set([ipName]) even if cell_names.txt 
        does not exit 
        
        >>> ws = ICManageWorkspace('/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5/icmanageworkspace01')
        >>> sorted (ws.getCellNamesForIPName('icmanageworkspace01', quiet=True, returnIpIfEmpty = True))
        ['cell01a', 'cell02b', 'cell03c']
        >>> sorted (ws.getCellNamesForIPName('icmanageworkspace02', quiet=True, returnIpIfEmpty = True))
        ['cell02a', 'cell02b', 'cell02c']
        
        Use class method :meth:`~ICManageWorkspace.getCellNamesForIPNameAndPath`
        when you have no :class:`~dm.ICManageWorkspace.ICManageWorkspace`
        instance.
        '''
        return dmx.dmlib.TopCells.getCellNamesForIPNameAndPath (ipName, 
                                                         self.path, 
                                                         quiet,
                                                         returnIpIfEmpty)
                    
    @classmethod
    def getCellNamesForIPNameAndPath(cls, ipName, path, quiet, returnIpIfEmpty = True):
        '''
        This is the class method version of
        :meth:`~ICManageWorkspace.getCellNamesForIPName` for
        use when there is no :class:`~dm.ICManageWorkspace.ICManageWorkspace`
        instance available.
        
        See :meth:`~ICManageWorkspace.getCellNamesForIPName` for documentation
        and tests.
        '''
        return dmx.dmlib.TopCells.getCellNamesForIPNameAndPath (ipName, 
                                                         path, 
                                                         quiet,
                                                         returnIpIfEmpty)

    def _getConfigurationTripletFromWorkspace(self, ipName):
        '''Return the `(projectName, ipName, configurationName)` triplet for the
        specified IP.  If `ipName` is None, use the top IP in the workspace.
        
        As implied by the name, this method gets its information from the IC
        Manage workspace.
        
        This method is for bootstrapping within
        :meth:`~ICManageWorkspace.__init__`.  It does not cache its results.
        '''
        if ipName is None or ipName == self.getWorkspaceAttribute('Variant'):
            # Return information about the top IP in the workspace
            return (self.getWorkspaceAttribute('Project'),
                    self.getWorkspaceAttribute('Variant'),
                    self.getWorkspaceAttribute('Config'))
            
        # Bootstrap by Instantiating an ICManageWorkspace for the top IP,
        # and get the triplet for the sub-IP from there
        wsForTopIP = ICManageWorkspace(self.path)
        return wsForTopIP.getConfigurationTriplet(ipName)
    
    # later            
    def delete(self):
        '''Delete this IC Manage workspace.  After calling this method, the
        behavior of this ICManageWorkspace instance is undefined.
        
        A test and usage example is in :meth:`~ICManageWorkspace.create`.
        '''
        commandArgs = ['workspace', '-x', self.workspaceName]
        self._runPM(commandArgs)

    def get_project_of_ip(self, ip):
        ret = ''
        configs = self.configurations
        for config in configs:
            variant = str(config['variant'])
            project = str(config['project'])
            project = project.split(':')[-1] if ':' in project else project
            if variant == ip:
                ret = project
                break
        return ret


    def get_ips(self):
        ips = []
        configs = self.configurations
        for config in configs:
            variant = str(config['variant'])
            if variant not in ips:
                ips.append(variant)
        return sorted(ips)

    def get_ips_with_project(self):
        ips = []
        configs = self.configurations
        for config in configs:
            variant = str(config['variant'])
            project = str(config['project'])
            project = project.split(':')[-1] if ':' in project else project
            if (project, variant) not in ips:
                ips.append((project, variant))
        return sorted(ips)

    def get_projects(self):
        projects = []
        configs = self.configurations
        for config in configs:
            project = str(config['project'])
            if project not in projects:
                projects.append(project)
        return sorted(projects)

    def get_deliverables(self, ip):
        return sorted(list([str(x) for x in self.getLibraryTypes(ip)]))

    def get_cells(self, ip):        
        if ip not in self.get_ips():
            raise dmError('IP {} is not present in this workspace'.format(ip))
        ipspec_dir = '{}/{}/{}'.format(self._workspaceroot, ip, 'ipspec')
        if not os.path.exists(ipspec_dir):
            raise dmError('{} does not exist'.format(ipspec_dir))
        cellnames_file = '{}/{}'.format(ipspec_dir, 'cell_names.txt')            
        if not os.path.exists(cellnames_file):
            raise dmError('{} does not exist'.format(cellnames_file))

        results = []
        invalid_cells = []
        with open(cellnames_file) as f:            
            for line in f.readlines():
                line = str(line.strip())
                m = re.match('\w', line)
                if m:
                    # http://pg-rdjira:8080/browse/DI-1069
                    # Cells not allowed to have upper case
                    has_upper = True if [x for x in line if x.isupper()] else False
                    if has_upper:
                        invalid_cells.append(str(line))
                    else:                        
                        results.append(str(line.lower()))
        if invalid_cells:
            print('Cells with upper cases found in ipspec ({}):'.format(cellnames_file))
            for cell in invalid_cells:
                print('* {}'.format(cell))
            raise dmError('Cells are not allowed with upper cases.')                
                                
        return sorted(list(set(results)))

    def get_unneeded_deliverables_for_ip(self, ip):        
        if ip not in self.get_ips():
            raise dmError('IP {} is not present in this workspace'.format(ip))
        ipspec_dir = '{}/{}/{}'.format(self._workspaceroot, ip, 'ipspec')
        if not os.path.exists(ipspec_dir):
            raise dmError('{} does not exist'.format(ipspec_dir))
        cells = self.get_cells(ip)
        for num, cell in enumerate(cells):            
            unneeded_deliverables_for_cell = self.get_unneeded_deliverables_for_cell(ip, cell)
            if not num:         
                results = set(unneeded_deliverables_for_cell)
            else:
                results = unneeded_deliverables.intersection(set(unneeded_deliverables_for_cell))
        return sorted(list(set(results)))

    def get_unneeded_deliverables_for_cell(self, ip, cell):  
        if ip not in self.get_ips():
            raise dmError('IP {} is not present in this workspace'.format(ip))
        ipspec_dir = '{}/{}/{}'.format(self._workspaceroot, ip, 'ipspec')
        if not os.path.exists(ipspec_dir):
            raise dmError('{} does not exist'.format(ipspec_dir))
        cells = self.get_cells(ip)
        if cell not in cells:
            raise dmError('Cell {} does not exist for IP {}'.format(cell, ip))

        unneeded_deliverables_file = '{}/{}.{}'.format(ipspec_dir, cell, 'unneeded_deliverables.txt')          
        results = []        
        if os.path.exists(unneeded_deliverables_file):
            with open(unneeded_deliverables_file) as f:
                for line in f.readlines():
                    line = str(line.strip())
                    m = re.match('\w', line)
                    if m:
                        results.append(str(line.lower()))

        return sorted(list(set(results)))

if __name__ == "__main__":
    # Running ICManageWorkspace_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    # Disabled due to incorrect/removed test data
#    import doctest
#    doctest.testmod()
    pass
    
    
