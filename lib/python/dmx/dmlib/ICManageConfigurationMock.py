#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageConfigurationMock.py#1 $

'''
Mock an instance of the :py:class:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration`
class to allow testing without contacting the IC Manage server.

Error Checking
================
To help you specify internally-consistent mock workspaces, the following
rules are enforced by assertions:

* If specified, the ``hierarchy`` and ``ipNames`` arguments must contain \
  the value of ``ipName`` as a key.
* If both the ``hierarchy`` and ``ipNames`` arguments are specified, \
  they must specify the same set of IPs (they must have the same keys)

The ``projectName``, ``ipName`` and ``configurationName`` Arguments
================================================================

These are the names that make up the `project/ip/configuration` triplet that
uniquely identifies an IC Manage configuration.  `ipName` is synonymous with
IC Manage `variant`.

>>> config = ICManageConfigurationMock(projectName='ElProjecto',
...                                    ipName='ip1',
...                                    configurationName='REL-1.0')
>>> config.projectName
'ElProjecto'
>>> config.ipName
'ip1'
>>> config.configurationName
'REL-1.0'

``ipName`` is required.  The default ``projectName`` is "project", and the
default ``configurationName`` is "dev".  The defaults are usually satisfactory:

>>> config = ICManageConfigurationMock('ip1')
>>> config.projectName
'project'
>>> config.ipName
'ip1'
>>> config.configurationName
'dev'

The ``hierarchy`` Argument
==================================
Specify the IP hierarchy using the ``hierarchy`` argument.  This is a
dictionary of the same style as that returned by the real
:py:attr:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration.hierarchy`
property:

For example, this workspace contains IP `ip1`, which instantiates `ip2`,
which instantiates `ip3`:

>>> config = ICManageConfigurationMock('ip1', hierarchy={'ip3': [], 'ip2': ['ip3'], 'ip1': ['ip2']})
>>> config.hierarchy
{'ip2': ['ip3'], 'ip3': [], 'ip1': ['ip2']}

For convenience, if you do not specify the ``hierarchy`` argument, the hierarchy
will be calculated from other arguments given:

1. The ``ipNames`` argument:

>>> config = ICManageConfigurationMock('ip1', ipNames=set(['ip1', 'ip2']))
>>> config.hierarchy
{'ip2': [], 'ip1': []}

2. The ``ipName`` argument

>>> config = ICManageConfigurationMock('ip1')
>>> config.hierarchy
{'ip1': []}

The ``ipNames`` Argument
==============================

Specify the set of IPs using the ``ipNames`` argument.  This is the set of IPs
in the mocked
:attr:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration.ipNames` property and the mocked
:meth:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration.getIpNames` method.

The real :py:class:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration` constructor
and :meth:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration.getIpNames` have a
``libType`` argument that allows you to select IPs with a given library type.
:func:`~ICManageConfigurationMock` has no such
argument, and the 
:meth:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration.getIpNames` ``libType``
argument is ignored.  In your test, just specify ``ipNames`` limited to the IPs
you want returned.

>>> config = ICManageConfigurationMock('ip1', ipNames=set(['ip1', 'ip2']))
>>> config.ipNames
set(['ip2', 'ip1'])
>>> config.getIpNames('any_lib_type_at_all')
set(['ip2', 'ip1'])

For convenience, if you do not specify the ``ipNames`` argument, the value will
be calculated from other arguments given:

1. The keys of the ``hierarchy`` argument:

>>> config = ICManageConfigurationMock('ip1', hierarchy={'ip3': [],
...                                                      'ip2': ['ip3'],
...                                                      'ip1': ['ip2']})
>>> config.ipNames
set(['ip2', 'ip3', 'ip1'])
>>> config.getIpNames('any_lib_type_at_all')
set(['ip2', 'ip3', 'ip1'])

2. The ``ipName`` argument

>>> config = ICManageConfigurationMock('ip1')
>>> config.ipNames
set(['ip1'])
>>> config.getIpNames('any_lib_type_at_all')
set(['ip1'])

The ``configurations`` Property
===================================

The ``configurations`` property is synthesized from ``ipNames``, ``projectName``
and ``configurationName``.  All configuration triplet values share the same
project and configuration name:

>>> config = ICManageConfigurationMock('ip1', ipNames=set(['ip1', 'ip2']))
>>> config.composites
{'ip2': ['project', 'ip2', 'dev'], 'ip1': ['project', 'ip1', 'dev']}

Querying Depot Files
================================

The real :meth:`dmx.dmlib.ICManageConfiguration.isFileExisting` method returns `True`
if the specified file exists in the IC Manage depot.  The mock
``isFileExisting()`` returns `True` if the file is specified in the set given as
the `existingFiles` argument.  The specification of files within the
`existingFiles` argument is the same as the arguments for
:meth:`dmx.dmlib.ICManageConfiguration.isFileExisting`.

>>> config = ICManageConfigurationMock('ip1', existingFiles=set([
...                                           ('ip1', 'cell_names.txt', 'ipspec'),
...                                           ('ip2', 'cell_names.txt', 'ipspec', 'ip2'),
...                                           ('ip2', 'cell_names.txt', 'ipspec', 'dev')
...                                           ]))
>>> config.isFileExisting('ip1', 'cell_names.txt', 'ipspec')
True
>>> config.isFileExisting('ip1', 'cell_names.txt', 'ipspec', libName='ip1')
True
>>> config.isFileExisting('ip1', 'cell_names.txt', 'ipspec', libName='nonexistentLibName')
False
>>>
>>> config.isFileExisting('ip2', 'cell_names.txt', 'ipspec', libName='dev')
True
>>> config.isFileExisting('ip2', 'cell_names.txt', 'ipspec')
False



Class Methods
================
Inasmuch as it makes sense, :func:`~ICManageConfigurationMock` defines class methods
using the actual methods from :py:class:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration`.

.. note:
    No class methods for now.

Defining Other ICManageConfiguration Methods
=======================================================

You must define the behavior for the remainder of the instance methods used
by the code under test.  See the documentation for
:mod:`~dmx.dmlib.ICManageWorkspaceMock` for instructions on
how to do this.

The Mock Function
======================
'''

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"


