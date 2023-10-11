#!/usr/bin/env python
'''
Class that define a Constant.
'''

from builtins import object
class _const(object):
    class ConstError(TypeError): pass
    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't rebind const: {}".format(name))
        self.__dict__[name] = value

'''
#############################################
### This part makes the class a singleton ###
#############################################
import sys
sys.modules[__name__] = _const()
'''
