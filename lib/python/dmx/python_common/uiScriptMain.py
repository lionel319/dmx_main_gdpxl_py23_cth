import os as _os
import sys as _sys
import datetime as _datetime
from dmx.python_common.uiPrintMessage import uiInfo as _uiInfo
from dmx.python_common.uiPrintMessage import uiWarning as _uiWarning
from dmx.python_common.uiPrintMessage import uiError as _uiError
from dmx.python_common.uiPrintMessage import uiCritical as _uiCritical
from dmx.python_common.uiPrintMessage import uiDebug as _uiDebug
from dmx.python_common.uiPrintMessage import logging
from functools import wraps
import inspect


def automain(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        parent = inspect.stack()[1][0]
        name = parent.f_locals.get('__name__', None)

        if name == '__main__':

            try:
                # debug mode ?
                logging(kwargs['debug'], kwargs['logfile'])

                base = _os.path.basename(_sys.argv[0])
                cmd = _os.path.splitext(base)[0]
    
                _uiInfo("******************************************************************************")
                _uiInfo("")
                _uiInfo("Running {} {}" .format(cmd, " ".join(_sys.argv[1:])))
                _uiInfo("")
                _uiInfo("Start date: {}" .format(_datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                _uiInfo("")
                _uiInfo("******************************************************************************")
                _uiInfo("")

                func(*args, **kwargs)

                _uiInfo("******************************************************************************")
                _uiInfo("")
                _uiInfo("End date: {}" .format(_datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                _uiInfo("")
                _uiInfo("STATUS:     %d info(s)  %d warning(s)   %d error(s)" % (_uiInfo.count, _uiWarning.count, _uiError.count))
                _uiInfo("")
                _uiInfo("******************************************************************************\n")


            except KeyboardInterrupt:
                _uiCritical("You cancelled the program!")

    return wrapper

