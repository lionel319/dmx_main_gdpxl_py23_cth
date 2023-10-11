#!/usr/bin/env python
""" get_waivers function
"""
from dmx.utillib.decorators import memoized
from dmx.ipqclib.log import uiError
from dmx.ipqclib.ipqcException import WaiverError
from dmx.tnrlib.waiver_file import WaiverFile

################## get_waivers() ####################
@memoized
def get_waivers(filepath):
    """Return list of waivers:
        --> waivers at deliverable level
        --> waivers at IP level
    """
    waiver = WaiverFile()

    try:
        waiver.load_from_file(filepath)
    except LookupError as err:
        raise WaiverError(err)
    except TypeError as err:
        raise WaiverError(err)
    except Exception as err:
        uiError(err)
        raise WaiverError(err)
    return waiver.waivers
