'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/command.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  define the abnr plugin base class: abnrlib.command.Command

Author: Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function

## @addtogroup dmxlib
## @{

from builtins import object
import subprocess
import abc
from future.utils import with_metaclass

class Command(object):
    '''Empty base class used for defining abnr plugins'''

    @classmethod
    def get_help(cls):
        '''short subcommand description'''
        assert(False)

    @classmethod
    def extra_help(cls):
        '''comments. notes, and explanations for the command'''
        return ''

    @classmethod
    def add_args(cls, parser):
        '''subcommand arguments'''
        assert(False)

    @classmethod
    def command(cls, args):
        '''execute the subcommand'''
        assert(False)

    echo = True
    execute = True

    @classmethod
    def do_command(cls, command, ignore_exit_code=True):
        '''execute a single shell command, if command is '' echo a blank line if commands are being executed'''
        if cls.echo or not cls.execute:
            print(command)
        if command != '' and cls.execute:
            if 0 != subprocess.call(command, shell=True) and not ignore_exit_code:
                raise Exception('bad exit status from command: ' + command)

class Runner(with_metaclass(abc.ABCMeta, object)):
    '''
    Abstract base class for abnr command runners
    '''

    @abc.abstractmethod
    def run(self):
        '''
        Runs the command flow
        :return: Integer exit code
        '''
        return

## @}
