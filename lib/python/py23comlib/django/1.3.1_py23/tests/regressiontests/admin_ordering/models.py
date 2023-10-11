# coding: utf-8
from builtins import object
from django.db import models
from django.contrib import admin

class Band(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    rank = models.IntegerField()

    class Meta(object):
        ordering = ('name',)

class Song(models.Model):
    band = models.ForeignKey(Band)
    name = models.CharField(max_length=100)
    duration = models.IntegerField()

    class Meta(object):
        ordering = ('name',)

class SongInlineDefaultOrdering(admin.StackedInline):
    model = Song

class SongInlineNewOrdering(admin.StackedInline):
    model = Song
    ordering = ('duration', )
