#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/VpMock.py#1 $

"""
Define a mock of a VpNadder instance for use with checkers based on the dmx.dmlib.CheckerBase
class.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"


from mock import Mock

from dmx.dmlib.VpNadder import VpNadder
from dmx.dmlib.Manifest import Manifest #@UnusedImport
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace


def VpMock(ip_name,
           cell_name=None,
           deliverableName='deliverableNameIsUndefined',
           ws=None,
           isSwip=False,
           restoreDirName=None,
           outputPathRoot=None,
           templatesetString=None):
    '''Mock :py:class:`dmx.dmlib.VpNadder` instance for use with checkers based on the
    :py:class:`dmx.dmlib.CheckerBase` class.
    
    While the real :py:class:`dmx.dmlib.VpNadder` has a `noICManage` argument, in the tests
    that use this mock it is more convenient to judge whether IC Manage is being
    used based on whether `ws` is specified--when `ws` is specified, it is
    presumed that the test uses IC Manage.
    '''
    vp = Mock(spec=VpNadder)
    vp.ip_name = ip_name
    vp.cell_name = cell_name
    vp.deliverableName = deliverableName
    if vp.cell_name is None:
        vp.cell_name = ip_name
        
    if ws is None:
        vp.ws = None
        vp.workspaceDirName = ICManageWorkspace.getAbsPathOrCwd('.')
        vp.isUsingICManage = False
    else:
        vp.ws = ws
        vp.workspaceDirName = ws.path
        vp.isUsingICManage = True
        
    vp.isSwip = isSwip
    vp.restoreDirName = restoreDirName
    vp.outputPathRoot = outputPathRoot

    vp.manifest = Manifest(vp.ip_name, vp.cell_name, templatesetString=templatesetString)
    
    vp.getLogDirName.return_value = VpNadder.getLogDirName(vp.ip_name, vp.cell_name) 
    vp.getCellTempDirName.return_value = VpNadder.getCellTempDirName(vp.ip_name,
                                                               vp.cell_name,
                                                               absolute=True)
    vp.getXUnitFileName.return_value = VpNadder.getXUnitFileName(vp.deliverableName,
                                                           vp.ip_name, vp.cell_name)
    return vp
