from __future__ import absolute_import
from builtins import object
from django.core.urlresolvers import set_urlconf

from . import urlconf_inner

class ChangeURLconfMiddleware(object):
    def process_request(self, request):
        request.urlconf = urlconf_inner.__name__

class NullChangeURLconfMiddleware(object):
    def process_request(self, request):
        request.urlconf = None
