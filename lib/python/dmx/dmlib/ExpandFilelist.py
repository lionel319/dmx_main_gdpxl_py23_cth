#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ExpandFilelist.py#1 $

"""
ExpandFilelist adjusts the relative paths in filelists and concatenates them.

Beginning with NightFury 4, :py:class:`dmx.dmlib.gencompositefilelist` should be used
for RTL filelists.

Command Line Interface
=======================
`ExpandFilelist` is exposed as a command line application as the
:doc:`expandfilelist`.
"""

import os
import shutil # @UnusedImport pylint: disable=W0611

from dmx.dmlib.expandfilelist_base import ExpandFilelistBase
from dmx.dmlib.parsers import parseFilelist
from dmx.dmlib.Manifest import Manifest


class ExpandFilelist(ExpandFilelistBase):
    """
    Instantiate a filelist expander to expand the filelists for the specified
    deliverable, and put the result in file `outputFileName`.
    
    Relative paths in the input filelists will be adjusted to be relative to
    `workingDirName`.  If you specify '/', all paths will be made absolute
    paths. The default is the current working directory.
    
    When `deliverableName` is not 'RTL', discard VCS options that appear in the
    input filelists (VCS options begin with '-' or '+').
 
    Note that there is no restriction on the relationship between the paths
    `outputFileName` and `workingDirName`.
    
    If `otherDeliverableName` and `otherIPs` are specified:
    
    * The specified `otherDeliverableName` filelist will be used for the IPs in \
      the list `otherIPs`
    * The `deliverableName` filelist will be used for the remaining IPs 

    The `templatesetString` argument is chiefly for testing.
    
    `dmx.dmlib.ExpandFilelist` is exposed as a command line application as the
    :doc:`expandfilelist`.  See :doc:`expandfilelist` for more detailed
    documentation.
    """
    
    workingDirNameDefault = '.'
    
    def __init__(self,
                 deliverableName,
                 outputFileName,
                 workingDirName=workingDirNameDefault,
                 otherDeliverableName=None,
                 otherIPs=None,
                 itemName=None,
                 templatesetString=None):
        super(ExpandFilelist, self).__init__(deliverableName,
                                             outputFileName,
                                             itemName)
        self._workingDirName = workingDirName
        self._otherDeliverableName = otherDeliverableName
        self._otherIPs = otherIPs if otherIPs is not None else []
        self._templatesetString = templatesetString
        assert (self._otherDeliverableName is not None) ==  bool(self._otherIPs), \
               "Must specify either both or neither otherDeliverableName and otherIPs"
        

    def expandAll(self, ws):
        '''Expand all the filelists for the top IP in the specified
        ICManageWorkspace.

        Argument `ws` may be `ICManageWorkspace` or for testing,
        `ICManageWorkspaceMock`.
        '''
        libType = ws.getLibType(self._deliverableName)
        self._setMissingFileExplanation("\n"
                                        "    This could be because the corresponding IP includes a library\n"
                                        "    of type '{}' that is actually empty.".format(libType))
        ipNames = ws.getIpNames(libType) | set(self._otherIPs)
        self.expandIPs(ipNames, ws)            
        
    def expandIPs(self, ipNames, ws):
        '''Expand filelists for the specified IPs (but not their sub-IPs), with
        all relative paths adjusted to be relative to the `workingDirName`
        specified upon construction.
        
        If `workspacePath` is `None`, the IC Manage workspace that contains the
        current working directory will be used. 
        '''
        filelists = self._getFilelists(ipNames, ws.path)
        self.expandFilelists(filelists)            

    def expandFilelists(self, filelists):
        '''Expand the list of `filelists` into a single filelist that
        contains all files in all sub-IPs, with all relative paths
        adjusted to be relative to the `workingDirName` specified upon
        construction.
        
        Put the result in `outputFileName`.  If `outputFileName` is None, the
        output will be sent to the standard output.
        '''
        lines = []
        for filelist in filelists:
            self._checkFilelist(filelist)
            lines.append("// Start files from filelist '{}'".format(filelist))
            lines += self.getFilelistLines(filelist, self._workingDirName,
                                         self._doKeepVCSOptions)
            lines.append("// End files from filelist '{}'".format(filelist))
            lines.append("")

        linesWithDuplicatesCommented = self._commentOutDuplicates(lines)
        self._writeListToFile(linesWithDuplicatesCommented, self._outputFileName)
        
    def _getFilelists(self, ipNames, workspacePath):
        """Convert IP names to filelist paths."""
        filelists = []
        for ipName in ipNames:
            if ipName in self._otherIPs:
                deliverableNameForThisIP = self._otherDeliverableName
            else:
                deliverableNameForThisIP = self._deliverableName
            # TO_DO: Inefficient to re-read the templateset for each IP
            manifest = Manifest(ipName, templatesetString=self._templatesetString)
            filelist = manifest.getFilelist(deliverableNameForThisIP, self._itemName)
            filelists.append(os.path.join(workspacePath, filelist))
        return filelists

    @classmethod
    def getFilelistLines(cls, 
                         filelistFileName, 
                         workingDirName = '.', 
                         doKeepVCSOptions=True):
        """Return a list of the file names appearing in the specified filelist file.
        
        A filelist contains file paths, one per line.  Relative paths appearing
        in the filelist are relative to the directory containing the filelist.

        The file names will be further adjusted to be relative to the path
        specified in the optional `workingDirName` argument.  If `workingDirName
        is `/`, all paths will be made absolute paths.
        
        The file paths must name an ordinary file, without XML entity references or
        wildcard characters.
        
        A filelist can contain comments.  Comments start at,
        
        * `//` at the beginning of the line
        * `//` surrounded by white space

        Comments terminate at the end of the line.
        
        When the `doKeepVCSOptions` argument is True (the default), include
        lines that begin with '-' or '+' after removing leading white space.
        If `doKeepVCSOptions` is false, discard them.
        
        Use the `dmx.dmlib.parsers.parseFilelist()` function if you want to merely
        parse the filelist file without adjusting the paths.
        
        Usage example:
        
        >>> if os.path.exists('testip1'):
        ...     shutil.rmtree('testip1')
        >>> os.makedirs('testip1/rtl')
        >>>
        >>> f = open('testip1/rtl/ip1.rtl.filelist', 'w')
        >>> f.write('// RTL filelist containing three files\\n')
        >>> f.write('//Test comment at the beginning of the line followed by non-whitespace\\n')
        >>> f.write('one.v                    // Relative path\\n')
        >>> f.write('dir/two.v                // Relative path\\n')
        >>> f.write('/full/path/to/three.v    // Full path\\n')
        >>> f.close()
        >>>
        >>> ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist')
        ['testip1/rtl/one.v', 'testip1/rtl/dir/two.v', '/full/path/to/three.v']
        >>>
        >>> actual = ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist', '/')
        >>> expected = [os.path.join(os.getcwd(), 'testip1/rtl/one.v'), os.path.join(os.getcwd(), 'testip1/rtl/dir/two.v'), '/full/path/to/three.v']
        >>> actual == expected
        True
        >>> ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist', 'testip2/vcs')
        ['../../testip1/rtl/one.v', '../../testip1/rtl/dir/two.v', '/full/path/to/three.v']

        When the `doKeepVCSOptions` argument is True (the default), include
        lines that begin with '-' or '+'.  If `doKeepVCSOptions` is false, discard
        them:
                
        >>> f = open('testip1/rtl/ip1.rtl.filelist', 'w')
        >>> f.write('// Most VCS options are just passed through\\n')
        >>> f.write('-anyMinusOption\\n')
        >>> f.write('+anyPlusOption\\n')
        >>> f.write('// These VCS options have relative paths in their arguments adjusted\\n')
        >>> f.write('+incdir+.+relpath/to/four.v+/full/path/to/five.v\\n')
        >>> f.write('-f relpath/to//six.v\\n')
        >>> f.write('-y relpath/to/./seven.v\\n')
        >>> f.write('// For the -v VCS option, the -v is removed, and the argument is treated as an ordinary file\\n')
        >>> f.write('-v relpath/to/eight.v\\n')
        >>> f.write('plainFile.v\\n')
        >>> f.close()
        >>>
        >>> ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist')
        ['-anyMinusOption', '+anyPlusOption', '+incdir+testip1/rtl+testip1/rtl/relpath/to/four.v+/full/path/to/five.v', '-f testip1/rtl/relpath/to/six.v', '-y testip1/rtl/relpath/to/seven.v', 'testip1/rtl/relpath/to/eight.v', 'testip1/rtl/plainFile.v']
        >>>
        >>> ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist', doKeepVCSOptions=False)
        ['testip1/rtl/plainFile.v']

        `pop()` can be used to access members without harming the database:
        
        >>> s = ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist')
        >>> ignoredValue = s.pop()
        >>> ExpandFilelist.getFilelistLines('testip1/rtl/ip1.rtl.filelist')
        ['-anyMinusOption', '+anyPlusOption', '+incdir+testip1/rtl+testip1/rtl/relpath/to/four.v+/full/path/to/five.v', '-f testip1/rtl/relpath/to/six.v', '-y testip1/rtl/relpath/to/seven.v', 'testip1/rtl/relpath/to/eight.v', 'testip1/rtl/plainFile.v']
        
        Further tests are in :py:class:`dmx.dmlib.ExpandFilelist_test`.
        """
        filelistDirName = os.path.dirname(filelistFileName)
        outputLines = []
        for line in parseFilelist(filelistFileName, doKeepVCSOptions):
            outputLines.append(cls._adjustLinePath(line, filelistDirName, workingDirName))
        return outputLines

    @classmethod
    def _adjustLinePath(cls, line, filelistDirName, workingDirName):
        '''Adjust the input line according to special circumstances like +incdir+.'''
        if not line.startswith(('-', '+')):
            # line is just a path, not a vcs option
            return cls.adjustPath(line, filelistDirName, workingDirName)
        
        if line.startswith('-v'):
            # Remove the -v and process as an ordinary file
            tokens = line.split()
            return cls.adjustPath(tokens[1], filelistDirName, workingDirName)
        
        if line.startswith(('-f', '-y')):
            tokens = line.split()
            return "{} {}".format(tokens[0], cls.adjustPath(tokens[1], filelistDirName, workingDirName))

        if line.startswith('+incdir+'):
            adjustedIncDirs = []
            incDirs = line.split('+')
            for pathName in incDirs[2:]:
                adjustedIncDirs.append(cls.adjustPath(pathName, filelistDirName, workingDirName))
            return '+incdir+{}'.format('+'.join(adjustedIncDirs))
        
        # It's a VCS option that needs no adjustment
        return line
    
    @classmethod
    def adjustPath(cls, pathName, filelistDirName, workingDirName):
        '''`pathName` is a path relative to `filelistDirName`.  Adjust the
        `pathName` to be relative to `workingDirName`.

        >>> ExpandFilelist.adjustPath('one.v', 'testip1/rtl', '.')
        'testip1/rtl/one.v'
        >>> ExpandFilelist.adjustPath('one.v', 'testip1/rtl', 'testip2/vcs')
        '../../testip1/rtl/one.v'

        If `pathName` is an absolute path, return it unchanged:
        >>> ExpandFilelist.adjustPath('/full/path/to/three.v', 'testip1/rtl', '.')
        '/full/path/to/three.v'

        If `workingDirName` is '/', return an absolute path.

        >>> actual = ExpandFilelist.adjustPath('one.v', 'testip1/rtl', '/')
        >>> expected = os.path.join(os.getcwd(), 'testip1/rtl/one.v')
        >>> actual == expected
        True
        '''
        if os.path.isabs(pathName):
            return pathName
        fullPathName = os.path.join(filelistDirName, pathName)
        if workingDirName == '/':
            return os.path.abspath(fullPathName)
        # Adjust to a relative path
        return os.path.relpath(fullPathName, workingDirName)


