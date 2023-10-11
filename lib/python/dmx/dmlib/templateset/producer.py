#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/producer.py#1 $

"""
Producer instantiates an object specifying the team that produces the given
deliverable.  It stores the XML element `<producer>`.  The class
:py:class:`dmx.dmlib.templateset.template` instantiates `<producer>` elements within
`<template>` elements.

`<producer>` contains no sub-elements.

The <producer> Element
=========================
This element has the following attributes:

* `id`, the name of this producer
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from xml.etree.ElementTree import Element, SubElement
from xml.etree.ElementTree import tostring # @UnusedImport pylint: disable=W0611

from dmx.dmlib.templateset.xmlbase import XmlBase

class Producer(XmlBase):
    '''Construct a deliverable producer of the specified name.
        
    >>> p = Producer('LAYOUT')
    >>> p.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    '<?xml version="1.0" encoding="utf-8"?>
      <producer id="LAYOUT"/> '
    '''
    
    def __init__(self, id_):
        self._id = id_

    @property
    def tagName(self):
        '''The tag name for this XML element.
        
        >>> p = Producer('LAYOUT')
        >>> p.tagName
        'producer'
        '''
        return self.__class__.__name__.lower()
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and
        messages.
        
        >>> p = Producer('LAYOUT')
        >>> p.reportName
        'Produced by'
        '''
        return 'Produced by'
    
    @property
    def id_(self):
        '''The name of the producer of this deliverable.
        
        >>> p = Producer('LAYOUT')
        >>> p.id_
        'LAYOUT'
        '''
        return self._id
    
    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.
        
        >>> producer = Producer('LAYOUT')
        >>> tostring(producer.element())      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<producer id="LAYOUT" />'
        
        Declare this instance as a SubElement of a parent:

        >>> producer = Producer('LAYOUT')
        >>> parent = Element("parent")
        >>> child = producer.element(parent)
        >>> tostring(parent)      #doctest: +ELLIPSIS
        '<parent><producer id="LAYOUT" /></parent>'
        '''
        assert self._id, 'Every producer has an id'  
        if parent is None:
            producer = Element(self.tagName)
        else:
            producer = SubElement(parent, self.tagName)
        producer.set('id', self._id)
        return producer

    def report(self, ipName, cellName):
        """Return a human readable string representation.

        >>> p = Producer('LAYOUT')
        >>> p.report('ip1', 'topCell1')      #doctest: +ELLIPSIS
        'Produced by LAYOUT'
        """
        assert self._id, 'Every producer has an id'  
        return '{} {}'.format(self.reportName, self._id)


if __name__ == "__main__":
    # Running Producer_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
