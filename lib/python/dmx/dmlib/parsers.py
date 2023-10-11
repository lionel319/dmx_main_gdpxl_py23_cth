#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/parsers.py#1 $

"""
This `dm.parsers` module contains file parsers related to
`Design Data Management <http://sw-wiki/twiki/bin/view/DesignAutomation/DesignDataManagement>`_.
"""

import os
import sys # @UnusedImport
import re
import shutil # pylint: disable=W0611
import xml.etree.ElementTree
from dmx.dmlib.dmError import dmError


def parseCellNamesFile(fileName):
    """Return a list of the lines appearing in the specified IPSPEC deliverable
    cell name file, removing comments and other such nonsense.
    
    Instead of using this function directly, consider using the `getCellNamesForIP()`
    method in :py:class:`altera_icm.workspace`.
    
    Currently this is equivalent to `dm.parsers.parseFilelist()`.  See that
    function for details and tests.
    """
    return parseFilelist(fileName)

def parseFilelist(fileName, doKeepVCSOptions=True):
    """Return a list of the lines appearing in the specified filelist file,
    removing comments and leading and trailing white space.  Comments start
    at,
    
    * `//` at the beginning of the line
    * `//` surrounded by white space

    Comments terminate at the end of the line.
    
    When the `doKeepVCSOptions` argument is True (the default), include
    lines that begin with '-' or '+' after removing leading white space.
    If `doKeepVCSOptions` is false, discard them.
            
    No adjustment of the file paths is performed; no normalization of file
    paths is performed.  That is the job of `ExpandFilelist.expandFilelists()`.

    Usage example:
    
    >>> if os.path.exists('testip1'):
    ...     shutil.rmtree('testip1')
    >>> os.makedirs('testip1/rtl')
    >>>
    >>> f = open('testip1/rtl/ip1.rtl.filelist', 'w')
    >>> f.write('// RTL filelist containing three files\\n')
    >>> f.write('//Test comment at the beginning followed by non-whitespace\\n')
    >>> f.write('one.v                    // Relative path\\n')
    >>> f.write('dir/two.v                // Relative path\\n')
    >>> f.write('/full/path/to/three.v    // Full path\\n')
    >>> f.close()
    >>>
    >>> parseFilelist('testip1/rtl/ip1.rtl.filelist')
    ['one.v', 'dir/two.v', '/full/path/to/three.v']
    >>>

    When the `doKeepVCSOptions` argument is True (the default), include
    lines that begin with '-' or '+'.  If `doKeepVCSOptions` is false, discard
    them:
    
    >>> f = open('testip1/rtl/ip1.rtl.filelist', 'w')
    >>> f.write("// VCS options start with '+' or '-'\\n")
    >>> f.write('-anyMinusOption\\n')
    >>> f.write('+anyPlusOption\\n')
    >>> f.write('+incdir+.+relpath/to/four.v+/full/path/to/five.v\\n')
    >>> f.write('-f relpath/to//six.v\\n')
    >>> f.write('-y relpath/to/./seven.v\\n')
    >>> f.write('-v relpath/to/eight.v\\n')
    >>> f.write('plainFile.v\\n')
    >>> f.close()
    >>>
    >>> parseFilelist('testip1/rtl/ip1.rtl.filelist')
    ['-anyMinusOption', '+anyPlusOption', '+incdir+.+relpath/to/four.v+/full/path/to/five.v', '-f relpath/to//six.v', '-y relpath/to/./seven.v', '-v relpath/to/eight.v', 'plainFile.v']
    >>>
    >>> parseFilelist('testip1/rtl/ip1.rtl.filelist', doKeepVCSOptions=False)
    ['plainFile.v']

    `pop()` can be used to access members without harming the database:
    
    >>> s = parseFilelist('testip1/rtl/ip1.rtl.filelist', doKeepVCSOptions=False)
    >>> ignoredValue = s.pop()
    >>> parseFilelist('testip1/rtl/ip1.rtl.filelist', doKeepVCSOptions=False)
    ['plainFile.v']
    
    Further tests are in :py:class:`dm.ExpandFilelist_test`.
    """
    outputLines = []
    with open(fileName, 'r') as f:
        for line in f:
            decommentedLine = re.sub(r'^//.*|\s//\s.*', '', line)
            decommentedLine = decommentedLine.strip()
            if not decommentedLine:
                # Nothing more than comments and white space on this line
                continue
            if (not doKeepVCSOptions) and  decommentedLine.startswith(('+', '-')):
                # Discard VCS option lines
                continue
            outputLines.append(decommentedLine)
    return outputLines

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
 
    
class MwReferenceLibraryControlFile(object):
    """Instantiate a reader/writer for Milkyway reference library control files.
    
    >>> if os.path.exists('test.reference_control_file.rpt'):
    ...     os.remove('test.reference_control_file.rpt')
    >>>
    >>> f = open('test.reference_control_file.rpt', 'w')
    >>> f.write('LIBRARY    test/topLib\\n')
    >>> f.write('  REFERENCE /full/path/name\\n')
    >>> f.write('  REFERENCE relative/path\\n')
    >>> f.write('  REFERENCE dirName\\n')
    >>> f.close()
    >>> refLibs = MwReferenceLibraryControlFile()
    >>> refLibs.read ('test.reference_control_file.rpt')
    >>> refLibs.get('test/topLib')
    ['/full/path/name', 'relative/path', 'dirName']
    """
    def __init__(self):
        self._libraries = {}
        
    @property
    def libraryNames(self):
        """The list of referencing libraries (LIBRARY), in alphabetical order.

        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.libraryNames
        []
        >>> refLibs.add('lib2', 'reflib2a')
        >>> refLibs.libraryNames
        ['lib2']
        >>> refLibs.add('./lib2', 'reflib2b')
        >>> refLibs.libraryNames
        ['lib2']
        >>> refLibs.add('lib1', 'reflib1a')
        >>> refLibs.libraryNames
        ['lib1', 'lib2']
       """
        libraryNames = self._libraries.keys()
        libraryNames.sort()
        return libraryNames
        
    def hasLibraryName(self, libraryName):
        """Is the specified referencing library (LIBRARY) defined?

        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.add('lib1', 'reflib1a')
        >>> refLibs.add('lib2', 'reflib2a')
        >>> refLibs.hasLibraryName('lib1')
        True
        >>> refLibs.hasLibraryName('lib2')
        True
        >>> refLibs.hasLibraryName('nonexistent')
        False
       """
        return (libraryName in self.libraryNames)

    def get(self, libraryName=None):
        """Get the list of reference libraries for the specified referencing
        library.  The reference libraries appear in the order in which they were
        added.
        
        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.get('lib1')
        []
        >>> refLibs.add('./lib1', 'reflib1a')
        >>> refLibs.add('lib1', 'reflib1b')
        >>> refLibs.add('lib2', 'reflib2a')
        >>> refLibs.add('lib2', 'reflib2b')
        >>> refLibs.get('lib1')
        ['reflib1a', 'reflib1b']
        >>> refLibs.get('lib2')
        ['reflib2a', 'reflib2b']
        >>> refLibs.get('./lib2')
        ['reflib2a', 'reflib2b']
        >>> refLibs.get('nonexistent')
        []
        
        It is very common for there to be only a single referencing library and
        reference library list.  In this case, you need not specify the
        referencing library name.  This eliminates problems with differences
        in format between the referencing library name specified and the name
        stored in the instance.
        
        >>> refLibs = MwReferenceLibraryControlFile()        
        >>> refLibs.get()
        []
        >>> refLibs.add('lib1', 'reflib1a')
        >>> refLibs.add('lib1', 'reflib1b')
        >>> refLibs.get()
        ['reflib1a', 'reflib1b']
        
        If no library name is specified but there are actually multiple
        referencing libraries, an exception will be raised. 

        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.add('lib1', 'reflib1a')
        >>> refLibs.add('lib1', 'reflib1b')
        >>> refLibs.add('lib2', 'reflib2a')
        >>> refLibs.add('lib2', 'reflib2b')
        >>> refLibs.get() #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ...multiple referencing LIBRARYs...
        """
        if libraryName is None:
            referencingLibraryCount = len(self._libraries)
            if referencingLibraryCount == 0:
                return []
            if referencingLibraryCount > 1:
                raise dmError("There are multiple referencing LIBRARYs when only one was expected")
            libraryName = iter(self._libraries).next()
        
        normLibraryName = os.path.normpath(libraryName)
        return self._libraries.get(normLibraryName, [])
        
    def add(self, libraryName, referenceLibraryName):
        """Add the specified reference library to the specified referencing
        library.
        
        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.add('lib1', 'reflib1a')
        >>> refLibs.add('lib1', 'reflib1b')
        >>> refLibs.add('lib2', 'reflib2a')
        >>> refLibs.add('lib2', 'reflib2b')
        >>> refLibs.get('lib1')
        ['reflib1a', 'reflib1b']
        >>> refLibs.get('lib2')
        ['reflib2a', 'reflib2b']
        """
        normLibraryName = os.path.normpath(libraryName)
        currentReferenceLibraries = self._libraries.setdefault(normLibraryName, [])
        currentReferenceLibraries.append(referenceLibraryName)
   
    def read(self, fileName):
        """Reset any previously defined reference libraries, and read the
        specified reference library control file.
        
        >>> if os.path.exists('test.reference_control_file.rpt'):
        ...     os.remove('test.reference_control_file.rpt')
        >>>
        >>> f = open('test.reference_control_file.rpt', 'w')
        >>> f.write('LIBRARY    test/topLib1\\n')
        >>> f.write('  REFERENCE /full/path/name1\\n')
        >>> f.write('  REFERENCE relative/path1\\n')
        >>> f.write('  REFERENCE dirName1\\n')
        >>> f.write('LIBRARY    test/topLib2\\n')
        >>> f.write('  REFERENCE /full/path/name2\\n')
        >>> f.write('  REFERENCE relative/path2\\n')
        >>> f.write('  REFERENCE dirName2\\n')
        >>> f.close()
        >>>
        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.read('test.reference_control_file.rpt')
        >>> refLibs.get('test/topLib1')
        ['/full/path/name1', 'relative/path1', 'dirName1']
        >>> refLibs.get('test/topLib2')
        ['/full/path/name2', 'relative/path2', 'dirName2']
        >>>
        >>> # Reading another file erases the old results.
        >>> f = open('test.reference_control_file.rpt', 'w')
        >>> f.write('LIBRARY    newlib\\n')
        >>> f.write('  REFERENCE newref\\n')
        >>> f.close()
        >>>
        >>> refLibs.read('test.reference_control_file.rpt')
        >>> refLibs.get('newlib')
        ['newref']
        >>> refLibs.get('test/topLib1')
        []
        >>> refLibs.get('test/topLib2')
        []
        
        It is an error for REFERENCE to precede LIBRARY:
        
        >>> f = open('test.reference_control_file.rpt', 'w')
        >>> f.write('  REFERENCE /full/path/name1\\n')
        >>> f.close()
        >>>
        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.read('test.reference_control_file.rpt') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ...'REFERENCE' precedes 'LIBRARY'...
        """
        self._libraries = {}
        libraryName = None
        with open(fileName, 'r') as f:
            for line in f:
                tokens = line.split()
                keyword = tokens[0]
                if keyword == 'LIBRARY':
                    libraryName = tokens[1]
                elif keyword == 'REFERENCE':
                    if libraryName is None:
                        raise dmError("In Milkyway reference control file '{}', "
                                    "'REFERENCE' precedes 'LIBRARY'.".format(fileName))
                    referenceLibraryName = tokens[1]
                    self.add(libraryName, referenceLibraryName)

    def write(self, fileName):
        """Write the specified reference library control file.  Arrange the
        referencing libraries in alphabetical order, and arrange the reference
        libraries in the order in which they were added.
        
        >>> if os.path.exists('test.reference_control_file.rpt'):
        ...     os.remove('test.reference_control_file.rpt')
        >>>
        >>> refLibs = MwReferenceLibraryControlFile()
        >>> refLibs.add('lib1', 'reflib1a')
        >>> refLibs.add('lib1', 'reflib1b')
        >>> refLibs.add('lib2', 'reflib2a')
        >>> refLibs.add('lib2', 'reflib2b')
        >>> refLibs.write('test.reference_control_file.rpt')
        >>> f = open('test.reference_control_file.rpt')
        >>> f.readlines()
        ['LIBRARY lib1\\n', '  REFERENCE reflib1a\\n', '  REFERENCE reflib1b\\n', 'LIBRARY lib2\\n', '  REFERENCE reflib2a\\n', '  REFERENCE reflib2b\\n']
        """
        libraryNames = self._libraries.keys()
        libraryNames.sort()
        lines = []
        for libraryName in libraryNames:
            lines.append('LIBRARY {}'.format(libraryName))
            for referenceLibraryName in self.get(libraryName):
                lines.append('  REFERENCE {}'.format(referenceLibraryName))
        lines.append('')
        
        fileContents = '\n'.join(lines)
        if fileName is None:
            sys.stdout.write(fileContents)
        else:
            f = open(fileName, 'w')
            f.write(fileContents)
            f.close()
            
    def diff(self, actual):
        """Return a list explaining the differences between this and the
        specified instance of
        :py:class:`dm.parsers.MwReferenceLibraryControlFile`.
        
        Only reference library control files that contain a single referencing
        library are supported.  Any differences in the referencing library are
        ignored.  This is because:
        
        # The vast majority of reference library control files contain just one \
          referencing library
        # The referencing library name can be different yet equivalent--`lib`, \
          `./lib`, `/path/to/lib` may or may not be the same library
        # Often the referencing libraries in the two reference library control \
          files are in fact different.  However you are really only interested \
          in comparing the reference libraries.

        Only a string comparison is performed.  No effort is made to reconcile
        with respect to the file system.
        
        For the sake of comparison, the order of the reference libraries is
        ignored.  The messages appear in the order of the reference libraries in
        `self`.
        
        Any messages will be worded assuming that `self` is correct, and
        `actual` is incorrect.

        >>> expected = MwReferenceLibraryControlFile()
        >>> expected.add('lib1', 'reflib1a')
        >>> expected.add('lib1', 'reflib1b')
        >>>
        >>> matching = MwReferenceLibraryControlFile()
        >>> matching.add('lib1', 'reflib1b')
        >>> matching.add('lib1', 'reflib1a')
        >>> expected.diff(matching)
        []
        >>>
        >>> missing = MwReferenceLibraryControlFile()
        >>> missing.add('lib1', 'reflib1b')
        >>> expected.diff(missing)
        ["Reference library 'reflib1a' is missing"]
        >>>
        >>> extra = MwReferenceLibraryControlFile()
        >>> extra.add('lib1', 'reflib1b')
        >>> extra.add('lib1', 'reflib1a')
        >>> extra.add('lib1', 'reflib1c')
        >>> expected.diff(extra)
        ["Reference library 'reflib1c' is extra and should not be defined"]

        It is an error for either reference library control file to contain
        more than one referencing library:
        
        >>> multiple = MwReferenceLibraryControlFile()
        >>> multiple.add('lib1', 'reflib1a')
        >>> multiple.add('lib1', 'reflib1b')
        >>> multiple.add('lib2', 'reflib2a')
        >>> multiple.add('lib2', 'reflib2b')
        >>>
        >>> single = MwReferenceLibraryControlFile()
        >>> single.add('lib1', 'reflib1a')
        >>> multiple.diff(single) #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: Cannot diff reference library control files containing multiple referencing libraries
        >>>
        >>> single.diff(multiple) #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: Cannot diff reference library control files containing multiple referencing libraries
        """
        try:
            refLibraries = set(self.get())
            actualRefLibraries = set(actual.get())            
        except dmError:
            raise dmError("Cannot diff reference library control files containing multiple referencing libraries")
        differences = []
        for missingRefLibrary in (refLibraries - actualRefLibraries):
            differences.append("Reference library '{}' is missing".format(missingRefLibrary))
                
        for extraRefLibrary in (actualRefLibraries - refLibraries):
            differences.append("Reference library '{}' is extra and should not be defined".format(extraRefLibrary))
                
        return differences

