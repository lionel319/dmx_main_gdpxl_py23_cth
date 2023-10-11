"""
29. Many-to-many and many-to-one relationships to the same table

Make sure to set ``related_name`` if you use relationships to the same table.
"""

from builtins import str
from builtins import object
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=20)

class Issue(models.Model):
    num = models.IntegerField()
    cc = models.ManyToManyField(User, blank=True, related_name='test_issue_cc')
    client = models.ForeignKey(User, related_name='test_issue_client')

    def __unicode__(self):
        return str(self.num)

    class Meta(object):
        ordering = ('num',)
