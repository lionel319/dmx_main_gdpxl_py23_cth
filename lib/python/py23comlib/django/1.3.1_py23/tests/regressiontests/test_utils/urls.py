from __future__ import absolute_import
from django.conf.urls.defaults import patterns

from . import views


urlpatterns = patterns('',
    (r'^get_person/(\d+)/$', views.get_person),
)
