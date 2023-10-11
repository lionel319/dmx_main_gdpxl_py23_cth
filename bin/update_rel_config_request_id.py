#!/usr/bin/env python

# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/update_rel_config_request_id.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""


"""

### std libraries
import os
import sys
import logging
import argparse

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.tnrlib.dashboard_query2 import DashboardQuery2
from dmx.abnrlib.icm import ICManageCLI
import re


### Global Varianbles
LOGGER = logging.getLogger()
SEP = '/'
SKIP_PROJECTS = ['da_i10']

def main():

    args = _add_args()
    _setup_logger(args)
    icm_pmlog_enable(mode=False)

   
    d = DashboardQuery2('guest', 'guest')
    icm = ICManageCLI()
    for project in icm.get_projects():
        if project in SKIP_PROJECTS or 'LabProject' in project:
            LOGGER.debug('Skipping {} ...'.format(project))
            continue
        for variant in icm.get_variants(project):
            for libtype in icm.get_libtypes(project, variant) + [None]:
                for config in icm.get_rel_configs(project, variant, libtype):
                    LOGGER.debug('working {}/{}/{}/{} ...'.format(project, variant, str(libtype), config))

                    if d.get_request_id_from_pvlc_cache(project, variant, str(libtype), config):
                        LOGGER.debug(">>> Found in cache. Skip...")
                        continue

                    try:
                        rid = d.get_request_id_from_pvlc(project, variant, libtype, config)
                        
                        ### echo append is better because if script dies halfway
                        ### we don't need to start all over again.
                        cmd = 'echo "{}/{}/{}/{}/{}" >> {}'.format(project, variant, str(libtype), config, rid, args.outfile)
                        LOGGER.debug(">>> {}".format(cmd))
                        os.system(cmd)
                    except:
                        LOGGER.debug(">>> Failed getting rid.")
                    

    LOGGER.info("Job Completed. Output file created at {}".format(args.outfile))



def _add_args():
    ''' Parse the cmdline arguments '''
    parser = argparse.ArgumentParser()

    parser.add_argument('--outfile', required=False, default='/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/common_info/rel_config_splunk_request_id.txt')
    parser.add_argument('--debug', required=False, action='store_true', default=False)

    args = parser.parse_args()
    return args


def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
         

def icm_pmlog_enable(mode=True):
    '''
    | Enable logging of pm/icmp4 commands to icm_pmlog.txt.
    | if ``mode`` is set to ``True``, loggings are logged to ``icm_pmlog.txt``.
    | if ``mode`` is set to ``False``, loggings are set to ``/dev/null``.
    '''
    if mode:
        os.environ['ICM_PM_LOG_FILE'] = 'icm_pmlog.txt'
    else:
        os.environ['ICM_PM_LOG_FILE'] = os.devnull



if __name__ == "__main__":
    sys.exit(main())

