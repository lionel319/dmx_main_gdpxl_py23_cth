#!/usr/bin/env python

import sys
import os
import argparse
import dmx.abnrlib.icm
import dmx.abnrlib.config_factory
import dmx.utillib.diskutils
import logging
import json

logging.basicConfig(format="-%(levelname)s- [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s".format(logging.DEBUG), level=logging.DEBUG)

def run(path_match, days):
    logging.info("Calling function: RUN")
    paths=get_list_of_cached_immutable_pvlc(path_match)
    if len(paths)>0:
        #Get All Workspaces and scrub them to isolate EWP ones
        all_ewp_ws=get_all_ewp_workspaces()
        pvc_config_dic={}
        #Approach -2
        #Get All PVLC combinations used by current EWP WSs
        all_pvlcs_used=get_all_pvlc_from_ws(all_ewp_ws)
        with open('all_pvlcs_used.json', 'w') as json_file_w: 
            json.dump(all_pvlcs_used, json_file_w)

        #For testing load the existing all_pvlc_used dict
        # with open('all_pvlcs_used.json', 'r') as f_all_pvlcs_used: 
        #     all_pvlcs_used = json.load(f_all_pvlcs_used)

        #For every cache path, counters will be maintained in a file for all PVLCs.
        #In every run, the counters will be updated accordingly. (Counter transates to days unused)
        #If counter value is -1, it means PVLC is in-use currently. 
        #Any postive integer value in the counter translates to days unused, starting from 0. 
        for path in paths:
            try:
                logging.info("Update counter called for path %s", str(path))
                pvlc_stat=update_pvlc_stat(path, all_ewp_ws, pvc_config_dic, all_pvlcs_used, days)
                write_cm_commands(path, pvlc_stat, days)
            except Exception as e:
                logging.info("Exception happened for path %s . ERROR: %s", str(path), str(e))


def get_list_of_cached_immutable_pvlc(path_match):
    du = dmx.utillib.diskutils.DiskUtils(site='local')
    logging.info("Path_match: %s", path_match)
    diskdata = du.get_all_disks_data(path_match)
    paths=[]
    for x in diskdata:
        paths.append(x['StandardPath'])
        #self.get_cache_pvlcs(x['StandardPath'])
    logging.info ("CACHED PATHS: %d", len(paths))
    logging.info("ALL CACHED PATHS: %s", str(paths))

    return paths

def get_all_ewp_workspaces():
    #Get All workspace
    icmcli = dmx.abnrlib.icm.ICManageCLI()
    all_ws = icmcli.get_workspaces()
    
    #Comment it out in cron for EWP scrubbing to be done
    #return all_ws

    #Take out all Non EWP workspaces
    logging.info("Started: Isolate EWP workspaces")
    all_ewp_ws=[]
    for ws in all_ws:
        try:
            if is_workspace_ewp_workspace(ws['workspace']):
                all_ewp_ws.append(ws)
        except Exception as e:
            logging.info("Exception in determing EWP status of Workspace %s, Error: %s", ws['workspace'], str(e))
            all_ewp_ws.append(ws)
    with open('all_ewp_workspaces.json', 'w') as json_file_w: 
            json.dump(all_ewp_ws, json_file_w)
    logging.info("Total EWP Workspaces: %d", len(all_ewp_ws))
    logging.info("Finished: Isolate EWP workspaces")
    return all_ewp_ws

def get_cache_pvlcs(path):
    cache_path=path + "/cache/"
    pvlc_dict={}
    pvlc_list=[]
    proj_dirs=[name for name in os.listdir(cache_path) if (os.path.isdir(os.path.join(cache_path, name)) and not name.startswith('.'))]
    for p in proj_dirs:
        pvlc_dict[p]={}
        proj_path=cache_path+p+"/"
        var_dirs=[name for name in os.listdir(proj_path) if (os.path.isdir(os.path.join(proj_path, name)) and not name.startswith('.'))]
        for v in var_dirs:
            pvlc_dict[p][v]={}
            var_path=proj_path+v+"/"
            lib_dirs=[name for name in os.listdir(var_path) if (os.path.isdir(os.path.join(var_path, name)) and not name.startswith('.'))]
            for l in lib_dirs:
                pvlc_dict[p][v][l]={}
                lib_path=var_path+l+"/"
                conf_dirs=[name for name in os.listdir(lib_path) if (os.path.isdir(os.path.join(lib_path, name)) and not name.startswith('.') and '.TEMP' not in name)]
                for c in conf_dirs:
                    pvlc_dict[p][v][l][c]=-2
                    pvlc_list.append([p,v,l,c])
    logging.info("Total number of PVLCs: %d", len(pvlc_list))
    #logging.info("Directory Structure: %s", str(pvlc_dict))
    return (pvlc_dict, pvlc_list)

