#!/usr/bin/env/python
"""Workspace object"""
import os
from joblib import Parallel, delayed
import dmx.dmxlib.workspace
from dmx.ipqclib.log import uiInfo, uiWarning, uiError, uiDebug
from dmx.ipqclib.utils import dir_accessible, RedirectStdStreams
from dmx.ipqclib.settings import _DB_FAMILY
from dmx.ecolib.ecosphere import EcoSphere


def populate_workspace(ip, ws, sync_cache=False, force=False): # pylint: disable=invalid-name
    """Sync workspace"""
    code = ws.sync(variants=[ip], skeleton=False, skip_update=True, sync_cache=sync_cache, \
            force=force)

    if code != 0:
        uiError("ipqclib/workspace.py: Error in syncing the workspace")
        return 1

    return 0

def easy_parallelize(my_list, ws, sync_cache=False, force=False): # pylint: disable=invalid-name
    """Parallelize function for workspace sync"""
    results = []
    results = Parallel(n_jobs=len(my_list), backend="threading")(delayed(populate_workspace)(i, \
                ws, sync_cache, force) for i in my_list)
    return results


def _get_project(ip_name, project=None):
    family = EcoSphere().get_family(_DB_FAMILY)
    project_name = family.get_icmproject_for_ip(ip_name)
    return project_name

class Workspace(dmx.dmxlib.workspace.Workspace):
    """Workspace object"""

    def __init__(self, ip_name, bom=None, project=None, ignore_clientname=False):
        self._ip_name = ip_name
        self._path = None
        self._ignore_clientname = ignore_clientname
        self._errors_waived = None
        self._errors_unwaived = None
        self._project = None

        if project:
            self._project  = project
        else:
            self._project = _get_project(ip_name)

        # Get workspace object
        if bom is None:
            dmx.dmxlib.workspace.Workspace.__init__(self, workspacepath=os.getcwd(), preview=False)
        # Create workspace if not existing
        else:
            dmx.dmxlib.workspace.Workspace.__init__(self, \
                    project=self._project, ip=self._ip_name, bom=bom, \
                    deliverable=None, preview=False)
            uiInfo("------------------")
            uiInfo("Workspace creation")
            uiInfo("------------------")
            self.create(ignore_clientname=self._ignore_clientname)

        # Get workspace path
        clientname = str(self.get_workspace_attributes()['Workspace'])
        dirpath = str(self.get_workspace_attributes()['Dir'])

        if (not self._ignore_clientname) and (dir_accessible(os.path.join(dirpath, clientname), \
                    os.F_OK)):
            self._path = os.path.join(dirpath, clientname)
        else:
            self._path = dirpath

        (self._project, self._bom) = self.get_project_bom(ip_name)
        uiDebug("Workspace - {}:{}@{}" .format(self._project, ip_name, self._bom))


    @property
    def path(self):
        return self._path

    @property
    def ip_name(self):
        "IP name"
        return self.ip

    @property
    def bom(self):
        "BOM name"
        return self._bom

    def sync_ipqc(self, sync_cache=False, dmx_cfgfile=None, requalify=False):
        """Sync workspace in parallele"""
        ips = self.get_ips()

        if dmx_cfgfile != None:
            self.sync(skeleton=False, skip_update=True, sync_cache=sync_cache, \
                    cfgfile=dmx_cfgfile, force=requalify)
        else:
            try:
                devnull = open(os.devnull, 'w')
                with RedirectStdStreams(stdout=devnull, stderr=devnull):
                    easy_parallelize(ips, self, sync_cache, force=requalify)
                uiInfo("{} are populated" .format(ips))
            except Exception as err: # pylint: disable=broad-except
                uiWarning("ipqclib.workspace.py: {}" .format(err))

        return 0
