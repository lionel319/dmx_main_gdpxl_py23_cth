#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageWorkspaceMock.py#1 $

'''
Mock an instance of the :py:class:`~dmx.dmlib.ICManageWorkspace.ICManageWorkspace`
class to allow testing without contacting the IC Manage server or using
real IC Manage workspaces.

Error Checking
================
To help you specify internally-consistent mock workspaces, the following
rules are enforced by assertions:

* If specified, the ``workspacePath`` argument must specify an existing path
* If specified, the ``hierarchy`` and ``cellNamesDict`` arguments must contain \
  the value of the ``topIpName`` argument as a key.
* If both the ``hierarchy`` and ``cellNamesDict`` arguments are specified, \
  they must specify the same set of IPs (they must have the same keys)

See :mod:`~dmx.dmlib.ICManageConfigurationMock` for further rules.

The ``topIpName`` Argument
==========================
The ``topIpName`` argument is the top of the hierarchy to be examined:
    
>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.ipName
'ip1'

In the real :py:class:`~dmx.dmlib.ICManageWorkspace.ICManageWorkspace`, ``topIpName``
defaults to the workspace top IP.  However,
:func:`~dmx.dmlib.ICManageWorkspaceMock.ICManageWorkspaceMock` cannot query IC Manage
to find a default value, so ``topIpName`` must always be specified.

The ``workspacePath`` Argument
=================================
``workspacePath`` is the directory that you want to use as the workspace root.
It must be an existing directory, but it is otherwise accepted as the workspace
root directory.  For example:

>>> ws = ICManageWorkspaceMock('ip1', workspacePath='/usr/bin')
>>> ws.path
'/usr/bin'

>>> ws = ICManageWorkspaceMock('ip1', workspacePath='/nonexistent')  #doctest: +ELLIPSIS
Traceback (most recent call last):
  ...
dmError: The specified workspace path '/nonexistent' is not a directory.

``workspacePath`` defaults to the current working directory:

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.path == os.path.abspath(os.path.curdir)
True

The mocked ``findWorkspace()`` works the same way:

>>> ws = ICManageWorkspaceMock('ip1', workspacePath='/usr/bin')
>>> ws.findWorkspace('/etc')
'/etc'
>>> ws.findWorkspace() == os.path.abspath(os.path.curdir)
True
>>> ws.findWorkspace('/nonexistent')  #doctest: +ELLIPSIS
Traceback (most recent call last):
  ...
dmError: The specified workspace path '/nonexistent' is not a directory.

Similarly, ``isWorkspace()`` merely checks whether the given path is an existing
directory:

>>> ws.isWorkspace('/etc')
True
>>> ws.isWorkspace('/nonexistent/path')
False
>>> ws.isWorkspace('/bin/ls')    # Exists, but not a directory
False

The ``cellNamesDict`` Argument
================================================
The ``cellNamesDict`` argument is a dictionary whose key is an IP name and
value is the set of cell names for that IP.  This mimics the
`cell_names.txt` file.  This data will be used by the mocked
``getIPNameForCellName()``, ``getCellNamesForIPName()`` methods, and by
:func:`~dmx.dmlib.ICManageConfigurationMock.ICManageConfigurationMock`.
    
>>> ws = ICManageWorkspaceMock('ip1', cellNamesDict={'ip1' : set(['cella', 'cellb']),
...                                                  'ip2' : set(['cellc', 'celld'])})
>>> ws.getCellNamesForIPName('ip1')
set(['cella', 'cellb'])
>>> ws.getCellNamesForIPName('ip2')
set(['cellc', 'celld'])
>>> ws.getCellNamesForIPName('undefined') #doctest: +ELLIPSIS
Traceback (most recent call last):
  ...
dmError: There is no IP named 'undefined' in the workspace
>>>
>>> ws.getIPNameForCellName('cella')
'ip1'
>>> ws.getIPNameForCellName('cellb')
'ip1'
>>> ws.getIPNameForCellName('cellc')
'ip2'
>>> ws.getIPNameForCellName('celld')
'ip2'
>>> ws.getIPNameForCellName('undefined') #doctest: +ELLIPSIS
Traceback (most recent call last):
  ...
dmError: There is no cell (or IP) named 'undefined' ...

For convenience, you can specify that an IP contains a single cell with the
same name as the IP by giving any ``cellName`` value that evaluates to `False`.
For instance, all of the IPs in the following example contain a single cell
with the same name as the IP:

>>> ws = ICManageWorkspaceMock('ip1', cellNamesDict={'ip1' : set(['ip1']),
...                                                    'ip2' : set([]),
...                                                    'ip3' : [],
...                                                    'ip4' : '',
...                                                    'ip5' : 0,
...                                                    'ip6' : None})
>>> ws.getCellNamesForIPName('ip1')
set(['ip1'])
>>> ws.getCellNamesForIPName('ip2')
set(['ip2'])
>>> ws.getCellNamesForIPName('ip3')
set(['ip3'])
>>> ws.getCellNamesForIPName('ip4')
set(['ip4'])
>>> ws.getCellNamesForIPName('ip5')
set(['ip5'])
>>> ws.getCellNamesForIPName('ip6')
set(['ip6'])

For even more convenience, if you do not specify the ``cellNamesDict`` argument,
the value will be calculated from other arguments given:

1. The keys of the ``hierarchy`` argument:

>>> ws = ICManageWorkspaceMock('ip1', hierarchy={'ip3': [],
...                                              'ip2': ['ip3'],
...                                              'ip1': ['ip2']})
>>> ws.getCellNamesForIPName('ip1')
set(['ip1'])
>>> ws.getCellNamesForIPName('ip2')
set(['ip2'])
>>> ws.getCellNamesForIPName('ip3')
set(['ip3'])

2. The ``ipName`` argument

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.getCellNamesForIPName('ip1')
set(['ip1'])

The ``elementsDict`` Argument
================================================
The ``elementsDict`` argument is a dictionary whose key is a cell name and
value is the set of elements for that IP.  This mimics the
`elements.txt` files.  This data will be used by the mocked
``getCellsInList('elements')`` method.
    
>>> ws = ICManageWorkspaceMock('ip1', elementsDict={'cella' : set(['cellb', 'celld']),
...                                                  'cellb' : set(['cellc']),
...                                                  'cellc' : set([])})
>>> ws.getCellsInList('ip1', 'elements', 'cella')
set(['cellb', 'celld'])
>>> ws.getCellsInList('ip1', 'elements', 'cellb')
set(['cellc'])
>>> ws.getCellsInList('ip1', 'elements', 'cellc')
set([])

If the specified `cellName` is not a key in `elementsDict`, an exception is
raised:
  
>>> ws = ICManageWorkspaceMock('ip1', elementsDict={'cella' : set(['cellb', 'celld'])})
>>> ws.getCellsInList('ip1', 'elements', cellName='nonexistent')
Traceback (most recent call last):
  ...
dmError: The specified cell 'nonexistent' is invalid because it is not a cell in IP 'ip1'.

Also, an exception is raised if you  specify the name of a list that does not
exist:

>>> ws = ICManageWorkspaceMock('ip1', elementsDict={'cella' : set(['cellb', 'celld'])})
>>> ws.getCellsInList('ip1', 'nonexistent')
Traceback (most recent call last):
  ...
dmError: In deliverable 'IPSPEC', there is no pattern named 'nonexistent'.

The `isIPNameDefault` argument works with `elements`, but
*using `isIPNameDefault=True` with per-cell lists like `elements` is probably not useful*:

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.getCellsInList('ip1', 'elements', isIPNameDefault=True)
set(['ip1'])
>>> ws.getCellsInList('ip1', 'elements', isIPNameDefault=False)
set([])
        

The ``moleculesDict`` Argument
================================================
The ``moleculesDict`` argument is a dictionary whose key is a cell name and
value is the set of molecules for that IP.  This mimics the
`molecules.txt` files.  This data will be used by the mocked
``getCellsInList('molecules')`` method.
    
>>> ws = ICManageWorkspaceMock('ip1', moleculesDict={'cella' : set(['cellb', 'celld']),
...                                                  'cellb' : set(['cellc']),
...                                                  'cellc' : set([])})
>>> ws.getCellsInList('ip1', 'molecules', 'cella')
set(['cellb', 'celld'])
>>> ws.getCellsInList('ip1', 'molecules', 'cellb')
set(['cellc'])
>>> ws.getCellsInList('ip1', 'molecules', 'cellc')
set([])

If the specified `cellName` is not a key in `moleculesDict`, an exception is
raised:
  
>>> ws = ICManageWorkspaceMock('ip1', moleculesDict={'cella' : set(['cellb', 'celld'])})
>>> ws.getCellsInList('ip1', 'molecules', cellName='nonexistent')
Traceback (most recent call last):
  ...
dmError: The specified cell 'nonexistent' is invalid because it is not a cell in IP 'ip1'.

Also, an exception is raised if you  specify the name of a list that does not
exist:

>>> ws = ICManageWorkspaceMock('ip1', moleculesDict={'cella' : set(['cellb', 'celld'])})
>>> ws.getCellsInList('ip1', 'nonexistent')
Traceback (most recent call last):
  ...
dmError: In deliverable 'IPSPEC', there is no pattern named 'nonexistent'.

The `isIPNameDefault` argument works with `molecules`, but
*using `isIPNameDefault=True` with per-cell lists like `molecules` is probably not useful*:

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.getCellsInList('ip1', 'molecules', isIPNameDefault=True)
set(['ip1'])
>>> ws.getCellsInList('ip1', 'molecules', isIPNameDefault=False)
set([])
        

The ``hierarchy`` Argument
===============================
Specify the IP hierarchy with the ``hierarchy`` argument.  This is a
dictionary of the same style as that returned by the real
:py:attr:`~dmx.dmlib.ICManageConfiguration.ICManageConfiguration.hierarchy` property.

For example, this workspace contains IP `ip1`, which instantiates `ip2`,
which instantiates `ip3`:

>>> ws = ICManageWorkspaceMock('ip1', hierarchy={'ip3': [], 'ip2': ['ip3'], 'ip1': ['ip2']})
>>> ws.hierarchy
{'ip2': ['ip3'], 'ip3': [], 'ip1': ['ip2']}

If you do not specify the ``hierarchy`` argument, the IP hierarchy is presumed
to consist of ``topIPName`` alone:

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.hierarchy
{'ip1': []}


    
Class Methods
================
Inasmuch as it makes sense, :func:`~dmx.dmlib.ICManageWorkspaceMock.ICManageWorkspaceMock` defines class methods
using the actual methods from :py:class:`~dmx.dmlib.ICManageWorkspace.ICManageWorkspace`:

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.getAbsPathOrCwd('/usr/bin')
'/usr/bin'
>>> ws.getLibType('RTL')
'rtl'
>>> ws.getDeliverableName('rtl')
'RTL'

Defining Other ICManageWorkspace Methods
=========================================
You must define the behavior for the remainder of the instance methods used
by the code under test.  For example, suppose the code under test uses
`ICManageWorkspace.getCellsInList()`.  Specify a return value for
:func:`~dmx.dmlib.ICManageWorkspaceMock.ICManageWorkspaceMock`, and the code under 
test will receive this value:

>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.getInfo.return_value = '/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.ip1'
>>> ws.getInfo('Client root')
'/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.ip1'
>>> ws.getInfo('anyOtherArgument')
'/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.ip1'

In the above example, the same value is returned regardless of the specified
argument.  If you need different behavior, define a proxy function to do
whatever you need:

>>> def getInfoProxy(name):
...     if name == 'Client root':
...         return '/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.ip1'
...     if name == 'Client name':
...         return 'rgetov.zz_dm_test.ip1'
...     return 'Something else'
>>> ws = ICManageWorkspaceMock('ip1')
>>> ws.getInfo = getInfoProxy
>>>
>>> ws.getInfo('Client root')
'/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.ip1'
>>> ws.getInfo('Client name')
'rgetov.zz_dm_test.ip1'
>>> ws.getInfo('Other')
'Something else'

The Mock Function
======================
'''

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"


