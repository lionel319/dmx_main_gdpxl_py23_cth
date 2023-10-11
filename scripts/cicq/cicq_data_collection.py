#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from builtins import str
from builtins import object
import logging
import argparse
import os
import subprocess
import sys
import re
import unicodedata
import json
import dmx.utillib.loggingutils
import copy

from dmx.utillib.utils import run_command
#sys.path.insert(0, '/nfs/site/disks/da_infra_1/users/wplim/testing/cicq/logging/anytree-2.8.0')
from anytree import NodeMixin, RenderTree, PostOrderIter
class GatherDataError(Exception): pass

logger = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)

class Dict2Obj(object):
    """
    Turns a dictionary into a class
    """
    #----------------------------------------------------------------------
    def __init__(self, dictionary):
        """Constructor"""
        '''
        self.name = 'abc'
        self.parent_id = dictionary.get('parent')
        self.id = dictionary.get('id')
        '''
        if dictionary:
            for key in dictionary:
                if key == 'parent':
                    converted_key = 'parent_id'
                    setattr(self, converted_key, dictionary[key])
                elif key == 'id':
                    converted_key = 'name'
                    setattr(self, converted_key, dictionary[key])
                    setattr(self, key, dictionary[key])
                else:
                    setattr(self, key, dictionary[key])

class TreeDict(NodeMixin, Dict2Obj):

    def __init__(self, data):
        #super(TreeDict, self).__init__()
        super(TreeDict, self).__init__(data)

def main():
    args = _add_args()
    if args.debug:
        logger = setup_logger(level=logging.DEBUG)
    else:
        logger = setup_logger(level=logging.INFO)

    project = args.project
    ip = args.ip
    thread = args.thread
    arcid = args.arcjob
    output = args.output
    bnum = args.bnum

    create_result_folder(output)
    json_file = get_json_file_from_arc_job(arcid, output)
    #write_json_str_to_file(loaded_str, 'results/arcjobs', arcid)
    post_process_data(json_file, project, ip, thread, output, bnum)

'''
def get_arc_job_from_teamcity():
    all_arc_job = []
    api = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(project, ip, thread, dryrun=False)
    all_builds = api.get_all_builds()
    all_builds =  json.loads(all_builds)
    all_build = all_builds['build']
    for build in all_build:
        if 'AgentRefresh' in build['buildTypeId']: continue
        arc_job = api.get_build_arc_job_id(build['id'])
        all_arc_job.append(arc_job)
'''
def get_actual_run_time(rootNode, largest_end_time=0):
    for node in PostOrderIter(rootNode):
        if node.is_leaf:
            #node.actual_runtime = node.elapsed_time 
            # when this script is run, the job that geenrating ndjson is stille xecuting thus will not have a valid runtime
            try:
                node.actual_runtime = int(node.set_nb_done_at) - int(node.set_create_at)
                node.actual_endtime = node.set_nb_done_at
            except:
                node.actual_runtime = 0 
                node.actual_endtime = 0
                node.set_nb_done_at = 0
        if node.descendants:
            print(max([x.actual_runtime for x in node.children]))
            #node.actual_runtime = int(max([int(x.actual_runtime) for x in node.children] + [int(node.elapsed_time)]))
            node.actual_endtime = int(max([int(x.actual_endtime) for x in node.children] + [int(node.set_nb_done_at)]))
            node.actual_runtime = int(node.actual_endtime) - int(node.set_create_at)
'''
def _get_actual_run_time(node, largest_end_time=0):
    #if node.set_nb_done_at > largest_end_time:
    #    largest_end_time = node.set_nb_done_at
    #else:
    #    node.actual_run_time = int(node.set_create_at) - int(node.set_nb_done_at) 
    print node.depth
    if node.children :
        for childnode in node.children:
            end_time = get_actual_run_time(childnode)

            if end_time > largest_end_time:
                largest_end_time = end_time
        #node.actual_runtime = int(largest_end_time) - int(node.set_create_at)
        node.actual_runtime = int(node.set_create_at) - int(largest_end_time)
        return largest_end_time
    else: 
        node.actual_runtime = node.elapsed_time
        return node.set_nb_done_at 
'''

def post_process_data(json_file, project, ip, thread, output, bnum):
    data = read_json_file(json_file, project, ip, thread)
    modified_data, rootNode = modified_json_data(data)
    fo = open(output+'/upload/'+os.path.basename(json_file), 'w+')

    get_actual_run_time(rootNode)
    for pre, fill, node in RenderTree(rootNode):
    #    print node.id, node.name, node.cicq_topcell
        #print("%s %s" % (pre, node.id) )
       # pre = pre.encode('ascii', 'ignore').decode('ascii')
        #print(" %s %s %s %s %s %s" % (pre.encode('utf-8'), node.id, node.name, node.root_parent, node.cicq_topcell, node.cicq_deliverable, node.cicq_checker))
        import datetime as dt
        a = dt.datetime.utcfromtimestamp(float(node.set_create_at)).strftime("%Y/%m/%d %H:%M") 
        b = dt.datetime.utcfromtimestamp(float(node.set_nb_done_at)).strftime("%Y/%m/%d %H:%M") 
        c = dt.datetime.utcfromtimestamp(float(node.actual_endtime)).strftime("%Y/%m/%d %H:%M") 
        d = dt.datetime.utcfromtimestamp(float(node.actual_runtime)).strftime("%Y/%m/%d %H:%M") 
        d = node.actual_runtime
        e = dt.datetime.utcfromtimestamp(float(node.actual_endtime)).strftime("%Y/%m/%d %H:%M") 
        print("{} {} {} {} {} {} {} {} {} {} {}".format(pre.encode('utf-8'),  node.id, node.name, node.root_parent, node.cicq_topcell, node.cicq_deliverable, node.cicq_checker, str(a), str(b), str(c), str(d)))

    #a =  node.__dict__
        d2 = copy.deepcopy(node.__dict__)
        d2['bnum'] = bnum
        try:
            del d2['_NodeMixin__parent']
        except:
            pass
        try:
            del d2['_NodeMixin__children']
        except:
            pass
        fo.write(json.dumps(d2)+'\n')
    fo.close()

