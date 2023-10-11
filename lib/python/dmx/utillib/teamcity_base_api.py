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

from builtins import object
import sys
import os
import logging
import xml.etree.ElementTree as ET
import xml.dom.minidom
import json

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.utillib.utils
from datetime import datetime

LOGGER = logging.getLogger(__name__)

class TeamcityBaseApiError(Exception):
    pass

class TeamcityBaseApi(object):

    def __init__(self, host, username='', password='', token='', version='2018.1', output_format='xml', dryrun=False):
        self.host = host
        self.username = username
        self.password = password
        self.token = token
        self.version = version
        self.output_format = output_format
        self.dryrun = dryrun

    def get_projects(self):
        request = 'projects'
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_project(self, projectId):
        request = 'projects/id:{}'.format(projectId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def delete_project(self, projectId):
        request = 'projects/id:{}'.format(projectId)
        cmd = self.get_curl_cmd(request, delete=True)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def add_project(self, name, projectId, parentProjectId):
        request = 'projects'
        databinary = '<newProjectDescription id="{}" name="{}"><parentProject locator="id:{}" /></newProjectDescription>'.format(
            projectId, name, parentProjectId)
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_buildtypes(self, count=1000, day=None):
        request = 'buildTypes?locator=count:{}'.format(1000)
        if day:
            today = datetime.today().strftime('%Y-%m-%d')
            today = datetime.now()    
            n_days_ago = (today - timedelta(days=days)).strftime('%Y%m%d')
            sinceDate = '{}T000000EDT'.format(n_days_ago)
            request = 'buildTypes?locator={},count:{}'.format(sinceDate, 1000000)
       # request = 'builds?locator=buildTypes/id:{}'.format(count)
      #  request = 'builds?locator=sinceDate:20211001T000000EDTi,count:100000000'
        #request = 'builds/?locator=property:(name:IP,value:acr_barak2_quad)'
    
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def get_buildtypes_by_project_id(self, projectId, count=1000):
        request = 'buildTypes?locator=affectedProject:(id:{}),count:{}'.format(projectId, count)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def get_buildtype(self, buildtypeId):
        request = 'buildTypes/id:{}'.format(buildtypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def get_build(self, buildId):
        request = 'builds/id:{}'.format(buildId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def get_success_build_for_buildtype(self, buildTypeId):
        request = 'buildTypes/id:{}/builds?locator=status:SUCCESS'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_failed_build_for_buildtype(self, buildTypeId):
        request = 'buildTypes/id:{}/builds?locator=status:FAILURE'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_all_build_for_buildtype(self, buildTypeId):
        request = 'buildTypes/id:{}/builds?'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_all_builds(self, count=1000):
        request = 'builds?locator=count:{}'.format(count)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_all_builds_for_days(self, days=None, count=100000000):
        today = datetime.today().strftime('%Y-%m-%d')
        today = datetime.now()    
        n_days_ago = (today - timedelta(days=days)).strftime('%Y%m%d')
        sinceDate = '{}T000000EDT'.format(n_days_ago)
    
    def get_agent(self, agentId):
        request = 'agents/id:{}'.format(agentId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def get_agentid_for_build(self, buildId):
        data = self.get_build(buildId)
        buildjson = json.loads(data)
        agentid = buildjson['agent']['id']
        return agentid

    def get_agent_homedir(self, agentId):
        data = json.loads(self.get_agent(agentId))
        prop = data['properties']['property']
        for p in prop:
            if 'name' in p and p['name'] == 'system.agent.home.dir':
                return p['value']
        return ''

    def add_buildtype(self, name, buildtypeId, projectId):
        request = 'buildTypes'
        databinary = '<buildType id="{}" name="{}" projectId="{}"></buildType>'.format(buildtypeId, name, projectId)
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)

    def delete_buildtype(self, buildtypeId):
        request = 'buildTypes/id:{}'.format(buildtypeId)
        cmd = self.get_curl_cmd(request, delete=True)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def add_buildtype_with_template_and_param(self, name, selfId, projectId):
        '''
        This method is left here just for reference purpose. It is here to show that
        there is indeed a way possible to send a single rest api call which will do
        all the followings, in one single call:-
        - build a new buildType under a project
        - attach a template to the buildType
        - set parameters values
        - and of course others ......
        '''
        request = 'buildTypes'.format(projectId)
        databinary = '''
        <buildType id="{}" name="{}" projectId="{}">
            <templates>
                <buildType id="PsgCicq_PsgBox_Cicq_CicqTemplate"/>
            </templates>
            <parameters>
                <property name="IP" value="liotestfc1"/>
                <property name="PROJECT" value="i10socfm"/>
                <property name="THREAD" value="test99"/>
            </parameters>
        </buildType> '''.format(selfId, name, projectId)
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)

    def get_agent_requirements_for_buildtype(self, buildtypeId):
        request = 'buildTypes/id:{}/agent-requirements/'.format(buildtypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout

    def add_agent_requirement_for_buildtype(self, buildtypeId, value, operator='equals'):
        request = 'buildTypes/id:{}/agent-requirements/'.format(buildtypeId)
        databinary = '''
        <agent-requirement type="{}">
            <properties count="2">
              <property name="property-name" value="system.agent.name"/>
              <property name="property-value" value="{}"/>
            </properties>
        </agent-requirement>'''.format(operator, value) 
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        return stdout


    def get_parameters_for_buildtype(self, buildTypeId):
        request = 'buildTypes/id:{}/parameters'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout
    
    def get_parameter_for_buildtype(self, buildTypeId, name):
        request = 'buildTypes/id:{}/parameters/{}'.format(buildTypeId, name)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout
    
    def set_parameter_for_buildtype(self, buildTypeId, name, value):
        request = 'buildTypes/id:{}/parameters'.format(buildTypeId, name)
        databinary = '<property name="{}" value="{}"/>'.format(name, value)
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout
    
    def attach_template_to_buildtype(self, templateId, buildTypeId):
        request = 'buildTypes/id:{}/templates'.format(buildTypeId)
        databinary = '<buildType id="{}"></buildType>'.format(templateId)
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def run_build(self, buildTypeId, props=None):
        '''
        if you wanna run the build overriding the default properties, then use the `props`.
        `props` is a dict, with key:value pair.
        '''
        request = 'buildQueue'.format(buildTypeId)
        maintag = '<buildType id="{}"/>'.format(buildTypeId)
        proptag = ''
        if props:
            for key, val in props.items():
                proptag += '<property name="{}" value="{}"/>'.format(key, val)
            proptag = '<properties>' + proptag + '</properties>'
            maintag += proptag

        databinary = '<build>' + maintag + '</build>'
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_triggers_for_buildtype(self, buildTypeId):
        request = 'buildTypes/id:{}/triggers'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def set_trigger_for_buildtype(self, buildTypeId, hour='0'):
        request = 'buildTypes/id:{}/triggers'.format(buildTypeId)
        databinary = '''<trigger type="schedulingTrigger">
            <properties>
                <property name="cronExpression_dm" value="*"/>
                <property name="cronExpression_dw" value="?"/>
                <property name="cronExpression_hour" value="*"/>
                <property name="cronExpression_min" value="0"/>
                <property name="cronExpression_month" value="*"/>
                <property name="cronExpression_sec" value="0"/>
                <property name="cronExpression_year" value="*"/>
                <property name="dayOfWeek" value="Sunday"/>
                <property name="enableQueueOptimization" value="true"/>
                <property name="hour" value="{}"/>
                <property name="minute" value="0"/>
                <property name="promoteWatchedBuild" value="true"/>
                <property name="revisionRule" value="lastFinished"/>
                <property name="revisionRuleBuildBranch" value="&lt;default&gt;"/>
                <property name="schedulingPolicy" value="daily"/>
                <property name="timezone" value="SERVER"/>
                <property name="triggerBuildWithPendingChangesOnly" value="true"/>
            </properties>
        </trigger>'''.format(hour)
        databinary = '''<trigger type="schedulingTrigger">
            <properties>
                <property name="hour" value="{}"/>
                <property name="minute" value="0"/>
                <property name="schedulingPolicy" value="daily"/>
                <property name="timezone" value="US/Pacific"/>
            </properties>
        </trigger>'''.format(hour)
        cmd = self.get_curl_cmd(request, databinary)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def delete_trigger_for_buildtype(self, buildTypeId, triggerId):
        request = 'buildTypes/id:{}/triggers/{}'.format(buildTypeId, triggerId)
        cmd = self.get_curl_cmd(request, delete=True)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_current_running_builds(self):
        request = 'builds?locator=running:true'
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def download_artifact_by_buildid(self, buildid, path):
        '''
        here's how to find the <path>
        - https://<teamcity-host>/app/rest/builds/<build-id>/artifacts
            > this will show u a list of available artifacts, and the children href.
        - https://<teamcity-host>/<children-href> -or- https://<teamcity-host>/app/rest/builds/<build-id>/children/<folder>
            > this will show u the <content-href>
        - https://<teamcity-host>/<content-href> -or- https://<teamcity-host>/app/rest/builds/<build-id>/content/<path>
            > this will download the artifact 

        ex:-
            https://<teamcity-host>/app/rest/builds/id:20263168/artifacts/content/email_notification.html/email_notification.html
            path == 'email_notification.html/email_notification.html'
        '''
        request = 'builds/{}/artifacts/content/{}'.format(buildid, path)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def download_buildlog_by_id(self, buildid):
        # https://teamcity01-fm.devtools.intel.com/downloadBuildLog.html?buildId=18639950
        request = self.host + '/downloadBuildLog.html?buildId={}'.format(buildid)
        cmd = self.get_curl_cmd(request, raw_request=True)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_current_running_build_for_buildtype(self, buildTypeId):
        request = 'builds?locator=running:true,buildType:{}'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_current_queued_build_for_buildtype(self, buildTypeId):
        request = 'buildQueue?locator=buildType:{}'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_latest_build_for_buildtype(self, buildTypeId):
        request = 'builds/buildType:id:{},lookupLimit:1'.format(buildTypeId)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_latest_artifact_for_buildtype(self, buildTypeId, filepath):
        request = 'builds/buildType:id:{}/artifacts/content/{}'.format(buildTypeId, filepath)
        cmd = self.get_curl_cmd(request)
        exitcode, stdout, stderr = self.run_command(cmd)
        self.report_run_command(exitcode, stdout, stderr)
        return stdout

    def get_curl_cmd(self, request, databinary='', delete=False, raw_request=False):
        finalcmd = "env -i curl --basic -H 'Content-Type: application/xml' -H 'Accept: application/{}' -H 'Origin: {}'".format(self.output_format, self.host)
        if self.token:
            finalcmd += " -H 'Authorization: Bearer {}'".format(self.token)
        elif self.username and self.password:
            finalcmd += " --user '{}:{}'".format(self.username, self.password)
        else:
            raise TeamcityBaseApiError("Either TOKEN or (USERNAME:PASSWORD) needs to be specified.")
        if databinary:
            finalcmd += ' --data-binary {}'.format(dmx.utillib.utils.quotify(databinary))
        if delete:
            finalcmd += ' --request DELETE'
        if not raw_request:
            finalcmd += ' {}'.format(dmx.utillib.utils.quotify(self.get_request_url(request)))
        else:
            finalcmd += ' {}'.format(dmx.utillib.utils.quotify(request))

        LOGGER.debug("finalcmd: {}".format(finalcmd))
        return finalcmd

    def get_request_url(self, request):
        url = self.host + '/app/rest'
        if self.version:
            url += '/{}'.format(self.version)
        url += '/{}'.format(request)
        return url

    def report_run_command(self, exitcode, stdout, stderr):
        LOGGER.debug("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcode, stdout, stderr))


    def prettyformat(self, text):
        if self.output_format == 'xml':
            dom = xml.dom.minidom.parseString(text)
            return dom.toprettyxml()
        elif self.output_format == 'json':
            return json.dumps(json.loads(text), indent=4)
        else:
            return text

    def run_command(self, cmd):
        if self.dryrun:
            return [0, '{"dryrun": "True"}', "NOTHING HAPPENED: cmd: {}".format(cmd)]
        else:
            return dmx.utillib.utils.run_command(cmd)

if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.INFO)
   