import os # @UnusedImport pylint: disable=W0611 
#from mock import Mock # @UnusedImport pylint: disable=W0611
from dmx.dmlib.Manifest import Manifest # @UnusedImport pylint: disable=W0611
from dmx.dmlib.dmError import dmError


def _processCellNamesDict(topIpName, cellNamesDict, hierarchy):
    '''Return the specified ``cellNamesDict`` pre-processed to make all the
    defaults explicit.  Check the values for errors and adherence to conventions
    and raise assertion errors for violations.

    When all cells are specified, the input is passed through without
    modification:
    
    >>> _processCellNamesDict('ip1',
    ...                       {'ip1' : set(['cella', 'cellb']),
    ...                        'ip2' : set(['cellc', 'celld'])},
    ...                       None)
    {'ip2': set(['cellc', 'celld']), 'ip1': set(['cella', 'cellb'])}
    
    If ``cellNamesDict`` is `None`, use the IPs from the ``hierarchy`` argument:
    
    >>> _processCellNamesDict('ip1',
    ...                       None,
    ...                       {'ip3': [], 'ip2': ['ip3'], 'ip1': ['ip2']})
    {'ip2': set(['ip2']), 'ip3': set(['ip3']), 'ip1': set(['ip1'])}
    
    If both ``cellNamesDict`` and ``hierarchy`` are `Bone`, default to a single
    IP containing a single cell:
    
    >>> _processCellNamesDict('ip1', None, None)
    {'ip1': set(['ip1'])}
    
    If a ``cellNameDict`` value evaluates to `False`, it is presumed to be
    the same as its corresponding key:
    
    >>> _processCellNamesDict('ip1', {'ip1' : set(['ip1']),
    ...                              'ip2' : set([]),
    ...                              'ip3' : [],
    ...                              'ip4' : '',
    ...                              'ip5' : 0,
    ...                              'ip6' : None},
    ...                              None)
    {'ip2': set(['ip2']), 'ip3': set(['ip3']), 'ip1': set(['ip1']), 'ip6': set(['ip6']), 'ip4': set(['ip4']), 'ip5': set(['ip5'])}
    
    ``cellNamesDict`` must contain 'topIpName' as a key:
    
    By convention, when an IP contains a single cell, it should be named the
    same as the IP:
    
    >>> _processCellNamesDict('ip1', {'ip1' : set(['ip2'])}, None) #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    AssertionError: The ICManageWorkspaceMock argument 'cellNamesDict' contains IP 'ip1' with a single cell 'ip2'...
    '''
    newCellNamesDict = {}
    
    if cellNamesDict is not None:
        for ipName, cellNames in cellNamesDict.items():
            if not cellNames:
                newCellNamesDict[ipName] = set([ipName])
            else:
                assert len(cellNames) > 1 or set([ipName]) == cellNames, \
                    "The ICManageWorkspaceMock argument 'cellNamesDict' contains IP '{}' with " \
                    "a single cell '{}'.  By convention, the names should be the same." \
                    "".format(ipName, set(cellNames).pop())
                newCellNamesDict[ipName] = cellNames
    elif hierarchy is not None:
        for ipName in hierarchy.keys():
            newCellNamesDict[ipName] = set([ipName])
    else:
        newCellNamesDict[topIpName] = set([topIpName])

    return newCellNamesDict

