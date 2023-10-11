#!/usr/bin/env python

## @package port_swweb_data_to_json
## @author Lionel Tan Yoke - Liang
## @brief This script reads in roadmap and checker data from the sw-web's database and generates the CloseData for EcoSphere.
## 
## This script reads in roadmap and checker data from the sw-web's database, and generates 4 json files:-
##
##    - milestones.json
##    - products.json
##    - deliverable_by_ip_type.json
##    - checkers.json
##
##    Example of generating the json database files for Nadder:-
## @code
##        $prog_swweb_data_to_json.py --project i14socnd --family ND
## @endcode
##
##    Example of generating the json database file for Falcon:-
## @code
##        $prog_swweb_data_to_json.py --project i10socfm --family FM
## @endcode
##
##    Example of generating the json database file for Crete3:-
## @code
##        $prog_swweb_data_to_json.py --project i14socnd --family CR 
## @endcode

import os
import sys
from web_api import WebAPI
from pprint import pprint
import argparse
import json
from altera.decorators import memoized

## Main Function
def main():
    parser = argparse.ArgumentParser(description = """
        Example of generating the json database files for Nadder:-
            $prog_swweb_data_to_json.py --project i14socnd --family ND

        Example of generating the json database file for Falcon:-
            $prog_swweb_data_to_json.py --project i10socfm --family FM
        
        Example of generating the json database file for Crete3:-
            $prog_swweb_data_to_json.py --project i14socnd --family CR
    """, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="example: i10socfm, i14socnd, ...")
    parser.add_argument("--family", required=True, help="First 2 characters of the project, eg: ND, CR, FM, ...")
    parser.add_argument("--include_type_check", required=False, default=False, action='store_true', help="Turning on this option will include type_checks in checkers.csv. Default: No.")
    args = parser.parse_args()

    print "Generating roadmap.json and roadmap_and_revisions_by_product.json ..."
    gen_roadmap_json(args)

    print "Generating deliverables_by_ip_type.json ..."
    gen_deliverables_by_ip_type_json(args)
    
    print "Generating deliverables_and_checkers_by_milestone.json ..."
    gen_deliverables_and_checkers_by_milestone_json(args)

    print "Generating checkers.json ..."
    gen_checkers_json(args)



## Generates roadmap.json 
##   
## Output file (@c roadmap_and_revisions_by_product.json) example:-
## @code
##    {
##        "ND1"           : {
##            "revisions"     : ["A"]
##            "milestones"    : "M2"
##        },
##        "ND5"           : {
##            "revisions"     : ["A", "A0"]
##            "milestones"    : "M1"
##        }
##    }
##
## Output file (@c roadmap.json) example:-
## @code
##    {
##        "M1"           : ["0.5", "1.0", ... "5.0"],
##        "M2"           : ["1.0", "2.0", ... "5.0"],
##    }
##
##
## @endcode
def gen_roadmap_json(args):
    ret = {}
    threads = get_threads(args.project, args.family)
    milestones = get_milestones(args.project, args.family)

    ### Generate roadmap.json
    with open("roadmap.json", "w") as f:
        json.dump({"R1":milestones}, f, indent=4, sort_keys=True)


    for thread in threads:
        pd, rev = thread.split('rev')
        if pd in ret:
            if rev not in ret[pd]['revisions']:
                ret[pd]['revisions'].append(rev)
        else:
            ret[pd] = {"revisions": [rev], "milestones":"R1"}
    with open("roadmap_and_revisions_by_product.json", "w") as f:
        json.dump(ret, f, indent=4, sort_keys=True)
    return ret

## Generates checkers.json
## 
## Output file (@c checkers.json) example:-
## @code
##     [
##         {
##             "Audit Ready": 1,
##             "Check Name": "r2g2",
##             "Deliverable": "sta",
##             "Documentation": "",
##             "Filelist": 0,
##             "Flow": "sta",
##             "SubFlow": "",
##             "Type": "c",
##             "Unix Userid": "kychng",
##         },
##         {
##             "Audit Ready": 1,
##             "Check Name": "AUTO",
##             "Deliverable": "ipxact",
##             "Documentation": "",
##             "Filelist": 0,
##             "Flow": "ipxact",
##             "SubFlow": "type",
##             "Type": "t",
##             "Unix Userid": "kmartine",
##         },
##         ...   ...   ...
##     ]
## @endcode
def gen_checkers_json(args):

    w = WebAPI()
    variant_types = get_variant_types(args.project)
    thread = get_threads(args.project, args.family)[0]
    milestones = get_milestones(args.project, args.family)
    ret = {}
    data = {}
    for vt in variant_types:
        for ms in milestones:
            if ms == '99':
                continue


            # test = (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone)
            for test in get_required_tests(args.project, ms, thread, vt):
                if test in data:
                    if ms not in data[test]:
                        data[test].append(ms)
                else:
                    data[test] = [ms]
    
    for test in data:

        ### Only add if SubFlow is not "type"
        ### UPDATE 19 sep 2016. Adds type_check too.
        ### append check if only 
        ### - (It is not a type_check) OR (it is a type_check, and the --include_type_check option is turned on)
        if (test[2] != 'type') or (test[2] == 'type' and args.include_type_check == True):
            
            flow = test[1].strip()
            subflow = test[2].strip()
            if subflow:
                key = "{}_{}".format(flow, subflow)
            else:
                key = flow
            ret[key] = {
                "Audit Ready": 1,
                "Check Name": test[4],
                "Deliverable": test[0],
                "Documentation": "",
                "Filelist": 0,
                "Flow": test[1],
                "SubFlow": test[2],
                "Type": test[3],
                "Unix Userid": test[6].split('@')[0],
                #"milestones": data[test],
            }

            '''
            ret.append({
                "Audit Ready": 1,
                "Check Name": test[4],
                "Deliverable": test[0],
                "Documentation": "",
                "Filelist": 0,
                "Flow": test[1],
                "SubFlow": test[2],
                "Type": test[3],
                "Unix Userid": test[6].split('@')[0],
                #"milestones": data[test],
            })
            '''
    
    with open("checkers.json", "w") as f:
        json.dump(ret, f, indent=4, sort_keys=True)
    return ret

