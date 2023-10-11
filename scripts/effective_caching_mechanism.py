#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/scripts/effective_caching_mechanism.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  abnr: Altera Build 'N Release
              command with subcommands for simplifying use of ICManage
              all subcommands are loaded from the abnrlib/plugins directory

Author: Anthony Galdes (ICManage)
        Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''

import sys
import os
import argparse
import logging
from pprint import pprint
import re
import grp
import pwd
import os


LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.abnrlib.icm
from dmx.utillib.utils import run_command

LOGGER = logging.getLogger()
DIGEST = {}     # CACHE dictionary for depot file digest
ICM = dmx.abnrlib.icm.ICManageCLI() # Make ICM global, to utilize its built-in caching mechanism


def main():
    args = parse_arguments()
    setup_logger(args)
    LOGGER.info(args)
    icm = dmx.abnrlib.icm.ICManageCLI()
    p = 'i10socfm'
    v = 'liotest1'
    l = 'ipspec'
    c = 'snap-cicq___liotestfc1___test1___2019-10-02-15_48_34'

    l = 'rdf'
    c = 'REL5.0FM6revA0--LionelTest__18ww425a'

    replace_srcdir_files_with_symlinks_from_dstdir(args)

    #replace_srcdir_files_with_symlinks_from_dstdir_by_pvlc(args, p, v, l, c)


def replace_srcdir_files_with_symlinks_from_dstdir(args):
    for root, dirs, files in os.walk(args.srcdir):
        print "root:{} , dirs:{}".format(root, dirs)
        if root.lstrip(srcdir).split('/') == len(4) and len[-1].startswith("snap/REL"):
            todolist.append()


def replace_srcdir_files_with_symlinks_from_dstdir_by_pvlc(args, project, variant, libtype, config):
    '''
    icm.get_dict_of_files() == {
        'i10socfm/liotest1/rdf:audit/audit.aib_ssm.rdf_bcmrbc.f': {
            'changelist': '13334427',
            'directory': '//depot/icm/proj/i10socfm/liotest1/rdf/dev/audit',
            'filename': 'audit.aib_ssm.rdf_bcmrbc.f',
            'library': 'dev',
            'libtype': 'rdf',
            'operation': 'add',
            'project': 'i10socfm',
            'release': '5',
            'type': 'text+l',
            'variant': 'liotest1',
            'version': '1'},
        ... ... ...
    }
    '''
    files = get_dict_of_icmfiles_by_pvlc(project, variant, libtype, config)


    for k,v in files.iteritems():
        pvldir = '/'.join([project, variant, libtype])
        relfilepath = re.sub('^{}:'.format(pvldir), '', k)
        srcfile = get_srcfile_from_pvlc(project, variant, libtype, config, args.srcdir, relfilepath)
        dstfile = get_dstfile_from_pvll(project, variant, libtype, v['library'], args.dstdir, relfilepath, v['version'])

        if not os.path.isfile(srcfile):
            LOGGER.warning('Skipping srcfile:{} as it does not exist.'.format(srcfile))
            LOGGER.warning('- dstfile:{}'.format(dstfile))
            continue

        if os.path.islink(srcfile):
            LOGGER.warning('Skipping srcfile:{} as it is symlink.'.format(srcfile))
            continue

        LOGGER.info("srcfile:{}\ndstfile:{}".format(srcfile, dstfile))
        project_group = get_project_group(args.srcdir, project)
        setup_dstfile_dir_if_not_exist(dstfile, args.dstdir, project_group)
        copy_srcfile_to_dstfile_if_dstfile_not_exist(srcfile, dstfile)
        setup_file_protection(dstfile, project_group)
        replace_srcfile_with_symlink_from_dstfile(srcfile, dstfile)
        setup_file_protection(srcfile, project_group)
        LOGGER.info("> Done.")


def replace_srcfile_with_symlink_from_dstfile(srcfile, dstfile):
    os.system("ln -fs {} {}".format(dstfile, srcfile))


def copy_srcfile_to_dstfile_if_dstfile_not_exist(srcfile, dstfile):
    if not os.path.isfile(dstfile):
        os.system("cp {} {}".format(srcfile, dstfile))


def setup_dstfile_dir_if_not_exist(dstfile, dstdir, group, mode='770'):
    '''
    dir needs to be created one level by one level, because
    - each level needs to be owned by project_group
    - each level needs to be chmod to 770
    '''
    rootdir = os.path.abspath(dstdir)
    dirpath = os.path.dirname(os.path.abspath(dstfile))
    os.system("mkdir -p {}".format(dirpath))

    while dirpath != rootdir:
        setup_file_protection(dirpath, group, mode)
        dirpath = os.path.dirname(dirpath)


def setup_file_protection(filepath, group, mode='770'):
    os.system("chgrp {} {}".format(group, filepath))
    os.system("chmod {} {}".format(mode, filepath))



def get_project_group(srcdir, project):
    s = os.stat(os.path.join(srcdir, project))
    gid = s.st_gid
    group = grp.getgrgid(gid)[0]
    return group


def copy_srcfile_to_dstfile(srcfile, dstfile):
    pass


def get_dstfile_from_pvll(project, variant, libtype, library, dstdir, relfilepath, revision):
    '''
    <dstdir>/<project>/<variant>/<libtype>/<library>/<relfilepath>.<rev>
    '''
    dstfile = os.path.join(os.path.abspath(dstdir), project, variant, libtype, library, relfilepath + '.{}'.format(revision))
    return dstfile


