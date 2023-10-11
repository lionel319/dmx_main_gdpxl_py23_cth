#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011,2015 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/CheckType_test.py#1 $

"""
Test the CheckType class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

import os
import unittest
import doctest
import shutil
import CheckType

from dm.VpMock import VpMock

def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the CheckType.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(CheckType))
    return tests

class TestCheckType(unittest.TestCase): # pylint: disable=R0904
    """Test the CheckType class."""

    def setUp(self):
        '''Set up the test'''
        def errorhandler(function, path, execinfo): # unused arg pylint: disable = W0613
            os.chmod(path, 0777)
            try:
                function(path)
            except:
                raise OSError("Cannot delete temporary file '{}'".format(path))
        if os.path.exists('testip1'):
            shutil.rmtree('testip1', onerror=errorhandler)
        if os.path.exists('+define+ALTR_HPS_TSMC_MACROS_OFF'):
            os.remove('+define+ALTR_HPS_TSMC_MACROS_OFF')
        if os.path.exists('-timescale=1ns'):
            shutil.rmtree('-timescale=1ns', onerror=errorhandler)

    def tearDown(self):
        pass

    # Leading "0" causes empty test to run first.
    def test_0_empty(self):
        '''Test initialization on empty instance'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertTrue(checker.check('TEST'))

    def test_1_checkPattern(self):
        '''Test the `<pattern>` type check.'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="file1">
              testip1/icc/testip1.file1
            </pattern>
            <pattern id="file2">
              testip1/icc/testip1.file2
            </pattern>
            <pattern id="dotdotdot">
              testip1/icc/....file3
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        os.makedirs('testip1/icc')
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        f = open('testip1/icc/testip1.file1', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Only one exists')
        f = open('testip1/icc/testip1.file2', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Only two exist')
        f = open('testip1/icc/testip1.file3', 'w')
        f.write('')
        f.close()
        self.assertTrue(checker.check('TEST'), 'All three exist')
        
        os.chmod('testip1/icc/testip1.file2', 0)
        self.assertFalse(checker.check('TEST'), 'File not readable')
        os.chmod('testip1/icc/testip1.file2', 0777)
        self.assertTrue(checker.check('TEST'))
        os.chmod('testip1/icc', 0)
        self.assertFalse(checker.check('TEST'), 'Directory not readable')
        os.chmod('testip1/icc', 0777)
        self.assertTrue(checker.check('TEST'))

    def test_2_checkPatternDotDotDot(self):
        '''Test the `<pattern>` type check with the Perforce ... wild card.'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="MINIMUM1">
            <pattern id="dotdotdot">
              testip1/icc/....file1
            </pattern>
          </template>
          <template id="MINIMUM2">
            <pattern id="dotdotdot" minimum="2">
              testip1/icc/....file2
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('MINIMUM1'), 'Nonexistent')
        
        self._createTestFile('testip1/icc/top.file1')
        self.assertTrue(checker.check('MINIMUM1'), 'Exists at top level')
        os.remove('testip1/icc/top.file1')
        
        self._createTestFile('testip1/icc/sub/sub/top.file1')
        self.assertTrue(checker.check('MINIMUM1'), 'Exists in a sub-directory')
        
        os.chmod('testip1/icc/sub/sub/top.file1', 0)
        self.assertFalse(checker.check('MINIMUM1'), 'File not readable')
        os.chmod('testip1/icc/sub/sub/top.file1', 0777)

        
        self.assertFalse(checker.check('MINIMUM2'), 'Nonexistent')
        
        self._createTestFile('testip1/icc/top.file2')
        self.assertFalse(checker.check('MINIMUM2'), 'Only one exists')

        self._createTestFile('testip1/icc/sub/sub/top.file2')
        self.assertTrue(checker.check('MINIMUM2'), 'All two exist')
        
        os.chmod('testip1/icc/sub/sub/top.file2', 0)
        self.assertFalse(checker.check('MINIMUM2'), 'File not readable')
        os.chmod('testip1/icc/sub/sub/top.file2', 0777)
        
    def test_3_checkPatternMinimum(self):
        '''Test the `<pattern minimum>` attribute type check.
        
        TO_DO: The `<pattern minimum>` attribute is only checked for wild cards
        recognized by Python :py:class:glob.glob`.  Namely, it does not check
        the number of files matched by the `...` pattern.
        '''
        os.makedirs('testip1/icc')
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="min0" minimum="0">
              testip1/icc/min0.txt
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertTrue(checker.check('TEST'), 'Nonexistent but optional')
        self._createTestFile('testip1/icc/min0.txt')
        self.assertTrue(checker.check('TEST'), 'Exists')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="min1" minimum="1">
              testip1/icc/min1.txt
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min1.txt')
        self.assertTrue(checker.check('TEST'), 'Exists')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="min2" minimum="2">
              testip1/icc/min2.txt
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min2.txt', 'w')
        self.assertFalse(checker.check('TEST'), 
                         'Exists, but without a wild card it is impossible to have enough')

        # Test with a * wildcard
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="min0glob" minimum="0">
              testip1/icc/min0glob*.txt
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertTrue(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min0globA.txt')
        self.assertTrue(checker.check('TEST'), 'Exists')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="min1glob" minimum="1">
              testip1/icc/min1glob*.txt
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min1globA.txt')
        self.assertTrue(checker.check('TEST'), 'One exists')
        self._createTestFile('testip1/icc/min1globB.txt')
        self.assertTrue(checker.check('TEST'), 'Two exist')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <pattern id="min2glob" minimum="2">
              testip1/icc/min2glob*.txt
            </pattern>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min2globA.txt')
        self.assertFalse(checker.check('TEST'), 'One exists but two required')
        self._createTestFile('testip1/icc/min2globB.txt')
        self.assertTrue(checker.check('TEST'), 'Two exist')
        self._createTestFile('testip1/icc/min2globC.txt')
        self.assertTrue(checker.check('TEST'), 'Three exist')

    def test_4_checkFilelist(self):
        '''Test the `<filelist>` type check with the .filelist filelist.'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="filelist1">
              testip1/icc/testip1.1.filelist
            </filelist>
            <filelist id="filelist2">
              testip1/icc/testip1.2.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nothing exists')
        # Build the filelist files
        os.makedirs('testip1/icc')
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        f = open('testip1/icc/testip1.1.filelist', 'w')
        f.write('// testip1.1.filelist\n')
        f.write('+incdir+include1\n')
        f.write('file1.txt\n')
        f.write('file2.txt\n')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Only one filelist exists')
        f = open('testip1/icc/testip1.2.filelist', 'w')
        f.write('// testip1.2.filelist\n')
        f.write('+incdir+include2\n')
        f.write('file3.txt\n')
        f.write('file4.txt\n')
        f.close()
        self.assertFalse(checker.check('TEST'), 
                         'Both filelists exists, but their contents do not')
        os.makedirs('testip1/icc/include1')
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        f = open('testip1/icc/file1.txt', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        f = open('testip1/icc/file2.txt', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        os.makedirs('testip1/icc/include2')
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        f = open('testip1/icc/file3.txt', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        f = open('testip1/icc/file4.txt', 'w')
        f.write('')
        f.close()
        self.assertTrue(checker.check('TEST'), 'All contents exist!')
        
        os.chmod('testip1/icc/include1', 0)
        self.assertFalse(checker.check('TEST'), '+include+ directory not readable')
        os.chmod('testip1/icc/include1', 0777)
        os.chmod('testip1/icc/testip1.2.filelist', 0)
        self.assertFalse(checker.check('TEST'), 'Filelist file not readable')
        os.chmod('testip1/icc/testip1.2.filelist', 0777)
        os.chmod('testip1/icc/file2.txt', 0)
        self.assertFalse(checker.check('TEST'), 'Content file not readable')
        os.chmod('testip1/icc/file2.txt', 0777)
        self.assertTrue(checker.check('TEST'))
        os.chmod('testip1/icc/file3.txt', 0)
        self.assertFalse(checker.check('TEST'), 'Content file not readable')
        os.chmod('testip1/icc/file3.txt', 0777)

    def test_5_checkCellFilelist(self):
        '''Test the `<filelist>` type check with the .f filelist.'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="cell_filelist">
              testip1/rtl/filelist/testip1.f
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nothing exists')
        # Build the filelist files
        os.makedirs('testip1/rtl/filelist')
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        f = open('testip1/rtl/filelist/testip1.f', 'w')
        f.write('// testip1.f\n')
        f.write('+incdir+wkspace_root/testip1/rtl/include\n')
        f.write('wkspace_root/testip1/rtl/file1.txt\n')
        f.write('wkspace_root/testip1/rtl/file2.txt\n')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Only the filelist file exists')
        os.makedirs('testip1/rtl/include')
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        f = open('testip1/rtl/file1.txt', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Not all contents exist...')
        f = open('testip1/rtl/file2.txt', 'w')
        f.write('')
        f.close()
        self.assertTrue(checker.check('TEST'), 'All contents exist!')
        
        os.chmod('testip1/rtl/include', 0)
        self.assertFalse(checker.check('TEST'), '+incdir+ directory not readable')
        os.chmod('testip1/rtl/include', 0777)
        os.chmod('testip1/rtl/filelist/testip1.f', 0)
        self.assertFalse(checker.check('TEST'), 'Filelist file not readable')
        os.chmod('testip1/rtl/filelist/testip1.f', 0777)
        os.chmod('testip1/rtl/file2.txt', 0)
        self.assertFalse(checker.check('TEST'), 'Content file not readable')
        os.chmod('testip1/rtl/file2.txt', 0777)
        self.assertTrue(checker.check('TEST'))
        self.assertTrue(checker.check('TEST'), 'All contents readable')

    def test_6_checkFilelistVCSOptions(self):
        '''Test the `<filelist>` type check on VCS options.'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="filelist1">
              testip1/icc/testip1.1.filelist
            </filelist>
           </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nothing exists')
        # Build the filelist files
        os.makedirs('testip1/icc')
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        f = open('testip1/icc/testip1.1.filelist', 'w')
        f.write('// testip1.1.filelist\n')
        f.write('+option\n')
        f.write('-option\n')
        f.close()
        self.assertFalse(checker.check('TEST'), 'Filelist contains VCS options')
        self.maxDiff = None
        self.assertItemsEqual(checker.errors,
            ["In 'TEST', filelist 'testip1/icc/testip1.1.filelist' contains the VCS "
                "option '+option'.  Specify VCS options on the VCS command line, "
                "not in the filelist.",
             "In 'TEST', filelist 'testip1/icc/testip1.1.filelist' contains the VCS "
                "option '-option'.  Specify VCS options on the VCS command line, "
                "not in the filelist."])
        
    def test_7_checkFilelistMinimum(self):
        '''Test the `<filelist minimum>` attribute type check.
        
        TO_DO: The `<filelist minimum>` attribute is only checked for wild cards
        recognized by Python :py:class:glob.glob`.  Namely, it does not check
        the number of files matched by the `...` pattern.
        '''
        os.makedirs('testip1/icc')
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="min0" minimum="0">
              testip1/icc/min0.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertTrue(checker.check('TEST'), 'Nonexistent but optional')
        self._createTestFile('testip1/icc/min0.filelist')
        self.assertTrue(checker.check('TEST'), 'Exists')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="min1" minimum="1">
              testip1/icc/min1.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min1.filelist')
        self.assertTrue(checker.check('TEST'), 'Exists')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="min2" minimum="2">
              testip1/icc/min2.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min2.filelist', 'w')
        self.assertFalse(checker.check('TEST'), 
                         'Exists, but without a '
                            'wild card it is impossible to have enough')

        # Test with a * wildcard
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="min0glob" minimum="0">
              testip1/icc/min0glob*.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertTrue(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min0globA.filelist')
        self.assertTrue(checker.check('TEST'), 'Exists')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="min1glob" minimum="1">
              testip1/icc/min1glob*.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min1globA.filelist')
        self.assertTrue(checker.check('TEST'), 'One exists')
        self._createTestFile('testip1/icc/min1globB.filelist')
        self.assertTrue(checker.check('TEST'), 'Two exist')

        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <filelist id="min2glob" minimum="2">
              testip1/icc/min2glob*.filelist
            </filelist>
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nonexistent')
        self._createTestFile('testip1/icc/min2globA.filelist')
        self.assertFalse(checker.check('TEST'), 'One exists but two required')
        self._createTestFile('testip1/icc/min2globB.filelist')
        self.assertTrue(checker.check('TEST'), 'Two exist')
        self._createTestFile('testip1/icc/min2globC.filelist')
        self.assertTrue(checker.check('TEST'), 'Three exist')

    def test_8_checkMilkyway(self):
        '''Test the `<milkyway>` type check.'''
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="TEST">
            <milkyway id="mwLib1" mimetype="application/octet-stream">
              <libpath>
                testip1/icc/libName1
              </libpath>
              <lib>
                libName1
              </lib>
            </milkyway>'
            <milkyway id="mwLib2" mimetype="application/octet-stream">
              <libpath>
                testip1/icc/libName2
              </libpath>
              <lib>
                libName2
              </lib>
            </milkyway>'
          </template>
        </templateset>'''
        checker = CheckType.CheckType(VpMock('testip1', templatesetString=manifestSetXml))
        self.assertFalse(checker.check('TEST'), 'Nothing exists')
        # Build the filelist files
        os.makedirs('testip1/icc')
        os.makedirs('testip1/icc/libName1')
        os.makedirs('testip1/icc/libName2')
        self.assertFalse(checker.check('TEST'), 'No lib files yet')
        f = open('testip1/icc/libName1/lib', 'w')
        f.write('')
        f.close()
        self.assertFalse(checker.check('TEST'), 'No libName2/lib file yet')
        f = open('testip1/icc/libName2/lib', 'w')
        f.write('')
        f.close()
        self.assertTrue(checker.check('TEST'), 'Both libs exist')
        os.chmod('testip1/icc/libName2/lib', 0)
        self.assertFalse(checker.check('TEST'), 'libName2/lib file not readable')
        os.chmod('testip1/icc/libName2/lib', 0777)
        self.assertTrue(checker.check('TEST'), 'libName2/lib file readable')

    @classmethod
    def _createTestFile(cls, fileName, contents=('')):
        '''Create the specified test file, and its directory if necessary.
        Add the specified contents to the file, one per line.
        '''
        dirName = os.path.dirname(fileName)
        if dirName and not os.path.exists(dirName):
            os.makedirs(dirName)
        f = open(fileName, 'w')
        for content in contents:
            f.write(content)
            f.write('\n')
        f.close()

if __name__ == "__main__":
    unittest.main (failfast=True, verbosity=2)
