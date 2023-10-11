#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/contextmgr.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: A collection of Context Manager libraries

'''

import os
import sys
import pwd
from contextlib import contextmanager
import json
import logging


LOGGER = logging.getLogger(__name__)
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')

@contextmanager
def cd(dirpath):
    cwd = os.getcwd()
    try:
        os.chdir(dirpath)
        yield
    finally:
        os.chdir(cwd)

@contextmanager
def setenv(envvardict):
    ori_envvardict = get_env_var(envvardict.keys())
    try:
        set_env_var(envvardict)
        yield
    finally:
        set_env_var(ori_envvardict)


def get_env_var(envvarlist):
    ret = {}
    for k in envvarlist:
        ret[k] = os.getenv(k, None)
    return ret


def set_env_var(envvardict):
    for k,v in envvardict.items():
        if v == None:
            # unsetenv
            os.environ.pop(k, None)
        else:
            # setenv
            os.environ[k] = str(v)



if __name__ == '__main__':
    pass
