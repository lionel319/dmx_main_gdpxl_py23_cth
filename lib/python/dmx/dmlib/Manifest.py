#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011-2015 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/Manifest.py#1 $

"""
The `Manifest` API provides simple, direct access to the file locations and
predecessor/successor relationships defined in the
`templateset <http://sw-wiki/twiki/bin/view/DesignAutomation/Templateset>`_
XML.

The `Manifest` API is used by applications like the :doc:`expandfilelist`,
:doc:`graph`, :doc:`listcheckers`, :doc:`ipcheck` and the :doc:`vp`.

Usage examples appear in the documentation below.  For further usage examples,
see :py:class:`dmx.dmlib.Graph`.
"""


from future import standard_library
standard_library.install_aliases()
from builtins import str
from past.builtins import basestring
from builtins import object
import collections
from xml.etree.ElementTree import ElementTree, XMLParser, tostring
from xml.dom import minidom
import os
import textwrap
from io  import StringIO

from dmx.dmlib.templateset.filebase import FileBase
from dmx.dmlib.dmError import dmError
from dmx.dmlib.templateset.template import Template
from dmx.dmlib.templateset.pattern import Pattern
from dmx.dmlib.templateset.filelist import Filelist
from dmx.dmlib.templateset.milkyway import Milkyway
from dmx.dmlib.templateset.openaccess import OpenAccess
from dmx.dmlib.templateset.totem import Totem
import dmx.dmlib.deliverables.utils.General as General # 


