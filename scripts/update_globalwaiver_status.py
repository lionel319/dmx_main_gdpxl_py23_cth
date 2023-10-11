#! /usr/bin/env python

import logging
import logging.config
import argparse
import os
import subprocess
import sys
import re
import unicodedata

sys.path.insert(0,'/nfs/site/disks/da_infra_1/users/wplim/depot/da/infra/dmx/main/lib/python')
from tdma_hsdes import HsdesConnection
from dmx.utillib.dmxmongodbbase import DmxMongoDbBase
from dmx.utillib.dmxwaiverdb import DmxWaiverDb


def main():
    args = _add_args()
    _setup_logger(args)

        
    all_approval_tickets = close_hsd_ticket(main_status='approved', reason='None', comment='All approval ticket closed.')
    update_mongo_db(all_approval_tickets)
 
def update_mongo_db(all_approval_tickets):
    '''
    Update mongodb global waiver status
    '''
    sign_off_ticket = []
    rejected_ticket = []

    mongodb = DmxWaiverDb()
    for approval_ticket, status in all_approval_tickets.items():
        if status == 'sign_off':
            sign_off_ticket.append(approval_ticket)
        elif status == 'wont_do':
            rejected_ticket.append(approval_ticket)

    mongodb.update_approval_status(sign_off_ticket, 'sign_off')
    mongodb.update_approval_status(rejected_ticket, 'wont_do')

def close_hsd_ticket(main_status, reason, comment):
    '''
    Close hsd ticket if approval ticket signoff
    '''
    logging.info('Get HSD ticket with main ticket status: \'open\'')
    hsdes_env = HsdesConnection.HSDES_PROD_ENVIRONMENT
    #hsdes_env = HsdesConnection.HSDES_PROD_ENVIRONMENT
    hsdes = HsdesConnection(env=hsdes_env)
    all_main_id = []
    all_approval_id = {} 
    need_to_close_ticket = {}

    support_details = hsdes.query_search("select status where Parent(tenant='fpga' AND subject='work_item' AND work_item.type='dmx_waiver_request'), \
                      Child(subject='approval')", count=100000)
    for line in support_details:
        parent_id = line.get('parent_id')
        approval_id = line.get('id')
        status = line.get('status')

        # skip 1306394410 because this is the default hsd case
        if parent_id == '1306878524': continue

        logging.debug("Close hsd ticket - {}. Status: \'{}\'. Reason: \'{}\'".format(parent_id, main_status, reason))

        if need_to_close_ticket.get(parent_id) is None or need_to_close_ticket.get(parent_id) is True:
            if status == 'sign_off' or status == 'wont_do':
                need_to_close_ticket[parent_id] = True
            else:
                need_to_close_ticket[parent_id] = False
        elif need_to_close_ticket.get(parent_id) is False:
            continue

        if approval_id not in all_approval_id:
            all_approval_id[approval_id] = status
        # Close hsd ticket 
        #hsdes.set_support_status(support_id=source_id, status=main_status, reason=reason, comment=comment, send_mail=True)
   # for ea_ticket, result in need_to_close_ticket.items():
   #     if result is True:
            #hsdes.set_support_status(support_id=ea_ticket, status=main_status, reason=reason, comment=comment, send_mail=True)
   #         hsdes.set_work_item_attributes(work_item_id=ea_ticket, status='approved')
    return all_approval_id 


def _add_args():
    ''' Parse the cmdline arguments '''
    # Simple Parser Example
    parser = argparse.ArgumentParser(description="Desc")
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument("-d", "--debug", action='store_true', help="debug level")
    args = parser.parse_args()

    return args

def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)


if __name__ == '__main__':
    sys.exit(main())

   
