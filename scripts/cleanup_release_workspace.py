#!/usr/bin/env python

from pprint import pprint, pformat
import re
import sys

import dmx.utillib.loggingutils
import logging
import dmx.utillib.utils
import dmx.abnrlib.icm

LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)

def main():

    icm = dmx.abnrlib.icm.ICManageCLI(preview=False)
    oldwsnames = icm.get_workspaces_for_user_by_age(user='psginfraadm', older_than=10)
    LOGGER.debug(pformat(oldwsnames))
    LOGGER.debug(len(oldwsnames))

    releasedir = '/nfs/site/disks/psg_tnr_1/release'
    for wsname in oldwsnames:
        rootDir = icm.get_workspace_details(wsname, retkeys=['rootDir'])
        if releasedir in rootDir:
            LOGGER.info("Deleting workspace {} - {}".format(wsname, rootDir))
            try:
                ret = icm.del_workspace(wsname, force=True, preserve=True)
                if ret:
                    LOGGER.info("- Workspace {} deleted.".format(wsname))
                else:
                    LOGGER.warning("- Problem deleting workspace {}.".format(wsname))
            except Exception as e:
                LOGGER.warning("- Problem deleting workspace {} : {}".format(wsname, str(e)))
        else:
            LOGGER.info("Skipping workspace {} - {}".format(wsname, rootDir))


if __name__ == '__main__':
    main()
