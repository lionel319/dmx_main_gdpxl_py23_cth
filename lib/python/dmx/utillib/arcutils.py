#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/arcutils.py#2 $
$Change: 7444498 $
$DateTime: 2023/01/15 19:15:53 $
$Author: lionelta $

Description: Class to instantiate connection to servers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''
from __future__ import print_function

from builtins import object
import os
import logging
import sys
import re
import time
import datetime
from pprint import pprint, pformat
import multiprocessing

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.server
from dmx.errorlib.exceptions import *

''' no longer applicated in cth environment
try:
    if sys.version_info[0] > 2:
        sys.path.insert(0, os.path.join(LIB, 'py23comlib', 'arc_utils', '1.7_py23'))
    import arc_orm.arc_orm
except:
    print("""
    Can't import arc_orm. Make sure you have: 
    - icd_cad_arc_utils/1.7 in your arc resource? -or-
    - /p/psg/flows/common/arc_utils/1.7 in your PATH/PYTHONPATH?
    """)
    raise
'''

LOGGER = logging.getLogger(__name__)

class ArcUtils(object):

    def __init__(self, cache=True):
        self.cache = cache
        self.cachedata = {}
        self.cachedatetime = {}
        self.cachewalkcollection = {}
        self.cachekvp = multiprocessing.Manager().dict()
        self.arc = '/p/psg/ctools/arc/bin/arc'
        #self.ao = arc_orm.arc_orm.ArcORM()


    def get_resource_usage(self, logfile=None):
        '''
        logfile == arc output stdout.txt file.
        If not given, will use $ARC_JOB_STORAGE/stdout.txt.

        Example of tail of logfile:-
        ... ... ...
        Your job looked like:

        ------------------------------------------------------------
        # LSBATCH: User input
        /p/psg/ctools/arc/scripts/lsf/arc_lsf_execute.sh 117983005
        ------------------------------------------------------------

        Successfully completed.

        Resource usage summary:

            CPU time :                                   4.28 sec.
            Max Memory :                                 65.77 MB
            Average Memory :                             -
            Total Requested Memory :                     -
            Delta Memory :                               -
            Max Swap :                                   -
            Max Processes :                              -
            Max Threads :                                -
            Run time :                                   10 sec.
            Turnaround time :                            13 sec.

        The output (if any) is above this job summary.



        PS:

        Read file </p/psg/data/lionelta/job/20190513/1100/117983005/stderr.txt> for stderr output of this job.
        ... ... ...

        '''
        if not logfile:
            logfile = os.path.join(os.getenv("ARC_JOB_STORAGE"), 'stdout.txt')

        cmd = 'tail -100 {}'.format(logfile)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)

        fields = {
            'CPU time :': 'cputime',
            'Max Memory :': 'memory',
            'Max Processes :': 'processes',
            'Max Threads :': 'threads',
            'Run time :': 'runtime'
        }

        data = {}
        for line in stdout.split('\n'):
            for key in fields:
                if key in line:
                    data[fields[key]] = self._get_resource_usage_value(line)
                    continue

        return data


    def _get_resource_usage_value(self, txt=''):
        '''
        txt = '    CPU time :    7355.14 sec.'
        return '7355.14'
        '''
        tmp = txt.split(":")
        retval = ''
        if len(tmp) > 1:
            retval = tmp[1].split()[0].strip()
        return retval


    def get_arc_job(self, arc_job_id='', site=os.getenv("ARC_SITE")):
        '''
        get the current arc job

        return = {
            'command': '/usr/intel/bin/tcsh',
            'family': '',
            'grp': 'cad',
            'host': 'ppgyli0117',
            'id': '12490144',
            'iwd': '/nfs/png/home/lionelta',
            'local': '1',
            'name': '',
            'no_db': '1',
            'os': 'linux64',
            'parent': '0',
            'priority': '0',
            'requirements': 'project/falcon/fm8dot2/5.0/phys',
            'resources': 'project/falcon/fm8dot2/5.0/phys/2018WW01',
            'set_create_at': '01/11/2018 16:26:26',
            'set_done_at': '01/11/2018 16:26:26',
            'status': 'done',
            'storage': '/p/psg/data/lionelta/job/20180111/1600/12490144',
            'tags': '0',
            'type': 'interactive',
            'user': 'lionelta'}
        '''
        if arc_job_id:
            server = dmx.utillib.server.Server(site=site).server
            cmd = 'ssh -q {} \'{} job {}\' '.format(server, self.arc, arc_job_id)
        else:
            cmd = '{} job'.format(self.arc)

        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        data = self._convert_string_to_kvp(stdout)
        return data


    def get_tool_version_from_current_environment(self, tool, autosort=True):
        '''
        Given the tool name, find the resource used in the current environment.

        Example:-
            current terminal is arc shell with
                project/falcon/branch/fm6dot2main/rc,dmx/main
            Given
                tool == 'dmx'
            Return '/main'

        Example:-
            current terminal is arc shell with
                project/falcon/fm6dot2/4.0/phys/2018WW29
            Given
                tool == 'dmx'
            Return '/11.1'

        If tool not found, return ''
        '''
        arcjob = self.get_arc_job()
        if 'resources' not in arcjob:
            return ''
        kvp = self.get_resolved_list_from_resources(arcjob['resources'], autosort=autosort)
        if tool not in kvp:
            return ''
        return kvp[tool]

    def get_resolved_list_from_resources_2(self, resources, autosort=True):
        '''
        This API behaves exactly the same as get_resolved_list_from_resources(), but
        this API uses arc_orm, whereas that one uses 'arc' command call.
        This API should be at least 20times faster that that one.

        For each level, return a tuple of
        (res name, hier, collections, leaves) where
        'res_name' is the name of the resource being returned
        'hier' is a list containing the resources expanded to get here
        'collections' is a list of collections from the 'resources' list
        'leaves' is a list of leaf resouces from the 'resources' list
        
        '''
        return {'no_longer_applicable': 'in_cth_environment'}

        ret = {}

        if autosort:
            resources = self.sort_resource_string(resources)

        for r in resources.split(','):
            for resname, hier, collections, leafs in self._walk_collection(r):
                if not collections and not leafs:
                    [t, a] = self._split_type_address_from_resource_name(resname)
                    ret[t] = a
                elif leafs:
                    for leaf in leafs:
                        [t, a] = self._split_type_address_from_resource_name(leaf)
                        ret[t] = a
        return ret

    def _walk_collection(self, res):
        if res not in self.cachewalkcollection:
            retlist = []
            for x in self.ao.walk_collection(res):
                retlist.append(x)
            self.cachewalkcollection[res] = retlist
        return self.cachewalkcollection[res]

    def sort_resource_string(self, resource_str):
        '''
        given:
            dmxdata/latestdev,cicq/latestdev,project/falcon/branch/fp8main/0.8/phys/rc,dmx/latestdev
        return:
            project/falcon/branch/fp8main/0.8/phys/rc,dmx/latestdev,dmxdata/latestdev,cicq/latestdev
        '''
        ### AutoSort 'project/bundle' resoure to first element
        ### https://jira.devtools.intel.com/browse/PSGDMX-1575
        sres = []
        for res in resource_str.split(','):
            r = res.strip()
            if r.startswith('project/'):
                sres.insert(0, r)
            else:
                sres.append(r)
        resources = ','.join(sres)
        return resources


    def get_resolved_list_from_resources(self, resources, autosort=True):
        '''
        if resources is a bundle,
            resource = 'project/falcon/fm8dot2/5.0/phys/2018WW01'
            return = {
                type: address,
                'p4': '/psgeng_no_map',
                'icmadmin': '/0.4',
                'dmx': '/9.4',
                'project_config': '/i10/2017WW51',
                ...   ...   ...
            }

        if resources is not a bundle:
            resource = 'dmx/9.4'
            return = {
                'dmx': '/9,4'
            }

        resources can be a mixture of resource, separated by comma.
        The right-hand-side of the resource always win.
            resource = 'project/falcon/fm8dot2/5.0/phys/2018WW01,icmadmin/0.1,dmx/main'
            return = {
                type: address,
                'p4': '/psgeng_no_map',
                'icmadmin': '/0.1',
                'dmx': '/main',
                'project_config': '/i10/2017WW51',
                ...   ...   ...
            }

        The resource on the right-most will always override the resource on the left-sides.

        By default (autosort=True), any resource which starts with 'project' will be sorted to the left most,
        so that the 'single-resource' will always override the 'collection-resource'(ie:- project/bundle/...),
        which exactly mimics the behavior of the actually arc shell.
        '''
        ret = {}

        ### AutoSort 'project/bundle' resoure to first element
        ### https://jira.devtools.intel.com/browse/PSGDMX-1575
        if autosort:
            resources = self.sort_resource_string(resources)

        if self.cache and resources in self.cachedata:
            return self.cachedata[resources]

        self.cache_resources_kvp_in_parallel(resources)

        for resource in resources.split(','):
            resource = resource.strip()
            data = self.get_kvp_from_resource(resource)

            ### Return [] if it is not a bundle
            if 'resolved' not in data:
                [t, a] = self._split_type_address_from_resource_name(resource)
                ret[t] = a
            else:
                ret.update(self.get_resolved_list_from_resources(data['resolved'], autosort=False))

        self.cachedata.update(ret)
        return ret

    def cache_resources_kvp_in_parallel(self, resources):
        '''
        Cache all resources in parallel. It makes a huge difference when
        there are tens or hundreds of resources that needs to run 
        'arc resource-info <resource>'
        '''
        threads = []
        for resource in resources.split(','):
            threads.append(multiprocessing.Process(target=self.get_kvp_from_resource, args=(resource,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        

    def is_resource_defined(self, resource):
        '''
        if yes, return the entire kvp as a dict
        else, return {}
        '''
        return self.get_kvp_from_resource(resource)


    def get_kvp_from_resource(self, resource):
        '''
        resource can be a bundle, or a single resource.

        eg:-
            resoource = 'dmx/9.4'
            return = {
                '+PYTHONPATH': 'PSG_FLOWS/common/dmx/9.4/lib/python:PSG_FLOWS/common/dmx/9.4/lib/python/dmx/tnrlib',
                'DMX_LEGACY': '1',
                'DMX_LIB': 'PSG_FLOWS/common/dmx/9.4/lib/python',
                'DMX_PATH': 'PSG_FLOWS/common/dmx/9.4/bin',
                'DMX_ROOT': 'PSG_FLOWS/common/dmx/9.4',
                'DMX_TCLLIB': '/p/psg/flows/common/icd_cad_tcllib/5/linux64/lib',
                'DMX_TNRLIB': 'PSG_FLOWS/common/dmx/9.4/lib/tcl/dmx/tnrlib',
                'ICD_CAD_QA_TCLLIB': 'PSG_FLOWS/common/dmx/9.4/lib/tcl/dmx/tnrlib',
                'IPQC_ROOT': 'PSG_FLOWS/common/dmx/9.4',
                '__resource_class': 'ARC::Resource::Generic',
                '__resource_name': 'dmx/9.4',
                '_resource_owner': 'kwlim,lionelta,taraclar,nbaklits',
                'address': '/9.4',
                'created_at': '01/09/2018 14:17:44',
                'definition_source': '$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/arcutils.py#2 $',
                'description': 'DMX bundle - 9.4 tool resource.',
                'id': '13203',
                'owner': '0',
                'supported_os': 'linux64',
                'type': 'dmx',
                'user': 'kwlim,lionelta,taraclar,nbaklits',
                'version': '9.4'
            }
        '''
        return {'no_longer_applicable': 'in_cth_env'}

        if self.cache and resource in self.cachekvp:
            return self.cachekvp[resource]

        '''
        cmd = '{} resource {}'.format(self.arc, resource)
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        data = self._convert_string_to_kvp(stdout)
        '''

        ''' no longer applicable in cth environment
        ### use arc_orm for runtime improvement.
        ao = arc_orm.arc_orm.ArcORM()
        data = ao.resource_info(resource)

        self.cachekvp[resource] = data
        return data
        '''

    def get_datetime_object_for_resource(self, arc_res):
        '''
        Given an arc_res(eg:- dmx/12.3), return the datetime object for the resource
        based on it's 'created_at' value.
        '''
        if arc_res not in self.cachedatetime:
            data = self.get_kvp_from_resource(arc_res)
            self.cachedatetime[arc_res] = self.get_datetime_object(data['created_at'])
        return self.cachedatetime[arc_res]


    def get_datetime_object(self, arc_resource_created_at_str):
        '''
        Given the value of 'create_at' from a resource, return the datetime object.
        This is the string return from arc_orm library:-
            created_at: Thu Apr 22 19:30:52 2021,

        *Do note that the string returned from calling 'arc resource <resource>' is in a different format:-
            created_at : 04/08/2019 10:46:10
        '''
        fmt = '%c'
        obj = datetime.datetime.strptime(arc_resource_created_at_str, fmt)
        return obj


    def _convert_string_to_kvp(self, lines):
        '''
        Running most of the 'arc' cmdline command will print out informat in  the following format:-
            key : value
        All these will be strings from stdout when executing with run_command()
        This function will convert all of those and return it into a single level dictionnary.
        '''
        data = {}
        for line in lines.split('\n'):
            if not re.search("^\s*$", line):
                key, value = line.split(' : ', 1)
                data[key.strip()] = value.strip()
        return data


    def _split_type_address_from_resource_name(self, name):
        '''
        name = 'dmx/9.4'
        return = ['dmx', '/9.4']
        '''
        if '/' not in name:
            return [name, '']

        m = re.search('^([^/]+)(.+)$', name.strip())
        return [m.group(1), m.group(2)]


    def get_job_output(self, arc_job_id, filesys='stdout', site=os.getenv("ARC_SITE")):
        '''
        Get the stdout/stderr output of the given arc_job_id.

        filesys: stdout/stderr
        site: sc/png
        return: string
        '''
        server = dmx.utillib.server.Server(site=site).server
        cmd = 'ssh -q {} \'cat `{} job-info {} storage`/{}.txt\''.format(server, self.arc, arc_job_id, filesys)
        LOGGER.debug("Running cmd: {}".format(cmd))
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        if exitcode:
            LOGGER.error('stdout: {}'.format(stdout))
            LOGGER.error('stderr: {}'.format(stderr))
            raise DmxErrorCFAR03('Failed getting {} job {}'.format(arc_job_id, filesys))
        return stdout


    def wait_for_job_completion(self, arc_job_id, children=True, site=os.getenv("ARC_SITE")):
        '''
        From 'arc help wait', ...
            Waits for a job and all its children to finish before returning the prompt.

        children: True/False
            if True, will wait until all children to finish
            if False, will return prompt after itself completed.
        site: sc/png
        '''
        server = dmx.utillib.server.Server(site=site).server
        if children:
            cmd = "ssh -q {} '{} wait {}' ".format(server, self.arc, arc_job_id)
            LOGGER.debug("Running cmd: {}".format(cmd))
            return os.system(cmd)
        else:
            done = True
            while done:
                status = self.get_arc_job(arc_job_id=arc_job_id, site=site)['status']
                LOGGER.debug("job status: {}".format(status))
                if status in ['done', 'failed']:
                    done = False
                time.sleep(30)


    def get_job_url(self, jobid):
        host = os.getenv("ARC_BROWSE_HOST")
        url = 'https://{}/arc/dashboard/reports/show_job/{}'.format(host, jobid)
        return url



if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

    a = ArcUtils()

    '''
    x = a.get_kvp_from_resource('project/falcon/fm8dot2/5.0/phys')
    x = a.get_arc_job()
    '''
    x = a.get_resolved_list_from_resource('project/falcon/fm8dot2/5.0/phys/2018WW01')
    x = a.get_resolved_list_from_resource('dmx/9.4')



    pprint(x)
