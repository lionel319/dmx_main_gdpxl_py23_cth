#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012,2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageConfiguration.py#1 $

"""
ICManageWorkspace is the API to the IC Manage workspace.

.. _hierarchy-of-libtype:

Finding a Hierarchy of a Library Type
===========================================

By default, `ICManageConfiguration` operates on all IPs within the
IC Manage configuration specified upon instantiation.  If you specify the
optional ``libType`` argument, `ICManageConfiguration` will only
consider the contiguous hierarchy of IPs that contain the specified IC Manage
library type.

For example, consider this hierarchy of IPs, where IP `icmanageworkspace03`
does not contain `rdf`, interrupting the `rdf` hierarchy::

                +------------------------------+
                |      icmanageworkspace01     |
                |      contains libType rdf    |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace02     |
                |      contains libType rdf    |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace03     |
                | does not contain libType rdf |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace04     |
                |      contains libType rdf    |
                +------------------------------+

When the library type is not specified, the `ICManageConfiguration` instance
contains all IPs:

    >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
    >>> config.ipNames
    set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02', 'icmanageworkspace01'])
    >>> config.hierarchy
    {'icmanageworkspace04': [], 'icmanageworkspace03': ['icmanageworkspace04'], 'icmanageworkspace02': ['icmanageworkspace03'], 'icmanageworkspace01': ['icmanageworkspace02']}
    
When the constructor argument ``libType='rdf'`` is specified, neither
`icmanageworkspace03` nor `icmanageworkspace04` are included because the `rdf`
hierarchy is interrupted by the absence of an `rdf` type library in
`icmanageworkspace03`:

    >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
    >>> config.ipNames
    set(['icmanageworkspace02', 'icmanageworkspace01'])
    >>> config.hierarchy
    {'icmanageworkspace02': [], 'icmanageworkspace01': ['icmanageworkspace02']}

.. _ipnames_vs_getipnames:

Choosing between ``ipNames`` and ``getIpNames()``
--------------------------------------------------------

As explained above, the :attr:`~ICManageConfiguration.ipNames` property
considers the hierarchy of the optional ``libType`` constructor argument.

The :meth:`~dm.ICManageConfiguration.getIpNames` method has its own ``libType``
argument, so it ignores the constructor ``libType`` argument as well as the
hierarchy:

    >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
    >>>
    >>> config.ipNames
    set(['icmanageworkspace02', 'icmanageworkspace01'])
    >>>
    >>> config.getIpNames('rdf')
    set(['icmanageworkspace04', 'icmanageworkspace02', 'icmanageworkspace01'])
    >>> # Get the IPs that contain any other library type
    >>> config.getIpNames('wild')
    set(['icmanageworkspace02'])

When you need to find a contiguous hierarchy of IPs containing a certain library
type, specify ``libType`` upon instantiation.  The
:attr:`~ICManageConfiguration.hierarchy` property will show this hierarchy, and
use the :attr:`~ICManageConfiguration.ipNames` property to get the set of names
of the IPs in this hierarchy.

When you do not care about hierarchy and simply want to find every IP that
contains a library of a given type, use the
:meth:`~ICManageConfiguration.getIpNames` method to get the set of names
of all IPs containing a library type.
:meth:`~ICManageConfiguration.getIpNames` can repeatedly query different library
types without instantiating a new `ICManageConfiguration`
instance each time.

Class Documentation
============================
"""

from builtins import str
__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2013 Altera Corporation"

import os, sys
import datetime
import subprocess
import re
from dmx.utillib.decorators import memoized
from dmx.dmlib.dmError import dmError
from dmx.dmlib.ICManageBase import ICManageBase
import dmx.abnrlib.icm

#Unkwown place holder, will delete if none is used.
@memoized
def _runP4Print(projectName, ipName, configurationName):
    '''Run the `xlp4 print` command and return the file contents.  Memoize the
    result.
    '''
    command = ['xlp4', 'print', '-q',
               '//intel/{}/{}/{}.icmCfg'.format(projectName,
                                                            ipName,
                                                            configurationName)]
    commandOutput = 'temporary initial string value'
    try:
        commandOutput = subprocess.check_output(command)
    except subprocess.CalledProcessError as error:
        ICManageBase.raiseError(error,
                   'getting configuration {}/{}/{}'.format(projectName,
                                                           ipName,
                                                           configurationName))
    return commandOutput

