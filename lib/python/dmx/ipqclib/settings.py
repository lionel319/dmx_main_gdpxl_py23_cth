#!/usr/bin/env python
# pylint: disable-msg=C0103
"""settings.py"""
import os
from dmx.utillib.arcenv import ARCEnv
from dmx.python_common.uiConfigParser import ConfigObj

############################################################################
# DB Environment Variable
############################################################################
arc = ARCEnv() # pylint: disable=C0103
_DB_PROJECT = arc.get_project()
_DB_FAMILY = arc.get_family()
_DB_FAMILY = _DB_FAMILY.lower().title()
_DB_THREAD = arc.get_thread()
_DB_DEVICE = arc.get_device()
_DB_PROCESS = arc.get_process()

############################################################################
# ARC related information
############################################################################
_ARC_PREFIX = 'arc submit -PE '
_ARC_LOCAL = _ARC_PREFIX + '--local '
if os.getenv('PSG_SITE') == 'sj':
    _ARC_URL_PICE = 'https://sj-arc.altera.com/arc/dashboard/reports/show_job/'
    _ARC_URL = 'http://sj-arc.altera.com/'
    _DATA_PATH = '/data'
    _DOMAIN = '@altera.com'
    _FIREFOX = '/apps/tools/bin/firefox'
    _BCC = ['wei.pin.lim@intel.com']
elif (os.getenv('PSG_SITE') == 'sc') or (os.getenv('PSG_SITE') == 'png'):

    if os.getenv('PSG_SITE') == 'sc':
        _ARC_URL_PICE = 'https://psg-sc-arc.sc.intel.com/arc/dashboard/reports/show_job/'
        _ARC_URL = 'https://psg-sc-arc.sc.intel.com/'

    if os.getenv('PSG_SITE') == 'png':
        _ARC_URL_PICE = 'https://psg-png-arc.png.intel.com/arc/dashboard/reports/show_job/'
        _ARC_URL = 'https://psg-png-arc.png.intel.com/'

    _DATA_PATH = '/p/psg/data'
    _DOMAIN = '@intel.com'
    _FIREFOX = '/usr/intel/bin/firefox'
    _BCC = ['wei.pin.lim@intel.com']
else:
    _ARC_URL_PICE = 'https://sj-arc.altera.com/arc/dashboard/reports/show_job/'
    _ARC_URL = 'http://sj-arc.altera.com/'
    _DATA_PATH = '/data'
    _DOMAIN = '@altera.com'
    _FIREFOX = '/apps/tools/bin/firefox'
    _BCC = ['wei.pin.lim@intel.com']


if os.path.exists(os.path.join(os.getenv('DMXDATA_ROOT'))):
    for family in os.listdir(os.path.join(os.getenv('DMXDATA_ROOT'))):
        if _DB_FAMILY.lower() == family.lower():
            if os.path.exists(os.path.join(os.getenv('DMXDATA_ROOT'), family, 'ipqc')):
                _IPQC_INIT = os.path.join(os.getenv('DMXDATA_ROOT'), family, 'ipqc', 'ipqc.ini')
                _IPQC_MAPPING = os.path.join(os.getenv('DMXDATA_ROOT'), family, 'ipqc', \
                        'mapping.ini')
                _IPQC_WRAPPER = os.path.join(os.getenv('DMXDATA_ROOT'), family, 'ipqc', \
                        'wrapper.ini')

    ipqc_info = ConfigObj(os.path.join(os.getenv('DMXDATA_ROOT'), _DB_FAMILY, 'ipqc', \
            'settings.ini'))
    _FUNC_FILE = os.path.join(os.path.dirname(ipqc_info['rel']['nfs']), 'settings', \
            'ipqc_functionality.ini')


############################################################################
# IPQC dashboard information
############################################################################
_FAILED = 'failed'
_PASSED = 'passed'
_WARNING = 'passed with waiver(s)'
_CHECKER_WAIVED = 'checker waived'
_CHECKER_SKIPPED = 'checker skipped'
_ALL_WAIVED = 'deliverable waived'
_FATAL_SYSTEM = 'fatal system'
_FATAL = 'fatal'
_NA = '-'
_NA_ERROR = 'not available'
_UNNEEDED = 'unneeded'
_NA_MILESTONE = 'na milestone'
_NOT_POR = 'not POR'

