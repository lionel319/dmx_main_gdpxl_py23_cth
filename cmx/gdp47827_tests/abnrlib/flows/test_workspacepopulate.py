#!/usr/intel/pkgs/python3/3.9.6/bin/python3
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
import UsrIntel.R1

import unittest
from mock import patch
import os, sys
import datetime
import time
import tempfile
from mock import patch
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))), 'lib', 'python')
sys.path.insert(0, LIB)

import cmx.abnrlib.flows.workspacepopulate
import cmx.utillib.utils
class TestWorkspacePopulateError(Exception): pass

class TestWorkspacePopulate(unittest.TestCase):

    def setUp(self):
        self.dmxmoab = cmx.abnrlib.flows.dmxmoab
        self.project = 'i18asockm'
        self.ip = 'liotest3'
        self.bom = 'dev'
        os.environ['GIT_REPOS'] = '/nfs/site/disks/psg.git.001'
        os.environ['IP_MODELS'] = '/nfs/site/disks/psg.mod.000'
        os.environ['CTH_SETUP_CMD'] = 'KM5A0P00_FE_RC'


        # setup dev workspace
        self.workarea_dev = '/tmp/cmx_reg_workarea/cth_dev' 
        os.system('mkdir -p {}'.format(self.workarea_dev)) 
        os.environ['WORKAREA'] = self.workarea_dev
        self.my_class_dev = cmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(self.project, self.ip, self.bom, 'cthfe') 
        self.my_class_dev.run()

        # setup snap workspace
        self.workarea_snap = '/tmp/cmx_reg_workarea/cthfe_snap' 
        os.system('mkdir -p {}'.format(self.workarea_snap)) 
        os.environ['WORKAREA'] = self.workarea_snap
        self.my_class_snap = cmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(self.project, self.ip, 'with_cthfe_snap', 'cthfe') 
        self.my_class_snap.run()

        # setup rel workspace
        self.workarea_rel = '/tmp/cmx_reg_workarea/cthfe_rel' 
        os.system('mkdir -p {}'.format(self.workarea_rel)) 
        os.environ['WORKAREA'] = self.workarea_rel
        self.my_class_rel = cmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(self.project, self.ip, 'with_cthfe_rel', 'cthfe') 
        self.my_class_rel.run()

    def tearDown(self):
        os.system('chmod 777 /tmp/cmx_reg_workarea/* -R ; rm -rf /tmp/cmx_reg_workarea/')
        pass

    def test_020___get_ip_models_with_cthfe_bom(self):
        result = '/nfs/site/disks/psg.mod.000/release/liotest3/'
        self.assertEqual(result, self.my_class_dev.get_ip_models(self.project, self.ip, 'cthfe', 'dev'))

    def test_021___get_ip_models_with_wipdev_cthfe_bom(self):
        result = '/nfs/site/disks/psg.mod.000/release/liotest3/'
        self.assertEqual(result, self.my_class_dev.get_ip_models(self.project, self.ip, 'cthfe', 'wipdev'))

    def test_022___get_ip_models_with_snap_cthfe_bom(self):
        result = '/nfs/site/disks/psg.mod.000/release/liotest3/'
        self.assertEqual(result, self.my_class_snap.get_ip_models(self.project, self.ip, 'cthfe', 'snap-'))

    def test_023___get_ip_models_with_rel_cthfe_bom(self):
        result = '/nfs/site/disks/psg.mod.000/release/liotest3/liotest3-a0-23ww21c'
        self.assertEqual(result, self.my_class_rel.get_ip_models(self.project, self.ip, 'cthfe', 'REL1.0KM2revA0__23ww215a'))

    def test_030___create_ip_deliverable_directory_and_symlink(self):
        os.chdir('/tmp/cmx_reg_workarea')
        os.system('mkdir -p ip_model')
        self.my_class_dev.create_ip_deliverable_directory_and_symlink('ip', 'deliverable', '/tmp/cmx_reg_workarea/ip_model')
        self.assertTrue(os.path.islink('/tmp/cmx_reg_workarea/ip/deliverable'))



if __name__ == '__main__':
    logging.basicConfig(format="[%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(), level=logging.DEBUG)

    unittest.main()

