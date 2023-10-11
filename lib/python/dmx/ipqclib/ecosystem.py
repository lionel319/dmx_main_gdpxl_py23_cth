#!/usr/bin/env python
"""ecosystem.py"""
import os
import json
from graphviz import Digraph
from dmx.ecolib.ecosphere import EcoSphere
from dmx.ipqclib.utils import remove_file, file_accessible, run_command, get_family
from dmx.ipqclib.settings import _DB_FAMILY, _DB_DEVICE
from dmx.ipqclib.log import uiError, uiCritical
from dmx.ipqclib.pre_dry_run import get_depth, find_all_paths

_COLOR = {'1.0': '#ff66ff', '2.0': '#00ccff', '3.0' : '#ffff99', '4.0' : '#ff6666', \
        '5.0' : '#66ff66', '99' : '#ff9900'}

def get_dot_milestone_info(init_value, deliverables_milestones, deliverable):
    """get_dot_milestone_info"""
    init_value = init_value + "<\n"
    init_value = init_value + '     <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">\n' # pylint: disable=C0301
    init_value = init_value + '         <TR>\n'
    init_value = init_value + '             <TD COLSPAN="{}">{}</TD>\n' \
            .format(len(deliverables_milestones[deliverable.name]), deliverable.name)
    init_value = init_value + '         </TR>\n'
    init_value = init_value + '         <TR>\n'

    for milestone in  deliverables_milestones[deliverable.name]:
        init_value = init_value + '             <TD BGCOLOR="{}">{}</TD>\n' \
                .format(_COLOR[milestone], milestone)

    init_value = init_value +   "   </TR>\n"

    return init_value

def get_dot_deliverable_info(init_value, deliverable):
    """get_dot_deliverable_info"""
    init_value = init_value + "<\n"
    init_value = init_value + '     <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">\n' # pylint: disable=C0301
    init_value = init_value + '         <TR>\n'
    init_value = init_value + '             <TD>{}</TD>\n' .format(deliverable.name)
    init_value = init_value +   "   </TR>\n"

    return init_value


def get_dot_checkers_ms_info(init_value, checkers, deliverables_milestones, deliverable):
    """get_dot_checkers_ms_info"""
    c_flag = []
    for checker in checkers:
        if checker in c_flag:
            continue
        init_value = init_value + '     <TR>\n'
        init_value = init_value + '             <TD  COLSPAN="{}" BGCOLOR="#B8B8B8">{}</TD>\n' \
                .format(len(deliverables_milestones[deliverable.name]), checker) # pylint: disable=C0301
        init_value = init_value +   "   </TR>\n"
        c_flag.append(checker)
    return init_value

def get_dot_checkers_info(init_value, checkers):
    """get_dot_checkers_info"""
    c_flag = []
    for checker in checkers:
        if checker in c_flag:
            continue
        init_value = init_value + '         <TR>\n'
        init_value = init_value + '             <TD BGCOLOR="#B8B8B8">{}</TD>\n' .format(checker)
        init_value = init_value +   "   </TR>\n"
        c_flag.append(checker)
    return init_value

