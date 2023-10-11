#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqdelete.py#2 $
$Change: 7437460 $
$DateTime: 2023/01/09 18:36:07 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import str
from builtins import object
import sys
import os
import logging
import textwrap
import tempfile
import re
from pprint import pprint, pformat

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.abnrlib.config_factory
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.utils
import dmx.utillib.server
import dmx.utillib.factory_cicq_api
import dmx.utillib.diskutils
import dmx.abnrlib.flows.cicqupdate
import dmx.utillib.server
import logging 
import dmx.utillib.admin
import json
import datetime
import configparser 

class CicqDeleteError(Exception): pass

class CicqDelete(object):
    '''
    Runner class for cicq delete 
    '''

    def __init__(self, project='i10socfm', ip='liotestfc1', thread='wplimrun1', day=None, dryrun=False):
        self.project = project
        self.ip = ip
        self.thread = thread
        self.dryrun = dryrun
        self.logger = logging.getLogger(__name__)
        self.user = os.getenv("USER")
        self.day = day
        self.api = dmx.utillib.factory_cicq_api.FactoryCicqApi(self.project, self.ip, self.thread, dryrun=self.dryrun)

    def delete_build_by_day(self):
        all_buildtypes_id = self.api.get_all_buildtypes_id()

        for buildtype_id in all_buildtypes_id:
            (prefix, project, ip, thread) = self.api.decompose_buildtype_id(buildtype_id)
            self.api = dmx.utillib.factory_cicq_api.FactoryCicqApi(project, ip, thread, dryrun=self.dryrun)
            self.logger.info('{}.{}.{}'.format(project, ip, thread))
            ret = self.api.get_latest_build_for_buildtype(buildtype_id)
            fmt = '%Y%m%d'
            try:
                jsondata = json.loads(ret)
                dtstr = jsondata['startDate'][:-12]
                dt = datetime.datetime.strptime(str(dtstr), fmt)
                delta = datetime.datetime.now() - dt
                #emails = self.get_cicq_ini_email(project, ip, thread)
                inactive_days = int(delta.days)
                self.logger.info('Inactive day = {}'.format(inactive_days))
                if  int(inactive_days) > int(self.day):
                    emails = self.get_cicq_ini_email(project, ip, thread)
                  #  today =  datetime.datetime.today().strftime('%Y-%m-%d')
                    self.cleanup_cicq_job()
                elif  int(inactive_days) > (int(self.day) -  7):
                    emails = self.get_cicq_ini_email(project, ip, thread)
                    self.send_reminder_email(project, ip, thread, inactive_days, self.day, emails)
               # elif inactive_days == 30 or inactive_days == 31:
               #     self.cleanup_cicq_job()

            except Exception as e:
                # this is for those who dont have any build yet
                pass

    def send_reminder_email_long_inactive_job(self, project, ip, thread, inactive_day, days, recipients):
        subject = 'Reminder: Removal of CICQ inactive job {}.{}.{}'.format(project, ip, thread)
        body = 'Dear user, <br><br><h2 style="color:Tomato;">You are receiving this email because you are in the CICQ job email list</h2>Your CICQ job {}.{}.{} has been inactive for <b>{}</b> days<br>It will be deleted on <b>15 November 2021</b>.<br><br>If you still need this job, kindly run \'dmx cicq run\' on your job to reset the counter.<br><br>Best regards,<br>psgicmsupport'.format(project, ip, thread, inactive_day)
        self.logger.debug('Emails send to {}'.format(recipients))
        #recipients = ['wei.pin.lim@intel.com']
        dmx.utillib.utils.sendmail(recipients, subject, body, cc_recipients=None, from_addr='psgicmsupport@intel.com', texttype='html')
        self.logger.info('Emails send to {}'.format(recipients))
        #sys.exit(1)
         

    def send_reminder_email(self, project, ip, thread, inactive_day, days, recipients):
        subject = 'Reminder: Removal of CICQ inactive job {}.{}.{}'.format(project, ip, thread)
        body = 'Dear user, <br><br><h2 style="color:Tomato;">You are receiving this email because you are in the CICQ job email list</h2>Your CICQ job {}.{}.{} has been inactive for <b>{}</b> days<br>It will be deleted when it hits <b>{}</b> days.<br><br>If you still need this job, kindly run \'dmx cicq run\' on your job to reset the counter.<br><br>Best regards,<br>psgicmsupport'.format(project, ip, thread, inactive_day, days)
     #   recipients = ['wei.pin.lim@intel.com']
        dmx.utillib.utils.sendmail(recipients, subject, body, cc_recipients=None, from_addr='psgicmsupport@intel.com', texttype='html')
        self.logger.info('Emails send to {}'.format(recipients))


    def get_cicq_ini_email(self, project, ip, thread):
        if os.path.exists('cicq.ini'):
            os.remove('cicq.ini')
        cicqObj = dmx.abnrlib.flows.cicqupdate.CicqUpdate(project, ip, config='', suffix=thread)
        cicqObj.download_cfgfile()
        fo = open('cicq.ini')
        for line in fo:
            line = line.rstrip()
            match = re.search('^\s*emails\s*=\s*(.*)', line)
            if match:
                return match.group(1).replace(' ','').split(',')
        fo.close()

    def run(self):
        if not dmx.utillib.admin.is_admin(self.user) and self.api.get_parameter('OWNER')!=self.user :
            raise CicqDeleteError('{} is not admin or owner of the thread. Only admin/owner is allowed to run this command'.format(self.user))

        if self.day:
            self.delete_build_by_day()
        else:
            self.api = dmx.utillib.factory_cicq_api.FactoryCicqApi(self.project, self.ip, self.thread, dryrun=self.dryrun)
            self.cleanup_cicq_job()

    def cleanup_cicq_job(self):
        # ret = api.delete_build()
        self.logger.info('Removing centralize work directory...')
        ret = self.remove_centralize_workdir()
        self.logger.info('Removing teamcity delete_build...')
        ret = self.api.delete_build()
        self.logger.info('Done')
        return ret
                        
    def remove_centralize_workdir(self):
        s = dmx.utillib.server.Server('sc')
        server = s.get_working_server()
        centralize_workdir = self.api.get_centralize_workdir()
        clientname  = self.api.get_centralize_workdir_client_name()
        dmx.utillib.utils.delete_client_as_psginfraadm(clientname)
        self.logger.info('Clientname : {}'.format(clientname))
      #  cmd = '{} {} \"arc shell project/falcon/fp8/1.0/phys/2022WW05 -- dmx workspace delete -w {} --yes-to-all; rm -rf {}\"'.format(self.api.ssh, server, clientname, centralize_workdir)
        cmd = '{} {} \"chmod 770 -R {}; rm -rf {}\"'.format(self.api.ssh, server, centralize_workdir, centralize_workdir)
        self.logger.info('Running : {}'.format(cmd))
        if not self.dryrun:
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
            if exitcode or stderr:
                self.logger.info(stdout)
                self.logger.error(stderr)
                #raise CicqDeleteError(stderr)






if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    
    project = 'i10socfm'
    variant = 'liotestfc1'
    config = 'dev'
    thread = 'test3'
    init = False
    a = CicqUpdate(project, variant, config, suffix=thread, init=init, dryrun=True)
    a.get_centralize_workdir()
    print("centralize_workdir: {}".format(a.centralize_workdir))


