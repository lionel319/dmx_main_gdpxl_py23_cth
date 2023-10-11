"""
Tests for various ways of registering models with the admin site.
"""

from builtins import object
from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=200)

class Location(models.Model):
    class Meta(object):
        abstract = True

class Place(Location):
    name = models.CharField(max_length=200)
