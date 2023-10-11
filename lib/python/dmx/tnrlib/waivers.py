#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/waivers.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
The Waivers class supports tracking and fetching of waivers.
Waivers may come from the ICE_MAN web application, or be 
provided via WaiverFile instances.

You must initialize Waivers with the name of the IC Manage 
configuration you want to validate against (only applies to
web-based waivers; WavierFile waivers apply to any configuration).

Use add_waiver_file() before you look for matching waivers to 
let this class know about waivers defined via waiver files.

Use find_matching_waiver() to see if a waiver exists. 
passing the variant, test name, and failing test result.
If a waiver exists, the waiver info will be returned.
If a waiver does not exist, None will be returned.
"""

# Altera libs
import os,sys
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
from dmx.tnrlib.waiver_file import WaiverFile


class Waivers:
    """
    Interface to ICE_MAN django app geared towards clients
    which need to apply waivers to a set of test failures.
    """
    def __init__(self):
        """
        Project is the IC Manage project waivers are associated with.

        Configuration is a snapshot configuration for the release;
        for libraries, it is the simple snap configuration of the library 
        being released, for variants it is the variant snapshot.

        Application_date is the date when the waiver is applied,
        although in fact this is ignored by the system at this time.

        Webapi allows the client to provide a different web interface
        for development/testing purposes.

        The milestone and thread are generally required since waivers 
        are usually specific to milestone/thread.  Global waivers should
        be rare, and those are the only ones that will be returned if
        you don't provide a milestone and thread.
        """
        self.waiver_files = []

    def add_waiver_file(self, waiver_file):
        """
        Tells this class about additional waivers which can apply
        when searching for matching waivers.  The argument is an
        instance of WaiverFile.  Do not add duplicate waiver_files
        as this will slow down searching for matches.
        """
        self.waiver_files.append(waiver_file)

    def find_matching_waiver(self, variant, flow, subflow, result):
        """
        Queries ICE_MAN to determine if a waiver exists for
        the given variant testflow (sub-)test result.
        Returns None if no applicable waiver exists;
        returns (creator, description, filepath) otherwise.
        """
        for waiver_file in self.waiver_files:
            match = waiver_file.find_matching_waiver(variant, flow, subflow, result)
            if match is not None:
                return match
        return None

    def find_matching_hsdes_waiver(self, variant, flow, subflow, result):
        """
        Queries ICE_MAN to determine if a waiver exists for
        the given variant testflow (sub-)test result.
        Returns None if no applicable waiver exists;
        returns (creator, description, filepath) otherwise.
        """
        for waiver_file in self.waiver_files:
            match = waiver_file.find_matching_hsdes_waiver(variant, flow, subflow, result)
            if match is not None:
                return match
        return None

