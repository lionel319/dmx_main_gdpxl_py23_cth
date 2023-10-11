#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_workspaceupdate.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $


import unittest
from mock import patch
import os, sys
import datetime
import time
import tempfile
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.abnrlib.flows.workspaceupdate
import dmx.utillib.utils
import dmx.abnrlib.config_factory

class MockClass():
    
    def get_config_factory_object(self):
        return True

class TestFlowWorkspaceUpdate(unittest.TestCase):

    def setUp(self):
        self.wp = dmx.abnrlib.flows.workspaceupdate
        self.project = 'i10socfm'
        self.ip = 'liotest1'
        self.bom = 'rel_and_dev'
        self.wsname = 'regtestws'
        self.envvar = 'DMX_WORKSPACE'
        
        self.wsdisk = '/tmp'
        os.environ[self.envvar] = self.wsdisk

    def tearDown(self):
        self._undefine_envvar()


    def _undefine_envvar(self):
        os.environ.pop(self.envvar, None)
        os.environ.pop('DB_FAMILIES', None)


    def test_100___workspace_disk___not_defined(self):
        self._undefine_envvar()
        with self.assertRaisesRegexp(Exception, '.*DMX_WORKSPACE not defined.*'):
            self.wp.WorkspaceUpdate(self.wsname)


    def test_502___get_dmx_cmd(self):
        w = self.wp.WorkspaceUpdate(self.wsname)
        ret = w._get_dmx_cmd()
        self.assertRegexpMatches(ret, '^.+dmx workspace update -w {} -o .* --debug.*; '.format(self.wsname))

    
    def test_503___get_final_cmd(self):
        w = self.wp.WorkspaceUpdate(self.wsname)
        os.environ['DB_FAMILIES'] = 'a b c'
        ret = w._get_final_cmd()
        self.assertRegexpMatches(ret, '^/p/psg/da/infra/admin/setuid/tnr_ssh -q localhost \'arc .+ -- \'"\'"\'setenv DMX_WORKSPACE .+;setenv DB_FAMILIES .+dmx workspace update -w {} -o .*--debug.*;.*\'"\'"\'\''.format(self.wsname))
    
               
    def test_701__read_config_file(self):
        result = {'va vb': 'la lb'} 
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'variants_libtypes')
        w = self.wp.WorkspaceUpdate(self.wsname)
        self.assertEqual(result, w.read_config_file(cfgfile))
        
    @patch('dmx.abnrlib.config_factory.ConfigFactory.get_deliverable_type_from_config_factory_object') 
    @patch('dmx.abnrlib.flows.workspaceupdate.WorkspaceUpdate.read_config_file') 
    @patch('dmx.abnrlib.flows.workspaceupdate.os.chdir')
    def test_801__get_dict_from_config__all(self, mock_os_chdir, mock_read_config_file, mock_get_deliverable_type_from_config_factory_object):
        mock_os_chdir.return_value = True
        result = {'liotest1': 'sta'}
        mock_read_config_file.return_value = {'*':'*'} 
        mock_get_deliverable_type_from_config_factory_object.return_value = {'liotest1': ['sta']}
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'variants_libtypes')
        w = self.wp.WorkspaceUpdate(self.wsname)
        self.assertEqual(result, w.get_dict_from_config(cfgfile, mock_get_deliverable_type_from_config_factory_object.return_value))
        
    @patch('dmx.abnrlib.config_factory.ConfigFactory.get_deliverable_type_from_config_factory_object') 
    @patch('dmx.abnrlib.flows.workspaceupdate.WorkspaceUpdate.read_config_file') 
    @patch('dmx.abnrlib.flows.workspaceupdate.os.chdir')
    def test_802__get_dict_from_config__none(self, mock_os_chdir, mock_read_config_file, mock_get_deliverable_type_from_config_factory_object):
        mock_os_chdir.return_value = True
        result = {'liotest1': 'sta'}
        mock_read_config_file.return_value = {'liotest1':'sta'} 
        mock_get_deliverable_type_from_config_factory_object.return_value = {}
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'variants_libtypes')
        w = self.wp.WorkspaceUpdate(self.wsname)
        self.assertEqual({}, w.get_dict_from_config(cfgfile, mock_get_deliverable_type_from_config_factory_object.return_value))
 
    @patch('dmx.abnrlib.config_factory.ConfigFactory.get_deliverable_type_from_config_factory_object') 
    @patch('dmx.abnrlib.flows.workspaceupdate.WorkspaceUpdate.read_config_file') 
    @patch('dmx.abnrlib.flows.workspaceupdate.os.chdir')
    def test_803__get_dict_from_config__multiple(self, mock_os_chdir, mock_read_config_file, mock_get_deliverable_type_from_config_factory_object):
        mock_os_chdir.return_value = True
        result = {'liotest1': 'sta'}
        mock_read_config_file.return_value = {'liotest1':'sta ipspec reldoc', 'testing':'sta'} 
        mock_get_deliverable_type_from_config_factory_object.return_value = {'liotest1': ['sta','ipspec'], 'testing': ['sta']}
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'variants_libtypes')
        w = self.wp.WorkspaceUpdate(self.wsname)
        self.assertEqual({'liotest1': 'sta ipspec', 'testing': 'sta'}, w.get_dict_from_config(cfgfile, mock_get_deliverable_type_from_config_factory_object.return_value))

    @patch('dmx.abnrlib.config_factory.ConfigFactory.get_deliverable_type_from_config_factory_object') 
    @patch('dmx.abnrlib.flows.workspaceupdate.WorkspaceUpdate.read_config_file') 
    @patch('dmx.abnrlib.flows.workspaceupdate.os.chdir')
    def test_804__get_dict_from_config__multiple2(self, mock_os_chdir, mock_read_config_file, mock_get_deliverable_type_from_config_factory_object):
        mock_os_chdir.return_value = True
        result = {'soc_aps_ram': 'ipspec', 'soc_dma_wrapper': 'ipspec', 'soc_i2c_wrapper': 'ipspec', 'soc_hps_pinmux': 'ipspec', 'flxpll_lib': 'ipspec', 'soc_pss_noc': 'ipspec', 'soc_aps_bridge': 'ipspec', 'soc_nand_ip': 'ipspec', 'intfclib': 'ipspec', 'soc_ecc_ram': 'ipspec', 'soc_reset_manager': 'ipspec', 'soc_ssi_master_wrapper': 'ipspec', 'soc_hps_nand_wrapper': 'ipspec', 'soc_watchdog_wrapper': 'ipspec', 'osc_lib': 'ipspec', 'por_lib': 'ipspec', 'soc_hps_psi': 'ipspec', 'soc_usbotg_wrapper': 'ipspec', 'soc_smmu_wrapper': 'ipspec', 'soc_hps': 'ipspec', 'soc_mobile_storage_ip': 'ipspec', 'soc_hps_idvp': 'ipspec', 'soc_uart_wrapper': 'ipspec', 'soc_common': 'ipspec', 'soc_security_manager': 'ipspec', 'soc_clock_manager': 'ipspec', 'soc_cs_wrapper': 'ipspec', 'soc_hps_dedio': 'ipspec', 'ip752hppll_lib': 'ipspec', 'soc_ccu_wrapper': 'ipspec', 'soc_fpga_bridge_lib': 'ipspec', 'intfclibhpsfm': 'ipspec', 'soc_timer_wrapper': 'ipspec', 'soc_serial_ctrl': 'ipspec', 'soc_system_manager': 'ipspec', 'soc_aps': 'ipspec', 'soc_gic_wrapper': 'ipspec', 'soc_cs_lib': 'ipspec', 'soc_std_macro': 'ipspec', 'soc_hps_wrapper': 'ipspec', 'soc_gpio_wrapper': 'ipspec', 'soc_pss': 'reldoc ipspec', 'soc_hps_fpga_bridges': 'ipspec', 'jtag_common': 'ipspec', 'soc_hps_mobile_storage_wrapper': 'ipspec', 'cnt_shared': 'ipspec', 'soc_hps_ram_wrappers': 'ipspec', 'soc_mpu_cortexa53': 'reldoc ipspec', 'soc_ssi_slave_wrapper': 'ipspec', 'physintspecfm': 'ipspec', 'soc_emac_wrapper': 'ipspec', 'soc_ca53_cpu': 'ipspec'}

        mock_read_config_file.return_value = {'soc_pss soc_mpu_cortexa53': 'reldoc', '*': 'ipspec'} 
        mock_get_deliverable_type_from_config_factory_object.return_value = {'soc_aps_ram': ['cvrtl', 'dftdsm', 'lint', 'reldoc', 'rtlcompchk', 'rtl', 'ipxact', 'cdc', 'bcmrbc', 'dv', 'ipspec'], 'soc_dma_wrapper': ['cdc', 'pv', 'sdf', 'oa', 'upf_rtl', 'schmisc', 'r2g2', 'dv', 'gln_filelist', 'bcmrbc', 'lint', 'fvsyn', 'rtl', 'cvsignoff', 'rv', 'laymisc', 'timemod', 'sta', 'complibphys', 'rcxt', 'syn', 'oasis', 'rtlcompchk', 'ipspec', 'complib', 'stamod', 'cdl', 'dftdsm', 'ipxact', 'fvpnr', 'upf_netlist', 'ippwrmod', 'pnr', 'reldoc', 'cvrtl'], 'soc_i2c_wrapper': ['lint', 'dftdsm', 'cvrtl', 'rtlcompchk', 'rdf', 'bcmrbc', 'reldoc', 'rtl', 'interrba', 'dv', 'cdc', 'ipxact', 'ipspec'], 'soc_hps_pinmux': ['rtl', 'ipspec', 'ipxact', 'dv', 'rtlcompchk', 'cdc', 'bcmrbc', 'lint', 'dftdsm', 'reldoc', 'cvrtl'], 'flxpll_lib': ['oa', 'rv', 'stamod', 'fv', 'ipspec', 'yx2gln', 'lint', 'oasis', 'upf_netlist', 'rdf', 'schmisc', 'interrba', 'complibphys', 'complib', 'ippwrmod', 'fetimemod', 'reldoc', 'rtl', 'rcxt', 'timemod', 'circuitsim', 'oa_sim', 'dv', 'laymisc', 'cdl', 'bcmrbc', 'rtlcompchk', 'pv', 'ilib', 'ipfloorplan'], 'soc_aps_bridge': ['ipxact', 'rtlcompchk', 'lint', 'rtl', 'ipspec', 'reldoc', 'cdc'], 'soc_nand_ip': ['dv', 'cvrtl', 'interrba', 'rtl', 'lint', 'reldoc', 'cdc', 'dftdsm', 'rtlcompchk', 'ipxact', 'rdf', 'bcmrbc', 'ipspec'], 'intfclib': ['reldoc', 'ipspec', 'intfc'], 'soc_ecc_ram': ['ipspec', 'rdf', 'dv', 'rtlcompchk', 'reldoc', 'interrba', 'cvrtl', 'lint', 'cdc', 'ipxact', 'bcmrbc', 'rtl', 'dftdsm'], 'soc_reset_manager': ['rtl', 'lint', 'rtlcompchk', 'cdc', 'ipspec', 'dv', 'dftdsm', 'ipxact', 'cvrtl', 'bcmrbc', 'reldoc'], 'soc_ssi_master_wrapper': ['reldoc', 'ipspec', 'cdc', 'ipxact', 'bcmrbc', 'dv', 'dftdsm', 'rtlcompchk', 'rtl', 'cvrtl', 'lint'], 'soc_hps_nand_wrapper': ['reldoc', 'ipspec', 'dv', 'dftdsm', 'cdc', 'rtlcompchk', 'rtl', 'cvrtl', 'bcmrbc', 'lint', 'ipxact'], 'soc_watchdog_wrapper': ['cvrtl', 'dftdsm', 'ipxact', 'bcmrbc', 'ipspec', 'rtlcompchk', 'reldoc', 'lint', 'dv', 'rtl', 'cdc'], 'osc_lib': ['rtlcompchk', 'reldoc', 'rv', 'ipspec', 'yx2gln', 'rcxt', 'complibphys', 'oa', 'bcmrbc', 'ippwrmod', 'stamod', 'timemod', 'complib', 'dv', 'pv', 'ilib', 'upf_netlist', 'oasis', 'rtl', 'ipfloorplan', 'schmisc', 'lint', 'interrba', 'laymisc', 'fv', 'fetimemod', 'rdf', 'circuitsim', 'oa_sim', 'cdl'], 'por_lib': ['rtlcompchk', 'pv', 'laymisc', 'oasis', 'ipspec', 'reldoc', 'yx2gln', 'interrba', 'cdl', 'rv', 'complibphys', 'fetimemod', 'complib', 'schmisc', 'rtl', 'fv', 'ilib', 'rcxt', 'dv', 'lint', 'circuitsim', 'oa', 'oa_sim', 'ippwrmod', 'ipfloorplan', 'upf_netlist', 'timemod', 'bcmrbc', 'stamod', 'rdf'], 'soc_hps_psi': ['ipspec', 'reldoc', 'rtl', 'dv', 'cvrtl', 'ipxact', 'dftdsm', 'bcmrbc', 'lint', 'cdc', 'rtlcompchk'], 'soc_usbotg_wrapper': ['reldoc', 'cvrtl', 'rtlcompchk', 'lint', 'cdc', 'rtl', 'dv', 'ipxact', 'dftdsm', 'bcmrbc', 'ipspec'], 'soc_smmu_wrapper': ['rtl', 'rtlcompchk', 'cvrtl', 'reldoc', 'lint', 'dv', 'cdc', 'bcmrbc', 'dftdsm', 'ipspec', 'ipxact'], 'soc_hps': ['cdl', 'pv', 'rv', 'rcxt', 'laymisc', 'upf_rtl', 'ipxact', 'dv', 'cdc', 'fvpnr', 'schmisc', 'complib', 'cvrtl', 'ipspec', 'rtl', 'syn', 'fvsyn', 'pnr', 'upf_netlist', 'gln_filelist', 'sta', 'cvsignoff', 'oa', 'r2g2', 'complibphys', 'oasis', 'lint', 'bcmrbc', 'rtlcompchk', 'timemod', 'ippwrmod', 'reldoc', 'stamod', 'dftdsm'], 'soc_mobile_storage_ip': ['reldoc', 'lint', 'dftdsm', 'cdc', 'ipspec', 'bcmrbc', 'rtl', 'ipxact', 'rdf', 'dv', 'cvrtl', 'rtlcompchk', 'interrba'], 'soc_uart_wrapper': ['rtl', 'bcmrbc', 'dftdsm', 'rtlcompchk', 'ipxact', 'rdf', 'lint', 'ipspec', 'cvrtl', 'reldoc', 'interrba', 'cdc', 'dv'], 'soc_pss_noc': ['cdc', 'rtlcompchk', 'reldoc', 'bcmrbc', 'dftdsm', 'rtl', 'dv', 'cvrtl', 'lint', 'ipspec', 'ipxact'], 'soc_common': ['reldoc', 'ipspec', 'rtl', 'cdc', 'rtlcompchk', 'lint', 'rdf', 'dv', 'cvrtl', 'dftdsm', 'interrba', 'ipxact', 'bcmrbc'], 'soc_security_manager': ['ipxact', 'cdc', 'lint', 'ipspec', 'cvrtl', 'bcmrbc', 'reldoc', 'rtlcompchk', 'rtl', 'dftdsm', 'dv'], 'soc_clock_manager': ['r2g2', 'pnr', 'cvsignoff', 'oa', 'oasis', 'complibphys', 'complib', 'upf_netlist', 'fvsyn', 'ipspec', 'rtlcompchk', 'dv', 'cdl', 'cdc', 'fvpnr', 'laymisc', 'sdf', 'sta', 'lint', 'gln_filelist', 'stamod', 'bcmrbc', 'ipxact', 'syn', 'reldoc', 'cvrtl', 'ippwrmod', 'dftdsm', 'rcxt', 'pv', 'schmisc', 'rv', 'timemod', 'rtl', 'upf_rtl'], 'soc_cs_wrapper': ['dv', 'rtlcompchk', 'cvrtl', 'ipspec', 'cdc', 'ipxact', 'lint', 'rtl', 'reldoc', 'dftdsm', 'bcmrbc'], 'soc_hps_idvp': ['rtl', 'reldoc', 'rtlcompchk', 'lint', 'bcmrbc', 'ipspec', 'ipxact', 'cdc', 'cvrtl', 'dv', 'dftdsm'], 'soc_hps_dedio': ['cvrtl', 'ipxact', 'bcmrbc', 'rtlcompchk', 'lint', 'cdc', 'reldoc', 'dv', 'rtl', 'dftdsm', 'ipspec'], 'ip752hppll_lib': ['dftdsm', 'ipxact', 'pnr', 'sdf', 'pv', 'fvsyn', 'sta', 'syn', 'cvimpl', 'schmisc', 'circuitsim', 'rtl', 'rv', 'cvrtl', 'fvpnr', 'cge', 'oa', 'interrba', 'rdf', 'gln_filelist', 'ipspec', 'stamod', 'cdl', 'bcmrbc', 'ippwrmod', 'cdc', 'upf_netlist', 'rcxt', 'lint', 'timemod', 'reldoc', 'cvsignoff', 'fetimemod', 'dfx', 'oasis', 'rtlcompchk', 'ilib', 'dv', 'pvector', 'upf_rtl', 'complibphys', 'r2g2', 'gp', 'complib', 'laymisc'], 'soc_ccu_wrapper': ['lint', 'dv', 'dftdsm', 'ipspec', 'ipxact', 'bcmrbc', 'cvrtl', 'rtlcompchk', 'reldoc', 'cdc', 'rtl'], 'soc_fpga_bridge_lib': ['interrba', 'lint', 'reldoc', 'dftdsm', 'rtlcompchk', 'rtl', 'cdc', 'ipxact', 'bcmrbc', 'ipspec', 'dv', 'cvrtl', 'rdf'], 'intfclibhpsfm': ['reldoc', 'ipspec', 'intfc'], 'soc_timer_wrapper': ['bcmrbc', 'cvrtl', 'rtlcompchk', 'cdc', 'ipspec', 'lint', 'dftdsm', 'dv', 'ipxact', 'reldoc', 'rtl'], 'soc_serial_ctrl': ['cdc', 'dv', 'dftdsm', 'bcmrbc', 'lint', 'ipxact', 'rtlcompchk', 'cvrtl', 'rtl', 'reldoc', 'ipspec'], 'soc_system_manager': ['dftdsm', 'dv', 'reldoc', 'cvrtl', 'rtl', 'lint', 'cdc', 'ipspec', 'ipxact', 'rtlcompchk', 'bcmrbc'], 'soc_aps': ['rtlcompchk', 'ippwrmod', 'dv', 'gln_filelist', 'cvrtl', 'fvsyn', 'bcmrbc', 'oasis', 'upf_rtl', 'syn', 'reldoc', 'cvsignoff', 'cdl', 'rtl', 'r2g2', 'upf_netlist', 'ipxact', 'cdc', 'sdf', 'timemod', 'rv', 'laymisc', 'pnr', 'pv', 'stamod', 'schmisc', 'sta', 'lint', 'complibphys', 'dftdsm', 'complib', 'oa', 'rcxt', 'fvpnr', 'ipspec'], 'soc_gic_wrapper': ['bcmrbc', 'rtlcompchk', 'reldoc', 'dv', 'lint', 'ipxact', 'cvrtl', 'cdc', 'rtl', 'dftdsm', 'ipspec'], 'soc_cs_lib': ['cdc', 'rtl', 'reldoc', 'dftdsm', 'bcmrbc', 'rtlcompchk', 'ipspec', 'ipxact', 'cvrtl', 'lint', 'dv'], 'soc_std_macro': ['dftdsm', 'ipspec', 'rtlcompchk', 'lint', 'reldoc', 'rtl', 'dv', 'interrba', 'ipxact', 'cvrtl', 'bcmrbc', 'rdf', 'cdc'], 'soc_hps_wrapper': ['stamod', 'timemod', 'syn', 'cdc', 'laymisc', 'ipxact', 'rv', 'bcmrbc', 'ippwrmod', 'cdl', 'upf_rtl', 'cvsignoff', 'fvsyn', 'r2g2', 'upf_netlist', 'ipspec', 'sdf', 'rcxt', 'cvrtl', 'reldoc', 'oa', 'lint', 'dftdsm', 'sta', 'dv', 'rtl', 'pv', 'circuitsim', 'fvpnr', 'gln_filelist', 'pnr', 'schmisc', 'oasis', 'complib', 'complibphys', 'rtlcompchk'], 'soc_gpio_wrapper': ['dv', 'bcmrbc', 'rtlcompchk', 'cdc', 'interrba', 'ipxact', 'dftdsm', 'cvrtl', 'rtl', 'ipspec', 'lint', 'reldoc', 'rdf'], 'soc_pss': ['lint', 'cvsignoff', 'cvrtl', 'complib', 'upf_rtl', 'dftdsm', 'oasis', 'ipxact', 'dv', 'laymisc', 'fvsyn', 'reldoc', 'fvpnr', 'pv', 'rtl', 'pnr', 'upf_netlist', 'sta', 'bcmrbc', 'oa', 'rv', 'cdc', 'syn', 'ipspec', 'schmisc', 'r2g2', 'complibphys', 'stamod', 'rcxt', 'rtlcompchk', 'ippwrmod', 'cdl', 'sdf', 'timemod', 'gln_filelist'], 'soc_hps_fpga_bridges': ['dv', 'cdc', 'cvrtl', 'dftdsm', 'bcmrbc', 'lint', 'rtlcompchk', 'reldoc', 'ipspec', 'ipxact', 'rtl'], 'jtag_common': ['reldoc', 'rtl', 'cvrtl', 'rtlcompchk', 'cdc', 'bcmrbc', 'dftdsm', 'interrba', 'ipxact', 'ipspec', 'rdf', 'dv', 'lint'], 'soc_hps_mobile_storage_wrapper': ['cvrtl', 'ipxact', 'bcmrbc', 'reldoc', 'cdc', 'rtlcompchk', 'lint', 'rtl', 'dftdsm', 'dv', 'ipspec'], 'cnt_shared': ['cvimpl', 'circuitsim', 'upf_rtl', 'oasis', 'rtlcompchk', 'cvrtl', 'dftdsm', 'ilib', 'rtl', 'pvector', 'rdf', 'syn', 'oa', 'laymisc', 'dv', 'interrba', 'complibphys', 'r2g2', 'pnr', 'gp', 'sta', 'bcmrbc', 'schmisc', 'rcxt', 'dfx', 'rv', 'sdf', 'cge', 'upf_netlist', 'ipxact', 'ipspec', 'fvpnr', 'fetimemod', 'stamod', 'pv', 'reldoc', 'complib', 'cvsignoff', 'fvsyn', 'cdc', 'timemod', 'gln_filelist', 'cdl', 'lint', 'ippwrmod'], 'soc_hps_ram_wrappers': ['reldoc', 'rtlcompchk', 'rtl', 'ipspec', 'lint'], 'soc_mpu_cortexa53': ['cvrtl', 'sdf', 'pv', 'fvsyn', 'bcmrbc', 'cdl', 'gln_filelist', 'complib', 'upf_netlist', 'r2g2', 'fvpnr', 'reldoc', 'timemod', 'rv', 'rtlcompchk', 'syn', 'dftdsm', 'rtl', 'oasis', 'dv', 'stamod', 'cvsignoff', 'laymisc', 'ipxact', 'oa', 'ipspec', 'cdc', 'sta', 'pnr', 'schmisc', 'lint', 'ippwrmod', 'rcxt', 'complibphys', 'upf_rtl'], 'soc_ssi_slave_wrapper': ['dftdsm', 'cdc', 'bcmrbc', 'rtl', 'ipxact', 'rtlcompchk', 'ipspec', 'lint', 'cvrtl', 'reldoc', 'dv'], 'physintspecfm': ['reldoc', 'ipspec', 'trackphys'], 'soc_emac_wrapper': ['dftdsm', 'cdc', 'rtlcompchk', 'lint', 'reldoc', 'ipspec', 'cvrtl', 'bcmrbc', 'rtl', 'ipxact', 'dv'], 'soc_ca53_cpu': ['stamod', 'dftdsm', 'schmisc', 'lint', 'ippwrmod', 'gln_filelist', 'fvpnr', 'pv', 'dv', 'bcmrbc', 'r2g2', 'fvsyn', 'sdf', 'timemod', 'upf_netlist', 'complibphys', 'complib', 'pnr', 'rtl', 'cdl', 'cdc', 'upf_rtl', 'ipxact', 'reldoc', 'oasis', 'sta', 'rcxt', 'ipspec', 'syn', 'oa', 'cvrtl', 'rv', 'laymisc', 'rtlcompchk', 'cvsignoff']}
        cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_flows_workspace___files', 'variants_libtypes')
        w = self.wp.WorkspaceUpdate(self.wsname)
        self.assertEqual(result, w.get_dict_from_config(cfgfile, mock_get_deliverable_type_from_config_factory_object.return_value))
 
    def test_901__write_cfg_file(self):
        w = self.wp.WorkspaceUpdate(self.wsname)
        cfgdict = {'liotest1':'sta'}
        data = '[1]\nvariants: liotest1\nlibtypes: sta\n\n'
        cfgfile = w.write_cfg_file(cfgdict, 'mutable')
        fo = open(cfgfile)
        result = fo.read()
        self.assertEqual(data, result)

    def test_902__write_cfg_file_multiple(self):
        w = self.wp.WorkspaceUpdate(self.wsname)
        cfgdict = {'liotest1':'sta ipspec', 'wplimtest1':'reldoc'}
        data = '[1]\nvariants: wplimtest1\nlibtypes: reldoc\n\n[2]\nvariants: liotest1\nlibtypes: sta ipspec\n\n'
        
        data1 = 'variants: wplimtest1\nlibtypes: reldoc'
        data2 = 'variants: liotest1\nlibtypes: sta ipspec'

        cfgfile = w.write_cfg_file(cfgdict, 'mutable')
        fo = open(cfgfile)
        result = fo.read()
        print("-------------------------------")
        print(data)
        print("-------------------------------")
        print(result)
        self.assertIn(data1, result)
        self.assertIn(data2, result)
       
    @patch('dmx.abnrlib.flows.workspaceupdate.get_workspace_disk')   
    def test_903_check_accessibility_of_workspace_directory(self, mock_workspace_disk):
        mock_workspace_disk.return_value = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL'
        wsname = 'lionelta_da_i16_dai16liotest1_2599'
        w = self.wp.WorkspaceUpdate(wsname)
        data = True
        flag = w.is_workspace_accessible()
        self.assertEqual(data, flag)       


if __name__ == '__main__':
    unittest.main()