status_data = { \
        _PASSED: {'name' : _PASSED, 'color' : '#04B404', 'code': 0, 'description': 'Check(s) \
        passed without any waivers', 'message': 'completed and passed'}, \
        _FAILED: {'name' : _FAILED, 'color' : '#CC3300', 'code': 1, 'description': 'Check(s) \
        Failed', 'message': 'completed and failed'}, \
        _FATAL_SYSTEM: {'name' : _FATAL_SYSTEM, 'color' : '#FF8000', 'code' : 2, 'description': \
        'Execution error (environment issue, input issue, ...)', 'message': 'needs to be executed'},
        _FATAL: {'name' : _FATAL, 'color' : '#000000', 'code' : 2, 'description': 'Checker \
                execution issue', 'message': 'needs to be executed'}, \
        _WARNING: {'name': _WARNING, 'color': '#FFFF33', 'code': 0, 'description': 'Check errors \
        have been waived / checker has been waived / deliverable has been waived', 'message': \
        'completed and passed with waivers'}, \
        _CHECKER_WAIVED: {'name': _CHECKER_WAIVED, 'color': '#FFFF33', 'code': 0, 'description': \
        'Check waived', 'message': 'checker waived'}, \
        _CHECKER_SKIPPED: {'name': _CHECKER_SKIPPED, 'color': '#CC3300', 'code': 0, 'description': \
        'Check skip', 'message': 'checker skipped'}, \
        _ALL_WAIVED: {'name': _ALL_WAIVED, 'color': '#FFFF33', 'code': 0, 'description': \
        'Deliverable has been waived', 'message': 'deliverable waived'}, \
        _NA: {'name': _NA, 'color' : '#E0E0E0', 'code': 0, 'description': 'N/A', 'message': '-', \
        'option': 'na'}, \
        _NA_MILESTONE: {'name': _NA, 'color' : '#CCFFFF', 'code': 0, 'description': \
        'Not applicable for this milestone', 'message': 'not applicable for this milestone'}, \
        _UNNEEDED: {'name': _UNNEEDED, 'color' : '#CCDDEE', 'code': 0, 'description': 'Not POR or \
        unneeded deliverable', 'message': 'unneeded deliverable', 'option': _UNNEEDED}, \
    }

############################################################################
# Immutable configuration
############################################################################
_REL = "REL"
_SNAP = "snap-"
_IMMUTABLE_BOM = (_REL, _SNAP, 'PREL')

_VIEW_RTL = 'view_rtl'
_VIEW_PHYS = 'view_phys'
_VIEW_TIMING = 'view_acds'
_VIEW_OTHER = 'view_other'

_MAP_VIEWS = { \
        _VIEW_RTL: {'name': "FRONT-END", 'color': '#99BB99'}, \
        _VIEW_PHYS: {'name': "BACK-END", 'color': '#66CCAA'}, \
        _VIEW_TIMING: {'name': "TIMING", 'color': '#66BBCC'}, \
        _VIEW_OTHER: {'name': 'OTHER', 'color': '#D3D3D3'} \
        }

_VIEW_ORDER = [_VIEW_RTL, _VIEW_PHYS, _VIEW_TIMING, _VIEW_OTHER]

_DELIVERABLES_DESCRIPTION = os.path.join(os.getenv('DMXDATA_ROOT'), 'misc', \
        'deliverables_description.json')

############################################################################
# Options to remove from checkers to avoid deadlock
############################################################################
_OPTIONS_TO_REMOVE = ['-watch']

_ICMANAGE = 'icmanage'
_SION = 'sion'
_WORKSPACE_TYPE = [_ICMANAGE, _SION]

_VIEW = 'view'
_FUNCTIONALITY = 'functionality'
_SIMPLE_PATTERN = r'simple#*\d*'
_SIMPLE = "simple"
_TEMPLATE_LIST = [_VIEW, _FUNCTIONALITY, _SIMPLE]
_DEFAULT_FUNC = "MISC"


#####################
# IPQC mode
#####################
_DRY_RUN = "dry-run"
_RUN_ALL = "run-all"
