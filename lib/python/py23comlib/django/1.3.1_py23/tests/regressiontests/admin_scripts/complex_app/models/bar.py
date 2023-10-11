from builtins import object
from django.db import models

from admin_scripts.complex_app.admin import foo
class Bar(models.Model):
    name = models.CharField(max_length=5)
    class Meta(object):
        app_label = 'complex_app'