def ICManageWorkspaceMock(topIpName, # pylint: disable = W0102
                          workspacePath=None,
                          hierarchy=None,
                          cellNamesDict=None,
                          elementsDict={},
                          moleculesDict={}):
    '''Define a mock of an :py:class:`~dmx.dmlib.ICManageWorkspace.ICManageWorkspace`
    instance.
    '''
    assert hierarchy is None or topIpName in hierarchy, \
        "'topIpName' must appear in 'hierarchy'"
    assert cellNamesDict is None or topIpName in cellNamesDict, \
        "'topIpName' must appear in 'cellNamesDict'"
    assert hierarchy is None or cellNamesDict is None or \
        set(hierarchy.keys()) ==  set(cellNamesDict.keys()), \
        "The IPs (keys) specified by the 'hierarchy' and 'cellNamesDict' " \
        "arguments must be the same"

    from dmx.dmlib.ICManageWorkspace import ICManageWorkspace
    from dmx.dmlib.ICManageConfigurationMock import ICManageConfigurationMock
    #from dmx.dmlib.ICManageBase import ICManageBase

    _cellNamesDict = _processCellNamesDict(topIpName, cellNamesDict, hierarchy)
    if cellNamesDict is None:
        # Leave the ipNames default calculation to ICManageConfigurationMock()
        ws = ICManageConfigurationMock(topIpName,
                                       hierarchy=hierarchy,
                                       ipNames=None)
    else:
        ws = ICManageConfigurationMock(topIpName,
                                       hierarchy=hierarchy,
                                       ipNames=set(_cellNamesDict.keys()))
    ws._mock_methods.extend(dir(ICManageWorkspace)) # pylint: disable = W0212
    ws._mock_name = 'ICManageWorkspaceMock'
    ws._spec_class = ICManageWorkspace

    ws.path = ICManageWorkspace.getAbsPathOrCwd(workspacePath)


    def getIPNameForCellNameProxy(cellName):
        for ipName, cellNames in _cellNamesDict.items():
            if cellName in cellNames:
                return ipName
        raise dmError("There is no cell (or IP) named '{}' in any of the IPs in the workspace"
              "".format(cellName))

    ws.getIPNameForCellName = getIPNameForCellNameProxy
    
    def getCellNamesForIPNameProxy(ipName, quiet=False):
        _ = quiet
        cellNames = _cellNamesDict.get(ipName)
        if cellNames is None:
            raise dmError("There is no IP named '{}' in the workspace".format(ipName))
        return cellNames

    ws.getCellNamesForIPName = getCellNamesForIPNameProxy
    
    def getCellsInListProxy(ipName, listName, cellName=None,
                            isIPNameDefault=False, quiet=True):
        if cellName is None:
            cellName = ipName
        cellNames = None
        if listName == 'cell_names':
            cellNames = getCellNamesForIPNameProxy(ipName, quiet)
        elif listName == 'molecules':
            cellNames = moleculesDict.get(cellName)
        elif listName == 'elements':
            cellNames = elementsDict.get(cellName)
        else:
            raise dmError("In deliverable 'IPSPEC', there is no pattern named '{}'.".format(listName))

        if cellNames is None:
            if isIPNameDefault:
                cellNames = set([ipName])
            elif cellName == ipName:
                # Even if not in elementsDict or moleculesDict,
                # ipName is always a legal cell name
                cellNames = set([])
            else:
                raise dmError("The specified cell '{}' is invalid because it is not "
                              "a cell in IP '{}'.".format(cellName, ipName))
        return cellNames
              
    ws.getCellsInList = getCellsInListProxy
    
    # Class methods
    ws.getAbsPathOrCwd = ICManageWorkspace.getAbsPathOrCwd
    ws.getLibType = ICManageWorkspace.getLibType
    ws.getDeliverableName = ICManageWorkspace.getDeliverableName
    # ICManageWorkspace.getConfigurationsFromICManage() is a class method, but
    # it cannot be used as-is because it touches IC Manage.
    
    # getCellNamesForIPNameAndPath() will look for the cell_names.txt file, so it's not so great
    ws.getCellNamesForIPNameAndPath = ICManageWorkspace.getCellNamesForIPNameAndPath
    
    def findWorkspaceProxy(path=None):
        return ICManageWorkspace.getAbsPathOrCwd(path)
    ws.findWorkspace = findWorkspaceProxy
    
    def isWorkspaceProxy(path):
        try:
            ICManageWorkspace.getAbsPathOrCwd(path)
        except dmError:
            return False
        return True
    ws.isWorkspace = isWorkspaceProxy

    return ws
