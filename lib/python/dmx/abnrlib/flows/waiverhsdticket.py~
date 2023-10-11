#!/usr/bin/env python

"""
Base class for DMX MySql Database. 
"""
from __future__ import print_function
from builtins import input
from builtins import str
from builtins import object
import sys
sys.path.insert(0, '/nfs/site/disks/psg_flowscommon_1/common_info/pymongo380a')
import tdma_hsdes
#sys.path.insert(0, '/p/psg/da/infra/api')
import pymongo
from pymongo import MongoClient, UpdateOne, DeleteOne
from bson.objectid import ObjectId
import logging
import copy
import csv
import os
import dmx.utillib.admin
from datetime import datetime
LOGGER = logging.getLogger(__name__)
from dmx.utillib.dmxwaiverdb import DmxWaiverDb
from dmx.utillib.utils import get_waiver_data
from dmx.tnrlib.waiver_file import WaiverFile
from bson.json_util import dumps, loads
#from tabulate import tabulate
import tabulate 
from tdma_hsdes import HsdesConnection
#print tdma_hsdes.__file__
#sys.exit(1)
from dmx.errorlib.exceptions import *
from dmx.ecolib.ecosphere import EcoSphere
import dmx.abnrlib.flows.dmxwaiver

class WaiverHsdTicket(object):
    ''' Waiver HSD ticket Class '''
 
    def __init__(self, waiver_data, server_type='prod', attachment=None, waiver_type=None, approver=None):
        self.waiver_data = waiver_data
        self.thread = self.waiver_data[0].get('thread') 
        self.project = self.waiver_data[0].get('project') 
        self.milestone = self.waiver_data[0].get('milestone') 
        self.ip = self.waiver_data[0].get('ip') 
        self.approver = approver
        self.dmxwaiver = DmxWaiverDb(servertype=server_type)
        if server_type == 'prod':
            self.hsdes_env = HsdesConnection.HSDES_PROD_ENVIRONMENT
        elif server_type == 'test':
            self.hsdes_env = HsdesConnection.HSDES_TEST_ENVIRONMENT

        self.hsdes = HsdesConnection(env=self.hsdes_env)
        self.waiver_type = waiver_type
 
        self.attachment = attachment 

    def create_ticket2(self):
        #self.main_caseid = self.create_main_ticket()
        #self.main_caseid = '1405605933' 
        self.main_caseid = '15010228547' 
        # attach attchment to main ticket
        self.upload_attachment() 
        try:
            self.approval_ticket_id, self.approval_by_deliverable = self.create_approval_ticket(self.main_caseid)
        except Exception as e:
            LOGGER.error(e)
            LOGGER.error('Fail to create approval ticket. RollbacK. HSD ticket {} status set to rejected'.format(self.main_caseid))
            self.hsdes.set_work_item_attributes(work_item_id=self.main_caseid, status='rejected', reason='wont_do')

    def upload_attachment(self):
        if self.attachment:
            LOGGER.info('Upload attachment to main ticket') 
            for ea_attach in self.attachment:
                self.hsdes.upload_support(support_id=self.main_caseid, upload_file=ea_attach)
 
    def append_ticket(self, ticketid):
        self.main_caseid = ticketid 
        support_details = self.hsdes.query_search("select description where Parent(id='{}' AND tenant='fpga' AND subject='work_item' AND work_item.type='dmx_waiver_request'), \
                                      Child(subject='approval')".format(ticketid), count=100000)
        original_description =  support_details[0]['description']
        self.main_caseid = self.append_main_ticket(ticketid, original_description)

        self.upload_attachment() 
        try:
            self.approval_ticket_id, self.approval_by_deliverable = self.create_approval_ticket(self.main_caseid)
        except Exception as e:
            LOGGER.error(e)
            LOGGER.error('Fail to create approval ticket. RollbacK. HSD ticket {} status set to rejected'.format(self.main_caseid))
            self.hsdes.set_work_item_attributes(work_item_id=self.main_caseid, status='rejected', reason='wont_do')


    def get_waiver_description(self):
        desc = '<table class="table table-bordered">  \
                   <tr>  \
                      <td>Thread</td>  \
                      <td>Project</td>  \
                      <td>IP</td>  \
                      <td>Flow</td>  \
                      <td>Subflow</td>  \
                      <td>Milestone</td>  \
                      <td>Reason</td>  \
                      <td>Error</td>  \
                      <td>User</td>  \
                   </tr>'

        for ea_waiver in self.waiver_data:
            thread = ea_waiver['thread']
            ip = ea_waiver['ip']
            deliverable = ea_waiver['deliverable']
            subflow = ea_waiver['subflow']
            milestone = ea_waiver['milestone']
            reason = ea_waiver['reason']
            error = ea_waiver['error']
            username = ea_waiver['user']
            desc = desc + ' <tr>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                                <td>{}</td>  \
                            </tr>  \
                        '.format(self.thread, self.project, ip, deliverable, subflow, milestone, reason, error, username)
        desc = desc + '</table> '
        return desc
   

    def append_main_ticket(self, ticketid, ori_desc):
        deliverable_waivers = []
        username = os.environ['USER']
        approval_id = None
        LOGGER.info('Appending hsd ticket..')
        #hsdes_env = HsdesConnection.HSDES_PROD_ENVIRONMENT

        today_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        desc = ori_desc + "<br>Added on {} by {}<br>".format(today_date, os.environ.get('USER')) + self.get_waiver_description() + "<br>"
        self.hsdes.set_work_item_attributes(work_item_id=ticketid, description=desc)

        # Need to set status to awaiting_approval only can create approval ticket
        self.hsdes.set_work_item_attributes(work_item_id=ticketid, reason='awaiting_approval')

        LOGGER.info('Append waiver to main ticket {} done.'.format(ticketid))
        return ticketid 


    def create_main_ticket(self):
        deliverable_waivers = []
        username = os.environ['USER']
        approval_id = None
        LOGGER.info('Creating hsd ticket..')
        #hsdes_env = HsdesConnection.HSDES_PROD_ENVIRONMENT
        title = 'DMX waiver request for \'{}\' {}/{} milestone \'{}\''.format(self.thread, self.project, self.ip, self.milestone)
        desc = "This request is generated by dmx to create waiver approval ticket. <br><br> "
        desc = desc + self.get_waiver_description()

        hsdes_mapping = self.get_family_and_release_from_thread_ms(self.thread, self.milestone)
        family = hsdes_mapping.get('family')
        release = hsdes_mapping.get('release')
        stepping = hsdes_mapping.get('stepping')
        ms = hsdes_mapping.get('ms')

        caseid = self.hsdes.new_work_item(title=title, description=desc, family=family, release=release, found_in=ms, work_item_type='dmx_waiver_request', owner=username, send_mail= True)

        # Need to set status to awaiting_approval only can create approval ticket
        self.hsdes.set_work_item_attributes(work_item_id=caseid, reason='awaiting_approval')

        LOGGER.info('Waiver HSDES main ticket {} created'.format(caseid))
        return caseid 

    def get_family_and_release_from_thread_ms(self, thread, milestone):
        hsdes_mapping_data = dmx.abnrlib.flows.dmxwaiver.DmxWaiver().get_hsdes_mapping_data()
        data = {}
        if milestone == '1.0' or milestone == '0.1':
            ms = hsdes_mapping_data.get(thread).get('ms1')
        elif milestone == '2.0' or milestone == '0.3':
            ms = hsdes_mapping_data.get(thread).get('ms2')
        elif milestone == '3.0' or milestone == '0.5':
            ms = hsdes_mapping_data.get(thread).get('ms3')
        elif milestone == '4.0' or milestone == '0.8':
            ms = hsdes_mapping_data.get(thread).get('ms4')
        elif milestone == '5.0' or milestone == '1.0':
            ms = hsdes_mapping_data.get(thread).get('ms5')
        else:
            ms = 'MS1.0'

        data['family'] = hsdes_mapping_data.get(thread).get('family')
        data['release'] = hsdes_mapping_data.get(thread).get('release')
        data['stepping'] = hsdes_mapping_data.get(thread).get('stepping')
        data['ms'] = ms

        return data



    def precheck_approval_ticket(self):
        #hsdes_env = HsdesConnection.HSDES_PROD_ENVIRONMENT
        #approval_ticket_desc = self.get_approval_ticket_description(self.waiver_data, self.thread, self.milestone)
        waivers_desc_by_deliverable, waivers_desc_by_subflow = self.get_approval_ticket_description(self.waiver_data, self.thread, self.milestone)

        return waivers_desc_by_deliverable, waivers_desc_by_subflow

    def create_ticket(self):
        waivers_desc_by_deliverable, waivers_desc_by_subflow = self.precheck_approval_ticket()
       # print waivers_desc_by_deliverable
       # print waivers_desc_by_subflow
        print('    Thread: {}'.format(self.thread))
        print('    Project: {}'.format(self.project))
        print('    Milestone: {}'.format(self.milestone))
        print('    Approver: {}'.format(self.approver))
        print('    Waiver Type: {}'.format(self.waiver_type))
        print('')
        val = input('Do you want to proceed? [y/n] : ')
        if val != 'y':
            LOGGER.info('Aborted') 
            sys.exit(1)
        self.main_caseid = self.create_main_ticket()
        self.upload_attachment() 
        self.approval_ticket_id, self.approval_by_deliverable = self.create_approval_ticket(self.main_caseid, waivers_desc_by_deliverable, waivers_desc_by_subflow)

    def create_approval_ticket(self, main_caseid, waivers_desc_by_deliverable, waivers_desc_by_subflow):
        approval_ticket_id = {}
        approval_by_deliverable = {}
        today_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        LOGGER.info('Creating approval ticket...')
        for deliverable, deliverable_desc in list(waivers_desc_by_deliverable.items()):
            approver, notify_list, APPROVER = self.get_approver_and_notify_list(self.thread, deliverable)
            title = 'Please review DMX waiver for \'{}\' {}/{}:{} milestone \'{}\''.format(self.thread, self.project, self.ip, deliverable, self.milestone)
            approval_id = self.hsdes.new_approval(title=title, owner=approver, deliverable=deliverable, notify=','.join(notify_list),  support_id=main_caseid, description=deliverable_desc, send_mail=False)
            LOGGER.info('Approval ticket {} for deliverable \'{}\' created and assigned to \'{}\''.format(approval_id, deliverable, approver))
            approval_ticket_id[deliverable] = approval_id
            approval_by_deliverable[deliverable] = approver

        for deliverable_subflow, deliverable_desc in list(waivers_desc_by_subflow.items()):
            deliverable = deliverable_subflow[0]
            subflow = deliverable_subflow[1]
            
            approver, notify_list, APPROVER = self.get_approver_and_notify_list(self.thread, deliverable, subflow)
            title = 'Please review DMX waiver for \'{}\' {}/{}:{} milestone \'{}\''.format(self.thread, self.project, self.ip, deliverable, self.milestone)
            approval_id = self.hsdes.new_approval(title=title, owner=approver, deliverable=deliverable, notify=','.join(notify_list),  support_id=main_caseid, description=deliverable_desc, send_mail=False)
            LOGGER.info('Approval ticket {} for deliverable \'{}-{}\' created and assigned to \'{}\''.format(approval_id, deliverable, subflow, approver))
            approval_ticket_id[deliverable, subflow] = approval_id
            approval_by_deliverable[deliverable, subflow] = approver



        return approval_ticket_id, approval_by_deliverable


    def get_approver_and_notify_list(self, thread, deliverable, subflow=None):
        '''
        Since we are getting approver from cmdline, there is no need to grep from database.
        In future if we need that, then only re-enable
        '''
        if subflow == '*':
            APPROVER = 'default'
        else:
            APPROVER = 'subflow'

        if self.approver:
            approver = self.approver

        notify_list = ['']

        return approver, notify_list, APPROVER 





    def get_approval_ticket_description(self, waiver_data, thread, milestone):
        waivers_desc_by_deliverable = {}
        waivers_desc_by_subflow = {}
        desc = 'This request is generated by dmx to create waiver approval ticket. <br><br> \
                <table class="table table-bordered">  \
                   <tr>  \
                      <td>Thread</td>  \
                      <td>Project</td>  \
                      <td>IP</td>  \
                      <td>Flow</td>  \
                      <td>Subflow</td>  \
                      <td>Milestone</td>  \
                      <td>Reason</td>  \
                      <td>Error</td>  \
                      <td>User</td>  \
                   </tr> \
                   {} \
                </table> '
 
        waivers_row = '<tr>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td>  \
                        <td>{}</td> \
                       </tr>' 

        for ea_waiver in waiver_data:
            thread = str(ea_waiver['thread'])
            ip = str(ea_waiver['ip'])
            deliverable = str(ea_waiver['deliverable'])
            subflow = str(ea_waiver['subflow'])
            milestone = str(ea_waiver['milestone'])
            reason = str(ea_waiver['reason'])
            error = str(ea_waiver['error'])
            username = str(ea_waiver['user'])

            '''
            if waivers_desc_by_deliverable.get(ip) is None:
                waivers_desc_by_deliverable[ip] = {}

            if waivers_desc_by_deliverable.get(ip).get(deliverable) is None :
                waivers_desc_by_deliverable[ip][deliverable]= {}
                waivers_desc_by_deliverable[ip][deliverable] = waivers_row.format(thread, ip, deliverable, subflow, milestone, reason, error, username)
            else:
                waivers_desc_by_deliverable[ip][deliverable] = waivers_desc_by_deliverable[ip][deliverable] + waivers_row.format(thread, ip, deliverable, subflow, milestone, reason, error, username)
            '''
            approver, notify_list, APPROVER = self.get_approver_and_notify_list(thread, deliverable, subflow)
            if APPROVER == 'subflow':
                if waivers_desc_by_subflow.get((deliverable, subflow)) is None :

                    waivers_desc_by_subflow[(deliverable, subflow)]= {}
                    waivers_desc_by_subflow[(deliverable, subflow)] = waivers_row.format(self.thread, self.project, ip, deliverable, subflow, milestone, reason, error, username)
                else:
                    waivers_desc_by_subflow[(deliverable, subflow)] = waivers_desc_by_deliverable[deliverable, subflow] + waivers_row.format(self.thread, self.project, ip, deliverable, subflow, milestone, reason, error, username)
            else: 

                if waivers_desc_by_deliverable.get(deliverable) is None :
                    waivers_desc_by_deliverable[deliverable]= {}
                    waivers_desc_by_deliverable[deliverable] = waivers_row.format(self.thread, self.project, ip, deliverable, subflow, milestone, reason, error, username)
                else:
                    waivers_desc_by_deliverable[deliverable] = waivers_desc_by_deliverable[deliverable] + waivers_row.format(self.thread, self.project, ip, deliverable, subflow, milestone, reason, error, username)

        for deliverable, waiver_desc in list(waivers_desc_by_deliverable.items()):
            waivers_desc_by_deliverable[deliverable] = desc.format(waiver_desc)

        for deliverable_subflow, waiver_desc in list(waivers_desc_by_subflow.items()):
            deliverable = deliverable_subflow[0]
            subflow = deliverable_subflow[1]
            waivers_desc_by_subflow[deliverable, subflow] = desc.format(waiver_desc)
    
        return waivers_desc_by_deliverable, waivers_desc_by_subflow


           
if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    
