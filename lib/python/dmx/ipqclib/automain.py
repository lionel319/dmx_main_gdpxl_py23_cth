#!/usr/bin/env python
"""automain.py"""
import sys as _sys
import datetime as _datetime
import inspect
import os
from functools import wraps
from dmx.ipqclib.log import uiInfo as _uiInfo
from dmx.ipqclib.log  import uiWarning as _uiWarning
from dmx.ipqclib.log  import uiError as _uiError
from dmx.ipqclib.log  import uiCritical as _uiCritical
from dmx.ipqclib.log  import logging

def automain(func): # pylint: disable=C0111
    @wraps(func)
    def wrapper(args): # pylint: disable=C0111
        os.environ['DMX_SKIP_TURNIN'] = '1'
        parent = inspect.stack()[1][0]
        name = parent.f_locals.get('__name__', None)
        result = 0

        if name == '__main__':

            
            logging(args.debug, args.logfile)

            cmd = 'ipqc'
            start_date = _datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            _uiInfo("******************************************************************************") # pylint: disable=C0301
            _uiInfo("")
            _uiInfo(__file__)
            _uiInfo("Running {} {}" .format(cmd, " ".join(_sys.argv[1:])))
            _uiInfo("")
            _uiInfo("Start date: {}" .format(start_date))
            _uiInfo("")
            _uiInfo("******************************************************************************") # pylint: disable=C0301
            _uiInfo("")

            result = func(args)
            end_date = _datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            _uiInfo("******************************************************************************") # pylint: disable=C0301
            _uiInfo("")
            _uiInfo("End date: {}" .format(end_date))
            _uiInfo("")
            _uiInfo("STATUS:     %d info(s)  %d warning(s)   %d error(s)" % \
                    (_uiInfo.count, _uiWarning.count, _uiError.count))
            _uiInfo("")
            _uiInfo("******************************************************************************\n") # pylint: disable=C0301
            return result

    return wrapper
