#!/usr/bin/env python
"""Check values given in options are correct."""
import os
from functools import wraps
from dmx.ipqclib.log import uiError, uiCritical
from dmx.ecolib.ecosphere import EcoSphere
from dmx.ecolib.ip import IPError
from dmx.dmlib.dmError import dmError
from dmx.ecolib.family import FamilyError
from dmx.ecolib.iptype import IPTypeError
from dmx.ipqclib.settings import _DB_FAMILY, _DB_DEVICE, _FUNCTIONALITY, _FUNC_FILE
from dmx.ipqclib.ipqcException import ipqcException, IPQCRunAllException
from dmx.ipqclib.utils import file_accessible, is_non_zero_file

def _get_info(args):
    if len(args.ip.split('@')) > 1:
        g_bom = args.ip.split('@')[1]
        local = False
    else:
        g_bom = None
        local = True

    return (g_bom, local)

def _get_ip_list(args):
    ip_list = []
    family = EcoSphere().get_family(_DB_FAMILY)
    ips = family.get_ips_names()

    if (len(args.ip_filter) == 1) and file_accessible(args.ip_filter[0], os.R_OK):

        if not is_non_zero_file(args.ip_filter[0]):
            uiCritical("--ip-filter option: {0} is emtpy".format(args.ip_filter[0]))

        with open(args.ip_filter[0], 'r') as fid:
            content = fid.read().strip()
            ip_list = content.split('\n')
    else:
        not_existing_ips = []

        for ip in args.ip_filter: # pylint: disable=invalid-name
            if not ip in ips:
                not_existing_ips.append(ip)
                continue

            ip_list.append(ip)

        if not_existing_ips != []:
            uiCritical("{0} does not exist".format(not_existing_ips))

    return ip_list

def precheck(func):
    """Precheck decorator for main function"""
    @wraps(func)
    def wrapper(args):
        """Wrapper functio for precheck decorator"""

        if (args.which == "run-all") or (args.which == "setup"):

            if (args.initfile != None) and (args.no_hierarchy is False):
                raise IPQCRunAllException("argument --init-file must be used with --no-hierarchy set to True") # pylint: disable=line-too-long


        if args.which == "dry-run":

            if (args.report_template == _FUNCTIONALITY) and \
                                      not file_accessible(_FUNC_FILE, os.R_OK):
                uiCritical("File {} not found !\n\t\tIf you are using --report-template functionality, {} file needs to exist" .format(_FUNC_FILE, _FUNC_FILE)) # pylint: disable=line-too-long

            # process ip-filter option. Can be a file or a list of ips
            if args.ip_filter != []:
                args.ip_filter = _get_ip_list(args)


        #############################################################
        ############ compute the set of deliverables ################
        # Support following case:
        #   --deliverable x y
        #   --deliverable view_phys
        #   --deliverable view_phys view_time
        #   --deliverable view_phys x y
        #############################################################
        if ('deliverable' in vars(args)) and (args.deliverable != []):

            family = EcoSphere().get_family(_DB_FAMILY)

            try:
                ip = family.get_ip(args.ip.split('@')[0], project_filter=args.project) #pylint: disable=invalid-name
                (g_bom, local) = _get_info(args)

                ip.get_all_deliverables(milestone=args.milestone, roadmap=_DB_DEVICE)
                ip.get_deliverables(bom=g_bom, local=local)
                ip.get_unneeded_deliverables(bom=g_bom, local=local)

                for deliverable in args.deliverable:
                    if deliverable in [view.name for view in family.get_views()]:
                        view = family.get_view(deliverable)
                        args.deliverable = args.deliverable + \
                            [i.name for i in view.get_deliverables()]
                        index = args.deliverable.index(deliverable)
                        args.deliverable.pop(index)
                args.deliverable = list(set(args.deliverable))

            except FamilyError as err:
                uiCritical(err)
            except IPError as err:
                uiError(err)
                raise ipqcException(err)
            except dmError as err:
                # pylint: disable=line-too-long
                err = str(err) + """\n\n\tWhat are the actions you can take:
                    1/ If you are out of workspace you need to give a <bom> to ip name option invokation: -i/--ip_name <ip_name>@<bom>.
                    2/ If you are within a workspace, check that .icmconfig files are not empty\n"""
                # pylint: enable=line-too-long
                raise ipqcException(err)
            except IPTypeError as err:
                uiCritical(err)

        # cellname can be a file containing the list of cells names or can be
        #   a list of cells names.
        if ("cellname" in vars(args)) and (args.cellname != []):

            arg = args.cellname
            if (len(arg) == 1) and file_accessible(arg[0], os.R_OK):
                with open(arg[0], 'r') as fid:
                    content = fid.read().strip().split('\n')
                    args.cellname = content

        result = func(args)
        return result

    return wrapper
