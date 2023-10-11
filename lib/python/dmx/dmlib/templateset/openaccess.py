#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/openaccess.py#1 $

"""
OpenAccess describes an OpenAccess cellView, cell or library.
It stores the XML element `<openaccess>`.

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> p = OpenAccess('&&ip_name;/oa/&&ip_name;', '&&ip_name;', '&&ip_name;', 'layout', 'oacMaskLayout')
>>> p.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
'<?xml version="1.0" encoding="utf-8"?>
  <openaccess id="oa" mimetype="application/octet-stream">
    <libpath>
      &ip_name;/oa/&ip_name;
    </libpath>
    <lib>
      &ip_name;
    </lib>
    <cell>
      &ip_name;
    </cell>
    <view viewtype="oacMaskLayout">
      layout
    </view>
  </openaccess> '

This describes a file path whose actual name is calculated by substituting:

* `&ip_name;` with the name of the IP
* `&layoutDirName;` with the name of the working directory in which layout is being performed

`<openaccess>` is contained within a deliverable template `<template>` element.
See the :py:class:`dmx.dmlib.templateset.template` class for a description of the `<template>` element.

The <openaccess> Element
==========================
The `<openaccess>` element contains the attributes and the sub-elements defined
in the base classes of this class.  The following attributes can be added:

* `id`, the logical name for this Milkyway database.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
* `minimum`, The minimum number of files that must be present. If this is zero, the file is optional.  The default is 1.
* `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.
"""

#from dmx.dmlib.dmError import dmError
from xml.etree.ElementTree import Element, tostring #@UnusedImport pylint: disable=W0611
from dmx.dmlib.templateset.itembase import ItemBase
from dmx.dmlib.templateset.dbbase import DbBase

class OpenAccess(DbBase):
    '''Construct a `&lt;_openaccess&gt;` deliverable item element.  The following
    attributes can be added:

    * `id`, the logical name for this _openaccess.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
    * `mimetype`, the `MIME internet media type <http://en.wikipedia.org/wiki/Internet_media_type>`_.  This is hardcoded to `application/octet-stream`, which indicates a binary file.
    * `minimum`, the minimum number of files that must exist.  Thus "0" means that the pattern is optional in the deliverable. "1" is the default. 
    * `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.

    Further, the following attribute can be added to the `<view viewtype="oacMaskLayout">` element:
    * `viewtype`, the OpenAccess view type

    >>> # Using a library path and name that are different is for
    >>> # flow designers who want to confuse their users.  Don't
    >>> # do it, except in unit tests.
    >>> p = OpenAccess('path/to/unLibName', 'libName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="oa" mimetype="application/octet-stream"><libpath>path/to/unLibName</libpath><lib>libName</lib></openaccess>'
    >>>
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="oa" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell></openaccess>'
    >>>
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="oa" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="oacMaskLayout">viewName</view></openaccess>'
    >>>
    >>> p = OpenAccess('path/to/libName', 'libName', None, 'viewName')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="oa" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><view viewtype="oacMaskLayout">viewName</view></openaccess>'
    >>>
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells')

    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="hierCells" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="oacMaskLayout">viewName</view></openaccess>'
    >>>
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells',
    ...     minimum=0)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="hierCells" mimetype="application/octet-stream" minimum="0"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="oacMaskLayout">viewName</view></openaccess>'
    >>>
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName', 'viewName',
    ...     id_='hierCells',
    ...     minimum=0,
    ...     versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><openaccess id="hierCells" mimetype="application/octet-stream" minimum="0" versioned="no"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="oacMaskLayout">viewName</view></openaccess>'
    >>>
    
    `element()` returns an XML element tree:
    
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> parent = Element("parent")
    >>> child = p.element(parent)
    >>> tostring(parent)
    '<parent><openaccess id="oa" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="oacMaskLayout">viewName</view></openaccess></parent>'
    
    If no parent is specified, the element returned is the root element:
    
    >>> p = OpenAccess('path/to/libName', 'libName', 'cellName', 'viewName')
    >>> tostring(p.element())
    '<openaccess id="oa" mimetype="application/octet-stream"><libpath>path/to/libName</libpath><lib>libName</lib><cell>cellName</cell><view viewtype="oacMaskLayout">viewName</view></openaccess>'

    `report()` provides a human-readable report:
            
    >>> f = OpenAccess('path/to/lib', 'lib', 'cell', 'view')
    >>> f.report('testip1', 'testip1')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'OpenAccess cellView: path/to/lib/cell/view    Logical name oa'
    '''

    openAccessDataFileName = {
        'oacMaskLayout':'layout.oa',
        'oacSchematic':'sch.oa',
        'oacSchematicSymbol':'symbol.oa',
        'oacNetlist':'netlist.oa',
        'oacHierDesign':'hierDesign.oa',
        'oacWafer':'wafer.oa',
        'oacVerilogAMSText':'verilog.vams',
        'oacVHDLAMSText':'vhdl.vhms',
        'oacVerilogText':'verilog.v',
        'oacVHDLText':'vhdl.vhd',
        'oacVerilogAText':'verilog.va',
        'oacSystemVerilogText':'verilog.sv',
        'oacSPECTREText':'spectre.scs',
        'oacSPICEText':'spice.spc',
        'oacHSPICEText':'hspice.hsp',
        'oacCDLText':'netlist.cdl',
    }
    viewTypeNames = set(openAccessDataFileName.keys()) 
    defaultId = 'oa'
    def __init__(self, libPath, libName, cellName=None, viewName=None,
                 viewType='oacMaskLayout',
                 id_=None,
                 minimum=ItemBase.minimumDefault,
                 versioned=ItemBase._versionedDefault): # pylint: disable=W0212
        if id_ is None:
            id_ = self.defaultId
        super(OpenAccess, self).__init__(libPath, libName, cellName, viewName, viewType,
                                   id_, minimum, versioned)

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'openaccess'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'OpenAccess'
    
        
if __name__ == "__main__":
    # Running OpenAccess_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
