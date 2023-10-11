#!/usr/bin/env python

import os
import sys
import logging
import argparse
import time

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.bambooconnection import *

LOGGER = logging.getLogger('dmx')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='Bamboo URL', required=True)
    parser.add_argument('--plan', help='Bamboo plan name', required=True)
    parser.add_argument('--username', help='Bamboo username', required=True)
    parser.add_argument('--password', help='Bamboo password', required=True)

    args = parser.parse_args()

    plan = args.plan
    url = args.url
    username = args.username
    password = args.password

    bamboo = BambooConnection(url, username, password)

    # Fire off plan
    LOGGER.info('Firing bamboo plan {}'.format(plan))
    current_plan = bamboo.build_plan(plan)
    plan_url = bamboo.get_plan_url(current_plan)

    # Poll for completion
    while not bamboo.is_plan_finished(current_plan):
        LOGGER.info('Plan {} is still running, check {} for progress. Next poll in 30s'.format(current_plan, plan_url))
        time.sleep(30)

    if bamboo.is_plan_successful(current_plan):
        LOGGER.info('Plan {} has passed'.format(current_plan))
        ret = 0
    else:
        LOGGER.error('Plan {} failed. Please check {} for errors'.format(current_plan, plan_url))
        ret = 1 

    return ret

if __name__ == '__main__':
    logging.basicConfig(format="%(levelname)s [%(asctime)s]: %(message)s")
    LOGGER.setLevel(logging.INFO)
    sys.exit(main())