from mock import Mock

from dmx.dmlib.ICManageConfiguration import ICManageConfiguration
from dmx.dmlib.ICManageBase import ICManageBase


def ICManageConfigurationMock(ipName,
                              projectName='project',
                              configurationName='dev',
                              hierarchy=None,
                              ipNames=None,
                              existingFiles=None):
    '''Define a mock of an
    :py:class:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration` instance.
    '''
    if ipNames is None:
        if hierarchy is None:
            # dmx.dmlib.ICManageWorkspaceMock._processCellNamesDict() does an analogous thing
            ipNames = set([ipName])
        else:
            ipNames = set(hierarchy.keys())
    if hierarchy is None:
        hierarchy = dict()
        for ipName_ in ipNames:
            hierarchy[ipName_] = []
    
    assert isinstance(hierarchy, dict), \
        "'hierarchy' must be a dict()"
    assert isinstance(ipNames, set), \
        "'ipNames' must be a set()"
    assert ipName in hierarchy, \
        "'ipName' must appear in 'hierarchy'"
    assert ipName in ipNames, \
        "'ipName' must appear in 'ipNames'"
    assert set(hierarchy.keys()) ==  ipNames, \
        "The IPs specified by the 'hierarchy' and 'ipNames' " \
        "arguments must be the same"

    spec = dir(ICManageConfiguration)
    spec.extend(dir(ICManageBase))
    config = Mock(spec=spec, name='ICManageConfigurationMock')
    config._spec_class = ICManageConfiguration
    
    config.projectName = projectName
    config.ipName = ipName
    config.configurationName = configurationName

    config.getIpNames.return_value = ipNames
    config.ipNames = ipNames
    
    config.composites = dict()
    for ipName_ in ipNames:
        config.composites[ipName_] = [projectName, ipName_, configurationName]
        
    config.hierarchy = hierarchy
    
    def isFileExistingProxy(ipName, fileName, libType, libName=None):
        if existingFiles is None:
            # No existing files at all specified
            return False
        
        if libName is None or libName == ipName:
            if (ipName, fileName, libType) in existingFiles:
                return True
        if (ipName, fileName, libType, libName) in existingFiles:
            return True
        return False
    config.isFileExisting = isFileExistingProxy 

    # Class methods
    config.getLibType = ICManageBase.getLibType
    config.getDeliverableName = ICManageBase.getDeliverableName

    # ICManageConfiguration.getConfigurationsFromICManage() is a class method, but
    # it cannot be used as-is because it touches IC Manage.
    
    return config
