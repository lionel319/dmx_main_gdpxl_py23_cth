#!/usr/bin/env python

import abc

class Workspace(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def workspace_path(self):
        pass

    @abc.abstractproperty
    def project_name(self):
        pass

    @abc.abstractproperty
    def ip_name(self):
        pass

    @abc.abstractproperty
    def deliverable_name(self):
        pass


    @abc.abstractmethod
    def create(self):
        pass


    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def delete(self):
        pass
