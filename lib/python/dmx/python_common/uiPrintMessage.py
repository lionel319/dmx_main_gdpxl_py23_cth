# -*- coding: utf-8 -*-
"""
Common user interface command to print message with level logging:
    
    Level	Value	Usage
    CRITICAL	50	Program is crashing.
    ERROR	40	Some operation are wrong
    WARNING	30	Something should catch user attention.
    INFO	20	Info message program is running. Ex: “Starting CSV parsing”
    DEBUG	10	Dump imformation in debug mode. For example to see the dict values.
"""

import logging as _logging
from functools import wraps as _wraps
from logging import FileHandler as _FileHandler
import inspect
import os as _os
import sys as _sys

def logging(debug=False, log_file=None):

    if debug != True:
        level = _logging.INFO
    else:
        level=_logging.DEBUG

    init_logger(level, log_file)
    
def init_logger(level=_logging.INFO, logfile=None):
    # create logger object to write in logs
    _logger = _logging.getLogger()
    # set the logger level to INFO
    _logger.setLevel(level)
        
    # create a formator that will add message level with prog prefix when the user outputs a message
    prog = _os.path.splitext(_os.path.basename(_sys.argv[0]))[0]
    formatter = _logging.Formatter('{}_%(levelname)-8s:    %(message)s' .format(prog.upper()))
    if logfile != None:
        # create handler that redirects log into file
        _file_handler = _FileHandler('%s' % logfile, 'w')
        # set the file handler to INFO level, use the defined formator, and add this handler to the logger
        _file_handler.setLevel(level)
        _file_handler.setFormatter(formatter)
        _logger.addHandler(_file_handler)
        
    # create another handler that redirects the message on console
    _stream_handler = _logging.StreamHandler()
    _stream_handler.setLevel(level)
    _stream_handler.setFormatter(formatter)
    _logger.addHandler(_stream_handler)


def _counter(func):
    @_wraps(func)
    def tmp(*args, **kwargs):
        tmp.count += 1
        return func(*args, **kwargs)
    tmp.count = 0
    return tmp

def uiDebug(msg):
    _logging.debug(msg)

@_counter
def uiInfo(msg):
    _logging.info(msg)

@_counter
def uiWarning(msg):
    _logging.warning(msg)

@_counter
def uiError(msg):
    _logging.error(msg)
    
def uiCritical(msg):
    _logging.critical(msg)
    exit(1)


