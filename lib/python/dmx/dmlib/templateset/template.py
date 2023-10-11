#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011-2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# Updated SCHMISC based on 10/20 Mun Fook Leong's & CDC changes FB#239617 on 10/22/2014
# Removed *.waiver as option from SCHMISC on 10/29/2014
# Updated SYN, FVSYN, FVPNR, STA and PNR file pattern (from ip_name to cell_name) on 10/30/2014 FB#241747
# add new routine, addMilkywayMutliCells to have cell_name as Milkyway Librray name on 11/31/2014
# Changed SCHMISC file pattern from "*" to cell_name on 11/05/2014 based on document updated on 11/3/2014
# Changed LAYMISC file pattern to audit.laymisc.laymisc_signoff.xml based on updated 11/05/2014
# Added &ip_name;/laymisc/&ip_name.signoff.html for LAYMISC on 11/07/2014
# Added &ip_name;/upf/netlist/*.upf (optional) for UPF on 11/07/2014
# Updated STA on 11/12/2014
# Changed UPF to drop upf/rtl/*.upf and upf/netlist/*.upf from the UPF template set. 11/13/2014
# Added new deliverable RELDOC 11/13/2014
# Chamge cell_name to "*" for SCHMISC FB#247038 11/21/2014
# Added &ip_name;/timemod/*/verilog/*.f as optional for TIMEMOD on 11/21/2014
# Updated consumer of each deliverables
# Updated SCHMISC to sync up the docmuent changed 12/09/2014
# Updated SCHMISC to add two optional files 12/10/2014
# Updated OA based on FB#249228 removed all type check
# updated FVSYN to inser "*", based on FB#252029
# Updated RELDOC to deleted .xml file on 1/8/2015
# Added new deliverable for TRACKPHYS on 1/9/2015
# Updated PNR to add ploc FB#256136
# Updated IPPWRMOD FB#257061; Change from cell_name to *
# Added files required for UPF with different varaints (ASIC and CUSTOM) type at comment section.
# Add tnrwaivers.csv at RELDOC as optional for command line waiver FB#260942
# Added schmisc/rv/*/*.[power_budge.csv and .spi] files
# Updated FB#261681
# Add two file list for RTL, FB#278355 2/11/2015
# Add to report successor and predecessor; FB#278382 Add two new files dm/templateset/successor.py & dm/templateset/successor_test.py 2/11/2015
# Changed PV file type to audit file list 2/12/2015
# Changed ip_name/cdc/*/cell_name.sgdc to ip_name/cdc/*/cell_name*.sgdc; FB#278796 2/13/2015
# Updaed all description to match the current document 3/2/2015
# Changed SCHMISC FB#282278
# Updated STAMOD FB#284857
# Change track_tcl to tcl for trackphys on 3/16/2015 FB#286092
# Updated DV to add <project>.<ip_name>.<icm config>.workset as file pattern 3/16/2015 FB#286090
# Updated Updated consumer/producer maps 3/19/2015
# Updated RTL to add GLN FB#288030
# Updated RV file pattern FB#293399
# Updated TIMEMOD to add &ip_name;/timemod/*/fverilog/*.spef.gz                (optional) FB#294757 4/24/2015
# Updated TIMEMOD to add &ip_name;/timemod/*/fverilogflist/*.f                (optional) FB#295316 4/27/2015
# Updated IPFLOORPLAN FB#297048
# Updated IPSPEC FB#297250 to add user_skip_cells.txt 5/6/2015 recalled.
# Updated schmisc to add rcxt_non_timing_skipcells.txt 5/20 FB#299790
# Updated RCXT file to gizp format FB#302045
# Updated SCHMISC to add cell_type FB#?? 6/2/15
# Updated SCHMISC based on FB#313174 7/26/15
# Updated IPFLOORPLAN make DEF fiels as optional FB#310843
# Updated TIMEMOD to add two file list FB#315036
# Updated RV remove latchup/<>.audit_rpt file FB#314822
# Updated SCHMISC FB 324146
# Updated SYN FB 323634
# ADD PKGDE and PKGEE FB#324460 and 324461
# Updated TIMEMOD FB 329422 add SDC file
# Updated TIMEMOD FB 329955 add OASIS file
# Update STA make files as optional; based on FB#375394
# Updated TIMEMOD FB 332895 add CDL file
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/template.py#1 $