class Manifest(object):
    '''Parse the deliverable templateset XML into
    an :py:class:`xml.etree.ElementTree.Element`.
    A `ParseError` exception is raised if the XML is invalid. 
    
    `Manifest` supports substitution of values for
    `entity references <http://www.ibm.com/developerworks/xml/library/x-tipentref/index.html>`_.
    The following entity reference values are always defined:
    
    * The value of entity `&ip_name;` is the value of the `ip_name` argument
    * The value of entity `&cell_name;` is the value of the `cell_name` argument. \
      The default is the value of the `ip_name` argument.
    * The value of entity `&deliverable_name;` is the value of the `deliverable_name` \
      argument.  The default is `DELIVERABLE_NAME_UNDEFINED`.

    Use the `entityValues` dictionary argument to specify values for any other
    XML entities that appear in the templateset.

    The `templatesetString` argument is only for testing and examples (as in the
    example below).  The default is the templateset packaged in the same
    `icd_cad_dm` ARC resource with :py:class:`dmx.dmlib.Manifest`.
    The default is appropriate for all practical applications.  If you need it,
    `templatesetFileName()` returns the default templateset file name.
    
    Suppose the templateset contains a deliverable `TEST` that
    contains a pattern named `xunit`.  :py:class:`dmx.dmlib.Manifest` is instantiated
    specifying values for `&ip_name;` and optionally `&cell_name;` and
    `&deliverable_name;`.
    Then, the `getPattern()` method can be used to retrieve the
    name(s) of the file(s) in the `xunit` pattern:
    
    >>> templatesetXml = """<?xml version="1.0" encoding="utf-8"?>
    ...     <templateset>
    ...        <template id="TEST">
    ...            <pattern id="xunit">
    ...                &ip_name;/&cell_name;/&deliverable_name;.xunit.xml
    ...            </pattern>
    ...        </template>
    ...    </templateset>"""
    >>> manifest = Manifest('ip1', 'cella', 'DEL',
    ...                     templatesetString=templatesetXml)
    >>> manifest.getPattern('TEST', 'xunit')
    'ip1/cella/DEL.xunit.xml'
    
    Again, the `templatesetString` argument is not used in practical applications.
    It is used above only to explicitly show the templateset contents and to
    decouple the example from the real templateset.
    '''
    deliverableNameDefault = 'DELIVERABLE_NAME_UNDEFINED'
    def __init__(self, #dangerous default pylint: disable=W0102  
                 ip_name,
                 cell_name=None,
                 deliverable_name=None,     #pylint: disable=C0103
                 templatesetString=None,
                 entityValues={}):          #dangerous default pylint: disable=W0102  

        self._ipNameArg = ip_name             #pylint: disable=C0103
        self._cellNameArg = cell_name
        self._deliverableNameArg = deliverable_name
        self._templatesetStringArg = templatesetString
        self._entityValuesArg = entityValues

        self._ipName = ip_name             #pylint: disable=C0103
        self._cellName = (cell_name if cell_name is not None
                           else ip_name)    #pylint: disable=C0103
        self._deliverableName = (deliverable_name if deliverable_name is not None
                                 else Manifest.deliverableNameDefault)
        parser = XMLParser()
        parser.parser.UseForeignDTD(True)
        parser.entity = entityValues
        parser.entity['ip_name'] = self._ipName
        parser.entity['cell_name'] = self.cell_name
        parser.entity['deliverable_name'] = self._deliverableName

        etree = ElementTree()
        if templatesetString is None:
            templatesetFile = open(self.templatesetFileName())
        else:
            templatesetFile = StringIO(templatesetString)
        self._rootElement = etree.parse(templatesetFile, parser=parser)
        templatesetFile.close()
        self._successors = None
        self._predecessors = None
        self._allAliases = None
        self._allTeams = None
        self._allDeliverables = None

    @classmethod
    def templatesetFileName(cls):
        '''Return the path to the templateset file for this version of DM.
        
        >>> Manifest.templatesetFileName()      #doctest: +ELLIPSIS
        '.../data/templateset.xml'
        '''
        dmRoot = os.path.dirname(__file__)
        return os.path.join(dmRoot, 'data', 'templateset.xml')

    @property
    def ip_name(self):
        '''The IP name as specified upon instantiation.

        >>> manifest = Manifest('testip1', templatesetString='<?xml version="1.0" encoding="utf-8"?><templateset><template /></templateset>')
        >>> manifest.ip_name
        'testip1'
        '''
        return self._ipName
    
    @property
    def cell_name(self):
        '''The cell name as specified upon instantiation.

        >>> manifest = Manifest('testip1', cell_name='topcell1', templatesetString='<?xml version="1.0" encoding="utf-8"?><templateset><template /></templateset>')
        >>> manifest.cell_name
        'topcell1'
        
        If no cell name was specified, it defaults to the specified IP name.

        >>> manifest = Manifest('testip1', templatesetString='<?xml version="1.0" encoding="utf-8"?><templateset><template /></templateset>')
        >>> manifest.cell_name
        'testip1'
        '''
        return self._cellName
    
    @property
    def deliverable_name(self):
        '''The deliverable name as specified upon instantiation.
        
        Note that the XML entity &deliverable_name; is used only in deliverable
        IPSPEC.  If you are not interested in deliverable IPSPEC, you are not
        interested in property `deliverable_name`.
        
        >>> manifest = Manifest('testip1', deliverable_name='DELIV', templatesetString='<?xml version="1.0" encoding="utf-8"?><templateset><template /></templateset>')
        >>> manifest.deliverable_name
        'DELIV'
        
        If no deliverable name was specified, it defaults to
        "DELIVERABLE_NAME_UNDEFINED"::
        
        >>> manifest = Manifest('testip1', templatesetString='<?xml version="1.0" encoding="utf-8"?><templateset><template /></templateset>')
        >>> manifest.deliverable_name
        'DELIVERABLE_NAME_UNDEFINED'
        '''
        return self._deliverableName
    
    @property
    def rootElement(self):
        '''
        The :py:class:`xml.etree.ElementTree` root `Element`. 
        Although it should not be necessary,
        through this property you can access the entire XML tree using
        :py:class:`xml.etree.ElementTree.Element` methods.
        
        >>> manifest = Manifest('testip1',templatesetString='<?xml version="1.0" encoding="utf-8"?><templateset><template /></templateset>')
        >>> manifest.rootElement.tag
        'templateset'
        '''
        return self._rootElement
   
    @property    
    def allAliases(self):
        """The set of all alias names that are defined.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <alias id="ALIAS0"/>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...        <alias id="ALIAS2">
        ...          <member> DEL3 </member>
        ...          <member> ALIAS0 </member>
        ...          <member> ALIAS1 </member>
        ...          <member> DEL4 </member>
        ...        </alias>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.allAliases
        set(['ALIAS2', 'ALIAS0', 'ALIAS1'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.allAliases
        >>> ignoredValue = s.pop()
        >>> manifest.allAliases
        set(['ALIAS2', 'ALIAS0', 'ALIAS1'])
        """
        self._buildAllAliases()
        return self._allAliases.copy()

    @property    
    def allTeams(self):
        """The set of all team names that are defined.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST1">
        ...           <producer id="A-TEAM"/>
        ...           <producer id="B-TEAM"/>
        ...           <consumer id="C-TEAM"/>
        ...         </template>
        ...        <template id="TEST2">
        ...           <producer id="C-TEAM"/>
        ...           <producer id="D-TEAM"/>
        ...           <producer id="E-TEAM"/>
        ...           <consumer id="F-TEAM"/>
        ...           <consumer id="G-TEAM"/>
        ...         </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.allTeams
        set(['E-TEAM', 'B-TEAM', 'D-TEAM', 'C-TEAM', 'F-TEAM', 'G-TEAM', 'A-TEAM'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.allTeams
        >>> ignoredValue = s.pop()
        >>> manifest.allTeams
        set(['E-TEAM', 'B-TEAM', 'D-TEAM', 'C-TEAM', 'F-TEAM', 'G-TEAM', 'A-TEAM'])
        """
        self._buildAllTeams()
        return self._allTeams.copy()

    @property    
    def predecessors(self):
        """A dictionary whose keys are deliverable names and the value is the
        set of predecessor deliverable names.
        
        Use this property only when you want to examine all the predecessors at
        once.  To get the predecessor(s) for a certain deliverable, use
        `getDeliverablePredecessor()`.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...    <templateset>
        ...      <template id="UNCONNECTED" />
        ...      
        ...      <template id="SUCCESSOR1" />
        ...      <template id="SUCCESSOR2" />
        ...      <template id="SUCCESSOR3" />
        ...      
        ...      <template id="PREDECESSOR1" />
        ...      <template id="PREDECESSOR2" />
        ...      <template id="PREDECESSOR3" />
        ...      
        ...      <successor id="SUCCESSOR1">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR2</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR2">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR3">
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.predecessors
        {'SUCCESSOR1': set(['PREDECESSOR1', 'PREDECESSOR2']), 'SUCCESSOR2': set(['PREDECESSOR1', 'PREDECESSOR3']), 'SUCCESSOR3': set(['PREDECESSOR3'])}
        >>>
        >>> # popitem() can be used to access members without harming the database
        >>> d = manifest.predecessors
        >>> ignoredValue = d.popitem()
        >>> manifest.predecessors
        {'SUCCESSOR1': set(['PREDECESSOR1', 'PREDECESSOR2']), 'SUCCESSOR2': set(['PREDECESSOR1', 'PREDECESSOR3']), 'SUCCESSOR3': set(['PREDECESSOR3'])}
        """
        if self._predecessors is None:
            self._buildPredecessorSuccessorDatabase()
        return self._predecessors.copy()

    @property    
    def successors(self):
        """Get a set of the successor(s) of the specified deliverable.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...    <templateset>
        ...      <template id="UNCONNECTED" />
        ...      
        ...      <template id="SUCCESSOR1" />
        ...      <template id="SUCCESSOR2" />
        ...      <template id="SUCCESSOR3" />
        ...      
        ...      <template id="PREDECESSOR1" />
        ...      <template id="PREDECESSOR2" />
        ...      <template id="PREDECESSOR3" />
        ...      
        ...      <successor id="SUCCESSOR1">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR2</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR2">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR3">
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.successors
        {'PREDECESSOR1': set(['SUCCESSOR1', 'SUCCESSOR2']), 'PREDECESSOR3': set(['SUCCESSOR2', 'SUCCESSOR3']), 'PREDECESSOR2': set(['SUCCESSOR1'])}
        >>>
        >>> # popitem() can be used to access members without harming the database
        >>> d = manifest.successors
        >>> ignoredValue = d.popitem()
        >>> manifest.successors
        {'PREDECESSOR1': set(['SUCCESSOR1', 'SUCCESSOR2']), 'PREDECESSOR3': set(['SUCCESSOR2', 'SUCCESSOR3']), 'PREDECESSOR2': set(['SUCCESSOR1'])}
        """
        if self._successors is None:
            self._buildPredecessorSuccessorDatabase()
        return self._successors.copy()

    def isTeam(self, teamName):
        """Is this producer/consumer team defined?

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST1">
        ...           <producer id="A-TEAM"/>
        ...           <consumer id="B-TEAM"/>
        ...         </template>
        ...        <template id="TEST2">
        ...           <producer id="C-TEAM"/>
        ...           <consumer id="D-TEAM"/>
        ...         </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.isTeam('A-TEAM')
        True
        >>> manifest.isTeam('B-TEAM')
        True
        >>> manifest.isTeam('C-TEAM')
        True
        >>> manifest.isTeam('D-TEAM')
        True
        >>> manifest.isTeam('NONEXISTENT')
        False
        """
        self._buildAllTeams()
        return teamName in self._allTeams
        

    def _buildAllTeams(self):
        '''Build the set of all team names if necessary.  This method is tested in
        the allTeams property.
        '''
        if self._allTeams is not None:
            # already built
            return
        self._allTeams = set()
        for template in self._rootElement.iterfind('template'):
            for item in template.iterfind('producer'):
                self._allTeams.add(item.get('id'))
            for item in template.iterfind('consumer'):
                self._allTeams.add(item.get('id'))


    def reportDeliverables (self, deliverableNames, includeFilePatterns=False):
        """Return a human-readable report of each of the specified deliverables:

        * Aliases that contain the deliverable
        * Predecessors and successors of the deliverable
        * Patterns, filelists, OpenAccess and Milkyway databases in the deliverable
              
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template caseid="100" id="TEST1">
        ...           <description> Describe TEST1. </description>
        ...           <pattern id="one" minimum="1">
        ...              &ip_name;/icc/&cell_name;.txt
        ...           </pattern>
        ...           <producer id="SOFTWARE-IPD"/>
        ...           <consumer id="SVT"/>
        ...        </template>
        ...
        ...        <template caseid="200" id="TEST2">
        ...           <description> Describe TEST2. </description>
        ...           <filelist id="list">
        ...             &ip_name;/icc/&ip_name;.filelist
        ...           </filelist>
        ...           <producer id="SOFTWARE-IPD"/>
        ...           <consumer id="LAYOUT"/>
        ...        </template>
        ...
        ...      <successor id="TEST2">
        ...        <predecessor>TEST1</predecessor>
        ...      </successor>
        ...
        ...      <alias id="ALIAS12">
        ...        <member>TEST1</member>
        ...        <member>TEST2</member>
        ...      </alias>
        ...    </templateset>'''
        >>> manifest = Manifest('ip1', 'cella', templatesetString=templatesetXML)
        >>> manifest.reportDeliverables(['TEST1']) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        "Deliverable 'TEST1' (case 100):\\nDescribe TEST1.\\n\\n  Produced by 'SOFTWARE-IPD'\\n  Consumed by 'SVT'\\n\\n  Member of aliases 'ALIAS12'\\n\\n  No predecessors\\n  Successors 'TEST2'\\n\\n  ip1/icc/cella.txt    Minimum 1 file, logical name 'one'\\n\\n"
        """
        report = []
        for deliverableName in deliverableNames:
            caseId = self.getDeliverableCaseId(deliverableName)
            report.append("Deliverable '{}' (case {}):".format (deliverableName,
                                                                caseId))
            description = self.getDeliverableDescription (deliverableName)
            report.append (textwrap.fill (description, width=80))
            report.append ('')
            report.extend (self._reportDeliverableProducers (deliverableName)) 
            report.extend (self._reportDeliverableConsumers (deliverableName)) 
            report.append ('')
            report.extend (self._reportDeliverableAliases (deliverableName))
            report.append ('')
            report.extend (self._reportDeliverablePrecedence (deliverableName))
            report.append ('')
            report.extend (self._reportDeliverableItems (deliverableName))
            report.append ('')
            if includeFilePatterns: # See http://fogbugz.altera.com/default.asp?290185
                report.append ("File specs:")
                for s in self.reportDeliverableFilePatterns (deliverableName,
                                                             indicateFilelists=True):
                    report.append ('  ' + s)
                report.append('')
            report.append('')
        return '\n'.join(report)
            
    def _reportDeliverableProducers (self, deliverableName):
        """Return a list of strings showing the producers of the
        specified deliverable.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <producer id="IP-ICD-ANALOG"/>
        ...          <producer id="IP-ICD-ASIC"/>
        ...          <consumer id="SVT"/>
        ...          <consumer id="TE"/>
        ...        </template>
        ...
        ...        <template id="EMPTY"/>
        ...    </templateset>'''
        >>> manifest = Manifest('ip1', 'cella', templatesetString=templatesetXML)
        >>> manifest._reportDeliverableProducers('TEST')
        ["  Produced by 'IP-ICD-ANALOG', 'IP-ICD-ASIC'"]
        >>> manifest._reportDeliverableProducers('EMPTY')
        ['  No producers defined']
        """
        producers = self.getDeliverableProducer(deliverableName)
        if producers:
            report = ["  Produced by '{}'".format("', '".join(producers))]
        else:
            report = ["  No producers defined"]
        return report

    def _reportDeliverableConsumers(self, deliverableName):
        """Return a list of strings showing the consumers of the
        specified deliverable.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <producer id="IP-ICD-ANALOG"/>
        ...          <producer id="IP-ICD-ASIC"/>
        ...          <consumer id="SVT"/>
        ...          <consumer id="TE"/>
        ...        </template>
        ...
        ...        <template id="EMPTY"/>
        ...    </templateset>'''
        >>> manifest = Manifest('ip1', 'cella', templatesetString=templatesetXML)
        >>> manifest._reportDeliverableConsumers('TEST')
        ["  Consumed by 'SVT', 'TE'"]
        >>> manifest._reportDeliverableConsumers('EMPTY')
        ['  No consumers defined']
        """
        consumers = self.getDeliverableConsumer(deliverableName)
        if consumers:
            report = ["  Consumed by '{}'".format("', '".join(consumers))]
        else:
            report = ["  No consumers defined"]
        return report

    def _reportDeliverableAliases(self, deliverableName):
        """Return a list of strings showing the aliases that contain the
        specified deliverable.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST1"/>
        ...        <template id="TEST2"/>
        ...        <template id="TEST3"/>
        ...        <template id="TEST4"/>
        ...      <alias id="ALIAS1">
        ...        <member>TEST1</member>
        ...      </alias>
        ...      <alias id="ALIAS12">
        ...        <member>TEST1</member>
        ...        <member>TEST2</member>
        ...      </alias>
        ...    </templateset>'''
        >>> manifest = Manifest('ip1', 'cella', templatesetString=templatesetXML)
        >>> manifest._reportDeliverableAliases('TEST1')
        ["  Member of aliases 'ALIAS12', 'ALIAS1'"]
        >>> manifest._reportDeliverableAliases('TEST2')
        ["  Member of aliases 'ALIAS12'"]
        >>> manifest._reportDeliverableAliases('TEST3')
        ['  Member of no aliases']
        >>> manifest._reportDeliverableAliases('TEST4')
        ['  Member of no aliases']
        """
        aliasesContainingDeliverable = set()
        for aliasName in self.allAliases:
            if deliverableName in self.getDeliverableAlias(aliasName):
                aliasesContainingDeliverable.add(aliasName)
        if aliasesContainingDeliverable:
            report = ["  Member of aliases '{}'".
                        format("', '".join(aliasesContainingDeliverable))]
        else:
            report = ["  Member of no aliases"]
        return report

    def _reportDeliverablePrecedence(self, deliverableName):
        """Return a list of strings showing the predecessors and successors of
        the specified deliverable.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST1"/>
        ...        <template id="TEST2"/>
        ...        <template id="TEST3"/>
        ...        <template id="TEST4"/>
        ...      <successor id="TEST2">
        ...        <predecessor>TEST1</predecessor>
        ...      </successor>
        ...      <successor id="TEST4">
        ...        <predecessor>TEST2</predecessor>
        ...        <predecessor>TEST3</predecessor>
        ...      </successor>
        ...    </templateset>'''
        >>> manifest = Manifest('ip1', 'cella', templatesetString=templatesetXML)
        >>> manifest._reportDeliverablePrecedence('TEST1')
        ['  No predecessors', "  Successors 'TEST2'"]
        >>> manifest._reportDeliverablePrecedence('TEST2')
        ["  Predecessors 'TEST1'", "  Successors 'TEST4'"]
        >>> manifest._reportDeliverablePrecedence('TEST3')
        ['  No predecessors', "  Successors 'TEST4'"]
        >>> manifest._reportDeliverablePrecedence('TEST4')
        ["  Predecessors 'TEST3', 'TEST2'", '  No successors']
        """
        prececessorNames = self.getDeliverablePredecessor(deliverableName)
        if prececessorNames:
            report = ["  Predecessors '{}'".format("', '".join(prececessorNames))]
        else:
            report = ["  No predecessors"]

        successorNames = self.getDeliverableSuccessor(deliverableName)
        if successorNames:
            report.append("  Successors '{}'".format("', '".join(successorNames)))
        else:
            report.append("  No successors")

        return report

    def _reportDeliverableItems(self, deliverableName):
        """
        Return a list of strings describing the deliverable items in the
        specified deliverable template.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="PATTERN">
        ...          <pattern id="zero" minimum="0">
        ...            &ip_name;/icc/zero.txt
        ...          </pattern>
        ...          <pattern id="one" minimum="1">
        ...            &ip_name;/icc/one.txt
        ...          </pattern>
        ...        </template>
        ...        <template id="FILELIST">
        ...          <filelist id="list">
        ...            &ip_name;/icc/&ip_name;.filelist
        ...          </filelist>
        ...        </template>
        ...        <template id="MILKYWAY">
        ...          <milkyway id="mwLib1" mimetype="application/octet-stream">
        ...            <libpath>&ip_name;/icc/lib1</libpath>
        ...          </milkyway>
        ...          <milkyway id="mwLib2" mimetype="application/octet-stream">
        ...            <libpath>&ip_name;/icc/lib2</libpath>
        ...          </milkyway>
        ...        </template>
        ...        <template id="OA">
        ...          <openaccess deep="yes" id="cellView1" mimetype="application/octet-stream">
        ...            <libpath>&ip_name;/icc/lib1</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('ip1', 'cella', templatesetString=templatesetXML)
        >>> manifest._reportDeliverableItems('PATTERN')
        ["  ip1/icc/zero.txt    Optional file, logical name 'zero'", "  ip1/icc/one.txt    Minimum 1 file, logical name 'one'"]
        >>> manifest._reportDeliverableItems('FILELIST')
        ["  ip1/icc/ip1.filelist    Filelist, Minimum 1 file, logical name 'list'"]
        >>> manifest._reportDeliverableItems('MILKYWAY')
        [" Milkyway path 'ip1/icc/lib1' library 'lib1'    Logical name 'mwLib1'", " Milkyway path 'ip1/icc/lib2' library 'lib2'    Logical name 'mwLib2'"]
        >>> manifest._reportDeliverableItems('OA')
        [" OpenAccess path 'ip1/icc/lib1' library 'lib' cell 'cell' view 'view' viewType 'oacMaskLayout'    Logical name 'cellView1'"]
        """
        report = []
        template = self._getDeliverable(deliverableName)
        for item in template:
            tag = item.tag
            if tag == 'description':
                # Already done in reportDeliverables()
                pass
            elif tag == 'producer':
                # Already done in reportDeliverables()
                pass
            elif tag == 'consumer':
                # Already done in reportDeliverables()
                pass
            elif tag == 'pattern': 
                report.append(self._reportPatternItem(item))
            elif tag == 'filelist':
                report.append(self._reportFilelistItem(item))
            elif tag == 'milkyway':
                report.append(self._reportDatabaseItem(item, 'Milkyway'))
            elif tag == 'openaccess':
                report.append(self._reportDatabaseItem(item, 'OpenAccess'))
            elif tag == 'totem':
                report.append(self._reportDatabaseItem(item, 'Totem'))
            elif tag == 'renamer':
                pass
            else:
                assert False, "Unknown <template> item <{}>".format(tag)
        return report

    @classmethod
    def _reportDeliverableDescription(cls, item):
        '''Return the string that describes the deliverable.'''
        description = item.text.strip()
        return textwrap.fill(description, width=80)

    @classmethod
    def _reportPatternItem(cls, item):
        '''Return a string describing the specified deliverable pattern item.'''
        pattern = item.text.strip()
        minimum = int(item.get('minimum', FileBase.minimumDefault))
        id_ = item.get('id')
        if minimum:
            report = "  {}    Minimum {} file, logical name '{}'".format(pattern,
                                                                       minimum,
                                                                       id_)
        else:
            report = "  {}    Optional file, logical name '{}'".format(pattern,
                                                                     id_)
        return report

