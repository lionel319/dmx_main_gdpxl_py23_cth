#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/pattern.py#1 $

"""
`Pattern` describes one file name pattern for a deliverable.
It stores the XML element `<pattern>`.

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> p = Pattern('&&ip_name;/&&layoutDirName;/file.txt', 'file')
>>> p.toxml()
'<?xml version="1.0" encoding="utf-8"?><pattern id="file">&ip_name;/&layoutDirName;/file.txt</pattern>'

This describes a file path whose actual name is calculated by substituting the
XML entity references:

* `&ip_name;` with the name of the IP
* `&layoutDirName;` with the name of the working directory in which layout is being performed

`<pattern>` is contained within a deliverable template `<template>` element.
See the :py:class:`dmx.dmlib.templateset.template` class for a description of the `<template>` element.

The <pattern> Element
=======================
The text of this element is the specification of a file that is part of the deliverable.
The pattern can contain XML entities and **Perforce** wild cards.  Wild cards are strongly
discouraged and require DA management approval.

`<pattern>` has the attributes defined in the base classes of this class. 
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from xml.etree.ElementTree import Element, SubElement, tostring
from dmx.dmlib.templateset.filebase import FileBase


class Pattern(FileBase):
    '''Construct a `<pattern>` deliverable item element.  The following
    attributes can be added:

    * `id`, the logical name for this pattern.  The :py:class:`dmx.dmlib.templateset.Manifest` \
       distinguishes items within deliverables using this name.  The `id` must \
       be unique within each deliverable.
    * `mimetype`, The `MIME internet media type <http://en.wikipedia.org/wiki/Internet_media_type>`_. \
       The MIME type is determined automatically by :py:class:`dmx.dmlib.templateset.filebase`.
    * `minimum`, the minimum number of files that must exist.  Thus "0" means \
       that the pattern is optional in the deliverable. "1" is the default. 
    * `versioned`, whether the files that make up the deliverable are version \
       controlled in Perforce, either `"yes"` or `"no"`.  The default is "yes". \
       See also the :py:class:`dmx.dmlib.templateset.template` `<template controlled>` attribute.

    >>> p = Pattern('&&ip_name;/&&layoutDirName;/file.txt')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><pattern id="file">&ip_name;/&layoutDirName;/file.txt</pattern>'
    >>>
    >>> p = Pattern('&&ip_name;/&&layoutDirName;/file.txt', 'topBcm')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><pattern id="topBcm">&ip_name;/&layoutDirName;/file.txt</pattern>'
    >>>
    >>> p = Pattern('&&ip_name;/&&layoutDirName;/file.txt', 'topBcm',
    ...     minimum=3)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><pattern id="topBcm" minimum="3">&ip_name;/&layoutDirName;/file.txt</pattern>'
    >>>
    >>> p = Pattern('&&ip_name;/&&layoutDirName;/file.txt', 'topBcm',
    ...     minimum=3)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><pattern id="topBcm" minimum="3">&ip_name;/&layoutDirName;/file.txt</pattern>'
    >>>
    >>> p = Pattern('&&ip_name;/&&layoutDirName;/file.txt', 'topBcm',
    ...     minimum=3,
    ...     versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><pattern id="topBcm" minimum="3" versioned="no">&ip_name;/&layoutDirName;/file.txt</pattern>'

    The MIME type is determined automatically.  For example, here is a pattern
    for an XML file:
    
    >>> p = Pattern('&&ip_name;/&&layoutDirName;/file.xml', 'file')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><pattern id="file" mimetype="text/xml">&ip_name;/&layoutDirName;/file.xml</pattern>'
    
    
    `report()` is inherited from the base class:
    
    >>> p = Pattern('&&ip_name;/vcs/file.txt', 'textFile')
    >>> p.report('ip1', 'ip1')      #doctest: +NORMALIZE_WHITESPACE
    'Path: ip1/vcs/file.txt    Logical Name: textFile'
    
    `element()` is inherited from the base class:
    
    >>> p = Pattern('xxx/yyy.txt', 'file')
    >>> parent = Element("parent")
    >>> child = p.element(parent)
    >>> tostring(parent)
    '<parent><pattern id="file">xxx/yyy.txt</pattern></parent>'
    
    If no parent is specified, the element returned is the root element:
    
    >>> p = Pattern('aaa/bbb.txt', 'file')
    >>> tostring(p.element())
    '<pattern id="file">aaa/bbb.txt</pattern>'
    
    The default of the `id` attribute is:
    
    >>> Pattern.defaultId
    'file'
    '''
    
    defaultId = 'file'
    
    def __init__(self, pattern, id_=None,
                 minimum=FileBase.minimumDefault,
                 versioned=FileBase._versionedDefault):
        if id_ is None:
            id_ = self.defaultId
        super(Pattern, self).__init__(pattern, id_, minimum, versioned)
        self._pattern = pattern

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'pattern'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Path'
    
    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.
        `element()` is inherited from the base class:
         
        If a parent Element is specified, make the ElementTree a SubElement of
        the parent:

        >>> p = Pattern('&&ip_name;/vcs/file.txt', 'textFile')
        >>> p.report('ip1', 'ip1')      #doctest: +NORMALIZE_WHITESPACE
        'Path: ip1/vcs/file.txt    Logical Name: textFile'
        
        `element()` is inherited from the base class:
         
        >>> p = Pattern('xxx/yyy.txt', 'file')
        >>> parent = Element("parent")
        >>> tostring(p.element())
        '<pattern id="file">xxx/yyy.txt</pattern>'
        '''
        e = super(Pattern, self).element(parent)
        return e
        
if __name__ == "__main__":
    # Running Pattern_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()

