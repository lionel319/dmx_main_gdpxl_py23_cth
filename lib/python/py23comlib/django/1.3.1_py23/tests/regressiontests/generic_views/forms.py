from builtins import object
from django import forms

from regressiontests.generic_views.models import Author


class AuthorForm(forms.ModelForm):
    name = forms.CharField()
    slug = forms.SlugField()

    class Meta(object):
        model = Author
