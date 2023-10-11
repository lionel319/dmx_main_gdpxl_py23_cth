#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/verifier.py#1 $

"""
Verify the internal consistency and semantics of the deliverable templateset XML.

Command Line Interface
=======================
`Verifier` is exposed as a command line application as the :doc:`templatesetverify`.

For more information on usage:

  templatesetverify -h
"""

import re
import os
import logging

from xml.etree.ElementTree import Element, ParseError
from dmx.dmlib.CheckerBase import CheckerBase
from dmx.dmlib.templateset.openaccess import OpenAccess
from dmx.dmlib.templateset.milkyway import Milkyway
from dmx.dmlib.Manifest import Manifest

# pylint: disable = W0622, W0104

class Verifier(CheckerBase):
    '''Construct a verifier for the specified templateset XML and verify it.
    
    If the doVerifyEveryTemplatePresent argument is True, check that every expected
    alias and deliverable template are defined.
    ''' 
    
    #'''The names of all Altera deliverable aliases.'''
    allAliasNames = (
        'FAKE',)
    
    #'''The names of all Altera deliverables.'''
    allDeliverableNames = (
        'BCMRBC',
        'CDC',
        'CDL',
        'CIRCUITSIM',
        'COMPLIB',
        'COMPLIBPHYS',
        'CVIMPL',
        'CVRTL',
        'CVSIGNOFF',
        'DFTDSM',
        'DV',
        'FCPWRMOD',
        'FV',
        'FVPNR',
        'FVSYN',
        'GP',
        'INTERRBA',
        'INTFC',
        'IPFLOORPLAN',
        'IPPWRMOD',
        'IPSPEC',
        'IPXACT',
        'LAYMISC',
        'LINT',
        'MW',
        'NETLIST',
        'OA',
        'OASIS',
        'OA_SIM',
        'PERIODICTST',
        'PINTABLE',
        'PKGDE',
        'PKGEE',
        'PNR',
        'PORTLIST',
        'PV',
        'R2G2',
        'RCXT',
        'RDF',
        'RELDOC',
        'RTL',
        'RTLCOMPCHK',
        'RV',
        'SCHMISC',
        'SDF',
        'STA',
        'STAMOD',
        'SYN',
        'TIMEMOD',
        'TRACKPHYS',
        'UPF',
        'UPFFC',
        'YX2GLN',
    )

    allTeamNames = {
    'DA',
    'FCI',
    'FCV',
    'ICD-PD',
    'ICD-IP',
    'IPD',
    'IP-DV',
    'LAY-IP',
    'NETLIST',
    'PACKAGING',
    'SOFTWARE',
    'SPNR',
    'TE',
    'LAYOUT',
    'SOFTWARE-IPD',
    'SVT',
    'IP-ICD-ANALOG',
    'IP-ICD-ASIC',
    'IP-ICD-DIGITAL',
    }
        
    def __init__(self, xmlString, doVerifyEveryTemplatePresent=False):
        super(Verifier, self).__init__(None)
        
        self._doVerifyEveryTemplatePresent = doVerifyEveryTemplatePresent
        self._itemIdNames = []
        self._sharedItems = dict()
        try:
            self._manifest = Manifest('ipNameValue', cell_name='cellNameValue', templatesetString=xmlString)        
        except ParseError as e:
            # Do CheckerBase.__init__() with a trivial (but error-free) Manifest
            super(Verifier, self).__init__(None)
            self._addError("The deliverable templateset has parsing errors: {}".format(e.message))
            return
        
        self._rootElement = self._manifest.rootElement
        self._actualAliasNames = self._getIdsOfElementsWithinRoot('alias')
        self._actualTemplateNames = self._getIdsOfElementsWithinRoot('template')
        self._actualAliasAndTemplateNames = self._actualAliasNames + self._actualTemplateNames
        self._actualAliasAndTemplateNames.sort()
        
        self.check(False)
        
    def __str__(self):
        '''English language name of this check.'''
        return "Templateset XML verifier"

    def _getIdsOfElementsWithinRoot(self, elementName):
        '''Within the root element, return a sorted list of ''' \
        '''the id attribute for all elements named elementName.'''
        ids = []
        self._rootElement, 'Member variable _rootElement is set before this method is called'
        for element in self._rootElement.findall(elementName):
            if not self._isIdAttrDefined(element):
                # Allow only valid ids.  An invalid id is illegal, but we'll verify that later.
                continue
            id_ = element.attrib['id']
            if id_ == "EMPTY":
                logging.warn("Warning: The EMPTY place holder deliverable '<{}>' id is present. \
                      This suggests that the deliverable specification is incomplete.".
                        format(elementName))
                continue
            ids.append(id_)
        ids.sort()
        return ids
    
    def _check(self):
        '''Verify the templateset.'''
        if not self._isVerifyRoot():
            return
        self._verifyUnique()
        self._verifyNamesLegal()
        self._verifyAliases()
        self._verifyTemplates()
    
    def _verifySuccessors(self):
        '''Verify the contents of the `<successor>` elements.'''
        actualSuccessorNames = self._getIdsOfElementsWithinRoot('successor')
        self._verifyListElementsUnique(actualSuccessorNames, "deliverable '<successor>'")

        if self._doVerifyEveryTemplatePresent:
            actualSuccessorNames = self._getIdsOfElementsWithinRoot('successor')
            self._verifyListsEquivalent(actualSuccessorNames, 
                                        self.allDeliverableNames, 
                                        "deliverable '<successor>'")

        for successor in self._rootElement.findall('successor'):
            self._verifySuccessor(successor)

    def _isVerifyRoot(self):
        '''Verify the root element.  ''' \
        '''Actually, this should probably be left to XML schema validation.'''
        expected = 'templateset'
        actual = self._rootElement.tag
        if actual != expected:
            self._addError("The root XML element name is '{}', but it should be '{}'.".
                                format(actual, expected))
            return False
        return True

    def _verifyUnique(self):
        '''Verify that the `<alias>` and `<template>` elements all have unique names.'''
        self._verifyListElementsUnique(self._actualAliasAndTemplateNames, 
                                       "deliverable '<alias> and/or <template>'")

    def _verifyNamesLegal(self):
        '''Verify that the `<alias>` and `<template>` elements id's are all legal.
        
        Per Jakob Frickelton in ICManage incident #89592:
        
            The library type name is 32 characters maximum and can have case,
            space and symbols, but you would do yourself a favor if you
            constrained it to [a-zA-z0-9_-].
            
        We will allow only capitals, numbers, and _.  The name must start with a letter.
        '''
        aliasAndDeliverableNameRe = r'^[A-Z][A-Z0-9_]*$'
        aliasAndDeliverableNameMaxLength = 32
        
        isLegalName =  re.compile(aliasAndDeliverableNameRe)
        for name in self._actualAliasAndTemplateNames:
            if len(name) > aliasAndDeliverableNameMaxLength:
                self._addError("Alias and/or deliverable name '{}' is illegal "
                               "because it contains more than {} characters.".format(
                                    name,
                                    aliasAndDeliverableNameMaxLength))
            if not isLegalName.search(name):
                self._addError("Alias and/or deliverable name '{}' is illegal "
                               "because it does not match '{}'.".format(
                                    name,
                                    aliasAndDeliverableNameRe))

    def _verifyAliases(self):
        '''Verify the contents of all the `<alias>' elements.'''
        if self._doVerifyEveryTemplatePresent:
            self._verifyListsEquivalent(self._actualAliasNames, 
                                        self.allAliasNames, 
                                        "deliverable '<alias>'")

        for alias in self._rootElement.findall('alias'):
            self._verifyAlias(alias)
            
    def _verifyAlias(self, alias):
        '''Verify the specified `<alias>` element.'''
        if not self._isIdAttrDefined(alias):
            self._addError("There is a deliverable '<alias>' "
                           "whose id attribute is undefined or is empty.")

        # Verify the <member> deliverable item(s)
        aliasName = alias.get('id')
        for member in alias.findall('member'):
            memberName = member.text.strip()
            if memberName not in self._actualAliasAndTemplateNames:
                self._addError("In alias '{}', '<member>' '{}' is not a "
                               "defined '<alias>' nor '<template>'.".format(aliasName, 
                                                                            memberName))
    
    def _verifyTemplates(self):
        '''Verify the contents of all the `<template>' elements.'''
        if self._doVerifyEveryTemplatePresent:
            self._verifyListsEquivalent(self._actualTemplateNames, 
                                        self.allDeliverableNames, 
                                        "deliverable '<template>'")

        isTemplateFound = False
        for template in self._rootElement.findall('template'):
            isTemplateFound = True
            self._itemIdNames = []
            self._verifyTemplate(template)
    
        if not isTemplateFound:
            self._addError("The templateset contains no deliverable templates.")
            
    def _verifyListElementsUnique(self, nameList, nameForMessage):
        '''Report the names in nameList that are not unique.
        nameForMessage is the name of the list.'''
        seenNames = set()
        for name in nameList:
            if name in seenNames:
                self._addError("The {} name '{}' is not unique.".format(nameForMessage, 
                                                                        name))
            else:
                seenNames.add(name)

    def _verifyListsEquivalent(self, actual, expected, nameForMessage):
        '''
        Report on the differences between the lists.  nameForMessage is the name of the list.
        From http://stackoverflow.com/questions/3462143/get-difference-between-two-lists
        '''
        s = set(expected)
        extraInActual = [x for x in actual if x not in s]
        s = set(actual)
        missingInActual = [x for x in expected if x not in s]
        if missingInActual:
            self._addError("All {} are not defined.  These are missing: {}".format(
                                nameForMessage, missingInActual))
        if extraInActual:
            self._addError("Extra, unknown {} present: {}".format(
                                nameForMessage, extraInActual))
        
    def _verifyTemplate(self, template):
        '''Verify the specified `<template>` element.'''
        if not self._isIdAttrDefined(template):
            self._addError("There is a deliverable '<template>' "
                           "whose id attribute is undefined or is empty.")
            
        self._verifyCaseId(template)
        self._verifyDescription(template)
        self._verifyProducer(template)
        self._verifyConsumer(template)
        self._verifyPattern(template)
        self._verifyFilelist(template)
        self._verifyOpenAccess(template)
        self._verifyMilkyway(template)
    
    def _verifyCaseId(self, template):
        '''Verify the `<template caseid>` attribute of the specified template element.'''
        deliverableName = template.get('id')
        caseid = template.get('caseid')
        if caseid is None:
            self._addError("In deliverable '{}', the <template caseid> "
                           "case number attribute is missing.".format(deliverableName))
            return
        try:
            int(caseid)
        except ValueError:
            self._addError("In deliverable '{}', the <template caseid=\"{}\"> case "
                           "number attribute is not a decimal integer."
                           "".format(deliverableName, caseid))
   
    def _verifyDescription(self, template):
        '''Verify the `<description>` element within the specified template element.'''
        deliverableName = template.get('id')
        description = template.find('description')
        if description is None:
            self._addError("In deliverable '{}', '<description>' is missing.".
                                format(deliverableName))
        elif description.text is None:
            self._addError("In deliverable '{}', '<description>' is empty.".
                              format(deliverableName))
        elif not description.text.strip():
            self._addError("In deliverable '{}', '<description>' contains only white space.".
                               format(deliverableName))
        elif len(template.findall('description')) != 1:
            self._addError("In deliverable '{}', there are multiple '<description>' elements.  "
                           "Exactly one is required.".format(deliverableName))
        else:
            pass
    

    def _verifyProducer(self, template):
        '''Verify the `<producer>` elements within the specified template element.
        '''
        self._verifyProducerOrConsumer(template, 'consumer')
    
    def _verifyConsumer(self, template):
        '''Verify the <consumer>` elements within the specified template element.
        '''
        self._verifyProducerOrConsumer(template, 'producer')
    
    def _verifyProducerOrConsumer(self, template, tagName):
        '''Verify the `<producer>` or `<consumer>` elements within the specified
        template element.  Argument `tagName` is either 'producer' or 'consumer'.
        '''
        deliverableName = template.get('id')
        ids = set()
        for item in template.iterfind(tagName):
            id_ = item.get('id')
            if id_ is None:
                self._addError("In deliverable '{}', there is a '<{}>' with no 'id' attribute."
                               "".format(deliverableName, tagName))
            elif id_ not in self.allTeamNames:
                self._addError("In deliverable '{}', '<{} id=\"{}\">' has an illegal team name."
                               "".format(deliverableName, tagName, id_))
            if id_ in ids:
                self._addError("In deliverable '{}', there are duplicate '<{} id=\"{}\">'."
                               "".format(deliverableName, tagName, id_))
            ids.add(id_)
                    
    def _verifyOpenAccess(self, template):
        '''Verify the `<openaccess>` deliverable item(s) within the specified template element.'''
        self._verifyDb(template, 'openaccess', 'OpenAccess', OpenAccess.viewTypeNames)

    def _verifyMilkyway(self, template):
        '''Verify the <milkyway> deliverable item(s).'''
        self._verifyDb(template, 'milkyway', 'Milkyway', Milkyway.viewTypeNames)

    def _verifyDb(self, template, tagName, dbName, legalViewTypeNames):
        '''Verify the specified deliverable item(s) within the specified EDA
        database (such as OpenAccess or Milkyway) template element.  Argument
        `dbName` is just used in messages.
        '''
        deliverableName = template.get('id')
        for element in template.findall(tagName):
            
            self._verifyDeliverableItemCommon(element, deliverableName,
                                              '<' + tagName + '>')

            # The file path to verify for uniqueness
            filePathName = ""

            # Verify <libpath> element
            libPath = element.find('libpath')
            if libPath is None:
                self._addError("In deliverable '{}', {} library path <libpath> is missing.".
                                   format(deliverableName, dbName))
            else:
                libPathText = libPath.text.strip()
                if not libPathText:
                    self._addError("In deliverable '{}', {} library path <libpath> is empty.".
                                      format(deliverableName, dbName))
                else:
                    filePathName = libPathText

            # Verify <lib> element
            lib = element.find('lib')
            if lib is None:
                self._addError("In deliverable '{}', {} library name <lib> is missing.".
                                  format(deliverableName, dbName))
            else:
                libText = lib.text.strip()
                if not libText:
                    self._addError("In deliverable '{}', {} library name <lib> is empty.".
                                      format(deliverableName, dbName))
                elif tagName == 'milkyway' and lib.text.strip() != os.path.basename(libPathText):
                    self._addError("In deliverable '{}', {} library name '{}' does "
                                   "not match the library path '{}'."
                                   "".format(deliverableName, dbName, libText, libPathText))
                
            # Verify <cell> element.  It is optional.
            isCellNamePresent = False
            cell = element.find('cell')
            if cell is not None:
                cellText = cell.text.strip()
                if not cellText:
                    self._addError("In deliverable '{}', {} cell name <cell> is empty.".
                                      format(deliverableName, dbName))
                else:
                    isCellNamePresent = True
                    filePathName = os.path.join(filePathName, cellText)
            
            # Verify <view> element
            isViewNamePresent = False 
            view = element.find('view')
            if view is not None:
                viewText = view.text.strip()
                if not viewText:
                    self._addError("In deliverable '{}', {} view name <view> is empty.".
                                      format(deliverableName, dbName))
                else:
                    isViewNamePresent = True
                    if isCellNamePresent:
                        filePathName = os.path.join(filePathName, viewText)
                        
            if isViewNamePresent:
                viewType = view.get('viewtype', '')
                if viewType:
                    if viewType not in legalViewTypeNames:
                        self._addError("In deliverable '{}', '<view viewtype='{}'>' is "
                                       "not a valid {} view type.".
                                            format(deliverableName, viewType, dbName))    
                elif tagName != 'milkyway':
                    # Milkyway does not really pay attention to view types like OpenAccess does
                    self._addError("In deliverable '{}', the {} '<view viewtype>' "
                                   "attribute is not specified.".format(deliverableName, 
                                                                        dbName))
            
            # _verifyDeliverableItemUniqueness() gets the file path from an Element,
            # so make a little fake element just to pass in the file path.
            filePathElement = Element('filepath')
            filePathElement.text = filePathName
            self._verifyDeliverableItemUniqueness(filePathElement, element, deliverableName)

    def _verifyPattern(self, template):
        '''Verify the <pattern> deliverable item(s).'''
        deliverableName = template.get('id')
        for element in template.findall('pattern'):
            
            self._verifyDeliverableItemCommon(element, deliverableName, '<pattern>')
                
            id_ = element.get('id')
            if (not element.text) or (not element.text.strip()):
                self._addError("In deliverable '{}', '<pattern id='{}'>' is empty.".
                                   format(deliverableName, id_))
                # Nothing else to verify about an empty pattern
                continue
            self._verifyDeliverableItemUniqueness(element, element, deliverableName)
            self._verifyWildCards(element.text.strip(), deliverableName)

    def _verifyWildCards(self, text, deliverableName):
        '''Verify the usage of wild cards in the <pattern> deliverable item text.'''
        if (text.count('*') or text.count('?')) and text.count('...'):
            self._addError("In deliverable '{}', '<pattern> {}' combines "
                           "glob wild cards '*' or '?' with "
                           "Perforce '...'.  This is unsupported.".format(deliverableName, 
                                                                          text))
        (startDir, startFileName) = os.path.split(text)
        if startDir.count('...'):
            self._addError("In deliverable '{}', '<pattern> {}' "
                           "contains '...' wild card in the directory.  '...' is "
                           "only supported at the beginning of the file name.".
                               format(deliverableName, text))
        if startFileName.count('...') > 1:
            self._addError("In deliverable '{}', '<pattern> {}' contains multiple '...' "
                           "wild cards in the file name.  '...' is supported only at the "
                           "beginning of the file name.".format(deliverableName, text))
        if (startFileName.count('...') == 1) and not startFileName.startswith('...'):
            self._addError("In deliverable '{}', '<pattern> {}' contains "
                           "a '...' not at the beginning of the file name.  '...' is "
                           "supported only at the beginning of the file name.".
                                format(deliverableName, text))
        
    def _verifyFilelist(self, template):
        '''Verify the <filelist> deliverable item(s).'''
        deliverableName = template.get('id')
        for element in template.findall('filelist'):
            
            self._verifyDeliverableItemCommon(element, deliverableName, '<filelist>')
                
            id_ = element.get('id')
            if (not element.text) or (not element.text.strip()):
                self._addError("In deliverable '{}', '<filelist id='{}'>' is empty.".
                                   format(deliverableName, id_))
            else:
                self._verifyDeliverableItemUniqueness(element, element, deliverableName)


    def _verifyDeliverableItemCommon(self, element, deliverableName, itemName):
        '''Verify the common aspects of elements derived from dmx.dmlib.templateset.itembase,
        like `<pattern>`, `<filelist>`, `<milkyway>` and so on.'''
        # Verify id attribute is defined and unique within a deliverable
        if not self._isIdAttrDefined(element):
            self._addError("In deliverable '{}', item '{}', the "
                           "id attribute is not defined or is empty.".
                                format(deliverableName, itemName))
        else:
            id_ = element.get('id')
            if id_ in self._itemIdNames:
                self._addError("In deliverable '{}', the '{}' id "
                               "attribute '{}' is not unique.".format(deliverableName, 
                                                                      itemName, 
                                                                      id_))
            else:
                self._itemIdNames.append(id_) 

    def _verifyDeliverableItemUniqueness(self, 
                                         elementContainingText, 
                                         elementWithSharedAttr, 
                                         deliverableName):
        '''Check that the text of the elementContainingText obeys the
        uniqueness requirements.
        '''
        text = elementContainingText.text
        if not text:
            # Empty element text is illegal, but will be verified elsewhere
            return
        text = text.strip()
        sharedName = elementWithSharedAttr.get('shared')
        if sharedName:
            nameForMessage = "a shared name within deliverable '{}'".format(deliverableName)
            self._verifyDeliverableDefined(sharedName, nameForMessage)
        otherDeliverableName = self._sharedItems.get(text, None)
        if otherDeliverableName is None:
            # text is unique, so no problem; add it
            if sharedName:
                self._sharedItems[text] = sharedName
            else:
                # If the shared attribute is undefined, use the deliverable name as the shared name
                self._sharedItems[text] = deliverableName
            return
        if deliverableName == otherDeliverableName:
            # A deliverable implicitly shares with itself; no problem
            return
        # The deliverable item text is not unique.  Verify that it is properly shared.
        if not sharedName:
            self._addError("Item '{}' appears in both deliverables '{}' and '{}', "
                           "but the shared attribute is not defined or is empty "
                           "in '<{}>' within deliverable '{}'.".
                                format(text, 
                                       deliverableName, 
                                       otherDeliverableName, 
                                       elementWithSharedAttr.tag, 
                                       deliverableName))
        elif sharedName != otherDeliverableName:
            self._addError("Item '{}' appears in both deliverables '{}' and '{}', "
                           "but the shared attribute '{}' in '<{}>' within "
                           "deliverable '{}' does not match.".
                               format(text, 
                                      deliverableName, 
                                      otherDeliverableName, 
                                      sharedName, 
                                      elementWithSharedAttr.tag, 
                                      deliverableName))
            
    def _verifyDeliverableDefined(self, name, whatItWasUsedAs):
        '''Verify that the specified deliverable is defined.
        `whatItWasUsedAs` appears in messages to explain how `name` is used.
        '''
        if (not name) or (name not in self._actualTemplateNames):
            self._addError("Deliverable name '{}' used as {} is not defined.".
                               format(name, whatItWasUsedAs))
       
    def _verifySuccessor(self, successor):
        '''Verify the specified `<successor>` element.'''
        if not self._isIdAttrDefined(successor):
            self._addError("There is a deliverable '<successor>' "
                           "whose id attribute is undefined or is empty.")
            predecessorDescription = "a predecessor"
        else:
            predecessorDescription = "a predecessor of '{}'".format(successor.get('id'))

        for predecessor in successor.findall('predecessor'):
            self._verifyDeliverableDefined(predecessor.text.strip(), 
                                           predecessorDescription)

    def _isIdAttrDefined(self, element):
        '''Determine whether the id attribute is defined on the specified element.'''
        id_ = element.get('id')
        return (id_ is not None) and id_
                    
        
if __name__ == "__main__":
    # Running Verifier_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod(verbose=2)