def get_srcfile_from_pvlc(project, variant, libtype, config, srcdir, relfilepath):
    '''
    <srcdir>/<project>/<variant>/<libtype>/<config>/<relfilepath>
    '''
    srcfile = os.path.join(os.path.abspath(srcdir), project, variant, libtype, config, relfilepath)
    return srcfile


def get_dict_of_icmfiles_by_pvlc(project, variant, libtype, config):
    '''
    icm.get_config(project, variant, config, libtype) == {
        'config': 'REL5.0FM6revA0--LionelTest__18ww425a',
        'description': 'testing [Local]',
        'library': 'dev',
        'libtype': 'rdf',
        'project': 'i10socfm',
        'release': '5',
        'variant': 'liotest1'}

    '''
    rel = ICM.get_config(project, variant, config, libtype)
    files = ICM.get_dict_of_files(project, variant, libtype, rel['release'], rel['library'])
    return files 




def get_files_digest_by_pvlc(project, variant, libtype, config):
    ret = {}
    icm = dmx.abnrlib.icm.ICManageCLI()
    rel = icm.get_config(project, variant, config, libtype)
    files = icm.get_dict_of_files(project, variant, libtype, rel['release'], rel['library'])
    for k,v in files.iteritems():
        depotpath = os.path.join(v['directory'], v['filename'])
        md5 = get_depot_file_digest(depotpath, v['version'])
        ret[depotpath] = md5
    return ret


def get_depot_file_digest(depotpath, revision):
    digest = get_depot_file_digest_from_cache_dict(depotpath, revision)
    if not digest:
        DIGEST[depotpath] = {}
        cmd = '_icmp4 -ztag -F "%rev% %digest%" verify {}'.format(depotpath)
        exitcode, stdout, stderr = run_command(cmd)
        for line in stdout.split('\n'):
            print '-{}-'.format(line)
            if not line or line.isspace():
                continue
            rev, md5 = line.split()
            DIGEST[depotpath][rev] = md5
        digest = DIGEST[depotpath][revision]
    return digest


def get_depot_file_digest_from_cache_dict(depotpath, revision):
    if depotpath in DIGEST:
        return DIGEST[depotpath][revision]
    else:
        return False


def setup_logger(args):
    if getattr(args, 'dryrun') and args.dryrun:
        levelname = '%(levelname)s-PREVIEW'     
    else:            
        levelname = '%(levelname)s' 

    if getattr(args, 'debug') and args.debug:
        logging.basicConfig(format="{} [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(levelname))
        LOGGER.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(format="{}: %(message)s".format(levelname))
        LOGGER.setLevel(logging.INFO)              


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='effective caching mechanism', 
        epilog=get_usage(), 
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--dryrun", default=False, required=False, action='store_true')
    parser.add_argument('--debug', default=False, required=False, action='store_true')
    parser.add_argument('--srcdir', required=True, metavar='(eg: /nfs/site/disks/fln_sion_1/cache)', help='folder where physical files are to be replaced with symlinks.')
    parser.add_argument('--dstdir', required=True, metavar='(eg: /nfs/site/disks/fln_sion_1/depot/icm/proj)', help='rootdir where final physical files will be deposited.')
    parser.add_argument('--iplist', required=False, default=None, nargs='+', help='Only work on the given list of IPs.')
    
    args = parser.parse_args()
    return args


def get_usage():
    return '''
========================================================
Example:

    > effective_caching_mechanism.py \\
        --srcdir /nfs/site/disks/fln_sion_1/cache \\
        --dstdir /nfs/site/disks/fln_sion_1/depot/icm/proj

    Assuming the following is the tree in --srcdir
    
    > tree /nfs/site/disks/fln_sion_1/cache
    i10socfm/liotest1/ipspec/
    |-- REL5.0FM6revA0__19ww111a
        |-- a.txt   (ver 1)
        |-- b.txt   (ver 6)
    |-- REL5.0FM6revA0__19ww222a
        |-- a.txt   (ver 2)
        |-- b.txt   (ver 6)


    
    This will be the resulting output:-
    
    > tree /nfs/site/disks/fln_sion_1/depot/icm/proj
    i10socfm/liotest1/ipspec
    |-- dev
        |-- a.txt.1
        |-- a.txt.2
        |-- b.txt.6
    
    > tree /nfs/site/disks/fln_sion_1/cache
    i10socfm/liotest1/ipspec/
    |-- REL5.0FM6revA0__19ww111a
        |-- a.txt <-- /nfs/site/disks/fln_sion_1/depot/icm/proj/i10socfm/liotest1/ipspec/a.txt.1
        |-- b.txt <-- /nfs/site/disks/fln_sion_1/depot/icm/proj/i10socfm/liotest1/ipspec/b.txt.6
    |-- REL5.0FM6revA0__19ww222a
        |-- a.txt <-- /nfs/site/disks/fln_sion_1/depot/icm/proj/i10socfm/liotest1/ipspec/a.txt.2
        |-- b.txt <-- /nfs/site/disks/fln_sion_1/depot/icm/proj/i10socfm/liotest1/ipspec/b.txt.6


    '''

if __name__ == '__main__':
    sys.exit(main())
