#!/usr/intel/pkgs/python3/3.10.8/bin/python3

import os
import sys
import json
from pprint import pprint
import textwrap
import logging
import configparser
import time

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)

import cmx.utillib.utils

sys.path.insert(0, '/p/cth/rtl/proj_tools/cth_mako_render/23.03.001')
import cth_design_cfg

LOGGER = logging.getLogger(__name__)

def parse_flowcfg(tool='dmx', workarea=None):
    workarea = raise_exception_if_workarea_not_defined(workarea)
    inifile = os.path.join(workarea, 'flows', tool, 'flow.cfg')
    if not os.path.isfile(inifile):
        raise Exception("flowcfg file not found: {}".format(inifile))
    return parse_inifile(inifile)

def parse_inifile(inifile):
    ret = {}
    design_config = configparser.RawConfigParser(strict=False,allow_no_value=True) # note duplicate sections merged, not kept
    design_config.optionxform = str # preserve case of keys
    design_config.read(inifile)
    data = ({section: dict(design_config[section]) for section in design_config.sections()})

    data['_filename_'] = inifile
    return data

def get_duts_data(cfgdir=None):
    if not cfgdir:
        workarea = raise_exception_if_workarea_not_defined()
        cfgdir = os.path.join(workarea, 'cfg')
    return cth_design_cfg.DutData(cfgdir)

def raise_exception_if_workarea_not_defined(workarea=None):
    workarea = get_workarea(workarea)
    if not workarea:
        raise Exception("$WORKAREA env var not defined.")
    return workarea

def get_workarea(workarea=None):
    if not workarea:
        workarea = os.getenv("WORKAREA")
    return workarea

def get_uniq_staging_bom_name(project, ip, deliverable):
    ''' Always use this API to create a temporary variant-bom.
    The naming convention is fixed, as we already have a cron that will clean up temporary bom 
    based on this naming convention.
    '''
    return '_for_tnr_{}_{}_{}'.format(deliverable, os.getenv("USER"), int(time.time()))

def get_uniq_staging_workarea(project='project', ip='ip'):
    staging_disk = '/nfs/site/disks/psg_dmx_1/ws'
    hostname = os.uname()[1]
    epoch = int(time.time())
    waname = '{}.{}.{}.{}.{}'.format(os.getenv("USER"), project, ip, hostname, epoch)
    staging_workarea = os.path.join(staging_disk, waname)
    return staging_workarea

def cth_env_cmd_wrapper(cfg='KM4A0P00I0S_R2G_RC.cth', workarea=None, cmd='whoami', host='localhost'):
    '''
    if workarea is not provided, we will create a uniq_staging_workarea and use it as the workarea.
    '''
    if not workarea:
        workarea = get_uniq_staging_workarea()
    cth_psetup_cmd = '''cth_psetup_psg -proj psg -cfg {} -rc -ward {} -cmd {}'''.format(cfg, workarea, cmx.utillib.utils.quotify(cmd))
    ssh_cmd = '''ssh localhost -q {}'''.format(cmx.utillib.utils.quotify(cth_psetup_cmd))
    return ssh_cmd

def get_setenv_str(envvardict=None, include_dmx_envvar=True):
    ''' Return the string of setenv. 
    Example:-
        get_setenv_str(None, include_dmx_envvar)
        return: 'setenv DB_FAMILY KM;setenv DB_THREAD KM2revA0; ...'

        get_setenv_str({"A":"B", "C":"D"}, False)
        return: 'setenv A B;setenv C D'
    '''
    dmx_envvar_list = ['DB_FAMILY', 'DB_THREAD', 'DB_DEVICE', 'DMXDATA_ROOT', 'DMX_SETTING_FILES_DIR']

    ret = ''
    if envvardict:
        for key in envvardict:
            val = envvardict[key]
            ret = ret + 'setenv {} {};'.format(key, val)
    if include_dmx_envvar:
        for key in dmx_envvar_list:
            val = os.getenv(key)
            if val:
                ret = ret + 'setenv {} {};'.format(key, val)
    return ret

if __name__ == '__main__':
    import UsrIntel.R1
    pprint(get_duts_data())
    print("=====")
    pprint(get_duts_data().keys())
    #pprint(parse_flowcfg())
    
    #print(get_setenv_str({"A":"B", "C":"D"}))

