#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/saveworkspace.py#1 $

"""
.. program:: saveworkspace

The `saveworkspace` command saves IC Manage workspace data to persistent JSON
files.  By default it saves them in the workspace directory::

  ICManageWorkspace.save/composites.json
  ICManageWorkspace.save/configurations.json
  ICManageWorkspace.save/hierarchy.json
  ICManageWorkspace.save/workspace.json

You can specify an alternate directory using the `--savedir` option.

After you use `saveworkspace` you can copy the workspace to some location
unknown to IC Manage.  When Altera Design Data Management commands like the
:doc:`expandfilelist` and the :doc:`vp` discover that your work area is unknown
to IC Manage, they will load the previously saved data instead.

Saving Workspace Data for Every IP
=====================================

When you specify the `--every` command line option, `saveworkspace` saves data
for each individual IP as if it were the top IP in the workspace.
        
The files are written to directory `--savedir` within the IP directory in
the specified `--saveworkspace` directory.  That is, for each IP `ipName`, the
files are saved in directory::
        
    saveworkspace/ipName/savedir
        
The default for `--saveworkspace` is the path to the current
workspace.  The default `--savedir` is `ICManageWorkspace.save`.

If you want to restore the workspace data from one of the sets of JSON files
created with `--every`, specify both the directory containing the files and the
IP name.

Command Options
=============================

The `saveworkspace` command has the following options:

.. option::  --workspace WORKSPACEPATH

The path to the IC Manage workspace.  The default is the
workspace that contains the current working directory.
The default is usually satisfactory.

.. option::  --savedir SAVEDIR

Directory to which the JSON files will be saved.
The default is `ICManageWorkspace.save` in the IC Manage workspace directory.
The default is usually satisfactory.

.. option:: --ip IPNAME

Name of the IP whose hierarchy is to be saved.
Of course this must be one of the IPs in the
workspace.  The default is the workspace top IP.
The default is usually satisfactory.

.. option:: --every

Save data for each individual IP as if it were the top IP in the workspace.  See
`Saving Workspace Data for Every IP`_.

.. option:: --saveworkspace OTHERWORKSPACE

The path of another workspace in which to save individual IP data.  The
default is the path to the current workspace.

Thus the JSON files for IP `ipName` will be saved in directory::

  OTHERWORKSPACE/ipName/SAVEDIR

It is an error to specify this option without the `--every` option.

.. option::  --version, -V

Show program's version number and exit.

Usage Examples
=============================

Use `saveworkspace` to save the state of the workspace in the default directory
`ICManageWorkspace.save` within the IC Manage workspace::

  arc shell project/nightfury
  cd /path/to/icmanage/workspace/
  saveworkspace
  
  cp -rp . /some/other/workingdir

  cd /some/other/workingdir
  vp --deliverables BDS,RTL --ip ip1 --flowalias BDS,BCMRBC,RTL
  vp --deliverables BDS,RTL --ip ip2 --flowalias BDS,BCMRBC,RTL
  
File Schema
=============================
All files saved by `saveworkspace` are JSON files.

configurations.json
---------------------
This file contains a dictionary.  The keys are the names of the composite
configurations in the workspace, and the values are the
`[projectName, ipName, configurationName]` triplet for the composite
configuration.

For example::

  {
    "icmanageworkspace03": [
      "zz_dm_test", 
      "icmanageworkspace03", 
      "dev"
    ], 
    "icmanageworkspace02": [
      "zz_dm_test", 
      "icmanageworkspace02", 
      "dev"
    ], 
    "icmanageworkspace01": [
      "zz_dm_test", 
      "icmanageworkspace01", 
      "dev"
    ]
  }


composites.json
---------------------
This file contains a list with the top composite configuration followed by the
flattened library configurations.

The structure of this file is identical to that produced by the IC Manage
command::

   pm configuration -L -a ... -DJ:
   
For example::

  [
    {
      "Property": [
        ""
      ], 
      "ConfType": "composite", 
      "LibDefsPath": "", 
      "Variant": "icmanageworkspace01", 
      "Project": "zz_dm_test", 
      "Configuration": "dev", 
      "ExtTrim": [
        ""
      ], 
      "Desc": ""
    }, 
    {
      "Description": "[Local](@icmanageworkspace01/rdf)", 
      "Variant": "icmanageworkspace01", 
      "Library": "icmanageworkspace01", 
      "Project": "IP:zz_dm_test", 
      "Location": "icmanageworkspace01/rdf", 
      "Release": "#ActiveDev", 
      "LibType": "rdf", 
      "Configuration": "dev"
    },
        ...
  }

hierarchy.json
---------------------
This file contains a dictionary showing the IP hierarchy of the IP.  The keys
are the names of all composite configurations in the workspace, and the values
are the names of the composite configurations included in the key configuration.

In other words, the keys are the names of all IPs in the workspace, and the
values are lists of IPs that are instantiated in each IP.

In the following example, `icmanageworkspace01` instantiates
`icmanageworkspace02`, which instantiates `icmanageworkspace03`.
`icmanageworkspace03` instantiates no other IP::

  {
    "icmanageworkspace01": [
      "icmanageworkspace02"
    ]
    "icmanageworkspace02": [
      "icmanageworkspace03"
    ], 
    "icmanageworkspace03": [], 
  }

info.json
---------------------
This file contains a dictionary showing information about the workspace that was
saved.

This file contains the same data produced by the IC Manage command::

   icmp4 info
   
For example::

{
  "Client name": "envadm.zz_dm_test.icmanageworkspace01.5", 
  "Client root": "/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5", 
  "Server version": "P4D/LINUX26X86_64/2010.2/347035 (2011/08/24)", 
  "Client address": "137.57.239.88:50550", 
  "Server root": "/usr/local/icmanage/depot", 
  "Server uptime": "6959:31:51", 
  "Server address": "sj-ice-icm.altera.com:1686", 
  "User name": "rgetov", 
  "Server license": "Altera 701 users for icmanage (support ends 2014/06/10) (expires 2014/06/10)", 
  "Case Handling": "sensitive", 
  "Current directory": "/ice_da/infra/icm/workspace/VP_ws/envadm.zz_dm_test.icmanageworkspace01.5", 
  "Client host": "sj-jmcgehee-l", 
  "Server date": "2013/09/19 14:51:43 -0700 PDT", 
  "Server license-ip": "137.57.243.70"
}

workspace.json
---------------------
The structure of this file is identical to that produced by the IC Manage
command::

   pm workspace -L ... -DJ:

The most interesting information in this file is the project name,
variant (IP) name, and configuration name of the top IP in the workspace.

For example::

  {
    "Loc": "", 
    "Attr": [
      "withClient", 
      "postSync", 
      "preSync"
    ], 
    "ConfType": "composite", 
    "Variant": "icmanageworkspace01", 
    "Project": "zz_dm_test", 
    "User": "rgetov", 
    "Workspace": "envadm.zz_dm_test.icmanageworkspace01.5", 
    "LibType": "", 
    "Config": "dev", 
    "Mount": [
      "native"
    ], 
    "Dir": "/ice_da/infra/icm/workspace/VP_ws", 
    "Desc": "ICManageWorkspace unit test workspace"
  }
"""