@memoized
def _getConfigContent(projectName, ipName, configurationName):
    '''Run the `icmp4 print` command and return the file contents.  Memoize the
    result.
    '''
    command = ['gdp', 'list', '/intel/{}/{}/{}/.**::content'.format(projectName, ipName, configurationName), '--columns', 'type,path,content']
    commandOutput = 'temporary initial string value'
    try:
        commandOutput = subprocess.check_output(command)
    except subprocess.CalledProcessError as error:
        ICManageBase.raiseError(error,
                   'getting configuration {}/{}/{}'.format(projectName,
                                                           ipName,
                                                           configurationName))
    return commandOutput

class ICManageConfiguration(ICManageBase):
    '''Instantiate an API to the IC Manage configuration of the specified
    project/IP/configuration.  "IP" is equivalent to IC Manage "variant".
    
    >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
    >>> config.ipNames
    set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02', 'icmanageworkspace01'])
    >>> config.hierarchy
    {'icmanageworkspace04': [], 'icmanageworkspace03': ['icmanageworkspace04'], 'icmanageworkspace02': ['icmanageworkspace03'], 'icmanageworkspace01': ['icmanageworkspace02']}

    The optional argument ``libType`` limits the configuration to the contiguous
    hierarchy of IPs that contain the specified library type.  See
    `Finding a Hierarchy of a Library Type <#finding-a-hierarchy-of-a-library-type>`_
    for details.
    
    >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
    >>> config.hierarchy
    {'icmanageworkspace02': [], 'icmanageworkspace01': ['icmanageworkspace02']}
    '''
    def __init__(self, projectName, ipName, configurationName,
                 libType=None):
        super(ICManageConfiguration, self).__init__()
        self._projectName = projectName
        self._ipName = ipName
        self._configurationName = configurationName
        assert (libType is None) or (libType.islower()), \
            "All library types are lower case (it is deliverable names that are upper case)"
        self._libType = libType     #: None means any library type
        
        # Properties have been defined for the following instance variables.
        # Always use the methods or properties exclusively, even within this
        # class.  _restore() is an exception to this rule.
        self._compositesAlwaysAccessViaProperty = None
        self._configurationsAlwaysAccessViaProperty = None
        self._creationTimeAlwaysAccessViaProperty = None
        self._hierarchyAlwaysAccessViaProperty = None
        self._ipNamesWithLibTypeAlwaysAccessViaProperty = None
        self._modificationTimeAlwaysAccessViaProperty = None
        self.icm = dmx.abnrlib.icm.ICManageCLI()

    def __repr__(self):
        '''String representation of this configuration.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01',
        ...                                'dev', libType='rtl')
        >>> repr(config)
        "ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rtl')"
        '''
        return "{}('{}', '{}', '{}', libType='{}')".format(self.__class__.__name__,
                                                    self._projectName,
                                                    self._ipName,
                                                    self._configurationName,
                                                    self._libType)

    def __str__(self):
        '''String for this configuration.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01',
        ...                                'dev', libType='rtl')
        >>> str(config)
        'zz_dm_test/icmanageworkspace01/dev for libType rtl'
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01',
        ...                                'dev')
        >>> str(config)
        'zz_dm_test/icmanageworkspace01/dev'
        '''
        result = "{}/{}/{}".format(self._projectName,
                                   self._ipName,
                                   self._configurationName)
        if self._libType is not None:
            result += " for libType {}".format(self._libType)
        return result
        
    @property
    def projectName(self):
        '''The project name specified upon instantiation.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.projectName
        'zz_dm_test'
        '''
        return self._projectName

    @property
    def ipName(self):
        '''The IP (variant) name specified upon instantiation.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.ipName
        'icmanageworkspace01'
        '''
        return self._ipName

    @property
    def configurationName(self):
        '''The configuration name specified upon instantiation.
        
        For example:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.configurationName
        'dev'
        '''
        return self._configurationName
    
    @property
    def libType(self):
        '''The library type specified upon instantiation, or `None` if no
        library type was specified.
        
        For example:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', 'rtl')
        >>> config.libType
        'rtl'
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.libType    # Returns None 
               
        '''
        return self._libType
    
    @classmethod
    def isConfiguration(cls, projectName, ipName, configurationName):
        '''Does the specified project/IP/configuration exist?
        
        >>> ICManageConfiguration.isConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        True
        >>> ICManageConfiguration.isConfiguration('nonexistent', 'icmanageworkspace01', 'dev')
        False
        >>> ICManageConfiguration.isConfiguration('zz_dm_test', 'nonexistent', 'dev')
        False
        >>> ICManageConfiguration.isConfiguration('zz_dm_test', 'icmanageworkspace01', 'nonexistent')
        False
        '''
        try:
            config = ICManageConfiguration(projectName, ipName, configurationName)
            config.configurations   # pylint: disable=W0104
            if config.configurations == []:
                return False
        except dmError:
            return False
        return True

    @property
    def configurations(self):
        '''The JSON representation of the:
        
        * Top composite configuration of the current workspace
        * The library configurations in the current workspace
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.configurations      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [{u'Property': [''], u'ConfType': u'composite', u'LibDefsPath': '', u'Variant': u'icmanageworkspace01', u'Project': u'zz_dm_test', ...},  ...]
        
        This is the same as the output of the IC Manage command::
        
          pm configuration -L -a ... -DJ:
        
        If you want the composite configurations for the sub-IPs, use method
        :meth:`~ICManageConfiguration.getConfigurationTriplet`.
        '''
        if self._configurationsAlwaysAccessViaProperty is None:
            all_data = self.icm.get_config_content_details(self._projectName, self._ipName, self._configurationName, hierarchy=True, retkeys=['name','release','type','path','variant:parent:name','project:parent:name','config:parent:name','libtype:parent:name'])

          #  all_data = self._queryGDP(('list', '/intel/{}/{}/{}/.**::content'.format(self._projectName, self._ipName, self._configurationName), '--columns', 'name,release,type,path,variant:parent:name,project:parent:name,config:parent:name,libtype:parent:name'))
            for data in all_data:
                data['project'] = data.pop('project:parent:name')
                data['variant'] = data.pop('variant:parent:name')
                data['config'] = data.pop('config:parent:name')
                data['libtype'] = data.pop('libtype:parent:name')
            self._configurationsAlwaysAccessViaProperty = (all_data)
           
        return self._configurationsAlwaysAccessViaProperty

    @property
    def ipNames(self):
        '''The set of IPs in the contiguous hierarchy of IPs that include the
        library type specified upon instantiation.
        
        See
        `Finding a Hierarchy of a Library Type <#finding-a-hierarchy-of-a-library-type>`_
        for a detailed discussion of the effect of the constructor library type
        argument.

        .. note::
           The :meth:`~ICManageConfiguration.getIpNames` method is similar in
           that it also returns a set of IP names.  See
           `Choosing between ipNames and getIpNames() <#choosing-between-ipnames-and-getipnames>`_
           for an explanation of how it is different.

        For instance, the example below operates on the following hierarchy::
        
                +------------------------------+
                |      icmanageworkspace01     |
                |      contains libType rdf    |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace02     |
                |      contains libType rdf    |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace03     |
                | does not contain libType rdf |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace04     |
                |      contains libType rdf    |
                +------------------------------+
            
        If no library type is specified upon construction, all IPs in the
        configuration appear in `ipNames`:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.ipNames
        set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02', 'icmanageworkspace01'])
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace02', 'dev')
        >>> config.ipNames
        set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02'])

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace03', 'dev')
        >>> config.ipNames
        set(['icmanageworkspace04', 'icmanageworkspace03'])

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace04', 'dev')
        >>> config.ipNames
        set(['icmanageworkspace04'])

        Now consider the effect of the ``libType`` constructor argument.
        Since `icmanageworkspace03` has no libType `rdf`, neither
        `icmanageworkspace03` nor its child `icmanageworkspace04` are included
        in `ipNames`, even though `icmanageworkspace04` does contain a library
        of type `rdf`:
                
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
        >>> config.ipNames
        set(['icmanageworkspace02', 'icmanageworkspace01'])
        
        No IP contains library type `nonexistent`:

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='nonexistent')
        >>> config.ipNames
        set([])

        '''
        return set(self.hierarchy.keys())
   
    def getIpNames(self, libType):
        '''Return the set of the names of all IPs that contain the specified
        library type.  The IP hierarchy or the library type specified upon
        construction are not considered.
        
        Return the set of every IP name if ``libType=None`` is specified.
        This behavior is required by internal code.   
        
        .. note::
            The :attr:`~ICManageConfiguration.ipNames` property is similar in
            that it also contains a set of IP names.  See
            `Choosing between ipNames and getIpNames() <#choosing-between-ipnames-and-getipnames>`_
            for an explanation of how it is different.

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.getIpNames('rdf')
        set(['icmanageworkspace04', 'icmanageworkspace02', 'icmanageworkspace01'])
        >>>
        >>> # Only icmanageworkspace02 has a wild library
        >>> config.getIpNames('wild')
        set(['icmanageworkspace02'])
        >>>
        >>> config.getIpNames(None)
        set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02', 'icmanageworkspace01'])
        >>>
        >>> config.getIpNames('nonexistent')
        set([])
        >>>
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace02', 'dev')
        >>> config.getIpNames('rdf')
        set(['icmanageworkspace04', 'icmanageworkspace02'])
        >>>
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace03', 'dev')
        >>> config.getIpNames('rdf')
        set(['icmanageworkspace04'])
        

        '''
        allIpNamesWithLibType = set()
        for jsonConfiguration in self.configurations:
            if (libType is None) or (('libtype' in jsonConfiguration) and (libType == jsonConfiguration['libtype'])):
                allIpNamesWithLibType.add(str(jsonConfiguration['variant']))
        return allIpNamesWithLibType


    #need to change conig:parent:name, curent this return ''
    def getLibraryTypes(self, ip_name):
        '''Return the set of library types in the specified IP.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>>
        >>> config.getLibraryTypes('icmanageworkspace01')
        set([u'ipspec', u'rtl', u'rdf'])
        >>> config.getLibraryTypes('icmanageworkspace02')
        set([u'wild', u'rtl', u'ipspec', u'rdf', u'ipfram'])
        >>> config.getLibraryTypes('icmanageworkspace03')
        set([u'ipspec', u'rtl'])
        >>> config.getLibraryTypes('icmanageworkspace04')
        set([u'rtl', u'rdf'])
        >>> config.getLibraryTypes('nonexistent')
        set([])
        '''
        libraryTypes = set()
        for jsonConfiguration in self.configurations:
            if (('config' in jsonConfiguration) and 
                ip_name == jsonConfiguration['variant'] and
                jsonConfiguration['type'] != 'config'):
                libraryTypes.add(jsonConfiguration['libtype'])
        return libraryTypes

    @property
    def composites(self):
        '''A dictionary whose keys are every `ipName` in the configuration.
        
        Each value is the `[projectName, ipName, configurationName]` triplet for
        the `ipName`.
        
        That is, this dictionary contains an entry for every composite
        configuration within the configuration specified upon instantiation.
        
        Just as you would guess, `ipName` within the value triplet is equal to
        the key.
        
        If you want the library configurations in the workspace, use property
        :attr:`~ICManageConfiguration.configurations`.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.composites
        {'icmanageworkspace04': ['zz_dm_test', 'icmanageworkspace04', 'dev'], 'icmanageworkspace03': ['zz_dm_test', 'icmanageworkspace03', 'dev'], 'icmanageworkspace02': ['zz_dm_test', 'icmanageworkspace02', 'dev'], 'icmanageworkspace01': ['zz_dm_test', 'icmanageworkspace01', 'dev']}
        '''
        if self._compositesAlwaysAccessViaProperty is None:
            self._setHierarchyAndComposites()
        return self._compositesAlwaysAccessViaProperty

    @property
    def hierarchy(self):
        """Dictionary containing an entry for each IP in the workspace.
        The value of each entry is the set of children of the IP.
        
        For instance, the examples below operate on the following hierarchy::
        
                +------------------------------+
                |      icmanageworkspace01     |
                |      contains libType rdf    |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace02     |
                |      contains libType rdf    |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace03     |
                | does not contain libType rdf |
                +--------------+---------------+
                               |
                               v
                +------------------------------+
                |      icmanageworkspace04     |
                |      contains libType rdf    |
                +------------------------------+
        
        If no library type was specified upon instantiation, the entire IP
        hierarchy is included:

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.hierarchy
        {'icmanageworkspace04': [], 'icmanageworkspace03': ['icmanageworkspace04'], 'icmanageworkspace02': ['icmanageworkspace03'], 'icmanageworkspace01': ['icmanageworkspace02']}

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace02', 'dev')
        >>> config.hierarchy
        {'icmanageworkspace04': [], 'icmanageworkspace03': ['icmanageworkspace04'], 'icmanageworkspace02': ['icmanageworkspace03']}

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace03', 'dev')
        >>> config.hierarchy
        {'icmanageworkspace04': [], 'icmanageworkspace03': ['icmanageworkspace04']}

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace04', 'dev')
        >>> config.hierarchy
        {'icmanageworkspace04': []}
        
        If a library type is specified, the hierarchy includes only IPs that
        have the specified library type.  For example, `icmanageworkspace03`
        does not contain `rdf`, so the hierarchy stops above it, at
        `icmanageworkspace02`:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
        >>> config.hierarchy
        {'icmanageworkspace02': [], 'icmanageworkspace01': ['icmanageworkspace02']}

        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='nonexistent')
        >>> config.hierarchy
        {}
        """
        if self._hierarchyAlwaysAccessViaProperty is None:
            self._setHierarchyAndComposites()
        return self._hierarchyAlwaysAccessViaProperty

    @classmethod
    def isRelease(cls, configurationName):
        """Return True if the specified configuration is a release configuration.
        
        >>> ICManageConfiguration.isRelease('endsWithREL')
        False
        >>> ICManageConfiguration.isRelease('RELForReal')
        True
        """
        return configurationName.startswith('REL')
    
    @classmethod
    def isSnapRelease(cls, configurationName):
        """Return True if the specified configuration is a snap release
        configuration.
        
        >>> ICManageConfiguration.isSnapRelease('endsWithsnap-')
        False
        >>> ICManageConfiguration.isSnapRelease('snap-ForReal')
        True
        """
        return configurationName.startswith('snap-')
    
    @property
    def creationTime(self):
        """The Python `datetime <http://docs.python.org/2/library/datetime.html>`_
        on which the configuration was created.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'REL2.0--TEST__11ww001aaa')
        >>> time = config.creationTime
        >>> type(time)
        <type 'datetime.datetime'>
        >>> str(time)
        '2013-03-14 16:37:36'
        """
        if self._creationTimeAlwaysAccessViaProperty is None:
            self._setTimes()
        return self._creationTimeAlwaysAccessViaProperty

    @property
    def modificationTime(self):
        """The Python `datetime <http://docs.python.org/2/library/datetime.html>`_
        on which the configuration was last modified.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'REL2.0--TEST__11ww001aaa')
        >>> time = config.modificationTime
        >>> type(time)
        <type 'datetime.datetime'>
        >>> str(time)
        '2013-03-14 16:38:20'
        """
        if self._modificationTimeAlwaysAccessViaProperty is None:
            self._setTimes()
        return self._modificationTimeAlwaysAccessViaProperty

    def _setTimes(self):
        '''Retrieve the dates from IC Manage and set the corresponding instance
        variables.
        
        Tested in the :attr:`~ICManageConfiguration.creationTime` and
        :attr:`~ICManageConfiguration.modificationTime` properties.
        '''
        assert (self._creationTimeAlwaysAccessViaProperty is None and 
                self._modificationTimeAlwaysAccessViaProperty is None), \
                "_creationTimeAlwaysAccessViaProperty and " \
                "_modificationTimeAlwaysAccessViaProperty are always set together"
                
        commandOutput = self.icm._get_objects('/intel/{}/{}/{}/.**::'.format(self._projectName, self._ipName, self._configurationName), ['type', 'path', 'content', 'created', 'modified'])

        if not commandOutput:
            # Even if there is no such file, icmp4 print gives no error.
            # p4 print does the same, so this is not IC Manage's fault.
            # So the same thing happens for empty and nonexistent files.
            return
        
        self._creationTimeAlwaysAccessViaProperty = commandOutput[0]['created'] 
        self._modificationTimeAlwaysAccessViaProperty = commandOutput[0]['modified'] 
        
        
    def getConfigurationTriplet(self, ipName):
        '''Return the `[projectName, ipName, configurationName]` list for the
        specified IP.
                
        If you want the library configurations in the workspace, use property
        `configurations`.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.getConfigurationTriplet('icmanageworkspace01')
        ['zz_dm_test', 'icmanageworkspace01', 'dev']
        >>> config.getConfigurationTriplet('icmanageworkspace02')
        ['zz_dm_test', 'icmanageworkspace02', 'dev']
        >>> config.getConfigurationTriplet('icmanageworkspace03')
        ['zz_dm_test', 'icmanageworkspace03', 'dev']
        '''
        if self._compositesAlwaysAccessViaProperty is None:
            self._setHierarchyAndComposites()
        try:
            return list(self._compositesAlwaysAccessViaProperty[ipName])
        except:
            raise dmError(
                "IP '{}' is not in the workspace.".format(ipName))

    def getIPsInHierarchy(self, ipName):
        """Return a set containing the specified IP name and the names of all
        IPs instantiated by it.
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
        >>> config.getIPsInHierarchy('icmanageworkspace01')
        set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02', 'icmanageworkspace01'])
        >>> config.getIPsInHierarchy('icmanageworkspace02')
        set(['icmanageworkspace04', 'icmanageworkspace03', 'icmanageworkspace02'])
        >>> config.getIPsInHierarchy('icmanageworkspace03')
        set(['icmanageworkspace04', 'icmanageworkspace03'])
        """
        ipNames = set([str(ipName)])
        for subIpName in self.hierarchy[ipName]:
            ipNames |= self.getIPsInHierarchy(str(subIpName))
        return ipNames
        
    def _setHierarchyAndComposites(self):
        """Get the composites and hierarchyfrom the
        //depot/icm/configs/projectName/ipName/configurationName.icmCfg files.
        The data are so closely related that they are both extracted
        at once.
        
        Tested in the composites and hierarchy properties.
        """
        # _ipName is unicode when it comes from getWorkspaceAttribute()
        assert self._compositesAlwaysAccessViaProperty is None, \
                'The composites should never be re-initialized'
        assert self._hierarchyAlwaysAccessViaProperty is None, \
                'The hierarchy should never be re-initialized'
        self._compositesAlwaysAccessViaProperty = {}
        self._hierarchyAlwaysAccessViaProperty = {}
        self._setHierarchyAndCompositesRecursive(self._projectName,
                                                 self._ipName,
                                                 self._configurationName)

    def _setHierarchyAndCompositesRecursive(self, projectName, ipName,
                                            configurationName):
        """Recursively extract the IP hierarchy from IC Manage.
        
        The data for the composites and hierarchy are so closely related that
        they are both extracted at once.
        
        Tested in the composites and hierarchy properties.

        This method is based on work by Anthony Galdes of IC Manage.
        """
        if not self._hasLibTypeFast(ipName):
            return

        if not self._addToComposites (projectName, ipName, configurationName):
            return # See http://fogbugz.altera.com/default.asp?221402 (infinite recursion)

        if ipName not in self._hierarchyAlwaysAccessViaProperty:
            self._hierarchyAlwaysAccessViaProperty[str(ipName)] = []
       
        #http://pg-rdjira.altera.com:8080/browse/DI-422 
        #Get config content from pm
        commandOutput = _getConfigContent(projectName, ipName, configurationName)
        commandOutput = commandOutput.decode()
        if not commandOutput:
            return

        for num, line in enumerate(commandOutput.rstrip().split('\n')):     
            # Skip the first line

            # config  /intel/i10socfm/liotest3/dev    
            # library /intel/i10socfm/liotest3/reldoc/dev 
            # release /intel/i10socfm/liotest3/ipspec/REL1.0FM6revA0__22ww112a
            if line.startswith(("release", "library")):
                continue
            # = re.match('.*Configuration="(.*?)".*Project="(.*?)".*Variant="(.*?)"', line)
            m = re.match('config.*/intel/(\S+)/(\S+)/(\S+)', line)
            if m:
                childProjectName = m.group(1)
                childIpName = m.group(2)
                childConfigurationName = m.group(3)
                if childProjectName == projectName and childIpName == ipName and childConfigurationName == configurationName:
                    continue
                #print childProjectName, childIpName, childConfigurationName
            else:
                raise dmError('Error getting sub-ips for {}/{}@{}'.format(projectName, ipName, configurationName))

            if self._hasLibTypeFast(childIpName):
                self._addToHierarchy(ipName, childIpName)
            # Recurse
            self._setHierarchyAndCompositesRecursive(childProjectName,
                                                     childIpName,
                                                     childConfigurationName)
    
    def _addToComposites(self, projectName, ipName, configName):
        '''
        Add the specified IP's configuration triplet.
        Returns:
            True (wasn't there, added)
            False (was already there, nothing done
        '''
        assert ipName
        
        if ipName not in self._compositesAlwaysAccessViaProperty:
            self._compositesAlwaysAccessViaProperty[ipName] = \
                    [projectName, ipName, configName]
            return True
        else:
            return False


    def _addToHierarchy(self, parentIPName, childIPName):
        '''Add the specified hierarchical relationship.
        
        When `childIPName` is `None` and the parent does not yet exist, just add
        the parent with no children.
        '''
        if childIPName not in self._hierarchyAlwaysAccessViaProperty:
            self._hierarchyAlwaysAccessViaProperty[childIPName] = []
            
        if parentIPName in self._hierarchyAlwaysAccessViaProperty:
            children = self._hierarchyAlwaysAccessViaProperty[parentIPName]
            if childIPName not in children:
                children.append(childIPName)
        else:
            self._hierarchyAlwaysAccessViaProperty[parentIPName] = [childIPName]

