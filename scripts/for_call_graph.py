#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecolib.ecosphere import EcoSphere

print EcoSphere().get_family("Nadder").get_thread("ND5revA").get_milestone("4.5").get_checkers("rtl")
