#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/milkyway.py#1 $

"""
Milkyway describes an Milkyway cellView, cell or library.
It stores the XML element `<milkyway>`.

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> p = Milkyway('&&ip_name;/&&layoutDirName;/&&ip_name;', id_='mwLib')
>>> p.toxml()
'<?xml version="1.0" encoding="utf-8"?><milkyway id="mwLib" mimetype="application/octet-stream"><libpath>&ip_name;/&layoutDirName;/&ip_name;</libpath><lib>&ip_name;</lib></milkyway>'

This describes a file path whose actual name is calculated by substituting:

* `&ip_name;` with the name of the IP
* `&layoutDirName;` with the name of the working directory in which layout is being performed

`<milkyway>` is contained within a deliverable template `<template>` element.
See the :py:class:`dmx.dmlib.templateset.template` class for a description of the `<template>` element.

The <milkyway> Element
========================
The `<milkyway>` element contains only the attributes and the sub-elements defined
in the base classes of this class.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from os.path import basename
from xml.etree.ElementTree import Element, tostring # @UnusedImport
from dmx.dmlib.templateset.itembase import ItemBase
from dmx.dmlib.templateset.dbbase import DbBase


class Milkyway(DbBase):
    '''Construct a `<milkyway>` deliverable item element.  The following
    attributes can be added:

    * `id_`, the logical name for this Milkyway database.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
    * `minimum`, The minimum number of files that must be present. If this is zero, the file is optional.  The default is 1.
    * `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.

    >>> p = Milkyway('path/to/libName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><milkyway id="mwLib" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway>'
    >>>
    >>> p = Milkyway('path/to/libName', id_='mwRefLib')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><milkyway id="mwRefLib" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway>'
    >>>
    >>> p = Milkyway('path/to/libName', id_='mwRefLib')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><milkyway id="mwRefLib" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway>'
    >>>
    >>> p = Milkyway('path/to/libName', id_='mwRefLib',
    ...     minimum=0)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><milkyway id="mwRefLib" mimetype="application/octet-stream" minimum="0"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway>'
    >>>
    >>> p = Milkyway('path/to/libName', id_='mwRefLib',
    ...     minimum=0,
    ...     versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><milkyway id="mwRefLib" mimetype="application/octet-stream" minimum="0" versioned="no"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway>'
     
    `element()` returns an XML element tree:
    
    >>> p = Milkyway('path/to/libName', id_='mwRefLib')
    >>> parent = Element("parent")
    >>> child = p.element(parent)
    >>> tostring(parent)
    '<parent><milkyway id="mwRefLib" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway></parent>'
    
    If no parent is specified, the element returned is the root element:
    
    >>> p = Milkyway('path/to/libName', id_='mwRefLib')
    >>> tostring(p.element())
    '<milkyway id="mwRefLib" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib></milkyway>'
    '''
    defaultId = 'mwLib'
    viewTypeNames = set(['Layout', 'Netlist', 'Schematic', 'Symbolic', 'LogicModel', 'Unknown'])
    
    def __init__(self, libPath, cellName=None, viewName=None,
                 viewType=None,
                 id_=None,
                 minimum=ItemBase.minimumDefault,
                 versioned=ItemBase._versionedDefault):
        libName = basename(libPath)
        if id_ is None:
            id_ = self.defaultId
        DbBase.__init__(self, libPath, libName,
                                   cellName,
                                   viewName,
                                   viewType,
                                   id_, minimum, versioned)

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'milkyway'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Milkyway'
    
        
if __name__ == "__main__":
    # Running Milkyway_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
