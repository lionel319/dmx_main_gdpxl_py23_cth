#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/Graph.py#1 $

"""
Create a `Graphviz <http://graphviz.org>`_ graph of a templateset or manifestset
predecessor/successor relationships.  Render it as a graphics format file or
as a GraphViz dot graph description language file.

Command Line Interface
=======================
`Graph` is exposed as a command line application as the :doc:`graph`.
"""

import os
import datetime
import subprocess
import logging

from dmx.dmlib.dmError import dmError

class Graph(object):
    """
    Instantiate a DM Graph object to represent and draw predecessor/successor
    relationships in the specified templateset or manifestset.
    """

    def __init__(self, parser):
        self._bomParser = parser
        self._dotList = []
        # self._g = None
        
    @property
    def dot(self):
        '''The dot language string describing the current graph.'''
        return '\n'.join(self._dotList)
        
    @property
    def dotList(self):
        '''A list of lines in the dot language string describing the current graph.

        This property is primarily for testing.
        '''
        return list(self._dotList)
        
    def createPredecessorGraph(self, deliverableAndAliasNames, direction='TB'):
        '''Create a graph showing the predecessor/successor relationships
        between the named deliverables.

        The optional argument `direction` determines the drawing direction:
        
        * "TB" Vertical, starting at the top
        * "LR" Horizontal, starting from the left
        * "BT" Vertical, starting at the bottom
        * "RL" Horizontal, starting from the right
        
        Use the `render()` method to render the graph as a file in a graphical
        format.
        '''
        self._dotList = []        
        self._dotList.append('digraph predecessor {')
        self._dotList.append('    node [fontname=Courier, style=filled, fillcolor=white];')
        self._dotList.append('    graph [rankdir={},'.format(direction))
        self._dotList.append('        label="\\n{} Alias Flow Diagram\\n    {}  Altera Corporation Proprietary and Confidential",'.format(','.join(deliverableAndAliasNames), datetime.date.today()))
        self._dotList.append('        labelloc=bottom,')
        self._dotList.append('        labeljust=center ];')
        
        nodeNames = self._bomParser.getDeliverableAliases(deliverableAndAliasNames)
        for nodeName in nodeNames:
            self._dotList.append('    {};'.format(nodeName))
            for predecessorName in self._bomParser.getDeliverablePredecessor(nodeName):
                if predecessorName in nodeNames:
                    self._dotList.append('    {} -> {};'.format(predecessorName, nodeName))
        self._dotList.append('}')
            
    def createFileHierGraph(self, deliverableAndAliasNames, direction='TB'):
        '''Create a graph showing the hierarchy of files in the specified
        deliverables.
        
        The optional argument `direction` determines the drawing direction:
        
        * "TB" Vertical, starting at the top
        * "LR" Horizontal, starting from the left
        * "BT" Vertical, starting at the bottom
        * "RL" Horizontal, starting from the right
        
        Use the `render()` method to render the graph as a file in a graphical
        format.
        '''
        self._dotList = []
        self._dotList.append('strict digraph fileHier {')
        self._dotList.append('    node [shape=folder, fillcolor=gold fontname=Courier, style=filled];')
        self._dotList.append('    graph [rankdir={},'.format(direction))
        self._dotList.append('        label="\\n{} Alias File Hierarchy\\n    {}  Altera Corporation Proprietary and Confidential",'.format(','.join(deliverableAndAliasNames), datetime.date.today()))
        self._dotList.append('        labelloc=bottom,')
        self._dotList.append('        labeljust=center ];')
        
        deliverableNames = self._bomParser.getDeliverableAliases(deliverableAndAliasNames)
        for deliverableName in deliverableNames:
            self._createPatternFileHier(deliverableName)
            self._createFilelistFileHier(deliverableName)
            self._createOpenAccessFileHier(deliverableName)
            self._createMilkywayFileHier(deliverableName)
        self._dotList.append('}')

    def _createPatternFileHier(self, deliverableName):
        '''Add the file hierarchy for any `<pattern>` in the specified deliverable.'''
        patterns = self._bomParser.getDeliverablePattern(deliverableName)
        for pattern in patterns:
            self._createFile(pattern, deliverableName, 'white')

    def _createFilelistFileHier(self, deliverableName):
        '''Add the file hierarchy for any `<filelist>` in the specified deliverable.'''
        filelists = self._bomParser.getDeliverableFilelist(deliverableName)
        for filelist in filelists:
            self._createFile(filelist, deliverableName, 'grey')

    def _createOpenAccessFileHier(self, deliverableName):
        '''Add the file hierarchy for any `<openaccess>` in the specified deliverable.'''
        dbs = self._bomParser.getDeliverableOpenAccess(deliverableName)
        for db in dbs:
            self._createFile(db[0], deliverableName, 'red', fileShape='folder')

    def _createMilkywayFileHier(self, deliverableName):
        '''Add the file hierarchy for any `<milkyway>` in the specified deliverable.'''
        dbs = self._bomParser.getDeliverableMilkyway(deliverableName)
        for db in dbs:
            self._createFile(db[0], deliverableName, 'orchid', fileShape='folder')

    def _createFile(self, path, deliverableName, fileColor, fileShape='box'):
        components = path.split(os.sep)
        if not components:
            logging.warn ("Warning: Deliverable '{}' contains an empty path.".
                             format(deliverableName))
            return
        previousComponentPath = ''
        componentPath = ''
        for component in components:
            componentPath = os.path.join(componentPath, component)
            self._dotList.append('    "{}"[label="{}"];'.format(componentPath, component))
            if previousComponentPath:
                self._dotList.append('    "{}" -> "{}";'.format(previousComponentPath, componentPath))
            previousComponentPath = componentPath
        # Set attributes on the file
        assert previousComponentPath == path, "previousComponentPath is the file name"
        self._dotList.append('    "{}"[label="{}\\n{}" shape={}, fontname=Courier, '
                             'style=filled, fillcolor={}];'.format(path,
                                                                   components[-1],
                                                                   deliverableName,
                                                                   fileShape,
                                                                   fileColor))

    def render(self, format_, fileName):
        """
        Render the current graph as a graphics format file.  Any of the
        `graphics output formats supported by Graphviz <http://graphviz.org/content/output-formats>`_
        are supported.
        
        If `format_` is 'dot', output the raw GraphViz dot graph description
        language.
        """
        if format_ == 'dot':
            with open(fileName, 'w') as f:
                f.write(self.dot)
            return
        
        command = "dot -T{} -o{} <<+++\n{}\n+++\n".format(format_, fileName, self.dot)
        status = subprocess.call(
            command,
            shell=True)
        if status != 0:
            raise dmError("The dot application exited with error status '{}'.".format(status))
        # requires gv, which is not installed at Altera
        # gv.render(self._g, format_, fileName)
