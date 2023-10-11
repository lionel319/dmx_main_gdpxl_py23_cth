#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/dbbase.py#1 $

"""
DbBase is a base class for design database deliverables.
It describes either an entire library, library and cell, or
library/cell/view triplet.  See :py:class:`dmx.dmlib.templateset.milkyway`, and
:py:class:`dmx.dmlib.templateset.openaccess` for concrete classes.

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> # DeliverableDbForTesting is a mock concrete class
>>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName')
>>> p.toxml()
'<?xml version="1.0" encoding="utf-8"?><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db>'

XML Elements
=============
The main purpose of this class is to produce XML using the `toxml()` method.
The main element in defined in the derived classes, not this abstract base class.

The main element has only the attributes defined in its base classes.

The <lib> Element
-------------------------
The text of this element is the library name.  It has no attributes.

The <cell> Element
-------------------------
The text of this element is the cell name.  It has no attributes.

The <view> Element
-------------------------
The text of this element is the view name.  It has no attributes.

Class Methods and Attributes
===============================
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from abc import ABCMeta  # , abstractmethod
from xml.etree.ElementTree import Element, SubElement, tostring
from dmx.dmlib.templateset.itembase import ItemBase
from dmx.dmlib.dmError import dmError


class DbBase(ItemBase):
    '''Construct a `&lt;_openaccess&gt;` deliverable item element.  The following
    attributes can be added:

    * `id`, the logical name for this _openaccess.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
    * `mimetype`, the `MIME internet media type <http://en.wikipedia.org/wiki/Internet_media_type>`_.  This is hardcoded to `application/octet-stream`, which indicates a binary file.
    * `minimum`, The minimum number of files that must be present. If this is zero, the file is optional.  The default is 1.
    * `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.

    >>> p = DeliverableDbForTesting('path/to/libName', 'libName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName', 'layout')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="layout">viewName</view></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', None, 'viewName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><view>viewName</view></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells')

    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="hierCells" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells',
    ...     minimum=0)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="hierCells" mimetype="application/octet-stream" minimum="0"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db>'
    >>>
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells',
    ...     minimum=0,
    ...     versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><db id="hierCells" mimetype="application/octet-stream" minimum="0" versioned="no"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db>'
    >>>
    
    It is an error to specify an undefined view type:
    
    >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName', 'nonexistent') #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    dmError: ... view type 'nonexistent' is invalid.
    '''
 
    __metaclass__ = ABCMeta
    
    # It would be nice to have @abstractclassvariable for viewTypeNames to force
    # instantiation of viewTypeNames in derived classes, but ABC provides no
    # such thing.  So define it as something non-iterable.
    viewTypeNames = None

    def __init__(self, libPath, libName, cellName, viewName, 
                 viewType, id, minimum, versioned):
        assert self.viewTypeNames is not None, \
                "viewTypeNames must be defined as a set() in the derived class"
        super(DbBase, self).__init__(id, self._mimetypeBinaryDefault, minimum, versioned)
        self._libPath = libPath
        self._libName = libName
        self._cellName = cellName
        self._viewName = viewName
        self._viewType = viewType
        if (viewType is not None) and (viewType not in self.viewTypeNames):
            raise dmError("{} view type '{}' is invalid.".format(self.reportName,
                                                                 viewType))

        assert self._libPath, 'Every database requires at least a library path'

    def element(self, parent=None):
        '''Return an XML :py:class:`xml.etree.ElementTree` representing this instance.
        
        If a parent Element is specified, make the ElementTree a SubElement of
        the parent:
        
        >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName')
        >>> parent = Element("parent")
        >>> child = p.element(parent)
        >>> tostring(parent)
        '<parent><db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db></parent>'
        
        If no parent is specified, the element returned is the root element:
        
        >>> p = DeliverableDbForTesting('path/to/libName', 'libName', 'cellName', 'viewName')
        >>> tostring(p.element())
        '<db id="database" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></db>'
        '''
        e = super(DbBase, self).element(parent)

        assert self._libName, 'Every database requires at least a library name'
        libPath = SubElement(e, 'libpath')
        libPath.text = self._libPath
        lib = SubElement(e, 'lib')
        lib.text = self._libName
        if self._cellName:
            cell = SubElement(e, 'cell')
            cell.text = self._cellName
        if self._viewName:
            view = SubElement(e, 'view')
            view.text = self._viewName
            if self._viewType:
                view.set('viewtype', self._viewType)
        return e

    def report(self, ipName, cellName):
        '''Return a human readable string representation.
        
        >>> f = DeliverableDbForTesting('path/to/libName', '&&ip_name;')
        >>> f.report('ip1', 'ip1')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        'DB library: path/to/libName    Logical name database'
        >>> f = DeliverableDbForTesting('path/to/libName', '&&ip_name;', 'cell')
        >>> f.report('ip1', 'ip1')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        'DB cell: path/to/libName/cell    Logical name database'
        >>> f = DeliverableDbForTesting('path/to/libName', '&&ip_name;', 'cell', 'view')
        >>> f.report('ip1', 'ip1')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        'DB cellView: path/to/libName/cell/view    Logical name database'
        >>> f = DeliverableDbForTesting('path/to/libName', '&&ip_name;', None, 'view')
        >>> f.report('ip1', 'ip1')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        'DB cellView: path/to/libName/*/view    Logical name database'
        '''
        ret = self.reportName
        if self._viewName:
            if self._cellName:
                ret += ' cellView: {}/{}/{}'.format(self._libPath, self._cellName, self._viewName)
            else:
                ret += ' cellView: {}/*/{}'.format(self._libPath, self._viewName)
        elif self._cellName:
            ret += ' cell: {}/{}'.format(self._libPath, self._cellName)
        else:
            ret += ' library: {}'.format(self._libPath)
        ret += "    Logical name {}".format(self._id)
        return self._substituteEntityRefs(ret, ipName, cellName)
        
# TODO: How to elide this except when __name__ == "__main__" or when
# DbBase_test.py is being run?
class DeliverableDbForTesting(DbBase):
    '''Mock derived class just for testing.  This simulates something like
    :py:class:`dmx.dmlib.templateset.openaccess` or :py:class:`dmx.dmlib.templateset.milkyway`.
    '''
    
    viewTypeNames = set(['layout', 'schematic'])
    
    def __init__(self, libPath, libName, cellName=None, viewName=None,
                 viewType = None,
                 id_='database',
                 minimum=1,
                 versioned=ItemBase._versionedDefault):
        super(DeliverableDbForTesting, self).__init__(libPath, libName, cellName, viewName,
                                   viewType, id_, minimum, versioned)
    
    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'db'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'DB'
    
    
if __name__ == "__main__":
    # Running DbBase_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
