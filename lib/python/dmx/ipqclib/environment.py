#!/usr/bin/env python
"""environment.py"""
from __future__ import print_function
import os
import re
import sys
import platform
from dmx.ipqclib.utils import run_command, file_accessible
from dmx.ipqclib.settings import _DB_FAMILY

class Environment(object):
    """Environment class"""
    def __init__(self, workdir, ipenv):

        self._workdir = workdir
        self._ipenv = ipenv
        self.tool_path = os.path.join(self._workdir, 'tools.env')
        self.cmd_path = os.path.join(self._workdir, 'ipqc.cmd')
        self.system = os.path.join(self._workdir, 'system.env')
        self._cmd = None

        for index, option in enumerate(sys.argv):
            if (option == '-i') or (option == '--ip_name'):
                sys.argv[index+1] = ipenv

        ### Command invoked for running check
        if ("run-all" in sys.argv[1:2]) or ("dry-run" in sys.argv[1:2]):
            self.base = 'ipqc'
            self._cmd = '{} {}' .format(self.base, " ".join(sys.argv[1:]))
        elif file_accessible(self.cmd_path, os.F_OK):
            self._cmd = self.get_cmd(self.cmd_path)
        else:
            self.base = 'ipqc'
            self._cmd = '{} {}' .format(self.base, " ".join(sys.argv[1:]))

        ### System information
        if file_accessible(self.system, os.F_OK):
            (self._os_name, self._hostname, self._release, self._machine) = \
                    self.get_system_info(self.system)
        else:
            (self._os_name, self._hostname, self._release, self._machine) = self._get_os_info()

        ### tool information
        self._arc_resources = self._get_arc_resources()
#        if file_accessible(self.tool_path, os.F_OK):
#            self._arc_resources = self.get_arc_resources(self.tool_path)
#        else:
#            self._arc_resources = self._get_arc_resources()


    @property
    def os_name(self):
        """os_name"""
        return self._os_name

    @property
    def hostname(self):
        """hostname"""
        return self._hostname

    @property
    def release(self):
        """release"""
        return self._release

    @property
    def machine(self):
        """machine"""
        return self._machine

    @property
    def arc_resources(self):
        """arc_resources"""
        return ','.join(self._arc_resources)

    # OS Information
    @staticmethod
    def _get_os_info():

        os_info = platform.uname()

        return (os_info[0], os_info[1], os_info[2], os_info[4])

    # ARC resources
    @staticmethod
    def _get_arc_resources():

        resources_list = []

        results = run_command('arc job-info')
        pattern = r'resources : (\S+)'
        match = re.search(pattern, results[1])

        if match:
            resources = match.group(1)

            resources_list = resources.split(',')

        return resources_list

    def _get_arc_project(self):

        project = []

        resources = self._get_arc_resources()

        if resources != []:

            pattern = 'project/'+_DB_FAMILY.lower()

            for resource in resources:
                if re.match(pattern, resource):
                    project.append(resource)
                    break

        return project

    def _get_project_tools(self):

        tools = []

        project = self._get_arc_project()

        if project != []:
            project = ''.join(project)
            results = run_command('arc resource-info {}' .format(project))
            out = results[1]
            tools = out.split(',')

        return tools

    def record_tools(self):
        """record_tools"""
        current_tools = list(set(self._get_arc_resources())-set(self._get_arc_project()))
        tools = self._get_project_tools()

        tools_list = tools + current_tools

        with open(self.tool_path, 'w') as fid:

            print('{}' .format(','.join(self._arc_resources)), file=fid)

            for tool in tools_list:
                print(tool, file=fid)

    def save_system_info(self):
        """save_system_info"""
        (os_name, hostname, release, machine) = self._get_os_info()
        with open(self.system, 'w') as fid:
            print('{} {} {} {}' .format(os_name, hostname, release, machine), file=fid)

    def save_cmd(self):
        """save_cmd"""
        with open(self.cmd_path, 'w') as fid:
            print(self._cmd, file=fid)

    def save(self):
        """save"""
        self.record_tools()
        self.save_cmd()
        self.save_system_info()

    @staticmethod
    def get_cmd(filepath):
        """get_cmd"""
        cmd = None
        with open(filepath, 'r') as fid:
            line = fid.readline()
        cmd = line[:-1]
        return cmd

    @staticmethod
    def get_system_info(filepath):
        """get_system_info"""
        with open(filepath, 'r') as fid:
            line = fid.readline()
        info = line[:-1].split()

        return (info[0], info[1], info[2], info[3])

    @staticmethod
    def get_arc_resources(filepath):
        """get_arc_resources"""
        resource = None
        with open(filepath, 'r') as fid:
            line = fid.readline()
        resource = line[:-1]

        return resource.split(',')

    @property
    def cmd(self):
        """cmd"""
        return self._cmd
