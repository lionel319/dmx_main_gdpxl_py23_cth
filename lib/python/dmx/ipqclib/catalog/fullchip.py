#!/usr/bin/env python
""" FullChip object
    It servers to define the hierarchy (Fullchip, Subsystem, IPs).
"""
import os
import re
import json
from dmx.ipqclib.utils import file_accessible, run_command
from dmx.ipqclib.catalog.utils import CatalogException


class FullChip(object):
    """ FullChip object
    """
    def __init__(self, name, icmproject, release, device, ipqc_catalog_settings_path):
        self._name = name
        self._icmproject = icmproject
        self._release = release
        self._device = device
        self._ipqc_catalog_settings_path = ipqc_catalog_settings_path
        filename = '{}_{}_hierarchy.json' .format(self._name, self._release)
        if file_accessible(filename, os.R_OK):
            self._hierarchy_file = filename
        else:
            self._hierarchy_file = self._get_hierarchy_file()
        (self._integration_ips, self._ips) = self._get_ips_by_category()


    def _get_hierarchy_file(self):

        filename = '{}_{}_hierarchy.json' .format(self._name, self._release)
        json_file = os.path.join(self._ipqc_catalog_settings_path, filename)

        (code, out) = run_command('dmx report content -p {} -i {} -b {} --json {}' \
                .format(self._icmproject, self._name, self._release, json_file))

        if code != 0:
            raise CatalogException("Error in catalog: {}" .format(out))

        return json_file

    def _get_ips_by_category(self):

        integration_ips = []
        all_ips = []

        with open(self._hierarchy_file, 'r') as fid:
            data = json.load(fid)

            for ip in data: # pylint: disable=invalid-name

                pattern = r'\S+/{}@\S+' .format(self._name)
                if re.search(pattern, ip):
                    pattern = r'\S+/(\S+)@\S+'
                    for subsystem in data[ip]['ip']:
                        match = re.search(pattern, subsystem)
                        if match:
                            integration_ips.append(match.group(1))


                pattern = r'\S+/(\S+)@\S+'
                match = re.search(pattern, ip)
                if match:
                    if (match.group(1) in integration_ips) or (match.group(1) == self._name):
                        continue

                    all_ips.append(match.group(1))

        return (integration_ips, all_ips)



    @property
    def name(self):
        """Fullchip name"""
        return self._name

    @property
    def release(self):
        """Fullchip release"""
        return self._release

    @property
    def device(self):
        """Fullchip device"""
        return self._device

    @property
    def integration_ips(self):
        """Subsystems"""
        return self._integration_ips

    @property
    def ips(self):
        """IPs"""
        return self._ips