import sys
import os
import argparse
import traceback

dmRoot = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'lib', 'python')
sys.path.insert(0, os.path.abspath(dmRoot))
                
from dmx.dmlib.dmError import dmError
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace
from dmx.utillib.version import Version

VERSION = Version()

def main(argv=None): # pylint: disable = W0613
    parser = argparse.ArgumentParser(
        description="Save IC Manage workspace data to persistent JSON files.  ")
    parser.add_argument('--ip', '-i', dest='ipName',
                        help="Name of the IP whose hierarchy is to be saved.  "
                             "Of course this must be one of the IPs in the "
                             "workspace.  The default is the workspace top IP.  "
                             "The default is usually satisfactory.")
    parser.add_argument('--workspace', '-w', dest='workspacePath',
                        default=None,
                        help="Workspace location.  The default is the workspace "
                             "that contains the current working directory.  "
                             "The default is usually satisfactory.")
    parser.add_argument('--savedir', '-s', '--outputdir', '-o', dest='saveDir',
                        help="Directory to which the JSON files will be saved. "
                             "The default is '{}' in the IC Manage workspace "
                             "directory.  "
                             "The default is usually satisfactory."
                             "".format(ICManageWorkspace.defaultSaveDirectoryName))
    parser.add_argument('--every', '-e', action="store_true", default=False,
                        help="Save data for each individual IP as if it were "
                        "the top IP in the workspace.")
    parser.add_argument('--saveworkspace', dest='saveWorkspacePath',
                        help="The path of another workspace in which to save "
                        "individual IP data. The default is the path to the "
                        "current workspace.  It is an error to specify this "
                        "option without the --every option.")

    parser.add_argument('--version', '-V', action='version',
                        version="{} Version {}\n".format(os.path.splitext(os.path.basename(__file__))[0], VERSION.dmx))
    args = parser.parse_args()
    
    if args.saveWorkspacePath and not args.every:
        raise dmError("The --saveworkspace option can only be used when the --every option is specified")
    
    ws = ICManageWorkspace(args.workspacePath, args.ipName)
    if args.every:
        ws.saveEveryIP(saveWorkspacePath=args.saveWorkspacePath,
                       saveDirName=args.saveDir)
    else:
        ws.save(args.saveDir)


def customExcepthook(typeIn, valueIn, tracebackIn):
    '''Override the default uncaught exception handler.'''
    print(typeIn.__name__ + ': ' + str(valueIn))
    print("")
    print("Make sure to include both the above error and the following in any questions you have:")
    print("Application {} version {}".format(__file__, VERSION.dmx))
    traceback.print_exception(typeIn, valueIn, tracebackIn)
    
sys.excepthook = customExcepthook

if __name__ == "__main__":
    sys.exit(main())
