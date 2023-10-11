#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/abnr.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  abnr: Altera Build 'N Release
              command with subcommands for simplifying use of ICManage
              all subcommands are loaded from the abnrlib/plugins directory

Author: Anthony Galdes (ICManage)
        Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''

import sys
if sys.version_info < (2, 7):
    print "Must use python 2.7+ - did you forget to load an ARC environment?"
    sys.exit(1)

import os
import argparse
import logging
import re
import textwrap

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.helplib.help import *

#LOGGER = logging.getLogger('dmx')

def main():
    print "\n\tWelcome to PICE! abnr and quick have been replaced by dmx. Please see mapping below."
    print "\tNote: sion/syncpoint still exists as is.\n"  
    helpmap_command('')
    print get_support_url()

if __name__ == '__main__':
    main()
    sys.exit(0)
