#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/successor.py#1 $

"""
This class defines the immediate prerequisites for each deliverable
by defining a predecessor-successor relationship.
It stores the XML elements `<successor>` and `<predecessor>`.  For example,

>>> t = Successor('CVRTL')
>>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
'<?xml version="1.0" encoding="utf-8"?>
<successor id="CVRTL">
 <predecessor>
    RTL
 </predecessor>
</successor> '

reveals that deliverable `CVRTL` is created from deliverable `RTL`.
Every deliverable has a successor-predecessor relationship defined.
However, that relationship
might be empty.  For example, RTL files are created manually&mdash;they are
original data that depends on nothing else in the flow.  By recursively following
the dependency relationships to the original files that have no predecessors (like BCMRBC),
the order of steps required to update any data can be derived.

Another way to think of this is how it would be represented in a Makefile.
The above relationship is equivalent to the following Makefile target dependency:

  CVRTL : RTL

The <successor> Element
-------------------------
This element has the following attributes:

* `id`, the name of this successor

The <predecessor> Element
----------------------------
The text of this element is the name of a deliverable from which the dependent
deliverable is made.

There are no attributes on this element.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

#pylint: disable-all

from xml.etree.ElementTree import Element, SubElement, tostring #@UnusedImport

from dmx.dmlib.templateset.xmlbase import XmlBase

class Successor(XmlBase):
    '''Construct the deliverable predecessor-successor relationship for the named deliverable.
        
    >>> t = Successor('BCMRBC')
    >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    '<?xml version="1.0" encoding="utf-8"?>
    <successor id="BCMRBC"/> '
    '''
     
    def __init__(self, idd):
        self._id = idd
        self._predecessorList = []
        self._caseid  = None
        self._isReady = False
        
        # Execute the function named by the name argument
        factoryFunction = getattr(self, '_' + idd)
        factoryFunction()

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'successor'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Successor'
    
    @property
    def id(self):
        '''The deliverable name of this successor.
        
        >>> t = Successor('CVRTL')
        >>> t.id
        'CVRTL'
        '''
        return self._id
    
    @property
    def caseid (self):
        '''The bug number under which corrections to this deliverable were submitted,
        or None if nothing has been reported.
        
        >>> t = Successor('CVRTL')
        >>> t.caseid 
        205261

        The default is None:
        
        >>> t = Successor('EMPTY')
        >>> t.caseid 

        '''
        return self._caseid 
    
    @property
    def isReady(self):
        '''Whether this deliverable has been approved as ready for use.

        >>> d = Successor('CVRTL')
        >>> d.isReady
        True

        The default is False:
        
        >>> d = Successor('EMPTY')
        >>> d.isReady
        False
        '''
        return self._isReady

    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.
        
        >>> t = Successor('CVRTL')
        >>> tostring(t.element())      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<successor...>...</successor>'
        
        Declare this instance as a SubElement of a parent:

        >>> t = Successor('CVRTL')
        >>> parent = Element("parent")
        >>> child = t.element(parent)
        >>> tostring(parent)      #doctest: +ELLIPSIS
        '<parent><successor...>...</successor></parent>'
        '''
        if parent is None:
            d = Element('successor')
        else:
            d = SubElement(parent, 'successor')
        d.set('id', self._id)
        for predecessorName in self._predecessorList:
            p = SubElement(d, 'predecessor')
            p.text = predecessorName
        return d
                   
    def report(self):
        '''Return a human readable string representation.
        
        >>> d = Successor('CVRTL')
        >>> d.report()
        'Successor CVRTL:\\n  Predecessor: RTL\\n'
        '''
        assert self._id, 'Every successor has an id'
        ret = 'Successor {}:\n'.format(self._id)
        
        for predecessor in self._predecessorList:
            ret += '  Predecessor: {}\n'.format(predecessor)

        return ret

    def _addPredecessor(self, predecessorName):
        '''Add a predecessor to this successor.
        
        >>> t = Successor('EMPTY')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="EMPTY"/> '
        >>>
        >>> t._addPredecessor('BCMRBC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="EMPTY">
          <predecessor>
            BCMRBC
          </predecessor>
        </successor> '
        '''
        self._predecessorList.append(predecessorName)
        


    def _fakeExcessTemplateForTesting(self):
        '''Create a fake, illegal successor.  This is used for creating errors in testing.

        >>> t = Successor('fakeExcessTemplateForTesting')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="fakeExcessTemplateForTesting"/> '
        '''
        pass
        
    def _EMPTY(self):
        '''Create an empty deliverable template.  This is for testing only.

        >>> t = Successor('EMPTY')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="EMPTY"/> '
        '''
        pass
    
    def _BCMRBC(self):
        '''Predecessors for successor BCMRBC.

        >>> t = Successor('BCMRBC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="BCMRBC"/> '
        '''
        self._caseid  = 205257
        self._isReady = True

    def _CDC(self):
        '''Predecessors for successor CDC.

        >>> t = Successor('CDC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="CDC">
          <predecessor>
            BCMRBC
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205259
        self._isReady = True
        self._addPredecessor('BCMRBC')
        self._addPredecessor('RTL')
        
    def _CDL(self):
        '''Predecessors for successor CDL.

        >>> t = Successor('CDL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="CDL">
          <predecessor>
            OA
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209050
        self._isReady = True
        self._addPredecessor('OA')
        
    def _CIRCUITSIM(self):
        '''Predecessors for successor CIRCUITSIM.

        >>> t = Successor('CIRCUITSIM')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="CIRCUITSIM">
          <predecessor>
            OA
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209037
        self._isReady = True
        self._addPredecessor('OA')

    def _COMPLIB(self):
        '''Predecessors for successor COMPLIB.

        >>> t = Successor('COMPLIB')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="COMPLIB">
          <predecessor>
            RTL
          </predecessor>
          <predecessor>
            INTFC
          </predecessor>
        </successor> '
        '''
        self._caseid  = 206838
        self._isReady = True
        self._addPredecessor('RTL')
        self._addPredecessor('INTFC')
        
    def _COMPLIBPHYS(self):
        '''Predecessors for successor COMPLIBPHYS.

        >>> t = Successor('COMPLIBPHYS')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="COMPLIBPHYS">
          <predecessor>
            COMPLIB
          </predecessor>
          <predecessor>
            TRACKPHYS
          </predecessor>
        </successor> '
        '''
        self._caseid  = 234535
        self._isReady = True
        self._addPredecessor('COMPLIB')
        self._addPredecessor('TRACKPHYS')
        
    def _CVIMPL(self):
        '''Predecessors for successor CVIMPL.

        >>> t = Successor('CVIMPL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="CVIMPL">
          <predecessor>
            CVRTL
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
          <predecessor>
            SYN
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209035
        self._isReady = True
        self._addPredecessor('CVRTL')
        self._addPredecessor('RTL')
        self._addPredecessor('SYN')
        
    def _CVRTL(self):
        '''Predecessors for successor CVRTL.

        >>> t = Successor('CVRTL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="CVRTL">
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205261
        self._isReady = True
        self._addPredecessor('RTL')
        
    def _CVSIGNOFF(self):
        '''Predecessors for successor CVSIGNOFF.

        >>> t = Successor('CVSIGNOFF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="CVSIGNOFF">
          <predecessor>
            CVRTL
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209036
        self._isReady = True
        self._addPredecessor('CVRTL')
        self._addPredecessor('RTL')
        
    def _DFTDSM(self):
        '''Predecessors for successor DFTDSM.

        >>> t = Successor('DFTDSM')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="DFTDSM">
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 216062
        self._isReady = True
        self._addPredecessor('RTL')

    def _DV(self):
        '''Predecessors for successor DV.

        >>> t = Successor('DV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="DV">
          <predecessor>
            INTERRBA
          </predecessor>
          <predecessor>
            NETLIST
          </predecessor>
          <predecessor>
            PNR
          </predecessor>
          <predecessor>
            RDF
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 208253
        self._isReady = True
        self._addPredecessor('INTERRBA')
        self._addPredecessor('NETLIST')
        self._addPredecessor('PNR')
        self._addPredecessor('RDF')
        self._addPredecessor('RTL')

    def _FCPWRMOD(self):
        '''Predecessors for successor FCPWRMOD.

        >>> t = Successor('FCPWRMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="FCPWRMOD">
          <predecessor>
            IPPWRMOD
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209040
        self._isReady = True
        self._addPredecessor('IPPWRMOD')

    def _FV(self):
        '''Predecessors for successor FV.

        >>> t = Successor('FV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="FV">
          <predecessor>
            RTL
          </predecessor>
          <predecessor>
            OA
          </predecessor>
          <predecessor>
            YX2GLN
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209041
        self._isReady = True
        self._addPredecessor('RTL')
        self._addPredecessor('OA')
        self._addPredecessor('YX2GLN')
        
    def _FVPNR(self):
        '''Predecessors for successor FVPNR.

        >>> t = Successor('FVPNR')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="FVPNR">
          <predecessor>
            PNR
          </predecessor>
          <predecessor>
            SYN
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205265
        self._isReady = True
        self._addPredecessor('PNR')
        self._addPredecessor('SYN')
        
    def _FVSYN(self):
        '''Predecessors for successor FVSYN.

        >>> t = Successor('FVSYN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="FVSYN">
          <predecessor>
            RTL
          </predecessor>
          <predecessor>
            SYN
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205267
        self._isReady = True
        self._addPredecessor('RTL')
        self._addPredecessor('SYN')
        
    def _GP(self):
        '''Predecessors for successor GP.

        >>> t = Successor('GP')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="GP">
          <predecessor>
            RTL
          </predecessor>
          <predecessor>
            RDF
          </predecessor>
          <predecessor>
            BCMRBC
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209043
        self._isReady = True
        self._addPredecessor('RTL')
        self._addPredecessor('RDF')
        self._addPredecessor('BCMRBC')

    def _INTERRBA(self):
        '''Predecessors for successor INTERRBA.

        >>> t = Successor('INTERRBA')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="INTERRBA">
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205270
        self._isReady = True
        self._addPredecessor('RTL')
        

    def _INTFC(self):
        '''Predecessors for successor INTFC.
        TO_DO: What kind of abstract?

        >>> t = Successor('INTFC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="INTFC"/> '
        '''
        self._caseid  = 206838
        self._isReady = True

    def _IPFLOORPLAN(self):
        '''Predecessors for successor IPFLOORPLAN.

        >>> t = Successor('IPFLOORPLAN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="IPFLOORPLAN">
          <predecessor>
            OA
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205275
        self._isReady = True
        self._addPredecessor('OA')

    def _IPSPEC(self):
        '''Predecessors for successor IPSPEC.

        >>> t = Successor('IPSPEC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="IPSPEC"/> '
        '''
        self._caseid  = 205286
        self._isReady = True

    def _IPPWRMOD(self):
        '''Predecessors for successor IPPWRMOD.

        >>> t = Successor('IPPWRMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="IPPWRMOD">
          <predecessor>
            BCMRBC
          </predecessor>
          <predecessor>
            RCXT
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209039
        self._isReady = True
        self._addPredecessor('BCMRBC')
        self._addPredecessor('RCXT')

    def _IPXACT(self):
        '''Predecessors for successor IPXACT.

        >>> t = Successor('IPXACT')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="IPXACT">
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._isReady = False
        self._caseid  = 209045
        self._addPredecessor('RTL')

    def _LAYMISC(self):
        '''Predecessors for successor LAYMISC.

        >>> t = Successor('LAYMISC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="LAYMISC">
          <predecessor>
            PV
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205448
        self._isReady = True
        self._addPredecessor('PV')


    def _LINT(self):
        '''Predecessors for successor LINT.

        >>> t = Successor('LINT')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="LINT">
          <predecessor>
            RTL
          </predecessor>
         </successor> '
        '''
        self._isReady = True
        self._caseid  = 205449
        self._addPredecessor('RTL')

    def _MW(self):
        '''Predecessors for successor MW.

        >>> t = Successor('MW')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="MW"> 
          <predecessor>
            COMPLIB
          </predecessor>
          <predecessor>
            IPFLOORPLAN
          </predecessor>
        </successor> '
        '''
        self._caseid  = 210067
        self._isReady = True
        self._addPredecessor('COMPLIB')
        self._addPredecessor('IPFLOORPLAN')

    def _NETLIST(self):
        '''Predecessors for successor NETLIST.

        >>> t = Successor('NETLIST')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="NETLIST">
          <predecessor>
            COMPLIB
          </predecessor>
        </successor> '
        '''
        self._caseid  = 206839
        self._isReady = True
        self._addPredecessor('COMPLIB')

    def _OA(self):
        '''Predecessors for successor OA.

        >>> t = Successor('OA')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="OA">
          <predecessor>
            NETLIST
          </predecessor>
          <predecessor>
            PNR
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209768
        self._isReady = True
        self._addPredecessor('NETLIST')
        self._addPredecessor('PNR')
        self._addPredecessor('RTL')

    def _OA_SIM(self):
        '''Predecessors for successor OA_SIM.

        >>> t = Successor('OA_SIM')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="OA_SIM"/> '
        '''
        self._caseid  = 82023
        self._isReady = True

    def _OASIS(self):
        '''Predecessors for successor OASIS.

        >>> t = Successor('OASIS')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="OASIS">
          <predecessor>
            MW
          </predecessor>
          <predecessor>
            NETLIST
          </predecessor>
          <predecessor>
            OA
          </predecessor>
          <predecessor>
            PNR
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205450
        self._isReady = True
        self._addPredecessor('MW')
        self._addPredecessor('NETLIST')
        self._addPredecessor('OA')
        self._addPredecessor('PNR')
        
    def _PERIODICTST(self):
        '''Predecessors for successor PERIODICTST.

        >>> t = Successor('PERIODICTST')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PERIODICTST"/> '
        '''
        self._caseid  = 205451
        self._isReady = True

    def _PINTABLE(self):
        '''Predecessors for successor PINTABLE.

        >>> t = Successor('PINTABLE')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PINTABLE"/> '
        '''
        self._caseid  = 28340
        self._isReady = True

    def _PKGDE(self):
        '''Predecessors for successor PKGDE.

        >>> t = Successor('PKGDE')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PKGDE">
          <predecessor>
            PINTABLE
          </predecessor>
        </successor> '
        '''
        self._caseid  = 324460
        self._isReady = True
        self._addPredecessor('PINTABLE')
        
    def _PKGEE(self):
        '''Predecessors for successor PKGEE.

        >>> t = Successor('PKGEE')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PKGEE">
          <predecessor>
            PINTABLE
          </predecessor>
        </successor> '
        '''
        self._caseid  = 324461
        self._isReady = True
        self._addPredecessor('PINTABLE')
        
    def _PNR(self):
        '''Predecessors for successor PNR.

        >>> t = Successor('PNR')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PNR">
          <predecessor>
            CVIMPL
          </predecessor>
          <predecessor>
            SYN
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205451
        self._isReady = True
        self._addPredecessor('CVIMPL')
        self._addPredecessor('SYN')
        
    def _PORTLIST(self):
        '''Predecessors for successor PORTLIST.

        >>> t = Successor('PORTLIST')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PORTLIST"/> '
        '''
        self._caseid  = 205453
        self._isReady = True

    def _PV(self):
        '''Predecessors for successor PV.

        >>> t = Successor('PV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="PV">
          <predecessor>
            CDL
          </predecessor>
          <predecessor>
            OA
          </predecessor>
          <predecessor>
            OASIS
          </predecessor>
          <predecessor>
            SCHMISC
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209046
        self._isReady = True
        self._addPredecessor('CDL')
        self._addPredecessor('OA')
        self._addPredecessor('OASIS')
        self._addPredecessor('SCHMISC')
        
    def _R2G2(self):
        '''Predecessors for successor R2G2.

        >>> t = Successor('R2G2')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="R2G2"/> '
        '''
        self._caseid  = 171832
        self._isReady = True

    def _RCXT(self):
        '''Predecessors for successor RCXT.

        >>> t = Successor('RCXT')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="RCXT">
          <predecessor>
            CDL
          </predecessor>
          <predecessor>
            OASIS
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209048
        self._isReady = True
        self._addPredecessor('CDL')
        self._addPredecessor('OASIS')
        
    def _RDF(self):
        '''Predecessors for successor RDF.

        >>> t = Successor('RDF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="RDF"/> '
        '''
        self._caseid  = 205454
        self._isReady = True

    def _RELDOC(self):
        '''Predecessors for successor RELDOC.

        >>> t = Successor('RELDOC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="RELDOC"/> '
        '''
        self._caseid  = 241400
        self._isReady = True


    def _RTL(self):
        '''Predecessors for successor RTL.

        >>> t = Successor('RTL')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="RTL"/> '
        '''
        self._caseid  = 205507
        self._isReady = True

    def _RTLCOMPCHK(self):
        '''Predecessors for successor RTLCOMPCHK.

        >>> t = Successor('RTLCOMPCHK')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="RTLCOMPCHK">
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205455
        self._isReady = True
        self._addPredecessor('RTL')

    def _RV(self):
        '''Predecessors for successor RV.

        >>> t = Successor('RV')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="RV">
          <predecessor>
            OASIS
          </predecessor>
          <predecessor>
            PNR
          </predecessor>
          <predecessor>
            RCXT
          </predecessor>
          <predecessor>
            SCHMISC
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209049
        self._isReady = True
        self._addPredecessor ('OASIS')
        self._addPredecessor ('PNR')
        self._addPredecessor ('RCXT')
        self._addPredecessor ('SCHMISC')

    def _SCHMISC(self):
        '''Predecessors for successor SCHMISC.

        >>> t = Successor('SCHMISC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="SCHMISC">
          <predecessor>
            CDL
          </predecessor>
          <predecessor>
            OA
          </predecessor>
          <predecessor>
            UPF
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209769
        self._isReady = True
        self._addPredecessor('CDL')
        self._addPredecessor('OA')
        self._addPredecessor('UPF')
        

    def _SDF(self):
        '''Predecessors for successor SDF.

        >>> t = Successor('SDF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="SDF">
          <predecessor>
            RCXT
          </predecessor>
          <predecessor>
            TIMEMOD
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209770
        self._isReady = True
        self._addPredecessor('RCXT')
        self._addPredecessor('TIMEMOD')
        
    def _STA(self):
        '''Predecessors for successor STA.

        >>> t = Successor('STA')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="STA">
          <predecessor>
            PNR
          </predecessor>
          <predecessor>
            RCXT
          </predecessor>
          <predecessor>
            TIMEMOD
          </predecessor>
        </successor> '
        '''
        self._caseid  = 82023
        self._isReady = True
        self._addPredecessor('PNR')
        self._addPredecessor('RCXT')
        self._addPredecessor('TIMEMOD')
        
    def _STAMOD(self):
        '''Predecessors for successor STAMOD.

        >>> t = Successor('STAMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="STAMOD"/> '
        '''
        self._caseid  = 205455
        self._isReady = True

    def _SYN(self):
        '''Predecessors for successor SYN.

        >>> t = Successor('SYN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="SYN">
          <predecessor>
            CVRTL
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
          <predecessor>
            UPF
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205456
        self._isReady = True
        self._addPredecessor('CVRTL')
        self._addPredecessor('RTL')
        self._addPredecessor('UPF')

    def _TIMEMOD(self):
        '''Predecessors for successor TIMEMOD.

        >>> t = Successor('TIMEMOD')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="TIMEMOD">
          <predecessor>
            CVSIGNOFF
          </predecessor>
          <predecessor>
            OA
          </predecessor>
          <predecessor>
            RCXT
          </predecessor>
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 205457
        self._isReady = True
        self._addPredecessor('CVSIGNOFF')
        self._addPredecessor('OA')
        self._addPredecessor('RCXT')
        self._addPredecessor('RTL')

    def _TRACKPHYS(self):
        '''Predecessors for successor TRACKPHYS.

        >>> t = Successor('TRACKPHYS')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="TRACKPHYS"/> '
        '''
        self._caseid  = 255069

    def _UPF(self):
        '''Predecessors for successor UPF.

        >>> t = Successor('UPF')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="UPF">
          <predecessor>
            RTL
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209037
        self._addPredecessor('RTL')

    def _UPFFC(self):
        '''Predecessors for successor UPFFC.

        >>> t = Successor('UPFFC')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="UPFFC">
          <predecessor>
            UPF
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209703
        self._isReady = True
        self._addPredecessor('UPF')

    def _YX2GLN(self):
        '''Predecessors for successor YX2GLN.
        
        >>> t = Successor('YX2GLN')
        >>> t.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <successor id="YX2GLN">
          <predecessor>
            OA
          </predecessor>
          <predecessor>
            RDF
          </predecessor>
        </successor> '
        '''
        self._caseid  = 209041
        self._isReady = True
        self._addPredecessor('OA')
        self._addPredecessor('RDF')

        # No predecessors

        
if __name__ == "__main__":
    # Running Successor_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
