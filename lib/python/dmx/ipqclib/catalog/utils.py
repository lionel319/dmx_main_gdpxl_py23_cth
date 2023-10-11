#!/usr/bin/env python
"""Utilities modules."""
import re
import subprocess

from dmx.ipqclib.utils import run_command
from dmx.ipqclib.log import uiError, uiWarning
from dmx.ipqclib.settings import _REL
from dmx.ipqclib.ipqcException import ReleaseInfoNotFound

_DELIMITER = '+++++'

class CatalogException(Exception):
    """Catalog execption"""
    pass

def get_variants(project):
    """
    Get the list of variants from ICManage for a given project
    """
    variants_list = []

    cmd = "pm variant -D {} -l {}" .format(_DELIMITER, project)
    (code, out) = run_command(cmd)

    if code != 0:
        uiError("Error when running {}\n{}" .format(cmd, out))
        return variants_list

    lines = out.strip().split('\n')

    for line in lines[1:]:
        variant_name = line.split(_DELIMITER)[0]

        if variant_name not in variants_list:
            variants_list.append(variant_name)

    return variants_list

def get_releases_for_variant(project, variant, products):
    """
        Get the list of releases for a given variant and project.
    """
    my_list = []
    products = [product.name for product in products]

    cmd = "pm configuration -D {} -l {} {}" .format(_DELIMITER, project, variant)

    out = ''
    try:
        out = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
	uiError("Variant not found")
	return my_list


    lines = out.strip().split('\n')

    for line in lines[1:]:
        release = line.split(_DELIMITER)[0]

        if (release not in my_list) and (release.startswith(_REL)):

            try:
                device = extract_info_from_release_name(release)[1]
            except (TypeError, ReleaseInfoNotFound) as err:
                uiWarning("Release {} for the given IP {}@{} is not compliant with the official release naming." .format(release, project, variant)) # pylint: disable=line-too-long
                uiWarning(err)
                continue

            # An IP can belong to multiple device. Example: SoftIP IPs are used in RNR and GDR
            # Do nothing if it does not belong to the given family.
            # A soft IP used in GDR does not belong to REYNOLDSROCK family.
            if device not in products:
                continue

            my_list.append(release)
        elif (release not in my_list) and (release.startswith('PREL')):
            my_list.append(release)

    return my_list

def extract_info_from_release_name(release):
    """
        Get milestone, device and revision information for a given release name.
    """
    pattern = _REL+'([0-9]\\.[0-9])([a-zA-Z0-9]+)'

    match = re.search(pattern, release)

    if match:
        milestone = match.group(1)
        thread = match.group(2)
        device = thread[0:3]
        revision = thread[3:]

        return (milestone, device, revision)

    raise ReleaseInfoNotFound("Release name {} is not valid." .format(release))