#    @classmethod
#    def _reportFilelistItem_Old(cls, item):
#        '''Return a string describing the specified deliverable filelist item.'''
#        filelist = item.text.strip()
#        id_ = item.get('id')
#        return "  {}    Filelist, logical name '{}'".format(filelist, id_)

    @classmethod
    def _reportFilelistItem(cls, item):
        '''Return a string describing the specified deliverable filelist item.'''
        filelist = item.text.strip()
        minimum = int(item.get('minimum', FileBase.minimumDefault))
        id_ = item.get('id')
        
        if minimum:
            report = "  {}    Filelist, Minimum {} file, logical name '{}'". \
                        format (filelist, minimum, id_)
        else:
            report = "  {}    Filelist, Optional file, logical name '{}'".format(filelist,
                                                                                 id_)
        return report 

    def _reportDatabaseItem(self, item, databaseName):
        '''Return a string describing the specified deliverable database item.'''
        nameList = self._getDatabaseList(item)
        # Reverse the list so pop() starts with the first member
        nameList.reverse()
        libPathName = nameList.pop()
        report = " {} path '{}'".format(databaseName, libPathName)

        if nameList:
            libName = nameList.pop()
            if libName is None:
                report += " library '{}'".format(os.path.basename(libPathName))
            else:
                report += " library '{}'".format(libName)

        if nameList:
            cellName = nameList.pop()
            report += " cell '{}'".format(cellName)

        if nameList:
            viewName = nameList.pop()
            report += " view '{}'".format(viewName)

        if nameList:
            viewTypeName = nameList.pop()
            report += " viewType '{}'".format(viewTypeName)

        id_ = item.get('id')
        report += "    Logical name '{}'".format(id_)
        return report
    
    def reportDeliverableFilePatterns (self, 
                                       deliverableName, 
                                       indicateFilelists):
        '''
        Persuant to http://fogbugz.altera.com/default.asp?290185:
        Return a list of ICManage/Perforce file specs.
        If 'indicateFilelists', the filelists are sufficed by ' (f)' 
        '''
        ret = []
        template = self._getDeliverable (deliverableName)
        for item in template:
            tag = item.tag
            
            # Skip 'non-file-spec' items:
            if tag in ('description', 
                       'producer',
                       'consumer',
                       'renamer'):
                continue

            spec = self._reportPatternFileSpec (item, indicateFilelists)
                
            if spec:
                ret.append (spec)

        return sorted (ret)

    def _reportPatternFileSpec (self, item, indicateFilelists):
        # See http://fogbugz.altera.com/default.asp?290185:
