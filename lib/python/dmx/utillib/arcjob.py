#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/arcjob.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to instantiate connection to servers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
from dmx.utillib.utils import *
from dmx.errorlib.exceptions import *

ARC_ROOT = '/p/psg/ctools/arc'
PICE_PG_ARC = 'https://psg-png-arc.png.intel.com'
PICE_SJ_ARC = 'https://psg-sc-arc.sc.intel.com'
JOB_DIR = 'arc/dashboard/reports/show_job'

class ArcJobError(Exception): pass

class ArcJob(object):
    def __init__(self):
        self.arc = '{}/bin/arc'.format(os.getenv('ARC_ROOT', ARC_ROOT))
        self.logger = logging.getLogger(__name__)
        if is_local_pg():
            self.arc_page = PICE_PG_ARC
        elif is_local_sj():
            self.arc_page = PICE_SJ_ARC
        else:
            self.arc_page = ''                           
        
    def submit_job(self, script, bundle=''):
        if bundle:
            command = '{} submit {} -- "{}"'.format(self.arc, bundle, script)
        else:
            command = '{} submit -- "{}"'.format(self.arc, script)

        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stderr)
            raise DmxErrorCFAR02('Error submitting job: {}'.format(command))
        id = stdout.splitlines()[0]
        return id

    def get_job_page(self, id):
        page = '{}/{}/{}'.format(self.arc_page, JOB_DIR, id)
        return page
    
    def wait_for_completion(self, id):
        completed = False
        while not completed:
            self.logger.info('Job {} is still running, next polling in 30 seconds.'.format(id))
            time.sleep(30)
            command = '{} job {} status'.format(self.arc, id)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                self.logger.error(stderr)
                raise DmxErrorCFAR03('Error getting job\'s status: {}'.format(command))
            completed = ('done' in stdout) or ('complete' in stdout)
        return
    
    def get_job_storage(self, id):   
        command = '{} job {} storage'.format(self.arc, id)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stderr)
            raise DmxErrorCFAR03('Error getting job\'s status: {}'.format(command))
        return stdout.strip()                             

    def get_job_return_code(self, id):   
        command = '{} job {} return_code'.format(self.arc, id)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            self.logger.error(stderr)
            raise DmxErrorCFAR03('Error getting job\'s status: {}'.format(command))
        return stdout                                

    def get_job_output(self, id):
        storage = self.get_job_storage(id)
        stdoutfile = '{}/stdout.txt'.format(storage)
        stderrfile = '{}/stderr.txt'.format(storage)
        stdout = [x.strip() for x in open(stdoutfile, 'r').readlines()]
        stderr = [x.strip() for x in open(stderrfile, 'r').readlines()]
        exitcode = int(self.get_job_return_code(id))
        return (exitcode, stdout, stderr)

    def find_immediate_children_jobid(self, arcjobid):
        cmd = 'arc job-query parent={}'.format(arcjobid)
        exitcode, stdout, stderr = run_command(cmd)
        return stdout.split()
                
    def concat_children_output(self, arcjobid):
        ''' Concatenate all immediate children job output to
        - concat_<arcjobid>_stdout.txt
        - concat_<arcjobid>_stderr.txt
        '''
        children_jobid_list = self.find_immediate_children_jobid(arcjobid)
        filelist = {'stdout.txt':{}, 'stderr.txt':{}}
        for f in filelist:
            filelist[f]['localfile'] = os.path.abspath('concat_{}_{}'.format(arcjobid, f))

        for f in filelist:
            localfile = filelist[f]['localfile']
            self.logger.debug("Cleanup Previous logfile: {}".format(localfile))
            cmd = 'echo "" > {}'.format(localfile)
            os.system(cmd)

        for jobid in children_jobid_list:
            storage = self.get_job_storage(jobid)
            for f in filelist:
                localfile = filelist[f]['localfile']
                storagefile = '{}/{}'.format(storage, f)
                
                header = '\n=========================\n=== JobId: {} ===\n=========================\n'.format(jobid)
                cmd = 'echo "{}" >> {}'.format(header, localfile)
                os.system(cmd)
                
                cmd = 'cat {} >> {}'.format(storagefile, localfile)
                self.logger.debug("Running: {}".format(cmd))
                os.system(cmd)

        return [filelist['stdout.txt']['localfile'], filelist['stderr.txt']['localfile']] 
        
            
            