class BijectionConfigFile(object):
    '''Parse the deliverable bijection config file XML into an
    :py:class:`xml.etree.ElementTree.Element`.
    
    A `ParseError` exception is raised if the XML is invalid:
    
    >>> f = open('testconfig.xml', 'w')
    >>> f.write("""<netlistconfig>
    ...         <configurations>
    ...         <!-- It is an error to not close the configurations tag -->
    ...       </netlistconfig>""")
    >>> f.close()
    >>> b = BijectionConfigFile('testconfig.xml') #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ParseError: mismatched tag: line ..., column ...
    '''
    def __init__(self, fileName):
        self._root = xml.etree.ElementTree.parse(fileName)

    def getRevision(self, ipName, deliverableName):
        '''Return the set of revisions of the specified dependent deliverable
        within the specified IP.
        
        Ordinarily, it is expected that the returned list contains one element:
        
        >>> f = open('testconfig.xml', 'w')
        >>> f.write("""<netlistconfig>
        ...         <configurations>
        ...           <configuration ip="ip1" version="ip1"/>
        ...           <configuration ip="ip2" deliverable="INTERMAP" version="RELx"/>
        ...           <configuration ip="testznum" deliverable="INTERMAP" version="RELx">
        ...             <dependency id="INTERMAP" ref="REL1"/>
        ...           </configuration>
        ...         </configurations>
        ...       </netlistconfig>""")
        >>> f.close()
        >>> b = BijectionConfigFile('testconfig.xml')
        >>> b.getRevision('testznum', 'INTERMAP')
        ['REL1']

        The returned list contains no elements if the specified IP/deliverable
        combination does not exist:
        
        >>> f = open('testconfig.xml', 'w')
        >>> f.write("""<netlistconfig>
        ...         <configurations>
        ...           <configuration ip="testznum" deliverable="INTERMAP" version="RELx">
        ...             <dependency id="DOESNOTMATCH" ref="REL1"/>
        ...           </configuration>
        ...         </configurations>
        ...       </netlistconfig>""")
        >>> f.close()
        >>> b = BijectionConfigFile('testconfig.xml')
        >>> b.getRevision('testznum', 'INTERMAP')
        []

        A list containing multiple revisions is most likely due to an error in
        the input file:
        
        >>> f = open('testconfig.xml', 'w')
        >>> f.write("""<netlistconfig>
        ...         <configurations>
        ...           <configuration ip="testznum" deliverable="INTERMAP" version="RELx">
        ...             <dependency id="INTERMAP" ref="REL1"/>
        ...             <!-- It is incorrect for this line to be repeated -->
        ...             <dependency id="INTERMAP" ref="REL2"/>
        ...           </configuration>
        ...         </configurations>
        ...       </netlistconfig>""")
        >>> f.close()
        >>> b = BijectionConfigFile('testconfig.xml')
        >>> b.getRevision('testznum', 'INTERMAP')
        ['REL1', 'REL2']

        '''
        # Synthesize xpath .//configurations/configuration[@ip='{}' and @deliverable='INTERMAP']/dependency[@id='INTERMAP'
        elements1 = self._root.findall(r".//configurations/configuration[@ip='{}']/dependency[@id='{}']".format(ipName, deliverableName))
        elements2 = self._root.findall(r".//configurations/configuration[@deliverable='{}']/dependency[@id='{}']".format(deliverableName, deliverableName))
        elements = set(elements1) & set(elements2)
        revisions = [element.attrib.get('ref') for element in elements]
        revisions.sort()
        return revisions
