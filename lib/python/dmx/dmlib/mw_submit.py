#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/mw_submit.py#1 $

"""
See the `Milkyway DM Flow 
<http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/MilkywayDMFlow>`_
article for documentation on this class.

*Warning to those who are copying P4Python code from this class:*
When using IC Manage, you must not use `P4.run_sync()` or `P4.run('sync')`.

This class is based on work by Tara Clark.
"""

import shutil
import os
import time
import logging

from P4 import P4, P4Exception
from dmx.dmlib.CheckerBase import CheckerBase
from dmx.dmlib.dmError import dmError
from dmx.dmlib.templateset.milkyway import Milkyway
from dmx.dmlib.deliverables.utils.MilkywayUtils import runICCompiler
from dmx.dmlib.deliverables.utils.Arc import checkAccessibleToArc
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace
from dmx.dmlib.Manifest import Manifest


class MwSubmit(object):
    '''Create a Milkyway release library submitter for IC Manage.

    The `ipName` argument is the name of the IP you will be submitting.

    The `deliverableName` is the name of the deliverable that contains the
    Milkyway data to be submitted.

    The `itemName` is the name of Milkyway item within the deliverable.  This is
    necessary only when the deliverable contains multiple Milkyway databases and
    you need to identify which to submit.  The default is `mwLib`, which is the
    default item name for Milkyway deliverables in the templateset.

    The `workspacePath` is the path to the IC Manage workspace containing the
    specified IP.  The default is the path to the workspace that contains the
    current working directory, so ordinarily you need not specify this.

    The `workingLibraryPath` is the path to the Milkyway working library.
    The default is the working library in the ICC deliverable.
    '''    
    tclScriptFileName = 'mw_submit.run.tcl'

    def __init__(self, 
                 ipName, 
                 workingLibraryPath, 
                 deliverableName,
                 itemName=Milkyway.defaultId, 
                 workspacePath=None):
        self._ipName = ipName
        self._workingLibraryPath = os.path.abspath(workingLibraryPath)
        self._deliverableName = deliverableName
        self._itemName = itemName
        self._workspace = ICManageWorkspace(workspacePath, ipName)
        
        if self._deliverableName in ('FCMW', 'FCHIERFLRPLN'):
            # FCI, the floorplanner tool used in NightFury, created the top level
            # Milkyway library with multiple CEL views.  The way that mwsubmit
            # handled this is a bit obscure, so I will leave in the code and
            # test just in case it is needed again.
            self._cellNames = set(['*'])
            self._viewNames = ('CEL')
        else:
            self._cellNames = self._workspace.getCellNamesForIPName(ipName)
            self._viewNames = ('CEL', 'FRAM', 'FILL', 'ILM')
        
        self._manifest = Manifest(ipName, ipName, deliverableName)
        
        release = self._manifest.getMilkyway(deliverableName, itemName)
        self._releaseLibraryPathRelative = Manifest.getLibraryPath(release)
        self._releaseLibraryPath = os.path.join(self._workspace.path,
                                                self._releaseLibraryPathRelative)
            
        self._iccWorkingDirectory = os.path.dirname(self._releaseLibraryPath)

        self._description = None

        # Properties have been defined for the following instance variables.
        # Always use the methods or properties exclusively, even within this
        # class.
        self._p4AccessOnlyViaProperty = None
        self._p4ChangeAccessOnlyViaProperty = None
        
    def submit(self, description, doSubmit=True, externalReleaseLibraryCreator=None):
        '''Create the release library from the working library and submit it to
        the depot.
        
        The `description` argument is used as the change list submission message.
        
        If the `doSubmit` argument is false, the  Perforce submit command will
        not be ussued.  This gives you a chance to inspect the submission with
        ``icmp4 opened``.  Then, ``icmp4 submit`` if you are satisfied, or
        ``icmp4 revert`` if you disapprove.

        
        The `externalReleaseLibraryCreator` argument is solely for testing.  It
        allows the tests to substitute their own sick and twisted libraries in
        order to torture test the Perforce operations.
        '''
        if not description:
            raise dmError("The submission description message must not be empty")
        self._description = description
        self._checkInputData()
        try:
            self._removeExistingReleaseLibrary()
            if externalReleaseLibraryCreator is None:
                self._createReleaseLibrary()
            else:
                externalReleaseLibraryCreator(self._releaseLibraryPath)
            if doSubmit:
                self._submitReleaseLibrary()
            else:
                logging.info("Warning: Not submitting to Perforce per user request.")
        except P4Exception as e:
            raise dmError('Perforce failed: {}'.format(e.value))
        finally:
            self._disconnectP4()
        self._printFinalReport()
            
    @property
    def p4(self):
        '''The P4 Python instance.
        '''
        if self._p4AccessOnlyViaProperty is None:
            self._p4AccessOnlyViaProperty = P4()
            self._p4AccessOnlyViaProperty.user = os.environ['LOGNAME']
            self._p4AccessOnlyViaProperty.client = self._workspace.getInfo('Client name')
            self._p4AccessOnlyViaProperty.protocol("app", "icmanage")
            logging.info("Connecting to Perforce")
            self._p4AccessOnlyViaProperty.connect()
            #self._p4AccessOnlyViaProperty.run_login()
        return self._p4AccessOnlyViaProperty
    
    def _checkInputData(self):
        '''Check that the input data is ready.  Raise an exception if not.
        
        *If you add to this, update the documentation in `../bin/mwsubmit.py`.*
        Search for "prerequisites".
        '''
        logging.info("Checking the readability of the working "
                     "library and writability of the release library")
        checkAccessibleToArc(self._workspace.path, "IC Manage workspace")
        if not CheckerBase.isMilkywayLibrary(self._workingLibraryPath):
            raise dmError("Working library '{}' is not a Milkyway library."
                          "".format(self._workingLibraryPath))
        if not os.access(self._iccWorkingDirectory, os.W_OK): # | os.X_OK
            raise dmError("Files must be written to '{}', but it is not writable."
                          "".format(self._iccWorkingDirectory))
        if (os.path.exists(self._releaseLibraryPath) and
                    not CheckerBase.isMilkywayLibrary(self._releaseLibraryPath)):
            raise dmError(
                "The pre-existing release library '{}'\n"
                "    is not a Milkyway library.  "
                "Please either move or delete this suspicious file."
                "".format(self._releaseLibraryPath))
        opened = self.p4.run_opened(os.path.join(self._releaseLibraryPath, '...'))
        if opened:
            raise dmError(
                "Perforce has files open in the pre-existing release library '{}'.\n"
                "    Please either submit or revert these files with:\n"
                "        icmp4 submit {}/...\n"
                "    or\n"
                "        icmp4 revert {}/..."
                "".format(self._releaseLibraryPath,
                          self._releaseLibraryPath,
                          self._releaseLibraryPath))
        syncs = []
        try:
            syncs = self.p4.run_sync('-n')
        except P4Exception as e:
            # e.warnings == ['File(s) up-to-date.'] means everything is good
            if e.errors or e.warnings != ['File(s) up-to-date.']:
                raise dmError("Your pre-existing release library '{}' cannot be deleted\n"
                              "    because {}".format(e.value))
        if syncs:
            messages = ["Your pre-existing release library '{}' cannot be deleted".
                            format(self._releaseLibraryPath),
                        "    because the following files are out of "
                        "date with respect to the Perforce depot:"]
            for sync in syncs:
                messages.append("        {}".format(sync['clientFile']))
            messages.append("    Please sync your release library using the command:\n")
            messages.append("        icmp4 sync {}/...".format(self._releaseLibraryPath))
            raise dmError('\n'.join(messages))
                         
    def _removeExistingReleaseLibrary(self):
        '''Remove any existing release library from the Perforce depot and the
        workspace.
        '''
        logging.info("Deleting the release library from the Perforce depot")
        assert self._description, "The description is required"
        try:
            status = self.p4.run_delete(os.path.join(self._releaseLibraryPath, '...'))
        except P4Exception as e:
            if e.errors:
                raise dmError('Failed to delete the release '
                              'library from the Perforce depot\n'
                              '    because Perforce failed: {}'.format(e.value))
            logging.info ('Info: {}'
                  '    This is not unusual if you are running mwsubmit '
                  'for the first time, when the Perforce depot contains nothing to delete.'
                  ''.format(e.value))
            # There is an apparent race condition when a new IP is submitted
            # for the first time.
            time.sleep(5)
            if os.path.exists(self._releaseLibraryPath):
                logging.info("Deleting the remaining vestiges of "
                             "the release library from the workspace")
                shutil.rmtree(self._releaseLibraryPath)
            return

        if status:
            errorMessages = [element for element in status 
                                if isinstance(element, basestring)]
            if errorMessages:
                raise dmError('Failed to delete the release library '
                              'from the Perforce depot because:\n'
                              '    {}'.format('\n    '.join(errorMessages)))
            
        description = "Delete in preparation for {}".format(self._description)
        openSpecs = self.p4.run_opened(os.path.join(self._releaseLibraryPath, '...'))
        if openSpecs:
            self.p4.run_submit('-d', 
                               description, 
                               os.path.join(self._releaseLibraryPath, '...'))

        if os.path.exists(self._releaseLibraryPath):
            shutil.rmtree(self._releaseLibraryPath)
        
    def _createReleaseLibrary(self):
        '''Copy the Milkyway cells from the working library to the release
        library by creating a script utilizing the ../tcl/mw_submit.tcl package
        and running it in IC Compiler.
        '''
        tclScriptPath = os.path.join(self._iccWorkingDirectory, self.tclScriptFileName)
        self._createTclScript(tclScriptPath)
        # Use a relative path for the Tcl script here because an absolute path
        # can look different from the server farm.  For example, /nobackup/ vs.
        # /net/hostname/nobackup/.
        logging.info("Running IC Compiler to create a new "
                     "release library and copy the top cell(s) to it.")
        isSuccess = runICCompiler(self.tclScriptFileName,
                                  self._iccWorkingDirectory,
                                  'mw_submit',
                                  removeLockFileFromLibrary=self._releaseLibraryPath)
        if not isSuccess:
            logFileName = os.path.join(self._iccWorkingDirectory, 'mw_submit.log')
            raise dmError("ICC failed to create the release "
                          "library and copy from the working library.\n"
                          "    See the ICC log file '{}' for details.".
                                format(logFileName))
    

    def _createTclScript(self, tclScriptPath):
        '''Create the IC Compiler Tcl script to create the release library and
        copy cells to it utilizing ../tcl/mw_submit.tcl.
        '''
        dmRoot = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        mwSubmitScriptName = os.path.join(dmRoot, 'tcl', 'mw_submit.tcl')
        assert os.path.exists(mwSubmitScriptName), "../tcl/mw_submit.tcl exists"
        with open(tclScriptPath, 'w') as f:
            f.write('# Create a Milkyway release library. '
                    'Copy cells from a working library to the\n')
            f.write('# release library in preparation for submission to IC Manage.\n')
            f.write('# This script is automatically created by '
                    'Python module dmx.dmlib.mw_submit.\n')
            f.write('\n')
            f.write('source "{}"\n'.format(mwSubmitScriptName))
            f.write('::mw_submit::create_release_library \\\n')
            f.write('    {' +  self._workingLibraryPath        + '} \\\n')
            f.write('    {' +  self._releaseLibraryPath        + '} \\\n')
            f.write('    {' +  ' '.join(self._cellNames)       + '} \\\n')
            f.write('    {' +  ' '.join(self._viewNames) + '}\n')
            f.write('\n')
            f.write('exit\n')
        
    def _submitReleaseLibrary(self):
        '''Add the files in the release library and submit them to Perforce.
        Close the Perforce connection.
        '''
        assert self._description, "The description is required"
        logging.info("Adding release library files to Perforce:")
        for fileName in self._getFilesInReleaseLibrary():
            logging.info("    {}".format(fileName))
            self.p4.run_add(fileName)
        logging.info("Submitting the above release library files to Perforce")
        self.p4.run_submit('-d', self._description,
                           os.path.join(self._releaseLibraryPath, '...'))

    def _getFilesInReleaseLibrary(self):
        '''Get a list of files in the release library, with undesirable files
        like `.lock*` and `.nfs*` filtered out.
        '''
        filteredFileNames = []
        for (root, dirNames, fileNames) in os.walk(self._releaseLibraryPath):
            _ = dirNames
            for fileName in fileNames:
                baseName = os.path.basename(fileName)
                if baseName.startswith('.lock') or baseName.startswith('.nfs'):
                    continue
                filteredFileNames.append(os.path.join(root, fileName))
        return filteredFileNames
    
    def _printFinalReport(self):
        logging.info("")
        logging.info("Successfully submitted the Milkyway release library for:")
        logging.info("  Description      {}".format(self._description))
        logging.info("  Project          {}".format(self._workspace.projectName))
        logging.info("  IP               {}".format(self._workspace.ipName))
        logging.info("  Configuration    {}".format(self._workspace.configurationName))
        logging.info("  Deliverable      {}".format(self._deliverableName))
        logging.info("")
        logging.info("  Milkyway Library {} (within a workspace)".
                        format(self._releaseLibraryPathRelative))
        logging.info("  Milkyway Cell(s) {}".format(', '.join(self._cellNames)))
        logging.info("  Milkyway Views   {}".format(', '.join(self._viewNames)))
        logging.info("")
        logging.info("To access this, create a workspace "
                     "that includes the above configuration.")
        logging.info("Or, if you already have "
                     "an existing workspace, do 'icmp4 sync {}/...'."
                        "".format(self._releaseLibraryPathRelative))
        logging.info("")
        logging.info("If you want to open the Milkyway library or its "
                     "cells for write, make sure")
        logging.info("to do 'icmp4 edit {}/...'.".
                        format(self._releaseLibraryPathRelative))
        logging.info("")
        logging.info("For detailed instructions see:")
        logging.info("  http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/"
                        "ICManageTraining#MilkyWay_Integration") 
        logging.info("")

    def _disconnectP4(self):
        '''Disconnect from Perforce.'''
        if self._p4AccessOnlyViaProperty is None:
            # Nothing to do
            return
        logging.info("Disconnecting from Perforce")
        self.p4.disconnect()
        self._p4AccessOnlyViaProperty = None
        
        
if __name__ == "__main__":
    # Running mw_submit_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
