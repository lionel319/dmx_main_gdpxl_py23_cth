#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/filebase.py#1 $

"""
FileBase is an abstract base class for deliverable items that are
simple files.  See :py:class:`dmx.dmlib.templateset.pattern` and
:py:class:`dmx.dmlib.templateset.filelist` for concrete classes.

The `toxml()` method returns the XML representation of the instance,
which is the main purpose of the class.  For example,

>>> # FileBaseForTesting is a mock concrete class
>>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=0, versioned=False)
>>> p.toxml()
'<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="0" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'

Class Methods and Attributes
===============================
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from abc import ABCMeta  # , abstractmethod
from xml.etree.ElementTree import Element, SubElement, tostring #@UnusedImport

from dmx.dmlib.templateset.xmlbase import XmlBase #@UnusedImport
from dmx.dmlib.templateset.itembase import ItemBase
from dmx.dmlib.dmError import dmError #@UnusedImport


class FileBase(ItemBase):
    '''Construct the abstract base class for template items that describe files,
    like `&lt;pattern&gt;` and `&lt;filelist&gt;`.
    
    The following XML attributes are included:

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
    
    >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=0, versioned=False)
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="0" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'
    '''

    __metaclass__ = ABCMeta
 
    _versionedDefault = True
    _idDefault = ''
    
    def __init__(self, text, idd, minimum, versioned):
        # mimetypes is initialized in ItemBase.  guess_type() returns a tuple
        mimetype = self.getMimetype(text)
        assert mimetype, \
            "The MIME type for '{}' must be defined.  If it's not, add it in " \
            "class dmx.dmlib.templateset.itembase.ItemBase".format(text)
        super(FileBase, self).__init__(idd, mimetype, minimum, versioned)
        self._text = text

    def element(self, parent=None):
        '''Create an element and initialize the attributes common to all deliverable
        template items.  For use in :py:func:`dmx.dmlib.templateset.pattern.element()`,
        :py:func:`dmx.dmlib.templateset.filelist.element()` and so on.

        If a parent Element is specified, make the ElementTree a SubElement of
        the parent:
        
        >>> p = FileBaseForTesting('xxx/yyy/file.txt', 'file')
        >>> parent = Element("parent")
        >>> child = p.element(parent)
        >>> tostring(parent)
        '<parent><item id="file">xxx/yyy/file.txt</item></parent>'
        
        If no parent is specified, the element returned is the root element:
        
        >>> p = FileBaseForTesting('aaa/bbb.txt', 'file')
        >>> tostring(p.element())
        '<item id="file">aaa/bbb.txt</item>'
        
        When non-default attributes are specified, they appear in the created Element:

        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file')
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file">&ip_name;/&layoutDirName;/file.txt</item>'
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=0)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="0">&ip_name;/&layoutDirName;/file.txt</item>'
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=0, versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="0" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=0, versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="0" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=0, versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="0" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=5, versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" minimum="5" versioned="no">&ip_name;/&layoutDirName;/file.txt</item>'
        
        The MIME type is automatically determined based on the file name and the
        mimetypes module initialization in :py:class:`dmx.dmlib.templateset.itembase`.  The MIME type
        for `.txt` files is the default:
        
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.txt', 'file', minimum=1, versioned=True)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file">&ip_name;/&layoutDirName;/file.txt</item>'
        
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.xml', 'file', minimum=1, versioned=True)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" mimetype="text/xml">&ip_name;/&layoutDirName;/file.xml</item>'
        
        >>> p = FileBaseForTesting('&&ip_name;/&&layoutDirName;/file.db', 'file', minimum=1, versioned=True)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="file" mimetype="application/octet-stream">&ip_name;/&layoutDirName;/file.db</item>'
        '''
        
        e = super(FileBase, self).element(parent)
        assert self._text, 'Every file item has content'
        e.text = self._text
        return e

    def report(self, ipName, cellName):
        '''Return a human readable string representation.
        
        'Item: ip1/vcs/file.txt'
        >>> p = FileBaseForTesting('&&ip_name;/vcs/file.txt', 'textFile')
        >>> p.report('ip1', 'ip1')      #doctest: +NORMALIZE_WHITESPACE
        'Item: ip1/vcs/file.txt    Logical Name: textFile'
        '''
        assert self._text, 'Every pattern has content'
        strr = self._substituteEntityRefs(self._text, ipName, cellName)
        return '{}: {}    Logical Name: {}'.format(self.reportName, strr, self._id)

# TODO: How to elide this except when __name__ == "__main__" or when
# FileBase_test.py is being run?
class FileBaseForTesting(FileBase):
    '''Fake derived class just for testing.  This simulates something like
    :py:class:`dmx.dmlib.templateset.pattern` or :py:class:`dmx.dmlib.templateset.filelist`.
    '''
    def __init__(self, text, idd,
                 minimum=FileBase.minimumDefault,
                 versioned=FileBase._versionedDefault):
        super(FileBaseForTesting, self).__init__(text, idd, minimum, versioned)
    
    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'item'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Item'
    

if __name__ == "__main__":
    # Running FileBase_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
