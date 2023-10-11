# Copyright 2011 Altera Corporation.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/decorators.py#1 $

"""
Useful decorators
"""

__author__ ="Yaron Kretchmer (ykretchm@altera.com)"
__version__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation."

class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, function):
        self.memo = {}
        self.function = function
        self.count_calls_total = 0
        self.count_calls_in_cache = 0
        
    def __call__(self, *args):
        self.count_calls_total += 1
        if args in self.memo:
            self.count_calls_in_cache += 1
            return self.memo[args]
        else:
            object = self.memo[args] = self.function(*args)
            return object

    def get_stats(self):
        return "calls in cache: %d out of %d (%.1f%%)" % \
               (self.count_calls_in_cache,
                self.count_calls_total,
                self.count_calls_in_cache*100.0/self.count_calls_total)


class CatchAndRelease(object):
    """
    A decorator which accepts two args:
        - 'exception_type' is the type of exception to catch
        - 'reporter_func' is the function to pass the exception

    If 'exception_type' is thrown by decorated function, we will catch it and
    pass it to 'reporter_func', and then return None
    """
    def __init__(self, exception_type, reporter_func):
        self.exception_type = exception_type
        self.reporter_func = reporter_func
        
    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except self.exception_type as e:
                self.reporter_func(e)
        return wrapped_f
