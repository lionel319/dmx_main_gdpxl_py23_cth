#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/description.py#1 $

"""
`Description` contains a natural language description of the deliverable.

`Description` stores the XML element `<description>`.
For example,

        >>> t = Description('Result of the frobnication verification.')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <description>
          Result of the frobnication verification.
        </description> '

When this `<description>` element appears in a `<template>` element,
it declares what data the deliverable contains.

The <description> Element
=========================
This element has no attributes.

The natural language description appears as the description of the `<description>`
element.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"


from xml.etree.ElementTree import Element, SubElement, tostring # pylint: disable=W0611 

from dmx.dmlib.templateset.xmlbase import XmlBase

class Description(XmlBase):
    '''Construct a deliverable description containing the specified description.
        
        >>> t = Description('Result of the frobnication verification.')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <description>
          Result of the frobnication verification.
        </description> '
    '''

    def __init__(self, text):
        super(Description, self).__init__()
        self.text = text

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'description'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Description'
    
    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.
        
        >>> t = Description('Description text')
        >>> tostring(t.element())      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<description>Description text</description>'
        
        Declare this instance as a SubElement of a parent:

        >>> t = Description('Description text')
        >>> parent = Element("parent")
        >>> child = t.element(parent)
        >>> tostring(parent)      #doctest: +ELLIPSIS
        '<parent><description>Description text</description></parent>'
        '''
        if parent is None:
            elem = Element(self.tagName)
        else:
            elem = SubElement(parent, self.tagName)
        elem.text = self.text
        return elem

    def report(self):
        '''Return a human readable string representation.
        
        >>> r = Description('/tools/whatever/description')
        >>> r.report()      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        'Renaming program: /tools/whatever/description'
        '''
        assert self.text, 'Every description has content'
        return 'Renaming program: {}'.format(self.text)

if __name__ == "__main__":
    # Running Description_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
