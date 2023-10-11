#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/alias.py#1 $

"""
Alias is a factory class that instantiates an object
specifying an alias and its members.  It stores the XML element `<alias>`.

The <alias> Element
=========================
This element has the following attributes:

* `id`, the name of this alias

The <member> Element
=========================
The text of this element is the name of a deliverable or another alias.
Of course, different aliases may contain the same member.  Obviously,
alias-member relationships must be acyclic.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

from xml.etree.ElementTree import Element, SubElement, tostring

from dmx.dmlib.templateset.xmlbase import XmlBase

class Alias(XmlBase):
    '''Construct a deliverable alias with the specified name.
    '''
     
    def __init__(self, id):
        self._id = id
        self._caseid  = None
        self._isReady = False
        self._members = []
        
        # Execute the function named by the id argument
        factoryFunction = getattr(self, '_' + id)
        factoryFunction()

    @property
    def tagName(self):
        '''The tag name for this XML element.'''
        return 'alias'
    
    @property
    def reportName(self):
        '''The natural language name for this object for use in reports and messages.'''
        return 'Alias'
    
    @property
    def id(self):
        '''The name of the alias.
        
        >>> a = Alias('FAKE')
        >>> a.id
        'FAKE'
        '''
        return self._id
    
    @property
    def caseid (self):
        '''The bug number under which corrections to this alias were submitted,
        or None if nothing has been reported.
        
        >>> a = Alias('FAKE')
        >>> a._caseid = 100
        >>> a.caseid
        100

        The default is None:
        
        >>> a = Alias('EMPTYALIAS')
        >>> a.caseid  is None
        True
        '''
        return self._caseid 
    
    @property
    def isReady(self):
        '''Whether this deliverable has been approved as ready for use.

        >>> a = Alias('FAKE')
        >>> a.caseid
        100

        The default is False:
        
        >>> a = Alias('EMPTYALIAS')
        >>> a.isReady
        False
        '''
        return self._isReady
    
    def element(self, parent=None):
        '''Return an XML ElementTree representing this instance.  If a parent
        Element is specified, make the ElementTree a SubElement of the parent.
        
        >>> alias = Alias('FAKE')
        >>> tostring(alias.element())      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<alias id="FAKE">...</alias>'
        
        Declare this instance as a SubElement of a parent:

        >>> alias = Alias('FAKE')
        >>> parent = Element("parent")
        >>> child = alias.element(parent)
        >>> tostring(parent)      #doctest: +ELLIPSIS
        '<parent><alias id="FAKE">...</alias></parent>'
        '''
        if parent is None:
            d = Element(self.tagName)
        else:
            d = SubElement(parent, self.tagName)
        d.set('id', self._id)
        for member in self._members:
            p = SubElement(d, 'member')
            p.text = member
        return d
                   
    def report(self):
        '''Return a human readable string representation.  Arguments ipName and
        cellName are unused, but required by the abstract method.
        
        >>> a = Alias('FAKE')
        >>> a.report()
        'Alias FAKE:\\n  BCMRBC\\n  CDC\\n  LINT\\n'
        '''
        assert self._id, 'Every alias has an id'
        ret = '{} {}:\n'.format(self.reportName, self._id)
        
        for member in self._members:
            ret += '  {}\n'.format(member)

        return ret
                   
    def _addMember(self, memberName):
        '''Create an alias member.
        
        >>> a = Alias('EMPTYALIAS')
        >>> a._addMember('SERVANT1')
        >>> a._addMember('SERVANT2')
        >>> a._addMember('SERVANT3')
        >>> a.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <alias id="EMPTYALIAS">
          <member> SERVANT1 </member>
          <member> SERVANT2 </member>
          <member> SERVANT3 </member>
        </alias> '
        '''
        self._members.append(memberName)
        
    def _fakeExcessAliasForTesting(self):
        '''Create a fake, illegal alias that will be used to create an errors during testing.

        >>> a = Alias('fakeExcessAliasForTesting')
        >>> a.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <alias id="fakeExcessAliasForTesting"/> '
        '''
        pass

    def _EMPTYALIAS(self):
        '''Create an empty deliverable alias.  This is for testing only.

        >>> a = Alias('EMPTYALIAS')
        >>> a.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <alias id="EMPTYALIAS"/> '
        '''
        pass
    
    def _FAKE(self):
        '''Fake deliverable alias for testing.
        
        >>> a = Alias('FAKE')
        >>> a.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        '<?xml version="1.0" encoding="utf-8"?>
        <alias id="FAKE">
           <member> BCMRBC </member>
           <member> CDC </member>
           <member> LINT </member>
        </alias> '
        '''
        self._caseid  = 100
        self._isReady = True
        # deliverable list from http://sw-web.altera.com/ice/roadmap/
        deliverableNames = ['bcmrbc', 'cdc', 'lint']
        for deliverableName in deliverableNames:
            self._addMember(deliverableName.upper())

#    def _ASIC_E0(self):
#        '''Deliverable alias for the ASIC design bucket milestone 3.0ND5revA
#        (E0).
#        
#        >>> a = Alias('ASIC_E0')
#        >>> a.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <alias id="ASIC_E0">
#           <member> BCMRBC </member>
#           <member> CDC </member>
#           <member> CIRCUITSIM </member>
#           <member> COMPLIB </member>
#           <member> CVIMPL </member>
#           <member> CVRTL </member>
#           <member> CVSIGNOFF </member>
#           <member> DV </member>
#           <member> FVPNR </member>
#           <member> FVSYN </member>
#           <member> INTERRBA </member>
#           <member> IPPWRMOD </member>
#           <member> IPSPEC </member>
#           <member> IPTIMEMOD </member>
#           <member> LINT </member>
#           <member> MW </member>
#           <member> PERIODICTST </member>
#           <member> PNR </member>
#           <member> PORTLIST </member>
#           <member> PV </member>
#           <member> RCXT </member>
#           <member> RDF </member>
#           <member> RTL </member>
#           <member> RTLCOMPCHK </member>
#           <member> RV </member>
#           <member> SDF </member>
#           <member> STA </member>
#           <member> SYN </member>
#           <member> UPF </member>
#        </alias> '
#        '''
#        self._caseid  = None
#        self._isReady = False
#        # deliverable list from http://sw-web.altera.com/ice/roadmap/
#        deliverableNames = ['bcmrbc', 'cdc', 'circuitsim', 'complib', 'cvimpl',
#                            'cvrtl', 'cvsignoff', 'dv', 'fvpnr', 'fvsyn',
#                            'interrba', 'ippwrmod', 'ipspec', 'iptimemod',
#                            'lint', 'mw', 'periodictst', 'pnr', 'portlist',
#                            'pv', 'rcxt', 'rdf', 'rtl', 'rtlcompchk', 'rv',
#                            'sdf', 'sta', 'syn', 'upf']
#        for deliverableName in deliverableNames:
#            self._addMember(deliverableName.upper())


#    def _OA(self):
#        '''Deliverable alias for the SCH and LAY deliverables that both reside
#        in the IC Manage "oa" libType.
#        
#        `altera_icm.icmbase.ICMBase.getDeliverableName('oa')` depends on this
#        alias because it returns "OA", which is not a deliverable name.
#        However, alias "OA" resolves to deliverables SCH and LAY, so it works.
#        
#        >>> a = Alias('OA')
#        >>> a.toxml(fmt='doctest')      #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
#        '<?xml version="1.0" encoding="utf-8"?>
#        <alias id="OA">
#          <member> LAY </member>
#          <member> SCH </member>
#        </alias> '
#        '''
#        self._caseid  = None
#        self._isReady = False
#        self._addMember('LAY')
#        self._addMember('SCH')


if __name__ == "__main__":
    # Running Alias_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
