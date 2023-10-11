from __future__ import absolute_import
from builtins import object
from django.forms import ModelForm
from .models import USPlace

class USPlaceForm(ModelForm):
    """docstring for PlaceForm"""
    class Meta(object):
        model = USPlace