def get_pvc_dict(pvlc_dict):
    pvc_dict={}
    for p in pvlc_dict:
        pvc_dict[p]={}
        for v in pvlc_dict[p]:
            pvc_dict[p][v]={}
            for l in pvlc_dict[p][v]:
                for c in pvlc_dict[p][v][l]:
                    if c not in pvc_dict[p][v]:
                        pvc_dict[p][v][c]={}
    return pvc_dict

def is_workspace_ewp_workspace(ws):
    #logging.info("Calling function: is_workspace_ewp_workspace")
    cli = dmx.abnrlib.icm.ICManageCLI()
    wsprop = cli.get_workspace_properties(ws)
    if 'PopulationDate' in wsprop:
        return True
    return False

def update_pvlc_stat(path, all_ewp_ws, pvc_config_dic, all_pvlcs_used, days):
    #Get previous counter statistics
    s=path.replace("/", "-")+"-data.json"
    filename=s[1:]
    try:
        with open(filename, 'r') as json_file: 
            pvlc_stat = json.load(json_file)
    except Exception as e:
        logging.info("Exception: %s", str(e))
        pvlc_stat={}

    #Overwrite the rm cmds file
    s=path.replace("/", "-")+"-RM-CMDs.txt"
    cmd_filename=s[1:]
    outF=open(cmd_filename, "w")
    cmd= "RM Commands for path: " + path
    outF.write(cmd)
    outF.close()

    #Get All cached PVLC dirs
    (pvlc_dict, pvlc_list)=get_cache_pvlcs(path)

    pvlc_count = 0
    pvlc_total=len(pvlc_list)

    #Check current cached PVLC one by one if in use, if not increase by 1 
    for p in pvlc_dict:
        for v in pvlc_dict[p]:
            for l in pvlc_dict[p][v]:
                for c in pvlc_dict[p][v][l]:
                    pvlc_count+=1
                    logging.info("PVLC Count: %d / %d", pvlc_count, pvlc_total)
                    #Approach-1
                    #if is_pvlc_used(p,v,l,c,all_ewp_ws,pvc_config_dic):

                    #Approach-2
                    if is_pvlc_in_used_list(p,v,l,c,all_pvlcs_used):
                        pvlc_dict[p][v][l][c]=-1
                    else:
                        found=0
                        if p in pvlc_stat:
                            if v in pvlc_stat[p]:
                                if l in pvlc_stat[p][v]:
                                    if c in pvlc_stat[p][v][l]:
                                        found =1
                                        if pvlc_stat[p][v][l][c] == -2:
                                            pvlc_dict[p][v][l][c]=0
                                        else:
                                            pvlc_dict[p][v][l][c]=pvlc_stat[p][v][l][c]+1
                        if found==0:
                            pvlc_dict[p][v][l][c]=0

                        persist_rm_cmd(path, cmd_filename, p, v, l, c, pvlc_dict[p][v][l][c], days)

    with open(filename, 'w') as json_file_w: 
        json.dump(pvlc_dict, json_file_w)
    logging.info ("Finished updating cache counters for path %s in file: %s", path, filename)
    return pvlc_dict


def is_pvlc_in_used_list(p,v,l,c,all_pvlcs_used):
    status=0
    if p in all_pvlcs_used:
        if v in all_pvlcs_used[p]:
            if l in all_pvlcs_used[p][v]:
                if c in all_pvlcs_used[p][v][l]:
                    status=1
    return status

def write_cm_commands(path, pvlc_dict, days=14):
    s=path.replace("/", "-")+"-RM-CMDs.txt"
    filename=s[1:]
    outF=open(filename, "w")
    logging.info("Finding cache files to be deleted for path %s and persisting in file: %s", path, filename)
    rm_prefix="rm -rf "
    all_lines=[]
    for p in pvlc_dict:
        for v in pvlc_dict[p]:
            for l in pvlc_dict[p][v]:
                for c in pvlc_dict[p][v][l]:
                    if pvlc_dict[p][v][l][c] >= int(days):
                        cmd= rm_prefix + path + "/cache/" + p + "/" + v  +"/"+ l +"/" + c + " \n"
                        all_lines.append(cmd)
    outF.writelines(all_lines)
    logging.info("Finished Garbage collection for path %s", path)

