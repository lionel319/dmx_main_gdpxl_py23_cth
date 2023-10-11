from __future__ import absolute_import
from builtins import object
from django import forms
from django.forms import ModelForm

from .models import (Product, Price, Book, DerivedBook, ExplicitPK, Post,
        DerivedPost, Writer, FlexibleDatePost)

class ProductForm(ModelForm):
    class Meta(object):
        model = Product

class PriceForm(ModelForm):
    class Meta(object):
        model = Price

class BookForm(ModelForm):
    class Meta(object):
       model = Book

class DerivedBookForm(ModelForm):
    class Meta(object):
        model = DerivedBook

class ExplicitPKForm(ModelForm):
    class Meta(object):
        model = ExplicitPK
        fields = ('key', 'desc',)

class PostForm(ModelForm):
    class Meta(object):
        model = Post

class DerivedPostForm(ModelForm):
    class Meta(object):
        model = DerivedPost

class CustomWriterForm(ModelForm):
   name = forms.CharField(required=False)

   class Meta(object):
       model = Writer

class FlexDatePostForm(ModelForm):
    class Meta(object):
        model = FlexibleDatePost
