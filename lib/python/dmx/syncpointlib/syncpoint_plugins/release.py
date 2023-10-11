#!/usr/bin/env python
'''
Description: plugin for "syncpoint add"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
from builtins import str
from builtins import input
import sys
import os
import pwd
import textwrap
import logging
import getpass
import datetime
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pprint import pprint, pformat

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, LIB)

import dmx.utillib.user
import dmx.syncpointlib.syncpointlock_api
from dmx.abnrlib.command import Command, Runner
#why do we use this? why not dmx.abnrlib.icmcompositeconfig.py?
#the effort to move to icmcompositeconfig is significantly higher, to explore in the future
from dmx.syncpointlib.composite_configs import CompositeConfigHierarchy
from dmx.abnrlib.icm import ICManageCLI
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
from dmx.syncpointlib.syncpoint_plugins.check import CheckConflict
from dmx.utillib.utils import get_altera_userid
import dmx.abnrlib.flows.checkconfigs

EMAIL_TEMPLATES = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"email_templates"))
ACCESS_LEVEL = {
                'admin' :1,
                'fclead':2,
                'sslead':3,
                'owner' :4,
                'user' :5,             
               }

class ReleaseError(Exception): pass

class ReleaseRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, syncpoint, project, variant, config, yes, nocheck, debug):
        self.user = get_altera_userid(os.getenv('USER'))
        self.syncpoint = syncpoint
        self.project = project
        self.variant = variant
        self.config = config
        self.yes = yes
        self.nocheck = nocheck        
        self.debug = debug
        self.sp = SyncpointWebAPI()
        self.icm = ICManageCLI()
                
        dmx.syncpointlib.syncpointlock_api.SyncpointLockApi().connect().raise_error_if_syncpoint_is_locked(self.syncpoint)

        #check if syncpoint exists
        if not self.sp.syncpoint_exists(syncpoint):
            raise ReleaseError("Syncpoint {0} does not exist".format(self.syncpoint))
             
        #check if project/variant/config exists  
        if not self.icm.config_exists(project, variant, config):
            if not self.icm.variant_exists(self.project, self.variant):
                if not self.icm.project_exists(self.project):
                    raise ReleaseError('Project {0} does not exist'.format(self.project))
                else:
                    raise ReleaseError('Variant {0} does not exist in project {1}'.format(self.variant, self.project))
            else:
                raise ReleaseError('Config {0} does not exist in project/variant {1}/{2}'.format(self.config, self.project, self.variant))

        #check if configuration is a REL or snap or PREL
        if not self.config.startswith('REL') and not self.config.startswith('snap') and not self.config.startswith('PREL'):
            raise ReleaseError("Config {0} is not a REL/PREL/snap configuration".format(self.config))

        #check if project/variant already in the given syncpoint
        if not self.sp.project_variant_exists(self.syncpoint, self.project, self.variant):
            raise ReleaseError("Project/Variant {0}/{1} does not exist for syncpoint {2}".format(self.project, self.variant,self.syncpoint))

        #get user's access level
        user_roles = self.sp.get_user_roles(self.user)       
        self.user_highest_access_level = ACCESS_LEVEL['user']
        for user_role in user_roles:
            if self.user_highest_access_level >= ACCESS_LEVEL[user_role]:
                self.user_highest_access_level = ACCESS_LEVEL[user_role]

        #check if user has permission to release a project/variant
        #anyone except 'user' may release a project/variant, user access level is 5
        if not self.user_highest_access_level <= ACCESS_LEVEL['owner']:
            raise ReleaseError("You do not have permission to release a project/variant.\nOnly owner, sslead and fclead may perform release on a project/variant")

        #check syncpoint has any conflict in its configuration tree
        checkconflict = CheckConflict(self.syncpoint)                
        if checkconflict.get_list_of_conflicts():
            if not self.nocheck:
                raise ReleaseError("Syncpoint {0} has configuration conflicts, please run syncpoint check first".format(self.syncpoint))                         


        cc = dmx.abnrlib.flows.checkconfigs.CheckConfigs(project=self.project, variant=self.variant, config=self.config, syncpoints=[self.syncpoint])
        self.conflicts = cc.run()
        if self.conflicts and not self.nocheck:
            self.LOGGER.error("Conflicts found ! Program aborted")
            self.LOGGER.error(pformat(self.conflicts))
            raise ReleaseError("{0}/{1}@{2} conflicts with configurations in syncpoint {3}. Release aborted.".format(self.project,self.variant,self.config,self.syncpoint))            


    def run(self):
        ret = 1
        releaser_fname = pwd.getpwuid(os.getuid())[4]
        #check if project/variant has been released before
        if self.sp.project_variant_released(self.syncpoint, self.project, self.variant):
            cfg = self.get_release_of_project_variant(self.syncpoint, self.project, self.variant)
            self.LOGGER.warning("Syncpoint/Project/Variant {0}/{1}/{2} has been released with {3}".format(self.syncpoint, self.project, self.variant, cfg))
            #check if current user is an owner
            #only fclead, sslead may re-release a released variant
            if not self.user_highest_access_level <= ACCESS_LEVEL['sslead']:
                #errors out if user is not a syncpoint lead
                raise ReleaseError("You do not have permission to re-release a released project/variant.\nOnly sslead and fclead may perform re-release on a released project/variant.")
            
            #ask for user confirmation to re-release
            if self.yes:
                ans = 'y'
            else:
                self.LOGGER.warning("Are you sure you would like to re-release?")
                ans = ""
                while ans != 'y' and ans != 'n':
                    ans = input("(y/n)?")

            if ans.lower() == 'n':
                raise ReleaseError("Release aborted")

            #build email body for automated release notification
            subject = "{0}/{1}@{2} updated to syncpoint {3}".format(self.project, self.variant, self.config, self.syncpoint)
            body = ""
            if not self.conflicts:
                body = "This is an automated notification from syncpoint. <br>" \
                       "{0}/{1}@{2} has been updated by {4} to syncpoint {3} <br>" \
                       "Please update your IP or IP subsystem configuration if needed" \
                       .format(self.project, self.variant, self.config, self.syncpoint, releaser_fname)
            else:
                body = "This is an automated notification from syncpoint. <br>" \
                       "{0}/{1}@{2} has been updated by {4} to syncpoint {3} <br>" \
                       "<br>" \
                       "This release was made with no-check switch, the conflicts are as below: <br>" \
                       "<table><tr><th rowspan=\"2\">Project</th><th rowspan=\"2\">Variant</th><th>Config Conflict 1</th><th>Config Conflict 2</th></tr><tr><th>Parent Config 1</th><th>Parent Config 2</th></tr>" \
                       .format(self.project, self.variant, self.config, self.syncpoint, releaser_fname)
                dict = {}                       
                for conflict in self.conflicts:
                    (psp,psv,psc),(csp,csv,csc) = conflict['src']
                    (pdp,pdv,pdc),(cdp,cdv,cdc) = conflict['dest']
                    if csp not in dict:
                        dict[csp] = {}
                    if csv not in dict[csp]:
                        dict[csp][csv] = []
                    dict[csp][csv].append([csc,psp,psv,psc,cdc,pdp,pdv,pdc])
                for p in dict:
                    for v in dict[p]:
                        for c1,pp1,pv1,pc1,c2,pp2,pv2,pc2 in dict[p][v]:
                            body = "{0}<tr><td rowspan=\"2\">{1}</td><td rowspan=\"2\">{2}</td><td>{3}</td><td>{4}</td></tr><tr><td>{5}/{6}/{7}</td><td>{8}/{9}/{10}</td></tr>".format(body,p,v,c1,c2,pp1,pv1,pc1,pp2,pv2,pc2)
                body = "{0}</table><br> Please update your IP or IP subsystem configuration if needed" \
                .format(body)
        else:
            subject = "{0}/{1}@{2} released to syncpoint {3}".format(self.project, self.variant, self.config, self.syncpoint)
            body = ""
            if not self.conflicts:
                body = "This is an automated notification from syncpoint. <br>" \
                       "{0}/{1}@{2} has been released by {4} to syncpoint {3} <br>" \
                       .format(self.project, self.variant, self.config, self.syncpoint, releaser_fname)
            else:
                body = "This is an automated notification from syncpoint. <br>" \
                       "{0}/{1}@{2} has been released by {4} to syncpoint {3} <br>" \
                       "<br>" \
                       "This release was made with no-check switch, the conflicts are as below: <br>" \
                       "<table><tr><th rowspan=\"2\">Project</th><th rowspan=\"2\">Variant</th><th>Config Conflict 1</th><th>Config Conflict 2</th></tr><tr><th>Parent Config 1</th><th>Parent Config 2</th></tr>" \
                       .format(self.project, self.variant, self.config, self.syncpoint, releaser_fname)
                dict = {}                       
                for conflict in self.conflicts:
                    (psp,psv,psc),(csp,csv,csc) = conflict['src']
                    (pdp,pdv,pdc),(cdp,cdv,cdc) = conflict['dest']
                    if csp not in dict:
                        dict[csp] = {}
                    if csv not in dict[csp]:
                        dict[csp][csv] = []
                    dict[csp][csv].append([csc,psp,psv,psc,cdc,pdp,pdv,pdc])
                for p in dict:
                    for v in dict[p]:
                        for c1,pp1,pv1,pc1,c2,pp2,pv2,pc2 in dict[p][v]:
                            body = "{0}<tr><td rowspan=\"2\">{1}</td><td rowspan=\"2\">{2}</td><td>{3}</td><td>{4}</td></tr><tr><td>{5}/{6}/{7}</td><td>{8}/{9}/{10}</td></tr>".format(body,p,v,c1,c2,pp1,pv1,pc1,pp2,pv2,pc2)
                body = "{0}</table>".format(body)                                

        ### Added link to Release Notes 
        ### http://pg-rdjira:8080/browse/DI-1172
        url = 'https://psg-sc-arc.sc.intel.com/p/psg/data/psginfraadm/catalogs/fm/rel/tnt_shared/REL3.0FM8revA0/REL3.0FM8revA0__17ww342a/relnote.html'
        body += '<br><br><br>'
        body += 'Release Catalog:<br>'
        body += '<a href="{}">link</a>'.format(self.get_release_catalog_link(self.project, self.variant, self.config))
        body += '<br><br><br>'




        #release project/variant/config
        ret = self.sp.release_syncpoint(self.syncpoint, self.project, self.variant, self.config, self.user)
        if not ret:
            #only send to admin in debugging mode
            if self.debug:                
                #get users with 'admin' role
                users = self.sp.get_users_by_role('admin')
            else:
                #get users with 'user' role
                users = self.sp.get_users_by_role('user')

            #users_email = self.get_users_email_by_userid(users)

            from_addr = "Automated.Syncpoint.Notification@altera.com"
            #send emails to user in 'user' list
            if self.send_email(users, subject, body, from_addr):
                self.LOGGER.info("{0}/{1}@{2} has been successfully released to syncpoint {3}".format(self.project, self.variant, self.config, self.syncpoint))
            else:
                msg = "Syncpoint release has encountered error sending mail notifications.\n" \
                      "To: {0}\n"\
                      "Subject: {1}\n"\
                      "Body: {2}\n"\
                      .format(users, subject,body)
                raise ReleaseError(msg)

        return ret


    def get_users_email_by_userid(self, userids):
        ''' ignore invalid users '''
        retlist = []
        for userid in userids:
            try:
                u = dmx.utillib.user.User(userid)
                email = u.get_email()
                if email:
                    retlist.append(email)
            except Exception as e:
                self.LOGGER.error(str(e))

        return retlist






    def get_release_catalog_link(self, project, variant, config):
        '''
        Returns the release catalog link 
        '''
        url = 'http://psg-sc-arc.sc.intel.com/p/psg/data/psginfraadm/catalogs/fm/rel/{}/{}/{}/relnote.html'.format(
            variant, self.get_thread_of_integration(config), config)
        return url


    def get_thread_of_integration(self, config):
        '''
        Return the thread-of-integration from a configuration.

        config == 'REL1.0FM8revA0--RTL--abc__17ww123a'
        return == 'REL1.0FM8revA0--RTL--abc'
        '''
        return re.sub('__\d\dww\d\d\d[a-z]$', '', config)


    def get_release_of_project_variant(self, syncpoint, project, variant):
        '''
        Returns configuration associated with the given syncpoint/project/variant
        '''
        results = self.sp.get_releases_from_syncpoint(syncpoint)
        results.sort()
        
        for (p,v,c) in results:
            if p == project and v == variant:
                return str(c)

    def send_email(self, recipients, subject, body, from_addr):
        COMMASPACE = ', '
        sender = 'Automated.Syncpoint.Notification@altera.com'
        to = []
        fqdn = '@intel.com'
        for r in recipients:
            if fqdn  not in r:
                to.append(r + fqdn)
        to = recipients

        html = """
                <html>
                <body><pre><code>{}</code></pre></body>
            </html>
            """ .format(body)

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = COMMASPACE.join(to)
        
        textPart = MIMEText(html, 'html')
        msg.attach(textPart)   
        
        self.LOGGER.info("Sending email notification with following data: \n{}".format(pformat(msg)))

        s = smtplib.SMTP('localhost')
        s.sendmail(sender, to, msg.as_string())
        s.quit()
        return True


class Release(Command):
    '''plugin for "syncpoint release"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint release"'''
        return 'Associate a release configuration with the given syncpoint/project/variant'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint release command associates a given release configuration with the given syncpoint/project/variant. In other words, user 'releases' a particular release to a milestone.
            Any user may perform release command, however, once a project/variant has been released, it cannot be released again by users other than leads. Only syncpoint leads may re-release a released project/variant.
            Everytime a release happens, each user defined with 'user' role will receive a notification from syncpoint.
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
           
            Usage
            =====
            syncpoint release -s <syncpoint> -p <project> -v <variant> -c <release configuration>
            Release a new release configuration to syncpoint/project/variant
            
            Example
            =====
            syncpoint release -s MS1.0 -p i14socnd -v ar_lib -c REL3.0aaa
            Releases REL3.0aaa to MS1.0/i14socnd/ar_lib
            ...
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint release" subcommand'''
        parser.add_argument('-s', '--syncpoint', metavar='syncpoint',required=True,
            help='Syncpoint to be released to')
        parser.add_argument('-p', '--project', metavar='project', required=True,
            help='Project to be released to')
        parser.add_argument('-v', '--variant', metavar='variant', required=True,
            help='Variant to be released to')
        parser.add_argument('-c', '--release-configuration', metavar='release-configuration', required=True,
            help='Release configuration to be released')
        parser.add_argument('-y', '--yes', action='store_true',
            help='Yes to re-release confirmation')
        parser.add_argument('-nc', '--nocheck', action='store_true',
            help='No check switch to force syncpoint to release a conflicting configuration')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint release command'''

        syncpoint = args.syncpoint
        project = args.project
        variant = args.variant
        config = args.release_configuration       
        yes = args.yes
        nocheck = args.nocheck
        debug = args.debug
            
        ret = 1
        runner = ReleaseRunner(syncpoint, project, variant, config, yes, nocheck, debug)
        ret = runner.run()

        sys.exit(ret)


        

                


