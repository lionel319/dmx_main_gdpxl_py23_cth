#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/itembase.py#1 $

"""
This is an abstract base class for :py:class:`dmx.dmlib.templateset.pattern`,
:py:class:`dmx.dmlib.templateset.filelist`, :py:class:`dmx.dmlib.templateset.openaccess`,
:py:class:`dmx.dmlib.templateset.milkyway` and other items within the deliverable template.
"""

import os
import mimetypes
import logging

from abc import ABCMeta  # , abstractmethod
from xml.etree.ElementTree import Element, tostring # @UnusedImport pylint: disable=W0611
from dmx.dmlib.templateset.xmlbase import XmlBase

class ItemBase(XmlBase):
    '''Construct the abstract base class for template items like `<pattern>`,
    `<filelist>`, `<openaccess>`, `<milkyway>`, and so on.
    
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

    
    >>> # DeliverableItemForTesting is a mock concrete class
    >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', minimum=0, versioned=False, mimetype='application/octet-stream', idd='topBcm')
    >>> p.toxml()
    '<?xml version="1.0" encoding="utf-8"?><item id="topBcm" mimetype="application/octet-stream" minimum="0" versioned="no" />'
    
    '''

    __metaclass__ = ABCMeta
 
    _versionedDefault = True
    minimumDefault = 1

    mimetypes.init()
    _mimetypeBinaryDefault = 'application/octet-stream'
    mimetypes.add_type(_mimetypeBinaryDefault, '.dat')
    mimetypes.add_type(_mimetypeBinaryDefault, '.db')
    mimetypes.add_type(_mimetypeBinaryDefault, '.ldb')
    mimetypes.add_type(_mimetypeBinaryDefault, '.ddc')
    mimetypes.add_type(_mimetypeBinaryDefault, '.dmz')
    mimetypes.add_type(_mimetypeBinaryDefault, '.gds')
    mimetypes.add_type(_mimetypeBinaryDefault, '.gdz')
    mimetypes.add_type(_mimetypeBinaryDefault, '.mcm')
    mimetypes.add_type(_mimetypeBinaryDefault, '.oas')
    mimetypes.add_type(_mimetypeBinaryDefault, '.zdb')
    
    _mimetypeDefault = mimetypes.guess_type('x.txt')[0]
    mimetypes.add_type(_mimetypeDefault, '.cdl')
    mimetypes.add_type(_mimetypeDefault, '.cfg')
    mimetypes.add_type(_mimetypeDefault, '.cir')
    mimetypes.add_type(_mimetypeDefault, '.cmd')
    mimetypes.add_type(_mimetypeDefault, '.def')
    mimetypes.add_type(_mimetypeDefault, '.do')
    mimetypes.add_type(_mimetypeDefault, '.eqv')
    mimetypes.add_type(_mimetypeDefault, '.exp')
    mimetypes.add_type(_mimetypeDefault, '.f')
    mimetypes.add_type(_mimetypeDefault, '.filelist')
    mimetypes.add_type(_mimetypeDefault, '.fsdb')
    mimetypes.add_type(_mimetypeDefault, '.init')
    mimetypes.add_type(_mimetypeDefault, '.lef')
    mimetypes.add_type(_mimetypeDefault, '.lib')
    mimetypes.add_type(_mimetypeDefault, '.log')
    mimetypes.add_type(_mimetypeDefault, '.mt0')
    mimetypes.add_type(_mimetypeDefault, '.rba')
    mimetypes.add_type(_mimetypeDefault, '.rpt')
    mimetypes.add_type(_mimetypeDefault, '.scandef')
    mimetypes.add_type(_mimetypeDefault, '.sdc')
    mimetypes.add_type(_mimetypeDefault, '.sgdc')
    mimetypes.add_type(_mimetypeDefault, '.sdf')
    mimetypes.add_type(_mimetypeDefault, '.sopcinfo')
    mimetypes.add_type(_mimetypeDefault, '.spef')
    mimetypes.add_type(_mimetypeDefault, '.spi')
    mimetypes.add_type(_mimetypeDefault, '.tcl')
    mimetypes.add_type(_mimetypeDefault, '.tr0')
    mimetypes.add_type(_mimetypeDefault, '.upf')
    mimetypes.add_type(_mimetypeDefault, '.v')
    mimetypes.add_type(_mimetypeDefault, '.sv')
    mimetypes.add_type(_mimetypeDefault, '.swl')
    mimetypes.add_type(_mimetypeDefault, '.dim_tbl')
    mimetypes.add_type(_mimetypeDefault, '.pp')
    mimetypes.add_type(_mimetypeDefault, '.prj')
    mimetypes.add_type(_mimetypeDefault, '.perc')
    mimetypes.add_type(_mimetypeDefault, '.vpd')
    mimetypes.add_type(_mimetypeDefault, '.waiver')
    mimetypes.add_type(_mimetypeDefault, '.rep')
    mimetypes.add_type(_mimetypeDefault, '.xe_tf')
    mimetypes.add_type(_mimetypeDefault, '.xe_ud')
    mimetypes.add_type(_mimetypeDefault, '.xe_lm_v')
    mimetypes.add_type(_mimetypeDefault, '.xe_flattened_ud')
    mimetypes.add_type(_mimetypeDefault, '.xe_report')
    mimetypes.add_type(_mimetypeDefault, '.xe_lm_inst_map')
    mimetypes.add_type(_mimetypeDefault, '.xe_lm_net_map')
    mimetypes.add_type(_mimetypeDefault, '.xe_log')
    mimetypes.add_type(_mimetypeDefault, '.html')
    mimetypes.add_type(_mimetypeDefault, '.cdb')
    mimetypes.add_type(_mimetypeDefault, '.list')
    mimetypes.add_type(_mimetypeDefault, '.ipf')
    mimetypes.add_type(_mimetypeDefault, '.timing')
    mimetypes.add_type(_mimetypeDefault, '.spf')
    mimetypes.add_type(_mimetypeDefault, '.report_analysis_coverage')
    mimetypes.add_type(_mimetypeDefault, '.report_aocvm')
    mimetypes.add_type(_mimetypeDefault, '.report_annotated_parasitics')
    mimetypes.add_type(_mimetypeDefault, '.check_timing')
    mimetypes.add_type(_mimetypeDefault, '.ploc')
    mimetypes.add_type(_mimetypeDefault, '.sum')
    mimetypes.add_type(_mimetypeDefault, '.errlog')
    mimetypes.add_type(_mimetypeDefault, '.workset')
    mimetypes.add_type(_mimetypeDefault, '.config')
    mimetypes.add_type(_mimetypeDefault, '.rapidesd_rpt')
    mimetypes.add_type(_mimetypeDefault, '.totem_log')
    mimetypes.add_type(_mimetypeDefault, '.rapidesd_sum')
    mimetypes.add_type(_mimetypeDefault, '.audit_rpt')
    mimetypes.add_type(_mimetypeDefault, '.zip')
    mimetypes.add_type(_mimetypeDefault, '.apccwaiver')

    mimetypes.add_type('application/vnd.ms-excel.sheet.macroEnabled.12', '.xlsm')
    mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')
    mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
    mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
    
    mimetypes.add_type('application/x-yaml', '.yaml')

    mimetypes.add_type('application/gpg', '.gpg')
    mimetypes.add_type('application/json', '.json')
    mimetypes.add_type('text/csv', '.csv')


    def __init__(self, id_, mimetype, minimum, versioned):
        super(ItemBase, self).__init__()
        self._minimum = minimum
        self.versioned = versioned
        self._mimetype = mimetype
        self._id = id_

    def element(self, parent=None):
        '''Create an element and initialize the attributes common to all deliverable
        template items.  For use in :py:func:`dmx.dmlib.templateset.pattern.element()`,
        :py:func:`dmx.dmlib.templateset.filelist.element()` and so on.

        If a parent `Element` is specified, make the `ElementTree` a `SubElement` of
        the parent:
        
        >>> p = DeliverableItemForTesting('xxx/yyy', 'file')
        >>> parent = Element("parent")
        >>> child = p.element(parent)
        >>> tostring(parent)
        '<parent><item id="file" /></parent>'
        
        If no parent is specified, the element returned is the root element:
        
        >>> p = DeliverableItemForTesting('aaa/bbb', 'file')
        >>> tostring(p.element())
        '<item id="file" />'
        
        When non-default attributes are specified, they appear in the created Element:

        >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', "bcm")
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="bcm" />'
        >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', "bcm", minimum=0)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="bcm" minimum="0" />'
        >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', "bcm", versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="bcm" versioned="no" />'
        >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', "bcm", minimum=0, versioned=False)
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="bcm" minimum="0" versioned="no" />'
        >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', "bcm", minimum=0, versioned=False, mimetype='application/octet-stream')
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="bcm" mimetype="application/octet-stream" minimum="0" versioned="no" />'
        >>> p = DeliverableItemForTesting('&&ip_name;/&&layoutDirName;', 'bcm', minimum=0, versioned=False, mimetype='application/octet-stream')
        >>> p.toxml()
        '<?xml version="1.0" encoding="utf-8"?><item id="bcm" mimetype="application/octet-stream" minimum="0" versioned="no" />'
        '''
        elem = super(ItemBase, self).element(parent)
        assert self._id, 'Every deliverable item has a non-empty id'
        elem.set('id', self._id)
        if self._mimetype != self._mimetypeDefault:
            elem.set('mimetype', self._mimetype)
        if self._minimum != self.minimumDefault:
            elem.set('minimum', str(self._minimum))
        if self.versioned != self._versionedDefault:
            elem.set('versioned', self._boolToStr(self.versioned))
        return elem

    @classmethod
    def getMimetype(cls, url):
        '''Get the MIME type for the specified URL or file name using the Python
        standard `mimetypes` module.  The standard types are available:
        
        >>> ItemBase.getMimetype('file.txt')
        'text/plain'
        >>> ItemBase.getMimetype('file.xml')
        'text/xml'
        >>> ItemBase.getMimetype('file.docx')
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        >>> ItemBase.getMimetype('file.xlsx')
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        Plus, at the beginning of :py:class:`dmx.dmlib.templateset.itembase`, additional MIME types
        have been defined for EDA files and databases:
        
        >>> ItemBase.getMimetype('/abs/path/to/file.rpt')
        'text/plain'
        >>> ItemBase.getMimetype('rel/path/to/file.filelist')
        'text/plain'
        >>> ItemBase.getMimetype('file.db')
        'application/octet-stream'
        
        If the MIME type is unknown, return None:
        >>> ItemBase.getMimetype('file.undefined') # Returns None
       
        The default for text files is:
        
        >>> ItemBase._mimetypeDefault
        'text/plain'
        
        and the default for binary files is:
        
        >>> ItemBase._mimetypeBinaryDefault
        'application/octet-stream'
        '''
        baseName = os.path.basename(url)
        if baseName.startswith('...'):
            return cls._mimetypeDefault
        if baseName in ('Makefile', '*',):
            return cls._mimetypeDefault
            
        assert mimetypes.inited, 'mimetypes.init() should have been executed'
        return mimetypes.guess_type(url)[0]
    
    @classmethod
    def _substituteEntityRefs(cls, inputStr, ipName, cellName):
        '''Replace entity refs with the specified values.
        
        >>> s = '&&ip_name; &&cell_name; &&another;'
        >>> DeliverableItemForTesting._substituteEntityRefs(s, 'ip', 'top')
        'ip top &&another;'
        '''
        s = inputStr.replace('&&ip_name;', ipName)
        s = s.replace('&&cell_name;', cellName)
        return s


# TO_DO: How to elide this except when __name__ == "__main__" or when
# ItemBase_test.py is being run?
class DeliverableItemForTesting(ItemBase):
    '''Mock derived class just for testing.
    '''
    def __init__(self, text, idd,
                 mimetype=ItemBase._mimetypeDefault,
                 minimum=ItemBase.minimumDefault,
                 versioned=ItemBase._versionedDefault):
        super(DeliverableItemForTesting, self).__init__(idd, mimetype, minimum, versioned)
        self._text = text
    
    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'item'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Item'
    
    def report(self, ipName, cellName):
        logging.info ("Item for IP '{}', cell name '{}'.".format(ipName, cellName))
        
        
if __name__ == "__main__":
    # Running ItemBase_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
