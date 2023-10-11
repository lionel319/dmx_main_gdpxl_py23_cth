# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/qa_logger.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
Logging support module for tests.  Test client main functions should 
import and call init_logging, providing the name of the logfile to 
be generated during testing.
"""
import logging

class SingleLevelFilter(logging.Filter):
    """
    Use this to write log messages of the given level, like this::

        # stderr handler (just errors)
        logger_stderr_handler = StreamHandler(stderr)
        logger_stderr_handler.setFormatter(Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d %H:%M:%S'))
        errors_only = SingleLevelFilter(ERROR, False)
        logger_stderr_handler.addFilter(errors_only)
        logger.addHandler(logger_stderr_handler)
    """
    def __init__(self, passlevel, reject):
        """
        Create a log filter.
        """
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        """
        Return a boolean indicating if the record should be filtered out.
        """
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)

def init_logging(logfile):
    """
    Creates a LOGGER instances which writes warnings and errors to stderr
    and all messages to the given log file. 
    """
#    logging.basicConfig(level=logging.DEBUG,
#                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
#                        datefmt='%m-%d %H:%M',
#                        filename=logfile,
#                        filemode='w')
#
#    # Client code that needs to log should use getLogger to get the instance:
#    logger = logging.getLogger('qa')
#
#    # One could make multiple LOGGERs by givng getLogger different names and setting the file handlers:
#    logger.addHandler(logging.FileHandler(logfile))
    logger = logging.getLogger() # Note there is no __name__ here.
    logger.setLevel(logging.DEBUG) 
    handler = logging.FileHandler( logfile )
    handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d %H:%M'))
    logger.addHandler(handler)

class MockLoggingHandler(logging.Handler):
    """
    Use this handler in unit tests to verify that certain
    messages have been posted.  Like this::

        mock = MockLoggingHandler()
        my_logger.addHandler(mock)
    """
    def __init__(self, *args, **kwargs):
        """
        Create a logging handler for tests.
        """
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        """
        Save the message so it can be checked later.
        """
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        """
        Clear all saved messages.
        """
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }
