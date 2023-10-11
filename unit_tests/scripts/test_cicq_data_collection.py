#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/unit_tests/scripts/test_cicq_data_collection.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import Mock, patch
import os, sys
import logging
import logging.config
logger = logging.getLogger()

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'scripts')
FILES= os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'scripts', 'files')
print LIB
sys.path.insert(0, LIB)
import shutil
import anytree
import cicq.cicq_data_collection

class TestCicqDataCollection(unittest.TestCase):

    def setUp(self):
        self.c = cicq.cicq_data_collection

    def test__001__dict2obj_key_contain_parent(self):
        myDict = { 'parent' : 'value1'}
        ins = self.c.Dict2Obj(myDict) 
        self.assertEqual('value1', ins.parent_id)

    def test__002__dict2obj_key_contain_parent_no_parent_key(self):
        myDict = { 'parent' : 'value1'}
        ins = self.c.Dict2Obj(myDict) 
        with self.assertRaises(AttributeError):
            ins.parent

    def test__003__dict2obj_key_contain_id(self):
        myDict = { 'id' : 'value1'}
        ins = self.c.Dict2Obj(myDict) 
        self.assertEqual('value1', ins.name)

    def test__004__dict2obj_key_contain_id_got_id_key(self):
        myDict = { 'id' : 'value1'}
        ins = self.c.Dict2Obj(myDict) 
        self.assertEqual('value1', ins.id)

    def test__005__treedict(self):
        myDict = { 'parent' : 'value1'}
        ins = self.c.TreeDict(myDict) 
        self.assertEqual('value1', ins.parent_id)

    def test__006__treedict_contain_parent_no_parent_key(self):
        myDict = { 'parent' : 'value1'}
        ins = self.c.TreeDict(myDict) 
        self.assertIsNone(ins.parent)

    def test__007__create_result_folder(self):
        output = 'myoutput'
        self.c.create_result_folder(output)
        self.assertTrue(os.path.isdir(output))
        self.assertTrue(os.path.isdir(output+'/arcjobs'))
        self.assertTrue(os.path.isdir(output+'/upload'))
        shutil.rmtree(output)

    def test__008__get_json_file_from_arc_job_pass(self):
        arcid = '356146640'
        output = 'myoutput'
        self.c.create_result_folder(output)
        ret = 'myoutput/arcjobs/356146640'
        self.assertEqual(ret, self.c.get_json_file_from_arc_job(arcid, output))
        shutil.rmtree(output)

    def test__009__get_json_file_from_arc_job_no_ouput_directory_create(self):
        arcid = '356146640'
        output = 'myoutput'
        with self.assertRaises(SystemExit):
            self.c.get_json_file_from_arc_job(arcid, output)

    def test__010__get_json_file_from_arc_job_ivalid_arc_id(self):
        arcid = '35610'
        output = 'myoutput'
        self.c.create_result_folder(output)
        with self.assertRaises(SystemExit):
            self.c.get_json_file_from_arc_job(arcid, output)
        shutil.rmtree(output)


    def test__011__read_json_file(self):
        jsonfile = FILES + '/356146640'
        project = 'n5soc'
        ip = 'acr_barak_quad2'
        thread = 'wplimrun3'
        data = self.c.read_json_file(jsonfile, project, ip, thread)
        all_keys = ['cicq_thread', 'set_create_at', 'family', 'resource_free', 'set_running_at', 'set_done_at', 'cicq_topcell', 'id', 'priority', 'requirements', 'cicq_deliverable', 'grp', 'set_queued_at', 'storage', 'elapsed_time', 'parent_id', 'cicq_ip', 'cicq_project', 'cicq_checker', 'type', 'resources', 'status', 'iwd', 'set_nb_done_at', 'nbqslot', 'return_code', 'host', 'root_parent', 'user', 'name', 'nb_job', 'command', 'os', 'lock', 'set_passed_at', 'mem', 'nb_name', 'local', 'nb_depends_on', 'nbq']

        for ea_d in data:
            for k in ea_d.__dict__.keys() :
                self.assertIn(k, all_keys) 

    def test__012__modified_json_data(self):
        jsonfile = FILES + '/356146640'
        project = 'n5soc'
        ip = 'acr_barak_quad2'
        thread = 'wplimrun3'
        data = self.c.read_json_file(jsonfile, project, ip, thread)
        data, rootNode = self.c.modified_json_data(data)
    

        # if contain parent, then cicq_topcell, cicq_deliverable and cicq_checker should follow parent value
        for ea_d in data:
            ref_d = ea_d.parent
            if ref_d and ref_d.cicq_topcell:
                self.assertEqual(ea_d.cicq_topcell, ref_d.cicq_topcell)

            if ref_d and ref_d.cicq_deliverable:
                self.assertEqual(ea_d.cicq_deliverable, ref_d.cicq_deliverable)

            if ref_d and ref_d.cicq_checker:
                self.assertEqual(ea_d.cicq_checker, ref_d.cicq_checker)


    def test__013__modified_json_data_rootNode_isroot(self):
        jsonfile = FILES + '/356146640'
        project = 'n5soc'
        ip = 'acr_barak_quad2'
        thread = 'wplimrun3'
        data = self.c.read_json_file(jsonfile, project, ip, thread)
        data, rootNode = self.c.modified_json_data(data)
    
        self.assertFalse(rootNode.parent)



if __name__ == '__main__':
    unittest.main()