#        minimum = int (item.get ('minimum', FileBase.minimumDefault))
#        if minimum == 0: # i.e. "optional"
#            return None

        pattern = item.text.strip()
        if indicateFilelists and item.tag == 'filelist':
            pattern += ' (f)'

        return pattern
    
        
    def writeManifestset(self, fileName):
        '''Write a manifestset XML to the specified file.
        
        A manifestset is a templateset XMLwith the entity references resolved.
        '''
        manifestset = '<?xml version="1.0" encoding="utf-8"?>' + \
                            tostring(self.rootElement, 'utf-8')
        reparsed = minidom.parseString(manifestset)
        prettyManifestset = reparsed.toprettyxml(indent='  ', encoding='utf-8')

        with open(fileName, 'w') as f:
            f.write(prettyManifestset)
    
    def isAlias(self, aliasName):
        """Is this alias defined?

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <alias id="ALIAS2">
        ...          <member> DEL3 </member>
        ...          <member> DEL4 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.isAlias("ALIAS1")
        True
        >>> manifest.isAlias("ALIAS2")
        True
        >>> manifest.isAlias("DEL1")
        False
        >>> manifest.isAlias("DEL2")
        False
        >>> manifest.isAlias("UNDEFINED")
        False
        """

        self._buildAllAliases()
        return aliasName in self._allAliases
        
    def _buildAllAliases(self):
        '''Build the set of all aliases if necessary.  This method is tested in
        the allAliases property.
        '''
        if self._allAliases is not None:
            # already built
            return
        self._allAliases = set()
        for alias in self._rootElement.iterfind('alias'):
            aliasName = alias.get('id')
            if not aliasName:
                raise dmError("Found 'alias' without an id attribute. " 
                              "This is not allowed.")
            self._allAliases.add(aliasName)
        
    @property    
    def allDeliverables(self):
        """The set of all deliverable names that are defined.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.allDeliverables
        set(['DEL1', 'DEL3', 'DEL2', 'DEL4'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.allDeliverables
        >>> ignoredValue = s.pop()
        >>> manifest.allDeliverables
        set(['DEL1', 'DEL3', 'DEL2', 'DEL4'])
        """
        self._buildAllDeliverables()
        return self._allDeliverables.copy()

    def isDeliverable(self, deliverableName):
        """Is this deliverable defined?

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <alias id="ALIAS2">
        ...          <member> DEL3 </member>
        ...          <member> DEL4 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.isDeliverable("DEL1")
        True
        >>> manifest.isDeliverable("DEL2")
        True
        >>> manifest.isDeliverable("DEL3")
        True
        >>> manifest.isDeliverable("DEL4")
        True
        >>> manifest.isDeliverable("ALIAS1")
        False
        >>> manifest.isDeliverable("ALIAS2")
        False
        >>> manifest.isDeliverable("UNDEFINED")
        False
        """
        self._buildAllDeliverables()
        return deliverableName in self._allDeliverables
        
    def isDeliverableControlled(self, deliverableName):
        """Is this deliverable a controlled deliverable?
        Uncontrolled deliverables are ignored by VP.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template controlled="yes" id="CONTROLLED"/>
        ...        <template controlled="no" id="UNCONTROLLED"/>
        ...        <template id="CONTROLLED_BY_DEFAULT"/>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.isDeliverableControlled('CONTROLLED')
        True
        >>> manifest.isDeliverableControlled('UNCONTROLLED')
        False
        >>> manifest.isDeliverableControlled('CONTROLLED_BY_DEFAULT')
        True
        """
        deliverable = self._getDeliverable(deliverableName)
        controlled = deliverable.get('controlled')
        if controlled is None:
            return Template.controlledDefault
        return controlled == 'yes'

    def isDeliverableEmpty(self, deliverableName):
        """Does this deliverable contain no deliverable types at all?

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="EMPTY"/>
        ...        <template id="PATTERN">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...        </template>
        ...        <template id="FILELIST">
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist1
        ...            </filelist>
        ...        </template>
        ...        <template id="MW">
        ...          <milkyway id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </milkyway>
        ...        </template>
        ...        <template id="OA">
        ...          <openaccess deep="yes" id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.isDeliverableEmpty('EMPTY')
        True
        >>> manifest.isDeliverableEmpty('PATTERN')
        False
        >>> manifest.isDeliverableEmpty('FILELIST')
        False
        >>> manifest.isDeliverableEmpty('MW')
        False
        >>> manifest.isDeliverableEmpty('OA')
        False
        """
        if self.getPatterns(deliverableName):
            return False
        if self.getFilelists(deliverableName):
            return False
        if self.getDeliverableMilkyway(deliverableName):
            return False
        if self.getDeliverableOpenAccess(deliverableName):
            return False
        return True
    
    def _buildAllDeliverables(self):
        '''Build the set of all deliverables if necessary.  This method is tested in
        the allDeliverables property.
        '''
        if self._allDeliverables is not None:
            # already built
            return
        self._allDeliverables = set()
        for deliverable in self._rootElement.iterfind('template'):
            deliverableName = deliverable.get('id')
            if not deliverableName:
                raise dmError("Found 'template' without an id attribute. "
                              "This is not allowed.")
            self._allDeliverables.add(deliverableName)
        
    def getDeliverableAlias(self, aliasName):
        """Recursively expand the member(s) in the specified deliverable
        `<alias>`.  The item will be returned as a set of string(s).
        
        Recursive, acyclical aliases are allowed.  As a courtesy
        to the client programmer, an alias declared as a member
        of itself is detected, throwing a :py:class:`dmx.dmlib.dmError`.
        Larger cycles are not detected.
        
        If the specified alias name is a deliverable name, that
        name is returned as-is.
        
        If the specified name is *neither a deliverable nor alias*,
        a :py:class:`dmx.dmlib.dmError` will be thrown.

        TO_DO: This code is remarkably inefficient.  When it was first created,
        self._allAliases and self._allDeliverables did not exist.  Making use of
        these will help a lot.


        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <alias id="ALIAS0"/>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...        <alias id="ALIAS2">
        ...          <member> DEL3 </member>
        ...          <member> ALIAS0 </member>
        ...          <member> ALIAS1 </member>
        ...          <member> DEL4 </member>
        ...        </alias>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableAlias('ALIAS0')
        set([])
        >>> manifest.getDeliverableAlias('ALIAS1')
        set(['DEL1', 'DEL2'])
        >>> manifest.getDeliverableAlias('ALIAS2')
        set(['DEL1', 'DEL3', 'DEL2', 'DEL4'])
        >>> manifest.getDeliverableAlias('DEL2')
        set(['DEL2'])
        >>> manifest.getDeliverableAlias('NONEXISTENT') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ...'NONEXISTENT'...
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableAlias('ALIAS2')
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableAlias('ALIAS2')
        True
        """
        assert isinstance(aliasName, basestring), 'aliasName valid'
        isAliasFound = False
        members = set()
        for alias in self._rootElement.iterfind('alias'):
            if alias.get('id') == aliasName:
                isAliasFound = True
                for member in alias.iterfind('member'):
                    # Recurse
                    members |= self.getDeliverableAlias(member.text.strip())
                break

        if not isAliasFound:
            # Treat aliasName as a deliverable and raise an exception if not found
            members.add(self._getDeliverable(aliasName, isAlias=True).get('id'))
        return members

    def getDeliverableAliases(self, deliverableAndAliasSet):
        """Expand a set of deliverable and alias names to a set of unique
        deliverable names.  Aliases are recursively expanded.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <alias id="ALIAS0"/>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...        <alias id="ALIAS2">
        ...          <member> DEL3 </member>
        ...          <member> ALIAS0 </member>
        ...          <member> ALIAS1 </member>
        ...          <member> DEL4 </member>
        ...        </alias>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableAliases(set(['ALIAS0']))
        set([])
        >>> manifest.getDeliverableAliases(set(['ALIAS1']))
        set(['DEL1', 'DEL2'])
        >>> manifest.getDeliverableAliases(set(['ALIAS2']))
        set(['DEL1', 'DEL3', 'DEL2', 'DEL4'])
        >>> manifest.getDeliverableAliases(set(['DEL2']))
        set(['DEL2'])
        >>>
        >>> manifest.getDeliverableAliases(set(['ALIAS0', 'ALIAS1']))
        set(['DEL1', 'DEL2'])
        >>> manifest.getDeliverableAliases(set(['ALIAS1', 'ALIAS2']))
        set(['DEL1', 'DEL3', 'DEL2', 'DEL4'])
        >>> manifest.getDeliverableAliases(set(['ALIAS1', 'DEL3']))
        set(['DEL1', 'DEL3', 'DEL2'])
        >>>
        >>> manifest.getDeliverableAliases('STRING') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        AssertionError: ... must be iterable, but not a string.
        >>> manifest.getDeliverableAliases(['NONEXISTENT']) #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ...'NONEXISTENT'...
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableAliases(set(['ALIAS1', 'DEL3']))
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableAliases(set(['ALIAS1', 'DEL3']))
        True
        """
        assert (isinstance(deliverableAndAliasSet, collections.Iterable) and \
               not isinstance(deliverableAndAliasSet, basestring)), \
            "getDeliverableAliases(deliverableAndAliasSet) argument must be iterable, but not a string."
        deliverables = set()
        for alias in deliverableAndAliasSet:
            deliverables |= self.getDeliverableAlias(alias)
        # TO_DO: Perhaps methods like this should be returning sets of
        # deliverable names rather than sets.
        return deliverables

    def getDeliverableAliasesCommaSeparated(self, deliverableAndAliasString):
        """Expand a string containing a comma-separated list of deliverable and
        alias names to a set of unique deliverable names.  See
        `getDeliverableAliases()` for details.
        
        This method also converts its inputs to upper case for the convenience
        of careless typists.
        
        This method is used to read command line arguments.  Use
        `getDeliverableAliases()` within an application.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <alias id="ALIAS0"/>
        ...
        ...        <alias id="ALIAS1">
        ...          <member> DEL1 </member>
        ...          <member> DEL2 </member>
        ...        </alias>
        ...
        ...        <template id="DEL1"/>
        ...        <template id="DEL2"/>
        ...        <template id="DEL3"/>
        ...        <template id="DEL4"/>
        ...
        ...        <alias id="ALIAS2">
        ...          <member> DEL3 </member>
        ...          <member> ALIAS0 </member>
        ...          <member> ALIAS1 </member>
        ...          <member> DEL4 </member>
        ...        </alias>
        ...
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableAliasesCommaSeparated('ALIAS0')
        set([])
        >>> manifest.getDeliverableAliasesCommaSeparated('ALIAS1')
        set(['DEL1', 'DEL2'])
        >>> manifest.getDeliverableAliasesCommaSeparated('ALIAS1,DEL3')
        set(['DEL1', 'DEL3', 'DEL2'])
        >>>
        >>> manifest.getDeliverableAliasesCommaSeparated('alias1,del3')
        set(['DEL1', 'DEL3', 'DEL2'])
        >>>
        >>> manifest.getDeliverableAliasesCommaSeparated(True) #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: Deliverable 'True' is not a string
        >>>
        >>> manifest.getDeliverableAliasesCommaSeparated('DEL1,ALIAS1,NONEXISTENT') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: 'NONEXISTENT' is neither a deliverable nor alias name.
        >>>
        >>> manifest.getDeliverableAliasesCommaSeparated('DEL1,ALIAS1,NONEXISTENT1,NONEXISTENT2') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: 'NONEXISTENT2, NONEXISTENT1' are neither deliverable nor alias names.
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableAliasesCommaSeparated('ALIAS1,DEL3')
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableAliasesCommaSeparated('ALIAS1,DEL3')
        True
        """
        if not isinstance(deliverableAndAliasString, basestring):
            raise dmError("Deliverable '{}' is not a string".
                            format(deliverableAndAliasString))
        deliverableAndAliasList = deliverableAndAliasString.upper().split(',')
        erroneousNames = set()
        for name in deliverableAndAliasList:
            if not (self.isDeliverable(name) or self.isAlias(name)):
                erroneousNames.add(name)
        errorCount = len(erroneousNames)
        if errorCount == 1:
            raise dmError(
                "'{}' is neither a deliverable nor alias name.".
                    format(', '.join(erroneousNames)))
        if errorCount > 1:
            raise dmError(
                "'{}' are neither deliverable nor alias names.".
                    format(', '.join(erroneousNames)))
        return self.getDeliverableAliases (deliverableAndAliasList)

    def getDeliverableCaseId(self, deliverableName):
        """Get the case (bug) number of the specified deliverable.
        
        Every deliverable is supposed to have decimal case ID, but ensuring that
        is left to the templateset verifier `dmx.dmlib.templateset.verifier`.  If the
        case ID is missing or invalid, return `None`. 

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template caseid="100" id="PROPER_CASEID"/>
        ...        <template caseid=" 2 " id="UNSTRIPPED_CASEID"/>
        ...        <template caseid="   " id="WHITESPACE_CASEID"/>
        ...        <template caseid="3da" id="HEXADECIMAL_CASEID"/>
        ...        <template caseid=""    id="EMPTY_CASEID"/>
        ...        <template              id="NO_CASEID"/>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableCaseId('PROPER_CASEID')
        100
        >>> manifest.getDeliverableCaseId('UNSTRIPPED_CASEID')
        2
        >>> manifest.getDeliverableCaseId('WHITESPACE_CASEID')
        
        >>> manifest.getDeliverableCaseId('HEXADECIMAL_CASEID')
        
        >>> manifest.getDeliverableCaseId('EMPTY_CASEID')
        
        >>> manifest.getDeliverableCaseId('NO_CASEID')
        
        """
        template = self._getDeliverable(deliverableName)
        caseId = template.get('caseid')
        if caseId is None:
            return None
        try:
            return int(caseId)
        except ValueError:
            return None
            

    def getDeliverableDescription(self, deliverableName):
        """Get the natural language description of the specified deliverable.
        
        The description string is returned as a single line.  If you like, use
        `textwrap.fill()` in the Python `textwrap` module to format it.

        Every deliverable is supposed to have a description, but ensuring that
        is left to the templateset verifier `dmx.dmlib.templateset.verifier`.  If the
        description is missing or invalid, return ``. 

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="PROPER_DESCRIPTION">
        ...            <description>
        ...               This deliverable is used
        ...               to test the getDeliverableDescription() method.
        ...            </description>
        ...        </template>
        ...        <template id="DUPLICATE_DESCRIPTION">
        ...            <description>
        ...               This description is the first of two.
        ...            </description>
        ...            <description>
        ...               This description is the second of two.
        ...            </description>
        ...        </template>
        ...        <template id="WHITESPACE_DESCRIPTION">
        ...            <description>    </description>
        ...        </template>
        ...        <template id="EMPTY_DESCRIPTION">
        ...            <description />
        ...        </template>
        ...        <template id="NO_DESCRIPTION">
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableDescription('PROPER_DESCRIPTION')
        'This deliverable is used to test the getDeliverableDescription() method.'
        >>> manifest.getDeliverableDescription('DUPLICATE_DESCRIPTION')
        'This description is the first of two.'
        >>> manifest.getDeliverableDescription('WHITESPACE_DESCRIPTION')
        ''
        >>> manifest.getDeliverableDescription('EMPTY_DESCRIPTION')
        ''
        >>> manifest.getDeliverableDescription('NO_DESCRIPTION')
        ''
        """
        template = self._getDeliverable(deliverableName)
        description = template.find('description')
        if description is None:
            return ''
        descriptionText = description.text
        if descriptionText is None:
            return ''
        return ' '.join(descriptionText.split())

    def getPattern(self, deliverableName, itemName=Pattern.defaultId):
        """Get the file path in the named `<pattern>` deliverable item
        within the specified deliverable.
        
        If the 'itemName` argument is unspecified or `None`, the following is
        used as the default:
        
        >>> Pattern.defaultId
        'file'
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <pattern id="lef">
        ...                ip1/icc/ip1.lef
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getPattern('TEST', 'lef')
        'ip1/icc/ip1.lef'
        >>> manifest.getPattern('TEST', 'def')
        'ip1/icc/ip1.def'
        >>> manifest.getPattern('TEST', 'list')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no pattern named 'list'.
        """
        return self._getFileKernel(deliverableName, 'pattern', itemName)
    
    def getPatterns(self, deliverableName):
        """Get the list of all file(s) in the named `<pattern>` deliverable item
        within the specified deliverable.
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <pattern id="lef">
        ...                ip1/icc/ip1.lef
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getPatterns('TEST')
        ['ip1/icc/ip1.def', 'ip1/icc/ip1.lef']
        >>> manifest.getPatterns('NONEXISTENT')
        Traceback (most recent call last):
          ...
        dmError: Could not find deliverable item(s) because deliverable 'NONEXISTENT' does not exist.
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getPatterns('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getPatterns('TEST')
        True
        """
        return self._getFilesKernel(deliverableName, 'pattern')
    
    def getDeliverablePattern(self, deliverableName, itemName=None):
        """This method is deprecated.
        
        Get the file(s) in the named `<pattern>` deliverable item
        within the specified deliverable.  The item will be returned as a set of string(s).
        
        If `itemName` is `None` or is not specified, all `<pattern>` within the
        deliverable are returned.
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <pattern id="lef">
        ...                ip1/icc/ip1.lef
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablePattern('TEST', 'lef')
        set(['ip1/icc/ip1.lef'])
        >>> manifest.getDeliverablePattern('TEST', 'def')
        set(['ip1/icc/ip1.def'])
        >>> manifest.getDeliverablePattern('TEST', 'list')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no pattern named 'list'.
        >>> manifest.getDeliverablePattern('TEST')
        set(['ip1/icc/ip1.lef', 'ip1/icc/ip1.def'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverablePattern('TEST')
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverablePattern('TEST')
        True
        """
        return set(self._getFilesKernel(deliverableName, 'pattern', itemName))
    
    def getDeliverablePatternFirst (self, 
                                    deliverableName,  # In manifest, e.g.: 'RTL' or 'SCH' 
                                    itemName,         # Usually 'id' in manifest 
                                    overwriteCellName = None):
        """
        Return the pattern string, whereas 'getDeliverablePattern()` returns a
        set of strings.
        
        Synonym (to some extent) of 'getPattern()', adding ability to overwriteCellName.
        
        Note that 'getDeliverablePattern()` can only return a set of multiple
        strings when the `itemName` argument is not specified, but we get only
        one string because we _are_ specifying `itemName` here.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="lef">
        ...                ip1/icc/ip1.lef
        ...            </pattern>
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablePatternFirst('TEST', 'lef')
        'ip1/icc/ip1.lef'
        >>> manifest.getDeliverablePatternFirst('TEST', 'def')
        'ip1/icc/ip1.def'
        """
        
        # Save/temporary set self._cellName
        if overwriteCellName:
            manifest = Manifest (ip_name           = self._ipNameArg,
                                 cell_name         = overwriteCellName,
                                 deliverable_name  = self._deliverableNameArg,
                                 templatesetString = self._templatesetStringArg,
                                 entityValues      = self._entityValuesArg)
        else:
            manifest = self
        
        ret = manifest.getPattern (deliverableName, itemName)
        
        return ret
        

    def getFilelist(self, deliverableName, itemName=Filelist.defaultId):
        """Get the filelist in the named `<filelist>` deliverable item
        within the specified deliverable.
        
        Use the :py:class:`dmx.dmlib.ExpandFilelist` `expandFilelist()` class method
        to retrieve a list of the files appearing within a filelist file.
        
        If the 'itemName` argument is unspecified or `None`, the following is
        used as the default:
        
        >>> Filelist.defaultId
        'filelist'
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist1
        ...            </filelist>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist2
        ...            </filelist>
        ...            <filelist id="listx">
        ...                ip1/icc/ip1.filelistx
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getFilelist('TEST', 'def')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no filelist named 'def'.
        >>> manifest.getFilelist('TEST', 'list')
        'ip1/icc/ip1.filelist1'
        >>> manifest.getFilelist('TEST', 'listx')
        'ip1/icc/ip1.filelistx'
        """
        return self._getFileKernel(deliverableName, 'filelist', itemName)

    def getFilelists(self, deliverableName):
        """Get the set of all filelists(s)  within the specified deliverable.
        The item will be returned as a list of string(s).
        
        Use the :py:class:`dmx.dmlib.ExpandFilelist` `expandFilelist()` class method to
        retrieve a list of the files appearing in a filelist file.  If no
        filelists are found in the deliverable, a :py:class:`dmx.dmlib.dmError` will be
        thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist1
        ...            </filelist>
        ...            <filelist id="listx">
        ...                ip1/icc/ip1.filelistx
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getFilelists('NONEXISTENT')
        Traceback (most recent call last):
          ...
        dmError: Could not find deliverable item(s) because deliverable 'NONEXISTENT' does not exist.
        >>> manifest.getFilelists('TEST')
        ['ip1/icc/ip1.filelist1', 'ip1/icc/ip1.filelistx']
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getFilelists('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getFilelists('TEST')
        True
        """
        return self._getFilesKernel(deliverableName, 'filelist')

    def getDeliverableFilelist(self, deliverableName, itemName=None):
        """Get the filelists(s) in the named `<filelist>` deliverable item
        within the specified deliverable.  The item will be returned as a set of string(s).
        
        Use the :py:class:`dmx.dmlib.ExpandFilelist`  `expandFilelist()` class method to retrieve a list of the files
        appearing in a filelist file.
        
        If `itemName` is `None` or is not specified, all `<filelist>` file names
        in the deliverable are returned.
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist1
        ...            </filelist>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist2
        ...            </filelist>
        ...            <filelist id="listx">
        ...                ip1/icc/ip1.filelistx
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableFilelist('TEST', 'def')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no filelist named 'def'.
        >>> manifest.getDeliverableFilelist('TEST', 'list')
        set(['ip1/icc/ip1.filelist2', 'ip1/icc/ip1.filelist1'])
        >>> manifest.getDeliverableFilelist('TEST', 'listx')
        set(['ip1/icc/ip1.filelistx'])
        >>> manifest.getDeliverableFilelist('TEST')
        set(['ip1/icc/ip1.filelist2', 'ip1/icc/ip1.filelistx', 'ip1/icc/ip1.filelist1'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableFilelist('TEST')
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableFilelist('TEST')
        True
        """
        return set(self._getFilesKernel(deliverableName, 'filelist', itemName))

    def _getFileKernel(self, deliverableName, itemTagName, itemName):
        """This is the common kernel of `getPattern()` and
        `getFilelist()`.  See their documentation for details.
        """
        assert itemTagName, 'itemTagName valid'
        template = self._getDeliverable(deliverableName)
        for item in template.iterfind(itemTagName):
            if (itemName is None) or (item.get('id') == itemName):
                return item.text.strip()
        raise dmError("In deliverable '{}', there is no {} named '{}'.".format(deliverableName,
                                                                               itemTagName,
                                                                               itemName))

    def _getFilesKernel(self, deliverableName, itemTagName, itemName=None):
        """This is the common kernel of `getDeliverablePattern()` and
        `getDeliverableFilelist()`.  See their documentation for details.
        """
        assert itemTagName, 'itemTagName valid'
        template = self._getDeliverable(deliverableName)
        items = []
        for item in template.iterfind(itemTagName):
            if (itemName is None) or (item.get('id') == itemName):
                items.append(item.text.strip())
        if not items and itemName is not None:
            raise dmError("In deliverable '{}', there is no {} named '{}'.".
                                format(deliverableName,
                                       itemTagName,
                                       itemName))
        return items

    def getDeliverablePatternAndMinimum(self, deliverableName, itemName=None):
        """Get the file(s) in the named `<pattern>` deliverable item
        within the specified deliverable along with their `minimum` attribute.
        The item will be returned as a set of lists of the form:
        
            set([patternString minimumNumberOfFiles] ... )
        
        This method is used mainly by :py:class:`dmx.dmlib.CheckType`.
        
        If the specified item does not exist within the deliverable, the returned
        set will be empty.
        
        if `itemName` is `None` or is not specified, all `<pattern>`
        in the deliverable are returned.
        
        If the specified *deliverable* does not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="zero" minimum="0">
        ...                ip1/icc/zero.txt
        ...            </pattern>
        ...            <pattern id="one" minimum="1">
        ...                ip1/icc/one.txt
        ...            </pattern>
        ...            <pattern id="two" minimum="2">
        ...                ip1/icc/two.txt
        ...            </pattern>
        ...            <pattern id="default"> <!-- default minimum -->
        ...                ip1/icc/default.txt
        ...            </pattern>
        ...            <filelist id="list">
        ...                ip1/icc/ip1.filelist
        ...            </filelist>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablePatternAndMinimum('TEST', 'zero')
        [['ip1/icc/zero.txt', 0]]
        >>> manifest.getDeliverablePatternAndMinimum('TEST', 'one')
        [['ip1/icc/one.txt', 1]]
        >>> manifest.getDeliverablePatternAndMinimum('TEST', 'two')
        [['ip1/icc/two.txt', 2]]
        >>> manifest.getDeliverablePatternAndMinimum('TEST', 'default')
        [['ip1/icc/default.txt', 1]]
        >>> manifest.getDeliverablePatternAndMinimum('TEST', 'list')
        []
        >>> manifest.getDeliverablePatternAndMinimum('TEST')
        [['ip1/icc/zero.txt', 0], ['ip1/icc/one.txt', 1], ['ip1/icc/two.txt', 2], ['ip1/icc/default.txt', 1]]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverablePatternAndMinimum('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverablePatternAndMinimum('TEST')
        True
        """
        template = self._getDeliverable(deliverableName)
        items = []
        for item in template.iterfind('pattern'):
            if (itemName is None) or (item.get('id') == itemName):
                pattern = item.text.strip()
                minimum = int(item.get('minimum', FileBase.minimumDefault))
                items.append([pattern, minimum])
        return items

    def getDeliverableFilelistAndMinimum(self, deliverableName, itemName=None):
        """Get the file(s) in the named `<filelist>` deliverable item
        within the specified deliverable along with their `minimum` attribute.
        The item will be returned as a set of lists of the form:
        
            set([filelistString minimumNumberOfFiles] ... )
        
        This method is used mainly by :py:class:`dmx.dmlib.CheckType`.
        
        If the specified item does not exist within the deliverable, the returned
        set will be empty.
        
        if `itemName` is `None` or is not specified, all `<filelist>`
        in the deliverable are returned.
        
        If the specified *deliverable* does not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <filelist id="zero" minimum="0">
        ...                ip1/icc/zero.filelist
        ...            </filelist>
        ...            <filelist id="one" minimum="1">
        ...                ip1/icc/one.filelist
        ...            </filelist>
        ...            <filelist id="two" minimum="2">
        ...                ip1/icc/two.filelist
        ...            </filelist>
        ...            <filelist id="default"> <!-- default minimum -->
        ...                ip1/icc/default.filelist
        ...            </filelist>
        ...            <pattern id="file">
        ...                ip1/icc/ip1.txt
        ...            </pattern>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableFilelistAndMinimum('TEST', 'zero')
        [['ip1/icc/zero.filelist', 0]]
        >>> manifest.getDeliverableFilelistAndMinimum('TEST', 'one')
        [['ip1/icc/one.filelist', 1]]
        >>> manifest.getDeliverableFilelistAndMinimum('TEST', 'two')
        [['ip1/icc/two.filelist', 2]]
        >>> manifest.getDeliverableFilelistAndMinimum('TEST', 'default')
        [['ip1/icc/default.filelist', 1]]
        >>> manifest.getDeliverableFilelistAndMinimum('TEST', 'file')
        []
        >>> manifest.getDeliverableFilelistAndMinimum('TEST')
        [['ip1/icc/zero.filelist', 0], ['ip1/icc/one.filelist', 1], ['ip1/icc/two.filelist', 2], ['ip1/icc/default.filelist', 1]]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableFilelistAndMinimum('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableFilelistAndMinimum('TEST')
        True
        """
        template = self._getDeliverable(deliverableName)
        items = []
        for item in template.iterfind('filelist'):
            if (itemName is None) or (item.get('id') == itemName):
                filelist = item.text.strip()
                minimum = int(item.get('minimum', FileBase.minimumDefault))
                items.append([filelist, minimum])
        return items

    def getMilkyway(self, deliverableName, itemName=Milkyway.defaultId):
        """Get the database in the named `<milkyway>` deliverable item
        within the specified deliverable.  The item(s) will be returned as
        a list of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        If the 'itemName` argument is unspecified or `None`, the following is
        used as the default:
        
        >>> Milkyway.defaultId
        'mwLib'
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if both the library path and the library was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyway('TEST', 'bothLibPathAndLibName')
        ['ip1/icc/lib', 'lib']
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyway('TEST', 'libPathOnly')
        ['ip1/icc/lib', 'lib']
        
        When `itemName` is not specified, all Milkyway libraries are returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib1</libpath>
        ...          </milkyway>
        ...          <milkyway id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib2</libpath>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyway('TEST', 'mw1')
        ['ip1/icc/lib1', 'lib1']
         
        When `itemName` is specified, only the named Milkyway library is returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib1</libpath>
        ...          </milkyway>
        ...          <milkyway id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib2</libpath>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyway('TEST', 'mw1')
        ['ip1/icc/lib1', 'lib1']
         """
        return self._getDatabaseKernel(deliverableName, 'milkyway', itemName)

    def getMilkyways(self, deliverableName):
        """Get all  `<milkyway>` databases within the specified deliverable.
        The items will be returned as a list of lists of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if both the library path and the library was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyways('TEST')
        [['ip1/icc/lib', 'lib']]
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyways('TEST')
        [['ip1/icc/lib', 'lib']]
        
        When there are multiple Milkyway libraries, they are all returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib1</libpath>
        ...          </milkyway>
        ...          <milkyway id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib2</libpath>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getMilkyways('TEST')
        [['ip1/icc/lib1', 'lib1'], ['ip1/icc/lib2', 'lib2']]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getMilkyways('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getMilkyways('TEST')
        True
        """
        return self._getDatabasesKernel(deliverableName, 'milkyway')

    def getDeliverableMilkyway(self, deliverableName, itemName=None):
        """This method is deprecated.
        
        Get the database(s) in the named `<milkyway>` deliverable item
        within the specified deliverable.  The item(s) will be returned as
        a list of list(s) of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        if `itemName` is `None` or is not specified, all `<milkyway>` databases
        in the deliverable are returned.
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if both the library path and the library was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableMilkyway('TEST', 'bothLibPathAndLibName')
        [['ip1/icc/lib', 'lib']]
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableMilkyway('TEST', 'libPathOnly')
        [['ip1/icc/lib', 'lib']]
        
        When `itemName` is not specified, all Milkyway libraries are returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib1</libpath>
        ...          </milkyway>
        ...          <milkyway id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib2</libpath>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableMilkyway('TEST')
        [['ip1/icc/lib1', 'lib1'], ['ip1/icc/lib2', 'lib2']]
         
        When `itemName` is specified, only the named Milkyway library is returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <milkyway id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib1</libpath>
        ...          </milkyway>
        ...          <milkyway id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/icc/lib2</libpath>
        ...          </milkyway>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableMilkyway('TEST', 'mw1')
        [['ip1/icc/lib1', 'lib1']]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableMilkyway('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableMilkyway('TEST')
        True
        """
        return self._getDatabasesKernel(deliverableName, 'milkyway', itemName)

    def getTotem(self, deliverableName, itemName=Totem.defaultId):
        """Get the database in the named `<totem>` deliverable item
        within the specified deliverable.  The item(s) will be returned as
        a list of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        If the 'itemName` argument is unspecified or `None`, the following is
        used as the default:
        
        >>> Totem.defaultId
        'totem'
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if both the library path and the library was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotem('TEST', 'bothLibPathAndLibName')
        ['ip1/irem/lib', 'lib']
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotem('TEST', 'libPathOnly')
        ['ip1/irem/lib', 'lib']
        
        When `itemName` is not specified, all Totem libraries are returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib1</libpath>
        ...          </totem>
        ...          <totem id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib2</libpath>
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotem('TEST', 'mw1')
        ['ip1/irem/lib1', 'lib1']
         
        When `itemName` is specified, only the named Totem library is returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib1</libpath>
        ...          </totem>
        ...          <totem id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib2</libpath>
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotem('TEST', 'mw1')
        ['ip1/irem/lib1', 'lib1']
         """
        return self._getDatabaseKernel(deliverableName, 'totem', itemName)

    def getTotems(self, deliverableName):
        """Get all  `<totem>` databases within the specified deliverable.
        The items will be returned as a list of lists of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if both the library path and the library was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotems('TEST')
        [['ip1/irem/lib', 'lib']]
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotems('TEST')
        [['ip1/irem/lib', 'lib']]
        
        When there are multiple Totem libraries, they are all returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <totem id="mw1" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib1</libpath>
        ...          </totem>
        ...          <totem id="mw2" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib2</libpath>
        ...          </totem>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getTotems('TEST')
        [['ip1/irem/lib1', 'lib1'], ['ip1/irem/lib2', 'lib2']]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getTotems('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getTotems('TEST')
        True
        """
        return self._getDatabasesKernel(deliverableName, 'totem')

    def getOpenAccess(self, deliverableName, itemName=OpenAccess.defaultId):
        """Get the database in the named `<openaccess>` deliverable item
        within the specified deliverable.  The item will be returned as
        a list of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        If the 'itemName` argument is unspecified or `None`, the following is
        used as the default:
        
        >>> OpenAccess.defaultId
        'oa'
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if the library alone was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getOpenAccess('TEST', 'bothLibPathAndLibName')
        ['ip1/irem/lib', 'lib']
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getOpenAccess('TEST', 'libPathOnly')
        ['ip1/irem/lib', 'lib']
        
        If the library and cell are specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cell" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...     <!-- no view -->
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getOpenAccess('TEST', 'cell')
        ['ip1/irem/lib', 'lib', 'cell']
        
        If the library, cell and view are specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cellView" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getOpenAccess('TEST', 'cellView')
        ['ip1/irem/lib', 'lib', 'cell', 'view', 'oacMaskLayout']
        >>> manifest.getOpenAccess('TEST', 'nonexistent')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no openaccess named 'nonexistent'.
        
        If the `itemName` argument is not specified, the first OpenAccess item
        will be returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cellView1" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib1</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...          <openaccess deep="yes" id="cellView2" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib2</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getOpenAccess('TEST', 'cellView1')
        ['ip1/irem/lib1', 'lib', 'cell', 'view', 'oacMaskLayout']
        >>> manifest.getOpenAccess('TEST', 'cellView2')
        ['ip1/irem/lib2', 'lib', 'cell', 'view', 'oacMaskLayout']
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getOpenAccess('TEST', 'cellView2')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getOpenAccess('TEST', 'cellView2')
        True
        """
        return self._getDatabaseKernel(deliverableName, 'openaccess', itemName)

    def getOpenAccesses(self, deliverableName):
        """Get the database(s) in the named `<openaccess>` deliverable item
        within the specified deliverable.  The item(s) will be returned as
        a list of list(s) of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        if `itemName` is `None` or is not specified, all `<openaccess>` databases
        in the deliverable are returned.
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if the library alone was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'bothLibPathAndLibName')
        [['ip1/irem/lib', 'lib']]
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'libPathOnly')
        [['ip1/irem/lib', 'lib']]
        
        If the library and cell are specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cell" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...     <!-- no view -->
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'cell')
        [['ip1/irem/lib', 'lib', 'cell']]
        
        If the library, cell and view are specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cellView" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'cellView')
        [['ip1/irem/lib', 'lib', 'cell', 'view', 'oacMaskLayout']]
        
        A single OpenAccess database can be selected using the `itemName` argument.
        If the specified item does not exist within the deliverable, the returned
        list will be empty.  If no item name is specified, all OpenAccess items are
        returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cellView1" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib1</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...          <openaccess deep="yes" id="cellView2" mimetype="application/octet-stream">
        ...            <libpath>ip1/irem/lib2</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'cellView2')
        [['ip1/irem/lib2', 'lib', 'cell', 'view', 'oacMaskLayout']]
        >>> manifest.getDeliverableOpenAccess('TEST', 'nonexistent')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no openaccess named 'nonexistent'.
        >>> manifest.getDeliverableOpenAccess('TEST')
        [['ip1/irem/lib1', 'lib', 'cell', 'view', 'oacMaskLayout'], ['ip1/irem/lib2', 'lib', 'cell', 'view', 'oacMaskLayout']]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableOpenAccess('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableOpenAccess('TEST')
        True
        """
        return self._getDatabasesKernel(deliverableName, 'openaccess')

    def getDeliverableOpenAccess(self, deliverableName, itemName=None):
        """Get the database(s) in the named `<openaccess>` deliverable item
        within the specified deliverable.  The item(s) will be returned as
        a list of list(s) of,

        * Library path
        * Library name
        * Cell name
        * View name
        * View type

        to the extent that they were specified in the XML.

        if `itemName` is `None` or is not specified, all `<openaccess>` databases
        in the deliverable are returned.
        
        If the specified `deliverableName` or `itemName` do not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        For example, if the library alone was specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="bothLibPathAndLibName" mimetype="application/octet-stream">
        ...            <libpath>ip1/oa/lib</libpath>    <!-- libpath not ending with '/' is ok -->
        ...            <lib>lib</lib>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'bothLibPathAndLibName')
        [['ip1/oa/lib', 'lib']]
        
        Actually the templateset needn't specify `<lib>`.  If it is omitted, the
        end of `<libpath>` is used:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="libPathOnly" mimetype="application/octet-stream">
        ...            <libpath>ip1/oa/lib/</libpath>     <!-- libpath ending with '/' is ok -->
        ...     <!-- no lib -->
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'libPathOnly')
        [['ip1/oa/lib', 'lib']]
        
        If the library and cell are specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cell" mimetype="application/octet-stream">
        ...            <libpath>ip1/oa/lib</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...     <!-- no view -->
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'cell')
        [['ip1/oa/lib', 'lib', 'cell']]
        
        If the library, cell and view are specified:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cellView" mimetype="application/octet-stream">
        ...            <libpath>ip1/oa/lib</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'cellView')
        [['ip1/oa/lib', 'lib', 'cell', 'view', 'oacMaskLayout']]
        
        A single OpenAccess database can be selected using the `itemName` argument.
        If the specified item does not exist within the deliverable, the returned
        list will be empty.  If no item name is specified, all OpenAccess items are
        returned:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...          <openaccess deep="yes" id="cellView1" mimetype="application/octet-stream">
        ...            <libpath>ip1/oa/lib1</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...          <openaccess deep="yes" id="cellView2" mimetype="application/octet-stream">
        ...            <libpath>ip1/oa/lib2</libpath>
        ...            <lib>lib</lib>
        ...            <cell>cell</cell>
        ...            <view viewtype="oacMaskLayout">view</view>
        ...          </openaccess>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableOpenAccess('TEST', 'cellView2')
        [['ip1/oa/lib2', 'lib', 'cell', 'view', 'oacMaskLayout']]
        >>> manifest.getDeliverableOpenAccess('TEST', 'nonexistent')
        Traceback (most recent call last):
          ...
        dmError: In deliverable 'TEST', there is no openaccess named 'nonexistent'.
        >>> manifest.getDeliverableOpenAccess('TEST')
        [['ip1/oa/lib1', 'lib', 'cell', 'view', 'oacMaskLayout'], ['ip1/oa/lib2', 'lib', 'cell', 'view', 'oacMaskLayout']]
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableOpenAccess('TEST')
        >>> sBeforePop = list(s)
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableOpenAccess('TEST')
        True
        """
        return self._getDatabasesKernel(deliverableName, 'openaccess', itemName)

    def _getDatabaseKernel(self, deliverableName, itemTagName, itemName):
        """This is the common kernel of `getDeliverableOpenAccess()` and
        `getDeliverableMilkyway()`.  See their documentation for details
        and tests.
        """
        assert itemTagName, 'itemTagName valid'
        template = self._getDeliverable(deliverableName)
