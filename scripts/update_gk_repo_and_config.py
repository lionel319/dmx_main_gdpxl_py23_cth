#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/scripts/update_gk_repo_and_config.py#5 $
$Change: 7698488 $
$DateTime: 2023/07/14 01:08:08 $
$Author: lionelta $

Description: API functions which interacts with Gatekeeper
'''
from __future__ import print_function

import os
import logging
import sys
import re
import argparse
from pprint import pprint,pformat
import textwrap

LIB = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.gkutils

LOGGER = logging.getLogger()

def main():
    args = get_args()
    set_logger(args)
    if args.debug:
        pprint(args)
        print(args.__dict__)
    
    gk = dmx.utillib.gkutils.GkUtils()
    if args.func == 'igr':
        return gk.clone_git_template_to_git_repo(args.tmplpath, args.repopath)
    elif args.func == 'ugc':
        gk.update_gk_clusters_steppings(args.clusters, args.steppings, preview=args.dryrun)
    elif args.func == 'gnl':
        ret = gk.get_newly_created_icm_libraries(args.libtype, args.days)
        pprint(ret)
    elif args.func == 'rrc':
        gk.reread_config(preview=args.dryrun)
    elif args.func == 'dpc':
        gk.dump_config()
    elif args.func == 'uet':
        gk.update_everything(args.libtype, args.days, args.tmplpath, args.repopath, preview=args.dryrun)
    elif args.func == 'crg':
        gk.change_repo_group(args.group, args.repopath)
    elif args.func == 'cb':
        gk.create_branch(args.cluster, args.step, args.branch, args.fromrev)
    elif args.func == 'lb':
        gk.list_branches(args.cluster, args.step)
    elif args.func == 'apu':
        gk.add_power_users(args.project, args.cluster, args.stepping, args.userids, preview=args.dryrun)

def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subpar = parser.add_subparsers()
    
    lb = subpar.add_parser('list_branches', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='List all branches for a given cluster/step.')
    lb.add_argument('--debug', action='store_true', default=False)
    lb.add_argument('--cluster', '-c', required=True, help='cluster')
    lb.add_argument('--step', '-s', required=True, help='step')
    lb.set_defaults(func='lb')
    
    cb = subpar.add_parser('create_branch', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='Create new branch for a given cluster/step git repo.')
    cb.add_argument('--debug', action='store_true', default=False)
    cb.add_argument('--cluster', '-c', required=True, help='cluster')
    cb.add_argument('--step', '-s', required=True, help='step')
    cb.add_argument('--branch', '-b', required=True, help='branch')
    cb.add_argument('--fromrev', '-f', required=False, default=None, help='If given, will branch from given SHA1/tag. Default will branch from master/HEAD')
    cb.set_defaults(func='cb')
    
    gnl = subpar.add_parser('change_repo_group', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='Change linux group for git repo.')
    gnl.add_argument('--debug', action='store_true', default=False)
    gnl.add_argument('--repopath', '-r', required=True, help='Fullpath to git_repo. Eg: /nfs/site/disks/psg.git.001/git_repos/liotest1-a0')
    gnl.add_argument('--group', '-g', required=True, help='group name')
    gnl.set_defaults(func='crg')

    gnl = subpar.add_parser('get_new_libraries', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='report out all newly created icm-libraries.')
    gnl.add_argument('--debug', action='store_true', default=False)
    gnl.add_argument('--libtype', '-l', default='cthfe', required=False, help='libtype')
    gnl.add_argument('--days', '-d', default='7', required=False, help='days')
    gnl.set_defaults(func='gnl')

    igr = subpar.add_parser('init_git_repo', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='Initialize(create) new (bare) git repo')
    igr.add_argument('--debug', action='store_true', default=False)
    igr.add_argument('--tmplpath', '-t', required=False, default='/nfs/site/disks/psg.git.001/git_templates/empty', help='fullpath to template git repo.')
    igr.add_argument('--repopath', '-r', required=True, help='fullpath to the new git repo.')
    igr.set_defaults(func='igr')

    apu = subpar.add_parser('add_power_users', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='add powerusers to a given project/cluster/stepping')
    apu.add_argument('--debug', action='store_true', default=False)
    apu.add_argument('--dryrun', '-n', action='store_true', default=False, help='if turn on, will skip the last stage (crt install)')
    apu.add_argument('--project', '-p', default='psg', help='Project (default: psg)')
    apu.add_argument('--cluster', '-c', default=None, help='cluster name')
    apu.add_argument('--stepping', '-s', default='a0', help='stepping (default: a0)')
    apu.add_argument('--userids', '-u', nargs='+', default=None, help='list of userid')
    apu.set_defaults(func='apu')

    ugc = subpar.add_parser('update_gk_config', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='update the given clusters/steppings into gk configs.')
    ugc.add_argument('--debug', action='store_true', default=False)
    ugc.add_argument('--dryrun', '-n', action='store_true', default=False, help='if turn on, will skip the last stage (crt install)')
    ugc.add_argument('--clusters', '-c', nargs='+', default=None, help='list of clusters')
    ugc.add_argument('--steppings', '-s', nargs='+', default=None, help='list of steppings')
    ugc.set_defaults(func='ugc')

    rrc = subpar.add_parser('reread_config', formatter_class=argparse.ArgumentDefaultsHelpFormatter, 
        help='run "turnin -rereadconfig" to load the latest gk config')
    rrc.add_argument("--dryrun", '-n', action='store_true', default=False, help='if turn in, will run -info instead of -rereadconfig')
    rrc.add_argument("--debug", action='store_true', default=False)
    rrc.set_defaults(func='rrc')

    dpc = subpar.add_parser('dump_config', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='run "turnin -dumpconfig" to report gk config. Use for checking if the newly updated config has taken effect.')
    dpc.add_argument("--debug", action='store_true', default=False)
    dpc.set_defaults(func='dpc')

    uet = subpar.add_parser('update_everything', formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help=textwrap.dedent('''Update everything. Here's what it will do:
        1)run 'get_new_libraries'
        2)run 'init_git_repo' 
        3)run 'update_gk_config'
        4)run 'reread_config'
        5)run 'dump_config'
        '''))
    uet.add_argument('--debug', action='store_true', default=False)
    uet.add_argument('--dryrun', '-n', action='store_true', default=False)
    uet.add_argument('--libtype', '-l', default='cthfe', required=False, help='libtype')
    uet.add_argument('--days', '-d', default='7', required=False, help='days')
    uet.add_argument('--tmplpath', '-t', required=False, default='/nfs/site/disks/psg.git.001/git_templates/empty', help='fullpath to template git repo.')
    uet.add_argument('--repopath', '-r', required=False, default='/nfs/site/disks/psg.git.001/git_repos', help='fullpath to the new git repo dir.')
    uet.set_defaults(func='uet')

    args = parser.parse_args()
    return args


def set_logger(arg):
    if arg.debug:
        fmt = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
        level = logging.DEBUG
    else:
        fmt = "%(levelname)s [%(asctime)s] - [%(module)s]: %(message)s"
        level = logging.INFO
    logging.basicConfig(format=fmt)
    LOGGER.setLevel(level)


if __name__ == '__main__':
    sys.exit(main())

