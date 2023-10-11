#!/usr/bin/env python
"""decorator to compute the status of the hierarchy IP
"""
# -*- coding: utf-8 -*-
import os
from operator import attrgetter
from dmx.ipqclib.settings import status_data, _IMMUTABLE_BOM, _ALL_WAIVED
from dmx.ipqclib.utils import file_accessible, get_catalog_paths
from dmx.ipqclib.report.report import Report
from dmx.ipqclib.options import FILTER_STATUS

def get_depth(ip, all_path): # pylint: disable=invalid-name
    """DAG - get depth of IP hierarchy
    """
    depth = 0

    for path in all_path:
        if ip in path:
            index = path.index(ip)

            if index > depth:
                depth = index

    return depth

# the default path=[] is necessary for recursivity
def find_all_paths(graph, start, end, path=[]): # pylint: disable=dangerous-default-value
    """DAG - get all possible paths from start IP  to end IP.
    """
    path = path + [start]
    if start == end:
        return [path]
    if start not in graph:
        return []
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths


# pylint: disable=protected-access
def pre_dry_run(func):
    """pre_dry_run decorator function for dry_run"""
    def func_wrapper(self):
        """Decorator wrapper function"""
        ### Format for hierarchical dashboard is fixed
        filename = 'ipqc.html'

        # No requalification
        #   --> if IP bom is immutable
        #       if report is in IPQC catalog, pick the results from IPQC catalog
        #       else compute results from local workspace
        #   --> if IP bom is mutable
        #       if report is already computed pick the results
        #       else compute results from local workspace
        if self._requalify is False:
            if self._ip.bom.startswith(_IMMUTABLE_BOM) or self._ip.bom.startswith('PREL'):
                (url_path, nfs_path) = get_catalog_paths(self._ip.name, self._ip.bom, \
                        self._ip.milestone)
            else:
                (url_path, nfs_path) = (self._ip.workdir, self._ip.workdir)

            # File are accessible on the http server. Pick the report on the server.
            #   Do not recompute everything
            if file_accessible(os.path.realpath(os.path.join(nfs_path, filename)), os.F_OK):
                self._ip.report_nfs = os.path.join(nfs_path, filename)
                self._ip.report_url = os.path.join(url_path, filename)
                result = []
                self._ip.record_file = os.path.join(nfs_path, 'ipqc.json')
                ip_data = self.set_status_from_record(self._ip.record_file)

                for cell, cell_values in sorted(ip_data.items()):
                    if (not isinstance(cell_values, dict)) or (cell == "summary"):
                        continue

                    for deliverable, deliverable_values in sorted(cell_values.items()):

                        if deliverable == 'status':
                            continue

                        ip_deliverable = self._ip.get_deliverable_ipqc(deliverable)
                        if (ip_deliverable is None) or (ip_deliverable.bom == ''):
                            continue

                        d_url_path = get_catalog_paths(self._ip.name, \
                                    self._ip.bom, self._ip.milestone, \
                                    deliverable=ip_deliverable)[0] \
                            if ip_deliverable.bom.startswith(_IMMUTABLE_BOM) or ip_deliverable.bom.startswith('PREL') else \
                            (os.path.join(self._ip.workdir, ip_deliverable.name), \
                             os.path.join(self._ip.workdir, ip_deliverable.name))[0]

                        ip_deliverable.report = os.path.join(d_url_path, filename)

                        if not isinstance(deliverable_values, dict):
                            continue

                        if  deliverable_values['status'] == _ALL_WAIVED:
                            result.append([cell, deliverable, '-', _ALL_WAIVED])
                            continue

                        for checker, checker_values in sorted(deliverable_values.items()):
                            if not isinstance(checker_values, dict):
                                continue
                            result.append([cell, deliverable, checker, \
                                    status_data[checker_values['status']]['message']])

                return result

            else:
                ### Start from the bottom and go to the top
                for sub_ipqc in sorted(self.hierarchy, key=attrgetter('depth'), reverse=True):

                    if sub_ipqc.ip.err != '':
                        continue

                    sub_ipqc.dry_run()
                    Report(sub_ipqc.ip.name, \
                            'html', \
                            ipqc=sub_ipqc, \
                            report_template=sub_ipqc.report_template, \
                            filter_status=sub_ipqc.options[FILTER_STATUS])
                return func(self)

        else:
            ### Start from the bottom and go to the top
            for sub_ipqc in sorted(self.hierarchy, key=attrgetter('depth'), reverse=True):

                if sub_ipqc.ip.err != '':
                    continue

                sub_ipqc.dry_run()
                Report(sub_ipqc.ip.name, \
                        'html', \
                        ipqc=sub_ipqc, \
                        report_template=sub_ipqc.report_template, \
                        filter_status=sub_ipqc.options[FILTER_STATUS] \
                        )

            return func(self)

    return func_wrapper
