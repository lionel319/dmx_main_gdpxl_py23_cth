from builtins import object
from django.db import models

class Foo(models.Model):
    name = models.CharField(max_length=5)
    class Meta(object):
        app_label = 'complex_app'
