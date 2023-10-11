#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/totem.py#1 $

"""
Totem describes an Apache Totem cell or library.
It stores the XML element `<totem>`.

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> p = Totem('&&ip_name;/irem/&&ip_name;', '&&ip_name;', '&&ip_name;', 'layout')
>>> p.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
'<?xml version="1.0" encoding="utf-8"?>
  <totem id="totem" mimetype="application/octet-stream">
    <libpath>
      &ip_name;/irem/&ip_name;
    </libpath>
    <lib>
      &ip_name;
    </lib>
    <cell>
      &ip_name;
    </cell>
    <view>
      layout
    </view>
  </totem> '

This describes a file path whose actual name is calculated by substituting:

* `&ip_name;` with the name of the IP
* `&layoutDirName;` with the name of the working directory in which layout is being performed

`<totem>` is contained within a deliverable template `<template>` element.
See the :py:class:`dmx.dmlib.templateset.template` class for a description of the `<template>` element.

The <totem> Element
==========================
The `<totem>` element contains the attributes and the sub-elements defined
in the base classes of this class.  The following attributes can be added:

* `id`, the logical name for this Milkyway database.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
* `minimum`, The minimum number of files that must be present. If this is zero, the file is optional.  The default is 1.
* `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from xml.etree.ElementTree import Element, tostring
from dmx.dmlib.templateset.itembase import ItemBase
from dmx.dmlib.templateset.dbbase import DbBase

class Totem(DbBase):
    '''Construct a `&lt;_totem&gt;` deliverable item element.  The following
    attributes can be added:

    * `id`, the logical name for this _totem.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
    * `mimetype`, the `MIME internet media type <http://en.wikipedia.org/wiki/Internet_media_type>`_.  This is hardcoded to `application/octet-stream`, which indicates a binary file.
    * `minimum`, the minimum number of files that must exist.  Thus "0" means that the pattern is optional in the deliverable. "1" is the default. 
    * `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.

    Further, the following attribute can be added to the `<view>` element:
    * `viewtype`, the Totem view type

    >>> # Using a library path and name that are different is for
    >>> # flow designers who want to confuse their users.  Don't
    >>> # do it, except in unit tests.
    >>> p = Totem('path/to/unLibName', 'libName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="totem" mimetype="application/octet-stream"><libpath>path/to/unLibName</libpath><lib>libName</lib></totem>'
    >>>
    >>> p = Totem('path/to/libName', 'libName', 'cellName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="totem" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell></totem>'
    >>>
    >>> p = Totem('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="totem" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></totem>'
    >>>
    >>> p = Totem('path/to/libName', 'libName', None, 'viewName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="totem" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><view>viewName</view></totem>'
    >>>
    >>> p = Totem('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells')

    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="hierCells" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></totem>'
    >>>
    >>> p = Totem('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells',
    ...     minimum=0)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="hierCells" mimetype="application/octet-stream" minimum="0"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></totem>'
    >>>
    >>> p = Totem('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells',
    ...     minimum=0,
    ...     versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><totem id="hierCells" mimetype="application/octet-stream" minimum="0" versioned="no"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></totem>'
    >>>
    
    `element()` returns an XML element tree:
    
    >>> p = Totem('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> parent = Element("parent")
    >>> child = p.element(parent)
    >>> tostring(parent)
    '<parent><totem id="totem" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></totem></parent>'
    
    If no parent is specified, the element returned is the root element:
    
    >>> p = Totem('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> tostring(p.element())
    '<totem id="totem" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view>viewName</view></totem>'

    `report()` provides a human-readable report:
            
    >>> f = Totem('path/to/lib', 'lib', 'cell', 'view')
    >>> f.report('testip1', 'testip1')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'Totem cellView: path/to/lib/cell/view    Logical name totem'
    '''
    # Currently, no view types for Totem are known
    viewTypeNames = set()
    
    defaultId = 'totem'
    
    def __init__(self, libPath, libName, cellName=None, viewName=None,
                 # viewType=None,
                 id_=None,
                 minimum=ItemBase.minimumDefault,
                 versioned=ItemBase._versionedDefault):
        if id_ is None:
            id_ = self.defaultId
        super(Totem, self).__init__(libPath, libName, cellName, viewName, None, # viewType,
                                   id_, minimum, versioned)

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'totem'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Totem'
    
        
if __name__ == "__main__":
    # Running Totem_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
