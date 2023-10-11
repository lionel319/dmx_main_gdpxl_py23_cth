#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/xmlbase.py#1 $

"""
This abstract base class provides an XML interface for the
:py:module:`dmx.dmlib.templateset` module classes.
"""

from abc import ABCMeta, abstractmethod, abstractproperty
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

import re
import logging

class XmlBase(object):
    """Provide XML methods for the :py:module:`dmx.dmlib.templateset` module classes."""
    __metaclass__ = ABCMeta

    _ipName = '&&ip_name;'
    _cellName = '&&cell_name;'
    _deliverableName = '&&deliverable_name;'
    
     
    @abstractproperty
    def tagName(self):
        '''The tag name for this XML element.

        This is an abstract property that all subclasses must implement.
        '''
        pass
    
    @abstractproperty
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.

        This is an abstract property that all subclasses must implement.
        '''
        pass
        
    @abstractmethod
    def report(self, ipName, cellName): # UnusedArg pylint: disable = W0613
        '''Return a human-readable string describing this element.

        This is an abstract method that all subclasses must implement.
        '''
        return ''
     
    @abstractmethod
    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.

        This is an abstract method that all subclasses must implement.
        '''
        if parent is None:
            return Element(self.tagName)
        return SubElement(parent, self.tagName)
     
    def toxml(self, fmt=None):
        '''Return the XML string representation.  Several formats are available:

        * `None`.  All XML on one line.
        * `'doctest'`.  Everything separated by spaces to be compatible with doctest.
        * `'pretty'`.  Pretty printed with indentation.
        '''
        withEscapedEntities =  '<?xml version="1.0" encoding="utf-8"?>' + tostring(self.element(), 'utf-8')
        if fmt is None:
            pass
        elif fmt == 'doctest':
            reparsed = minidom.parseString(withEscapedEntities)
            withEscapedEntities = reparsed.toprettyxml(indent='', newl=' ', encoding='utf-8')
            # _xmlplus adds a \n after  <?xml version="1.0" encoding="utf-8"?>
            # and doctest does not like it.  If this happens, change it to a space.
            withEscapedEntities = withEscapedEntities.replace('<?xml version="1.0" encoding="utf-8"?>\n',
                                                              '<?xml version="1.0" encoding="utf-8"?> ', 1)
        elif fmt == 'pretty':
            reparsed = minidom.parseString(withEscapedEntities)
            withEscapedEntities = reparsed.toprettyxml(indent='  ', encoding='utf-8')
        else:
            assert False, "Legal values of fmt are None, 'doctest', or 'pretty'."
        return self._unescapeAmp(withEscapedEntities)
            
    def write(self, fileName, fmt=None):
        '''Write the XML representation of this instance to the specified file,
        in the specified fmt.  The choices of fmt are the same as `toxml()`.
        '''
        f = open(fileName, 'w')
        f.write(self.toxml(fmt))
        f.close()
    
    @classmethod
    def getNames(cls):
        '''Return a sorted list of all deliverables defined in class
        :py:class:`dmx.dmlib.templateset.template` or :py:class:`dmx.dmlib.templateset.successor`.
        
        *This is only for use within the py:module:`dmx.dmlib.templateset` module.*
        Client programmers should use :py:class:`dmx.dmlib.Manifest` property
        `allDeliverables`.
        
        TO_DO: Strictly speaking, this method should be in a separate abstract
        base class and inherited by :py:class:`dmx.dmlib.templateset.template` and
        :py:class:`dmx.dmlib.templateset.successor` only.
        
        >>> from dmx.dmlib.templateset.template import Template
        >>> deliverableNames = Template.getNames()
        >>> 'RTL' in deliverableNames
        True
        >>> 'EMPTY' in deliverableNames
        False
        >>> 'NONEXISTENT' in deliverableNames
        False
        >>> maybeSorted = list(deliverableNames)
        >>> deliverableNames.sort()
        >>> maybeSorted == deliverableNames
        True
        '''
        isDeliverableMethodName = re.compile(r'^_[A-Z][A-Z0-9_]*$')
        deliverableMethods = filter(isDeliverableMethodName.search, dir(cls)) #pylint: disable = W0141
        if '_EMPTY' in deliverableMethods:
            deliverableMethods.remove('_EMPTY')
        if '_EMPTYALIAS' in deliverableMethods:
            deliverableMethods.remove('_EMPTYALIAS')
        deliverableNames = [methodName.lstrip('_') for methodName in deliverableMethods]
        deliverableNames.sort()
        return deliverableNames
        
    @classmethod               
    def _boolToStr(cls, b):
        '''Convert a boolean value to the string to be used in XML.

        >>> XmlBase._boolToStr(True)
        'yes'
        >>> XmlBase._boolToStr(False)
        'no'
        '''
        if b:
            return 'yes'
        return 'no'

    @classmethod               
    def _unescapeAmp(cls, s):
        '''Convert '&amp;&amp;entityName;' to &entityName; so that it becomes a
        real XML entity.
        '''
        return s.replace('&amp;&amp;', '&')


# TO_DO: How to elide this except when __name__ == "__main__" or when
# DbBase_test.py is being run?
class DeliverableSubClass(XmlBase):
    '''Fake derived class just for testing.'''
    def __init__(self, text): # pylint: disable = W0231
        self._text = text # this is base class field
    
    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'templateset'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'template set'
    
    def element(self, parent=None):
        top = Element('top')
        element = SubElement(top, 'element')
        element.text = self._text
        return top

    def report(self, ipName, cellName):
        logging.info ("XML element for IP '{}', cell name '{}'.".format(ipName, cellName))


if __name__ == "__main__":
    assert False, "Cannot instantiate abstract base class alone.  Run XmlBase_test.py."