class Ecosystem(object):
    """Ecosystem class"""
    def __init__(self, ip=None, project=None, milestones=False, milestone='99', ip_type=None, checkers=False, 
            ip_graph=False, output_dir=None, view=None):

        if not(ip is None) and (len(ip.split('@')) > 1):
            self._ip = ip.split('@')[0]
            self._bom = ip.split('@')[1]
        else:
            self._ip = ip
            self._bom = None

        self._milestones = milestones
        self._milestone = milestone
        self._ip_type = ip_type
        self._checkers = checkers
        self._project = project
        self._ip_graph = ip_graph
        self._view = view

        if output_dir != None:
            self._output_dir = output_dir
        else:
            self._output_dir = os.getcwd()
        self._output_file = os.path.join(self._output_dir, 'ecosystem')

        if file_accessible(self._output_file, os.W_OK):
            remove_file(self._output_file)

        self._family = get_family()
        self._device = self._family.get_product(_DB_DEVICE)

    def _get_deliverables(self):
        if self._ip != None:
            ipobj = self._family.get_ip(self._ip, project_filter=self._project)
            if self._bom != None:
                deliverables = ipobj.get_deliverables(bom=self._bom, local=False, \
                        milestone=self._milestone)
            else:
                deliverables = ipobj.get_all_deliverables(milestone=self._milestone)

        elif self._ip_type != None:
            ipobj = self._family.get_iptype(self._ip_type)
            deliverables = ipobj.get_all_deliverables(milestone=self._milestone)
        else:
            deliverables = self._device.get_deliverables(milestone=self._milestone)


        if self._view != None:
            deliverables = []
            list_of_views = [view.name for view in self._family.get_views()]

            if not self._view in list_of_views:
                uiCritical("{} is not a valid views. Valid views are {}" .format(self._view, \
                        list_of_views))

            view = self._family.get_view(self._view)
            tmp_deliverables = view.get_deliverables()

            for deliverable_from_view in tmp_deliverables:
                if deliverable_from_view.name in [deli.name for deli in \
                        self._device.get_deliverables(milestone=self._milestone)]:
                    deliverables.append(deliverable_from_view)

        return deliverables

    def _get_milestones_per_deliverable(self):
        deliverables_milestones = {}
        for deliverable in self._device.get_deliverables():

            milestones_list = []

            for milestone in self._device.get_milestones():
                if milestone.name == '99':
                    continue
                deliverables_list = [d.name for d in \
                        self._device.get_deliverables(milestone=milestone.name)]

                if deliverable.name in deliverables_list:
                    milestones_list.append(milestone.name)

            deliverables_milestones[deliverable.name] = milestones_list

        return deliverables_milestones

    def _get_label(self):
        label = '"{} {} - Deliverable ecosystem' .format(_DB_FAMILY, _DB_DEVICE)

        if not self._ip is None:
            if self._bom != None:
                label = label + ' - IP ' + self._ip + '@' + self._bom
            else:
                label = label + ' - IP ' + self._ip

        if not self._ip_type is None:
            label = label + ' - IP Type ' + self._ip_type

        if (self._milestones != True) and (self._milestone != '99'):
            label = label + ' - milestone ' + self._milestone

        if self._view != None:
            label = label + ' - view ' + self._view

        label = 'label=' + label + '"'

        return label


    def get_ecosystem(self):
        """get_ecosystem - graph creation"""

        deliverables_milestones = self._get_milestones_per_deliverable()
        deliverables = self._get_deliverables()

        label = self._get_label()

        dot = Digraph(comment='Falcon Ecosystem')
        dot.body.extend(['rankdir=TB', 'size="8,5"', label])

        for deliverable in deliverables:

            checkers = []

            if self._checkers is True:
                checkers = [c.checkname for c in deliverable.get_checkers()]

            init_value = ''

            # MILESTONE
            if self._milestones is True:
                init_value = get_dot_milestone_info(init_value, deliverables_milestones, \
                        deliverable)

                # CHECKERS
                if self._checkers is True:
                    init_value = get_dot_checkers_ms_info(init_value, checkers, \
                            deliverables_milestones, deliverable)

                init_value = init_value + "</TABLE>>"

                dot.node(deliverable.name, '''{}''' .format(init_value), shape="box")
            else:
                init_value = get_dot_deliverable_info(init_value, deliverable)

                # CHECKERS
                if self._checkers is True:
                    init_value = get_dot_checkers_info(init_value, checkers)

                init_value = init_value + "</TABLE>>"

                dot.node(deliverable.name, '''{}''' .format(init_value), shape="box")

            if deliverable.successor == []:
                continue

            for successor in deliverable.successor:
                if successor in [d.name for d in deliverables]:
                    dot.edge(deliverable.name, successor)

        dot.render(self._output_file, view=False)

        if self._ip_graph is True:
            get_ip_graph(self._ip, self._bom)

        return self._output_file+'.pdf'

    @property
    def output_file(self):
        """output_file"""
        return self._output_file


def get_input_info(ip_name, project, bom, output_dir):
    """get_input_info"""
    family = get_family()

    if bom is None:
        bom = 'dev'

    if project is None:
        project = family.get_icmproject_for_ip(ip_name)

    if not output_dir is None:
        output_dir = output_dir
    else:
        output_dir = os.getcwd()

    return project, bom, output_dir

