#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/dmlib/dmfactory.py#1 $
$Change: 7733831 $
$DateTime: 2023/08/09 03:35:58 $
$Author: wplim $

Description: Abstract base class used for representing IC Manage configurations. See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)
from cmx.dmlib.archie import ARCHIE
from cmx.dmlib.eoumgr import EOUMGR
from cmx.dmlib.arc import ARC

class DMFactory:

    def create_dm(self, name, stages=None):
        if name == 'ipde':
            dm = ARCHIE(stages)

        elif name == 'r2g':
            dm = EOUMGR(stages)

        elif name == 'arc':
            dm = ARC(stages)

        else:
            raise Exception("No DM created based on deliverable name")

        return dm


if __name__ == "__main__":
    sys.exit(main())