# List of VCS options whose path should be adjusted
#+ad=<partition_filename>
#+applylearn[+<filename>]
## +csdf+precomp+dir+<directory>
#+incdir+<directory>
#+ntb_cache_dir=<path_name_to_directory>
#+ntb_load=path_name_to_libtb.so
#+optconfigfile+<filename>
#+putprotect+<target_dir>
#+vcdfile+<filename>
#+vera_load=<filename.vro>
#+vera_mload=<filename>
## +vpdfile+<filename>
#-E <program>
#-F <filename>
#-Mlib=<directory>
#-Mmakeprogram=<program>
#-P <pli.tab>
## -a <filename>
## -assert report[=<filename>]
#-cc <compiler>
#-cm_assert_hier <filename>
#-cm_constfile <filename>
## -cm_dir <directory_path_name>
#-cm_fsmcfg <filename>
#-cm_fsmresetfiltser <filename>
#-cm_hier <filename>
## -cm_log <filename>
## -cm_name <filename>
#-cm_tglfile <filename>
#-f <filename>
#-file filename
## -grw <filename>
#-i <filename>
## -k <filename> | off
## -l <filename>
#-l<name>
#-ld <linker>
#-ntb_incdir <directory_path>
#-ntb_opts print_deps[=<filename>]
#-ntb_sfname <filename>
## -o <name>
#-ova_cov_hier <filename>
#-ova_file <filename>
## -ova_name <name | /<pathname>/<name>
#-parameters <filename>
#-syslib <libs>
#-v <filename>
## -vcd <filename>
## -vcd2vpd <vcd_filename> <vcdplus_filename>
## -vpd2vcd <vcdplus_filename> <vcd_filename>
#-y <directory_pathname>
 
    
    
