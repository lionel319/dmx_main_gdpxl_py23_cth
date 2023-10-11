from builtins import object
from django.db import models

class Publication(models.Model):
    title = models.CharField(max_length=30)

    class Meta(object):
        app_label = 'model_package'
