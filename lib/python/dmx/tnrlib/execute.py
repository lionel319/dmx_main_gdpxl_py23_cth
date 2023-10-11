# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/execute.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
A simple wrapper around Popen to run commands and get their output.
"""
from subprocess import Popen, PIPE

def execute(cmd, shell=False):
    """
    Execute the cmd list and return (stdout,stderr) as lists.
    """
    if shell:
        cmd = ' '.join(cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell)
    (o,e) = p.communicate()
    return (o.splitlines(), e.splitlines())

