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
import tempfile
import re

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.utillib.jenkins_base_api
import dmx.utillib.utils
import dmx.utillib.server

LOGGER = logging.getLogger(__name__)

class JenkinsCicqApiError(Exception):
    pass

class JenkinsCicqApi(dmx.utillib.jenkins_base_api.JenkinsBaseApi):

    def __init__(self, project, ip, thread, dryrun=False):
        super(JenkinsCicqApi, self).__init__()
        self.project = project
        self.ip = ip
        self.thread = thread
        self.jobName = '{}.{}.{}'.format(self.project, self.ip, self.thread)
        self.buildtypeId = self.jobName # for backward compatibility

        self._job_tree = None
        self._job_filepath = None

        self.ssh = '/p/psg/da/infra/admin/setuid/tnr_ssh'
      
    def get_parameter(self, name: str):
        tree, xmlfile = self.get_job()
        return self.get_elementtree_param(tree, name)
        
    def set_parameter(self, name: str, value: str):
        tree, xmlfilepath = self.get_job()
        newtree = self.update_elementtree_param(tree, name, value)
        _, tmpfile = tempfile.mkstemp()
        newtree.write(tmpfile)
        self.update_job(self.jobName, tmpfile)
        self._job_tree = newtree
        self._job_filepath = tmpfile
        
    def run_job(self, props: dict=None, follow_console_output=False):
        return self.build(self.jobName, params=props, follow_console_output=follow_console_output)

    def setup(self, workdir: str=''):
        if not workdir:
            raise Exception("Workdir not provided. Kindly provide the workdir.")
        self.create_job(workdir=workdir)
        self.create_view()
        self.add_job_to_view(self.jobName, self.project)

    def create_view(self):
        tree, tmpfile = self.get_view('template')
        super(JenkinsCicqApi, self).create_view(self.project, tmpfile)

    def delete_job(self):
        return super(JenkinsCicqApi, self).delete_job(self.jobName)

    def get_job(self) -> [ET, str]:
        if not self._job_tree:
            self._job_tree, self._job_filepath = super(JenkinsCicqApi, self).get_job(self.jobName)
        return [self._job_tree, self._job_filepath]
    
    def create_job(self, workdir: str):
        self.copy_job('template', self.jobName)
        self.set_parameter("CICQ_PROJECT", self.project)
        self.set_parameter("CICQ_IP", self.ip)
        self.set_parameter("CICQ_THREAD", self.thread)
        self.set_parameter("OWNER", os.getenv("USER"))
        self.set_parameter("CICQ_PATH", workdir)

    def get_all_threads_name(self, teamcity_compliant=None):
        ''' $teamcity_compliant param is meant for backward compatibility with teamcity_cicq_api '''
        retlist = []
        jobnames = self.list_jobs()
        for name in jobnames:
            ret = self.decompose_jobname(name)
            if ret:
                retlist.append(ret[-1])
        return retlist

    def decompose_jobname(self, jobname: 'project.ip.thread') -> ['project', 'ip', 'thread'] or None:
        sname = jobname.split('.')
        if len(sname) == 3:
            return sname
        return None

    def get_centralize_workdir(self):
        return self.get_parameter("CICQ_PATH")

    def set_centralize_workdir(self, value):
        return self.set_parameter("CICQ_PATH", value)

    def get_arc_resources(self):
        self.get_parameter("ARC_RESOURCES")

    def set_arc_resources(self, value):
        return self.set_parameter("ARC_RESOURCES", value)

    def get_refbom(self):
        return self.get_parameter("CICQ_REFBOM")

    def set_refbom(self, value):
        return self.set_parameter("CICQ_REFBOM", value)

    '''
    NOTES:
        - jenkins cli 'console' command will always return the last build only.
        - the last line of a complete job is "Finished: ..."
        - jenkins will only have 1 queueing job
            > what this means is, no matter how many times u hit the 'run' button, u will only see 1 queueing job.
    '''

    def get_current_running_build(self):
        exitcode, stdout, stderr = self.console(self.jobName, lines=1)
        if 'Finished: ' in stdout or 'ERROR: Permalink lastBuild produced no build' in stderr:
            data = {'count': 0, 'build': []}
        else:
            data = {'count': 1, 'build':[{'webUrl': '', 'id': 'lastBuild'}]}
        return data

    def get_latest_build(self):
        return {'id': 'lastBuild'}

    def get_current_queued_build(self):
        ''' always return 0, just for backward compatibility. We no longer need this in jenkins. '''
        data = {'count': 0}
        return data

    def get_agentid_for_build(self, buildid=None):
        return 'NA'

    def get_agent_arc_job_id_for_buildid(self, agentid=None, buildid=None):
        '''
        >../../../scripts/jenkins/cicq_jenkin_cli console i10socfm.jtag_common.liotest2 | grep 'Waiting on ARC job to complete:'
        Waiting on ARC job to complete: 664216136
        '''
        exitcode, stdout, stderr = self.console(self.jobName)
        match = re.search("Waiting on ARC job to complete: (\d+)", stdout)
        if match:
            return match.group(1)
        return ''

    def get_jobname_by_thread(self, thread: str) -> "jobname" or None:
        jobnames = self.list_jobs()
        for jobname in jobnames:
            ret = self.decompose_jobname(jobname)
            if ret and ret[-1] == thread:
                return jobname
        return ''

    #########################################
    #########################################
    ### These methods are meant for backward compatibility for teamcity_cicq_api.py
    #########################################
    #########################################
    def get_buildtype(self, buildtypeId=None):
        ''' this method is used in abnrlib/flows/cicqupdate.py to check for the job existance in teamcity '''
        retval = 'Found'
        try:
            self.get_job()
        except:
            retval = 'Could not find'
        return retval

    def get_all_buildtypes_id(self) -> ['jobname', 'jobname', ...]:
        ''' Used in dmx cicq delete: return all jenkins jobname which comform to cicq naming, ie: <project>.<ip>.<thread> '''
        retlist = []
        jobnames = self.list_jobs()
        for jobname in jobnames:
            decomname = self.decompose_jobname(jobname)
            if decomname:
                retlist.append(jobname)
        return retlist

    def decompose_buildtype_id(self, jobname: 'project.ip.thread'):
        ''' Used in dmx cicq delete: '''
        project, ip, thread = self.decompose_jobname(jobname)
        return ['_', project, ip, thread]

    def get_latest_build_for_buildtype(self, jobname):
        ''' Used in dmx cicq delete: '''
        dateobj = self.get_lastbuild_datetime(jobname)
        ### If we can't find the last build date, do not delete the job.
        ### Thus, we set the startDate as today's date
        if not dateobj:
            dateobj = datetime.datetime.now()
        fmt = '%Y%m%d'
        datestr = dateobj.strftime(fmt) + 'xxxxxxxxxxxx'
        ret = {'startDate': datestr}
        return json.dumps(ret)

    def get_centralize_workdir_client_name(self):
        icmconfig = '{}/cicq/workspace/{}___{}___cicq_integration_{}/.icmconfig'.format(self.get_centralize_workdir(), self.project, self.ip, self.thread)
        cmd = 'cat {} | head -n 1 | awk -F= \'{{print $2}}\' '.format(icmconfig)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        ret = stdout.rstrip()
        return ret



    ########################################################################
    ### Create alias, for backward compatibility for teamcity_cicq_api.py
    ########################################################################
    run_build = run_job
    setup_build = setup
    delete_build = delete_job
    get_current_running_build_arc_job_id = get_agent_arc_job_id_for_buildid
    get_buildtype_by_thread = get_jobname_by_thread

if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    '''
    p = 'i10socfm'
    i = 'jtag_common'
    t = 'liotest2'
    a = JenkinsCicqApi(p, i, t)
    #a.set_centralize_workdir('/nfs/site/disks/psg_cicq_2/users/cicq/{}.{}.{}'.format(p, i, t))
    print(a.help())
    '''
    p = 'proA'
    i = 'ipB'
    t = 'threadC'
    a = JenkinsCicqApi(p, i, t)
    '''
    #a.setup()
    #a.run_build(props={'name':'tan yoke ming', 'age': 'very young'})
    print("===============?")
    print(a.get_parameter("CICQ_PATH"))
    print(a.get_parameter("CICQ_PROJECT"))
    print(a.get_parameter("CICQ_IP"))
    print(a.get_parameter("CICQ_THREAD"))
    print(a.get_parameter("xxx"))
    #a.set_parameter("CICQ_PATH", "/nfs/site/disks/psg_cicq_1/users/cicq/proA.ipB.threadC")
    '''
    print("----------------------")
    print(a.get_all_threads_name())
