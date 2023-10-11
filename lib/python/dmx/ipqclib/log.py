#!/usr/bin/env python
"""
Common user interface command to print message with level logging:

    Level	Value	Usage
    CRITICAL	50	Program is crashing.
    ERROR	40	Some operation are wrong
    WARNING	30	Something should catch user attention.
    INFO	20	Info message program is running. Ex: "Starting CSV parsing"
    DEBUG	10	Dump imformation in debug mode. For example to see the dict values.
"""
# -*- coding: utf-8 -*-

import logging as _logging
from logging import FileHandler as _FileHandler
from functools import wraps as _wraps
import inspect

def logging(debug=False, log_file=None):
    """logging function - init logger"""
    if debug != True:
        level = _logging.INFO
    else:
        level = _logging.DEBUG

    init_logger(level, log_file)

def init_logger(level=_logging.INFO, logfile=None):
    """ create logger object to write in logs"""
    _logger = _logging.getLogger()
    # set the logger level to INFO
    _logger.setLevel(level)

    # create a formator that will add message level with prog prefix when the user outputs a message
    prog = 'ipqc'
    formatter = _logging.Formatter('{}_%(levelname)-8s:    %(message)s' .format(prog.upper()))
    formatter = _logging.Formatter('{}_%(levelname)-8s: [%(asctime)s] : [%(lineno)s][%(pathname)s]: %(message)s' .format(prog.upper()))
    # create handler that redirects log into file
    _file_handler = _FileHandler('%s' % logfile, 'w')
    # set the file handler to INFO level, use the defined formator, and add this handler to the
    # logger
    _file_handler.setLevel(level)
    _file_handler.setFormatter(formatter)
    _logger.addHandler(_file_handler)

    # create another handler that redirects the message on console
    _stream_handler = _logging.StreamHandler()
    _stream_handler.setLevel(level)
    _stream_handler.setFormatter(formatter)
    _logger.addHandler(_stream_handler)
    try:
        childLogger = _logging.getLogger('dmx.dmxlib.flows.workspace') # pylint: disable=invalid-name
        childLogger.setLevel(_logging.CRITICAL)
    except Exception: # pylint: disable=broad-except
        pass

    try:
        childLogger2 = _logging.getLogger('dmx.abnrlib.flows.workspace') # pylint: disable=invalid-name
        childLogger2.setLevel(_logging.CRITICAL)
    except Exception: # pylint: disable=broad-except
        pass

def lineno():
    frames = inspect.stack()
    '''
    c = 1
    for f in frames:
        print '{} {}'.format(c, f)
        c += 1
    sys.exit()
    '''
    i = 3
    return [frames[i][1], frames[i][2]]

def _counter(func):
    @_wraps(func)
    def tmp(*args, **kwargs):
        """Count the number of info, warning, error message(s)"""
        tmp.count += 1
        return func(*args, **kwargs)
    tmp.count = 0
    return tmp


def uiDebug(msg, *args, **kwargs): # pylint: disable=invalid-name
    """logger for debug"""
    #_logging.debug(msg, *args, **kwargs)
    _logging.debug('[{}]{}'.format(lineno(), msg), *args, **kwargs)

@_counter
def uiInfo(msg, *args, **kwargs): # pylint: disable=invalid-name
    """logger for info"""
    _logging.info('[{}]{}'.format(lineno(), msg), *args, **kwargs)

def _stars(func):
    @_wraps(func)
    def printstars(*args, **kwargs):
        """print * before and after the string"""
        stars_string = '*' * len(kwargs["msg"])
        _logging.info(stars_string)
        func(*args, **kwargs)
        _logging.info(stars_string)
        uiInfo("")
    return printstars

@_stars
def uiInfoStars(*args, **kwargs): # pylint: disable=invalid-name
    """logger for info and encapsulate the info around stars"""
    uiInfo(*args, **kwargs)

@_counter
def uiWarning(msg, *args, **kwargs): # pylint: disable=invalid-name
    """logger for warning"""
    #_logging.warning(msg, *args, **kwargs)
    _logging.warning('[{}]{}'.format(lineno(), msg), *args, **kwargs)

@_counter
def uiError(msg, *args, **kwargs): # pylint: disable=invalid-name
    """logger for error"""
    #_logging.error(msg, *args, **kwargs)
    _logging.error('[{}]{}'.format(lineno(), msg), *args, **kwargs)

def uiCritical(msg, *args, **kwargs): # pylint: disable=invalid-name
    """logger for system issue"""
    _logging.critical(msg, *args, **kwargs)
    raise SystemExit(1)
