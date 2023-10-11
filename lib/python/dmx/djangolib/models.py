"""
EcoSphere database.
"""

__author__ ="TAN YOKE LIANG (yltan@altera.com)"
__version__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2009-2010 Altera Corporation."


from django.db import models

class Owner(models.Model):
    ''' Table that stores ownership of a variant '''

    id = models.IntegerField(primary_key=True)
    datetime = models.DateTimeField()
    project = models.CharField(max_length=250)
    variant = models.CharField(max_length=250)
    owner = models.CharField(max_length=20)
    type = models.CharField(max_length=50)
    updater = models.CharField(max_length=50)
   
    def __unicode__(self):
        return "{}({})[{}]".format(self.variant, self.owner, self.datetime)

    class Meta:
        db_table = u'owners'
        app_label = 'test'

class Cellname(models.Model):
    ''' Table that stores cellname '''

    id = models.IntegerField(primary_key=True)
    project = models.CharField(max_length=250)
    variant = models.CharField(max_length=250)
    cellname = models.CharField(max_length=500)
    product = models.CharField(max_length=20)
    updater = models.CharField(max_length=50)
    datetime = models.DateTimeField()

    def __unicode__(self):
        return "{}/{}:{}".format(self.project, self.variant, self.cellname)

    class Meta:
        db_table = u'cellnames'
        app_label = 'test'

class Unneeded(models.Model):
    ''' Unneeded Deliverables table '''

    id = models.IntegerField(primary_key=True)
    project = models.CharField(max_length=250)
    variant = models.CharField(max_length=250)
    cellname = models.CharField(max_length=500)
    libtype = models.CharField(max_length=50)
    updater = models.CharField(max_length=50)
    datetime = models.DateTimeField()
    
    def __unicode__(self):
        return "{}/{}:{} {}".format(self.project, self.variant, self.libtype, self.cellname )

    class Meta:
        db_table = u'unneededs'
        app_label = 'test'

class Disk(models.Model):
    ''' Disk table '''

    id = models.IntegerField(primary_key=True)
    site = models.CharField(max_length=45)
    dept = models.CharField(max_length=45)
    group = models.CharField(max_length=60)
    subgroup = models.CharField(max_length=60)
    disk = models.CharField(max_length=250)
    volume = models.CharField(max_length=250)
    tier = models.CharField(max_length=6)
    size = models.FloatField()
    used = models.FloatField()
    year = models.IntegerField(max_length=4)
    quarter = models.CharField(max_length=45)
    project = models.CharField(max_length=45)
    type = models.CharField(max_length=45)
    ownerid = models.CharField(max_length=150)
    requestid = models.CharField(max_length=45)
    requestor = models.CharField(max_length=45)
    createdby = models.CharField(max_length=45)
    volname = models.CharField(max_length=250)
    updated = models.IntegerField(max_length=1)
    
    def __unicode__(self):
        return "{}/{}".format(self.ownerid, self.disk)

    class Meta:
        db_table = u'fc_disk'
        app_label = 'test'



