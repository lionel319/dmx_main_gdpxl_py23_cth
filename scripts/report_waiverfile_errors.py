#!/usr/bin/env python

import os
import sys
#sys.path.insert(0, '/nfs/site/disks/da_infra_1/users/yltan/depot/da/infra/dmx/main/lib/python')
import logging
import dmx.tnrlib.waiver_file


LOGGER = logging.getLogger()


def main():
    wf = dmx.tnrlib.waiver_file.WaiverFile()
    wf.load_from_file(sys.argv[1])

if __name__ == "__main__":
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    main()

