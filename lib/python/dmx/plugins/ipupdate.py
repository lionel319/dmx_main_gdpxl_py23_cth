#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/ipupdate.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: ip update dmx subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import sys
import logging
import textwrap

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.updatevariant import UpdateVariant
import dmx.ecolib.ecosphere

class IPUpdateError(Exception): pass

class IPUpdate(Command):
    '''
    Updates an IP to keep it in sync with it's type definition
    Only adds new deliverables and updates the dev boms.
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Update an ip to keep it in sync with it's type definition
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''
        create ip arguments
        '''
        add_common_args(parser)
        parser.add_argument('-p', '--project',
                            metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip',
                            metavar='ip', required=True)
        parser.add_argument('-t', '--type', dest='ip_type',
                            metavar='ip_type', required=True)
        
    @classmethod
    def extra_help(cls):
        '''
        Detailed help for update ip
        '''
        extra_help = '''\
        "ip update" updates a ip by adding any new deliverables as defined by the ip type.
        It removes references to, and boms for deliverables that are not defined for
        the ip type.
        IP update may also modify the ip-type of an existing ip.

        --project <project>
        --ip <ip>
        
        Updates an ip to bring it in line with the latest definition for it's type.
        This command does the following:
        - add missing icm-libtypes to the variant
        - add 'dev' icm-library to libtypes if they do not exist.
        - add missing libtype@dev into variant@dev  
        - for all the variant's mutable config:
          > remove invalid libtype@config from those variant@config
          > delete the libtype@config (if it is a mutable config)

        --type <type> (optional)
        If ip-type is specified, ip update will modify the ip's ip-type to the
        specified ip-type.

        Example
        =======
        $ dmx ip update --project i10socfm --ip my_ip
        Update the ip my_ip within project i10socfm

        $ dmx ip update --project i10socfm --ip my_ip --type asic
        Modify the ip-type of my_ip to asic, then updates my_ip to the definition of asic ip-type
        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''
        Execute the subcommand
        '''
        project = args.project
        ip = args.ip
        ip_type = args.ip_type
        preview = args.preview

        ret = 1

        update = UpdateVariant(project, ip, ip_type, preview)
        ret = update.run()

        return (ret)