def create_result_folder(output):
    if not os.path.exists(output):
        os.mkdir(output)
    if not os.path.exists(output + '/arcjobs'):
        os.mkdir(output+'/arcjobs')
    if not os.path.exists(output + '/upload'):
        os.mkdir(output+'/upload')


def modified_json_data(data):
    
    for ea_d in data:
        for ref_data in data:
            if ea_d.parent_id == ref_data.id:
                ea_d.parent = ref_data
                if ref_data.cicq_topcell!= '' and ea_d.cicq_topcell == '':
                    ea_d.cicq_topcell=ref_data.cicq_topcell
                #else:
                #    ea_d.cicq_topcell = ea_d.name
    
                if ref_data.cicq_deliverable!= '':
                    ea_d.cicq_deliverable=ref_data.cicq_deliverable
               # else:
               #     ea_d.cicq_deliverable = ea_d.name
    
                if ref_data.cicq_checker!= '':
                    ea_d.cicq_checker=ref_data.cicq_checker
              #  else:
              #      ea_d.cicq_checker = ea_d.name
    
                if ref_data.name!= '' and ea_d.name is None:
                    ea_d.name=ref_data.name
    
        # if no deliverable no topcell no checker name
        # mean it is cicq job, reuse jobname
    for ea_d in data:
        if ea_d.parent is None:
            rootNode = ea_d
        ''' 
        if ea_d.cicq_topcell == '':
            ea_d.cicq_topcell = ea_d.name
            #ea_d.cicq_topcell == ea_d.name            
        if ea_d.cicq_deliverable == '':
            ea_d.cicq_deliverable = ea_d.name
        if ea_d.cicq_checker == '':
            ea_d.cicq_checker = ea_d.name
        '''
    return data, rootNode

def read_json_file(filename, project, ip, thread):
    cicq_project = project
    cicq_ip = ip
    cicq_thread = thread
    root_id = os.path.basename(filename)
    data = [] 

    with open(filename) as f:
        for line in f:
            cicq_deliverable = ''
            cicq_checker = ''
            cicq_topcell = ''
            j_content = json.loads(line)
    
           # jobObj = TreeDict(j_content)
            jobObj = TreeDict(data=j_content)
           # jobObj = Dict2Obj(j_content)
    
            jobname = str(j_content['name'])
            match = re.search('ipqc_top_(\S+)?\.(\S+)?', jobname)
            if match:
                cicq_ip = match.group(1)
                cicq_deliverable = match.group(2)
    
            match = re.search('{}\.(\S+)?\.(\S+)?\.(\S+)?'.format(cicq_ip), jobname)
            if match:
                cicq_topcell = match.group(1)
                cicq_deliverable = match.group(2)
                cicq_checker = match.group(3)
            jobObj.cicq_topcell= cicq_topcell
            jobObj.cicq_deliverable= cicq_deliverable
            jobObj.cicq_checker= cicq_checker
            jobObj.root_parent= root_id
            jobObj.cicq_thread= cicq_thread
            jobObj.cicq_ip= cicq_ip
            jobObj.cicq_project= cicq_project
            try:
                jobObj.set_nb_done_at = jobObj.set_done_at
            except:
                pass

            jobObj.cicq_project= cicq_project
            data.append(jobObj)
    return data 

def get_json_file_from_arc_job(arcid, output):
    arcjob_result = output + '/arcjobs'
    output_file = arcjob_result + '/' + arcid
    cmd = 'curl http://psg-sc-arc-web01.sc.intel.com/arc/api/jobtree/{0}/ | jq -c \'.[]\' > {1}'.format(arcid, output_file)
    exitcode, stdout, stderr = run_command(cmd)
    if not exitcode or not stderr:
        return output_file
    else:
        logger.error(stderr)
        sys.exit(1)
      #  return loaded_json

def write_json_str_to_file(jstr, output, arcid):
    with open(output+'/'+arcid, 'w+') as fo:
        fo.write(jstr)




def _add_args():
    ''' Parse the cmdline arguments '''
    # Simple Parser Example
    parser = argparse.ArgumentParser(description="Desc")
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument("-t", "--thread", help="thread name")
    optional.add_argument("-p", "--project", help="project name")
    optional.add_argument("-i", "--ip", help="ip name")
    optional.add_argument("-a", "--arcjob", help="arcjob")
    optional.add_argument("-o", "--output", default='results', help="output")
    optional.add_argument("-d", "--debug", action='store_true', help="debug level")
    optional.add_argument("--bnum", help="buildnum")
    args = parser.parse_args()


    return args


def setup_logger(name=None, level=logging.INFO):
    ''' Setup the logger for the logging module.

    If this is a logger for the top level (root logger),
        name=None
    else
        the __name__ variable from the caller should be passed into name

    Returns the logger instant.
    '''

    if name:
        LOGGER = logging.getLogger(name)
    else:
        LOGGER = logging.getLogger()

    if level <= logging.DEBUG:
        fmt = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
    else:
        fmt = "%(levelname)s: %(message)s"

    logging.basicConfig(format=fmt)
    LOGGER.setLevel(level)

    return LOGGER


if __name__ == '__main__':
    sys.exit(main())

   