#        items = []
        for item in template.iterfind(itemTagName):
            if (itemName is None) or item.get('id') == itemName:
                return self._getDatabaseList(item)
        raise dmError("In deliverable '{}', there is no {} named '{}'.".format(deliverableName,
                                                                               itemTagName,
                                                                               itemName))

    def _getDatabasesKernel(self, deliverableName, itemTagName, itemName=None):
        """This is the common kernel of `getOpenAccess()` and `getMilkyway()`.
        See their documentation for details and tests.
        """
        assert itemTagName, 'itemTagName valid'
        template = self._getDeliverable(deliverableName)
        items = []
        for item in template.iterfind(itemTagName):
            if (itemName is None) or item.get('id') == itemName:
                items.append(self._getDatabaseList(item))
        if not items and itemName is not None:
            raise dmError("In deliverable '{}', there is no {} named '{}'.".format(deliverableName,
                                                                                   itemTagName,
                                                                                   itemName))
        return items

    @classmethod
    def getLibraryPath(cls, dbList):
        '''Return the library path from the list returned by
        `getOpenAccess()` or `getMilkyway()`.
                
        >>> dbList = ['path/to/lib0', 'lib0', 'cell0', 'view0', 'oacMaskLayout0']
        >>> Manifest.getLibraryPath(dbList)
        'path/to/lib0'
        '''
        return dbList[0]
    
    @classmethod
    def getLibraryName(cls, dbList):
        '''Return the library name from the list returned by
        `getOpenAccess()` or `getMilkyway()`.
                
        >>> dbList = ['path/to/lib0', 'lib0', 'cell0', 'view0', 'oacMaskLayout0']
        >>> Manifest.getLibraryName(dbList)
        'lib0'
        '''
        return dbList[1]
    
    @classmethod
    def getCellName(cls, dbList):
        '''Return the cell name from the list returned by
        `getOpenAccess()` or `getMilkyway()`.
                
        >>> dbList = ['path/to/lib0', 'lib0', 'cell0', 'view0', 'oacMaskLayout0']
        >>> Manifest.getCellName(dbList)
        'cell0'
        >>> Manifest.getCellName(['path/to/lib0', 'lib0']) # Returns None
        
        '''
        if len(dbList) < 3:
            return None
        return dbList[2]
    
    @classmethod
    def getViewName(cls, dbList):
        '''Return the view name from the list returned by
        `getOpenAccess()` or `getMilkyway()`.
                
        Return `None` if no view name is defined.
        
        >>> dbList = ['path/to/lib0', 'lib0', 'cell0', 'view0', 'oacMaskLayout0']
        >>> Manifest.getViewName(dbList)
        'view0'
        >>> Manifest.getViewName(['path/to/lib0', 'lib0', 'cell0']) # Returns None
        
        '''
        if len(dbList) < 4:
            return None
        return dbList[3]
    
    @classmethod
    def getViewType(cls, dbList):
        '''Return the library path from the list returned by
        `getOpenAccess()` or `getMilkyway()`.
                
        Return `None` if no view type is defined.
        
        >>> dbList = ['path/to/lib0', 'lib0', 'cell0', 'view0', 'oacMaskLayout0']
        >>> Manifest.getViewType(dbList)
        'oacMaskLayout0'
        >>> Manifest.getViewType(['path/to/lib0', 'lib0', 'cell0', 'view0']) # Returns None
        
        '''
        if len(dbList) < 5:
            return None
        return dbList[4]
    
    @classmethod
    def getMilkywayCellViewName(cls, dbList):
        '''From the list returned by `getMilkyway()`:
        
        * Return `cellName.viewName` if the view name is defined
        * Return `cellName` if the view name is not defined
        * Return `None` if the cell name is not defined
        
        This `cellName.viewName` formatting is only valid in Milkyway, not
        OpenAccess.
                
        >>> dbList = ['path/to/lib0', 'lib0', 'cell0', 'FRAM', 'oacMaskLayout0']
        >>> Manifest.getMilkywayCellViewName(dbList)
        'cell0.FRAM'
        >>> Manifest.getMilkywayCellViewName(['path/to/lib0', 'lib0', 'cell0'])
        'cell0'
        >>> Manifest.getMilkywayCellViewName(['path/to/lib0', 'lib0']) # Returns None
        
        '''
        cellName = cls.getCellName(dbList)
        if cellName is None:
            return None
        viewName = cls.getViewName(dbList)
        if viewName is None:
            return cellName
        return '{}.{}'.format(cellName, viewName)
        
    def getDeliverableProducer(self, deliverableName):
        """Get the producer(s) of the specified deliverable.
        The producers will be returned as a set of string(s).
        
        If the specified `deliverableName` does not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST">
        ...          <producer id="IP-ICD-ANALOG"/>
        ...          <producer id="IP-ICD-ASIC"/>
        ...          <producer id="IP-ICD-DIGITAL"/>
        ...          <consumer id="LAYOUT"/>
        ...          <consumer id="SOFTWARE-IPD"/>
        ...          <consumer id="SVT"/>
        ...        </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableProducer('TEST')
        set(['IP-ICD-ANALOG', 'IP-ICD-DIGITAL', 'IP-ICD-ASIC'])
        >>> manifest.getDeliverableProducer('NONEXISTENT')
        Traceback (most recent call last):
          ...
        dmError: Could not find deliverable item(s) because deliverable 'NONEXISTENT' does not exist.
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableProducer('TEST')
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableProducer('TEST')
        True
        """
        return self._getDeliverableElementIdsKernel(deliverableName, 'producer')

    def getDeliverableConsumer(self, deliverableName):
        """Get the consumer(s) of the specified deliverable.
        The consumers will be returned as a set of string(s).
        
        If the specified `deliverableName` does not exist, a
        :py:class:`dmx.dmlib.dmError` will be thrown.

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST">
        ...          <producer id="IP-ICD-ANALOG"/>
        ...          <producer id="IP-ICD-ASIC"/>
        ...          <producer id="IP-ICD-DIGITAL"/>
        ...          <consumer id="LAYOUT"/>
        ...          <consumer id="SOFTWARE-IPD"/>
        ...          <consumer id="SVT"/>
        ...        </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableConsumer('TEST')
        set(['SOFTWARE-IPD', 'SVT', 'LAYOUT'])
        >>> manifest.getDeliverableConsumer('NONEXISTENT')
        Traceback (most recent call last):
          ...
        dmError: Could not find deliverable item(s) because deliverable 'NONEXISTENT' does not exist.
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableConsumer('TEST')
        >>> sBeforePop = s.copy()
        >>> ignoredValue = s.pop()
        >>> sBeforePop == manifest.getDeliverableConsumer('TEST')
        True
        """
        return self._getDeliverableElementIdsKernel(deliverableName, 'consumer')

    def _getDeliverableElementIdsKernel(self, deliverableName, tagName):
        """This is the common kernel of `getDeliverableProducer()` and
        `getDeliverableConsumer()`.  See their documentation for details
        and tests.
        """
        assert tagName, 'tagName valid'
        template = self._getDeliverable(deliverableName)
        ids = set()
        for item in template.iterfind(tagName):
            ids.add(item.get('id').strip())
        return ids

    def getDeliverablesProducedBy(self, producerName):
        """Get the deliverables produced by the specified producer.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST1">
        ...          <producer id="A-TEAM"/>
        ...          <producer id="B-TEAM"/>
        ...          <consumer id="C-TEAM"/>
        ...          <consumer id="D-TEAM"/>
        ...        </template>
        ...        <template id="TEST2">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...        <template id="TEST3">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablesProducedBy('A-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesProducedBy('B-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesProducedBy('C-TEAM')
        set(['TEST3', 'TEST2'])
        >>> manifest.getDeliverablesProducedBy('D-TEAM')
        set([])
        """
        return self._getDeliverablesContainingElementWithId('producer', producerName)

    def getDeliverablesConsumedBy(self, consumerName):
        """Get the deliverables produced by the specified consumer.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST1">
        ...          <producer id="A-TEAM"/>
        ...          <producer id="B-TEAM"/>
        ...          <consumer id="C-TEAM"/>
        ...          <consumer id="D-TEAM"/>
        ...        </template>
        ...        <template id="TEST2">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...        <template id="TEST3">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablesConsumedBy('A-TEAM')
        set(['TEST3', 'TEST2'])
        >>> manifest.getDeliverablesConsumedBy('B-TEAM')
        set([])
        >>> manifest.getDeliverablesConsumedBy('C-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesConsumedBy('D-TEAM')
        set(['TEST1'])
        """
        return self._getDeliverablesContainingElementWithId('consumer', consumerName)
    
    def _getDeliverablesContainingElementWithId(self, tagName, id_):
        """Get the deliverables that contain elements named `tagName` and id
        attribute `id_`.  That is, elements of the form,
        
            <tagName id=id_>

        This is the common kernel of `getDeliverablesProducedBy()` and
        `getDeliverablesConsumedBy()`.  See their documentation for details
        and tests.
        """
        assert isinstance(id_, basestring), 'id_ valid'
        deliverableNames = set()
        for template in self._rootElement.iterfind('template'):
            for item in template.iterfind(tagName):
                _ = item.get('id')
                if item.get('id') == id_:
                    deliverableNames.add(template.get('id'))
        return deliverableNames

    def getDeliverablesProducedByCommaSeparated(self, producerNamesCommaSeparated):
        """Expand a string containing a comma-separated list of producer teams
        to a set of unique deliverable names.  See `getDeliverablesProducedBy()`
        for details.
        
        This method also converts its inputs to upper case for the convenience
        of careless typists.
        
        This method is used to read command line arguments.  Use
        `getDeliverablesProducedBy()` within an application.
        
        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST1">
        ...          <producer id="A-TEAM"/>
        ...          <producer id="B-TEAM"/>
        ...          <consumer id="C-TEAM"/>
        ...          <consumer id="D-TEAM"/>
        ...        </template>
        ...        <template id="TEST2">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...        <template id="TEST3">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablesProducedByCommaSeparated('A-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('B-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('C-TEAM')
        set(['TEST3', 'TEST2'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('D-TEAM')
        set([])
        >>>
        >>> manifest.getDeliverablesProducedByCommaSeparated('A-TEAM,B-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('B-TEAM,D-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('A-TEAM,C-TEAM')
        set(['TEST1', 'TEST3', 'TEST2'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('a-team,c-team')
        set(['TEST1', 'TEST3', 'TEST2'])
        >>> manifest.getDeliverablesProducedByCommaSeparated('C-TEAM,NONEXISTENT')
        Traceback (most recent call last):
          ...
        dmError: 'NONEXISTENT' is not a producer team name.
        """
        return self._getDeliverablesProducedOrConsumedByCommaSeparated('producer',
                                                    producerNamesCommaSeparated)

    def getDeliverablesConsumedByCommaSeparated(self, consumerNamesCommaSeparated):
        """Get the deliverables produced by the specified consumer.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...      <templateset>
        ...        <template id="TEST1">
        ...          <producer id="A-TEAM"/>
        ...          <producer id="B-TEAM"/>
        ...          <consumer id="C-TEAM"/>
        ...          <consumer id="D-TEAM"/>
        ...        </template>
        ...        <template id="TEST2">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...        <template id="TEST3">
        ...          <producer id="C-TEAM"/>
        ...          <consumer id="A-TEAM"/>
        ...        </template>
        ...      </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablesConsumedByCommaSeparated('A-TEAM')
        set(['TEST3', 'TEST2'])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('B-TEAM')
        set([])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('C-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('D-TEAM')
        set(['TEST1'])
        >>>
        >>> manifest.getDeliverablesConsumedByCommaSeparated('A-TEAM,B-TEAM')
        set(['TEST3', 'TEST2'])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('B-TEAM,C-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('C-TEAM,D-TEAM')
        set(['TEST1'])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('c-team,d-team')
        set(['TEST1'])
        >>> manifest.getDeliverablesConsumedByCommaSeparated('C-TEAM,NONEXISTENT')
        Traceback (most recent call last):
          ...
        dmError: 'NONEXISTENT' is not a consumer team name.
        """
        return self._getDeliverablesProducedOrConsumedByCommaSeparated('consumer',
                                                    consumerNamesCommaSeparated)

    def _getDeliverablesProducedOrConsumedByCommaSeparated(self, tagName, itemsString):
        """This is the common kernel of `_getDeliverablesProducedByCommaSeparated()`
        and `_getDeliverablesConsumedByCommaSeparated()`.  See their
        documentation for details and tests.
        """
        if not isinstance(itemsString, basestring):
            raise dmError("The {} list '{}' is not a string".format(tagName,
                                                                    itemsString))
        itemList = itemsString.upper().split(',')
        erroneousNames = set()
        for name in itemList:
            if not self.isTeam(name):
                erroneousNames.add(name)
        errorCount = len(erroneousNames)
        if errorCount == 1:
            raise dmError(
                "'{}' is not a {} team name.".format(', '.join(erroneousNames), tagName))
        if errorCount > 1:
            raise dmError(
                "'{}' are not {} team names.".format(', '.join(erroneousNames), tagName))

        deliverables = set()
        for itemName in itemList:
            deliverables |= self._getDeliverablesContainingElementWithId (tagName, 
                                                                          itemName)
        return deliverables

    @classmethod
    def _getDatabaseList(cls, item):
        '''Get the list that describes the specified database deliverable item.'''
        ret = []
        libPath = item.find('libpath')
        if libPath is None:
            # It's not our job to verify the templateset here, but this is just too much
            raise dmError(
                "Element '<libpath>' within '<{} id='{}'>' is missing, which is illegal.".
                    format(item.tag, item.get('id')))
        libPathName = os.path.normpath(libPath.text.strip())
        if not libPathName:
            # It's not our job to verify the templateset here, but this is just too much
            raise dmError(
                "Element '<lib>' within '<{} id='{}'>' is empty, which is illegal.".
                    format(item.tag, item.get('id')))
        ret.append(libPathName)
        
        lib = item.find('lib')
        if lib is None:
            ret.append(os.path.basename(libPathName))
        else:
            libName = lib.text.strip()
            if libName:
                ret.append(libName)
            else:
                ret.append(os.path.basename(libPathName))

        cell = item.find('cell')
        if cell is None:
            return ret
        cellName = cell.text.strip()
        if not cellName:
            return ret
        ret.append(cellName)

        view = item.find('view')
        if view is None:
            return ret
        viewName = view.text.strip()
        if not viewName:
            return ret
        ret.append(viewName)

        viewType = view.get('viewtype')
        if not viewType:
            return ret
        ret.append(viewType)
        
        return ret

    def _getDeliverable(self, deliverableName, isAlias=False):
        """Get the element representing the specified deliverable.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...     <templateset>
        ...        <template id="TEST">
        ...            <pattern id="def">
        ...                ip1/icc/ip1.def
        ...            </pattern>
        ...            <pattern id="lef">
        ...                ip1/icc/ip1.lef
        ...            </pattern>
        ...        </template>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest._getDeliverable('TEST').get('id')
        'TEST'
        """
        assert isinstance(deliverableName, basestring), 'deliverableName valid'
        for template in self._rootElement.iterfind('template'):
            if template.get('id') == deliverableName:
                return template

        if isAlias:
            msg = "Could not find any alias nor deliverable named '{}'.". \
                    format(deliverableName)
        else:
            msg = "Could not find deliverable item(s) " \
                    "because deliverable '{}' does not exist.".format(deliverableName)
        raise dmError(msg)

    def getDeliverablePredecessor(self, deliverableName):
        """Get a set of the predecessor(s) of the specified deliverable.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...    <templateset>
        ...      <template id="UNCONNECTED" />
        ...      
        ...      <template id="SUCCESSOR1" />
        ...      <template id="SUCCESSOR2" />
        ...      <template id="SUCCESSOR3" />
        ...      
        ...      <template id="PREDECESSOR1" />
        ...      <template id="PREDECESSOR2" />
        ...      <template id="PREDECESSOR3" />
        ...      
        ...      <successor id="SUCCESSOR1">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR2</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR2">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR3">
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverablePredecessor('UNCONNECTED')
        set([])
        >>> manifest.getDeliverablePredecessor('PREDECESSOR1')
        set([])
        >>> manifest.getDeliverablePredecessor('SUCCESSOR1')
        set(['PREDECESSOR1', 'PREDECESSOR2'])
        >>> manifest.getDeliverablePredecessor('SUCCESSOR2')
        set(['PREDECESSOR1', 'PREDECESSOR3'])
        >>> manifest.getDeliverablePredecessor('SUCCESSOR3')
        set(['PREDECESSOR3'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverablePredecessor('SUCCESSOR2')
        >>> ignoredValue = s.pop()
        >>> manifest.getDeliverablePredecessor('SUCCESSOR2')
        set(['PREDECESSOR1', 'PREDECESSOR3'])
        """
        if self._predecessors is None:
            self._buildPredecessorSuccessorDatabase()
        return self._predecessors.get(deliverableName, set()).copy()

    def getDeliverableSuccessor(self, deliverableName):
        """Get a set of the successor(s) of the specified deliverable.  

        Usage example:
        
        >>> from dmx.dmlib.Manifest import Manifest
        >>> templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        ...    <templateset>
        ...      <template id="UNCONNECTED" />
        ...      
        ...      <template id="SUCCESSOR1" />
        ...      <template id="SUCCESSOR2" />
        ...      <template id="SUCCESSOR3" />
        ...      
        ...      <template id="PREDECESSOR1" />
        ...      <template id="PREDECESSOR2" />
        ...      <template id="PREDECESSOR3" />
        ...      
        ...      <successor id="SUCCESSOR1">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR2</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR2">
        ...        <predecessor>PREDECESSOR1</predecessor>
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...      <successor id="SUCCESSOR3">
        ...        <predecessor>PREDECESSOR3</predecessor>
        ...      </successor>
        ...    </templateset>'''
        >>> manifest = Manifest('testip1', templatesetString=templatesetXML)
        >>> manifest.getDeliverableSuccessor('UNCONNECTED')
        set([])
        >>> manifest.getDeliverableSuccessor('SUCCESSOR1')
        set([])
        >>> manifest.getDeliverableSuccessor('PREDECESSOR1')
        set(['SUCCESSOR1', 'SUCCESSOR2'])
        >>> manifest.getDeliverableSuccessor('PREDECESSOR2')
        set(['SUCCESSOR1'])
        >>> manifest.getDeliverableSuccessor('PREDECESSOR3')
        set(['SUCCESSOR2', 'SUCCESSOR3'])
        >>>
        >>> # pop() can be used to access members without harming the database
        >>> s = manifest.getDeliverableSuccessor('PREDECESSOR1')
        >>> ignoredValue = s.pop()
        >>> manifest.getDeliverableSuccessor('PREDECESSOR1')
        set(['SUCCESSOR1', 'SUCCESSOR2'])
        """
        if self._successors is None:
            self._buildPredecessorSuccessorDatabase()
        return self._successors.get(deliverableName, set()).copy()

    def _buildPredecessorSuccessorDatabase(self):
        """Create the database of predecessors and successors.  This method
        is run just once the first time `getDeliverablePredecessor()` or
        `getDeliverableSuccessor()` is called.
        """
        assert (self._successors is None) and (self._predecessors is None), \
            'Invariant: _successors and _predecessors both uninitialized'
        self._successors = dict()
        self._predecessors = dict()

        for successor in self._rootElement.iterfind('successor'):
            successorName = successor.get('id')
            if not successorName:
                raise dmError("Found 'successor' without an id attribute. "
                              "This is not allowed.")
            predecessorNames = set()
            
            for predecessor in successor.iterfind('predecessor'):
                predecessorName = predecessor.text.strip()
                if not predecessorName:
                    raise dmError("Found 'predecessor' without a text value. "
                                  "This is not allowed.")
                self._successors.setdefault(predecessorName, set()).add(successorName)
                predecessorNames.add(predecessorName)

            self._predecessors[successorName] = predecessorNames
            
    def getPredecessorSuccessorPairs (self, deliverableNames):
        '''
        Returns a list of 'predecessor, successor' items for 'deliverableNames'.
        Note that if some deliverable doesn't have any predecessor or successor,
        *it will *not* be included in the result
        The result is sorted 
        '''
        edgeSet = set()
        for d in deliverableNames:
            for p in self.getDeliverablePredecessor(d):
                if p not in deliverableNames:
                    continue
                edgeSet.add ((p, d))
            for s in self.getDeliverableSuccessor (d):
                if s not in deliverableNames:
                    continue
                edgeSet.add ((d, s))
        ret = sorted (edgeSet)
        return ret        
        
            
    def sortDeliverablesTopologically (self, deliverableNames):
        '''
        Returns a topologically-sorted copy of 'deliverableNames' 
        (predecessors come first)
        On errors, returns a single string
        '''
        
        edgeList = self.getPredecessorSuccessorPairs (deliverableNames)
        
        # Determine 'astrayNodes' (will be added explicitely)
        linkedNodes = set()
        for e in edgeList:
            linkedNodes.add (e[0])
            linkedNodes.add (e[1])
        astrayNodes = set (deliverableNames) - set (linkedNodes)
                
        try:
            ret = []
            sortedDeliverables = General.sort_DAG (edgeList)
            
            for r in sortedDeliverables:
                if r in deliverableNames:
                    ret.append (r)
                    
            for a in astrayNodes:
                ret.append (a)
                    
            return ret
        
        except IndexError as e:
            return str (e)
        
    @staticmethod
    def getAllDefaultDeliverables():
        '''
        Returns a topologically-sorted list (successof first) of all deliverables
        as defined in the 'official' templateset.xml
        On errors, returns a single string
        '''
        fakeManifest = Manifest ('fakeIp')
        allDeliverables = fakeManifest.allDeliverables
        allSorted = fakeManifest.sortDeliverablesTopologically (allDeliverables)
        return allSorted
    
    @staticmethod
    def getAllDefaultPredecessorSuccessorPairs():
        '''
        Returns a list of all (predecessor, successor) deliverables as defined in the
        'official' templateset.xml
        Note that deliverables *without* predecessors or successor will *not* end up
        in the result.
        '''
        fakeManifest = Manifest ('fakeIp')
        allDeliverables = fakeManifest.allDeliverables
        ret = fakeManifest.getPredecessorSuccessorPairs (allDeliverables)
        return ret
        
            

if __name__ == "__main__":
    # Running Manifest_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod(verbose=True)