"""
Template is a factory class that instantiates an object
specifying the files that make up a given deliverable.
It stores the XML element `<template>`.

The template contains sub-elements:

* `<pattern>` file path pattern deliverable item.  See :py:class:`dmx.dmlib.templateset.pattern`.
* `<filelist>` filelist deliverable item.  See :py:class:`dmx.dmlib.templateset.filelist`.
* `<milkyway>` Milkyway  deliverable item.  See :py:class:`dmx.dmlib.templateset.milkyway`.
* `<openaccess>` OpenAccess deliverable item.  See :py:class:`dmx.dmlib.templateset.openaccess`.

The template is used to calculate the actual names
of files for a given IP.  For example,

>>> t = Template('RTL')
>>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
'<?xml version="1.0" encoding="utf-8"?>
<template caseid="205507" id="RTL">
  <description> ... </description>
  <filelist id="cell_filelist_dv">
    &ip_name;/rtl/filelists/dv/&cell_name;.f
  </filelist>
  <filelist id="cell_filelist_syn" minimum="0">
    &ip_name;/rtl/filelists/syn/&cell_name;.f
  </filelist>
  <filelist id="cell_filelist_gv" minimum="0">
    &ip_name;/rtl/filelists/gv/&cell_name;.f
  </filelist>
  <filelist id="cell_filelist_mbist" minimum="0">
    &ip_name;/rtl/filelists/mbist/&cell_name;.f
  </filelist>
  <filelist id="fe_gln" minimum="0">
    &ip_name;/rtl/filelists/fe_gln/&cell_name;.f
  </filelist>
  <pattern id="file" minimum="0">
    &ip_name;/rtl/....v
  </pattern>
  <producer id="ICD-IP"/>
  <consumer id="ICD-PD"/>
  <consumer id="NETLIST"/>
  <consumer id="IPD"/>
  <consumer id="SOFTWARE"/>
  <consumer id="IP-DV"/>
  <consumer id="FCV"/>
  <consumer id="TE"/>
</template> '


Here we see that the `BDS` deliverable is made up of a single file whose
actual name is calculated by substituting `&ip_name;` with the name of the IP,
and `&cell_name;` with the name of a top-level cell within that IP.
Most often, there is only one top-level cell per IP, in which case
`&cell_name;` = `&ip_name;`.

The class :py:class:`dmx.dmlib.templateset.templateset` creates a template set,
which contains a complete set of all templates defined.

The subclasses of :py:class:`dmx.dmlib.templateset.itembase` create the deliverable
items (like `<pattern>` in the above example) that make up the deliverable.

Whenever possible, a deterministic file name is specified, and regular
expressions are avoided.  When there is no choice but to use regular
expressions, Perforce style regular expressions are used.

The <template> Element
=========================
This element has the following attributes:

* `case`, the `Fogbugz <http://fogbugz.altera.com>`_ case number
* `id`, the name of this template
* `controlled`, whether the deliverable must be kept in sync with other deliverables defined in the context, either `"yes"` or `"no", default "yes"`
* `versioned`, whether the deliverable files are stored in the version control system, either `"yes"` or `"no", default "yes"`

XML Entities
==============
XML entities of the form `&entityName;` are variable references for which values
are substituted when the XML file is read:

* `&ip_name;`, the name of the IP
* `&cell_name;`, the name a top-level cell within the IP.  Most often, there is only one top-level cell per IP, in which case `&cell_name;` = `&ip_name;`.
* `&deliverable_name;`, the name of the deliverable \
   _that is currently being checked by VP_.  This is not the `id` of this `<template>`.
This allows the path to each deliverable to vary from IP to IP, while remaining
deterministic.

Programmer's Note Regarding Entity References
------------------------------------------------
The rendering of the leading `&` in entity references is a bit tricky:

* Python ElementTree always escapes `&` as `&amp;`
* Therefore, this module uses `&&` in string literals that represent entity references, like `&&ip_name;`
* ElementTree renders `&&ip_name;` as `&amp;&amp;ip_name;`
* Then, as a final post-processing step, `dmx.dmlib.templateset.xmlbase.toxml()` replaces `&amp;&amp;` with `&`

This way, the resultant XML contains the properly formed entity reference `&ip_name;`.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import os
import textwrap
from xml.etree.ElementTree import Element, SubElement
from xml.etree.ElementTree import tostring # @UnusedImport pylint: disable=W0611

from dmx.dmlib.templateset.description import Description
from dmx.dmlib.templateset.pattern import Pattern
from dmx.dmlib.templateset.filelist import Filelist
from dmx.dmlib.templateset.milkyway import Milkyway
from dmx.dmlib.templateset.openaccess import OpenAccess
from dmx.dmlib.templateset.totem import Totem
from dmx.dmlib.templateset.producer import Producer
from dmx.dmlib.templateset.consumer import Consumer
from dmx.dmlib.templateset.itembase import ItemBase
from dmx.dmlib.templateset.xmlbase import XmlBase

class Template(XmlBase):
    '''Construct a deliverable template of the specified name and version.
        
    >>> t = Template('RTL')
    >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    '<?xml version="1.0" encoding="utf-8"?>
    <template caseid="205507" id="RTL">
      <description> ... </description>
      <filelist id="cell_filelist_dv">
        &ip_name;/rtl/filelists/dv/&cell_name;.f
      </filelist>
      <filelist id="cell_filelist_syn" minimum="0">
        &ip_name;/rtl/filelists/syn/&cell_name;.f
      </filelist>
      <filelist id="cell_filelist_gv" minimum="0">
        &ip_name;/rtl/filelists/gv/&cell_name;.f
      </filelist>
      <filelist id="cell_filelist_mbist" minimum="0">
        &ip_name;/rtl/filelists/mbist/&cell_name;.f
      </filelist>
      <filelist id="fe_gln" minimum="0">
        &ip_name;/rtl/filelists/fe_gln/&cell_name;.f
      </filelist>
      <pattern id="file" minimum="0">
        &ip_name;/rtl/....v
      </pattern>
      <producer id="ICD-IP"/>
      <consumer id="ICD-PD"/>
      <consumer id="NETLIST"/>
      <consumer id="IPD"/>
      <consumer id="SOFTWARE"/>
      <consumer id="IP-DV"/>
      <consumer id="FCV"/>
      <consumer id="TE"/>
    </template> '
    '''
    controlledDefault = True
    _versionedDefault = True
    _renamerProgramDefault = 'unknownRenamer'
    
    def __init__(self, id_): # 'Base' __init__ not called: pylint: disable = W0231
        self._id = id_
        self._idlower = self._id.lower()
        self._controlled = self.controlledDefault
        self._versioned = self._versionedDefault
        self._caseid = None
        self._isReady = False
        self._patternList = []
        self._filelistList = []
        self._milkywayList = []
        self._openaccessList = []
        self._totemList = []
        self._producerList = []
        self._consumerList = []
        
        # Execute the function named by the id_ argument
        factoryFunction = getattr(self, '_' + id_)
        factoryFunction()

        self._descriptionOnlyAccessViaProperty = factoryFunction.__doc__

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'template'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Deliverable'
    
    @property
    def id_(self):
        '''The name of the deliverable in this deliverable template.
        
        >>> t = Template('RTL')
        >>> t.id_
        'RTL'
        '''
        return self._id
    
    @property
    def caseid(self):
        '''The Fogbugz case number under which corrections to this deliverable
        were submitted, or None if nothing has been reported.
        
        >>> t = Template('RTL')
        >>> t.caseid
        205507

        The default is None:
        
        >>> t = Template('fakeTemplateWithNoCaseForTesting')
        >>> t.caseid

        '''
        return self._caseid

    @property
    def description(self):
        """The deliverable description, stripped and formatted.
        
        >>> t = Template('EMPTY')
        >>> t.description      #doctest: +NORMALIZE_WHITESPACE
        'Empty deliverable used only for testing the templateset generation software.'
        """
        listOfWords = self._descriptionOnlyAccessViaProperty.split()
        indexOfDoctest = listOfWords.index('>>>')
        return ' '.join(listOfWords[:indexOfDoctest])

    @property
    def isReady(self):
        '''Whether this deliverable has been approved as ready for use.

        >>> t = Template('RTL')
        >>> t.isReady
        True

        The default is False:
        
        >>> t = Template('EMPTY')
        >>> t.isReady
        False
        '''
        return self._isReady

    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.
        
        >>> template = Template('RTL')
        >>> tostring(template.element())      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<template ...>...</template>'
        
        Declare this instance as a SubElement of a parent:

        >>> template = Template('RTL')
        >>> parent = Element("parent")
        >>> child = template.element(parent)
        >>> tostring(parent)      #doctest: +ELLIPSIS
        '<parent><template ...>...</template></parent>'
        '''
        if parent is None:
            template = Element(self.tagName)
        else:
            template = SubElement(parent, self.tagName)
        if self.caseid is not None:
            template.set('caseid', str(self.caseid))
        # template.set('author', self._author)
        if self._controlled != self.controlledDefault:
            template.set('controlled', self._boolToStr(self._controlled))
        # template.set('date', str(self._date))
        template.set('id', self._id)
        # template.set('version', self._version)
        if self._versioned != self._versionedDefault:
            template.set('versioned', self._boolToStr(self._versioned))
            
        
        description = Description(self.description)
        description.element(template)
        
        for filelist in self._filelistList:
            filelist.element(template)
        for pattern in self._patternList:
            pattern.element(template)
        for milkyway in self._milkywayList:
            milkyway.element(template)
        for openaccess in self._openaccessList:
            openaccess.element(template)
        for totem in self._totemList:
            totem.element(template)

        for producer in self._producerList:
            producer.element(template)
        for consumer in self._consumerList:
            consumer.element(template)

        return template

    def report(self, ipName, cellName):
        """Return a human readable string representation.
        """
        assert self._id, 'Every template has an id'
        
        ret = '{} {} (case {}):\n'.format(self.reportName, self._id, self.caseid)
        ret += textwrap.fill(self.description, width=80)
        ret += '\n'
        
        for filelist in self._filelistList:
            ret += '  '
            ret += filelist.report(ipName, cellName)
            ret += '\n'
        for pattern in self._patternList:
            ret += '  '
            ret += pattern.report(ipName, cellName)
            ret += '\n'

        for db in self._milkywayList:
            ret += '  '
            ret += db.report(ipName, cellName)
            ret += '\n'

        for db in self._openaccessList:
            ret += '  '
            ret += db.report(ipName, cellName)
            ret += '\n'

        for db in self._totemList:
            ret += '  '
            ret += db.report(ipName, cellName)
            ret += '\n'

        for producer in self._producerList:
            ret += '  '
            ret += producer.report(ipName, cellName)
            ret += '\n'

        for consumer in self._consumerList:
            ret += '  '
            ret += consumer.report(ipName, cellName)
            ret += '\n'

#        assert self._renamer, 'Every template has a renamer'
#        ret += '  '
#        ret += self._renamer.report()
        return ret

    def _addPatternWithWorkingDir(self, workingDirName, fileExtension,
                                  prependTopCellName=True,
                                  minimum=ItemBase.minimumDefault,
                                  addDot=True,
                                  id_='file'):
        '''Create a path name of the format, 'ipName/design_intent/ipName.fileExtension'.
        
        >>> t = Template('EMPTY')
        >>> t._addPatternWithWorkingDir('workingDir', 'fileName.txt')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/workingDir/&cell_name;.fileName.txt
          </pattern>
        </template> '
        
        Without the IP name prepended to the file name: 
        
        >>> t = Template('EMPTY')
        >>> t._addPatternWithWorkingDir('workingDir', 'fileName.txt', prependTopCellName=False)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/workingDir/fileName.txt
          </pattern>
        </template> '
        
        >>> t = Template('EMPTY')
        >>> t._addPatternWithWorkingDir('workingDir', 'fileName.txt', prependTopCellName=False)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/workingDir/fileName.txt
          </pattern>
        </template> '
        '''
        fileName = self._createFileName(fileExtension, prependTopCellName, addDot)
        pathName = os.path.join(self._ipName, workingDirName, fileName)
        self._patternList.append(Pattern(pathName, id_, minimum=minimum))

    def _addFilelistWithWorkingDir(self, workingDirName, fileName=None,
                                   minimum=ItemBase.minimumDefault, id_='cell_filelist'):
        '''Create a filelist name of the format,
        'ipName/deliverableName/workingDirName/cellName..f'.
        
        >>> t = Template('EMPTY')
        >>> t._addFilelistWithWorkingDir('wd')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <filelist id="cell_filelist">
            &ip_name;/wd/&cell_name;.f
          </filelist>
        </template> '
        
        With the file name specified: 
        
        >>> t = Template('EMPTY')
        >>> t._addFilelistWithWorkingDir('wd', 'xxx.f')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <filelist id="cell_filelist">
            &ip_name;/wd/xxx.f
          </filelist>
        </template> '
        
        >>> t = Template('EMPTY')
        >>> t._addFilelistWithWorkingDir('wd', 'xxx.filelist')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <filelist id="cell_filelist">
            &ip_name;/wd/xxx.filelist
          </filelist>
        </template> '
        '''
        if fileName is None:
            fileName = '{}.f'.format(self._cellName, self._idlower)
        pathName = os.path.join(self._ipName, workingDirName, fileName)
        self._filelistList.append(Filelist(pathName, id_, minimum=minimum))
            
    def _addPattern(self, fileExtension,
                      prependTopCellName=True,
                      minimum=ItemBase.minimumDefault,
                      addDot=True,
                      id_='file'):
        '''Create a path name of the format, 'ipName/deliverableName/ipName.fileExtension'.
        
        >>> t = Template('EMPTY')
        >>> t._addPattern('fileName.txt')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/empty/&cell_name;.fileName.txt
          </pattern>
        </template> '
        
        Without the IP name prepended to the file name: 
        
        >>> t = Template('EMPTY')
        >>> t._addPattern('fileName.txt', prependTopCellName=False)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/empty/fileName.txt
          </pattern>
        </template> '
        
        >>> t = Template('EMPTY')
        >>> t._addPattern('fileName.txt', prependTopCellName=False)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/empty/fileName.txt
          </pattern>
        </template> '
        '''
        fileName = self._createFileName(fileExtension, prependTopCellName, addDot)
        pathName = os.path.join(self._ipName, self._idlower, fileName)
        self._patternList.append(Pattern(pathName, id_, minimum=minimum))
    

    def _addReleaseNotes(self):
        '''Add a Word format release note of the format,
        'ipName/deliverableName/releasenotess.docx' to the deliverable.
        
        >>> t = Template('EMPTY')
        >>> t._addReleaseNotes()
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
            &ip_name;/empty/releasenotes.docx
          </pattern>
        </template> '
        '''
        self._addPattern('releasenotes.docx', prependTopCellName=False, id_='releasenotes')

    def _addFilelist(self, fileName=None, minimum=ItemBase.minimumDefault, id_='cell_filelist'):
        '''Create a filelist name of the format, 'ipName/deliverableName/filelist/cellName.f'.
        
        >>> t = Template('EMPTY')
        >>> t._addFilelist()
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <filelist id="cell_filelist">
            &ip_name;/empty/filelist/&cell_name;.f
          </filelist>
        </template> '
        
        With a specified file name: 
        
        >>> t = Template('EMPTY')
        >>> t._addFilelist('file.f')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <filelist id="cell_filelist">
            &ip_name;/empty/filelist/file.f
          </filelist>
        </template> '
        '''
        if fileName is None:
            fileName = '{}.f'.format(self._cellName)
        workingDirName =  os.path.join(self._idlower, 'filelist')
        self._addFilelistWithWorkingDir(workingDirName, fileName, minimum, id_)

    def _addOpenAccessCellView(self, viewName, viewType, id_='oaDesign',
                               minimum=ItemBase.minimumDefault):
        '''Add the OpenAccess cellView `ip_name/ip_name/viewName`.
        
        >>> t = Template('EMPTY')
        >>> t._addOpenAccessCellView('layout', 'oacMaskLayout')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <openaccess id="oaDesign" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/oa/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
            <cell>
              &cell_name;
            </cell>
            <view viewtype="oacMaskLayout">
              layout
            </view>
          </openaccess>
        </template> '
        >>>
        >>> t = Template('EMPTY')
        >>> t._addOpenAccessCellView('layout', 'oacMaskLayout', id_='layoutView')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <openaccess id="layoutView" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/oa/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
            <cell>
              &cell_name;
            </cell>
            <view viewtype="oacMaskLayout">
              layout
            </view>
          </openaccess>
        </template> '
        >>>
        >>> t = Template('EMPTY')
        >>> t._addOpenAccessCellView('layout', 'oacMaskLayout', id_='layoutView', minimum=0)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <openaccess id="layoutView" mimetype="application/octet-stream" minimum="0">
            <libpath>
              &ip_name;/oa/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
            <cell>
              &cell_name;
            </cell>
            <view viewtype="oacMaskLayout">
              layout
            </view>
          </openaccess>
        </template> '
        '''
        libPath = os.path.join(self._ipName, 'oa', self._ipName)
        self._openaccessList.append(OpenAccess(libPath,
                                                          self._ipName, # lib name
                                                          self._cellName, # cell name
                                                          viewName,     # view name
                                                          viewType,
                                                          id_=id_,
                                                          minimum=minimum))

    def _addOpenAccessAllCellViews(self, viewName, viewType, id_='oaDesign',
                                   minimum=ItemBase.minimumDefault):
        '''Add the OpenAccess cellViews `ip_name/*/viewName`, where `*` means all cell names.
        
        >>> t = Template('EMPTY')
        >>> t._addOpenAccessAllCellViews('layout', 'oacMaskLayout')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <openaccess id="oaDesign" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/oa/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
            <view viewtype="oacMaskLayout">
              layout
            </view>
          </openaccess>
        </template> '
        >>>
        >>> t = Template('EMPTY')
        >>> t._addOpenAccessAllCellViews('layout', 'oacMaskLayout', id_='layoutView')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <openaccess id="layoutView" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/oa/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
            <view viewtype="oacMaskLayout">
              layout
            </view>
          </openaccess>
        </template> '
        >>>
        >>> t = Template('EMPTY')
        >>> t._addOpenAccessAllCellViews('layout', 'oacMaskLayout', id_='layoutView')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <openaccess id="layoutView" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/oa/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
            <view viewtype="oacMaskLayout">
              layout
            </view>
          </openaccess>
        </template> '
        '''
        libPath = os.path.join(self._ipName, 'oa', self._ipName)
        self._openaccessList.append(OpenAccess(libPath,
                                                          self._ipName, # lib name
                                                          None,         # cell name
                                                          viewName,     # view name
                                                          viewType,
                                                          id_=id_,
                                                          minimum=minimum,
                                                          ))

    def _addMilkywayMutliCells(self, cellName=None, viewName=None,
                         viewType=None, suffix=None, id_='mwLib'):
        '''Add the specified Milkyway library.
        
        >>> t = Template('EMPTY')
        >>> t._addMilkywayMutliCells()
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/&cell_name;
            </libpath>
            <lib>
              &cell_name;
            </lib>
          </milkyway>
        </template> '
        
        >>> t = Template('EMPTY')
        >>> t._addMilkywayMutliCells(suffix='__suffix')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="..." controlled="no" id="EMPTY">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/&cell_name;__suffix
            </libpath>
            <lib>
              &cell_name;__suffix
            </lib>
          </milkyway>
        </template> '
        '''
        libPath = os.path.join(self._ipName, self._idlower, self._cellName)
        if suffix is not None:
            libPath += suffix
        self._milkywayList.append(Milkyway(libPath, cellName, viewName,
                 viewType, id_))
    
    def _addMilkywayCell(self, cellName=None, viewName=None,
                         viewType=None, suffix=None, id_='mwLib'):
        '''Add the specified Milkyway library.
        
        >>> t = Template('EMPTY')
        >>> t._addMilkywayCell()
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
          </milkyway>
        </template> '
        
        >>> t = Template('EMPTY')
        >>> t._addMilkywayCell(suffix='__suffix')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="..." controlled="no" id="EMPTY">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/&ip_name;__suffix
            </libpath>
            <lib>
              &ip_name;__suffix
            </lib>
          </milkyway>
        </template> '
        '''
        libPath = os.path.join(self._ipName, self._idlower, self._ipName)
        if suffix is not None:
            libPath += suffix
        self._milkywayList.append(Milkyway(libPath, cellName, viewName,
                 viewType, id_))
    
    def _addMilkywayCellWithWorkingDir(self, workingDirName, cellName=None, viewName=None,
                         viewType=None, suffix=None, id_='mwLib'):
        '''Add the specified Milkyway library.
        
        >>> t = Template('EMPTY')
        >>> t._addMilkywayCellWithWorkingDir('empty/logical')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/logical/&ip_name;__empty
            </libpath>
            <lib>
              &ip_name;__empty
            </lib>
          </milkyway>
        </template> '
        
        >>> t = Template('EMPTY')
        >>> t._addMilkywayCellWithWorkingDir('empty/physical', suffix='__suffix')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="..." controlled="no" id="EMPTY">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/physical/&ip_name;__suffix
            </libpath>
            <lib>
              &ip_name;__suffix
            </lib>
          </milkyway>
        </template> '
        '''
        libPath = os.path.join(self._ipName, workingDirName, self._ipName)
        if suffix is None:
            libPath += '__' + self._idlower
        else:
            libPath += suffix
        self._milkywayList.append(Milkyway(libPath, cellName, viewName,
                 viewType, id_))
    
    def _addTotem(self, isStatic=True, id_=None, minimum=ItemBase.minimumDefault):
        '''Add the specified Totem database.
        
        The default is database `&ip_name;.static.cmm`, with id `static`:
        
        >>> t = Template('EMPTY')
        >>> t._addTotem()
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <totem id="static" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/&cell_name;.static.cmm
            </libpath>
            <lib>
              &cell_name;.static.cmm
            </lib>
          </totem>
        </template> '
        
        If you specify a dynamic database, it is  `&ip_name;.dynamic.cmm`, with
        id `dynamic`:
        
        >>> t = Template('EMPTY')
        >>> t._addTotem(isStatic=False)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <totem id="dynamic" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/empty/&cell_name;.dynamic.cmm
            </libpath>
            <lib>
              &cell_name;.dynamic.cmm
            </lib>
          </totem>
        </template> '
        
        You can of course also specify the id and minimum number of files:
        
        >>> t = Template('EMPTY')
        >>> t._addTotem(id_='totem2', minimum=0)
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <totem id="totem2" mimetype="application/octet-stream" minimum="0">
            <libpath>
              &ip_name;/empty/&cell_name;.static.cmm
            </libpath>
            <lib>
              &cell_name;.static.cmm
            </lib>
          </totem>
        </template> '
        '''
        libraryName = self._cellName 
        if isStatic:
            if id_ is None:
                id_ = 'static'
            libraryName += '.static.cmm'
        else:
            if id_ is None:
                id_ = 'dynamic'
            libraryName += '.dynamic.cmm'
        libPath = os.path.join(self._ipName, self._idlower, libraryName)
        self._totemList.append(Totem(libPath, libraryName, id_=id_, minimum=minimum))
    
    def _addProducer(self, id_):
        '''Add a producer with the specified team name.
        
        >>> t = Template('EMPTY')
        >>> t._addProducer('LAY-IP')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <producer id="LAY-IP"/>
        </template> '
        '''
        self._producerList.append(Producer(id_))

    def _addConsumer(self, id_):
        '''Add a consumer with the specified team name.
        
        >>> t = Template('EMPTY')
        >>> t._addConsumer('LAY-IP')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description> ... </description>
          <consumer id="LAY-IP"/>
        </template> '
        '''
        self._consumerList.append(Consumer(id_))

    @classmethod
    def _createFileName(cls, fileExtension, prependTopCellName, addDot=True):
        '''Create a file name, either with or without the ipName prepended.
        
        >>> Template._createFileName('fileName.txt', False)
        'fileName.txt'
        >>> Template._createFileName('fileName.txt', True)
        '&&cell_name;.fileName.txt'
        '''
        if prependTopCellName:
            if addDot:
                return cls._cellName + '.' + fileExtension
            return cls._cellName + fileExtension
        return fileExtension

    def _fakeExcessTemplateForTesting(self):
        '''Fake excess deliverable used only for testing the templateset
        generation software.

        >>> t = Template('fakeExcessTemplateForTesting')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="fakeExcessTemplateForTesting">
          <description>
            Fake excess deliverable used only for testing the templateset
            generation software.
          </description>
          <pattern id="file">
            &ip_name;/fakeexcesstemplatefortesting/&cell_name;.fake.txt
          </pattern>
        </template> '
        '''
        self._controlled = False
        self._caseid = 0
        self._addPattern("fake.txt")

    
    def _fakeTemplateWithDuplicatesForTesting(self):
        '''Fake deliverable containing duplicate files used only for testing
        the templateset generation software.

        >>> t = Template('fakeTemplateWithDuplicatesForTesting')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="fakeTemplateWithDuplicatesForTesting">
          <description>
            Fake deliverable containing duplicate files used only for testing
            the templateset generation software.
          </description>
          <pattern id="file">
            &ip_name;/faketemplatewithduplicatesfortesting/&cell_name;.txt
          </pattern>
          <pattern id="file">
            &ip_name;/faketemplatewithduplicatesfortesting/&cell_name;.txt
          </pattern>
        </template> '
        '''
        self._caseid = 0
        self._controlled = False
        self._addPattern("txt", id_="file")
        self._addPattern("txt", id_="file")

    def _fakeTemplateWithNoCaseForTesting(self):
        '''Fake deliverable containing no case number used only for testing
        the templateset generation software.

        >>> t = Template('fakeTemplateWithNoCaseForTesting')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template controlled="no" id="fakeTemplateWithNoCaseForTesting">
          <description>
            ...
          </description>
        </template> '
        '''
        self._controlled = False

    
    # Allow all-capital names
    # pylint #pylint: disable-msg=C0103

    def _EMPTY(self):
        '''Empty deliverable used only for testing the templateset generation
        software.

        >>> t = Template('EMPTY')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="0" controlled="no" id="EMPTY">
          <description>
            Empty deliverable used only for testing the templateset generation
            software.
          </description>
        </template> '
        '''
        self._caseid = 0
        self._controlled = False
    
    # AAAMOD eliminated per case 28046
    
#    def _ABX2GLN(self):
#        '''Abstracted gate-level Verilog model generated from schematics.
#        This also includes behavior models for blocks that the abstraction tool
#        cannot abstract.
#        
#        >>> t = Template('ABX2GLN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="24167" id="ABX2GLN">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/abx2gln/&ip_name;.abx2gln.filelist
#          </filelist>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 24167
#        self._isReady = True
#
#        self._addFilelist()
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("TE")


    def _BCMRBC(self):
        '''BCMRBC exists to describe configuration and constraint rules developed by the designer
        during their design. The BCM will comply with the XML format and will be verified by BCM
        tool. RBC will be in System Verilog format and will also be verified by BCM Tool. Audit
        files are also delivered in accordance with the Audit checks defined for this deliverable.
        Requirement of an audit check for this deliverable is still under evaluation.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/BCMRBC_Definition.docx

        >>> t = Template('BCMRBC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205257" id="BCMRBC">
          <description> ... </description>
          <pattern id="bcm" mimetype="text/xml">
            &ip_name;/bcmrbc/&cell_name;.bcm.xml
          </pattern>
          <pattern id="di" minimum="0">
            &ip_name;/bcmrbc/....di.filelist
          </pattern>
          <pattern id="rbc">
            &ip_name;/bcmrbc/&cell_name;.rbc.sv
          </pattern>
          <pattern id="config" minimum="0">
            &ip_name;/bcmrbc/addbcm.config
          </pattern>
          <pattern id="subconfig" minimum="0">
            &ip_name;/bcmrbc/*.bcm_substitute.config
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 205257
        self._isReady = True

        self._addPattern("bcm.xml",     id_='bcm')
        self._addPattern("....di.filelist", prependTopCellName=False, id_='di',  minimum=0)
        self._addPattern("rbc.sv",      id_='rbc')
        self._addPattern("addbcm.config", prependTopCellName=False, id_='config',  minimum=0)
        self._addPattern("*.bcm_substitute.config", prependTopCellName=False, id_='subconfig',  minimum=0)
        self._addProducer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("TE")
        # cell_name;.rbc.sv, &cell_name;.bcm.xml requested (back?)
        # by http://fogbugz/default.asp?110433 - R.G.

#    def _BDS(self):
#        '''Block Data Sheets. IP block port lists for all instances. Composed
#        of BLOCKSIZE: Block size spreadsheet(floorplan) that contain a full list
#        of IP block size. Block size allocation estimation, estimated dimension
#        of the block allocated.  The final block size will be driven from PnR.
#
#        >>> t = Template('BDS')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28062" id="BDS">
#          <description> ... </description>
#          <pattern id="file" mimetype="text/xml">
#            &ip_name;/bds/&cell_name;.bds.xml
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28062
#        self._isReady = True
#
#        self._addPattern('bds.xml')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    # BLKTB removed per case 28063.  Then reinstated as IPTB.
#
#    def _BUMPS(self):
#        '''Bump or bond pad layout physical placement.
#
#        >>> t = Template('BUMPS')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="27748" id="BUMPS">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/bumps/&ip_name;.pad.txt
#          </pattern>
#          <producer id="LAYOUT"/>
#          <consumer id="PACKAGING"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 27748
#        self._isReady = True
##        self._addPattern("pad.txt")
#        self._addPattern (self._ipName + '.pad.txt', 
#                          id_='file',
#                          prependTopCellName=False)        
#        self._addProducer("LAYOUT")
#        self._addConsumer("PACKAGING")
#        self._addConsumer("PD-ICD")


    def _CDC(self):
        '''CDC is needed to detect clock domain crossing issues, which might
        cause functional or timing failures not detect-able by logic or timing
        simulation. SpyGlass CDC tool is used to detect CDC issues in all ASIC
        blocks. Deliverables are constraint (SGDC), waivers and log file.
        They are not directly consumed by other deliverables. They are there to
        check for CDC issues and make sure these are addressed.  
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/CDC_Definition.docx

        >>> t = Template('CDC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205259" id="CDC">
          <description> ... </description>
          <pattern id="rpt">
            &ip_name;/cdc/*/reports/*.moresimple.rpt
          </pattern>
          <pattern id="cfg">
            &ip_name;/cdc/*/&cell_name;.cfg
          </pattern>
          <pattern id="prj">
            &ip_name;/cdc/*/&cell_name;.prj
          </pattern>
          <pattern id="sgdc">
            &ip_name;/cdc/*/&cell_name;*.sgdc
          </pattern>
          <pattern id="swl" minimum="0">
            &ip_name;/cdc/*/&cell_name;*.swl
          </pattern>
          <producer id="ICD-IP"/>
        </template> '
        '''
        self._caseid = 205259
        self._isReady = True
        
        dirName = os.path.join(self._idlower, '*')
        self._addPatternWithWorkingDir(dirName, "reports/*.moresimple.rpt",
                                       id_='rpt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "cfg",
                                       id_='cfg')
        self._addPatternWithWorkingDir(dirName, "prj",
                                       id_='prj')
        self._addPatternWithWorkingDir(dirName, "*.sgdc",
                                       id_='sgdc', addDot=False)
        self._addPatternWithWorkingDir(dirName, "*.swl", addDot=False,
                                       id_='swl',
                                       minimum=0)
        self._addProducer("ICD-IP")

    def _CDL(self):
        '''The CDL deliverable exists to store:
           1. Netlist for Physical Verifications (PV)
              a. Based on /ipspec/cell_names.txt
           2. audit.<&cell_name>.cdl.f
           3. audit.<&cell_name>.cdl.OA.xml
           4. audit.<&cell_name>.cdl.netlist.xml
           5. <&cell_name>.cdl.log

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/CDL_Definition.docx

        >>> t = Template('CDL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209050" id="CDL">
          <description> ... </description>
          <pattern id="cdl">
          &ip_name;/cdl/&cell_name;.cdl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="LAY-IP"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 209050
        self._isReady = True

        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, 'cdl',
                id_='cdl')
        self._addProducer("ICD-IP")
        self._addConsumer("LAY-IP")
        self._addConsumer("ICD-PD")

#    def _CELFRAM(self):
#        '''Milkyway CEL view and FRAM view. Depending on the physical synthesis
#        flow, this will either be copied from the ICC Milkyway working library,
#        or translated from deliverable LAY.
#
#        >>> t = Template('CELFRAM')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="59038" id="CELFRAM">
#          <description> ... </description>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/celfram/&ip_name;__celfram
#            </libpath>
#            <lib>
#              &ip_name;__celfram
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view>
#              CEL 
#            </view>
#          </milkyway>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 59038
#        self._isReady = True
#        self._addMilkywayCell(self._cellName, 'CEL')
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("PD-ICD")

#    def _CIRCUITSIM(self):
#        '''Spice netlists for power up simulation with SPICE, BDA and 
#        hsim:fastspice).
#
#        >>> t = Template('CIRCUITSIM')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="92371" id="CIRCUITSIM">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/circuitsim/&ip_name;.circuitsim.filelist
#          </filelist>
#          <pattern id="spi" minimum="0">
#            &ip_name;/circuitsim/powerup/*.spi
#          </pattern>
#          <pattern id="mt0" minimum="0">
#            &ip_name;/circuitsim/powerup/*.mt0
#          </pattern>
#          <pattern id="tr0" minimum="0">
#            &ip_name;/circuitsim/powerup/*.tr0
#          </pattern>
#          <pattern id="fsdb" minimum="0">
#            &ip_name;/circuitsim/powerup/*.fsdb
#          </pattern>
#          <pattern id="cir" minimum="0">
#            &ip_name;/circuitsim/powerup/*.cir
#          </pattern>
#          <pattern id="powerup_icc" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" minimum="0">
#            &ip_name;/circuitsim/powerup/*.powerup_icc.xlsx
#          </pattern>
#          <pattern id="mode_transitions_icc" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" minimum="0">
#            &ip_name;/circuitsim/powerup/*.mode_transitions_icc.xlsx
#          </pattern>
#          <pattern id="functional" minimum="0">
#            &ip_name;/circuitsim/functional/*
#          </pattern>
#          <pattern id="power" minimum="0">
#            &ip_name;/circuitsim/power/*
#          </pattern>
#          <pattern id="speed" minimum="0">
#            &ip_name;/circuitsim/speed/*
#          </pattern>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 92371
#        self._isReady = True
#
#        self._addFilelist()
#        
#        dirName = os.path.join(self._idlower, 'powerup')
#        self._addPatternWithWorkingDir(dirName, '*.spi',
#                                       id_='spi',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(dirName, '*.mt0',
#                                       id_='mt0',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(dirName, '*.tr0',
#                                       id_='tr0',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(dirName, '*.fsdb',
#                                       id_='fsdb',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(dirName, '*.cir',
#                                       id_='cir',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(dirName, '*.powerup_icc.xlsx',
#                                       id_='powerup_icc',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(dirName, '*.mode_transitions_icc.xlsx',
#                                       id_='mode_transitions_icc',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'functional')
#        self._addPatternWithWorkingDir(dirName, '*',
#                                       id_='functional',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'power')
#        self._addPatternWithWorkingDir(dirName, '*',
#                                       id_='power',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'speed')
#        self._addPatternWithWorkingDir(dirName, '*',
#                                       id_='speed',
#                                       minimum=0,
#                                       prependTopCellName=False)
#        
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("PD-ICD")
#
    def _CIRCUITSIM(self):
        '''This deliverable is used for capture the circuit simulation with spice like tool.
           One must have is powerup simulation.
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/CIRCUITSIM_Definition.docx

        >>> t = Template('CIRCUITSIM')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209037" id="CIRCUITSIM">
          <description> ... </description>
          <pattern id="functional">
            &ip_name;/circuitsim/functional/*
          </pattern>
          <pattern id="power">
            &ip_name;/circuitsim/power/*
          </pattern>
          <pattern id="powerup">
            &ip_name;/circuitsim/powerup/*
          </pattern>
          <pattern id="speed">
            &ip_name;/circuitsim/speed/*
          </pattern>
          <pattern id="sms">
            &ip_name;/circuitsim/sms/*
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 209037
        self._isReady = True

        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, 'functional/*',
                                       id_='functional',
                                       prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'power/*',
                                       id_='power',
                                       prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'powerup/*',
                                       id_='powerup',
                                       prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'speed/*',
                                       id_='speed',
                                       prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'sms/*',
                                       id_='sms',
                                       prependTopCellName=False)
        
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")

#    def _CV(self):
#        '''Constraint generation and verification results and generated
#        constraints files, using the Fishtail tool.
#
#        >>> t = Template('CV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="87821" id="CV">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/cv/results/&cell_name;.cv.rpt
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 87821
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'results')
#        self._addPatternWithWorkingDir(dirName, self._idlower + ".rpt")
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-ICD-DIGITAL")

    def _COMPLIB(self):
        '''The Componet Library (COMPLIB) deliverable provides specifc information in
        a compact database form (.dmz) for each IP.  The DMZ component is used for
        logical connectivity, physical implementation of the IP, and integration of
        the IP into higher levels of the design hierarchy.  Each IP within the ICM tree
        is compiled into its own DMZ component.  DMZ components are combined by means
        of a DMZ utility to produce a merged DMZ Component library containing a set of
        IPs within the ICM tree.  Only the merged library is consumed by other deliverables.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/COMPLIB_Definition.docx

        >>> t = Template('COMPLIB')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="206838" id="COMPLIB">
          <description> ... </description>
          <pattern id="file" mimetype="application/octet-stream">
            &ip_name;/complib/*.dmz
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="TE"/>
        </template> '
        '''
# Jack changed spec
#          <pattern id="dmz_file" mimetype="application/octet-stream">
#            &ip_name;/complib/&cell_name;_cmpntLib.dmz
#          </pattern>
#          <pattern id="fpsrc_tcl" minimum="0">
#            &ip_name;/complib/src/&cell_name;_fp.tcl
#          </pattern>
#          <pattern id="src_tcl" minimum="0">
#            &ip_name;/complib/src/&cell_name;_bind.tcl
#          </pattern>
#          <pattern id="src_txt" minimum="0">
#            &ip_name;/complib/src/&cell_name;_cmpntLib.txt
#          </pattern>
#          <pattern id="dp_dmz" mimetype="application/octet-stream" minimum="0">
#            &ip_name;/complib/dp/&cell_name;_fp.dmz
#          </pattern>
#          <pattern id="dp_def">
#            &ip_name;/complib/dp/&cell_name;.def
#          </pattern>
#          <pattern id="dp_lef">
#            &ip_name;/complib/dp/&cell_name;.lef
#          </pattern>

        self._caseid = 206838
        self._isReady = True
        self._addPattern('*.dmz', prependTopCellName=False)
#        dirName = os.path.join(self._idlower)
#        self._addPatternWithWorkingDir(dirName, '_cmpntLib.dmz', addDot=False,
#                                       id_='dmz_file')
#
#        dirName = os.path.join(self._idlower, 'src')
#        self._addPatternWithWorkingDir(dirName, '_fp.tcl',
#                                       id_='fpsrc_tcl', minimum=0, addDot=False)
#        dirName = os.path.join(self._idlower, 'src')
#        self._addPatternWithWorkingDir(dirName, '_bind.tcl', minimum=0, addDot=False,
#                                       id_='src_tcl')
#        dirName = os.path.join(self._idlower, 'src')
#        self._addPatternWithWorkingDir(dirName, '_cmpntLib.txt',
#                                       id_='src_txt', minimum=0, addDot=False)
#
#        dirName = os.path.join(self._idlower, 'dp')
#        self._addPatternWithWorkingDir(dirName, '_fp.dmz', id_='dp_dmz', minimum=0, addDot=False)
#        dirName = os.path.join(self._idlower, 'dp')
#        self._addPatternWithWorkingDir(dirName, 'def', id_='dp_def')
#        dirName = os.path.join(self._idlower, 'dp')
#        self._addPatternWithWorkingDir(dirName, 'lef', id_='dp_lef')

        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("TE")

    def _COMPLIBPHYS(self):
        '''The Componet Library Physical(COMPLIBPHYS) deliverable provides additional physical
        design information from the logical for each IP. COMPLIBPHY continues development of
        the DMZ component containing all the logical information from COMPLIB and adding to it.
        The physical information in a DMZ component is used for, physical implementation of the IP,
        and integration of the IP into higher levels of the design hierarchy.  Each IP within
        the ICM tree is compiled into its own DMZ component.  DMZ components are combined by means of
        a DMZ utility to produce a merged DMZ Component library containing a set of  IPs within the
        ICM tree.  Only the merged library is consumed by other deliverables.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/COMPLIBPHYS_Definition.docx

        >>> t = Template('COMPLIBPHYS')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="234535" id="COMPLIBPHYS">
          <description> ... </description>
          <pattern id="file" mimetype="application/octet-stream">
            &ip_name;/complibphys/*.dmz
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="TE"/>
        </template> '
        '''

        self._caseid = 234535
        self._isReady = True
        self._addPattern('*.dmz', prependTopCellName=False)

        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("TE")

    def _CVIMPL(self):
        '''CVIMPL exists to collect timing constraints developed by the physical design
         engineer/Backend engineer during implementation of the design. The constraints
         will comply with the industry standard Synopsys Design Constraint format and will
         be vetted using the Fishtail tool flows. For each mode, one SDC file will be
         delivered to run the STA flow in R2G2. Some of the timing constraints could be
         in TCL format and sourced from within the SDC file.   Source constraints will
         come from the CVRTL deliverable.

         The implementation engineer is responsible to define/find these constraints if
         not supplied. There are points in the design process where it is expected that
         CVIMPL will NOT be provided. If no CVIMPL constraints are supplied to the
         Implementation team, they can use CVRTL constraints as a placeholder by copying
         them into the CVIMPL directory for use in R2G2. (Please consult R2G2
         documentation for additional help) These constraints MUST NOT be checked in to the
         CVIMPL deliverable unless verified by FISHTAIL.

         If supplied in the ICM workspace, the CVIMPL constraints are expected to be FISHTAIL
         verified and used for PnR. The verified constraints in CVIMPL will be used by
         physical implementation tools like Synopsys ICC.

         Audit files are also delivered in accordance with the Audit checks defined for this
         deliverable. Requirement of an audit check for this deliverable is still under evaluation.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/CVIMPL_Definition.docx

        >>> t = Template('CVIMPL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209035" id="CVIMPL">
          <description> ... </description>
          <filelist id="sdc_filelist" minimum="0">
            &ip_name;/cvimpl/constraints/&cell_name;.sdc.filelist
          </filelist>
          <pattern id="csdc">
            &ip_name;/cvimpl/constraints/&cell_name;.*.sdc
          </pattern>
          <pattern id="sdc" minimum="0">
            &ip_name;/cvimpl/constraints/*/*.sdc
          </pattern>
          <pattern id="tcl" minimum="0">
            &ip_name;/cvimpl/constraints/*/*.tcl
          </pattern>
          <pattern id="waivers" minimum="0">
            &ip_name;/cvimpl/waivers/*.waive.tcl
          </pattern>
          <pattern id="rpt" minimum="0">
            &ip_name;/cvimpl/results/&cell_name;_*.rpt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-IP"/>
          <consumer id="SPNR"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 209035
        self._isReady = True


        dirName = os.path.join(self._idlower, 'constraints')
        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._cellName),
                                        id_='sdc_filelist', minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.sdc',
                                        id_='csdc')

        dirName = os.path.join(self._idlower, 'constraints', '*')
        self._addPatternWithWorkingDir(dirName, '*.sdc', 
                                       id_='sdc', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.tcl', 
                                       id_='tcl', prependTopCellName=False, minimum=0)
        
        dirName = os.path.join(self._idlower, 'waivers')
        self._addPatternWithWorkingDir(dirName, '*.waive.tcl',
                                       id_='waivers', prependTopCellName=False, minimum=0)
        
        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, '_*.rpt', addDot=False, minimum=0, id_='rpt')
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-IP")
        self._addConsumer("SPNR")
        self._addConsumer("ICD-PD")

    def _CVRTL(self):
        '''CVRTL exists to collect timing constraints developed by the designer during RTL design.
        The constraints will comply with the industry standard Synopsys Design Constraint format
        and will be vetted using the Fishtail tool flows.  For each mode, one SDC file will be
        delivered to run the STA flow in R2G2. Some of the timing constraints could be in TCL
        format and sourced from within the SDC file.
        Audit files are also delivered in accordance with the Audit checks defined for this
        deliverable. Requirement of an audit check for this deliverable is still under evaluation.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/CVRTL_Definition.docx

        >>> t = Template('CVRTL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205261" id="CVRTL">
          <description> ... </description>
          <filelist id="sdc_filelist" minimum="0">
            &ip_name;/cvrtl/constraints/&cell_name;.sdc.filelist
          </filelist>
          <pattern id="csdc">
            &ip_name;/cvrtl/constraints/&cell_name;.*.sdc
          </pattern>
          <pattern id="sdc" minimum="0">
            &ip_name;/cvrtl/constraints/*/*.sdc
          </pattern>
          <pattern id="tcl" minimum="0">
            &ip_name;/cvrtl/constraints/*/*.tcl
          </pattern>
          <pattern id="waivers" minimum="0">
            &ip_name;/cvrtl/waivers/*.waive.tcl
          </pattern>
          <pattern id="rpt" minimum="0">
            &ip_name;/cvrtl/results/&cell_name;_*.rpt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 205261
        self._isReady = True


        dirName = os.path.join(self._idlower, 'constraints')
        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._cellName),
                                        id_='sdc_filelist', minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.sdc',
                                        id_='csdc')

        dirName = os.path.join(self._idlower, 'constraints', '*')
        self._addPatternWithWorkingDir(dirName, '*.sdc', 
                                       id_='sdc', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.tcl', 
                                       id_='tcl', prependTopCellName=False, minimum=0)
        
        dirName = os.path.join(self._idlower, 'waivers')
        self._addPatternWithWorkingDir(dirName, '*.waive.tcl',
                                       id_='waivers', prependTopCellName=False, minimum=0)
        
        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, '_*.rpt', addDot=False, minimum=0, id_='rpt')
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-IP")
        self._addConsumer("ICD-PD")

    def _CVSIGNOFF(self):
        '''CVSIGNOFF exists to collect timing constraints developed by the designer
        for signing off the design. The constraints will comply with the industry standard
        'Synopsys Design Constraint' format and will be vetted using the Fishtail tool flows.
        An SDC filelist will be delivered which will point to one or more constraint (SDC) files.
        Some of the timing constraints could be in TCL format. Source constraints will come
        from the CVRTL and CVSIGNOFF deliverables. These timing constraints will be saved in
        CVSIGNOFF, verified using Fishtail and then read into Synopsys Primetime for timing
        analysis and timing signoff.
        Audit files are also delivered in accordance with the Audit checks defined for
        this deliverable. Requirement of an audit check for this deliverable is still under evaluation. 
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/CVSIGNOFF_Definition.docx

        >>> t = Template('CVSIGNOFF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209036" id="CVSIGNOFF">
          <description> ... </description>
          <filelist id="sdc_filelist" minimum="0">
            &ip_name;/cvsignoff/constraints/&cell_name;.sdc.filelist
          </filelist>
          <pattern id="csdc">
            &ip_name;/cvsignoff/constraints/&cell_name;.*.sdc
          </pattern>
          <pattern id="sdc" minimum="0">
            &ip_name;/cvsignoff/constraints/*/*.sdc
          </pattern>
          <pattern id="tcl" minimum="0">
            &ip_name;/cvsignoff/constraints/*/*.tcl
          </pattern>
          <pattern id="waivers" minimum="0">
            &ip_name;/cvsignoff/waivers/*.waive.tcl
          </pattern>
          <pattern id="rpt" minimum="0">
            &ip_name;/cvsignoff/results/&cell_name;_*.rpt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-IP"/>
          <consumer id="SPNR"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 209036
        self._isReady = True


        dirName = os.path.join(self._idlower, 'constraints')
        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._cellName),
                                        id_='sdc_filelist', minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.sdc',
                                        id_='csdc')

        dirName = os.path.join(self._idlower, 'constraints', '*')
        self._addPatternWithWorkingDir(dirName, '*.sdc', 
                                       id_='sdc', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.tcl', 
                                       id_='tcl', prependTopCellName=False, minimum=0)
        
        dirName = os.path.join(self._idlower, 'waivers')
        self._addPatternWithWorkingDir(dirName, '*.waive.tcl',
                                       id_='waivers', prependTopCellName=False, minimum=0)
        
        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, '_*.rpt', addDot=False, minimum=0, id_='rpt')
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-IP")
        self._addConsumer("SPNR")
        self._addConsumer("ICD-PD")

#    def _DEVPROG(self):
#        '''Chain Information on 1.CSR chain sequence 2.CSR bit count per
#        IP 3.CSR bit count per segment 4. CB Hardwired Info Table.
#
#        >>> t = Template('DEVPROG')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="37800" id="DEVPROG">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/devprog/releasenotes.docx
#          </pattern>
#          <pattern id="aux_eram" mimetype="text/csv">
#            &ip_name;/devprog/&cell_name;.aux_eram.csv
#          </pattern>
#          <pattern id="csr_length_report" mimetype="text/csv">
#            &ip_name;/devprog/&cell_name;.csr_length_report.csv
#          </pattern>
#          <pattern id="csr_chain" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.csr_chain.xlsx
#          </pattern>
#          <pattern id="jtag_sequence" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.jtag_sequence.xlsx
#          </pattern>
#          <pattern id="config_io_spec" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.config_io_spec.xlsx
#          </pattern>
#          <pattern id="cb_hw" mimetype="text/tab-separated-values">
#            &ip_name;/devprog/&cell_name;.cb_hw.tsv
#          </pattern>
#          <pattern id="dfm" mimetype="text/tab-separated-values">
#            &ip_name;/devprog/&cell_name;.dfm.tsv
#          </pattern>
#          <pattern id="global_routing_master" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.global_routing_master.xlsx
#          </pattern>
#          <pattern id="io_hps_post" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.io_hps_post.xlsx
#          </pattern>
#          <pattern id="dras_requirement" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.dras_requirement.xlsx
#          </pattern>
#          <pattern id="rowclk_reach" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.rowclk_reach.xlsx
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>#
#
#    def _DEVPROG(self):
#        '''Chain Information on 1.CSR chain sequence 2.CSR bit count per
#        IP 3.CSR bit count per segment 4. CB Hardwired Info Table.
#
#        >>> t = Template('DEVPROG')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="37800" id="DEVPROG">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/devprog/releasenotes.docx
#          </pattern>
#          <pattern id="aux_eram" mimetype="text/csv">
#            &ip_name;/devprog/&cell_name;.aux_eram.csv
#          </pattern>
#          <pattern id="csr_length_report" mimetype="text/csv">
#            &ip_name;/devprog/&cell_name;.csr_length_report.csv
#          </pattern>
#          <pattern id="csr_chain" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.csr_chain.xlsx
#          </pattern>
#          <pattern id="jtag_sequence" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.jtag_sequence.xlsx
#          </pattern>
#          <pattern id="config_io_spec" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.config_io_spec.xlsx
#          </pattern>
#          <pattern id="cb_hw" mimetype="text/tab-separated-values">
#            &ip_name;/devprog/&cell_name;.cb_hw.tsv
#          </pattern>
#          <pattern id="dfm" mimetype="text/tab-separated-values">
#            &ip_name;/devprog/&cell_name;.dfm.tsv
#          </pattern>
#          <pattern id="global_routing_master" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.global_routing_master.xlsx
#          </pattern>
#          <pattern id="io_hps_post" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.io_hps_post.xlsx
#          </pattern>
#          <pattern id="dras_requirement" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.dras_requirement.xlsx
#          </pattern>
#          <pattern id="rowclk_reach" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprog/&cell_name;.rowclk_reach.xlsx
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 37800
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('aux_eram.csv', id_='aux_eram')
#        self._addPattern('csr_length_report.csv', id_='csr_length_report')
#        self._addPattern('csr_chain.xlsx', id_='csr_chain')
#        self._addPattern('jtag_sequence.xlsx', id_='jtag_sequence')
#        self._addPattern('config_io_spec.xlsx', id_='config_io_spec')
#        self._addPattern('cb_hw.tsv', id_='cb_hw')
#        self._addPattern('dfm.tsv', id_='dfm')
#        self._addPattern('global_routing_master.xlsx', id_='global_routing_master')
#        self._addPattern('io_hps_post.xlsx', id_='io_hps_post')
#        self._addPattern('dras_requirement.xlsx', id_='dras_requirement')
#        self._addPattern('rowclk_reach.xlsx', id_='rowclk_reach')
#        self._addProducer("PD-ICD")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _DEVPROGMISC(self):
#        '''Device independent configuration support files.
#
#        >>> t = Template('DEVPROGMISC')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="99014" id="DEVPROGMISC">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/devprogmisc/releasenotes.docx
#          </pattern>
#          <pattern id="global_reset_usage_guidelines" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprogmisc/&cell_name;.global_reset_usage_guidelines.xlsx
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 99014
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('global_reset_usage_guidelines.xlsx',
#                         id_='global_reset_usage_guidelines')
#        self._addProducer("PD-ICD")
#        self._addConsumer("SVT")
#
#    def _DFT(self):
#        '''Design for test (DFT) insertion flow netlist and constraint output
#        files.
#
#        >>> t = Template('DFT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="109544" id="DFT">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/dft/results/&ip_name;.dft.filelist
#          </filelist>
#          <filelist id="sdc_filelist">
#            &ip_name;/dft/results/&ip_name;.sdc.filelist
#          </filelist>
#          <pattern id="scandef">
#            &ip_name;/dft/results/&cell_name;.dft.scandef
#          </pattern>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 109544
#        self._isReady = True
#
#        dirName = os.path.join(self._idlower, 'results')
#        self._addFilelistWithWorkingDir(dirName, '{}.{}.filelist'.format(self._ipName,
#                                                                          self._idlower))
#        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._ipName),
#                                        id_='sdc_filelist')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.scandef', id_='scandef')
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#
    def _DFTDSM(self):
        '''Spyglass DFT is used to detect any scanability, testability or coverage
           issues at RTL level. SpyGlass DFT tool is used to check on the RTL in
           all ASIC IPs before synthesis. Deliverables are constraint (SGDC),
           filelist, report file and waiver. It enables early detection of potential
           testability issues which can be addressed at the earlier stages of the design cycle.
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/DFTDSM_Definition.docx

        >>> t = Template('DFTDSM')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="216062" id="DFTDSM">
          <description> ... </description>
          <filelist id="filelist">
            &ip_name;/dftdsm/&cell_name;.f
          </filelist>
          <pattern id="rpt">
            &ip_name;/dftdsm/reports/&cell_name;.dft_stuckat.moresimple.rpt
          </pattern>
          <pattern id="stuck">
            &ip_name;/dftdsm/reports/&cell_name;.dft_stuckat.stuck_at_coverage.rpt
          </pattern>
          <pattern id="atspeed">
            &ip_name;/dftdsm/reports/&cell_name;.dft_atspeed.moresimple.rpt
          </pattern>
          <pattern id="atspeed_tran">
            &ip_name;/dftdsm/reports/&cell_name;.dft_atspeed.transition_coverage.rpt
          </pattern>
          <pattern id="sgdc">
            &ip_name;/dftdsm/&cell_name;.sgdc
          </pattern>
          <pattern id="swl" minimum="0">
            &ip_name;/dftdsm/&cell_name;.swl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-IP"/>
        </template> '
        '''
        self._caseid = 216062
        self._isReady = True


        dirName = os.path.join(self._idlower)
        self._addFilelistWithWorkingDir(dirName, '{}.f'.format(self._cellName),
                                        id_='filelist')

        dirName = os.path.join(self._idlower, 'reports')
        self._addPatternWithWorkingDir(dirName, 'dft_stuckat.moresimple.rpt', id_='rpt')
        self._addPatternWithWorkingDir(dirName, 'dft_stuckat.stuck_at_coverage.rpt', id_='stuck')
        self._addPatternWithWorkingDir(dirName, 'dft_atspeed.moresimple.rpt', id_='atspeed')
        self._addPatternWithWorkingDir(dirName, 'dft_atspeed.transition_coverage.rpt', id_='atspeed_tran')

        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, 'sgdc', id_='sgdc')
        self._addPatternWithWorkingDir(dirName, 'swl', id_='swl', minimum="0")

        self._addProducer("ICD-IP")
        self._addConsumer("ICD-IP")

#    def _DIMTABLE(self):
#        '''Global routing line column offset table.  Used by ITG EFA tool.
#
#        >>> t = Template('DIMTABLE')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28525" id="DIMTABLE">
#          <description> ... </description>
#          <pattern id="file" mimetype="text/tab-separated-values">
#            &ip_name;/dimtable/&cell_name;.dimtable.tsv
#          </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28525
#        self._isReady = True
#        self._addPattern("dimtable.tsv")
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("TE")
#
    def _DV(self):
        '''Desirn verification. This deliverable contains results from all IP, Subsystem and Chip level verification.

           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/DV_Definition.docx

        >>> t = Template('DV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="208253" id="DV">
          <description> ... </description>
          <pattern id="wkset">
            &ip_name;/dv/*.&ip_name;.*.workset
          </pattern>
          <pattern id="file" mimetype="text/xml">
            &ip_name;/dv/audit/audit.&cell_name;.dv.xml
          </pattern>
          <producer id="IP-DV"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 208253
        self._isReady = True

        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, '*.{}.*.workset'.format(self._ipName), id_='wkset', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'audit')
        self._addPatternWithWorkingDir(dirName, 'audit.{}.dv.xml'.format(self._cellName), id_='file', prependTopCellName=False)
                                       
        self._addProducer("IP-DV")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")

#    def _FCMW(self):
#        '''Level 0 Connected ICC Milkyway database.  
#
#        >>> t = Template('FCMW')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="93737" id="FCMW">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcmw/releasenotes.docx
#          </pattern>
#          <milkyway id="mw_logical" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/fcmw/logical/&ip_name;__fcmw
#            </libpath>
#            <lib>
#              &ip_name;__fcmw
#            </lib>
#          </milkyway>
#          <milkyway id="mw_physical" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/fcmw/physical/&ip_name;__fcmw
#            </libpath>
#            <lib>
#              &ip_name;__fcmw
#            </lib>
#          </milkyway>
#          <producer id="PD-ICD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 93737
#        self._isReady = True
#
#        self._addReleaseNotes()
#        # Was:
##        self._addMilkywayCell(self._cellName, 'CEL', suffix='')
#        # As per FB 128763, became:
#        dirName = os.path.join(self._idlower, 'logical')
#        self._addMilkywayCellWithWorkingDir(dirName, id_='mw_logical')
#        dirName = os.path.join(self._idlower, 'physical')
#        self._addMilkywayCellWithWorkingDir(dirName, id_='mw_physical')
#        
#        self._addProducer("PD-ICD")
#        self._addConsumer("LAYOUT")
#    
#    
#    
#    def _FCFLRPLN(self):
#        '''Full chip floorplan.  Floorplan information includes Row & column
#        count for the CORE IPs IP logical dimension (address and data width)
#        IP placement information Redundancy location and information.
#
#        >>> t = Template('FCFLRPLN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="25211" id="FCFLRPLN">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcflrpln/releasenotes.docx
#          </pattern>
#          <pattern id="flat_floorplan_def">
#            &ip_name;/fcflrpln/flat/def/&cell_name;.flat_floorplan.def
#          </pattern>
#          <pattern id="flat_floorplan_verilog">
#            &ip_name;/fcflrpln/flat/verilog/&cell_name;.flat_floorplan.v
#          </pattern>
#          <pattern id="flat_attribute_setting" mimetype="application/x-tcl">
#            &ip_name;/fcflrpln/flat/attributes/&cell_name;.flat_attribute_setting.tcl
#          </pattern>
#          <pattern id="flat_attribute_setting_xml" mimetype="text/xml">
#            &ip_name;/fcflrpln/&cell_name;.flat_attribute_setting.xml
#          </pattern>
#          <pattern id="flat_floorplan_spreadsheet" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fcflrpln/flat/&cell_name;.flat_floorplan.xlsx
#          </pattern>
#          <milkyway id="mwLib" mimetype="application/octet-stream"> 
#              <libpath> 
#                  &ip_name;/fcflrpln/&ip_name; 
#              </libpath> 
#              <lib> 
#                  &ip_name;
#              </lib>
#              <cell>
#                  &cell_name;
#              </cell>
#              <view>
#                  CEL
#              </view>
#          </milkyway>          
#          <producer id="LAYOUT"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="PACKAGING"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 25211
#        self._isReady = True
#        self._addReleaseNotes()
#        workingDirName = os.path.join(self._idlower, 'flat', 'def')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_floorplan.def', 
#                                       id_='flat_floorplan_def')
#        
#        workingDirName = os.path.join(self._idlower, 'flat', 'verilog')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_floorplan.v', 
#                                       id_='flat_floorplan_verilog')
#        
#        workingDirName = os.path.join(self._idlower, 'flat', 'attributes')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_attribute_setting.tcl', 
#                                       id_='flat_attribute_setting')
#
#        self._addPattern('flat_attribute_setting.xml', id_='flat_attribute_setting_xml')
#        
#        
#        workingDirName = os.path.join(self._idlower, 'flat')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_floorplan.xlsx', 
#                                       id_='flat_floorplan_spreadsheet')
#        
#        self._addMilkywayCell(suffix='', cellName=self._cellName, viewName='CEL')
#
#        # Start BugzId:130360
#        self._addProducer("LAYOUT")
#        # End BugzId:130360
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("PACKAGING")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _FCHIERFLRPLN(self):
#        '''Hierarchical full chip floorplan.
#
#        >>> t = Template('FCHIERFLRPLN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="86041" id="FCHIERFLRPLN">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fchierflrpln/releasenotes.docx
#          </pattern>
#          <pattern id="attribute_setting" mimetype="text/xml">
#            &ip_name;/fchierflrpln/&cell_name;.attribute_setting.xml
#          </pattern>
#          <pattern id="version">
#            &ip_name;/fchierflrpln/version.txt
#          </pattern>
#          <pattern id="hierarchy_tmpl" mimetype="text/x-python">
#            &ip_name;/fchierflrpln/&cell_name;.hierarchy_tmpl.py
#          </pattern>
#          <pattern id="tile_list" mimetype="text/csv">
#            &ip_name;/fchierflrpln/&cell_name;.tile_list.csv
#          </pattern>
#          <pattern id="flat_floorplan" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fchierflrpln/&cell_name;.flat_floorplan.xlsx
#          </pattern>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/fchierflrpln/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view>
#              CEL 
#            </view>
#          </milkyway>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <producer id="LAYOUT"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 86041
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addMilkywayCell(self._cellName, 'CEL', suffix='')
#        self._addPattern('attribute_setting.xml', id_='attribute_setting')
#        self._addPattern('version.txt', prependTopCellName=False, id_='version')
#        self._addPattern('hierarchy_tmpl.py', id_='hierarchy_tmpl')
#        self._addPattern('tile_list.csv', id_='tile_list')
#        self._addPattern('flat_floorplan.xlsx', id_='flat_floorplan')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        # Start BugzId:130360
#        self._addProducer("LAYOUT")
#        # End BugzId:130360
#        self._addConsumer("PD-ICD")
#
#    def _FCPNETLIST(self):
#        '''Top level fullchip netlist and full chip attributes for use in
#        physical design (FCVNETLIST is for verification).
#
#        >>> t = Template('FCPNETLIST')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="36917" id="FCPNETLIST">
#          <description> ... </description>
#          <filelist id="fullcore">
#            &ip_name;/fcpnetlist/&ip_name;.fcpnetlist.filelist
#          </filelist>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcpnetlist/releasenotes.docx
#          </pattern>
#          <pattern id="attributes" mimetype="text/xml">
#            &ip_name;/fcpnetlist/&cell_name;.attributes.xml
#          </pattern>
#          <pattern id="config" mimetype="text/xml">
#            &ip_name;/fcpnetlist/config.xml
#          </pattern>
#          <pattern id="file">
#            &ip_name;/fcpnetlist/&cell_name;.fcpnetlist.v
#          </pattern>
#          <pattern id="params">
#            &ip_name;/fcpnetlist/&cell_name;.params.v
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 36917
#        self._isReady = True
#        self._addFilelist(id_="fullcore")
#        self._addReleaseNotes()
#        self._addPattern('attributes.xml', id_="attributes")
#        self._addPattern('config.xml', id_="config", prependTopCellName=False)
#        self._addPattern(self._idlower + '.v')
#        self._addPattern('params.v', id_="params")
#        self._addProducer("PD-ICD")
#        self._addConsumer("LAYOUT")
#        
#    def _FCPWRMOD(self):
#        '''Full chip power model.
#
#        >>> t = Template('FCPWRMOD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="86952" id="FCPWRMOD">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcpwrmod/releasenotes.docx
#          </pattern>
#          <pattern id="file">
#            &ip_name;/fcpwrmod/...
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 86952
#        self._isReady = True
#        self._addReleaseNotes()
##        self._addPattern(self._idlower + '.v') # See 86952, 6/19.13
#        self._addPattern('...', prependTopCellName=False)
#        self._addProducer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#

    def _FCPWRMOD(self):
        '''Full chip power model.
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/FCPWRMOD_Definition.docx

        >>> t = Template('FCPWRMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209040" id="FCPWRMOD">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/fcpwrmod/...
          </pattern>
          <producer id="ICD-IP"/>
          <producer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 209040
        self._isReady = True
        self._addPattern('...', prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addProducer("ICD-PD")

#    def _FCRBA(self):
#        '''Fullchip RBA - Ram Bit Address at fullchip level. This has the
#        information for every configuration bit location and the function it
#        controls in the entire chip.
#
#        >>> t = Template('FCRBA')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE 
#        '<?xml version="1.0" encoding="utf-8"?>
#          <template caseid="26827" id="FCRBA">
#            <description>
#              Fullchip RBA - Ram Bit Address at fullchip level. This has the information for every configuration bit location and the function it controls in the entire chip.
#            </description>
#            <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#              &ip_name;/fcrba/releasenotes.docx
#            </pattern>
#            <pattern id="rba">
#              &ip_name;/fcrba/&cell_name;.rba
#            </pattern>
#            <pattern id="expanded_mcf_fcl">
#              &ip_name;/fcrba/&cell_name;.expanded_mcf_fcl.txt
#            </pattern>
#            <pattern id="flat_connectivity">
#              &ip_name;/fcrba/&cell_name;.flat_connectivity.txt
#            </pattern>
#            <pattern id="inbf_flat_connectivity_merge_mcf">
#              &ip_name;/fcrba/&cell_name;.inbf_flat_connectivity_merge_mcf.txt
#            </pattern>
#            <pattern id="borrowed">
#              &ip_name;/fcrba/&cell_name;.borrowed.rba
#            </pattern>
#            <pattern id="routing_gz">
#              &ip_name;/fcrba/&cell_name;.routing.rba.gz
#            </pattern>
#            <pattern id="rif">
#              &ip_name;/fcrba/&cell_name;.rif.txt
#            </pattern>
#            <pattern id="red_crams" mimetype="text/tab-separated-values" minimum="0">
#              &ip_name;/fcrba/&cell_name;.red_crams.tsv
#            </pattern>
#            <pattern id="feedthroughs" mimetype="text/tab-separated-values">
#              &ip_name;/fcrba/&cell_name;.feedthroughs.tsv
#            </pattern>
#            <producer id="PD-ICD"/>
#            <consumer id="SOFTWARE-IPD"/>
#            <consumer id="SVT"/>
#            <consumer id="TE"/>
#            <renamer>
#              unknownRenamer
#            </renamer>
#          </template> '
#        '''
#        self._caseid = 26827
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('rba', id_='rba')
##        self._addPattern('mcf_fcl.txt', id_='mcf_fcl') # http://fogbugz.altera.com/default.asp?126893
#        self._addPattern('expanded_mcf_fcl.txt', id_='expanded_mcf_fcl')
#        #self._addPattern('inbf_expanded_mcf_fcl.txt', id_='inbf_expanded_mcf_fcl')
#        self._addPattern('flat_connectivity.txt', id_='flat_connectivity')
#        self._addPattern('inbf_flat_connectivity_merge_mcf.txt', id_='inbf_flat_connectivity_merge_mcf')
#        self._addPattern('borrowed.rba', id_='borrowed')
#        self._addPattern('routing.rba.gz', id_='routing_gz')
#        self._addPattern('rif.txt', id_='rif')
#        self._addPattern('red_crams.tsv', id_='red_crams', minimum = 0)
##        self._addPattern('edcrc.rba', id_='edcrc') # See http:fogbugz.altera.com/default.asp?126893
#        self._addPattern('feedthroughs.tsv', id_='feedthroughs')
#        self._addProducer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#        
#    def _FCTIMEMOD(self):
#        '''Clock uncertainty between subsystems.
#
#        >>> t = Template('FCTIMEMOD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="172554" id="FCTIMEMOD">
#          <description> ... </description>
#          <pattern id="hssi_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/hssi.core.cu.xlsx
#          </pattern>
#          <pattern id="io_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/io.core.cu.xlsx
#          </pattern>
#          <pattern id="core_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/core.core.cu.xlsx
#          </pattern>
#          <pattern id="hps_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/hps.core.cu.xlsx
#          </pattern>
#          <pattern id="hps_io" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/hps.io.cu.xlsx
#          </pattern>
#          <pattern id="acumen" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/acumen.cu.xlsx
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 172554
#        self._isReady = True
#        self._addPattern("hssi.core.cu.xlsx", id_='hssi_core', prependTopCellName=False)
#        self._addPattern("io.core.cu.xlsx", id_='io_core', prependTopCellName=False)
#        self._addPattern("core.core.cu.xlsx", id_='core_core', prependTopCellName=False)
#        # Does not exist in NF5
#        self._addPattern("hps.core.cu.xlsx", id_='hps_core', prependTopCellName=False)
#        # Does not exist in NF5
#        self._addPattern("hps.io.cu.xlsx", id_='hps_io', prependTopCellName=False)
#        self._addPattern("acumen.cu.xlsx", id_='acumen', prependTopCellName=False)
#        self._addProducer("PD-ICD")
#        self._addConsumer("PD-ICD")
#
#    def _FCV(self):
#        '''Full chip verification testbench files and testcases.
#
#        >>> t = Template('FCV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="44664" id="FCV">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/fcv/...
#          </pattern>
#          <producer id="SVT"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 44664
#        self._isReady = True
#        self._addPattern('...', prependTopCellName=False)
#        self._addProducer("SVT")
#        self._addConsumer("SVT")
#
#    def _FCVNETLIST(self):
#        '''Top level full chip logical netlist and full chip attributes for use
#        in verification (FCPNETLIST is for physical design).
#
#        >>> t = Template('FCVNETLIST')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="36918" id="FCVNETLIST">
#          <description> ... </description>
#          <filelist id="fullcore">
#            &ip_name;/fcvnetlist/&ip_name;.fcvnetlist.filelist
#          </filelist>
#          <filelist id="coreless" minimum="0">
#            &ip_name;/fcvnetlist/&ip_name;.fcvnetlist.coreless.filelist
#          </filelist>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcvnetlist/releasenotes.docx
#          </pattern>
#          <pattern id="attributes" mimetype="text/xml">
#            &ip_name;/fcvnetlist/&cell_name;.attributes.xml
#          </pattern>
#          <pattern id="config" mimetype="text/xml">
#            &ip_name;/fcvnetlist/config.xml
#          </pattern>
#          <pattern id="netlist_buffer">
#            &ip_name;/fcvnetlist/&cell_name;.lnetlist.buffers.v
#          </pattern>
#          <pattern id="netlist_coreless" minimum="0">
#            &ip_name;/fcvnetlist/&cell_name;.lnetlist.coreless.v
#          </pattern>
#          <pattern id="netlist">
#            &ip_name;/fcvnetlist/&cell_name;.lnetlist.v
#          </pattern>
#          <pattern id="params_coreless">
#            &ip_name;/fcvnetlist/&cell_name;.params.coreless.v
#          </pattern>
#          <pattern id="params">
#            &ip_name;/fcvnetlist/&cell_name;.params.v
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 36918
#        self._isReady = True
#        self._addFilelist(id_='fullcore')
#        self._addFilelist(id_='coreless',
#                          minimum = 0,
#                          fileName='{}.{}.coreless.filelist'.format(self._ipName,
#                                                                    self._idlower))
#        self._addReleaseNotes()
#        self._addPattern('attributes.xml', id_="attributes")
#        self._addPattern('config.xml', id_="config", prependTopCellName=False)
#        self._addPattern('lnetlist.buffers.v', id_="netlist_buffer")
#        self._addPattern('lnetlist.coreless.v', id_="netlist_coreless", minimum=0)
#        self._addPattern('lnetlist.v', id_="netlist")
#        self._addPattern('params.coreless.v', id_="params_coreless")
#        self._addPattern('params.v', id_="params")
#        self._addProducer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#        # filelist eliminated as per http://fogbugz/default.asp?115843 - R.G.
#
#    def _FIRMWARE(self):
#        '''C code used by embedded microprocessors for calibration.
#
#        >>> t = Template('FIRMWARE')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="86550" id="FIRMWARE">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/firmware/c_code/&ip_name;.firmware.filelist
#          </filelist>
#          <pattern id="makefile">
#            &ip_name;/firmware/c_code/Makefile
#          </pattern>
#          <pattern id="sopcinfo">
#            &ip_name;/firmware/sopcinfo/&cell_name;.sopcinfo
#          </pattern>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 86550
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'c_code')
#        self._addFilelistWithWorkingDir(dirName)
#        self._addPatternWithWorkingDir(dirName, 'Makefile', id_="makefile",
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'sopcinfo')
#        self._addPatternWithWorkingDir(dirName, 'sopcinfo', id_='sopcinfo')
#        
#
#    def _FOUNDRY(self):
#        '''Final data delivered to foundry for fabrication.
#
#        >>> t = Template('FOUNDRY')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="136611" id="FOUNDRY">
#          <description> ... </description>
#          <pattern id="gdz" mimetype="application/octet-stream">
#            &ip_name;/foundry/gds/&cell_name;.gds.gdz
#          </pattern>
#          <pattern id="gdz_gpg" mimetype="application/gpg">
#            &ip_name;/foundry/gds/&cell_name;.gds.gdz.gpg
#          </pattern>
#          <pattern id="torf" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/foundry/docs/&cell_name;.torf.xlsx
#          </pattern>
#          <pattern id="iplist">
#            &ip_name;/foundry/docs/&cell_name;.iplist.txt
#          </pattern>
#          <producer id="DM"/>
#          <consumer id="DM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 136611
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'gds')
#        self._addPatternWithWorkingDir(dirName, 'gds.gdz', id_="gdz")
#        self._addPatternWithWorkingDir(dirName, 'gds.gdz.gpg', id_="gdz_gpg")
#        dirName = os.path.join(self._idlower, 'docs')
#        self._addPatternWithWorkingDir(dirName, 'torf.xlsx', id_="torf")
#        self._addPatternWithWorkingDir(dirName, 'iplist.txt', id_="iplist")
#        self._addProducer("DM")
#        self._addConsumer("DM")
#        
#    def _FUNCRBA(self):
#        '''Ram Bit Address, the coordinate of configuration bits and the
#        function it controls.
#
#        >>> t = Template('FUNCRBA')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="24161" id="FUNCRBA">
#          <description> ... </description>
#          <pattern id="functional">
#            &ip_name;/funcrba/&cell_name;.functional.rba
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 24161
#        self._isReady = True
#        self._addPattern("functional.rba", id_='functional')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _FV(self):
#        '''Formal verification results for custom IP.
#
#        >>> t = Template('FV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="87822" id="FV">
#          <description> ... </description>
#          <pattern id="file" minimum="0">
#            &ip_name;/fv/results/...
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 87822
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'results')
#        self._addPatternWithWorkingDir(dirName, "...", minimum=0,
#                                       prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#
#    def _FVDFT(self):
#        '''Formal verification reports for synthesized gate netlist to
#        DFT-inserted gate netlist comparison.
#
#        >>> t = Template('FVDFT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="109544" id="FVDFT">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/fvdft/results/&cell_name;.fvdft.rpt
#          </pattern>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 109544
#        self._isReady = True
#
#        dirName = os.path.join(self._idlower, 'results')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.rpt')
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 37800
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('aux_eram.csv', id_='aux_eram')
#        self._addPattern('csr_length_report.csv', id_='csr_length_report')
#        self._addPattern('csr_chain.xlsx', id_='csr_chain')
#        self._addPattern('jtag_sequence.xlsx', id_='jtag_sequence')
#        self._addPattern('config_io_spec.xlsx', id_='config_io_spec')
#        self._addPattern('cb_hw.tsv', id_='cb_hw')
#        self._addPattern('dfm.tsv', id_='dfm')
#        self._addPattern('global_routing_master.xlsx', id_='global_routing_master')
#        self._addPattern('io_hps_post.xlsx', id_='io_hps_post')
#        self._addPattern('dras_requirement.xlsx', id_='dras_requirement')
#        self._addPattern('rowclk_reach.xlsx', id_='rowclk_reach')
#        self._addProducer("PD-ICD")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _DEVPROGMISC(self):
#        '''Device independent configuration support files.
#
#        >>> t = Template('DEVPROGMISC')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="99014" id="DEVPROGMISC">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/devprogmisc/releasenotes.docx
#          </pattern>
#          <pattern id="global_reset_usage_guidelines" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/devprogmisc/&cell_name;.global_reset_usage_guidelines.xlsx
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 99014
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('global_reset_usage_guidelines.xlsx',
#                         id_='global_reset_usage_guidelines')
#        self._addProducer("PD-ICD")
#        self._addConsumer("SVT")
#
#    def _DFT(self):
#        '''Design for test (DFT) insertion flow netlist and constraint output
#        files.
#
#        >>> t = Template('DFT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="109544" id="DFT">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/dft/results/&ip_name;.dft.filelist
#          </filelist>
#          <filelist id="sdc_filelist">
#            &ip_name;/dft/results/&ip_name;.sdc.filelist
#          </filelist>
#          <pattern id="scandef">
#            &ip_name;/dft/results/&cell_name;.dft.scandef
#          </pattern>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 109544
#        self._isReady = True
#
#        dirName = os.path.join(self._idlower, 'results')
#        self._addFilelistWithWorkingDir(dirName, '{}.{}.filelist'.format(self._ipName,
#                                                                          self._idlower))
#        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._ipName),
#                                        id_='sdc_filelist')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.scandef', id_='scandef')
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#
#    def _DIMTABLE(self):
#        '''Global routing line column offset table.  Used by ITG EFA tool.
#
#        >>> t = Template('DIMTABLE')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28525" id="DIMTABLE">
#          <description> ... </description>
#          <pattern id="file" mimetype="text/tab-separated-values">
#            &ip_name;/dimtable/&cell_name;.dimtable.tsv
#          </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28525
#        self._isReady = True
#        self._addPattern("dimtable.tsv")
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("TE")
#
#    def _FCMW(self):
#        '''Level 0 Connected ICC Milkyway database.  
#
#        >>> t = Template('FCMW')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="93737" id="FCMW">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcmw/releasenotes.docx
#          </pattern>
#          <milkyway id="mw_logical" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/fcmw/logical/&ip_name;__fcmw
#            </libpath>
#            <lib>
#              &ip_name;__fcmw
#            </lib>
#          </milkyway>
#          <milkyway id="mw_physical" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/fcmw/physical/&ip_name;__fcmw
#            </libpath>
#            <lib>
#              &ip_name;__fcmw
#            </lib>
#          </milkyway>
#          <producer id="PD-ICD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 93737
#        self._isReady = True
#
#        self._addReleaseNotes()
#        # Was:
##        self._addMilkywayCell(self._cellName, 'CEL', suffix='')
#        # As per FB 128763, became:
#        dirName = os.path.join(self._idlower, 'logical')
#        self._addMilkywayCellWithWorkingDir(dirName, id_='mw_logical')
#        dirName = os.path.join(self._idlower, 'physical')
#        self._addMilkywayCellWithWorkingDir(dirName, id_='mw_physical')
#        
#        self._addProducer("PD-ICD")
#        self._addConsumer("LAYOUT")
#    
#    
#    
#    def _FCFLRPLN(self):
#        '''Full chip floorplan.  Floorplan information includes Row & column
#        count for the CORE IPs IP logical dimension (address and data width)
#        IP placement information Redundancy location and information.
#
#        >>> t = Template('FCFLRPLN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="25211" id="FCFLRPLN">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcflrpln/releasenotes.docx
#          </pattern>
#          <pattern id="flat_floorplan_def">
#            &ip_name;/fcflrpln/flat/def/&cell_name;.flat_floorplan.def
#          </pattern>
#          <pattern id="flat_floorplan_verilog">
#            &ip_name;/fcflrpln/flat/verilog/&cell_name;.flat_floorplan.v
#          </pattern>
#          <pattern id="flat_attribute_setting" mimetype="application/x-tcl">
#            &ip_name;/fcflrpln/flat/attributes/&cell_name;.flat_attribute_setting.tcl
#          </pattern>
#          <pattern id="flat_attribute_setting_xml" mimetype="text/xml">
#            &ip_name;/fcflrpln/&cell_name;.flat_attribute_setting.xml
#          </pattern>
#          <pattern id="flat_floorplan_spreadsheet" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fcflrpln/flat/&cell_name;.flat_floorplan.xlsx
#          </pattern>
#          <milkyway id="mwLib" mimetype="application/octet-stream"> 
#              <libpath> 
#                  &ip_name;/fcflrpln/&ip_name; 
#              </libpath> 
#              <lib> 
#                  &ip_name;
#              </lib>
#              <cell>
#                  &cell_name;
#              </cell>
#              <view>
#                  CEL
#              </view>
#          </milkyway>          
#          <producer id="LAYOUT"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="PACKAGING"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 25211
#        self._isReady = True
#        self._addReleaseNotes()
#        workingDirName = os.path.join(self._idlower, 'flat', 'def')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_floorplan.def', 
#                                       id_='flat_floorplan_def')
#        
#        workingDirName = os.path.join(self._idlower, 'flat', 'verilog')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_floorplan.v', 
#                                       id_='flat_floorplan_verilog')
#        
#        workingDirName = os.path.join(self._idlower, 'flat', 'attributes')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_attribute_setting.tcl', 
#                                       id_='flat_attribute_setting')
#
#        self._addPattern('flat_attribute_setting.xml', id_='flat_attribute_setting_xml')
#        
#        
#        workingDirName = os.path.join(self._idlower, 'flat')
#        self._addPatternWithWorkingDir(workingDirName, 
#                                       'flat_floorplan.xlsx', 
#                                       id_='flat_floorplan_spreadsheet')
#        
#        self._addMilkywayCell(suffix='', cellName=self._cellName, viewName='CEL')
#
#        # Start BugzId:130360
#        self._addProducer("LAYOUT")
#        # End BugzId:130360
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("PACKAGING")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _FCHIERFLRPLN(self):
#        '''Hierarchical full chip floorplan.
#
#        >>> t = Template('FCHIERFLRPLN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="86041" id="FCHIERFLRPLN">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fchierflrpln/releasenotes.docx
#          </pattern>
#          <pattern id="attribute_setting" mimetype="text/xml">
#            &ip_name;/fchierflrpln/&cell_name;.attribute_setting.xml
#          </pattern>
#          <pattern id="version">
#            &ip_name;/fchierflrpln/version.txt
#          </pattern>
#          <pattern id="hierarchy_tmpl" mimetype="text/x-python">
#            &ip_name;/fchierflrpln/&cell_name;.hierarchy_tmpl.py
#          </pattern>
#          <pattern id="tile_list" mimetype="text/csv">
#            &ip_name;/fchierflrpln/&cell_name;.tile_list.csv
#          </pattern>
#          <pattern id="flat_floorplan" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fchierflrpln/&cell_name;.flat_floorplan.xlsx
#          </pattern>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/fchierflrpln/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view>
#              CEL 
#            </view>
#          </milkyway>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <producer id="LAYOUT"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 86041
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addMilkywayCell(self._cellName, 'CEL', suffix='')
#        self._addPattern('attribute_setting.xml', id_='attribute_setting')
#        self._addPattern('version.txt', prependTopCellName=False, id_='version')
#        self._addPattern('hierarchy_tmpl.py', id_='hierarchy_tmpl')
#        self._addPattern('tile_list.csv', id_='tile_list')
#        self._addPattern('flat_floorplan.xlsx', id_='flat_floorplan')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        # Start BugzId:130360
#        self._addProducer("LAYOUT")
#        # End BugzId:130360
#        self._addConsumer("PD-ICD")
#
#    def _FCPNETLIST(self):
#        '''Top level fullchip netlist and full chip attributes for use in
#        physical design (FCVNETLIST is for verification).
#
#        >>> t = Template('FCPNETLIST')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="36917" id="FCPNETLIST">
#          <description> ... </description>
#          <filelist id="fullcore">
#            &ip_name;/fcpnetlist/&ip_name;.fcpnetlist.filelist
#          </filelist>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcpnetlist/releasenotes.docx
#          </pattern>
#          <pattern id="attributes" mimetype="text/xml">
#            &ip_name;/fcpnetlist/&cell_name;.attributes.xml
#          </pattern>
#          <pattern id="config" mimetype="text/xml">
#            &ip_name;/fcpnetlist/config.xml
#          </pattern>
#          <pattern id="file">
#            &ip_name;/fcpnetlist/&cell_name;.fcpnetlist.v
#          </pattern>
#          <pattern id="params">
#            &ip_name;/fcpnetlist/&cell_name;.params.v
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 36917
#        self._isReady = True
#        self._addFilelist(id_="fullcore")
#        self._addReleaseNotes()
#        self._addPattern('attributes.xml', id_="attributes")
#        self._addPattern('config.xml', id_="config", prependTopCellName=False)
#        self._addPattern(self._idlower + '.v')
#        self._addPattern('params.v', id_="params")
#        self._addProducer("PD-ICD")
#        self._addConsumer("LAYOUT")
#        
#    def _FCPWRMOD(self):
#        '''Full chip power model.
#
#        >>> t = Template('FCPWRMOD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="86952" id="FCPWRMOD">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcpwrmod/releasenotes.docx
#          </pattern>
#          <pattern id="file">
#            &ip_name;/fcpwrmod/...
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 86952
#        self._isReady = True
#        self._addReleaseNotes()
##        self._addPattern(self._idlower + '.v') # See 86952, 6/19.13
#        self._addPattern('...', prependTopCellName=False)
#        self._addProducer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#
#    def _FCRBA(self):
#        '''Fullchip RBA - Ram Bit Address at fullchip level. This has the
#        information for every configuration bit location and the function it
#        controls in the entire chip.
#
#        >>> t = Template('FCRBA')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE 
#        '<?xml version="1.0" encoding="utf-8"?>
#          <template caseid="26827" id="FCRBA">
#            <description>
#              Fullchip RBA - Ram Bit Address at fullchip level. This has the information for every configuration bit location and the function it controls in the entire chip.
#            </description>
#            <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#              &ip_name;/fcrba/releasenotes.docx
#            </pattern>
#            <pattern id="rba">
#              &ip_name;/fcrba/&cell_name;.rba
#            </pattern>
#            <pattern id="expanded_mcf_fcl">
#              &ip_name;/fcrba/&cell_name;.expanded_mcf_fcl.txt
#            </pattern>
#            <pattern id="flat_connectivity">
#              &ip_name;/fcrba/&cell_name;.flat_connectivity.txt
#            </pattern>
#            <pattern id="inbf_flat_connectivity_merge_mcf">
#              &ip_name;/fcrba/&cell_name;.inbf_flat_connectivity_merge_mcf.txt
#            </pattern>
#            <pattern id="borrowed">
#              &ip_name;/fcrba/&cell_name;.borrowed.rba
#            </pattern>
#            <pattern id="routing_gz">
#              &ip_name;/fcrba/&cell_name;.routing.rba.gz
#            </pattern>
#            <pattern id="rif">
#              &ip_name;/fcrba/&cell_name;.rif.txt
#            </pattern>
#            <pattern id="red_crams" mimetype="text/tab-separated-values" minimum="0">
#              &ip_name;/fcrba/&cell_name;.red_crams.tsv
#            </pattern>
#            <pattern id="feedthroughs" mimetype="text/tab-separated-values">
#              &ip_name;/fcrba/&cell_name;.feedthroughs.tsv
#            </pattern>
#            <producer id="PD-ICD"/>
#            <consumer id="SOFTWARE-IPD"/>
#            <consumer id="SVT"/>
#            <consumer id="TE"/>
#            <renamer>
#              unknownRenamer
#            </renamer>
#          </template> '
#        '''
#        self._caseid = 26827
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('rba', id_='rba')
##        self._addPattern('mcf_fcl.txt', id_='mcf_fcl') # http://fogbugz.altera.com/default.asp?126893
#        self._addPattern('expanded_mcf_fcl.txt', id_='expanded_mcf_fcl')
#        #self._addPattern('inbf_expanded_mcf_fcl.txt', id_='inbf_expanded_mcf_fcl')
#        self._addPattern('flat_connectivity.txt', id_='flat_connectivity')
#        self._addPattern('inbf_flat_connectivity_merge_mcf.txt', id_='inbf_flat_connectivity_merge_mcf')
#        self._addPattern('borrowed.rba', id_='borrowed')
#        self._addPattern('routing.rba.gz', id_='routing_gz')
#        self._addPattern('rif.txt', id_='rif')
#        self._addPattern('red_crams.tsv', id_='red_crams', minimum = 0)
##        self._addPattern('edcrc.rba', id_='edcrc') # See http:fogbugz.altera.com/default.asp?126893
#        self._addPattern('feedthroughs.tsv', id_='feedthroughs')
#        self._addProducer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#        
#    def _FCTIMEMOD(self):
#        '''Clock uncertainty between subsystems.
#
#        >>> t = Template('FCTIMEMOD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="172554" id="FCTIMEMOD">
#          <description> ... </description>
#          <pattern id="hssi_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/hssi.core.cu.xlsx
#          </pattern>
#          <pattern id="io_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/io.core.cu.xlsx
#          </pattern>
#          <pattern id="core_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/core.core.cu.xlsx
#          </pattern>
#          <pattern id="hps_core" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/hps.core.cu.xlsx
#          </pattern>
#          <pattern id="hps_io" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/hps.io.cu.xlsx
#          </pattern>
#          <pattern id="acumen" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/fctimemod/acumen.cu.xlsx
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 172554
#        self._isReady = True
#        self._addPattern("hssi.core.cu.xlsx", id_='hssi_core', prependTopCellName=False)
#        self._addPattern("io.core.cu.xlsx", id_='io_core', prependTopCellName=False)
#        self._addPattern("core.core.cu.xlsx", id_='core_core', prependTopCellName=False)
#        # Does not exist in NF5
#        self._addPattern("hps.core.cu.xlsx", id_='hps_core', prependTopCellName=False)
#        # Does not exist in NF5
#        self._addPattern("hps.io.cu.xlsx", id_='hps_io', prependTopCellName=False)
#        self._addPattern("acumen.cu.xlsx", id_='acumen', prependTopCellName=False)
#        self._addProducer("PD-ICD")
#        self._addConsumer("PD-ICD")
#
#    def _FCV(self):
#        '''Full chip verification testbench files and testcases.
#
#        >>> t = Template('FCV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="44664" id="FCV">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/fcv/...
#          </pattern>
#          <producer id="SVT"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 44664
#        self._isReady = True
#        self._addPattern('...', prependTopCellName=False)
#        self._addProducer("SVT")
#        self._addConsumer("SVT")
#
#    def _FCVNETLIST(self):
#        '''Top level full chip logical netlist and full chip attributes for use
#        in verification (FCPNETLIST is for physical design).
#
#        >>> t = Template('FCVNETLIST')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="36918" id="FCVNETLIST">
#          <description> ... </description>
#          <filelist id="fullcore">
#            &ip_name;/fcvnetlist/&ip_name;.fcvnetlist.filelist
#          </filelist>
#          <filelist id="coreless" minimum="0">
#            &ip_name;/fcvnetlist/&ip_name;.fcvnetlist.coreless.filelist
#          </filelist>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/fcvnetlist/releasenotes.docx
#          </pattern>
#          <pattern id="attributes" mimetype="text/xml">
#            &ip_name;/fcvnetlist/&cell_name;.attributes.xml
#          </pattern>
#          <pattern id="config" mimetype="text/xml">
#            &ip_name;/fcvnetlist/config.xml
#          </pattern>
#          <pattern id="netlist_buffer">
#            &ip_name;/fcvnetlist/&cell_name;.lnetlist.buffers.v
#          </pattern>
#          <pattern id="netlist_coreless" minimum="0">
#            &ip_name;/fcvnetlist/&cell_name;.lnetlist.coreless.v
#          </pattern>
#          <pattern id="netlist">
#            &ip_name;/fcvnetlist/&cell_name;.lnetlist.v
#          </pattern>
#          <pattern id="params_coreless">
#            &ip_name;/fcvnetlist/&cell_name;.params.coreless.v
#          </pattern>
#          <pattern id="params">
#            &ip_name;/fcvnetlist/&cell_name;.params.v
#          </pattern>
#          <producer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 36918
#        self._isReady = True
#        self._addFilelist(id_='fullcore')
#        self._addFilelist(id_='coreless',
#                          minimum = 0,
#                          fileName='{}.{}.coreless.filelist'.format(self._ipName,
#                                                                    self._idlower))
#        self._addReleaseNotes()
#        self._addPattern('attributes.xml', id_="attributes")
#        self._addPattern('config.xml', id_="config", prependTopCellName=False)
#        self._addPattern('lnetlist.buffers.v', id_="netlist_buffer")
#        self._addPattern('lnetlist.coreless.v', id_="netlist_coreless", minimum=0)
#        self._addPattern('lnetlist.v', id_="netlist")
#        self._addPattern('params.coreless.v', id_="params_coreless")
#        self._addPattern('params.v', id_="params")
#        self._addProducer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#        # filelist eliminated as per http://fogbugz/default.asp?115843 - R.G.
#
#    def _FIRMWARE(self):
#        '''C code used by embedded microprocessors for calibration.
#
#        >>> t = Template('FIRMWARE')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="86550" id="FIRMWARE">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/firmware/c_code/&ip_name;.firmware.filelist
#          </filelist>
#          <pattern id="makefile">
#            &ip_name;/firmware/c_code/Makefile
#          </pattern>
#          <pattern id="sopcinfo">
#            &ip_name;/firmware/sopcinfo/&cell_name;.sopcinfo
#          </pattern>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 86550
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'c_code')
#        self._addFilelistWithWorkingDir(dirName)
#        self._addPatternWithWorkingDir(dirName, 'Makefile', id_="makefile",
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'sopcinfo')
#        self._addPatternWithWorkingDir(dirName, 'sopcinfo', id_='sopcinfo')
#        
#
#    def _FOUNDRY(self):
#        '''Final data delivered to foundry for fabrication.
#
#        >>> t = Template('FOUNDRY')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="136611" id="FOUNDRY">
#          <description> ... </description>
#          <pattern id="gdz" mimetype="application/octet-stream">
#            &ip_name;/foundry/gds/&cell_name;.gds.gdz
#          </pattern>
#          <pattern id="gdz_gpg" mimetype="application/gpg">
#            &ip_name;/foundry/gds/&cell_name;.gds.gdz.gpg
#          </pattern>
#          <pattern id="torf" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/foundry/docs/&cell_name;.torf.xlsx
#          </pattern>
#          <pattern id="iplist">
#            &ip_name;/foundry/docs/&cell_name;.iplist.txt
#          </pattern>
#          <producer id="DM"/>
#          <consumer id="DM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 136611
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'gds')
#        self._addPatternWithWorkingDir(dirName, 'gds.gdz', id_="gdz")
#        self._addPatternWithWorkingDir(dirName, 'gds.gdz.gpg', id_="gdz_gpg")
#        dirName = os.path.join(self._idlower, 'docs')
#        self._addPatternWithWorkingDir(dirName, 'torf.xlsx', id_="torf")
#        self._addPatternWithWorkingDir(dirName, 'iplist.txt', id_="iplist")
#        self._addProducer("DM")
#        self._addConsumer("DM")
#        
#    def _FUNCRBA(self):
#        '''Ram Bit Address, the coordinate of configuration bits and the
#        function it controls.
#
#        >>> t = Template('FUNCRBA')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="24161" id="FUNCRBA">
#          <description> ... </description>
#          <pattern id="functional">
#            &ip_name;/funcrba/&cell_name;.functional.rba
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 24161
#        self._isReady = True
#        self._addPattern("functional.rba", id_='functional')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _FV(self):
#        '''Formal verification results for custom IP.
#
#        >>> t = Template('FV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="87822" id="FV">
#          <description> ... </description>
#          <pattern id="file" minimum="0">
#            &ip_name;/fv/results/...
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 87822
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'results')
#        self._addPatternWithWorkingDir(dirName, "...", minimum=0,
#                                       prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#

    def _FV(self):
        '''FV exists to collect the Formal Equivalence report from an industry
        standard solution like Conformal LEC. There is no database to deliver,
        simply the result file showing the state of compare or equivalence.
        Audit files are also delivered in accordance with the Audit checks
        defined for this deliverable. Specifically this checks the post SYN gate
        level netlist versus the original RTL.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/FV_Definition.docx

        >>> t = Template('FV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209041" id="FV">
          <description> ... </description>
          <pattern id="lec_log">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/&cell_name;.log
          </pattern>
          <pattern id="do">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/&cell_name;.do
          </pattern>
          <pattern id="sum_log">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/&cell_name;_summary.log
          </pattern>
          <pattern id="reporta">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/abort.rpt
          </pattern>
          <pattern id="reportbb">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/black_box.rpt
          </pattern>
          <pattern id="reportb">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/comp_data.rpt
          </pattern>
          <pattern id="reportc">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/design_data.rpt
          </pattern>
          <pattern id="reportd">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/gate_sum.rpt
          </pattern>
          <pattern id="reporte">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/ignored_inputs.rpt
          </pattern>
          <pattern id="reportf">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/ignored_outputs.rpt
          </pattern>
          <pattern id="reportg">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/noneq.rpt
          </pattern>
          <pattern id="reporth">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/pin_constraints.rpt
          </pattern>
          <pattern id="reporti">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/pin_direction.rpt
          </pattern>
          <pattern id="reportj">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/remove_instances.rpt
          </pattern>
          <pattern id="reportk">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/renaming_rule.rpt
          </pattern>
          <pattern id="reportl">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/statistic.rpt
          </pattern>
          <pattern id="reportm">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/stuck_at.rpt
          </pattern>
          <pattern id="reportn">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/unmap_extra.rpt
          </pattern>
          <pattern id="reporto">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/unmap_notmap.rpt
          </pattern>
          <pattern id="reportp">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/unmap_unreach.rpt
          </pattern>
          <pattern id="reportq">
            &ip_name;/fv/rtl_vs_schematic/&cell_name;/reports/user_mapped_point.rpt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 209041
        self._isReady = True
        dirName = os.path.join(self._idlower, 'rtl_vs_schematic', self._cellName)
        self._addPatternWithWorkingDir(dirName, 'log', id_='lec_log')
        self._addPatternWithWorkingDir(dirName, 'do', id_='do')
        self._addPatternWithWorkingDir(dirName, '_summary.log', addDot=False, id_='sum_log')
        dirName = os.path.join(self._idlower, 'rtl_vs_schematic', self._cellName, 'reports')
        self._addPatternWithWorkingDir(dirName, 'abort.rpt', id_='reporta', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'black_box.rpt', id_='reportbb', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'comp_data.rpt', id_='reportb', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'design_data.rpt', id_='reportc', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'gate_sum.rpt', id_='reportd', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'ignored_inputs.rpt', id_='reporte', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'ignored_outputs.rpt', id_='reportf', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'noneq.rpt', id_='reportg', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'pin_constraints.rpt', id_='reporth', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'pin_direction.rpt', id_='reporti', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'remove_instances.rpt', id_='reportj', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'renaming_rule.rpt', id_='reportk', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'statistic.rpt', id_='reportl', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'stuck_at.rpt', id_='reportm', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'unmap_extra.rpt', id_='reportn', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'unmap_notmap.rpt', id_='reporto', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'unmap_unreach.rpt', id_='reportp', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'user_mapped_point.rpt', id_='reportq', prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("TE")

#    def _FVDFT(self):
#        '''Formal verification reports for synthesized gate netlist to
#        DFT-inserted gate netlist comparison.
#
#        >>> t = Template('FVDFT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="109544" id="FVDFT">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/fvdft/results/&cell_name;.fvdft.rpt
#          </pattern>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 109544
#        self._isReady = True
#
#        dirName = os.path.join(self._idlower, 'results')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.rpt')
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")

    def _FVPNR(self):
        '''FVPNR exists to collect the Formal Equivalence report from an
        industry standard solution like Conformal LEC. There is no database to
        deliver, simply the result file showing the state of compare or
        equivalence.

        Audit files are also delivered in accordance with the Audit checks
        defined for this deliverable. Specifically this checks the post PNR gate
        level netlist versus the SYN gate level netlist.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/FVPNR_Definition.docx

        >>> t = Template('FVPNR')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205265" id="FVPNR">
          <description> ... </description>
          <pattern id="lec_log">
            &ip_name;/fvpnr/results/&cell_name;.lec.log
          </pattern>
          <pattern id="abort">
            &ip_name;/fvpnr/results/&cell_name;.abort.rpt
          </pattern>
          <pattern id="black_box">
            &ip_name;/fvpnr/results/&cell_name;.black_box.rpt
          </pattern>
          <pattern id="comp_data">
            &ip_name;/fvpnr/results/&cell_name;.comp_data.rpt
          </pattern>
          <pattern id="design_data">
            &ip_name;/fvpnr/results/&cell_name;.design_data.rpt
          </pattern>
          <pattern id="gate_sum">
            &ip_name;/fvpnr/results/&cell_name;.gate_sum.rpt
          </pattern>
          <pattern id="ignored_inputs">
            &ip_name;/fvpnr/results/&cell_name;.ignored_inputs.rpt
          </pattern>
          <pattern id="ignored_outputs">
            &ip_name;/fvpnr/results/&cell_name;.ignored_outputs.rpt
          </pattern>
          <pattern id="modeling_msg">
            &ip_name;/fvpnr/results/&cell_name;.modeling_msg.rpt
          </pattern>
          <pattern id="noneq">
            &ip_name;/fvpnr/results/&cell_name;.noneq.rpt
          </pattern>
          <pattern id="pin_constraints">
            &ip_name;/fvpnr/results/&cell_name;.pin_constraints.rpt
          </pattern>
          <pattern id="pin_direction">
            &ip_name;/fvpnr/results/&cell_name;.pin_direction.rpt
          </pattern>
          <pattern id="renaming_rule">
            &ip_name;/fvpnr/results/&cell_name;.renaming_rule.rpt
          </pattern>
          <pattern id="statistic">
            &ip_name;/fvpnr/results/&cell_name;.statistic.rpt
          </pattern>
          <pattern id="stuck_at">
            &ip_name;/fvpnr/results/&cell_name;.stuck_at.rpt
          </pattern>
          <pattern id="unmap_extra">
            &ip_name;/fvpnr/results/&cell_name;.unmap_extra.rpt
          </pattern>
          <pattern id="unmap_notmap">
            &ip_name;/fvpnr/results/&cell_name;.unmap_notmap.rpt
          </pattern>
          <pattern id="unmap_unreach">
            &ip_name;/fvpnr/results/&cell_name;.unmap_unreach.rpt
          </pattern>
          <pattern id="do" minimum="0">
            &ip_name;/fvpnr/run/&cell_name;.*.do
          </pattern>
          <pattern id="conformal_tcl">
            &ip_name;/fvpnr/run/&cell_name;.conformal.tcl
          </pattern>
          <producer id="ICD-IP"/>
          <producer id="SPNR"/>
          <consumer id="ICD-IP"/>
          <consumer id="SPNR"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 205265
        self._isReady = True
        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, 'lec.log', id_='lec_log')
        self._addPatternWithWorkingDir(dirName, 'abort.rpt', id_='abort')
        self._addPatternWithWorkingDir(dirName, 'black_box.rpt', id_='black_box')
        self._addPatternWithWorkingDir(dirName, 'comp_data.rpt', id_='comp_data')
        self._addPatternWithWorkingDir(dirName, 'design_data.rpt', id_='design_data')
        self._addPatternWithWorkingDir(dirName, 'gate_sum.rpt', id_='gate_sum')
        self._addPatternWithWorkingDir(dirName, 'ignored_inputs.rpt', id_='ignored_inputs')
        self._addPatternWithWorkingDir(dirName, 'ignored_outputs.rpt', id_='ignored_outputs')
        self._addPatternWithWorkingDir(dirName, 'modeling_msg.rpt', id_='modeling_msg')
        self._addPatternWithWorkingDir(dirName, 'noneq.rpt', id_='noneq')
        self._addPatternWithWorkingDir(dirName, 'pin_constraints.rpt', id_='pin_constraints')
        self._addPatternWithWorkingDir(dirName, 'pin_direction.rpt', id_='pin_direction')
        self._addPatternWithWorkingDir(dirName, 'renaming_rule.rpt', id_='renaming_rule')
        self._addPatternWithWorkingDir(dirName, 'statistic.rpt', id_='statistic')
        self._addPatternWithWorkingDir(dirName, 'stuck_at.rpt', id_='stuck_at')
        self._addPatternWithWorkingDir(dirName, 'unmap_extra.rpt', id_='unmap_extra')
        self._addPatternWithWorkingDir(dirName, 'unmap_notmap.rpt', id_='unmap_notmap')
        self._addPatternWithWorkingDir(dirName, 'unmap_unreach.rpt', id_='unmap_unreach')
        dirName = os.path.join(self._idlower, 'run')
        self._addPatternWithWorkingDir(dirName, '*.do', id_='do', minimum=0)
        self._addPatternWithWorkingDir(dirName, 'conformal.tcl', id_='conformal_tcl')
        self._addProducer("ICD-IP")
        self._addProducer("SPNR")
        self._addConsumer("ICD-IP")
        self._addConsumer("SPNR")
        self._addConsumer("ICD-PD")

    def _FVSYN(self):
        '''FSYN exists to collect the Formal Equivalence report from an industry
        standard solution like Conformal LEC. There is no database to deliver,
        simply the result file showing the state of compare or equivalence.

        Audit files are also delivered in accordance with the Audit checks
        defined for this deliverable. Specifically this checks the post SYN gate
        level netlist versus the original RTL.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/FVSYN_Definition.docx

        >>> t = Template('FVSYN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205267" id="FVSYN">
          <description> ... </description>
          <pattern id="lec_log">
            &ip_name;/fvsyn/results/&cell_name;*.lec.log
          </pattern>
          <pattern id="abort">
            &ip_name;/fvsyn/results/&cell_name;*.abort.rpt
          </pattern>
          <pattern id="black_box">
            &ip_name;/fvsyn/results/&cell_name;*.black_box.rpt
          </pattern>
          <pattern id="comp_data">
            &ip_name;/fvsyn/results/&cell_name;*.comp_data.rpt
          </pattern>
          <pattern id="design_data">
            &ip_name;/fvsyn/results/&cell_name;*.design_data.rpt
          </pattern>
          <pattern id="gate_sum">
            &ip_name;/fvsyn/results/&cell_name;*.gate_sum.rpt
          </pattern>
          <pattern id="ignored_inputs">
            &ip_name;/fvsyn/results/&cell_name;*.ignored_inputs.rpt
          </pattern>
          <pattern id="ignored_outputs">
            &ip_name;/fvsyn/results/&cell_name;*.ignored_outputs.rpt
          </pattern>
          <pattern id="modeling_msg">
            &ip_name;/fvsyn/results/&cell_name;*.modeling_msg.rpt
          </pattern>
          <pattern id="noneq">
            &ip_name;/fvsyn/results/&cell_name;*.noneq.rpt
          </pattern>
          <pattern id="pin_constraints">
            &ip_name;/fvsyn/results/&cell_name;*.pin_constraints.rpt
          </pattern>
          <pattern id="pin_direction">
            &ip_name;/fvsyn/results/&cell_name;*.pin_direction.rpt
          </pattern>
          <pattern id="renaming_rule">
            &ip_name;/fvsyn/results/&cell_name;*.renaming_rule.rpt
          </pattern>
          <pattern id="statistic">
            &ip_name;/fvsyn/results/&cell_name;*.statistic.rpt
          </pattern>
          <pattern id="stuck_at">
            &ip_name;/fvsyn/results/&cell_name;*.stuck_at.rpt
          </pattern>
          <pattern id="unmap_extra">
            &ip_name;/fvsyn/results/&cell_name;*.unmap_extra.rpt
          </pattern>
          <pattern id="unmap_notmap">
            &ip_name;/fvsyn/results/&cell_name;*.unmap_notmap.rpt
          </pattern>
          <pattern id="unmap_unreach">
            &ip_name;/fvsyn/results/&cell_name;*.unmap_unreach.rpt
          </pattern>
          <pattern id="do" minimum="0">
            &ip_name;/fvsyn/run/&cell_name;.*.do
          </pattern>
          <pattern id="conformal_tcl">
            &ip_name;/fvsyn/run/&cell_name;.conformal.tcl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="SPNR"/>
        </template> '
        '''
        self._caseid = 205267
        self._isReady = True
        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, '*.lec.log', addDot=False, id_='lec_log')
        self._addPatternWithWorkingDir(dirName, '*.abort.rpt', addDot=False, id_='abort')
        self._addPatternWithWorkingDir(dirName, '*.black_box.rpt', addDot=False, id_='black_box')
        self._addPatternWithWorkingDir(dirName, '*.comp_data.rpt', addDot=False, id_='comp_data')
        self._addPatternWithWorkingDir(dirName, '*.design_data.rpt', addDot=False, id_='design_data')
        self._addPatternWithWorkingDir(dirName, '*.gate_sum.rpt', addDot=False, id_='gate_sum')
        self._addPatternWithWorkingDir(dirName, '*.ignored_inputs.rpt', addDot=False, id_='ignored_inputs')
        self._addPatternWithWorkingDir(dirName, '*.ignored_outputs.rpt', addDot=False, id_='ignored_outputs')
        self._addPatternWithWorkingDir(dirName, '*.modeling_msg.rpt', addDot=False, id_='modeling_msg')
        self._addPatternWithWorkingDir(dirName, '*.noneq.rpt', addDot=False, id_='noneq')
        self._addPatternWithWorkingDir(dirName, '*.pin_constraints.rpt', addDot=False, id_='pin_constraints')
        self._addPatternWithWorkingDir(dirName, '*.pin_direction.rpt', addDot=False, id_='pin_direction')
        self._addPatternWithWorkingDir(dirName, '*.renaming_rule.rpt', addDot=False, id_='renaming_rule')
        self._addPatternWithWorkingDir(dirName, '*.statistic.rpt', addDot=False, id_='statistic')
        self._addPatternWithWorkingDir(dirName, '*.stuck_at.rpt', addDot=False, id_='stuck_at')
        self._addPatternWithWorkingDir(dirName, '*.unmap_extra.rpt', addDot=False, id_='unmap_extra')
        self._addPatternWithWorkingDir(dirName, '*.unmap_notmap.rpt', addDot=False, id_='unmap_notmap')
        self._addPatternWithWorkingDir(dirName, '*.unmap_unreach.rpt', addDot=False, id_='unmap_unreach')
        dirName = os.path.join(self._idlower, 'run')
        self._addPatternWithWorkingDir(dirName, '*.do', id_='do', minimum=0)
        self._addPatternWithWorkingDir(dirName, 'conformal.tcl', id_='conformal_tcl')
        self._addProducer("ICD-IP")
        self._addConsumer("SPNR")

#    def _GLNPOSTPNR(self):
#        '''Post place and route Verilog gate-level netlist.
#
#        >>> t = Template('GLNPOSTPNR')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="24175" id="GLNPOSTPNR">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/glnpostpnr/&ip_name;.glnpostpnr.filelist
#          </filelist>
#          <producer id="IP-PNR"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 24175
#        self._isReady = True
#
#        self._addFilelist()
#        self._addProducer("IP-PNR")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("TE")
#
#    def _GLNPREPNR(self):
#        '''Synthesized Verilog gate-level netlist.
#
#        >>> t = Template('GLNPREPNR')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28349" id="GLNPREPNR">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/glnprepnr/&ip_name;.glnprepnr.filelist
#          </filelist>
#          <pattern id="ddc" mimetype="application/octet-stream" minimum="0">
#            &ip_name;/glnprepnr/&cell_name;.ddc
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28349
#        self._isReady = True
#
#        self._addFilelist()
#        #self._addPattern("*.v", prependTopCellName=False, id_='verilog')
#        self._addPattern("ddc", id_='ddc', minimum=0)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#        self._addConsumer("TE")
#
    def _GP(self):
        '''Golden Pattern means
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/GP_Definition.docx

        >>> t = Template('GP')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209043" id="GP">
          <description> ... </description>
          <pattern id="vpd">
            &ip_name;/gp/*.vpd
          </pattern>
          <pattern id="txt">
            &ip_name;/gp/*_bcm_inst.txt
          </pattern>
          <pattern id="vfile">
            &ip_name;/gp/*.v
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 209043
        self._isReady = True

        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, "*.vpd",
                                       id_='vpd', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*_bcm_inst.txt",
                                       id_='txt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.v",
                                       id_='vfile', prependTopCellName=False)

        self._addProducer("ICD-IP")
        self._addConsumer("TE")

#    def _ICC(self):
#        '''Working directory for IC Compiler.  When tools like `mwsubmit` need
#        to find things are in the IC Compiler working directory, this
#        deliverable reveals the location.  Ordinarily, this deliverable is not
#        checked with VP.
#
#        >>> t = Template('ICC')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="121268" id="ICC">
#          <description> ... </description>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/icc/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view>
#              CEL 
#            </view>
#          </milkyway>
#          <producer id="LAYOUT"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 121268
#        self._isReady = True
#        self._addMilkywayCell(self._cellName, 'CEL', suffix='')
#        self._addProducer("LAYOUT")
#        self._addConsumer("LAYOUT")
#
#
#    def _INTERMAP(self):
#        '''Mapping information between subsystems.
#
#        >>> t = Template('INTERMAP')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="135568" id="INTERMAP">
#          <description> ... </description>
#          <pattern id="baum_interface_mapping_table" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" minimum="0">
#            &ip_name;/intermap/*.baum_interface_mapping_table.xlsx
#          </pattern>
#          <pattern id="hio_interface_mapping_table" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/intermap/*.hio_interface_mapping_table.xlsx
#          </pattern>
#          <producer id="IP-ICD-DIGITAL"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 135568
#        self._isReady = True
#        self._addPattern("*.baum_interface_mapping_table.xlsx",
#                         id_='baum_interface_mapping_table',
#                         minimum=0, prependTopCellName=False)
#        self._addPattern("*.hio_interface_mapping_table.xlsx",
#                         id_='hio_interface_mapping_table',
#                         prependTopCellName=False)
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addConsumer("PD-ICD")

    def _INTERRBA(self):
        '''INTERRBA exists to describe the CRAM Definition for routing blocks.
        The difference between INTERRBA definition compared to a block RDF is
        that this describes which connections are connected when CRAM setting is
        ENABLED.  Audit files are also delivered in accordance with the Audit
        checks defined for this deliverable.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/INTERRBA_Definition.docx

        >>> t = Template('INTERRBA')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205270" id="INTERRBA">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/interrba/&cell_name;.interblock.rba
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 205270
        self._isReady = True
        self._addPattern("interblock.rba")
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("TE")

    def _INTFC(self):
        '''The Interface Library (INTFCLIB) deliverable provides specifc information
        in a compact database form (.dmz) for interfaces used by DMZ components.
        Interfaces are development in groups independently (and may have different owners).
        Interface groups have their own directory with the intfc ICM tree.
        Interface owners may add more group directories as required.
        Each interface group contains a src subdirectory that additionally contains
        the DMZ interface Tcl definition file.  Multiple interfaces within a group
        may be supported as a single Tcl file (with multiple interface definitions)
        or by separate Tcl files.  DMZ interface Tcl source files are 'compiled' into
        a DMZ interface database file through the dmzInterfcBuilder utility. 
        DMZ interface data files are combined by means of the DMZ utility dmzIntfcMgr
        to produce a single merged DMZ group library containing all the interfaces within
        the group.  This single merged group interface library is submitted to ICM as
        the deliverable for the group as 'intfc_group_intfcLib.dmz'. 
        A release is made by merging all group interface libraries into one composite library.
        This DMZ data file is delivered in the intfc directory library.  The src directory of
        the library directory will contain the dmzIntfcMgr control text file of all the group
        interface libraries to merge. This composite library is the only interface data file
        consumed by IP and hierarchical assemblies.
        Added by Henry Jen. As of 2015 ww05, a new directory called widthheight is created:
        intfclib/intfc/widthheight. This new directory serves to store IP wrapper sizes.
        See page 4 for details on files stored under widthheight.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/INTFC_Definition.docx

        >>> t = Template('INTFC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="206838" id="INTFC">
          <description> ... </description>
          <pattern id="intfc_dmz" mimetype="application/octet-stream">
            &ip_name;/intfc/library/library_intfcLib.dmz
          </pattern>
          <pattern id="txt">
            &ip_name;/intfc/library/src/library.txt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="NETLIST"/>
          <consumer id="IPD"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 206838
        self._isReady = True
        dirName = os.path.join(self._idlower, 'library')
        self._addPatternWithWorkingDir(dirName, 'library_intfcLib.dmz',
                                       id_='intfc_dmz', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'src/library.txt',
                                       id_='txt', prependTopCellName=False)

        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("NETLIST")
        self._addConsumer("IPD")
        self._addConsumer("TE")

    def _IPXACT(self):
        '''IPXACT is an XML standard (IEEE 1685-2009) for SOC construction. The SOC team uses it
           for Register Description as well as SOC level stitching and integration. 
           IPXACT XMLs are produced by individual RTL/block owners. Port descriptions are mandatory
           in the XML while register descriptions are required only when registers are present in a block. 
           XMLs are delivered by IP vendors (e.g Synopsys, ARM) as well as created by Altera engineers.
           All XMLs are managed and verified by the Magillem tool. 
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/IPXACT_Definition.docx

        >>> t = Template('IPXACT')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209045" id="IPXACT">
          <description> ... </description>
          <pattern id="file" mimetype="text/xml">
            &ip_name;/ipxact/&cell_name;.xml
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="ICD-IP"/>
        </template> '
        '''
        # See also http://fogbugz/default.asp?172714
        self._caseid = 209045
        self._isReady = True
        self._addPattern (fileExtension = "xml", 
                          id_           = 'file')
        
        self._addProducer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("ICD-IP")

#    def _IPFRAM(self):
#        '''Abstract view generated by IP to show the port locations.
#
#        >>> t = Template('IPFRAM')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="27754" id="IPFRAM">
#          <description> ... </description>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/ipfram/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view>
#              CEL 
#            </view>
#          </milkyway>
#          <producer id="LAYOUT"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 27754
#        self._isReady = True
#        self._addMilkywayCell(self._cellName, 'CEL', suffix='')
#        self._addProducer("LAYOUT")
#        self._addConsumer("LAYOUT")
#
#
#    def _IPPLACE(self):
#        '''Placement file.
#
#        >>> t = Template('IPPLACE')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28467" id="IPPLACE">
#          <description> ... </description>
#          <pattern id="top">
#            &ip_name;/ipplace/&cell_name;.ipplace.def
#          </pattern>
#          <pattern id="file">
#            &ip_name;/ipplace/...
#          </pattern>
#          <producer id="IP-PNR"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28467
#        self._isReady = True
#        self._addPattern(self._idlower + '.def', id_='top')
#        self._addPattern('....def', prependTopCellName=False)
#        self._addProducer("IP-PNR")
#        self._addConsumer("TE")
#        
#
    def _IPPWRMOD(self):
        '''The IPPWRMOD deliverables exist to capture the power collateral (power consumption
           for different modes) needed for Quartus Early-Power-Estimator
           (EPE) / Power-Play-Power-Analyzer (PPPA) and IP/Fullchip Power goal/budget closure.
           The deliverable is also named IPPWRMOD in the 20nm projects.
           For 14nm projects, only the ICM IP variants identified as power modeling hierarchy
           will need to deliver this IPPWRMOD deliverables. For IP variants that is identified
           not to delivery, IP owners will have to update the 'unneeded deliverables' accordingly
           as per describe in IPSPEC spec.
           The deliverables contains the following files
          1.    Filelist - <*>.ippwrmod.filelist
                This file will list down the complete files (Ex. power model, or optional netlist)
           that is provided for the power model delivery
                Due to the DMZ Wrapper/Base Function and Power Molecule methodology, the <*> name
           may not always be the top-cell names in IPSPEC/cell_names.txt. Thus, it <*> can be
           any arbitrary cell names.
          2.    Power Model (Optional)
                There will be 2 separate file delivery for Dynamic Power (<*>.dynamic_power.xlsx)
           and Static Power (<*>.static_power.xlsx)
                The exact format/content for the Dynamic/Static power file is still work-in-progress & TBD.
          3.    Netlists (Optional)
                The Verilog (*.v) and SPF (*.spf) netlist is optional and limited to the few IP variants
           (Ex. LAB/MLAB/IOB) cases that the SW Power Model is generating lower-level power numbers for
           Quartus internal PPPA or AIOT model.

           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/IPPWRMOD_Definition.docx

        >>> t = Template('IPPWRMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209039" id="IPPWRMOD">
          <description> ... </description>
          <filelist id="filelist">
            &ip_name;/ippwrmod/*.ippwrmod.filelist
          </filelist>
          <pattern id="dynamic" mimetype="application/vnd.ms-excel" minimum="0">
            &ip_name;/ippwrmod/xls/*.dynamic_power.xls
          </pattern>
          <pattern id="static" mimetype="application/vnd.ms-excel" minimum="0">
            &ip_name;/ippwrmod/xls/*.static_power.xls
          </pattern>
          <pattern id="spf" minimum="0">
            &ip_name;/ippwrmod/netlist/spf/*.spf.gz
          </pattern>
          <pattern id="verilog" minimum="0">
            &ip_name;/ippwrmod/netlist/verilog/*.v
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 209039
        self._isReady = True

#       Based on FB# 227723 changed from pattern to filelist
        dirName = os.path.join(self._idlower)
#        self._addPatternWithWorkingDir(dirName, 'ippwrmod.filelist',
#                                       id_='filelist')
        self._addFilelistWithWorkingDir(dirName, '*.ippwrmod.filelist',
                                        id_='filelist')
        dirName = os.path.join(self._idlower, 'xls')
        self._addPatternWithWorkingDir(dirName, '*.dynamic_power.xls', minimum=0,
                                       id_='dynamic', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.static_power.xls', minimum=0,
                                       id_='static', prependTopCellName=False)

        dirName = os.path.join(self._idlower, 'netlist', 'spf')
        self._addPatternWithWorkingDir(dirName, "*.spf.gz",
                                       id_='spf', minimum=0,
                                       prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'netlist', 'verilog')
        self._addPatternWithWorkingDir(dirName, "*.v", minimum=0,
                                       id_='verilog', prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")

    def _IPFLOORPLAN(self):
        '''The IPFLOORPLAN deliverable exists to define data needed to define the
        bounding box of a design that is intended. Essentially a place to store
        the floorplan.def of an IP typically generated by layout. This should
        include def sections for design, diearea, pins, macro components and blockages.
        Additionally, IPFLOORPLAN will  contain lef for the IP. All custom blocks,
        embedded in PnR especially, must submit lef abstracts for IP. These will
        in turn be converted in the PnR flow to FRAM views in MW and used in the PnR flow.

        IPFLOORPLAN deliverable files should contain:
            &ip_name;/ipfloorplan/<&cell_name>;.floorplan.def     Logical Name: def     
            &ip_name;/ipfloorplan/<&cell_name>;.floorplan.lef       Logical Name: lef
            &ip_name;/ipfloorplan/audit/audit.<&cell_name>.ipfloorplan_lefout.xml
            &ip_name;/ipfloorplan/audit/audit.<&cell_name>.ipfloorplan_defout.xml
            &ip_name;/ipfloorplan/lef/<&cell_name>_lefout.txt
            &ip_name;/ipfloorplan/lef/<&cell_name>_lefout.errlog
            &ip_name;/ipfloorplan/def/<&cell_name>_defout.txt
            &ip_name;/ipfloorplan/def/<&cell_name>_defout.errlog (DMZ do not have def compare)
            &ip_name;/ipfloorplan/APCC/<&cell_name>.apccwaiver (optional)

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/IPFLOORPLAN_Definition.docx
         
        >>> t = Template('IPFLOORPLAN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205275" id="IPFLOORPLAN">
          <description> ... </description>
          <pattern id="def" minimum="0">
            &ip_name;/ipfloorplan/&cell_name;.floorplan.def
          </pattern>
          <pattern id="lef">
            &ip_name;/ipfloorplan/&cell_name;.floorplan.lef
          </pattern>
          <pattern id="leftxt">
            &ip_name;/ipfloorplan/lef/&cell_name;_lefout.txt
          </pattern>
          <pattern id="leflog">
            &ip_name;/ipfloorplan/lef/&cell_name;_lefout.errlog
          </pattern>
          <pattern id="deftxt" minimum="0">
            &ip_name;/ipfloorplan/def/&cell_name;_defout.txt
          </pattern>
          <pattern id="deflog" minimum="0">
            &ip_name;/ipfloorplan/def/&cell_name;_defout.errlog
          </pattern>
          <pattern id="apcc" minimum="0">
            &ip_name;/ipfloorplan/APCC/&cell_name;.apccwaiver
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SPNR"/>
          <consumer id="FCI"/>
        </template> '
        '''
        self._caseid = 205275
        self._isReady = True
        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, "floorplan.def", minimum=0,
                                       id_='def')
        self._addPatternWithWorkingDir(dirName, "floorplan.lef",
                                       id_='lef')
        dirName = os.path.join(self._idlower, "lef")
        self._addPatternWithWorkingDir(dirName, "_lefout.txt",
                                       addDot=False, id_='leftxt')
        self._addPatternWithWorkingDir(dirName, "_lefout.errlog",
                                       addDot=False, id_='leflog')
        dirName = os.path.join(self._idlower, "def")
        self._addPatternWithWorkingDir(dirName, "_defout.txt", minimum=0,
                                       addDot=False, id_='deftxt')
        self._addPatternWithWorkingDir(dirName, "_defout.errlog", minimum=0,
                                       addDot=False, id_='deflog')
        dirName = os.path.join(self._idlower, "APCC")
        self._addPatternWithWorkingDir(dirName, "apccwaiver",
                                       minimum=0, id_='apcc')
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SPNR")
        self._addConsumer("FCI")
#        dirName = os.path.join(self._idlower, 'lef')
#        self._addPatternWithWorkingDir(dirName, "lef.txt",
#                                       id_='leftxt')
#        self._addPatternWithWorkingDir(dirName, "errlog",
#                                       id_='leflog')
#        dirName = os.path.join(self._idlower, 'def')
#        self._addPatternWithWorkingDir(dirName, "def.txt",
#                                       id_='deftxt')
#        self._addPatternWithWorkingDir(dirName, "errlog",
#                                       id_='deflog')

#          <pattern id="leftxt">
#            &ip_name;/ipfloorplan/lef/&cell_name;.lef.txt
#          </pattern>
#          <pattern id="leflog">
#            &ip_name;/ipfloorplan/lef/&cell_name;.errlog
#          </pattern>
#          <pattern id="deftxt">
#            &ip_name;/ipfloorplan/def/&cell_name;.def.txt
#          </pattern>
#          <pattern id="deflog">
#            &ip_name;/ipfloorplan/def/&cell_name;.errlog
#          </pattern>

    def _IPSPEC(self):
        '''The IPSPEC deliverable exists to provide information about the content of a variant.
           For 14nm projects all variants in IC Manage need to deliver an IPSPEC deliverable.
           The IPSPEC deliverable is a crucial component to many test systems that run tests against
           collateral delivered by our engineering teams and must exist from the time a variant
           is created. Failing to deliver an IPSPEC deliverable will result in a non-waivable error
           in the gated release system.
           Users should ensure that the list text files are saved with UNIX-style line endings and
           not Windows-style line endings. Most modern text editors can translate the format for you.
           This deliverable contains the following files:
           The cell_names.txt file
           This file defines the names of cells within the variant that can be instantiated by other
           variants.  The cell names appear one per line.  Blank lines are ok, and lines beginning
           with a hash character (#) will be ignored (use for comments).
           The file is required to exist.
           The IPSPEC cell_names.txt file is the vehicle for an IP owner to communicate to the
           downstream user what is being delivered and can be instantiated in the parent.
           Therefore IP blocks which have base functions and wrappers around those base functions
           need to list the wrappers in the cell_names.txt file since only the wrappers are exported
           and can be instantiated but not the base functions.
           Further details on this file can be found in the Multiple Cells per IP section of the VP documentation.
              <cellname>.unneeded_deliverables.txt files
           This file, if it exists, informs the gated release system (and quick check utility) that
           the deliverables listed in the file (one per line) do not need to be provided (or tested)
           by the system for the given cellname.
           Each entry must be a valid ICManage libtype for the variant and must be all lower case
           following the format of the libtype.
           The file is optional.
           The IPSPEC deliverable may not be listed an unneeded.
             <cellname>.molecules.txt files
           Each cell can optionally have a cellName.molecules.txt file that lists the timing
           molecules within the cell.  Timing molecules are those Verilog modules for which
           there are Liberty models.
           A cell that has a corresponding cellName.molecules.txt and an entry in the cell name
           list in cell_names.txt is a 'top-cell'. However a cell can have a  cellName.molecules.txt
           file without an entry in cell_names.txt.
           The format is a list of cell names, one per line. The file should exist whenever timing
           collateral is being generated.  This would mean at any stage that TIMEMOD is to
           be delivered.  Note that we are going to be delivering TIMEMOD much earlier in ND than in NF.
           The IP owners are responsible for creating the molecules.txt file.  By the time the
           'placeholder' timing collateral is delivered, these files must have been delivered.
           If the molecules.txt for a cell is missing, it is the same as an empty molecules.txt
           file.  It simply means that there are no timing molecules for that cell.
           Instances of timing molecules are:
           . The leaf elements of any Verilog netlist used for timing closure for SSD or
           SW are called Timing Molecules.
           . A Timing Molecule may have had its Liberty model generated from a collection of
           Timing Elements at a lower level of hierarchy.
           . A Timing Molecule may also just be a simple gate (e.g. inverter) with a Liberty
           model if it is seen by SSD or SW.
           . A Timing Element is a unit of design represented by a Liberty model which does not
           need to be seen by SSD or SW, e.g. is needed by CIP only.
           . Example:  An ASIC block that needs to have a Liberty model because of Quartus
           is a Timing Molecule.  The Liberty model is generated by running PrimeTime on
           a netlist composed of Timing Elements.
           . Examples of Timing Elements include ICF standard cells and possibly analog blocks
           embedded below a Timing Molecule.
           Multiple timing tools are expected to use this file.  For example, the plan for
           Virtuoso is to have the Verilog netlister automatically read this file to identify
           the stop cells.  Similarly, the flow that runs extraction can use this file
           to identify the SKIP_CELL list.  Finally, Software is tentatively considering
           using this list to identify the molecules that they actually care about.
           In NightFury, timing molecules were called 'atoms', but that name is already
           in use elsewhere.  To avoid confusion, in Nadder we have changed
           the name to 'molecules'.
             <cellname>.elements.txt files
           Existence:
                A cell that has a molecules.txt file which contains its own name (i.e. it is seen
           by Quartus) may have a $topcell.elements.txt file
           Contents:
                The $topcell.elements.txt file contains all leaf cells that are needed
           by RC-LVS for running for extraction purposes.
           Each leaf cell listed in the *.elements.txt file is expected to have a Liberty
           file somewhere in the design workspace.
           Format:
                The format of the $topcell.elements.txt file is one leaf cell per line, where the
           leaf cell's library name is separated from the leaf cell name by a ' ':
                   oa_library1 leaf_cell1
                   oa_library1 leaf_cell2
           The library name may be optional if the leaf cell listed in the $topcell.elements.txt
           file is actually in the library itself, the library name may be omitted.
                allmolecules.txt files
           Existence:
                This is an optional file at the variant level.
           Contents:
                This file contains all the molecules that would be needed by any of the topcells
           in the variant.  Each leaf cell listed in the allmolecules.txt file is expected to have
           a Liberty file somewhere in the design workspace.
           Format:
                The format of the allmolecules file is one leaf cell per line, where the leaf
           cell's library name is separated from the leaf cell name by a ' ':
                 oa_library1 leaf_cell1
                 oa_library1 leaf_cell2
           The library name may be optional if the leaf cell listed in the allmolecules.txt
           file is actually in the library itself, the library name may be omitted.
           allelements.txt files
           Existence:

           This is an optional file at the variant level.   However, if this file exists,
           allmolecules.txt should also exist.
           Contents:
                This file contains all the elements that would be needed by any of the topcells
           in the variant.  Each leaf cell listed in the allelements.txt file is expected to have
           a Liberty file somewhere in the design workspace.
           Format:
                The format of the allelements file is one leaf cell per line, where the leaf cell's
           library name is separated from the leaf cell name by  ' ':
                   oa_library1 leaf_cell1
                   oa_library1 leaf_cell2
           The library name may be optional if the leaf cell listed in the allmolecules.txt file
           is actually in the library itself, the library name may be omitted.
           Notes:
                $topcell.molecules.txt and $topcell.elements.txt and allmolecules.txt and
           allelements.txt do not need to include names of standard or structured design cells.
                  Such cells will be automatically assumed to be leaf cells for the design by the
           flows using these files.
           The $topcell.elements.txt file is needed for blocks that are molecules but are also
           composed of leaf cells
                  RC-LVS needs to know the list of leaf cells

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/IPSPEC_Definition.docx
        
        >>> t = Template('IPSPEC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205286" id="IPSPEC">
          <description> ... </description>
          <pattern id="cell_names">
            &ip_name;/ipspec/cell_names.txt
          </pattern>
          <pattern id="elements" minimum="0">
            &ip_name;/ipspec/&cell_name;.elements.txt
          </pattern>
          <pattern id="molecules" minimum="0">
            &ip_name;/ipspec/&cell_name;.molecules.txt
          </pattern>
          <pattern id="unneeded_deliverables" minimum="0">
            &ip_name;/ipspec/&cell_name;.unneeded_deliverables.txt
          </pattern>
          <pattern id="allmolecules" minimum="0">
            &ip_name;/ipspec/allmolecules.txt
          </pattern>
          <pattern id="allelements" minimum="0">
            &ip_name;/ipspec/allelements.txt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._addPattern('cell_names.txt', 
                         id_='cell_names',
                         prependTopCellName=False)
        # Added per rumours. Yes, rumors (J.M.)
        # Made *optional* per rumors. Yes, rumors (R.G.)
        self._addPattern('elements.txt', id_='elements', minimum=0)

        self._addPattern('molecules.txt', id_='molecules', minimum=0)        
        
        # Added per 208011
        self._addPattern('unneeded_deliverables.txt', 
                         id_='unneeded_deliverables',
                         minimum=0)
        # Added per FB#227434
        self._addPattern('allmolecules.txt', 
                         id_='allmolecules',
                         prependTopCellName=False,
                         minimum=0)
        self._addPattern('allelements.txt', 
                         id_='allelements',
                         prependTopCellName=False,
                         minimum=0)
        
        self._caseid = 205286
        self._isReady = True
        self._controlled = True
        self._versioned = True
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("TE")

#    def _IPTIMEMOD(self):
#        '''Synopsys liberty (.lib) files for IP blocks.  These libs could be
#        hand-generated or generated from Nanotime.  It will not change the
#        format/type of the file.
#        
#        IPTIMEMOD replaces TNODES.
#
#        >>> t = Template('IPTIMEMOD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="79259" id="IPTIMEMOD">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/iptimemod/&ip_name;.iptimemod.filelist
#          </filelist>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 79259
#        self._isReady = True
#
#        self._addFilelist()
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#
#    def _IPV(self):
#        '''IP testbench components including testlist (regresion_list),
#        testbench filelist and all related testbench components.
#
#        >>> t = Template('IPV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28063" id="IPV">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/ipv/...
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28063
#        self._isReady = True
#
#        self._addPattern('...', prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#        
#    def _IREM(self):
#        '''RTL2GDS flow IR drop and electromigration reports in Redhawk and text
#        formats.
#
#        >>> t = Template('IREM')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="82024" id="IREM">
#          <description> ... </description>
#          <pattern id="filelist" minimum="0">
#            &ip_name;/irem/results/&ip_name;.irem.filelist
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 82024
#        self._isReady = True       
#
#        # ASIC style
#        dirName = os.path.join(self._idlower, 'results')
#        # self._addFilelistWithWorkingDir(dirName, minimum=0)
#        # As per http://fogbugz.altera.com/default.asp?154507, the file is *not*
#        # a filelist anymore but retains the same name, for reasons of backward 
#        # compatibility:
#        self._addPatternWithWorkingDir(dirName, self._ipName + '.irem.filelist',
#                                       id_="filelist", prependTopCellName=False, minimum=0)
#        # CUSTOM style
#        # CASE:154968 - we can't enforce a common layout for Totem data between the
#        # ASIC and CUSTOM teams so we have to drop it as part of the templateset
#        # The data check for this deliverable (CASE:92678) does a custom ASIC or
#        # CUSTOM Totem files check based on the spec from Kevin Leong. - IRC
#        #self._addTotem(isStatic=True, minimum=0)
#
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#        
#   
    def _NETLIST(self):
        '''The netlist (NETLIST) deliverable provides a gate-level Verilog netlist of the specific IP block.
        This deliverable is part of hierarchical IP blocks.  The netlist is a single-level of hierarchy and
        does not contain the netlist(s) of  lower-level instances.  The netlist is typically created from
        the DMZ utility dmzNetlister which requires the collateral from associated COMPLIB deliverable.

        This deliverable considers that the Verilog netlist may be created outside of the DMZ flow, however,
        details for such a flow have not been discussed at this time.

        The recommendation is to use the DMZ netlister.

        A release is made by running the dmzNetlister utility via the control script in the src directory.
        An audit trace file will be created along with the netlist deliverable.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/NETLIST_Definition.docx

        >>> t = Template('NETLIST')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="206839" id="NETLIST">
        <description> ... </description>
          <filelist id="cell_filelist">
            &ip_name;/netlist/filelists/dv/&cell_name;.f
          </filelist>
          <filelist id="cell_filelist_syn" minimum="0">
            &ip_name;/netlist/filelists/syn/&cell_name;.f
          </filelist>
          <pattern id="file">
            &ip_name;/netlist/&cell_name;.v
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="FCV"/>
          <consumer id="FCI"/>
          <consumer id="IPD"/>
          <consumer id="NETLIST"/>
          <consumer id="SOFTWARE"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 206839
        self._isReady = True
        dirName = os.path.join(self._idlower, 'filelists/dv')
        self._addFilelistWithWorkingDir(dirName,
                                        fileName=self._cellName + '.f',
                                        id_='cell_filelist')
        dirName = os.path.join(self._idlower, 'filelists/syn')
        self._addFilelistWithWorkingDir(dirName,
                                        fileName=self._cellName + '.f',
                                        id_='cell_filelist_syn', minimum = 0)
        self._addPattern("v",     id_='file')
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("FCV")
        self._addConsumer("FCI")
        self._addConsumer("IPD")
        self._addConsumer("NETLIST")
        self._addConsumer("SOFTWARE")
        self._addConsumer("TE")


#    def _LAY(self):
#        '''OpenAccess layout database.  Associated non-OpenAccess files are in
#        LAYMISC.
#
#        >>> t = Template('LAY')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="57834" id="LAY">
#          <description> ... </description>
#          <openaccess id="layout" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/oa/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view viewtype="oacMaskLayout">
#              layout
#            </view>
#          </openaccess>
#          <openaccess id="lfp" mimetype="application/octet-stream" minimum="0">
#            <libpath>
#              &ip_name;/oa/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view viewtype="oacMaskLayout">
#              lfp
#            </view>
#          </openaccess>
#          <producer id="IP-PNR"/>
#          <producer id="LAYOUT"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 57834
#        self._isReady = True
#
#        self._addOpenAccessCellView('layout',      'oacMaskLayout', id_='layout')
#        self._addOpenAccessCellView('lfp',         'oacMaskLayout', id_='lfp', minimum=0)
#        self._addProducer("IP-PNR")
#        self._addProducer("LAYOUT")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("LAYOUT")

    def _LAYMISC(self):
        '''The LAYMISC deliverable exists to store:
               &ip_name.signoff.html -- tapeout signoff violations
               audit.&cell_name.laymisc_signoff.xml file
        Notes:
               Layout Errors file for runsets that allowed waiver from the same variant will be used to extract to generate the signoff.html.
               The signoff comment for individual waived errors will be extracted from CPYDB from all variants of the same workspace.
               audit.laymisc.laymisc_signoff.xml file generated based on the extraction run and only 1 xml per variant.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/LAYMISC_Definition.docx

        >>> t = Template('LAYMISC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205448" id="LAYMISC">
          <description> ... </description>
          <pattern id="html">
            &ip_name;/laymisc/&ip_name;.signoff.html
          </pattern>
          <producer id="LAY-IP"/>
          <producer id="FCI"/>
          <consumer id="LAY-IP"/>
          <consumer id="FCI"/>
          <consumer id="ICD-IP"/>
        </template> '
        '''
        self._caseid = 205448
        self._isReady = True
        
        #workingDirName = os.path.join(self._idlower)
#        self._addPattern('audit.laymisc.laymisc_signoff.xml', id_='signoff',
#                         prependTopCellName=False)
        self._addPattern('{}.signoff.html'.format(self._ipName), id_='html',
                         prependTopCellName=False)
        self._addProducer("LAY-IP")
        self._addProducer("FCI")
        self._addConsumer("LAY-IP")
        self._addConsumer("FCI")
        self._addConsumer("ICD-IP")

    def _LINT(self):
        '''Lint is needed to check for HDL syntax, structural, coding and
        consistency problems in RTL descriptions which might be potential
        functional issues. It is required to ensure RTL design quality. The
        SpyGlass tool is used to lint on the RTL in all ASIC and Custom IPs.
        Deliverables are filelist, report file, log file and waiver. They are not
        directly consumed by other deliverables. It enables early detection of
        potential design issues which can be addressed at the earlier stages of
        the design development.   
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/LINT_Definition.docx

        >>> t = Template('LINT')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205449" id="LINT">
          <description> ... </description>
          <pattern id="custom_filelist" minimum="0">
            &ip_name;/lint/filelist/&cell_name;.custom.lint.f
          </pattern>
          <pattern id="lint_filelist">
            &ip_name;/lint/filelist/&cell_name;.lint.f
          </pattern>
          <pattern id="mustfix_log">
            &ip_name;/lint/&cell_name;.mustfix_results/console.log
          </pattern>
          <pattern id="mustfix_rpt">
            &ip_name;/lint/&cell_name;.mustfix_results/moresimple.rpt
          </pattern>
          <pattern id="review_log">
            &ip_name;/lint/&cell_name;.review_results/console.log
          </pattern>
          <pattern id="review_rpt">
            &ip_name;/lint/&cell_name;.review_results/moresimple.rpt
          </pattern>
          <pattern id="swl" minimum="0">
            &ip_name;/lint/&cell_name;.swl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
        </template> '
        '''
        self._caseid = 205449
        self._isReady = True
        
        workingDirName = os.path.join(self._idlower, 'filelist')
        self._addPatternWithWorkingDir(workingDirName,
                                        'custom.lint.f',
                                        id_='custom_filelist', minimum=0)
        self._addPatternWithWorkingDir(workingDirName,
                                        'lint.f',
                                        id_='lint_filelist')

        workingDirName = os.path.join(self._idlower, self._cellName + '.mustfix_results')
        self._addPatternWithWorkingDir(workingDirName, 'console.log', id_='mustfix_log', prependTopCellName=False)
        self._addPatternWithWorkingDir(workingDirName, 'moresimple.rpt', id_='mustfix_rpt', prependTopCellName=False)
        
        workingDirName = os.path.join(self._idlower, self._cellName + '.review_results')
        self._addPatternWithWorkingDir(workingDirName, 'console.log', id_='review_log', prependTopCellName=False)
        self._addPatternWithWorkingDir(workingDirName, 'moresimple.rpt', id_='review_rpt', prependTopCellName=False)

        self._addPattern('swl', id_='swl', minimum=0)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")

#    def _MCFD(self):
#        '''Core logical connectivity.
#
#        >>> t = Template('MCFD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="114827" id="MCFD">
#          <description> ... </description>
#        <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#          &ip_name;/mcfd/releasenotes.docx
#        </pattern>
#        <pattern id="mcfd" mimetype="application/x-tcl">
#          &ip_name;/mcfd/&cell_name;.mcfd.tcl.gz
#        </pattern>
#        <pattern id="mcf_fcl">
#          &ip_name;/mcfd/&cell_name;.core_mcf_fcl.txt.gz
#        </pattern>
#        <pattern id="leim_redundancy">
#          &ip_name;/mcfd/&cell_name;.leim_redundancy.txt
#        </pattern>
#        <pattern id="mcf_expceted_ncs">
#          &ip_name;/mcfd/&cell_name;.mcf_expceted_ncs.txt
#        </pattern>
#        <pattern id="mcf_multiple_output_inouts">
#          &ip_name;/mcfd/&cell_name;.mcf_multiple_output_inouts.txt
#        </pattern>
#        <pattern id="dim_tbl">
#          &ip_name;/mcfd/&cell_name;.dim_tbl
#        </pattern>
#        <pattern id="cdaf_mcf">
#          &ip_name;/mcfd/&cell_name;.cdaf_mcf.tsv.pp.gz
#        </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 114827
#        self._isReady = True
#        
#        self._addReleaseNotes()        
#        
#        self._addPattern("mcfd.tcl.gz",                    id_='mcfd')
#        self._addPattern("core_mcf_fcl.txt.gz",            id_='mcf_fcl')
#        self._addPattern("leim_redundancy.txt",            id_='leim_redundancy')
#        self._addPattern("mcf_expceted_ncs.txt",           id_='mcf_expceted_ncs')
#        self._addPattern("mcf_multiple_output_inouts.txt", id_='mcf_multiple_output_inouts')
#        self._addPattern("dim_tbl",                        id_='dim_tbl')
#        self._addPattern("cdaf_mcf.tsv.pp.gz",             id_='cdaf_mcf')
#
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("TE")
#
#    def _MCFL(self):
#        '''Core MCF file for layout MCF programming.  This is the layout version
#        of the MCFD.
#
#        >>> t = Template('MCFL')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28469" id="MCFL">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/mcfl/*.mcfl.txt
#          </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28469
#        self._isReady = True
#        self._addPattern('*.mcfl.txt', prependTopCellName=False, minimum=1)
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("LAYOUT")
#
#    def _MRFTEMP(self):
#        '''MRF template file to check against the layout option file.
#        This is usually only included in the second IP-to-PD release.
#
#        >>> t = Template('MRFTEMP')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28474" id="MRFTEMP">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/mrftemp/&cell_name;.mrftemp.txt
#          </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28474
#        self._isReady = True
#        self._addPattern('mrftemp.txt')
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("LAYOUT")
#
    def _MW(self):
        '''Physical database for sub-systems, CR_*, sector_sa, sector, and full chip. This is
        the Milkyway representation of these blocks. The blocks are constructed and assembled
        until we get to the full chip.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/MW_Definition.docx

        >>> t = Template('MW')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="210067" id="MW">
          <description> ... </description>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/mw/&ip_name;
            </libpath>
            <lib>
              &ip_name;
            </lib>
          </milkyway>
          <producer id="FCI"/>
          <consumer id="LAY-IP"/>
          <consumer id="ICD-IP"/>
          <consumer id="FCI"/>
        </template> '
        '''
        self._caseid = 210067
        self._isReady = True

        self._addMilkywayCell()
        self._addProducer("FCI")
        self._addConsumer("LAY-IP")
        self._addConsumer("ICD-IP")
        self._addConsumer("FCI")

#    def _NPP(self):
#        '''New Product Plan document. This is not part of the IP build.
#
#        >>> t = Template('NPP')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="57077" controlled="no" id="NPP" versioned="no">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/npp/releasenotes.docx
#          </pattern>
#          <pattern id="fs" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document" minimum="0">
#            &ip_name;/npp/&cell_name;.fs.docx
#          </pattern>
#          <pattern id="is" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document" minimum="0">
#            &ip_name;/npp/&cell_name;.is.docx
#          </pattern>
#          <pattern id="mas" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document" minimum="0">
#            &ip_name;/npp/&cell_name;.mas.docx
#          </pattern>
#          <pattern id="pa" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document" minimum="0">
#            &ip_name;/npp/&cell_name;.pa.docx
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <producer id="PD-ICD"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 57077
#        self._isReady = True
#        self._controlled = False
#        self._versioned = False
#        self._addReleaseNotes()
#        self._addPattern('fs.docx', id_='fs', minimum=0)
#        self._addPattern('is.docx', id_='is', minimum=0)
#        self._addPattern('mas.docx', id_='mas', minimum=0)
#        self._addPattern('pa.docx', id_='pa', minimum=0)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addProducer("PD-ICD")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")

    def _OA(self):
        '''This deliverable is used to store the physical IC design data, schematic and layout, in the OpenAccess format.
           This OA deliverable needs special support for the setup the virtuoso cds.lib.
           Need to include the OA library definition in the cds.libicm as:
           DEFINE &ip_name;  <workspace_root>/&ip_name;/oa/&ip_name;

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/OA_Definition.docx

        >>> t = Template('OA')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209768" id="OA">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/oa/...
          </pattern>
          <producer id="ICD-IP"/>
          <producer id="LAY-IP"/>
          <producer id="FCI"/>
          <consumer id="ICD-IP"/>
          <consumer id="LAY-IP"/>
          <consumer id="FCI"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 209768
        self._isReady = True

        self._addPattern('...', prependTopCellName=False)

        self._addProducer("ICD-IP")
        self._addProducer("LAY-IP")
        self._addProducer("FCI")
        self._addConsumer("ICD-IP")
        self._addConsumer("LAY-IP")
        self._addConsumer("FCI")
        self._addConsumer("SOFTWARE")

    def _OA_SIM(self):
        '''This deliverable is used to store the simulation schematic/testbench in OpenAccess format.
         This OA deliverable needs special support for the setup the virtuoso cds.lib.
         Need to include the OA library definition in the cds.libicm as:
              DEFINE &ip_name;_sim <workspace_root>/&ip_name;/oa_sim/&ip_name;_sim

         Note that the filelist is an output.  That is why it uses `&cell_name;`.
         DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/OA_SIM_Definition.docx
        
        >>> t = Template('OA_SIM')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="82023" id="OA_SIM">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/oa_sim/...
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-IP"/>
        </template> '
        '''
        self._caseid = 82023
        self._isReady = True
        self._addPattern('...', prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-IP")

    def _OASIS(self):
        '''The OASIS deliverable exists to store:
        1. Stream File
           a. Based on /ipspec/cell_names.txt
           b. Bump stream files for full-chip bump integration -- apply to Core Sector, IO SS, HSSI SS, Clarke and FC only.
        2. audit.<&cell_name>.oasis.f
        3. audit.<&cell_name>.oasis.OA.xml (OA) or audit.<&cell_name>.oasis.premerge.xml (MW)
        4. audit.<&cell_name>.oasis.merge.xml
        5.  <&cell_name>.oas.log

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/OASIS_Definition.docx

        >>> t = Template('OASIS')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205450" id="OASIS">
          <description> ... </description>
          <pattern id="file" mimetype="application/octet-stream">
            &ip_name;/oasis/&cell_name;.oas
          </pattern>
          <producer id="LAY-IP"/>
          <producer id="SPNR"/>
          <producer id="FCI"/>
          <consumer id="ICD-IP"/>
          <consumer id="LAY-IP"/>
          <consumer id="SPNR"/>
          <consumer id="FCI"/>
          <consumer id="IPD"/>
        </template> '
        '''
        self._caseid = 205450
        self._isReady = True
        self._addPattern('oas')
        self._addProducer("LAY-IP")
        self._addProducer("SPNR")
        self._addProducer("FCI")
        self._addConsumer("ICD-IP")
        self._addConsumer("LAY-IP")
        self._addConsumer("SPNR")
        self._addConsumer("FCI")
        self._addConsumer("IPD")
        
#    def _OPTDAT(self):
#        '''Option.dat file after cleaning the MCFTemp.
#
#        >>> t = Template('OPTDAT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="27761" id="OPTDAT">
#          <description> ... </description>
#          <pattern id="mcfopts" minimum="0">
#            &ip_name;/optdat/*.mcfopts.init
#          </pattern>
#          <pattern id="metal" mimetype="application/octet-stream" minimum="0">
#            &ip_name;/optdat/*.metal.dat
#          </pattern>
#          <pattern id="options" mimetype="application/octet-stream" minimum="0">
#            &ip_name;/optdat/*.options.dat
#          </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 27761
#        self._isReady = True
#        self._addPattern('*.mcfopts.init', prependTopCellName=False, id_='mcfopts', minimum=0)
#        self._addPattern('*.metal.dat', prependTopCellName=False, id_='metal', minimum=0)
#        self._addPattern('*.options.dat', prependTopCellName=False, id_='options', minimum=0)
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("LAYOUT")

    def _PERIODICTST(self):
        '''Each file in this deliverable contains a shell script that executes
        a test of the type suggested by the file name.
        
        The script will be run with the top of the workspace as the current
        working directory.
        
        Before the script is run, a review synced IC Manage workspace will exist.
        That is, the workspace will contain directories only.
        
        Thus the script must begin with ``icmp4 sync`` on the files needed to
        run the test.  If the script wants a different working directory, the
        script must cd to that directory.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/PERIODICTST_Definition.docx

        >>> t = Template('PERIODICTST')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205451" id="PERIODICTST">
          <description> ... </description>
          <pattern id="cdc" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/cdc.sh
          </pattern>
          <pattern id="design_intent" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/design_intent.sh
          </pattern>
          <pattern id="drc" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/drc.sh
          </pattern>
          <pattern id="lint" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/lint.sh
          </pattern>
          <pattern id="lvs" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/lvs.sh
          </pattern>
          <pattern id="simulation" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/simulation.sh
          </pattern>
          <pattern id="sta" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/sta.sh
          </pattern>
          <pattern id="vp" mimetype="application/x-sh" minimum="0">
            &ip_name;/periodictst/vp.sh
          </pattern>
        </template> '
        '''
        self._caseid = 205451
        self._isReady = True

        self._addPattern('cdc.sh', prependTopCellName=False, minimum=0, id_='cdc')
        self._addPattern('design_intent.sh', prependTopCellName=False, minimum=0, id_='design_intent')
        self._addPattern('drc.sh', prependTopCellName=False, minimum=0, id_='drc')
        self._addPattern('lint.sh', prependTopCellName=False, minimum=0, id_='lint')
        self._addPattern('lvs.sh', prependTopCellName=False, minimum=0, id_='lvs')
        self._addPattern('simulation.sh', prependTopCellName=False, minimum=0, id_='simulation')
        self._addPattern('sta.sh', prependTopCellName=False, minimum=0, id_='sta')
        self._addPattern('vp.sh', prependTopCellName=False, minimum=0, id_='vp')
        
#    def _PDN(self):
#        '''No Description provided.
#
#        >>> t = Template('PDN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="58142" controlled="no" id="PDN" versioned="no">
#          <description> ... </description>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 58142
#        self._isReady = True
#        self._controlled = False
#        self._versioned = False
#
    def _PINTABLE(self):
        '''Pintables are spreadsheets created by IC Design that describe each IO and power
           pad on a device, its characteristics (e.g. die location, IO bank, programming/test
           functions, vertical migration constraints), and the corresponding pin it connects
           to for each supported package.

           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/PINTABLE_Definition.docx

        >>> t = Template('PINTABLE')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="28340" id="PINTABLE">
          <description> ... </description>
          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
            &ip_name;/pintable/releasenotes.docx
          </pattern>
          <pattern id="file" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
            &ip_name;/pintable/&ip_name;.pintable.xlsx
          </pattern>
          <producer id="ICD-PD"/>
          <consumer id="ICD-IP"/>
          <consumer id="LAY-IP"/>
          <consumer id="PACKAGING"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="FCI"/>
          <consumer id="FCV"/>
          <consumer id="NETLIST"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 28340
        self._isReady = True
        self._addReleaseNotes()
        #workingDirName = os.path.join(self._idlower)
        self._addPattern('{}.pintable.xlsx'.format(self._ipName), id_='file',
                         prependTopCellName=False)
        self._addProducer("ICD-PD")
        self._addConsumer("ICD-IP")
        self._addConsumer("LAY-IP")
        self._addConsumer("PACKAGING")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("FCI")
        self._addConsumer("FCV")
        self._addConsumer("NETLIST")
        self._addConsumer("TE")
#
#    # PINTABLESPEC removed per bug 27765
#
    def _PKGDE(self):
        '''Complete package physical layout database created by Packaging at various design stages
           including final package tape-out that has all bump to ball connection and power delivery network. 
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared Documents/Release Management/Deliverables/PKGDE_Definition.docx

        >>> t = Template('PKGDE')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="324460" id="PKGDE">
          <description> ... </description>
          <pattern id="mcm" mimetype="application/octet-stream">
             &ip_name;/pkgde/*.mcm
          </pattern>
          <pattern id="zip">
            &ip_name;/pkgde/*.zip
          </pattern>
          <producer id="PACKAGING"/>
          <consumer id="PACKAGING"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 324460
        self._isReady = False

        self._addPattern('*.mcm', id_='mcm',
                         prependTopCellName=False)        

        self._addPattern('*.zip', id_='zip',
                         prependTopCellName=False)        

        self._addProducer("PACKAGING")
        self._addConsumer("PACKAGING")
        self._addConsumer("ICD-PD")
 
#
#
    def _PKGEE(self):
        '''Complete package IO and PDN models that extracted from package physical layout database
            for Quartus IBIS model and ICD/PE system level simulation
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared Documents/Release Management/Deliverables/PKGEE_Definition.docx

        >>> t = Template('PKGEE')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="324461" id="PKGEE">
          <description> ... </description>
          <pattern id="zip">
            &ip_name;/pkgee/*.zip
          </pattern>
          <producer id="PACKAGING"/>
          <consumer id="PACKAGING"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 324461
        self._isReady = False

        self._addPattern('*.zip', id_='zip',
                         prependTopCellName=False)        

        self._addProducer("PACKAGING")
        self._addConsumer("PACKAGING")
        self._addConsumer("ICD-PD")

    def _PNR(self):
        '''This deliverable captures all the output collateral from the PnR flow.
        Currently Nadder uses R2G2 as the POR tool/flow in this space and that flow is
        setup to populate data in these ICM deliverable directories.
           CVIMPL is an optional deliverable and meant to be the mechanism whereby
        debug with front end design/exchange is facilitated. It si NOT required.
        But IF it exists it should be used for ICC. Designers need to be aware of this
        and copy constraints to the correct location in the R2G2 flow.
           COPMLIBPHYS is required for floorplan def of core elements floorplanned by DMZ.
           PLOC file is used to distinguish shield net shapes from power net shapes.
        A utility added in the R2G2 flow for ICC generates these attributes and stores in
        the .ploc file. (Lai Chuang Teo -- developed this flow. Cheen Kok Lee added to R2G2)
        See FB 250849

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/PNR_Definition.docx

        >>> t = Template('PNR')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205451" id="PNR">
          <description> ... </description>
          <pattern id="def">
            &ip_name;/pnr/results/&cell_name;.pnr.def.gz
          </pattern>
          <pattern id="lvs_v">
            &ip_name;/pnr/results/&cell_name;.pnr.lvs.v
          </pattern>
          <pattern id="pt_v">
            &ip_name;/pnr/results/&cell_name;.pnr.pt.v
          </pattern>
          <pattern id="lef">
            &ip_name;/pnr/results/&cell_name;.pnr.lef
          </pattern>
          <pattern id="ploc">
            &ip_name;/pnr/results/&cell_name;.ploc
          </pattern>
          <milkyway id="mwLib" mimetype="application/octet-stream">
            <libpath>
              &ip_name;/pnr/&cell_name;
            </libpath>
            <lib>
              &cell_name;
            </lib>
          </milkyway>
          <producer id="SPNR"/>
          <consumer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="FCI"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 205451
        self._isReady = True


        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, 'pnr.def.gz', id_='def')
        self._addPatternWithWorkingDir(dirName, 'pnr.lvs.v', id_='lvs_v')
        self._addPatternWithWorkingDir(dirName, 'pnr.pt.v', id_='pt_v')
        self._addPatternWithWorkingDir(dirName, 'pnr.lef', id_='lef')
        self._addPatternWithWorkingDir(dirName, 'ploc', id_='ploc')
#        dirName = os.path.join(self._idlower, 'audit')
#        self._addPatternWithWorkingDir(dirName, '*', id_='audit', prependTopCellName=False)
        dirName = os.path.join(self._idlower)
        self._addMilkywayMutliCells()
        self._addProducer("SPNR")
        self._addConsumer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("FCI")
        self._addConsumer("TE")

    def _PORTLIST(self):
        '''PORTLIST exists to describe interface names and constraint rules for
        ports under different modes or attributes developed by the designer
        during their design. Two types of files are stored in this folder:
        1) The Interface definition. Interface definition will comply with the
        Verilog format and will be verified by Fishtail.
        2) Port rules will be in TCL format and will DMZ Tool. Audit files are
        also delivered in accordance with the Audit checks defined for this
        deliverable. 
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/PORTLIST_Definition.docx

        >>> t = Template('PORTLIST')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205453" id="PORTLIST">
          <description> ... </description>
          <pattern id="intfc">
            &ip_name;/portlist/&ip_name;.intfc.v
          </pattern>
          <pattern id="bind">
            &ip_name;/portlist/&ip_name;.bind.tcl
          </pattern>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 205453
        self._isReady = True

        self._addPattern('{}.intfc.v'.format(self._ipName), id_='intfc',
                         prependTopCellName=False)
        self._addPattern('{}.bind.tcl'.format(self._ipName), id_='bind',
                         prependTopCellName=False)
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")


#    def _PNRCTS(self):
#        '''Placed and clock-tree synthesized databases and files, including
#        Milkyway database, Verilog netlists, placed DEF netlist, and GDS database.
#
#        >>> t = Template('PNRCTS')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="87827" id="PNRCTS">
#          <description> ... </description>
#          <filelist id="sdc_filelist">
#            &ip_name;/pnrcts/results/&ip_name;.sdc.filelist
#          </filelist>
#          <pattern id="dc_v">
#            &ip_name;/pnrcts/results/&cell_name;.pnrcts.dc.v
#          </pattern>
#          <pattern id="def">
#            &ip_name;/pnrcts/results/&cell_name;.pnrcts.def
#          </pattern>
#          <pattern id="gds" mimetype="application/octet-stream">
#            &ip_name;/pnrcts/results/&cell_name;.pnrcts.gds
#          </pattern>
#          <pattern id="lvs_v">
#            &ip_name;/pnrcts/results/&cell_name;.pnrcts.lvs.v
#          </pattern>
#          <pattern id="pt_v">
#            &ip_name;/pnrcts/results/&cell_name;.pnrcts.pt.v
#          </pattern>
#          <pattern id="scandef">
#            &ip_name;/pnrcts/results/&cell_name;.pnrcts.scandef
#          </pattern>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/pnrcts/&ip_name;__pnrcts
#            </libpath>
#            <lib>
#              &ip_name;__pnrcts
#            </lib>
#          </milkyway>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 87827
#        self._isReady = True
#        self._addMilkywayCell()
#        dirName = os.path.join(self._idlower, 'results')
#        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._ipName),
#                                        id_='sdc_filelist')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.dc.v', id_='dc_v')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.def', id_='def')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.gds', id_='gds')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.lvs.v', id_='lvs_v')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.pt.v', id_='pt_v')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.scandef', id_='scandef')
#
#    # PNRDATA eliminated per 28490
#
#    def _PNRINTENT(self):
#        '''Input and configuration files for automatic place and route.
#
#        >>> t = Template('PNRINTENT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="42178" id="PNRINTENT">
#          <description> ... </description>
#          <pattern id="prepnrsdc">
#            &ip_name;/pnrintent/&cell_name;.*.prepnr.sdc
#          </pattern>
#          <pattern id="prepnrspec"  mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/pnrintent/&cell_name;.prepnrspec.xlsx
#          </pattern>
#          <pattern id="powerconfig">
#            &ip_name;/pnrintent/&cell_name;.powerconfig.v
#          </pattern>
#          <pattern id="powerip">
#            &ip_name;/pnrintent/&cell_name;.powerip.txt
#          </pattern>
#          <pattern id="prepnrscandef" mimetype="application/x-tcl">
#            &ip_name;/pnrintent/&cell_name;.prepnrscandef.tcl
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 42178
#        self._isReady = True
#        self._addPattern("*.prepnr.sdc", id_='prepnrsdc')
#        self._addPattern("prepnrspec.xlsx", id_='prepnrspec')
#        self._addPattern("powerconfig.v", id_='powerconfig')
#        self._addPattern("powerip.txt", id_='powerip')
#        self._addPattern("prepnrscandef.tcl", id_='prepnrscandef')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#
#    def _PNRPLACED(self):
#        '''Placed databases and files, including Milkyway DB, Verilog netlists,
#        placed DEF netlist, and GDS database.
#
#        >>> t = Template('PNRPLACED')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="87826" id="PNRPLACED">
#          <description> ... </description>
#          <filelist id="sdc_filelist">
#            &ip_name;/pnrplaced/results/&ip_name;.sdc.filelist
#          </filelist>
#          <pattern id="dc_v">
#            &ip_name;/pnrplaced/results/&cell_name;.pnrplaced.dc.v
#          </pattern>
#          <pattern id="def">
#            &ip_name;/pnrplaced/results/&cell_name;.pnrplaced.def
#          </pattern>
#          <pattern id="gds" mimetype="application/octet-stream">
#            &ip_name;/pnrplaced/results/&cell_name;.pnrplaced.gds
#          </pattern>
#          <pattern id="lvs_v">
#            &ip_name;/pnrplaced/results/&cell_name;.pnrplaced.lvs.v
#          </pattern>
#          <pattern id="pt_v">
#            &ip_name;/pnrplaced/results/&cell_name;.pnrplaced.pt.v
#          </pattern>
#          <pattern id="scandef">
#            &ip_name;/pnrplaced/results/&cell_name;.pnrplaced.scandef
#          </pattern>
#          <milkyway id="mwLib" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/pnrplaced/&ip_name;__pnrplaced
#            </libpath>
#            <lib>
#              &ip_name;__pnrplaced
#            </lib>
#          </milkyway>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 87826
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'results')
#        self._addFilelistWithWorkingDir(dirName, '{}.sdc.filelist'.format(self._ipName),
#                                        id_='sdc_filelist')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.dc.v', id_='dc_v')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.def', id_='def')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.gds', id_='gds')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.lvs.v', id_='lvs_v')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.pt.v', id_='pt_v')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.scandef', id_='scandef')
#        self._addMilkywayCell()
#
#    def _PORTMODEL(self):
#        '''Reference IP port models.
#
#        >>> t = Template('PORTMODEL')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="152938" id="PORTMODEL">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/portmodel/releasenotes.docx
#          </pattern>
#          <pattern id="bds" mimetype="text/xml">
#            &ip_name;/portmodel/bds/*.bds.xml
#          </pattern>
#          <pattern id="bbox">
#            &ip_name;/portmodel/bbox/*.v
#          </pattern>
#          <pattern id="bbox_fft">
#            &ip_name;/portmodel/bbox_fft/*.v
#          </pattern>
#          <producer id="SSD"/>
#          <consumer id="FCV"/>
#          <consumer id="SSD"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 152938
#        self._isReady = True
#        self._addReleaseNotes()
#        dirName = os.path.join(self._idlower, 'bds')
#        self._addPatternWithWorkingDir(dirName, '*.bds.xml',
#                                       id_='bds',
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'bbox')
#        self._addPatternWithWorkingDir(dirName, '*.v',
#                                       id_='bbox',
#                                       prependTopCellName=False)
#        dirName = os.path.join(self._idlower, 'bbox_fft')
#        self._addPatternWithWorkingDir(dirName, '*.v',
#                                       id_='bbox_fft',
#                                       prependTopCellName=False)
#        self._addProducer("SSD")
#        self._addConsumer("FCV")
#        self._addConsumer("SSD")
#        self._addConsumer("TE")
#
#    def _POSTPNRSCANDEF(self):
#        '''No description provided.
#
#        >>> t = Template('POSTPNRSCANDEF')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="42192" id="POSTPNRSCANDEF">
#          <description> ... </description>
#          <pattern id="file" minimum="0">
#            &ip_name;/postpnrscandef/*.spef
#          </pattern>
#          <producer id="IP-PNR"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 42192
#        self._isReady = True
#        self._addPattern('*.spef', minimum=0, prependTopCellName=False)
#        self._addProducer("IP-PNR")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#
#    def _PV(self):
#        '''RTL2GDS flow physical verification (LVS, DRC, etc) reports and spice
#        netlist used for verification.
#
#        >>> t = Template('PV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="82021" id="PV">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/pv/netlist/&cell_name;.pv.spi
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 82021
#        self._isReady = True
#        dirName = os.path.join(self._idlower, 'netlist')
#        self._addPatternWithWorkingDir(dirName, self._idlower + '.spi')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#
#    # RBC merged into BCM per Kamal Patel per 5/24/12 email
#
#    # RCE eliminated per 28504

    def _PV(self):
        '''The PV deliverable exists to store:
           1. *.LAYOUT_ERRORS
           2. *.RESULTS
           3. *.LVS_ERRORS
           4. audit.<&cellname>.pv.<ID>.xml files
           5. audit.<&cellname>.pv.f
              a. Based on /ipspec/cell_names.txt

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/PV_Definition.docx

        >>> t = Template('PV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209046" id="PV">
          <description> ... </description>
          <filelist id="audit_filelist">
            &ip_name;/pv/audit/audit.&cell_name;.pv.f
          </filelist>
          <producer id="LAY-IP"/>
          <producer id="FCI"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 209046
        self._isReady = True

        dirName = os.path.join(self._idlower, 'audit')
        self._addFilelistWithWorkingDir(dirName, 'audit.{}.pv.f'.format(self._cellName),
                                        id_='audit_filelist')
        self._addProducer("LAY-IP")
        self._addProducer("FCI")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("FCV")
        self._addConsumer("TE")

    def _R2G2(self):
        '''R2G2 is to store user input settings and scripts used by the R2G2 flow.
        It is provided as a convenience and is not an official deliverable with any checks.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/R2G2_Definition.docx

        >>> t = Template('R2G2')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="171832" id="R2G2">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/r2g2/...
          </pattern>
          <producer id="SPNR"/>
          <consumer id="SPNR"/>
        </template> '
        '''
        self._caseid = 171832
        self._isReady = True
        self._addPattern('...', prependTopCellName=False)
        self._addProducer("SPNR")
        self._addConsumer("SPNR")

#    def _RCXT(self):
#        '''Parasitic extraction data of a routed IP in SPEF format.
#
#        >>> t = Template('RCXT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="82022" id="RCXT">
#          <description> ... </description>
#          <filelist id="filelist">
#            &ip_name;/rcxt/results/&cell_name;.rcxt.filelist
#          </filelist>
#          <producer id="IP-PNR"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 82022
#        self._isReady = True
#
#        dirName = os.path.join(self._idlower, 'results')
#        # Use `&cell_name;` because this is an output
#        self._addFilelistWithWorkingDir(dirName, '{}.{}.filelist'.format(self._cellName, self._idlower))
#        self._addProducer("IP-PNR")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#
#    # REF removed per bug 28522

    def _RCXT(self):
        '''The RCXT deliverable exists to store:
             RC netlist for post-layout simulation, and Static Timing Analysis.
             Extraction output files are based on a control file list.
           Custom Extraction
           GDS|OASIS|PIPO audit.log file  &ip_name;/gds|oasis|oa/audit
           CDL audit.log file  &ip_name;/cdl/audit
           Equiv audit.log file  &ip_name;/pv/audit
           User's skip-cells audit.log file &ip_name;/ipspec/audit

           Asic Extraction
           Milkyway audit.log file  &ip_name;/mw/audit
           User's skip-cells audit.log file &ip_name;/ipspec/audit

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/RCXT_Definition.docx

        >>> t = Template('RCXT')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209048" id="RCXT">
          <description> ... </description>
          <pattern id="spf" minimum="0">
            &ip_name;/rcxt/lion2_run/&cell_name;/STAR/&cell_name;.*.SPF
          </pattern>
          <pattern id="spef" minimum="0">
            &ip_name;/rcxt/lion2_run/&cell_name;/STAR/&cell_name;.*.SPEF.gz
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 209048
        self._isReady = True
        
        dirName = os.path.join(self._idlower, 'lion2_run', self._cellName, 'STAR')
        self._addPatternWithWorkingDir(dirName, "*.SPF",
                                       id_='spf', minimum=0)
        self._addPatternWithWorkingDir(dirName, "*.SPEF.gz",
                                       id_='spef', minimum=0)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")

    def _RDF(self):
        '''RDF exists to describe Register or CRAM Definition developed by
        the designer during their design. The RDF will comply with the IP-XACT
        XML format and will be verified by Magillem tool. Audit files are also
        delivered in accordance with the Audit checks defined for this
        deliverable. Requirement of an audit check for this deliverable is
        still under evaluation.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/RDF_Definition.docx

        >>> t = Template('RDF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205454" id="RDF">
          <description> ... </description>
          <pattern id="rdf" mimetype="text/xml" minimum="0">
            &ip_name;/rdf/&cell_name;.rdf.xml
          </pattern>
          <pattern id="flist" minimum="0">
            &ip_name;/rdf/&cell_name;.rdf.filelist
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 205454
        self._isReady = True

        self._addPattern("rdf.xml", minimum=0, id_='rdf')
        self._addPattern("rdf.filelist", minimum=0, id_='flist')
        
        self._addProducer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("TE")

    def _RELDOC(self):
        '''The documentation related to the released configuration is hosted within this deliverable.
           Primarily intended to host the release notes, it is also used for Tapeout documentation,
           sign-off and any document related to a given configuration. 
             DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/RELDOC_Definition.docx

        >>> t = Template('RELDOC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="241400" id="RELDOC">
          <description> ... </description>
          <pattern id="doc" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document" minimum="0">
            &ip_name;/reldoc/releasenotes.docx 
          </pattern>
          <pattern id="txt" minimum="0">
            &ip_name;/reldoc/releasenotes.txt 
          </pattern>
          <pattern id="csv" mimetype="text/csv" minimum="0">
            &ip_name;/reldoc/tnrwaivers.csv
          </pattern>
          <producer id="ICD-IP"/>
          <producer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 241400
        self._isReady = True
        
        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, "releasenotes.docx",
                                       id_='doc', minimum=0, prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "releasenotes.txt",
                                       id_='txt', minimum=0, prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "tnrwaivers.csv",
                                       id_='csv', minimum=0, prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addProducer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("TE")

#    def _RIF(self):
#        '''Redundancy information, used to generate repaired CRAM image for
#        running redundancy simulation.
#
#        >>> t = Template('RIF')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28505" id="RIF">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/rif/&cell_name;.rif.txt
#          </pattern>
#          <producer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28505
#        self._isReady = True
#        self._addPattern("rif.txt")
#        self._addProducer("SOFTWARE-IPD")
#        self._addConsumer("SVT")

    def _RTL(self):
        '''This deliverable contains the Verilog source files and filelists for IP blocks
           Filelist are sorted into usages for design verification (dv),  synthesis (syn),
           gate-level verification (gv), and memory built-in self-test (mbist).
           These separated lists are used by flows that do not always want the full
           set of Verilog functional files.
           Additionally, it contains gate level source substitution list for pre-compiled
           or manually compiled IP modules that are meant to be replaced in the implementation
           flow. The 'fe_gln'  list is expected to point to IP in the configuration of the parent.
           Two modes of replacement are allowed, local to the IP and a global/project level.
           This document will focus on 'loacal' only.  Use DMZFlistMgr to expand the fe_gln filelist.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/RTL_Definition.docx

        >>> t = Template('RTL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
          <template caseid="205507" id="RTL">
            <description> ... </description>
          <filelist id="cell_filelist_dv">
            &ip_name;/rtl/filelists/dv/&cell_name;.f
          </filelist>
          <filelist id="cell_filelist_syn" minimum="0">
            &ip_name;/rtl/filelists/syn/&cell_name;.f
          </filelist>
          <filelist id="cell_filelist_gv" minimum="0">
            &ip_name;/rtl/filelists/gv/&cell_name;.f
          </filelist>
          <filelist id="cell_filelist_mbist" minimum="0">
            &ip_name;/rtl/filelists/mbist/&cell_name;.f
          </filelist>
          <filelist id="fe_gln" minimum="0">
            &ip_name;/rtl/filelists/fe_gln/&cell_name;.f
          </filelist>
          <pattern id="file" minimum="0">
            &ip_name;/rtl/....v
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="NETLIST"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 205507
        self._isReady = True

#        dirName = os.path.join(self._idlower, 'filelist')
#        self._addFilelistWithWorkingDir(dirName,
#                                        fileName=self._cellName + '.f',
#                                        id_='cell_filelist',
#                                        minimum = 0)

        dirName2 = os.path.join(self._idlower, 'filelists')
        self._addFilelistWithWorkingDir(dirName2 + '/dv',
                                        fileName=self._cellName + '.f',
                                        id_='cell_filelist_dv',
                                        minimum = 1)
        self._addFilelistWithWorkingDir(dirName2 + '/syn',
                                        fileName=self._cellName + '.f',
                                        id_='cell_filelist_syn',
                                        minimum = 0)
        self._addFilelistWithWorkingDir(dirName2 + '/gv',
                                        fileName=self._cellName + '.f',
                                        id_='cell_filelist_gv',
                                        minimum = 0)
        self._addFilelistWithWorkingDir(dirName2 + '/mbist',
                                        fileName=self._cellName + '.f',
                                        id_='cell_filelist_mbist',
                                        minimum = 0)
        self._addFilelistWithWorkingDir(dirName2 + '/fe_gln',
                                        fileName=self._cellName + '.f',
                                        id_='fe_gln',
                                        minimum = 0)

        self._addPattern('....v',
                         minimum=0,
                         prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("NETLIST")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("TE")



    def _RTLCOMPCHK(self):
        '''RTLCOMPCHK (RTL compile check) is needed to ensure that the RTL
        design is compilable across three simulators that used in ICE and IPD.
        The three simulators are VCS, NCSim and Modelsim. All ASIC RTL and
        custom behavioral models are required to pass RTLCOMPCHK. Deliverables
        are filelist, compile command file and log files. They are not directly
        consumed by other deliverables. It is required to be compilation error
        free to enable design work by Altera and Altera's customer.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/RTLCOMPCHK_Definition.docx

        >>> t = Template('RTLCOMPCHK')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205455" id="RTLCOMPCHK">
          <description> ... </description>
          <pattern id="cell_filelist">
            &ip_name;/rtlcompchk/filelist/&cell_name;.f
          </pattern>
          <pattern id="vcs_cmd">
            &ip_name;/rtlcompchk/vcs/&cell_name;.vcs.compile.cmd
          </pattern>
          <pattern id="vcs_log">
           &ip_name;/rtlcompchk/vcs/&cell_name;.vcs.log
          </pattern>
          <pattern id="ncsim_cmd">
            &ip_name;/rtlcompchk/ncsim/&cell_name;.ncsim.compile.cmd
          </pattern>
          <pattern id="ncsim_log">
            &ip_name;/rtlcompchk/ncsim/&cell_name;.ncsim.log
          </pattern>
          <pattern id="modelsim_cmd">
            &ip_name;/rtlcompchk/modelsim/&cell_name;.modelsim.compile.cmd
          </pattern>
          <pattern id="modelsim_log">
            &ip_name;/rtlcompchk/modelsim/&cell_name;.modelsim.log
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 205455
        self._isReady = True
        dirName = os.path.join(self._idlower, 'filelist')
        self._addPatternWithWorkingDir(dirName, 'f', id_='cell_filelist')
        for simulator in ['vcs', 'ncsim', 'modelsim']:
            dirName = os.path.join(self._idlower, simulator)
            fileName = '{}.{}.compile.cmd'.format(self._cellName, simulator)
            id_ = '{}_cmd'.format(simulator)
            self._addPatternWithWorkingDir(dirName, fileName, id_=id_,
                                           prependTopCellName=False)
            fileName = '{}.{}.log'.format(self._cellName, simulator)
            id_ = '{}_log'.format(simulator)
            self._addPatternWithWorkingDir(dirName, fileName, id_=id_,
                                           prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")
        self._addConsumer("TE")
 
    def _RV(self):
        '''This deliverable contains the ASIC and Custom IR/EM related roll up models and output files
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/RV_Definition.docx

        >>> t = Template('RV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209049" id="RV">
          <description> ... </description>
          <pattern id="rapidesd_rpt">
            &ip_name;/rv/rapidESD/esd/*.rapidesd_rpt
          </pattern>
          <pattern id="rapidesd_log">
            &ip_name;/rv/rapidESD/esd/*.totem_log
          </pattern>
          <pattern id="rapidesd_sum">
            &ip_name;/rv/rapidESD/esd/*.rapidesd_sum
          </pattern>
          <pattern id="rapidesd_audit">
            &ip_name;/rv/rapidESD/esd/*.audit_rpt
          </pattern>
          <pattern id="rapidlup_rpt">
            &ip_name;/rv/rapidESD/latchup/*.rapidesd_rpt
          </pattern>
          <pattern id="rapidlup_log">
            &ip_name;/rv/rapidESD/latchup/*.totem_log
          </pattern>
          <pattern id="rapidlup_sum">
            &ip_name;/rv/rapidESD/latchup/*.rapidesd_sum
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 209049
        self._isReady = True
        
        dirName = os.path.join(self._idlower,'rapidESD/esd')
        self._addPatternWithWorkingDir(dirName, "*.rapidesd_rpt",
                                       id_='rapidesd_rpt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.totem_log",
                                       id_='rapidesd_log', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.rapidesd_sum",
                                       id_='rapidesd_sum', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.audit_rpt",
                                       id_='rapidesd_audit', prependTopCellName=False)
        dirName = os.path.join(self._idlower,'rapidESD/latchup')
        self._addPatternWithWorkingDir(dirName, "*.rapidesd_rpt",
                                       id_='rapidlup_rpt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.totem_log",
                                       id_='rapidlup_log', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.rapidesd_sum",
                                       id_='rapidlup_sum', prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("SOFTWARE")


#    def _RTLLEC(self):
#        '''Modified RTL files for LEC and FCV flows.
#
#        >>> t = Template('RTLLEC')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="153308" id="RTLLEC">
#          <description> ... </description>
#          <pattern id="file" minimum="0">
#            &ip_name;/rtllec/*.v
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="FCV"/>
#          <consumer id="SSD"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 153308
#        self._isReady = True
#
#        self._addPattern('*.v',
#                         minimum=0,
#                         prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("FCV")
#        self._addConsumer("SSD")
#        self._addConsumer("TE")
#
#    def _RTL2GDS(self):
#        '''Configuration files for the rtl2gds system. These files are necessary
#        for reproducing rtl2gds subflow results in another workspace.
#
#        >>> t = Template('RTL2GDS')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="82173" id="RTL2GDS">
#          <description> ... </description>
#          <pattern id="file" mimetype="application/json">
#            &ip_name;/rtl2gds/*.json
#          </pattern>
#          <producer id="IP-PNR"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 82173
#        self._isReady = True
#        self._addPattern('*.json', prependTopCellName=False)
#        self._addProducer("IP-PNR")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#
#    def _SCC(self):
#        '''
#        Input and output data for static connectivity checker flow information.
#
#        Static connectivity check is run on the FCMW database, and is meant to 
#        detect top-level connectivity errors, including those that may not be caught 
#        via full-chip logic verification. SCC team receives the FCMW database, 
#        runs connectivity checks on it, and feeds back any detected connectivity 
#        error to the Netlist team as well as FCV (SVT) team. 
#
#        >>> t = Template('SCC')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="127253" id="SCC">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/scc/releasenotes.docx
#          </pattern>
#          <pattern id="aliases_cmds" mimetype="application/x-tcl">
#            &ip_name;/scc/aliases_cmds.tcl
#          </pattern>
#          <pattern id="scc" mimetype="application/vnd.ms-excel.sheet.macroEnabled.12">
#            &ip_name;/scc/SCC_*.xlsm
#          </pattern>
#          <pattern id="scc_build_commands" mimetype="application/x-tcl">
#            &ip_name;/scc/scc_build_commands.tcl
#          </pattern>
#          <pattern id="scc_load_commands" mimetype="application/x-tcl">
#            &ip_name;/scc/scc_load_commands.tcl
#          </pattern>
#          <pattern id="scc_load_commands_logical" mimetype="application/x-tcl">
#            &ip_name;/scc/scc_load_commands_logical.tcl
#          </pattern>
#          <pattern id="trace_arcs_definition" mimetype="application/x-tcl">
#            &ip_name;/scc/trace_arcs_definition.tcl
#          </pattern>
#          <producer id="SCC"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SCC"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 127253
#        self._isReady = True
#        self._addReleaseNotes()
#        self._addPattern('aliases_cmds.tcl', id_='aliases_cmds', prependTopCellName=False)
#        self._addPattern('SCC_*.xlsm', id_='scc', prependTopCellName=False)
#        self._addPattern('scc_build_commands.tcl', id_='scc_build_commands', prependTopCellName=False)
#        self._addPattern('scc_load_commands.tcl', id_='scc_load_commands', prependTopCellName=False)
#        self._addPattern('scc_load_commands_logical.tcl', id_='scc_load_commands_logical', prependTopCellName=False)
#        self._addPattern('trace_arcs_definition.tcl', id_='trace_arcs_definition', prependTopCellName=False)
#        self._addProducer('SCC')
#        self._addConsumer('PD-ICD')
#        self._addConsumer('SCC')
#        self._addConsumer('SVT')
#
#    def _SCH(self):
#        '''OpenAccess schematic database.  Associated non-OpenAccess files are
#        in SCHMISC.
#
#        >>> t = Template('SCH')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="28509" id="SCH">
#          <description> ... </description>
#          <openaccess id="schematic" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/oa/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view viewtype="oacSchematic">
#              schematic
#            </view>
#          </openaccess>
#          <openaccess id="symbol" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/oa/&ip_name;
#            </libpath>
#            <lib>
#              &ip_name;
#            </lib>
#            <cell>
#              &cell_name;
#            </cell>
#            <view viewtype="oacSchematicSymbol">
#              symbol
#            </view>
#          </openaccess>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 28509
#        self._isReady = True
#
#        # Schematic and symbol views
#        self._addOpenAccessCellView('schematic', 'oacSchematic',       id_='schematic')
#        self._addOpenAccessCellView('symbol',    'oacSchematicSymbol', id_='symbol')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("TE")
#
#    def _SCHMISC(self):
#        '''Non-OpenAccess files tightly linked to SCH deliverable.
#
#        >>> t = Template('SCHMISC')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="51367" id="SCHMISC">
#          <description> ... </description>
#          <pattern id="default_waivers" mimetype="text/xml">
#            &ip_name;/schmisc/scherc/default.waivers.xml
#          </pattern>
#          <pattern id="default_waived" mimetype="text/xml">
#            &ip_name;/schmisc/scherc/default.waived.xml
#          </pattern>
#          <pattern id="powertable" mimetype="application/x-tcl">
#            &ip_name;/schmisc/perc/&cell_name;.powertable.tcl
#          </pattern>
#          <pattern id="project_powertable" mimetype="application/x-tcl">
#            &ip_name;/schmisc/perc/project.powertable.tcl
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
##          <pattern id="cell_names">
##            &ip_name;/schmisc/&ip_name;.ip_topcell.txt
##          </pattern>
##          <pattern id="hybrid_cell">
##            &ip_name;/schmisc/&ip_name;.hybrid_cell.txt
##          </pattern>
##          <pattern id="filler_cell">
##            &ip_name;/schmisc/&ip_name;.filler_cell.txt
##          </pattern>
#
#        self._caseid = 51367
#        self._isReady = True
#        schercDirectoryName = os.path.join(self._idlower, 'scherc')
#        self._addPatternWithWorkingDir(schercDirectoryName, 
#                                       'default.waivers.xml', 
#                                       id_='default_waivers',
#                                       prependTopCellName=False)
#        self._addPatternWithWorkingDir(schercDirectoryName, 
#                                       'default.waived.xml', 
#                                       id_='default_waived',
#                                       prependTopCellName=False)
#        
#        percDirectoryName = os.path.join(self._idlower, 'perc')
#        self._addPatternWithWorkingDir(percDirectoryName, 
#                                       'powertable.tcl',
#                                       id_='powertable')
#        self._addPatternWithWorkingDir(percDirectoryName, 
#                                       'project.powertable.tcl',
#                                       id_='project_powertable', 
#                                       prependTopCellName=False)
#        
#        # See FB 119656
#        #And then see FB 133442
##        self._addPattern(self._ipName + '.ip_topcell.txt', 
##                         id_='cell_names',
##                         prependTopCellName=False)        
##        self._addPattern(self._ipName + '.hybrid_cell.txt', 
##                         id_='hybrid_cell',
##                         prependTopCellName=False)        
##        self._addPattern(self._ipName + '.filler_cell.txt', 
##                         id_='filler_cell',
##                         prependTopCellName=False)        
#        
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
        
    def _SCHMISC(self):
        '''The SCHMISC deliverable is required to run following tools/methodology/flows:
           1. PERC
              schmisc/perc/&cell_name;.waiver (optional)
              schmisc/perc/&cell_name;.perc_glitch_checker.csv (optional files, no check and checksum needed) FB#246675
              schmisc/perc/cell_tags_schmisc.perc - manual creation, can be empty if not used
              schmisc/perc/&cellname;/P1/&cellname;.perc.log (optional files, no check and checksum needed) FB#287784
              schmisc/perc/&cellname;/P1/&cellname;.perc.rep
              schmisc/perc/&cellname;/P1/&cellname;.signal.txt
              schmisc/perc/&cellname;/P1/&cellname;.power.txt
              schmisc/perc/&cellname;/P1/&cellname;.drd.dump.powertable.tcl
              schmisc/perc/&cellname;/P1/&cellname;.any.txt
              schmisc/perc/&cellname;/P1/&cellname;.lownom.txt schmisc/perc/&cellname;/P1/&cellname;.nom.txt
              schmisc/perc/&cellname;/P1/&cellname;.nv.txt
              schmisc/perc/&cellname;/P1/&cellname;.hv.txt
              schmisc/perc/&cellname;/P1/&cellname;.ehv.txt
              schmisc/perc/&cellname;/P1/&cellname;.uhv.txt
              schmisc/perc/&cellname;/P1/hvlist/*.txt (optional files, no check and checksum needed)
              schmisc/perc/&cellname;/P1/hvlist/*.tcl (optional files, no check and checksum needed)
           2. Physical (ICF HV flow, and layout critical signal flow)
              schmisc/physical/&cell_name;_critical_design_spec.xlsx - can be a dummy file if not used.
              schmisc/physical/ECO_indicator.xlsx - can be empty file if not used
           3. RV
              schmisc/rv/&cellname;.power_budget.csv
              schmisc/rv/&cellname;.spi
	   4. RCXT
              schmisc/rcxt/rcxt_non_timing_skipcells.txt (optional file)
           5. cell_type/cell_type.txt
              defines cell type for PnR. (optioanl file)

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/SCHMISC_Definition.docx

        >>> t = Template('SCHMISC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209769" id="SCHMISC">
          <description> ... </description>
          <pattern id="crtsign" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
            &ip_name;/schmisc/physical/&cell_name;_critical_design_spec.xlsx
          </pattern>
          <pattern id="eco" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
            &ip_name;/schmisc/physical/ECO_indicator.xlsx
          </pattern>
          <pattern id="perc">
            &ip_name;/schmisc/perc/cell_tags_schmisc.perc
          </pattern>
          <pattern id="waiver" minimum="0">
            &ip_name;/schmisc/perc/*.waiver
          </pattern>
          <pattern id="checker_csv" mimetype="text/csv" minimum="0">
            &ip_name;/schmisc/perc/*.perc_glitch_checker.csv
          </pattern>
          <pattern id="log" minimum="0">
            &ip_name;/schmisc/perc/*/P1/*.perc.log
          </pattern>
          <pattern id="rep">
            &ip_name;/schmisc/perc/*/P1/*.perc.rep
          </pattern>
          <pattern id="sgn">
            &ip_name;/schmisc/perc/*/P1/*.signal.txt
          </pattern>
          <pattern id="ptxt">
            &ip_name;/schmisc/perc/*/P1/*.power.txt
          </pattern>
          <pattern id="pwr">
            &ip_name;/schmisc/perc/*/P1/*.drd.dump.powertable.tcl
          </pattern>
          <pattern id="anytxt">
            &ip_name;/schmisc/perc/*/P1/*.any.txt
          </pattern>
          <pattern id="lownomtxt">
            &ip_name;/schmisc/perc/*/P1/*.lownom.txt
          </pattern>
          <pattern id="nomtxt">
            &ip_name;/schmisc/perc/*/P1/*.nom.txt
          </pattern>
          <pattern id="nvtxt">
            &ip_name;/schmisc/perc/*/P1/*.nv.txt
          </pattern>
          <pattern id="hvtxt">
            &ip_name;/schmisc/perc/*/P1/*.hv.txt
          </pattern>
          <pattern id="ehvtxt">
            &ip_name;/schmisc/perc/*/P1/*.ehv.txt
          </pattern>
          <pattern id="uhvtxt">
            &ip_name;/schmisc/perc/*/P1/*.uhv.txt
          </pattern>
          <pattern id="hvlisttxt" minimum="0">
            &ip_name;/schmisc/perc/*/P1/hvlist/*.txt
          </pattern>
          <pattern id="hvlisttcl" minimum="0">
            &ip_name;/schmisc/perc/*/P1/hvlist/*.tcl
          </pattern>
          <pattern id="rvcsv" mimetype="text/csv">
            &ip_name;/schmisc/rv/*.power_budget.csv
          </pattern>
          <pattern id="rvspi">
            &ip_name;/schmisc/rv/*.spi
          </pattern>
          <pattern id="rcxtfile" minimum="0">
            &ip_name;/schmisc/rcxt/rcxt_non_timing_skipcells.txt
          </pattern>
          <pattern id="celltype" minimum="0">
            &ip_name;/schmisc/cell_type/cell_type.txt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="LAY-IP"/>
        </template> '
        '''
        self._caseid = 209769
        self._isReady = True
        
        dirName = os.path.join(self._idlower, 'physical')
        self._addPatternWithWorkingDir(dirName, "_critical_design_spec.xlsx",
                                       id_='crtsign', addDot=False)
        self._addPatternWithWorkingDir(dirName, "ECO_indicator.xlsx",
                                       id_='eco',
                                       prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'perc')
        self._addPatternWithWorkingDir(dirName, "cell_tags_schmisc.perc",
                                       id_='perc',
                                       prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.waiver",
                                       id_='waiver', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, "*.perc_glitch_checker.csv",
                                       id_='checker_csv', prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, 'perc', '*/P1')
        self._addPatternWithWorkingDir(dirName, "*.perc.log",
                                       id_='log', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, "*.perc.rep",
                                       id_='rep', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.signal.txt",
                                       id_='sgn', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.power.txt",
                                       id_='ptxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.drd.dump.powertable.tcl",
                                       id_='pwr', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.any.txt",
                                       id_='anytxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.lownom.txt",
                                       id_='lownomtxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.nom.txt",
                                       id_='nomtxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.nv.txt",
                                       id_='nvtxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.hv.txt",
                                       id_='hvtxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.ehv.txt",
                                       id_='ehvtxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.uhv.txt",
                                       id_='uhvtxt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "hvlist/*.txt",
                                       id_='hvlisttxt', minimum=0, prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "hvlist/*.tcl",
                                       id_='hvlisttcl', minimum=0, prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'rv')
        self._addPatternWithWorkingDir(dirName, "*.power_budget.csv",
                                       id_='rvcsv', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, "*.spi",
                                       id_='rvspi', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'rcxt')
        self._addPatternWithWorkingDir(dirName, "rcxt_non_timing_skipcells.txt",
                                       id_='rcxtfile', minimum=0, prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'cell_type')
        self._addPatternWithWorkingDir(dirName, "cell_type.txt",
                                       id_='celltype', minimum=0, prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("LAY-IP")

    def _SDF(self):
        '''SDF is used to define cell and net delays for paths in ASIC style
        design. This format has a limited use model in that only TD would be
        consuming the SDF files. Two sets, one at the fastest ICE (PVT) corner
        and another at the slowest ICE corner.  A dominant corner for fast and
        slow will be picked for SDF generation flow. Note: Dominant corners in
        the INTEL process are NOT guaranteed to show ALL violations!
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/SDF_Definition.docx

        >>> t = Template('SDF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209770" id="SDF">
          <description> ... </description>
          <pattern id="file">
            &ip_name;/sdf/results/&cell_name;.*.sdf
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 209770
        self._isReady = True
        dirName = os.path.join(self._idlower, 'results')
        self._addPatternWithWorkingDir(dirName, '*.sdf')
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")

#    def _SPYGLASS(self):
#        '''Results of RTL linting with the Atreta Spyglass tool.
#
#        >>> t = Template('SPYGLASS')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="87825" id="SPYGLASS">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/spyglass/...
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 87825
#        self._isReady = True
#
#        self._addPattern('...', prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")

    def _STA(self):
        '''The STA is a placeholder for timing flow at this time.

         DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/STA_Definition.docx

        >>> t = Template('STA')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="82023" id="STA">
          <description> ... </description>
          <pattern id="list" minimum="0">
            &ip_name;/sta/results/*/&cell_name;.opin_c_total.list
          </pattern>
          <pattern id="ipf" minimum="0">
            &ip_name;/sta/results/*/&cell_name;.ptpx.ipf
          </pattern>
          <pattern id="timing" minimum="0">
            &ip_name;/sta/results/*/&cell_name;.timing
          </pattern>
          <pattern id="analysis" minimum="0">
            &ip_name;/sta/results/*/*.report_analysis_coverage
          </pattern>
          <pattern id="aocvm" minimum="0">
            &ip_name;/sta/results/*/*.report_aocvm
          </pattern>
          <pattern id="annotated" minimum="0">
            &ip_name;/sta/results/*/*.report_annotated_parasitics
          </pattern>
          <pattern id="check_timing" minimum="0">
            &ip_name;/sta/results/*/*.check_timing
          </pattern>
          <pattern id="log" minimum="0">
            &ip_name;/sta/results/*/read_parasitic.*.log
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="SPNR"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 82023
        self._isReady = True
        dirName = os.path.join(self._idlower, 'results/*')
        self._addPatternWithWorkingDir(dirName, 'opin_c_total.list',
                                        id_='list', minimum=0)
        self._addPatternWithWorkingDir(dirName, 'ptpx.ipf',
                                        id_='ipf', minimum=0)
        self._addPatternWithWorkingDir(dirName, 'timing',
                                        id_='timing', minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.report_analysis_coverage',
                                        id_='analysis', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.report_aocvm',
                                        id_='aocvm', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.report_annotated_parasitics',
                                        id_='annotated', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.check_timing',
                                        id_='check_timing', prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, 'read_parasitic.*.log',
                                        id_='log', prependTopCellName=False, minimum=0)
        self._addProducer("ICD-IP")
        self._addConsumer("SPNR")
        self._addConsumer("ICD-PD")

    def _STAMOD(self):
        '''The STAMOD deliverable is required to run STA with PrimeTime.
           The models will be in both NLDM and CCS formats, and support noise, power.
           The timing arcs will be CRAM configuration based and not MODE based.
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/STAMOD_Definition.docx

        >>> t = Template('STAMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205455" id="STAMOD">
          <description> ... </description>
          <pattern id="ccslib">
            &ip_name;/stamod/*/lib/ccs/*.lib
          </pattern>
          <pattern id="ccsdb" mimetype="application/octet-stream">
            &ip_name;/stamod/*/lib/ccs/*.db
          </pattern>
          <pattern id="nlib">
            &ip_name;/stamod/*/lib/nldm/*.lib
          </pattern>
          <pattern id="ndb" mimetype="application/octet-stream">
            &ip_name;/stamod/*/lib/nldm/*.db
          </pattern>
          <pattern id="spf">
            &ip_name;/stamod/*/spf/*.spf
          </pattern>
          <pattern id="vfile">
            &ip_name;/stamod/*/verilog/*.v
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 205455
        self._isReady = True
        dirName = os.path.join(self._idlower, '*/lib/ccs')
        self._addPatternWithWorkingDir(dirName, '*.lib', id_='ccslib',
                                           prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.db', id_='ccsdb',
                                           prependTopCellName=False)
        dirName = os.path.join(self._idlower, '*/lib/nldm')
        self._addPatternWithWorkingDir(dirName, '*.lib', id_='nlib',
                                           prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.db', id_='ndb',
                                           prependTopCellName=False)
        dirName = os.path.join(self._idlower, '*/spf')
        self._addPatternWithWorkingDir(dirName, '*.spf', id_='spf',
                                           prependTopCellName=False)
        dirName = os.path.join(self._idlower, '*/verilog')
        self._addPatternWithWorkingDir(dirName, '*.v', id_='vfile',
                                           prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
 
#    def _STARVISION(self):
#        '''StarVision tool database.  No description provided.
#
#        >>> t = Template('STARVISION')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="92321" id="STARVISION">
#          <description> ... </description>
#          <pattern id="releasenotes" mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document">
#            &ip_name;/starvision/releasenotes.docx
#          </pattern>
#          <pattern id="file" mimetype="application/octet-stream">
#            &ip_name;/starvision/&cell_name;.zdb
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <producer id="IP-PNR"/>
#          <producer id="LAYOUT"/>
#          <producer id="PD-ICD"/>
#          <producer id="TE"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 92321
#        self._isReady = True
#        
#        self._addReleaseNotes()
#
#        self._addPattern('zdb')
#        
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addProducer("IP-PNR")
#        self._addProducer("LAYOUT")
#        self._addProducer("PD-ICD")
#        self._addProducer("TE")
#        
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("TE")
#        
#    def _SUBSYSCONN(self):
#        '''Subsystem connectivity information (currently in form of TCL code):
#        IO, HSSI.
#
#        >>> t = Template('SUBSYSCONN')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="37815" id="SUBSYSCONN">
#          <description> ... </description>
#          <pattern id="file" mimetype="application/x-tcl">
#            &ip_name;/subsysconn/*.tcl
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 37815
#        self._isReady = True
#
#        self._addPattern('*.tcl', prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("PD-ICD")
#
#    def _SUBSYSMW(self):
#        '''Subsystem Milkyway database.
#
#        >>> t = Template('SUBSYSMW')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="44656" id="SUBSYSMW">
#          <description> ... </description>
#          <milkyway id="mw_logical" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/subsysmw/logical/&ip_name;__subsysmw
#            </libpath>
#            <lib>
#              &ip_name;__subsysmw
#            </lib>
#          </milkyway>
#          <milkyway id="mw_physical" mimetype="application/octet-stream">
#            <libpath>
#              &ip_name;/subsysmw/physical/&ip_name;__subsysmw
#            </libpath>
#            <lib>
#              &ip_name;__subsysmw
#            </lib>
#          </milkyway>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="PD-ICD"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 44656
#        self._isReady = True
#
#        dirName = os.path.join(self._idlower, 'logical')
#        self._addMilkywayCellWithWorkingDir(dirName, id_='mw_logical')
#        dirName = os.path.join(self._idlower, 'physical')
#        self._addMilkywayCellWithWorkingDir(dirName, id_='mw_physical')
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("PD-ICD")

    def _SYN(self):
        '''This deliverable captures all the output collateral from the SYN flow
        Currently Nadder uses R2G2 as the POR tool/flow in this space and that
        flow is setup to populate data in these ICM deliverable directories.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/SYN_Definition.docx

        >>> t = Template('SYN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205456" id="SYN">
          <description> ... </description>
          <pattern id="syn_v">
            &ip_name;/syn/results/netlist/&cell_name;.syn.v
          </pattern>
          <pattern id="sdc">
            &ip_name;/syn/results/sdc/*.sdc
          </pattern>
          <pattern id="upf_results">
            &ip_name;/syn/results/upf/&cell_name;.syn.upf
          </pattern>
          <pattern id="ddc" mimetype="application/octet-stream" minimum="0">
            &ip_name;/syn/results/ddc/&cell_name;.syn.ddc
          </pattern>
          <pattern id="tcl" minimum="0">
            &ip_name;/syn/results/fe_gln_constraints/&cell_name;.fe_gln_inst_map.tcl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="SPNR"/>
        </template> '
        '''
        self._caseid = 205456
        self._isReady = True


        dirName = os.path.join(self._idlower, 'results', 'netlist')
        self._addPatternWithWorkingDir(dirName, 'syn.v', id_='syn_v')

        dirName = os.path.join(self._idlower, 'results', 'sdc')
        self._addPatternWithWorkingDir(dirName, '*.sdc', id_='sdc', prependTopCellName=False)
        
        dirName = os.path.join(self._idlower, 'results', 'upf')
        self._addPatternWithWorkingDir(dirName, 'syn.upf', id_='upf_results')
        
        dirName = os.path.join(self._idlower, 'results', 'ddc')
        self._addPatternWithWorkingDir(dirName, 'syn.ddc', id_='ddc', minimum=0)
        
        dirName = os.path.join(self._idlower, 'results', 'fe_gln_constraints')
        self._addPatternWithWorkingDir(dirName, 'fe_gln_inst_map.tcl', id_='tcl', minimum=0)
        
        self._addProducer("ICD-IP")
        self._addConsumer("SPNR")

    # SYNTHESIS eliminated per 28513
    
#    def _TAPEOUT(self):
#        '''Final tapeout data. This is used to generate the TORF
#        (Tapeout Release Form) and then it is sent to TSMC for mask making.
#
#        >>> t = Template('TAPEOUT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="72021" id="TAPEOUT">
#          <description> ... </description>
#          <pattern id="error_signoff" mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
#            &ip_name;/tapeout/docs/&cell_name;.error_signoff.xlsx
#          </pattern>
#          <pattern id="final_verification">
#            &ip_name;/tapeout/final_verification/...
#          </pattern>
#          <pattern id="gds" mimetype="application/octet-stream">
#            &ip_name;/tapeout/gds/&cell_name;.gds.gz
#          </pattern>
#          <producer id="LAYOUT"/>
#          <consumer id="LAYOUT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 72021
#        self._isReady = True
#
#
#        dirName = os.path.join(self._idlower, 'docs')
#        self._addPatternWithWorkingDir(dirName, 'error_signoff.xlsx', id_='error_signoff')
#        dirName = os.path.join(self._idlower, 'final_verification')
#        self._addPatternWithWorkingDir(dirName, '...', prependTopCellName=False, id_='final_verification')
#        dirName = os.path.join(self._idlower, 'gds')
#        self._addPatternWithWorkingDir(dirName, 'gds.gz', id_='gds')
#        self._addProducer("LAYOUT")
#        self._addConsumer("LAYOUT")
#
    def _TIMEMOD(self):
        '''The TIMEMODEL deliverable exists to capture the timing collateral needed
        for Quartus and Global timing closure. This deliverable was originally named
        iptimemod in the 20nm projects.

           The directory structure for the TIMEMODEL deliverable can be found at:
              http://rd/ice/product/Nadder/Timing/SitePages/Timing%20Collateral%20Naming%20Conventions.aspx

           Nadder Timing Sharepoint is available at:
        http://rd/ice/product/Nadder/Timing/SitePages/Home.aspx
           General overview of delivery requirements for each stage is available at:
              http://rd/ice/product/Nadder/Timing/SitePages/Timing%20Collateral%20Deliveries.aspx

           TIMEMOD delivery instructions for placeholder collateral is available at:
        http://rd/ice/product/Nadder/Timing/SitePages/Delivering%20Placeholder%20Timing%20Collateral.aspx

           In addition, ASIC flow derived models are stored in the stage_named/ilib subdir.
        These follow ICF naming conventions and the merged version will be mapped to
        BIN names prior to delivery to Quartus.
           Proposed names:
           Libs named: &cell_name.<corner>.<parasitics_corner>.<mode>.lib
           Merged libs: &cell_name.<corner>.<parasitics_corner>.merged.lib

           Users should ensure that the list text files are saved with UNIX-style line
        endings and not Windows-style line endings. Most modern text editors can
        translate the format for you.

        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/TIMEMOD_Definition.docx

        >>> t = Template('TIMEMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="205457" id="TIMEMOD">
          <description> ... </description>
          <filelist id="filelist">
            &ip_name;/timemod/&ip_name;.*.timemod.filelist
          </filelist>
          <pattern id="ilib" minimum="0">
            &ip_name;/timemod/*/ilib/&cell_name;.*.lib
          </pattern>
          <pattern id="lib" minimum="0">
            &ip_name;/timemod/*/lib/*.lib
          </pattern>
          <pattern id="spef" minimum="0">
            &ip_name;/timemod/*/spef/*.spef.gz
          </pattern>
          <pattern id="fspef" minimum="0">
            &ip_name;/timemod/*/spef/*.speflist.f
          </pattern>
          <pattern id="spef_mapping" mimetype="text/csv" minimum="0">
            &ip_name;/timemod/*/spef/*.spef_mapping.csv
          </pattern>
          <pattern id="verilog" minimum="0">
            &ip_name;/timemod/*/verilog/*.v
          </pattern>
          <pattern id="verilogflist" minimum="0">
            &ip_name;/timemod/*/verilog/*.f
          </pattern>
          <pattern id="sdc" minimum="0">
            &ip_name;/timemod/*/sdc/*.sdc
          </pattern>
          <pattern id="spf" minimum="0">
            &ip_name;/timemod/*/spf/*.spf
          </pattern>
          <pattern id="rtl2lib" minimum="0">
            &ip_name;/timemod/placeholder/rtl2lib/*
          </pattern>
          <pattern id="bom" minimum="0">
            &ip_name;/timemod/*.bom.cfg
          </pattern>
          <pattern id="fverilog" minimum="0">
            &ip_name;/timemod/*/fverilog/*.v
          </pattern>
          <pattern id="fvspef" minimum="0">
            &ip_name;/timemod/*/fverilog/*.spef.gz
          </pattern>
          <pattern id="fverilogflist" minimum="0">
            &ip_name;/timemod/*/fverilog/*.f
          </pattern>
          <pattern id="fverilogspeflist" minimum="0">
            &ip_name;/timemod/*/fverilog/*.speflist.f
          </pattern>
          <pattern id="fsdc" minimum="0">
            &ip_name;/timemod/*/fverilog/*.sdc
          </pattern>
          <pattern id="script_pl" mimetype="application/x-perl" minimum="0">
            &ip_name;/timemod/*/scripts/*.pl
          </pattern>
          <pattern id="script_py" mimetype="text/x-python" minimum="0">
            &ip_name;/timemod/*/scripts/*.py
          </pattern>
          <pattern id="script_csh" mimetype="application/x-csh" minimum="0">
            &ip_name;/timemod/*/scripts/*.csh
          </pattern>
          <pattern id="script_tcl" minimum="0">
            &ip_name;/timemod/*/scripts/*.tcl
          </pattern>
          <pattern id="script_sh" mimetype="application/x-sh" minimum="0">
            &ip_name;/timemod/*/scripts/*.sh
          </pattern>
          <pattern id="oas" mimetype="application/octet-stream" minimum="0">
            &ip_name;/timemod/*/oasis/*.oas
          </pattern>
          <pattern id="cdl" minimum="0">
            &ip_name;/timemod/*/cdl/*.cdl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="IPD"/>
          <consumer id="SOFTWARE"/>
          <consumer id="IP-DV"/>
          <consumer id="FCV"/>
        </template> '
        '''
        self._caseid = 205457
        self._isReady = True
        dirName = os.path.join(self._idlower)
        self._addFilelistWithWorkingDir(dirName, '{}.*.timemod.filelist'.format(self._ipName),
                                        id_='filelist')

        dirName = os.path.join(self._idlower, '*', 'ilib')
        self._addPatternWithWorkingDir(dirName, '*.lib', id_='ilib',
                                       minimum=0)
        dirName = os.path.join(self._idlower, '*', 'lib')
        self._addPatternWithWorkingDir(dirName, '*.lib', id_='lib',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'spef')
        self._addPatternWithWorkingDir(dirName, '*.spef.gz', id_='spef',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.speflist.f', id_='fspef',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.spef_mapping.csv', id_='spef_mapping',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'verilog')
        self._addPatternWithWorkingDir(dirName, '*.v', id_='verilog',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.f', id_='verilogflist',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'sdc')
        self._addPatternWithWorkingDir(dirName, '*.sdc', id_='sdc',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'spf')
        self._addPatternWithWorkingDir(dirName, '*.spf', id_='spf',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, 'placeholder', 'rtl2lib')
        self._addPatternWithWorkingDir(dirName, '*', id_='rtl2lib',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, '*.bom.cfg', id_='bom',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'fverilog')
        self._addPatternWithWorkingDir(dirName, '*.v', id_='fverilog',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.spef.gz', id_='fvspef',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.f', id_='fverilogflist',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.speflist.f', id_='fverilogspeflist',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.sdc', id_='fsdc',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'scripts')
        self._addPatternWithWorkingDir(dirName, '*.pl', id_='script_pl',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.py', id_='script_py',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.csh', id_='script_csh',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.tcl', id_='script_tcl',
                                       prependTopCellName=False, minimum=0)
        self._addPatternWithWorkingDir(dirName, '*.sh', id_='script_sh',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'oasis')
        self._addPatternWithWorkingDir(dirName, '*.oas', id_='oas',
                                       prependTopCellName=False, minimum=0)
        dirName = os.path.join(self._idlower, '*', 'cdl')
        self._addPatternWithWorkingDir(dirName, '*.cdl', id_='cdl',
                                       prependTopCellName=False, minimum=0)
        self._addProducer("ICD-IP")
        self._addConsumer("IPD")
        self._addConsumer("SOFTWARE")
        self._addConsumer("IP-DV")
        self._addConsumer("FCV")

    def _TRACKPHYS(self):
        '''TRACKPHYS deliverable will be used to contain physical track assignment for
           signals and power pins. TRACKPHYS deliverable will also be used to assign
           track pattern for IPs that will go through DMZ for track assignment. 

           Background: DMZ is used to assign physical tracks to signals and power interfaces.
           The source of where each of the signals and power needs to be on will
           be stored track/trackassignment. Before a signal can be assigned to a track,
           the track pattern type must be known; stored in track/trackpattern. Otherwise,
           a track number is useless.

           TRACKPHYS will contain Excel spreadsheets. The content of the Excel spreadsheet
           will be converted to text files which will be used when invoking DMZ.
           The TRACKPHYS deliverable resides in the special physintspec variant.


        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/TRACKPHYS_Definition.docx

        >>> t = Template('TRACKPHYS')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="255069" id="TRACKPHYS">
          <description> ... </description>
          <pattern id="agmnd" mimetype="application/vnd.ms-excel.sheet.macroEnabled.12">
            &ip_name;/trackphys/trackassignment/excel/ND*.xlsm
          </pattern>
          <pattern id="gtp" mimetype="application/vnd.ms-excel.sheet.macroEnabled.12">
            &ip_name;/trackphys/trackassignment/excel/GenerateTrackPattern.xlsm
          </pattern>
          <pattern id="agmtcl">
            &ip_name;/trackphys/trackassignment/tcl/*.track.tcl
          </pattern>
          <pattern id="ptnnd" mimetype="application/vnd.ms-excel.sheet.macroEnabled.12">
            &ip_name;/trackphys/trackpattern/excel/NDTrackPattern.xlsm
          </pattern>
          <pattern id="ptntcl">
            &ip_name;/trackphys/trackpattern/tcl/trackpattern.tcl
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
        </template> '
        '''
        self._caseid = 255069
        self._isReady = True
        dirName = os.path.join(self._idlower, 'trackassignment/excel')
        self._addPatternWithWorkingDir(dirName, 'ND*.xlsm',
                                       id_='agmnd', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'GenerateTrackPattern.xlsm',
                                       id_='gtp', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'trackassignment/tcl')
        self._addPatternWithWorkingDir(dirName, '*.track.tcl',
                                       id_='agmtcl', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'trackpattern/excel')
        self._addPatternWithWorkingDir(dirName, 'NDTrackPattern.xlsm',
                                       id_='ptnnd', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'trackpattern/tcl')
        self._addPatternWithWorkingDir(dirName, 'trackpattern.tcl',
                                       id_='ptntcl', prependTopCellName=False)

        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")


#    def _TV(self):
#        '''Timing verification data.
#
#        >>> t = Template('TV')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="132008" id="TV">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/tv/...
#          </pattern>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 132008
#        self._isReady = True
#
#        self._addPattern('...', prependTopCellName=False)
#

    def _UPF(self):
        '''This deliverable contains all the IP level UPF files. UPF is 'Unified Power Format'
        file which specifies the power intent of each IP block.  This also contains the '.lib'
        files which are compatible with the UPF files per IP. There should be a separate directory
        underneath called 'Verdi' for running and debugging VSI-LP tool.
        following files are required for all IPs:
        &ip_name;/upf/netlist/&cell_name;.upf 
        &ip_name;/upf/netlist/&cell_name;.vsi.tcl 
        &ip_name;/upf/netlist/reports/&cell_name;.report_lp.rpt
        &ip_name;/upf/netlist/reports/&cell_name;.report_lp.filtered.rpt
        &ip_name;/upf/netlist/reports/&cell_name;.report_lp.waive.rpt
        &ip_name;/upf/netlist/perc/&cell_name;.signal.powertable.tcl
        &ip_name;/upf/netlist/perc/&cell_name;.cell_tags_upf.perc 
        following files are required for ASIC IPs:
        &ip_name;/upf/rtl/&cell_name;.upf 
        &ip_name;/upf/rtl/&cell_name;.vsi.tcl 
        &ip_name;/upf/rtl/reports/&cell_name;.report_lp.rpt 
        &ip_name;/upf/rtl/reports/&cell_name;.report_lp.filtered.rpt 
        &ip_name;/upf/rtl/reports/&cell_name;.report_lp.waive.rpt 
        following files are reuired for CUSTOM IPs:
        &ip_name;/upf/netlist/&cell_name;.v
        &ip_name;/upf/netlist/&cell_name;.lib
        &ip_name;/upf/netlist/&cell_name;.ldb
        Since we have problem to distinguish it, all of exclusives are mark as optional.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/UPF_Definition.docx

        >>> t = Template('UPF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209037" id="UPF">
          <description> ... </description>
          <pattern id="tcl_file" minimum="0">
          &ip_name;/upf/rtl/*.vsi.tcl
          </pattern>
          <pattern id="upf_rpt" minimum="0">
          &ip_name;/upf/rtl/reports/*.report_lp.rpt
          </pattern>
          <pattern id="upf_rptfilter" minimum="0">
          &ip_name;/upf/rtl/reports/*.report_lp.filtered.rpt
          </pattern>
          <pattern id="upf_rptwaiver" minimum="0">
          &ip_name;/upf/rtl/reports/*.report_lp.waive.rpt
          </pattern>
          <pattern id="ntcl_file">
          &ip_name;/upf/netlist/*.vsi.tcl
          </pattern>
          <pattern id="nupf_rpt">
          &ip_name;/upf/netlist/reports/*.report_lp.rpt
          </pattern>
          <pattern id="nupf_rptfilter">
          &ip_name;/upf/netlist/reports/*.report_lp.filtered.rpt
          </pattern>
          <pattern id="nupf_rptwaiver">
          &ip_name;/upf/netlist/reports/*.report_lp.waive.rpt
          </pattern>
          <pattern id="npwrtble">
          &ip_name;/upf/netlist/perc/*.signal.powertable.tcl
          </pattern>
          <pattern id="ptag">
          &ip_name;/upf/netlist/perc/*.cell_tags_upf.perc
          </pattern>
          <pattern id="v_file" minimum="0">
          &ip_name;/upf/netlist/*.v
          </pattern>
          <pattern id="upf_lib" minimum="0">
          &ip_name;/upf/netlist/*.lib
          </pattern>
          <pattern id="upf_db" mimetype="application/octet-stream" minimum="0">
          &ip_name;/upf/netlist/*.ldb
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 209037
        self._isReady = True

        dirName = os.path.join(self._idlower, 'rtl')
        self._addPatternWithWorkingDir(dirName, '*.vsi.tcl',
                id_='tcl_file', minimum=0, prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'rtl/reports')
        self._addPatternWithWorkingDir(dirName, '*.report_lp.rpt',
                id_='upf_rpt', minimum=0, prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.report_lp.filtered.rpt',
                id_='upf_rptfilter', minimum=0, prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.report_lp.waive.rpt',
                id_='upf_rptwaiver', minimum=0, prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'netlist')
        self._addPatternWithWorkingDir(dirName, '*.vsi.tcl',
                id_='ntcl_file', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'netlist/reports')
        self._addPatternWithWorkingDir(dirName, '*.report_lp.rpt',
                id_='nupf_rpt', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.report_lp.filtered.rpt',
                id_='nupf_rptfilter', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.report_lp.waive.rpt',
                id_='nupf_rptwaiver', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'netlist/perc')
        self._addPatternWithWorkingDir(dirName, '*.signal.powertable.tcl',
                id_='npwrtble', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.cell_tags_upf.perc',
                id_='ptag', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'netlist')
        self._addPatternWithWorkingDir(dirName, '*.v',
                id_='v_file', minimum=0, prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.lib', minimum=0,
                id_='upf_lib', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, '*.ldb', minimum=0,
                id_='upf_db', prependTopCellName=False)

        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("SOFTWARE")

    def _UPFFC(self):
        '''This deliverable contains all the IP level UPFFC files. UPFFC is 'Unified Power Format'
        file which specifies the power intent of each IP block.  This also contains the '.lib'
        files which are compatible with the UPFFC files per IP. There should be a separate directory
        underneath called 'Verdi' for running and debugging VSI-LP tool.
        DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/UPFFC_Definition.docx

        >>> t = Template('UPFFC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209703" id="UPFFC">
          <description> ... </description>
          <pattern id="topupf">
          &ip_name;/upffc/top.upf
          </pattern>
          <pattern id="pinupf">
          &ip_name;/upffc/pin.upf
          </pattern>
          <pattern id="upf_rpt">
          &ip_name;/upffc/Verdi/reports/report_lp.rpt
          </pattern>
          <pattern id="upf_rptfilter">
          &ip_name;/upffc/Verdi/reports/report_lp.filtered.rpt
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="ICD-PD"/>
          <consumer id="SOFTWARE"/>
        </template> '
        '''
        self._caseid = 209703
        self._isReady = True

        dirName = os.path.join(self._idlower)
        self._addPatternWithWorkingDir(dirName, 'top.upf',
                id_='topupf', prependTopCellName=False)
        self._addPatternWithWorkingDir(dirName, 'pin.upf',
                id_='pinupf', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'Verdi/reports')
        self._addPatternWithWorkingDir(dirName, 'report_lp.rpt',
                id_='upf_rpt', prependTopCellName=False)
        dirName = os.path.join(self._idlower, 'Verdi/reports')
        self._addPatternWithWorkingDir(dirName, 'report_lp.filtered.rpt',
                id_='upf_rptfilter', prependTopCellName=False)
        self._addProducer("ICD-IP")
        self._addConsumer("ICD-PD")
        self._addConsumer("SOFTWARE")

#    def _VPD(self):
#        '''Verification planning document for the IP/MegaIP/Sub-system.
#        It can consist of zero, one or multiple Word documents.
#
#        >>> t = Template('VPD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="52302" controlled="no" id="VPD" versioned="no">
#          <description> ... </description>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 52302
#        self._isReady = True
#        self._controlled = False
#        self._versioned = False
##        self._addPattern('*.vpd.docx', prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        
#    def _VPOUT(self):
#        '''Verification Platform (VP) results.
#
#        >>> t = Template('VPOUT')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="84746" id="VPOUT">
#          <description> ... </description>
#          <pattern id="report">
#            &ip_name;/vpout/PerformedChecksReport.txt
#          </pattern>
#          <pattern id="xunit" mimetype="text/xml">
#            &ip_name;/vpout/&cell_name;/&deliverable_name;.xunit.xml
#          </pattern>
#          <producer id="IP-ICD-ANALOG"/>
#          <producer id="IP-ICD-ASIC"/>
#          <producer id="IP-ICD-DIGITAL"/>
#          <producer id="IP-ICD-MIXEDCUSTOM"/>
#          <producer id="IP-PNR"/>
#          <producer id="LAYOUT"/>
#          <producer id="PACKAGING"/>
#          <producer id="PD-ICD"/>
#          <producer id="SOFTWARE-IPD"/>
#          <producer id="SVT"/>
#          <producer id="TE"/>
#          <consumer id="IP-ICD-ANALOG"/>
#          <consumer id="IP-ICD-ASIC"/>
#          <consumer id="IP-ICD-DIGITAL"/>
#          <consumer id="IP-ICD-MIXEDCUSTOM"/>
#          <consumer id="IP-PNR"/>
#          <consumer id="LAYOUT"/>
#          <consumer id="PACKAGING"/>
#          <consumer id="PD-ICD"/>
#          <consumer id="SOFTWARE-IPD"/>
#          <consumer id="SVT"/>
#          <consumer id="TE"/>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 84746
#        self._isReady = True
#
#        self._addPattern('PerformedChecksReport.txt', id_='report', prependTopCellName=False)
#        self._addPattern('{}/{}.xunit.xml'.format(self._cellName, self._deliverableName),
#                         id_='xunit', prependTopCellName=False)
#        self._addProducer("IP-ICD-ANALOG")
#        self._addProducer("IP-ICD-ASIC")
#        self._addProducer("IP-ICD-DIGITAL")
#        self._addProducer("IP-ICD-MIXEDCUSTOM")
#        self._addProducer("IP-PNR")
#        self._addProducer("LAYOUT")
#        self._addProducer("PACKAGING")
#        self._addProducer("PD-ICD")
#        self._addProducer("SOFTWARE-IPD")
#        self._addProducer("SVT")
#        self._addProducer("TE")
#        self._addConsumer("IP-ICD-ANALOG")
#        self._addConsumer("IP-ICD-ASIC")
#        self._addConsumer("IP-ICD-DIGITAL")
#        self._addConsumer("IP-ICD-MIXEDCUSTOM")
#        self._addConsumer("IP-PNR")
#        self._addConsumer("LAYOUT")
#        self._addConsumer("PACKAGING")
#        self._addConsumer("PD-ICD")
#        self._addConsumer("SOFTWARE-IPD")
#        self._addConsumer("SVT")
#        self._addConsumer("TE")
#
#    def _WILD(self):
#        '''Unstructured deliverable where anything goes.
#        Named in honor of Carl Dealy.
#
#        >>> t = Template('WILD')
#        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <template caseid="46352" id="WILD">
#          <description> ... </description>
#          <pattern id="file">
#            &ip_name;/wild/...
#          </pattern>
#          <renamer>
#            unknownRenamer
#          </renamer>
#        </template> '
#        '''
#        self._caseid = 46352
#        self._isReady = True
#        self._controlled = True
#        self._versioned = True
#        self._addPattern('...', prependTopCellName=False)

    def _YX2GLN(self):
        '''YX is an abstraction tool that used to translate the transistor netlist into Gate level model for ATPG and LEC usage
           DOC: http://rd/ice/product/Nadder/NadderPlanning/Shared%20Documents/Release%20Management/Deliverables/YX2GLN_Definition.docx

        >>> t = Template('YX2GLN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <template caseid="209041" id="YX2GLN">
          <description> ... </description>
          <pattern id="tf">
            &ip_name;/yx2gln/directives/&cell_name;.xe_tf
          </pattern>
          <pattern id="ud">
            &ip_name;/yx2gln/directives/&cell_name;.xe_ud
          </pattern>
          <pattern id="atpgud">
            &ip_name;/yx2gln/directives/&cell_name;_atpg.xe_ud
          </pattern>
          <pattern id="lecud">
            &ip_name;/yx2gln/directives/&cell_name;_lec.xe_ud
          </pattern>
          <pattern id="lmv">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;.xe_lm_v
          </pattern>
          <pattern id="flatud">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;.xe_flattened_ud
          </pattern>
          <pattern id="report">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;.xe_report
          </pattern>
          <pattern id="imap">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;.xe_lm_inst_map
          </pattern>
          <pattern id="nmap">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;.xe_lm_net_map
          </pattern>
          <pattern id="log">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;.xe_log
          </pattern>
          <pattern id="alog">
            &ip_name;/yx2gln/ATPG_model/&cell_name;/&cell_name;_summary.log
          </pattern>
          <pattern id="llmv">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;.xe_lm_v
          </pattern>
          <pattern id="lflatud">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;.xe_flattened_ud
          </pattern>
          <pattern id="lreport">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;.xe_report
          </pattern>
          <pattern id="limap">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;.xe_lm_inst_map
          </pattern>
          <pattern id="lnmap">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;.xe_lm_net_map
          </pattern>
          <pattern id="llog">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;.xe_log
          </pattern>
          <pattern id="lalog">
            &ip_name;/yx2gln/LEC_model/&cell_name;/&cell_name;_summary.log
          </pattern>
          <producer id="ICD-IP"/>
          <consumer id="SPNR"/>
          <consumer id="TE"/>
        </template> '
        '''
        self._caseid = 209041
        self._isReady = True
        dirName = os.path.join(self._idlower, 'directives')
        self._addPatternWithWorkingDir(dirName, 'xe_tf', id_='tf')
        self._addPatternWithWorkingDir(dirName, 'xe_ud', id_='ud')
        self._addPatternWithWorkingDir(dirName, '_atpg.xe_ud', addDot=False, id_='atpgud')
        self._addPatternWithWorkingDir(dirName, '_lec.xe_ud', addDot=False, id_='lecud')
        dirName = os.path.join(self._idlower, 'ATPG_model', self._cellName)
        self._addPatternWithWorkingDir(dirName, 'xe_lm_v', id_='lmv')
        self._addPatternWithWorkingDir(dirName, 'xe_flattened_ud', id_='flatud')
        self._addPatternWithWorkingDir(dirName, 'xe_report', id_='report')
        self._addPatternWithWorkingDir(dirName, 'xe_lm_inst_map', id_='imap')
        self._addPatternWithWorkingDir(dirName, 'xe_lm_net_map', id_='nmap')
        self._addPatternWithWorkingDir(dirName, 'xe_log', id_='log')
        self._addPatternWithWorkingDir(dirName, '_summary.log', addDot=False, id_='alog')
        dirName = os.path.join(self._idlower, 'LEC_model', self._cellName)
        self._addPatternWithWorkingDir(dirName, 'xe_lm_v', id_='llmv')
        self._addPatternWithWorkingDir(dirName, 'xe_flattened_ud', id_='lflatud')
        self._addPatternWithWorkingDir(dirName, 'xe_report', id_='lreport')
        self._addPatternWithWorkingDir(dirName, 'xe_lm_inst_map', id_='limap')
        self._addPatternWithWorkingDir(dirName, 'xe_lm_net_map', id_='lnmap')
        self._addPatternWithWorkingDir(dirName, 'xe_log', id_='llog')
        self._addPatternWithWorkingDir(dirName, '_summary.log', addDot=False, id_='lalog')
        self._addProducer("ICD-IP")
        self._addConsumer("SPNR")
        self._addConsumer("TE")

        
if __name__ == "__main__":
    # Running DeliverableFTemplate_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()