#    def hasIp(self, ip_name):
#        '''Return True if the specified IP is present in the hierarchy of the
#        IP or the workspace that was specified upon instantiation.
#        
#        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev')
#        >>> config.hasIp('icmanageworkspace01')
#        True
#        >>> config.hasIp('icmanageworkspace02')
#        True
#        >>> config.hasIp('icmanageworkspace03')
#        True
#        >>> config.hasIp('nonexistent')
#        False
#        '''
#        for jsonConfiguration in self.configurations:
#            if jsonConfiguration['Variant'] == ip_name:
#                return True
#        return False
    
    def _hasLibTypeFast(self, ipName):
        '''Return True if the library type specified upon instantiation is
        included in the specified IP.
        
        For the sake of efficency, `_hasLibTypeFast()` presumes that the
        specified IP exists.  Incorrect results can occur if the IP does not
        exist:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType=None)
        >>> config._hasLibTypeFast('nonexistentIP')
        True
        
        Client programmers should use ``ipName in config.ipNames``:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
        >>> config.ipNames
        set(['icmanageworkspace02', 'icmanageworkspace01'])
        >>>
        >>> 'icmanageworkspace02' in config.ipNames
        True
        >>> 'icmanageworkspace03' in config.ipNames
        False
        >>> 'nonexistentIP' in config.ipNames
        False
        
        In the following examples, `icmanageworkspace01` exists, so
        `_hasLibTypeFast()` operates correctly:
        
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rtl')
        >>> config._hasLibTypeFast('icmanageworkspace01')
        True
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='rdf')
        >>> config._hasLibTypeFast('icmanageworkspace01')
        True
        >>> config = ICManageConfiguration('zz_dm_test', 'icmanageworkspace01', 'dev', libType='wild')
        >>> config._hasLibTypeFast('icmanageworkspace01')
        False
        '''
        if self._libType is None:
            return True
        if self._ipNamesWithLibTypeAlwaysAccessViaProperty is None:
            self._ipNamesWithLibTypeAlwaysAccessViaProperty = self.getIpNames(self._libType)
        return ipName in self._ipNamesWithLibTypeAlwaysAccessViaProperty

        
if __name__ == "__main__":
    # Running ICManageWorkspace_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
    