def get_ip_hierarchy(data):
    """get_ip_hierarchy"""
    hierarchy = {}
    boms = {}

    for i in data:
        #ipname = (i.split('/')[1]).split('@')[0]
        #sub_bom = (i.split('/')[1]).split('@')[1]
        [project, ipname, sub_bom] = i.split('/')

        list_of_subips = []

        for sub_ip in data[i]['ip']:
            #sname = (sub_ip.split('/')[1]).split('@')[0]
            [project, sname, sbom] = i.split('/')
            list_of_subips.append(sname)

        hierarchy[ipname] = list_of_subips
        boms[ipname] = sub_bom

    return hierarchy, boms

def get_ip_top_info(data, info, ip_name):
    """get_ip_top_info"""

    top_hierarchy = {}
    top_boms = {}

    for i in data:
        #ipname = (i.split('/')[1]).split('@')[0]
        #sub_bom = (i.split('/')[1]).split('@')[1]
        [project, ipname, sub_bom] = i.split('/')

        if ipname == ip_name:
            list_of_ips = []

            for sub_ip in data[i]['ip']:
                #sname = (sub_ip.split('/')[1]).split('@')[0]
                #sbom = (sub_ip.split('/')[1]).split('@')[1]
                [project, sname, sbom] = i.split('/')

                list_of_ips.append(sname)
                info["boms"][sname] = sbom

            top_hierarchy[ipname] = list_of_ips
            top_boms[ipname] = sub_bom

    return top_hierarchy, top_boms


def get_ip_hierarchy_info(ip_name, data):
    """get_ip_hierarchy_info"""

    info = {}

    (info["hierarchy"], info["boms"]) = get_ip_hierarchy(data)
    (info["top_hierarchy"], info["top_boms"]) = get_ip_top_info(data, info, ip_name)

    leaf_ips = []
    depths_ip = {}

    for ipname, sub_ips in info["hierarchy"].items():

        if sub_ips == []:
            leaf_ips.append(ipname)


    for ipname, sub_ips in info["hierarchy"].items():

        depth = {}
        paths = []

        for subip in leaf_ips:
            paths = paths + find_all_paths(info["hierarchy"], ip_name, subip)

        depth[ipname] = get_depth(ipname, paths)
        depths = list(set(depth.values()))
        max_depth = max(depths)

        depths_ip[ipname] = max_depth

    return info["hierarchy"], depths_ip


def get_ip_graph(ip_name, bom, output_dir=None, project=None):
    """get_ip_graph"""

    input_info = {}
    input_info["ip_name"] = ip_name
    (input_info["project"], input_info["bom"], input_info["output_dir"]) = get_input_info(ip_name, \
            project, bom, output_dir)
    input_info["output_file"] = os.path.join(input_info["output_dir"], 'ip_graph')
    input_info["tmp_file"] = os.path.join(input_info["output_dir"], 'hierarchy_tmp.json')

    (code, out) = run_command("dmx report content -p {} -i {} -b {} --json {}" .format(\
            input_info["project"], ip_name, input_info["bom"], input_info["tmp_file"]))

    if code != 0:
        uiError(out)
        exit(1)

    input_info["data"] = json.load(open(input_info["tmp_file"]))

    (input_info["hierarchy"], input_info["depths_ip"]) = \
            get_ip_hierarchy_info(ip_name, input_info["data"])


    label = 'label="IP graph - {} {} - {}@{}"' .format(_DB_FAMILY, _DB_DEVICE, ip_name, \
            input_info["bom"])

    dot = Digraph(comment='IP Hierarchy')
    dot.body.extend(['rankdir=TB', 'size="8,5"', label])

    for ipname, depth in input_info["depths_ip"].items():

        init_value = '' + "<\n"
        init_value = init_value + '     <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">\n' # pylint: disable=C0301
        init_value = init_value + '         <TR>\n'
        init_value = init_value + '             <TD>{}</TD>\n' .format(ipname)
        init_value = init_value +   "   </TR>\n"

        init_value = init_value + '         <TR>\n'
        init_value = init_value + '             <TD>level {}</TD>\n' .format(depth)
        init_value = init_value +   "   </TR>\n"
        init_value = init_value + "</TABLE>>"


        dot.node(ipname, init_value)

    for ipname, sub_ips in input_info["hierarchy"].items():
        for sub_ip in sub_ips:
            dot.edge(ipname, sub_ip)

    if file_accessible(input_info["output_file"], os.W_OK):
        remove_file(input_info["output_file"])

    dot.render(input_info["output_file"], view=False)

    return input_info["output_file"]+'.pdf'
