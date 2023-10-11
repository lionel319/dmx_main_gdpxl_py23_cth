#!/usr/bin/env python

import os
import sys
import logging
import argparse
import time

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.tnrlib.dashboard_query2
from pprint import pprint
import dmx.utillib.releaselog
import dmx.abnrlib.icm

LOGGER = logging.getLogger('dmx')
USERNAME = 'guest'
PASSWORD = 'guest'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p')
    parser.add_argument('--variant', '-v')
    parser.add_argument('--libtype', '-l', default=None)
    parser.add_argument('--config', '-c')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--output', '-o')

    args = parser.parse_args()

    project = args.project
    variant = args.variant
    libtype = args.libtype
    config = args.config
    debug = args.debug
    output = args.output

    if debug:
        LOGGER.setLevel(logging.DEBUG)

    q = dmx.tnrlib.dashboard_query2.DashboardQuery2(USERNAME, PASSWORD)

    if config:
        relconfigs = [config]
        libtypes = [libtype]
    else:
        cli = dmx.abnrlib.icm.ICManageCLI()
        if libtype:
            libtypes = [libtype]
        else:
            libtypes = cli.get_libtypes(project, variant)
            libtypes.append(None)
            
    for l in libtypes:
        relconfigs = cli.get_rel_configs(project, variant, l)

        for rel in relconfigs:
            if l:
                msg = 'Processing {}/{}:{}@{}'.format(project, variant, l, rel)
            else:
                msg = 'Processing {}/{}@{}'.format(project, variant, rel)

            LOGGER.info(msg)
            LOGGER.info('Getting waived errors...')
            results = q.get_waived_errors_from_pvlc(project, variant, l, rel, with_topcell=True)
            LOGGER.debug('Waived errors: {}'.format(results))

            LOGGER.info('Getting release info...')
            rid = q.get_request_id_from_pvlc(project, variant, l, rel)
            headers = q.run_query('search index=qa request_id={} status="Start handling request" | table *'.format(rid))[0]
            LOGGER.debug('Headers: {}'.format(headers))

            releaser = headers['user']
            arcjob = headers['arc_job_id']
            relconfig = rel
            snapconfig = headers['config']
            milestone = headers['milestone']
            thread = headers['thread'] 
            description = headers['description']
            release_id = headers['abnr_release_id']
            datetime = headers['timestamp']
            filename = '{}/{}.json'.format(output, release_id)
            lib = l if l else 'None'

            releaselog = dmx.utillib.releaselog.ReleaseLog(filename, project, variant, lib, snapconfig, releaser, datetime, arcjob, relconfig, milestone, thread, description, release_id)
            releaselog.json['dmx_version'] = ''
            releaselog.json['dmxdata_version'] = ''

            for result in results:
                flow = result['flow']
                subflow = result['subflow']
                topcell = result['flow-topcell'] if 'flow-topcell' in result else ''
                error = result['error']
                waiver = result['waiver-reason']
                status = 'waived'
                releaselog.add_result(flow, subflow, topcell, status, error, waiver)

            releaselog.save()

if __name__ == '__main__':
    logging.basicConfig(format="%(levelname)s [%(asctime)s]: %(message)s")    
    LOGGER.setLevel(logging.INFO)
    sys.exit(main())
