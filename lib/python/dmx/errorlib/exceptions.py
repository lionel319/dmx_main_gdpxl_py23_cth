#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/errorlib/exceptions.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: 
    This library creates dynamic Exception classes based on the cfgfiles/errorcodes.json
    All errors in errorcodes.json will have their respective Exception class created with 'DmxError' prefix.


Usage:
    from dmx.errorlib.exceptions import *

    try:
        raise DmxErrorICWS01("testing 1 2 3")
    except DmxErrorICWS01 as e:
        print "Workspace Not Found."

'''
import os
import sys


__LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, __LIB)

import dmx.utillib.utils
import dmx.errorlib.errorcode

__all__ = []

def __create_dynamic_exception_classes():
    ec = dmx.errorlib.errorcode.ErrorCode()
    errdata = ec.load_errorcode_data_file()

    for code, info in errdata.items():
        classname = 'DmxError{}'.format(code)
        globals()[classname] = type(classname, (Exception,), {})
        globals()['__all__'].append(classname)  # Only allow DmxError* classes to be imported

__create_dynamic_exception_classes()

if __name__ == '__main__':
    pass