def persist_rm_cmd(path, cmd_filename, p, v, l, c, stat, days=14):
    if int(stat)>=int(days):
        outF=open(cmd_filename, "a")
        cmd= "rm -rf " + path + "/cache/" + p + "/" + v  +"/"+ l +"/" + c + " \n"
        outF.write(cmd)
        outF.close()

def get_all_pvlc_from_ws(all_ewp_ws):
    logging.info("Calling function get_all_pvlc_from_ws")
    #Dictionary to store Config tree objects for particular P, V, C
    #Dictionary example={p1:{v1:{c1:<cf_object>}}}
    pvc_config_dic={}

    #Dictionary to store all PVLCS used from EWP Workspaces.
    #Dictionary example={p1:{v1:{l1:[c1,c2]}}}
    all_pvlcs_used={}

    total=len(all_ewp_ws)
    count=0
    for ws in all_ewp_ws:
        count+=1
        logging.info ("WS Count: %d / %d", count, total)

        #If libtype is present no need to get/create Config Tree
        if ws['libtype']:
            logging.info("Workspace: project: %s, variant: %s, libtype: %s, config: %s",ws['project'],ws['variant'],ws['libtype'],ws['config'])
            
            #If P, V, L, C doesn't already exist in the dictionary add it, this way there is only one entry of unique P,V,L,C
            if ws['project'] not in all_pvlcs_used:
                all_pvlcs_used[ws['project']]={}
                    
            if ws['variant'] not in all_pvlcs_used[ws['project']]:
                all_pvlcs_used[ws['project']][ws['variant']]={}

            if ws['libtype'] not in all_pvlcs_used[ws['project']][ws['variant']]:
                all_pvlcs_used[ws['project']][ws['variant']][ws['libtype']]=[]

            if ws['config'] not in all_pvlcs_used[ws['project']][ws['variant']]:
                all_pvlcs_used[ws['project']][ws['variant']][ws['libtype']].append(ws['config'])

        else:
            logging.info("Workspace: project: %s, variant: %s, config: %s",ws['project'],ws['variant'],ws['config'])
            try:
                # Check if Config tree is already fetched. If fetched, that means all PVLCs from that CF has already been added 
                # to the all_pvlc_used dictionary, then do nothing.
                cf = pvc_config_dic[ws['project']][ws['variant']][ws['config']]
                logging.info("Config already added to All PVLCs")
            except:
                #exception will happen if P, V, C not present in CF dictionary, that means create the config Tree and 
                #add all the participating (P,V,L,C)'s to the all_pvlcs_used dictionary.
                try:
                    cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(ws['project'], ws['variant'], ws['config'])

                    #Ading all PVLCs from Config tree to our All PVLC dictionary
                    for subcf in cf.flatten_tree():
                        if subcf.is_simple() and not subcf.is_mutable():
                            if subcf.project not in all_pvlcs_used:
                                all_pvlcs_used[subcf.project]={}
                            if subcf.variant not in all_pvlcs_used[subcf.project]:
                                        all_pvlcs_used[subcf.project][subcf.variant]={}
                            if subcf.libtype not in all_pvlcs_used[subcf.project][subcf.variant]:
                                        all_pvlcs_used[subcf.project][subcf.variant][subcf.libtype]=[]
                            if subcf.config not in all_pvlcs_used[subcf.project][subcf.variant]:
                                       all_pvlcs_used[subcf.project][subcf.variant][subcf.libtype].append(subcf.config)

                    #Storing CF in dictionary for further referral later in loops
                    if ws['project'] not in pvc_config_dic:
                        pvc_config_dic[ws['project']]={}
                    
                    if ws['variant'] not in pvc_config_dic[ws['project']]:
                        pvc_config_dic[ws['project']][ws['variant']]={}

                    if ws['config'] not in pvc_config_dic[ws['project']][ws['variant']]:
                       pvc_config_dic[ws['project']][ws['variant']][ws['config']]=cf

                except Exception as e:
                    logging.info("Exception at create_from_icm PVLC: %s : %s : %s \n ::: Exception: %s", ws['project'], ws['variant'], ws['config'], str(e))
    return all_pvlcs_used

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Garbage Collection on EWP')
    parser.add_argument('-p', '--path_match', metavar='path_match', action='store', help='String to match for cache paths')
    parser.add_argument('-d', '--days', metavar='days', action='store', help='Days to retain a specific PVLC dir in a cached path')
    args=parser.parse_args()
    logging.info("Garbage Collection on EWP")
    try:
        run(args.path_match, args.days)
    except:
        e=sys.exc_info()[0]
        logging.info(e)
        sys.exit(1)
    sys.exit(0)
