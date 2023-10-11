#!/usr/bin/env python

"""
Base class of interacting with TeamCity.
Input and Output to the rest api is in XML format.

Explanation:-
-------------
- username/password OR token needs to be given.
  > username/password is user's userid/password
  > if use token(recommanded) instead, token can be generated (refer below on 'token generation' section)
- by default, the returned output format is 'xml'
  > other options: json


Example:-
---------
from dmx.utillib.teamcity_base_api import TeamcityBaseApi
from pprint import pprint
import json

a = TeamcityBaseApi(token='abcd1234xxxx', output_format='json')
ret = a.get_projects()
print a.prettyformat(ret)


Token Generation
----------------
- open up your Teamcity page
- click at your username link at the top right
- click at 'Access Token' at the left panel
- click 'Create access token'

"""
from __future__ import print_function

from builtins import str
import sys
import os
import logging
import xml.etree.ElementTree as ET
import xml.dom.minidom
import json
from pprint import pprint, pformat
import re
import datetime

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.utillib.teamcity_base_api
import dmx.utillib.utils
import dmx.utillib.server

LOGGER = logging.getLogger(__name__)

class TeamcityCicqApiError(Exception):
    pass

class TeamcityCicqApi(dmx.utillib.teamcity_base_api.TeamcityBaseApi):

    def __init__(self, project, ip, thread, dryrun=False):
        super(TeamcityCicqApi, self).__init__(
            host='https://teamcity01-fm.devtools.intel.com',
            #token = 'eyJ0eXAiOiAiVENWMiJ9.aTBEYmNvV3pKUUphakNjdUF4aUk0Sml2dkNn.NGRmYjk1NWYtOGNkZC00YTE3LWE5ODItZmM0ZDdkOTAyZjkx',   # Lionel's token
            token = 'eyJ0eXAiOiAiVENWMiJ9.QzBvMk9hUEZFci1XZUllRXNxVnlXcV92U2xJ.ZjhlYzE0M2YtZjk2Ny00MTgzLWJkZjUtMGFlN2I5MGI1ZDNk',   # psgcicq_tc's token
            output_format = 'json',
            dryrun=dryrun
        )
        self.project = project
        self.ip = ip
        self.thread = thread
        self.prefix = 'PsgCicq'
        self.parentProjectName = 'Production'
        self.parentProjectId = '{}___{}'.format(self.prefix, self.parentProjectName)
        self.templateId = 'PsgCicq_PsgBox_Cicq_CicqTemplate'
        self.projectName = self.project
        self.projectId = '{}___{}'.format(self.prefix, self.projectName)
        self.buildtypeName = '{}.{}.{}'.format(self.project, self.ip, self.thread)
        
        ### These properties are meant for replacing dots to a teamcity-compatible-character.
        self._dot = '\.'
        self._tcdot = '_DoT_'
        
        self.buildtypeId = '{}___{}___{}___{}'.format(self.prefix, self.project, self.ip, self.replace_dots_to_teamcity_compliant(self.thread))

        self.ssh = '/p/psg/da/infra/admin/setuid/tnr_ssh'
       
    def add_project(self):
        return super(TeamcityCicqApi, self).add_project(self.projectName, self.projectId, self.parentProjectId)

    def get_project(self):
        return super(TeamcityCicqApi, self).get_project(self.projectId)

    def delete_project(self):
        LOGGER.info("This command is currently not supported!")

    def add_buildtype(self):
        return super(TeamcityCicqApi, self).add_buildtype(self.buildtypeName, self.buildtypeId, self.projectId)

    def attach_template_to_buildtype(self):
        return super(TeamcityCicqApi, self).attach_template_to_buildtype(self.templateId, self.buildtypeId)

    def get_parameter(self, name):
        ret = super(TeamcityCicqApi, self).get_parameter_for_buildtype(self.buildtypeId, name)
        try:
            val = json.loads(ret)['value']
        except:
            val = ''
        return val

    def set_parameter(self, name, value):
        return super(TeamcityCicqApi, self).set_parameter_for_buildtype(self.buildtypeId, name, value)

    def run_build(self, props=None):
        return super(TeamcityCicqApi, self).run_build(self.buildtypeId, props=props)

    def setup_build(self, workdir=''):
        if not workdir:
            raise Exception("Workdir not provided. Kindly provide the workdir.")
        self.add_project()
        self.add_buildtype()
        self.attach_template_to_buildtype()
        self.set_parameter("PROJECT", self.project)
        self.set_parameter("IP", self.ip)
        self.set_parameter("THREAD", self.thread)
        self.set_parameter("OWNER", os.environ.get('USER'))
        self.set_centralize_workdir(workdir)

    def delete_build(self):
        return super(TeamcityCicqApi, self).delete_buildtype(self.buildtypeId)

    def setup_trigger(self, hour='0'):
        '''
        For Cicq, the work model is to only have 1 trigger at any one time.
        Thus, we delete all triggers, and then only add this trigger.
        '''
        self.delete_all_triggers()
        return self.add_trigger(hour)

    def delete_trigger(self, triggerId):
        return super(TeamcityCicqApi, self).delete_trigger_for_buildtype(self.buildtypeId, triggerId)

    def add_trigger(self, hour='0'):
        return super(TeamcityCicqApi, self).set_trigger_for_buildtype(self.buildtypeId, hour)

    def get_triggers(self):
        return super(TeamcityCicqApi, self).get_triggers_for_buildtype(self.buildtypeId)

    def get_triggers_id(self):
        ret = super(TeamcityCicqApi, self).get_triggers_for_buildtype(self.buildtypeId)
        jsondata = json.loads(ret)
        if jsondata['count'] == 0:
            return []
        else:
            return [x['id'] for x in jsondata['trigger']]
    
    def delete_all_triggers(self):
        for tid in self.get_triggers_id():
            self.delete_trigger(tid)

    def get_arc_resources(self):
        return self.get_parameter('ARC_RESOURCES')

    def set_arc_resources(self, value):
        return self.set_parameter('ARC_RESOURCES', value)

    def set_refbom(self, value):
        return self.set_parameter('env.CICQ_REFBOM', value)

    def get_refbom(self):
        return self.get_parameter('env.CICQ_REFBOM')

    def set_centralize_workdir(self, value):
        return self.set_parameter('CICQ_PATH', value)

    def get_centralize_workdir(self):
        ret = self.get_parameter('CICQ_PATH')
        ret = ret.replace('%PROJECT%', self.project)
        ret = ret.replace('%IP%', self.ip)
        ret = ret.replace('%THREAD%', self.thread)
        return ret

    def get_centralize_workdir_client_name(self):
        icmconfig = '{}/cicq/workspace/{}___{}___cicq_integration_{}/.icmconfig'.format(self.get_centralize_workdir(), self.project, self.ip, self.thread)
        cmd = 'cat {} | head -n 1 | awk -F= \'{{print $2}}\' '.format(icmconfig)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        ret = stdout.rstrip()
        return ret

    def replace_dots_to_teamcity_compliant(self, text):
        return re.sub(self._dot, self._tcdot, text)

    def reverse_replace_dots_to_teamcity_compliant(self, text):
        return re.sub(self._tcdot, '.', text)

    def get_all_projects_id(self):
        ret = super(TeamcityCicqApi, self).get_project(self.parentProjectId)
        jsondata = json.loads(ret)
        retlist = []
        for project in jsondata['projects']['project']:
            retlist.append(project['id'])
        return retlist

    def get_all_buildtypes_id(self):
        return [x['id'] for x in self.get_all_buildtypes()]

    def get_all_buildtypes(self):
        ret = super(TeamcityCicqApi, self).get_buildtypes()
        jsondata = json.loads(ret)
        retlist = []
        for bt in jsondata['buildType']:
            if bt['projectId'].startswith('{}___'.format(self.prefix)) and bt['id'].startswith('{}___'.format(bt['projectId'])):
                retlist.append(bt)
        return retlist

    def get_buildtype_by_thread(self, thread):
        all_buildtypes = self.get_all_buildtypes()
        for bt in all_buildtypes:
            _prefix, _project, _ip, _thread = self.decompose_buildtype_id(bt['id'])
            if _thread == thread:
                return bt
        return None

    def get_all_threads_name(self, teamcity_compliant=True):
        retlist = []
        buildtypes_id = self.get_all_buildtypes_id()
        for btid in buildtypes_id:
            prefix, project, ip, thread = self.decompose_buildtype_id(btid)
            if not teamcity_compliant:
                thread = self.reverse_replace_dots_to_teamcity_compliant(thread)
            retlist.append(thread)
        return retlist

    def get_current_running_build(self):
        ret = super(TeamcityCicqApi, self).get_current_running_build_for_buildtype(self.buildtypeId)
        jsondata = json.loads(ret)
        return jsondata

    def get_current_queued_build(self):
        ret = super(TeamcityCicqApi, self).get_current_queued_build_for_buildtype(self.buildtypeId)
        jsondata = json.loads(ret)
        return jsondata

    def get_current_running_build_agent(self):
        build = self.get_current_running_build()
        buildid = build['build'][0]['id']
        ret = self.get_build(buildid)
        jsondata = json.loads(ret)
        agentId = jsondata['agent']['id']
        ret = self.get_agent(agentId)
        jsondata = json.loads(ret)
        return jsondata

    def get_current_running_build_agent_homedir(self):
        data = self.get_current_running_build_agent()
        prop = data['properties']['property']
        for p in prop:
            if 'name' in p and p['name'] == 'system.agent.home.dir':
                return p['value']
        return ''

    def get_current_running_build_num(self):
        data = self.get_current_running_build()
        return data['build'][0]['number']

    def get_current_running_build_arc_job_id(self):
        '''
        This API meant to workaround the issue of the older API:
            get_current_running_build_arc_job_id___old 
        (Please see docs of old API for details)
        
        This API does:-
        - look for the current running build id
        - look for the agent that runs this build
        - look for the agent's homedir
        - extract out the arcjobid from the agent's homedir's log
        '''
        homedir = self.get_current_running_build_agent_homedir()
        return self.get_last_arc_job_id_from_agent_homedir(homedir)

    def get_agent_last_arc_job_id(self, agentid):
        homedir = self.get_agent_homedir(agentid)
        return self.get_last_arc_job_id_from_agent_homedir(homedir)
    
    def get_agent_arc_job_id_for_buildid(self, agentid, buildid):
        homedir = self.get_agent_homedir(agentid)
        return self.get_arc_job_id_for_buildid_from_agent_homedir(homedir, buildid)
    
    def get_arc_job_id_for_buildid_from_agent_homedir(self, agent_home_dir, buildid, site='sc'):
        s = dmx.utillib.server.Server(site)
        server = s.get_working_server()
        agentlog = os.path.join(agent_home_dir, 'logs', 'teamcity-build.log')
        cmd = ''' {} {} -q 'cat {}' '''.format('ssh', server, agentlog)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        LOGGER.debug("Running: {}".format(cmd))
        LOGGER.debug('exitcode: {}\nstdout: {}\nstderr: {}\n'.format(exitcode, stdout, stderr))
        '''
        stdout: 
        [2021-09-08 17:00:08,242]   INFO - ----------------------------------------- [ Step 'Command Line' (simpleRunner), Build "i10socfm / i10socfm.fmio12pnr_serdesdpa_top.FM6revB0" #372 {id=19695003, buildTypeId='PsgCicq___i10socfm___fmio12pnr_serdesdpa_top___FM6revB0'} ] -----------------------------------------
        '''
        
        pattern1 = '----- \[ Step .* {{id={}, '.format(buildid)
        pattern2 = 'Waiting on ARC job to complete: (\d+)'
        start = False
        end = False
        for line in stdout.split('\n'):
            match = re.search(pattern1, line)
            if match:
                if not start:
                    start = True
                else:
                    ### We can't seem to find the arcjobid(can't find matching line of pattern2)
                    ### Thus, return ''
                    end = True
                    return ''
            elif start and not end:
                m = re.search(pattern2, line)
                if m:
                    arcjobid = m.group(1)
                    end = True
                    return arcjobid

    def get_last_arc_job_id_from_agent_homedir(self, agent_home_dir, site='sc'):
        s = dmx.utillib.server.Server(site)
        server = s.get_working_server()
        agentlog = os.path.join(agent_home_dir, 'logs', 'teamcity-build.log')
        lookupstr = "Waiting on ARC job to complete:"
        cmd = ''' {} {} -q 'grep "{}" {} | tail -1' '''.format('ssh', server, lookupstr, agentlog)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        if lookupstr in stdout:
            return stdout.split('complete: ')[-1].strip()
        else:
            return ''

    def get_build_arc_job_id(self, buildId):
        try:
            stdout = self.download_buildlog_by_id(buildId)
            m = re.search("Waiting on ARC job to complete: (\d+)", stdout)
            arcjobid = m.group(1)
            return arcjobid
        except Exception as e:
            LOGGER.debug("Problem getting running job id. {}".format(str(e)))
            return None


    def get_current_running_build_arc_job_id___old(self):
        '''
        This API downloads the Build Log from teamcity.
        The problem with this is when teamcity host is having high load, 
        the Teamcity's BuildLog is not updated live, and thus, no data is gotten.
        
        We now have a new API of achieving this. Please look into:
            get_current_running_build_arc_job_id()
        '''
        try:
            data = self.get_current_running_build()
            stdout = self.download_buildlog_by_id(data['build'][0]['id'])
            m = re.search("Waiting on ARC job to complete: (\d+)", stdout)
            arcjobid = m.group(1)
            return arcjobid
        except Exception as e:
            LOGGER.debug("Problem getting running job id. {}".format(str(e)))
            return None

    def decompose_buildtype_id(self, btid=None):
        if not btid:
            btid = self.buildtypeId
        r_btid = self.reverse_replace_dots_to_teamcity_compliant(btid)
        ret = r_btid.split('___', 3)
        return ret  # ret = [prefix, project, ip, thread]

    def get_latest_build(self):
        ret = super(TeamcityCicqApi, self).get_latest_build_for_buildtype(self.buildtypeId)
        jsondata = json.loads(ret)
        return jsondata
    
    def get_latest_build_datetime(self):
        ret = super(TeamcityCicqApi, self).get_latest_build_for_buildtype(self.buildtypeId)
        jsondata = json.loads(ret)
        fmt = '%Y%m%dT%H%M%S'
        dtstr = jsondata['startDate'][:-5]  # dtstr = 20200818T012445-0700
        return datetime.datetime.strptime(dtstr, fmt)

    def __repr__(self):
        return '{}/{}/{}'.format(self.project, self.ip, self.thread)

    def get_build_num_from_arc(self):
        api = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(project, ip, thread, dryrun=False)

        all_builds = self.get_all_builds()
        all_builds =  json.loads(all_builds)
        all_build = all_builds['build']
        #print len(all_build)
        project = ''
        ip = ''
        thread = ''
        for build in all_build:
            buildId = build['id']
            buildTypeId = build['buildTypeId']
            if 'AgentRefresh' in buildTypeId: continue
            ret = self.get_build(buildId)
            builds =  json.loads(ret)
            bnum = builds['number']
            for ea_prop in  builds['properties']['property']:
                if ea_prop['name'] == 'PROJECT':
                    project = ea_prop['value']
                if ea_prop['name'] == 'IP':
                    ip = ea_prop['value']
                if ea_prop['name'] == 'THREAD':
                    thread = ea_prop['value']
        
            #if builds['startDate'].startswith('202110'):
            arc_job =  self.get_build_arc_job_id(build['id'])
        
if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

    p = 'i10socfm'
    i = 'liotestfc1'
    t = 'test3'
    a = TeamcityCicqApi(p, i, t)
    #a.set_centralize_workdir('/nfs/site/disks/psg_cicq_2/users/cicq/{}.{}.{}'.format(p, i, t))
    print(a.get_centralize_workdir())



