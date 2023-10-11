#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/filelist.py#1 $

"""
`Filelist` describes one filelist for a deliverable.
It stores the XML element `<filelist>`.

A filelist is a file that contains a list of files that
are included in the deliverable.

Within the filelist file:

* File names are listed one per line.  No wild cards are allowed.
* Relative paths are relative to the directory containing the filelist
* Comments run:
   * From `#` or `//` at the beginning of the line to the end of the line
   * From `#` or `//` surrounded by white space to the end of the line

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> p = Filelist('&&ip_name;/design_intent/file.filelist', 'filelist')
>>> p.toxml()
'<?xml version="1.0" encoding="utf-8"?><filelist id="filelist">&ip_name;/design_intent/file.filelist</filelist>'

This describes a file path whose actual name is calculated by substituting the
XML entity references:

* `&ip_name;` with the name of the IP
* `&layoutDirName;` with the name of the working directory in which layout is being performed

`<filelist>` is contained within a deliverable template `<template>` element.
See the :py:class:`dmx.dmlib.templateset.template` class for a description of the `<template>` element.

The <filelist> Element
========================
The text of this element is the literal name of a single filelist file.
As shown above, the text can contain XML entities, but unlike `<pattern>`,
**no wildcards are allowed**.

`<filelist>` has the attributes defined in the base classes of this class. 
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from xml.etree.ElementTree import Element, SubElement, tostring
from dmx.dmlib.templateset.xmlbase import XmlBase
from dmx.dmlib.templateset.filebase import FileBase


class Filelist(FileBase):
    '''Construct a `&lt;_filelist&gt;` deliverable item element.  The following
    attributes can be added:

    * `id`, the logical name for this _filelist.  The verification platform will refer to this item using this name.  This must be unique within each deliverable.
    * `mimetype`, The `MIME internet media type <http://en.wikipedia.org/wiki/Internet_media_type>`_.  The main distinction is between text, which can be merged, and binary data files, which are presumed unmergable. The default is `text/plain`.  Use `application/octet-stream` for arbitrary binary data.
    * `minimum`, the minimum number of files that must exist.  Thus "0" means that the pattern is optional in the deliverable. "1" is the default. 
    * `versioned`, whether the files that make up the deliverable are version controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes".  See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.

    >>> p = Filelist('&&ip_name;/&&layoutDirName;/&&ip_name;.filelist')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><filelist id="filelist">&ip_name;/&layoutDirName;/&ip_name;.filelist</filelist>'
    >>>
    >>> p = Filelist('&&ip_name;/&&layoutDirName;/&&ip_name;.filelist', 'topBcm')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><filelist id="topBcm">&ip_name;/&layoutDirName;/&ip_name;.filelist</filelist>'
    >>>
    >>> p = Filelist('&&ip_name;/&&layoutDirName;/&&ip_name;.filelist', 'topBcm',
    ...     minimum=0)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><filelist id="topBcm" minimum="0">&ip_name;/&layoutDirName;/&ip_name;.filelist</filelist>'
    >>>
    >>> p = Filelist('&&ip_name;/&&layoutDirName;/&&ip_name;.filelist', 'topBcm',
    ...     minimum=0,
    ...     versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><filelist id="topBcm" minimum="0" versioned="no">&ip_name;/&layoutDirName;/&ip_name;.filelist</filelist>'
    
    The default of the `id` attribute is:
    
    >>> Filelist.defaultId
    'filelist'
    '''

    defaultId = 'filelist'
    
    def __init__(self, pattern, id_=None,
                 versioned=FileBase._versionedDefault,
                 minimum=FileBase.minimumDefault):
        if id_ is None:
            id_ = self.defaultId
        super(Filelist, self).__init__(pattern, id_, minimum, versioned)

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'filelist'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Filelist'
    
        
if __name__ == "__main__":
    # Running Filelist_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
