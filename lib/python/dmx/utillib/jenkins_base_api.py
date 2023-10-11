#!/usr/bin/env python

"""
Base class of interacting with TeamCity.
Input and Output to the rest api is in XML format.

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

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.utillib.utils
import dmx.utillib.server

LOGGER = logging.getLogger(__name__)

class JenkinsBaseApiError(Exception):
    pass

class JenkinsBaseApi():

    def __init__(self):
        self.exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'scripts', 'jenkins', 'cicq_jenkin_cli')

    def help(self):
        self._printoutput(self._run('help'))
    
    def list_jobs(self):
        exitcode, stdout, stderr = self._run('list-jobs')
        retval = []
        if stdout:
            for line in stdout.splitlines():
                sline = line.strip()
                if sline:
                    retval.append(sline)
        return retval

    def get_job(self, jobname: str) -> [ET, str]:
        _, tmpfile = tempfile.mkstemp()
        exitcode, stdout, stderr = self._run(f'get-job {jobname} > {tmpfile}')
        self._printoutput((exitcode, stdout, stderr))
        if exitcode:
            raise JenkinsBaseApiError(stderr)
        tree = ET.parse(tmpfile)
        return [tree, tmpfile]

    def create_job(self, jobname, xmlfilepath: str):
        output = self._run(f'create-job {jobname} < {xmlfilepath}')
        self._printoutput(output)
        return output[0]

    def delete_job(self, jobname: str):
        output = self._run(f'delete-job {jobname}')
        self._printoutput(output)
        return output[0]

    def update_job(self, jobname: str, xmlfilepath: str):
        output = self._run(f'update-job {jobname} < {xmlfilepath}')
        self._printoutput(output)
        return output[0]

    def copy_job(self, srcjobname: str, dstjobname: str):
        output = self._run(f'copy-job {srcjobname} {dstjobname}')
        self._printoutput(output)
        return output[0]

    def add_job_to_view(self, jobname: str, viewname: str):
        output = self._run(f'add-job-to-view {viewname} {jobname}')
        self._printoutput(output)
        return output[0]

    def create_view(self, viewname: str, xmlfilepath: str):
        output = self._run(f'create-view {viewname} < {xmlfilepath}')
        self._printoutput(output)
        return output[0]

    def get_view(self, viewname: str):
        _, tmpfile = tempfile.mkstemp()
        exitcode, stdout, stderr = self._run(f'get-view {viewname} > {tmpfile}')
        tree = ET.parse(tmpfile)
        return [tree, tmpfile]

    def delete_view(self, viewname: str):
        output = self._run(f'delete-view {viewname}')
        self._printoutput(output)
        return output[0]


    def build(self, jobname, params: dict=None, follow_console_output=False) -> ['int: exitcode', 'str: stdout', 'str: stderr']:
        optstr = ''
        if params:
            for key,val in params.items():
                optstr += f' -p {key}="{val}"'
        if follow_console_output:
            optstr += ' -f -v'
        cmd = f'build {jobname} {optstr}'
        output = self._run(cmd)
        self._printoutput(output, cmd)
        return output

    def update_elementtree_param(self, tree: ET, key: str, value: str) -> ET:
        root = tree.getroot()
        elements = root.findall('./properties/hudson.model.ParametersDefinitionProperty/parameterDefinitions/hudson.model.StringParameterDefinition')
        for e in elements:
            name = e.find("name").text
            val = e.find("defaultValue").text
            if name == key:
                e.find("defaultValue").text = value
        return tree

    def get_elementtree_param(self, tree: ET, key: str) -> str or None:
        root = tree.getroot()
        elements = root.findall('./properties/hudson.model.ParametersDefinitionProperty/parameterDefinitions/hudson.model.StringParameterDefinition')
        for e in elements:
            name = e.find("name").text
            val = e.find("defaultValue").text
            if name == key:
                return e.find("defaultValue").text
        return None

    def console(self, jobname, buildname='lastBuild', lines=-1) -> str:
        cmd = f'console {jobname} {buildname} -n {lines}'
        output = self._run(cmd)
        self._printoutput(output, cmd)
        return output

    def get_lastbuild_datetime(self, jobname):
        return self.get_build_datetime(jobname, build='lastBuild')

    def get_build_datetime(self, jobname: str, build: str) -> datetime.datetime or None:
        ''' there is no such service in jenkins-cli, thus , we need to get it from REST '''
        cmd = self._get_curl_cmd(f'job/{jobname}/{build}/api/json')
        exitcode, stdout, stderr =  dmx.utillib.utils.run_command(cmd)
        self._printoutput((exitcode, stdout, stderr), cmd)
        if not exitcode:
            data = json.loads(stdout)
            if 'timestamp' in data:
                ### timestamp recorded in jenkins is in millisecond, thus we need to divide 1000 to get the seconds
                epoch = data['timestamp'] / 1000
                ret = datetime.datetime.fromtimestamp(epoch)
                return ret
        return None

    def _get_curl_cmd(self, request):
        host = 'https://cje-fm-owrp-prod03.devtools.intel.com/psg-infra-cicq/'
        token = 'psgcicq_tc:11db7dae53664b5da2b643af7e539b99c2'
        finalcmd = f"env -i curl --basic -H 'Content-Type: application/xml' -H 'Accept: application/json' -H 'Origin: {host}'"
        finalcmd = f"/usr/bin/env -i curl --basic -H 'Content-Type: application/xml' -H 'Accept: application/json' -u {token} {host}{request}"
        return finalcmd

    def _printoutput(self, output_from_run: list, cmd: str=''):
        if cmd:
            LOGGER.debug(f"\nCMD: {cmd}")
        exitcode, stdout, stderr = output_from_run
        LOGGER.debug(f"\nEXITCODE: {exitcode}\nSTDOUT: {stdout}\nSTDERR: {stderr}\n")

    def _run(self, cmdstr):
        exitcode, stdout, stderr = dmx.utillib.utils.run_command('{} {}'.format(self.exe, cmdstr))
        return (exitcode, stdout, stderr)


if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    a = JenkinsBaseApi()
    #print(a.help())
    #print(a.list_jobs())
    #tree, filename = a.get_job('i10socfm.jtag_common.liotest2')
    #print(tree)
    #tree.write('before.xml')
    #a.build('test1', params={'name': 'dan and lio', 'age': 'ming and osl'}, follow_console_output=True)
    #a.update_elementtree_param(tree, 'CICQ_IP', 'wtf man haha')
    #tree.write("after.xml")
    #viewtree, viewfile = a.get_view('template')
    #a.create_view('aaa', viewfile)
    #a.add_job_to_view('i10socfm.jtag_common.liotest999', 'aaa')
    #a.delete_view('aaa')
    print(a.get_lastbuild_datetime('test1'))

