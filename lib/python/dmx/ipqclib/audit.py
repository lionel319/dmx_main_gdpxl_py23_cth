#!/usr/bin/env python
"""audit.py"""
from __future__ import print_function
import os
import shutil
from dmx.ipqclib.utils import file_accessible, memoized
from dmx.ipqclib.log import uiWarning

#########################################################################
#   All information related to audit
#########################################################################
class Audit(object):
    """Audit"""
    def __init__(self, workspace_path, ip_name, deliverable_name, checker_id, workdir, \
            bom_is_immutable):
        self._workspace_path = workspace_path
        self._ip_name = ip_name
        self._deliverable_name = deliverable_name
        self._checker_id = checker_id
        self._workdir = workdir
        self._bom_is_immutable = bom_is_immutable
        self._audit_file = None
        self.prefix_path = os.path.join(self._workspace_path, self._ip_name, \
                self._deliverable_name, 'audit')

    ########################################################
    #################### has_file() ########################
    # check if audit is an xml file and file exists
    # check if audit is a filelist and filelist exists
    # check if files in filelist exist
    ########################################################
    def has_file(self, cellname):
        """has_file"""
        if self.get_file(cellname) != None:
            return True
        return False


    ########################################################
    ############ _get_files_from_filelist() ################
    # returns a list of xml files containing into a filelist
    ########################################################
    # unit test - to do
    @memoized
    def _get_files_from_filelist(self, audit_file):

        audit_file_list = []

        with open(audit_file) as fid:
            for line in fid:
                # skipped blank lineget_audit
                if not line.strip():
                    continue
                else:
                    audit = line.strip('\n')
                    audit = os.path.join(self.prefix_path, audit)
                    audit_file_list.append(audit)

        return audit_file_list

    def get_files_from_filelist(self, audit_file):
        """get_files_from_filelist"""
        return self._get_files_from_filelist(audit_file)

    #####################################################
    #################### get_file() #####################
    # if no audit file return None value
    # if has filelist, return filelist
    # if has xml file, return xml file
    #####################################################
    def get_file(self, cellname):
        """get_file"""
        # audit filelist
        audit_filelist = os.path.join(self.prefix_path, '.'.join(('audit', cellname, \
                self._checker_id, 'f')))
        # xml audit file
        audit_file = os.path.join(self.prefix_path, '.'.join(('audit', cellname, \
                self._checker_id, 'xml')))

        if file_accessible(audit_filelist, os.F_OK):
            self._audit_file = audit_filelist
            return audit_filelist

        if file_accessible(audit_file, os.F_OK):
            self._audit_file = audit_file
            return audit_file

        return None

    #####################################################
    #################### get_files() ####################
    # if no audit file return empty list
    # if has filelist, return filelist and xml files
    #####################################################
    def get_files(self, cellname):
        """get_files"""
        list_of_files = []

        # this condition is useful to warranty that files in filelist exist
        if self.has_file(cellname):
            filepath = self.get_file(cellname)
            if self.is_filelist(filepath):
                list_of_files.append(filepath)
                list_of_files = list_of_files + self._get_files_from_filelist(filepath)

            audit_file = os.path.join(self.prefix_path, '.'.join(('audit', cellname, \
                    self._checker_id, 'xml')))

            if file_accessible(audit_file, os.F_OK):
                list_of_files.append(audit_file)

        return list_of_files

    #####################################################
    ############### file_is_editable() ##################
    # if xml file is not editable return False
    # if filelist is not editable return False
    # if file in filelist is not editable return False
    #####################################################
    def file_is_editable(self, audit_file):
        """file_is_editable"""
        if self.is_filelist(audit_file):
            if file_accessible(audit_file, os.W_OK):
                for audit in self._get_files_from_filelist(audit_file):
                    if not file_accessible(audit, os.W_OK):
                        return False
                return True

            return False

        if (not self.is_filelist(audit_file)) and (file_accessible(audit_file, os.W_OK)):
            return True

        return False

    #####################################################
    ############### list_of_file_not_editable() #########
    # return list of not editable files
    #####################################################
    def get_list_of_file_not_editable(self, audit_file):
        """get_list_of_file_not_editable"""

        list_of_files = []

        if not file_accessible(audit_file, os.W_OK):
            list_of_files.append(audit_file)

        if self.is_filelist(audit_file):
            for audit in self._get_files_from_filelist(audit_file):
                if not file_accessible(audit, os.W_OK):
                    list_of_files.append(audit)

        return list_of_files

    #####################################################
    ################# is_filelist() #####################
    #####################################################
    @staticmethod
    def is_filelist(filepath):
        """is_filelist"""
        return filepath.endswith('.f')


    def set_audit(self, cellname):
        """set_audit"""
        if not self.has_file(cellname):
            return None

        filepath = self.get_file(cellname)

        if self.is_filelist(filepath):
            basename = os.path.splitext(os.path.basename(filepath))[0]
            new_audit_filelist = os.path.join(self._workdir, self._deliverable_name, \
                    basename+'.html')
            new_f = open(new_audit_filelist, 'w')
            print("<!DOCTYPE html>", file=new_f)
            print("<html>", file=new_f)
            print("<body>", file=new_f)
            for audit in self._get_files_from_filelist(filepath):
                audit = audit.strip('\n')
                new_audit = os.path.join(self._workdir, self._deliverable_name, \
                        os.path.basename(audit))
                try:
                    shutil.copyfile(os.path.join(self.prefix_path, audit), new_audit)
                    print('<p><a href=%s ; type=\"text/xml\">%s</a></p>' % \
                            (os.path.basename(new_audit), os.path.basename(audit)), file=new_f)
                except IOError as err:
                    print('{}' .format(os.path.basename(audit)), file=new_f)
                    uiWarning(err)
            print("</body>", file=new_f)
            print("</html>", file=new_f)
            new_f.close()

            shutil.copyfile(self._audit_file, os.path.join(self._workdir, self._deliverable_name, \
                    os.path.basename(self._audit_file)))

            return new_audit_filelist

        new_audit = os.path.join(self._workdir, self._deliverable_name, \
                os.path.basename(self._audit_file))
        shutil.copyfile(self._audit_file, new_audit)

        return new_audit
