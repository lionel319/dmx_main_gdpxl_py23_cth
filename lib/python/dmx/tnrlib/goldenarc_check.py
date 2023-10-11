#!/usr/bin/env python
'''
Golden Arc Check Library
'''
from __future__ import print_function
from builtins import str
from builtins import object
import os
import sys
import logging
from pprint import pprint
from datetime import datetime
import xml.etree.ElementTree

# Altera libs
import os,sys
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)

import dmx.utillib.utils
import dmx.utillib.loggingutils
import dmx.tnrlib.test_runner
import dmx.utillib.arcutils
import dmx.abnrlib.goldenarc_db

class GoldenArcCheck(object):

    def __init__(self, project, variant, libtype, config, wsroot, milestone, thread, views=None, prel=None, prod=False):
        '''
        config == always the config of project/variant@config. (not the libtype's config)
        '''
        self.logger = logging.getLogger(__name__)
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.config = config
        self.wsroot = wsroot
        self.milestone = milestone
        self.thread = thread
        self.views = views
        self.prel = prel

        self.db = dmx.abnrlib.goldenarc_db.GoldenarcDb(prod=prod)
        self.db.connect()
        ### The default collection for the databse is 'GoldenArc', and can be accessed thru self.db.col
        ### If there is a need to change the column(eg: for regression, which is pointing to other collection, set this:-
        ###     self.db.col = self.db.db.db['RegtestGoldenArc']

        self.au = dmx.utillib.arcutils.ArcUtils()

        self.result = {}
        self.tests_failed = []  # lists of TestFailure objects 
        self._cache = {'resdate':{}, '2bcheck':{}, 'gadb':{}}

    def report(self, printout=True):
        '''
        only_errors==True
            reports only errors
        only_errors==False
            reports all 
        '''
        for provar in self.result:
            for auditfile in self.result[provar]:
                data = self.result[provar][auditfile]
                if data['errors']:
                    if printout:
                        print('FAIL: {}'.format(auditfile))
                    for e in data['errors']:
                        if printout:
                            print('- {}'.format(e))
                        errmsg = 'Failed goldenarc check for {}: {}'.format(auditfile, e)
                        self.testrunner.log_test_fail(flow='goldenarc', error=errmsg, variant=self.variant, libtype=self.libtype)
                else:
                    if printout:
                        print('PASS: {}'.format(auditfile))
        
        self.tests_failed = self.testrunner.tests_failed
        return self.tests_failed


    def run_test(self):
        '''
        returns: number of errors found
        To get the full result details, look into self.result dictionary.
        Here is the data structure of self.result:-

        self.result = {
            (i10socfm, cw_lib): {
                cw_lib/lint/audit/audit.cw_lib.lint_mustfix.xml: {
                    arcres: 'project/falcon/blabla,rtl/1.3,python/3.4',
                    flow: 'lint',
                    subflow: 'mustfix',
                    errors: ['err_str_1', 'err_str_2', ...],
                    checks: {
                        dmx: {
                            gold: /1.3,
                            used: /1.4,
                            fail: 1  ### (1==fail, 0==pass)
                        },
                        dmxdata: {
                            gold: /1.3,
                            used: /1.4,
                            fail: 0  ### (1==fail, 0==pass)
                        },
                        ... ... ...
                    },
                },
            },
        }
        '''
        required_audit_logs = self.get_required_audit_logs_hierarchically()
        self.get_audit_logs_metadata(required_audit_logs)

        for provar in self.result:
            for auditfile in self.result[provar]:
                data = self.result[provar][auditfile]
                goldreslist = self.get_resources_tobe_checked_for_flow(data['flow'], data['subflow'])
                self.logger.debug("Resources that needs to be checked for ({}/{}): {}".format(data['flow'], data['subflow'], goldreslist))
                data['checks'] = {}
                for goldtool, goldversion in goldreslist:
                    goldres = goldtool + goldversion    # goldres = 'dmx/13.2'
                    data['checks'][goldtool] = {'gold':'', 'used':''}
                    data['checks'][goldtool]['gold'] = goldversion
                    golddatetime = self.au.get_datetime_object_for_resource(goldres)

                    try:
                        usedcollection = self.au.get_resolved_list_from_resources_2(data['arcres'])
                        usedtool = goldtool # usedtool = 'dmx'
                        usedversion = usedcollection[usedtool]  # usedversion = '/13.2'
                        usedres = usedtool + usedversion    # usedres = 'dmx/13.2'
                        data['checks'][usedtool]['used'] = usedversion
                        useddatetime = self.au.get_datetime_object_for_resource(usedres)

                        if useddatetime >= golddatetime:
                            # PASS
                            data['checks'][goldtool]['fail'] = 0
                        else:
                            # FAIL
                            data['checks'][goldtool]['fail'] = 1
                            data['errors'].append("Golden({}) / Used({}).".format(goldres, usedres))
                    except Exception as e:
                        data['checks'][goldtool]['fail'] = 1
                        data['errors'].append(str(e))

    def get_resources_tobe_checked_for_flow(self, flow, subflow):
        key = (flow, subflow)
        if key not in self._cache['2bcheck']:
            self._cache['2bcheck'][key] = []
            gadb = self.get_goldenarc_db_for_thread_milestone()
            for ea in gadb:
                if ea['flow'] == flow and ea['subflow'] == subflow:
                    self._cache['2bcheck'][key].append([ea['tool'], ea['version']])
        return self._cache['2bcheck'][key]
   

    def get_goldenarc_db_for_thread_milestone(self):
        if not self._cache['gadb']:
            self._cache['gadb'] = self.db.get_goldenarc_list(thread=self.thread, milestone=self.milestone)
        return self._cache['gadb']


    def get_resource_datetime_obj(self, res):
        if res not in self._cache['resdate']:
            self._cache['resdate'][res] = self.au.get_datetime_object_for_resource(res)
        return self._cache['resdate'][res]


    def get_audit_logs_metadata(self, audit_logs_dict):
        '''
        audit_logs_dict: output from get_required_audit_logs_hierarchically()

        output: {
            (project, variant):
                audit.n1.xml => {arcres: 'arc_resource_string', flow: 'lint', subflow: 'mustfix', ...}
                audit.n2.xml =>  {arcres: 'arc_resource_string', flow: 'lint', subflow: 'mustfix', ...}
                ... ... ...
            (project, variant2):
                audit.n1.xml =>  {arcres: 'arc_resource_string', flow: 'lint', subflow: 'mustfix', ...}
                ... ... ... 
            ... ... ...
        }
        '''
        ret = {}
        for provar in audit_logs_dict:
            ret[provar] = {}
            for af in audit_logs_dict[provar]:
                ret[provar][af] = {'arcres': '', 'flow': '', 'subflow': '', 'errors': []}
                try:
                    tree = xml.etree.ElementTree.parse(os.path.join(self.wsroot, af))
                    root = tree.getroot()
                    env = root.find('environment')
                    flow = root.find('flow')
                    ret[provar][af]['arcres'] = env.attrib['arc_resources']
                    ret[provar][af]['flow'] = flow.attrib['name']
                    ret[provar][af]['subflow'] = flow.attrib['subflow']
                except Exception as e:
                    ret[provar][af]['errors'].append('Failed loading audit file. {}'.format(str(e)))
        self.result = ret
        return ret


    def get_test_runner_obj(self, project, variant, libtype, config, wsroot, milestone, thread, views=None, prel=None):
        self.testrunner = dmx.tnrlib.test_runner.TestRunner(project, variant, libtype, config, wsroot, milestone, thread, log_audit_validation_to_splunk=False, views=views, prel=prel)
        return self.testrunner

    def get_required_audit_logs_hierarchically(self):
        '''
        get all the required audit_logs hierarchically, ie:-
        - all the audit_logs that needs to be validated for a 'variant-release' for all sub ips
        - all the audit_logs that needs to be validated for a 'libtype-release' for all libtypes

        output: {
            (project, variant): [audit.xml, audit.xml, ...],
            (project, variant): [audit.xml, audit.xml, ...],
            ... ... ...
        }
        '''
        data = {}
        cfobj = self.get_config_factory_obj()

        if self.libtype:
            self.logger.info("Working on {} ...".format([self.project, self.variant, self.libtype]))
            tr = self.get_test_runner_obj(self.project, self.variant, self.libtype, self.config, self.wsroot, self.milestone, self.thread, self.views, self.prel)
            tr._cfobj = self._cfobj
            unneeded_deliverables = tr.get_unneeded_deliverables()
            audit_files, required_files = tr.get_required_files(include_all_files=True, unneeded_deliverables=unneeded_deliverables)
            data[(self.project, self.variant)] = audit_files
        else:
            for c in cfobj.flatten_tree():
                if c.is_config():
                    self.logger.info("Working on {} ...".format(c))
                    tr = self.get_test_runner_obj(c.project, c.variant, None, c.config, self.wsroot, self.milestone, self.thread, self.views, self.prel)
                    tr._cfobj = self._cfobj
                    unneeded_deliverables = tr.get_unneeded_deliverables()
                    audit_files, required_files = tr.get_required_files(include_all_files=True, unneeded_deliverables=unneeded_deliverables)
                    data[(c.project, c.variant)] = audit_files

        ### Do some post-processing before returning the results:-
        ### 1. filter out rubbish (files which are less than 3 characters)
        ### 2. filter out files which are not xml (namely, *.f files)
        ### 3. convert them to their relative path to wsroot
        ret = {}
        for provar in data:
            ret[provar] = []
            for af in data[provar]:
                if len(af) < 3:
                    continue
                if af.endswith('.f'):
                    continue

                if af.startswith('/p/psg/') or af.startswith('/nfs/'):
                    rp = os.path.relpath(af, os.path.realpath(self.wsroot))
                elif af.startswith('/'):
                    rp = af.lstrip('/')
                else:
                    rp = af
                ret[provar].append(rp)
        return ret


    def convert_path_relative_to_wsroot(self, filepath, wsroot):
        if filepath.startswith('/p/psg/') or filepath.startswith('/nfs/'):
            rp = os.path.relpath(filepath, os.path.realpath(wsroot))
        elif filepath.startswith('/'):
            rp = filepath.lstrip('/')
        else:
            rp = filepath
        return rp

    def get_config_factory_obj(self):
        self.logger.debug("Getting config factory ...")
        if not hasattr(self, '_cfobj') or not self._cfobj:
            self.logger.debug(" ... config factory object not found. Generating now ...")
            self._cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config)
        return self._cfobj



if __name__ == '__main__':
    main()


