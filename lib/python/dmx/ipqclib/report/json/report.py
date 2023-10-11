#!/usr/bin/env python
from __future__ import print_function
from dmx.ipqclib.settings import _ARC_URL

class ReportJSON():

    def __init__(self, ip_name, ipqc=None):

        self._ipqc = ipqc
        self._filename = self._ipqc.ip.record_file
        self._ipqc.ip.report_url = _ARC_URL + self._filename


    @property
    def filename(self):
        return self._filename
