#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/consumer.py#1 $

"""
Consumer instantiates an object specifying the team that consumes a given
deliverable.  It stores the XML element `<consumer>`.  The class
:py:class:`dmx.dmlib.templateset.template` instantiates `<consumer>` elements within
`<template>` elements.

`<consumer>` contains no sub-elements.

The <consumer> Element
=========================
This element has the following attributes:

* `id`, the name of this consumer
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from xml.etree.ElementTree import Element, SubElement
from xml.etree.ElementTree import tostring # @UnusedImport pylint: disable=W0611

from dmx.dmlib.templateset.xmlbase import XmlBase

class Consumer(XmlBase):
    '''Construct a deliverable consumer of the specified name.
        
    >>> c = Consumer('LAYOUT')
    >>> c.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    '<?xml version="1.0" encoding="utf-8"?>
      <consumer id="LAYOUT"/> '
    '''
    
    def __init__(self, id_):
        self._id = id_

    @property
    def tagName(self):
        '''The tag name for this XML element.
        
        >>> c = Consumer('LAYOUT')
        >>> c.tagName
        'consumer'
        '''
        return self.__class__.__name__.lower()
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and
        messages.
        
        >>> c = Consumer('LAYOUT')
        >>> c.reportName
        'Consumed by'
        '''
        return 'Consumed by'
    
    @property
    def id_(self):
        '''The name of the consumer of this deliverable.
        
        >>> c = Consumer('LAYOUT')
        >>> c.id_
        'LAYOUT'
        '''
        return self._id
    
    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.
        
        >>> consumer = Consumer('LAYOUT')
        >>> tostring(consumer.element())      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<consumer id="LAYOUT" />'
        
        Declare this instance as a SubElement of a parent:

        >>> consumer = Consumer('LAYOUT')
        >>> parent = Element("parent")
        >>> child = consumer.element(parent)
        >>> tostring(parent)      #doctest: +ELLIPSIS
        '<parent><consumer id="LAYOUT" /></parent>'
        '''
        assert self._id, 'Every consumer has an id'  
        if parent is None:
            consumer = Element(self.tagName)
        else:
            consumer = SubElement(parent, self.tagName)
        consumer.set('id', self._id)
        return consumer

    def report(self, ipName, cellName):
        """Return a human readable string representation.

        >>> c = Consumer('LAYOUT')
        >>> c.report('ip1', 'topCell1')      #doctest: +ELLIPSIS
        'Consumed by LAYOUT'
        """
        assert self._id, 'Every consumer has an id'  
        return '{} {}'.format(self.reportName, self._id)


if __name__ == "__main__":
    # Running Consumer_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
