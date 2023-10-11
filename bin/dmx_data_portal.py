#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/dmx_data_portal.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  dmx_data_portal: 
              set all the golden data for dmx

Author: Natalia Baklitskaya

Copyright (c) Intel 2016 (what's the new Intel copyright?!)
All rights reserved.
'''

import sys
if sys.version_info < (2, 7):
    print "Must use python 2.7+ - did you forget to load an ARC environment?"
    sys.exit(1)

import os

if not os.environ['DMX_ROOT']:
    print "Must be in a dmx environment - arc shell dmx"
    sys.exit(1)
else:
   dmx_root = os.environ['DMX_ROOT']

def main():
    # TODO is there an env var for browser preference?  Is firefox always in our path?
    # cmd = "firefox " + dmx_root + "/web/dmx_data_portal/html/load_validate.html"
    cmd = "firefox http://sjdmxweb01.sc.intel.com/dmxweb/design_data_editor/index.html"
    os.system(cmd)

         
if __name__ == '__main__':
    main()
    sys.exit(0)