## Generates deliverables_by_ip_type.json
## 
## Output file (@c deliverables_by_ip_type.json) example:-
## @code
##     {
##         "asic": 
##             [
##                 "BCMRBC",
##                 "CDC",
##                 "CIRCUITSIM",
##                 "COMPLIB",
##                 "IPPWRMOD",
##                 "IPSPEC",
##                 "IPXACT",
##                 "LINT",
##                 "RDF",
##                 "RTL",
##                 "RTLCOMPCHK",
##                 "SCHMISC",
##                 "SYN",
##                 "TIMEMOD"
##             ],
##                 ...   ...   ...
## @endcode
def gen_deliverables_by_ip_type_json(args):

    w = WebAPI()
    variant_types = get_variant_types(args.project)
    thread = get_threads(args.project, args.family)[0]
    milestones = get_milestones(args.project, args.family)
    ret = {}
    new = {}
    for vt in variant_types:
        ret[vt] = {}
        for ms in ['99']:
            ret[vt][ms] = sorted([a.upper() for a in get_required_libtypes(args.project, ms, thread, vt)])
            new[vt] = sorted([a.upper() for a in get_required_libtypes(args.project, ms, thread, vt)])
    with open("deliverables_by_ip_type.json", "w") as f:
        json.dump(new, f, indent=4, sort_keys=True)
    return ret


def gen_deliverables_and_checkers_by_milestone_json(args):

    w = WebAPI()
    variant_types = get_variant_types(args.project)
    thread = get_threads(args.project, args.family)[0]
    milestones = get_milestones(args.project, args.family)
    
    ret = {}
    for ms in milestones:
        ret[ms] = {"deliverables":[], "checkers":[]}

    
    for vt in variant_types:
        for ms in milestones:
            ret[ms]['deliverables'] += [a.upper() for a in get_required_libtypes(args.project, ms, thread, vt)]
    
            
            # test = (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone)
            for test in get_required_tests(args.project, ms, thread, vt):
                if (test[2] != 'type') or (test[2] == 'type' and args.include_type_check == True):
                    flow = test[1].strip()
                    subflow = test[2].strip()
                    if subflow:
                        key = "{}_{}".format(flow, subflow)
                    else:
                        key = flow
                    ret[ms]['checkers'].append(key)
    


    ### remove duplicated entries and sort arrays
    for ms in ret:
        for cat in ['deliverables', 'checkers']:
            ret[ms][cat] = sorted(set(ret[ms][cat]))

    with open("deliverables_and_checkers_by_milestone.json", "w") as f:
        json.dump(ret, f, indent=4, sort_keys=True)
    return ret



@memoized
def get_required_tests(project, ms, thread, vt):
    w = WebAPI()
    return w.get_required_tests(project, ms, thread, vt)


@memoized
def get_required_libtypes(project, ms, thread, vt):
    w = WebAPI()
    return w.get_required_libtypes(project, ms, thread, vt)


## Returns the schedule_items for a given project
##
## @code
## ret = get_valid_schedule_items('i14socnd')
## ret == [('ND5revA', '5.0', ('ND5revA', '4.5'), ...]
## @endcode
@memoized
def get_valid_schedule_items(project):
    w = WebAPI()
    return w.get_valid_schedule_items(project)

## Returns the list of available milestones for a given project and family. 
##
## @code 
## ret = get_milestones('i14socnd', 'CR')
## ret == ['1.0', '3.0', '5.0']
## @endcode
@memoized
def get_milestones(project, family):
    w = WebAPI()
    ret = []
    for milestone, thread in get_valid_schedule_items(project):
        if thread.startswith(family) and milestone not in ret:
            ret.append(milestone)
    ret = sorted(ret)
    return ret

## Returns a list of threads for a given family
##
## @code
## ret = get_threads('i14socnd', 'ND')
## ret == ['ND4revA', 'ND5revA', ...]
## @endcode
@memoized
def get_threads(project, family):
    w = WebAPI()
    ret = []
    for milestone, thread in get_valid_schedule_items(project):
        if thread.startswith(family) and thread not in ret:
            ret.append(thread)
    ret = sorted(ret)
    return ret

## Returns a list of variant_Types for a given project
##
## @code
## ret = get_variant_types('i14socnd')
## ret == ['asic', 'custom', ...]
## @endcode
@memoized
def get_variant_types(project):
    w = WebAPI()
    return w.get_variant_type_definitions(project).keys()


if __name__ == '__main__':
    main()

