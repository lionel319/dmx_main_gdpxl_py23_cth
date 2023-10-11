# Copyright 2010 Altera Corporation.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/arc_utils/1.7_py23/arc_orm/models.py#1 $

"""
ARC Database models for main job/resource data.
"""

from builtins import object
__author__ ="Robert Romano (rromano@altera.com)"
__version__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2009-2010 Altera Corporation."

import sys
import os
if sys.version_info[0] > 2:
    py23comlib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
    sys.path.insert(0, os.path.join(py23comlib, 'django', '1.3.1_py23'))
from django.db import models

class Resources(models.Model):
    id = models.IntegerField(primary_key=True)
    address = models.TextField()
    type = models.CharField(max_length=135)
    owner = models.IntegerField()
    user = models.CharField(max_length=135)
    created_at = models.IntegerField()

    def __unicode__(self):
        return u'%s%s' % (self.type, self.address)
    class Meta(object):
        db_table = u'resources'
        
class Jobs(models.Model):
    id = models.IntegerField(primary_key=True)
    command = models.TextField()
    status = models.CharField(max_length=192)
    parent = models.IntegerField()
    priority = models.IntegerField()
    type = models.CharField(max_length=192)
    user = models.CharField(max_length=135)
    storage = models.TextField()
    name = models.TextField()
    family = models.IntegerField(null=True, blank=True)
    iwd = models.TextField()
    os = models.CharField(max_length=135)
    grp = models.CharField(max_length=192)
    return_code = models.IntegerField(null=True, blank=True)
    class Meta(object):
        db_table = u'jobs'

class JobData(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.ForeignKey(Jobs, db_column = 'job')
    name = models.CharField(max_length=192)
    value = models.TextField()
    class Meta(object):
        db_table = u'job_data'

class JobMessages(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.ForeignKey(Jobs, db_column = 'job')
    type = models.CharField(max_length=192)
    value = models.CharField(max_length=192)
    processed = models.IntegerField()
    class Meta(object):
        db_table = u'job_messages'

class JobRequirements(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.ForeignKey(Jobs, db_column = 'job')
    type = models.CharField(max_length=192)
    address = models.TextField()
    class Meta(object):
        db_table = u'job_requirements'

class JobResources(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.ForeignKey(Jobs, db_column = 'job')
    resource = models.IntegerField()
    class Meta(object):
        db_table = u'job_resources'

class JobTags(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.ForeignKey(Jobs, db_column = 'job')
    resource = models.IntegerField()
    class Meta(object):
        db_table = u'job_tags'

class Processes(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.ForeignKey(Jobs, db_column = 'job')
    serviced = models.IntegerField()
    priority = models.IntegerField()
    os = models.CharField(max_length=135, blank=True)
    grp = models.CharField(max_length=135, blank=True)
    class Meta(object):
        db_table = u'processes'

class ResourceData(models.Model):
    id = models.IntegerField(primary_key=True)
    resource = models.ForeignKey(Resources, db_column = 'resource')
    name = models.CharField(max_length=384)
    value = models.TextField()
    class Meta(object):
        db_table = u'resource_data'

class ResourceMap(models.Model):
    id = models.IntegerField(primary_key=True)
    type = models.CharField(unique=True, max_length=150)
    class_field = models.CharField(max_length=150, db_column='class') # Field renamed because it was a Python reserved word. Field name made lowercase.
    class Meta(object):
        db_table = u'resource_map'



