#!/usr/bin/env python

import os
import sys
import logging

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.abnrlib.icm import ICManageCLI



LOGGER = logging.getLogger()
OLDER_THAN = 30  # only process workspaces that are older than this many days
RELEASER = 'psginfraadm'
ICMPROJECTS = ['i10socfm', 'Falcon_Mesa']

logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

def main():
    icm = ICManageCLI()
    workspaces = icm.get_workspaces_for_user_by_age(RELEASER, older_than=OLDER_THAN)
    for wsname in workspaces:
        try:
            LOGGER.info("Processing workspace {} ...".format(wsname))

            d = icm.get_workspace_details(wsname)
            if d['Dir'].startswith('/nfs/site/disks/fln_tnr_1') or  d['Dir'].startswith('/nfs/sc/disks/fln_tnr_1') or \
               d['Dir'].startswith('/nfs/site/disks/whr_tnr_1') or  d['Dir'].startswith('/nfs/sc/disks/whr_tnr_1'):
                LOGGER.info("- Deleting workspace {} ...".format(wsname))
                icm.del_workspace(wsname, preserve=False, force=True)
            else:
                LOGGER.info("- Skip workspace {} ...".format(wsname))
        except Exception as e:
            LOGGER.error(str(e))

    for project in ICMPROJECTS:
        for variant in icm.get_variants(project):
            for config in icm.get_configs(project, variant):
                if config.startswith("tnr-placeholder"):
                    try:
                        LOGGER.info("- Deleting config {}/{}@{} ...".format(
                            project, variant, config))
                        icm.del_config(project, variant, config)
                    except Exception as e:
                        LOGGER.error(str(e))

if __name__ == '__main__':
    sys.exit(main())

