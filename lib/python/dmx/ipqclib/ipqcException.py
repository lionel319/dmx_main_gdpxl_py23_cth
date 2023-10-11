#!/usr/bin/python
"""Exceptions for IPQC"""
# -*- coding: utf-8 -*-

import traceback

class ipqcException(Exception):
    """ Exception for IPQC"""
    pass

class ipqcHierException(Exception):
    """ Exception for IPQC hierarchy"""
    pass

class PermissionError(Exception):
    """ Exception for permission"""
    pass

class NotADirectoryError(Exception):
    """ Exception for path not a directory"""
    pass

class EmptyAuditXMLFile(Exception):
    """ Exception for empty audit file"""
    pass

class MissingDeliverable(Exception):
    """ Exception for missing deliverable"""
    pass

class IniConfigCorrupted(Exception):
    """ Exception for IPQC config file"""
    pass

class WaiverError(Exception):
    """ Exception for IPQC waiver error"""
    pass

class ReleaseInfoNotFound(Exception):
    """ Exception for IPQC catalog - release is not found"""
    pass

class IPQCSendmailException(Exception):
    """ Exception for IPQC sendmail"""

    def __init__(self, err):
        super(IPQCSendmailException, self).__init__(err)
        self.err = err

    def __str__(self):
        return 'Error during IPQC sendmail: ' + self.err

class IPQCRunAllException(Exception):
    """ Exception for IPQC run-all"""

    def __init__(self, err):
        super(IPQCRunAllException, self).__init__(err)
        self.err = err

    def __str__(self):
        return traceback.format_exc()
        return 'Error during IPQC run-all: ' + str(self.err)

class IPQCDryRunException(Exception):
    """ Exception for IPQC dry-run"""

    def __init__(self, err):
        super(IPQCDryRunException, self).__init__(err)
        self.err = err

    def __str__(self):
        return 'Error during IPQC dry-run: ' + str(self.err)
