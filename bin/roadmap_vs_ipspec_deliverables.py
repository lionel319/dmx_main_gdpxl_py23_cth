#!/usr/bin/env python

# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/roadmap_vs_ipspec_deliverables.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""


"""

### std libraries
import os
import sys
import logging
import argparse

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace
from dmx.abnrlib.icm import ICManageCLI
import dmx.ecolib.ecosphere
from pprint import pprint
import traceback
import csv


### Global Varianbles
LOGGER = logging.getLogger()
DATA = {}
ERRORS = []

def main():

    args = _add_args()
    _setup_logger(args)
    icm_pmlog_enable(mode=False)

    LOGGER.info(args)

    icm = ICManageCLI()
    eco = dmx.ecolib.ecosphere.EcoSphere()

    for project in args.projects:
        LOGGER.info("Working on project:{} ...".format(project))

        DATA[project] = {}
        family = eco.get_family_for_icmproject(project)
       
        if 'all' in args.variants:
            variants = icm.get_variants(project)
        else:
            variants = args.variants

        for variant in variants:
            LOGGER.info("Working on variant:{} ...".format(variant))

            try:
                ip = family.get_ip(variant)
                DATA[project][variant] = {}
            except Exception as e:
                ERRORS.append(traceback.format_exc())
                continue

            try:

                for cellname in ip.get_cells_names(local=False, bom=args.bom):
                    LOGGER.info("Working on cell:{} ...".format(cellname))

                    DATA[project][variant][cellname] = {}
                    cell = ip.get_cell(cellname, local=False, bom=args.bom)
                    unneeded = cell.get_unneeded_deliverables(local=False, bom=args.bom)
                    DATA[project][variant][cellname]['unneeded_deliverables'] = unneeded
                    DATA[project][variant][cellname]['roadmap_deliverables'] = cell.get_all_deliverables(milestone=args.milestone)
                    DATA[project][variant][cellname]['missing_deliverables'] = []
                    DATA[project][variant][cellname]['delivered_deliverables'] = []
                    
                    ### The deliverables are objects. Make them into string
                    for key in ['unneeded_deliverables', 'roadmap_deliverables', 'missing_deliverables', 'delivered_deliverables']:
                        DATA[project][variant][cellname][key] = [x.name for x in DATA[project][variant][cellname][key]]
                    
                    DATA[project][variant][cellname]['missing_deliverables'] = list( set(DATA[project][variant][cellname]['roadmap_deliverables']) & set(DATA[project][variant][cellname]['unneeded_deliverables']) )
                    DATA[project][variant][cellname]['delivered_deliverables'] = list( set(DATA[project][variant][cellname]['roadmap_deliverables']) - set(DATA[project][variant][cellname]['unneeded_deliverables']) ) 
                
            except Exception as e:
                ERRORS.append(traceback.format_exc())
                #DATA[project][variant].pop(cellname, None)  # Remove the dict
                continue


    LOGGER.info('Dumping data file ...')
    dump_data()
    LOGGER.info('Dumping error file ...')
    dump_errors()


    LOGGER.info("===================================")
    LOGGER.info("DONE")
    LOGGER.info("===================================")
            

def dump_data(outfile="./rvid_data.csv"):
    with open(outfile, 'wb') as csvfile:
        w = csv.writer(csvfile)
        w.writerow(['project', 'variant', 'cellname', 'roadmap_deliverables', 'unneeded_deliverables', 'missing_deliverables', 'delivered_deliverables'])
        for project in DATA:
            for variant in DATA[project]:
                for cellname in DATA[project][variant]:
                    w.writerow([project, variant, cellname, 
                        ' '.join(DATA[project][variant][cellname]['roadmap_deliverables']),
                        ' '.join(DATA[project][variant][cellname]['unneeded_deliverables']),
                        ' '.join(DATA[project][variant][cellname]['missing_deliverables']),
                        ' '.join(DATA[project][variant][cellname]['delivered_deliverables'])
                    ])
    LOGGER.info("Successfully generated {}".format(outfile))


def dump_errors(outfile="./rvid_errors.txt"):
    with open(outfile, 'w') as f:
        for e in ERRORS:
            f.write(e)
            f.write("\n")
    LOGGER.info("Successfully generated {}".format(outfile))


def _add_args():
    ''' Parse the cmdline arguments '''
    parser = argparse.ArgumentParser()

    parser.add_argument('--projects', '-p', required=True, nargs='+', help='ICM projects.')
    parser.add_argument('--variants', '-v', required=True, nargs='+', help='ICM variants. ("all" for all the variants in the given projects)')
    parser.add_argument('--milestone', '-m', required=False, default='99', help='Milestone. (default: 99 (if unspecified))')
    parser.add_argument('--bom', '-b', required=False, default='dev', help='''The configuration that is used for extracting the ipspec data. 
        To specify the config of an ipspec, 'ipspec@config'.
        To specify the config of the ip, 'config'.
        (default: ipspec@dev)
        ''')
    parser.add_argument('--debug', required=False, default=False, action='store_true', help='Turn on debug mode.')

    args = parser.parse_args()
    return args


def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)


def icm_pmlog_enable(mode=True):
    '''
    | Enable logging of pm/icmp4 commands to icm_pmlog.txt.
    | if ``mode`` is set to ``True``, loggings are logged to ``icm_pmlog.txt``.
    | if ``mode`` is set to ``False``, loggings are set to ``/dev/null``.
    '''
    if mode:
        os.environ['ICM_PM_LOG_FILE'] = 'icm_pmlog.txt'
    else:
        os.environ['ICM_PM_LOG_FILE'] = os.devnull






if __name__ == "__main__":
    sys.exit(main())

