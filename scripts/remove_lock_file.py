#! /usr/bin/env python

import logging
import logging.config
import argparse
import os
import subprocess
import sys
import re
import unicodedata
import dmx.utillib.diskutils
import dmx.utillib.utils
def main():
    '''
    This scriptis to clean up .lock file when populate_cache end.

    1. Get all sion path
    2. check .lock folder
    3. if .lockfile end with _<arc_id>, delete

    '''
    args = _add_args()
    logger = _setup_logger(args)
    arc_id = args.arc_id

    site = os.environ.get('EC_SITE')
    du = dmx.utillib.diskutils.DiskUtils(site)
    dd = du.get_all_disks_data("_sion.*_")
    sion_paths = [ ea_dd.get('StandardPath')+'/cache/.locks/*' for ea_dd in dd] +  [ ea_dd.get('StandardPath')+'/*/.locks/*' for ea_dd in dd]
    for ea_sion_path in sion_paths:
        #cmd = 'find \'{}\' -name \'*.{}\' | xargs rm -rf'.format(ea_sion_path, arc_id)
        cmd = ' grep --with-filename {} {} | awk -F ":" \'{{print $1}}\' | xargs rm -rf'.format(arc_id, ea_sion_path)
        logger.info(cmd)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        if exitcode:
            logger.warning(exitcode)
            logger.warning(stdout)
            logger.warning(stderr)
            logger.warning('Cmd - {} run failed. Didnt find any matching .lock file'.format(cmd))


def _add_args():
    ''' Parse the cmdline arguments '''
    # Simple Parser Example
    parser = argparse.ArgumentParser(description="Desc")
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument("-d", "--debug", action='store_true', help="debug level")
    required.add_argument("-a", "--arc_id", required=True, help="arc id")
    args = parser.parse_args()

    return args

def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level, stream=sys.stdout)
    logger = logging.getLogger(__name__)
    return logger

if __name__ == '__main__':
    sys.exit(main())

   
