#!/usr/bin/env python
# coding: utf-8
import os
import sys, getopt
from subprocess import Popen, PIPE, check_output
import re
import random
import getpass
import time
import argparse
import glob
import dmx.abnrlib.icm
import dmx.utillib.utils
from dmx.abnrlib.flows.updatevariant import UpdateVariant
import logging

class Pre_Check_Input_For_Errors():

    def __init__(self, some_src_prj, some_dst_prj, some_src_bom, some_dst_bom, some_source_ip_name, some_dest_ip_name):
        self.source_proj = some_src_prj
        self.dest_proj = some_dst_prj
        self.source_bom = some_src_bom
        self.destination_bom = some_dst_bom
        self.IP_source_name = some_source_ip_name
        self.IP_dest_name = some_dest_ip_name
        self.icm_client = dmx.abnrlib.icm.ICManageCLI()
        self.logger = logging.getLogger(__name__)

    def error_handling(self):

        if not self.icm_client.config_exists(self.source_proj, self.IP_source_name, self.source_bom):
            self.logger.error("\n" + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " does not exist!!")
            sys.exit(1)


        if not self.icm_client.project_exists(self.dest_proj):
            self.logger.error("\nThe destination project " + self.dest_proj + " does not exist!!Can not continue")
            sys.exit(1)


        if (self.source_proj == self.dest_proj) and (self.IP_source_name == self.IP_dest_name) and (self.source_bom == self.destination_bom):
            self.logger.error("\nUsing the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed")
            sys.exit(1)


        if (self.source_proj == self.dest_proj) and (self.IP_source_name == self.IP_dest_name) and (self.source_bom != self.destination_bom):

            if self.icm_client.config_exists(self.dest_proj, self.IP_dest_name, self.destination_bom):
                self.logger.error("\nUsing the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed as " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " already exists\nPlease use dmx overlay for this")

            else:
                self.logger.error("\nUsing the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed as " + self.dest_proj + "/" + self.IP_dest_name + " already exists\nPlease use dmx derive bom for this")

            sys.exit(1)


        if (self.source_proj == self.dest_proj) and (self.IP_source_name != self.IP_dest_name):
   
            if self.icm_client.variant_exists(self.dest_proj, self.IP_dest_name):

                if self.icm_client.config_exists(self.dest_proj, self.IP_dest_name, self.destination_bom):
                    self.logger.error("\nUsing the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed as " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " already exists\nPlease use dmx overlay for this")

                else:
                    self.logger.error("\nUsing the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed as " + self.dest_proj + "/" + self.IP_dest_name + " already exists\nPlease use dmx derive bom for this")
                
                sys.exit(1)



        if (self.source_proj != self.dest_proj):

            if self.icm_client.variant_exists(self.dest_proj, self.IP_dest_name):

                if self.icm_client.config_exists(self.dest_proj, self.IP_dest_name, self.destination_bom):
                    self.logger.error("Using the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed as " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " already exists\nPlease use dmx overlay for this")

                else:
                    self.logger.error("\nUsing the proliferate to run " + self.source_proj + "/" + self.IP_source_name + "@" + self.source_bom + " ---> " + self.dest_proj + "/" + self.IP_dest_name + "@" + self.destination_bom + " is not allowed as " + self.dest_proj + "/" + self.IP_dest_name + " already exists\nPlease use dmx overlay or derive bom for this")

                sys.exit(1)



class IP_Library_Importation():

    def __init__(self, src_prj, dst_prj, src_bom, dst_bom, ip, userid, dest_ip):
        self.dst_res =""
        self.src_prj = src_prj
        self.dst_prj = dst_prj
        self.src_bom = src_bom
        self.dst_bom = dst_bom
        self.ip = ip
        self.desti_ip = dest_ip
        self.preview = True
        self.userid = userid
        self.cli = dmx.abnrlib.icm.ICManageCLI()
        self.update_variant = "" 
        self.source_ip_with_libtype_details = ""

        if not self.dst_bom:
            self.dst_bom = self.src_bom

        if not self.userid:
            self.userid = os.getenv('USER')

        if not self.desti_ip:
            self.desti_ip = self.ip 
    
        if not self.cli.does_icmp4_user_exist(self.userid) and not re.search("psginfraadm", self.userid):
            self.logger.info("\nThe user id " + userid + " does not exist\nUsing the current user")
            self.userid = os.getenv('USER')

        if re.search("psginfraadm", self.userid):
            self.logger.error("\nThe user id can not be 'psginfraadm'")
            sys.exit(1)


    def get_Arc_resource(self):
        get_arc_resource_command = "arc job-info resources"
        arc_resource_of_user = check_output(get_arc_resource_command, shell=True)
        return arc_resource_of_user.rstrip("\n")
 


    def check_if_IP_to_be_migrated_already_exists_in_new_proj(self):
        return self.cli.variant_exists(self.dst_prj, self.desti_ip)



    def get_IP_type(self):
        ip_type_cmd ="pm propval -n \"Variant Type\" -l " + self.src_prj + " " + self.ip
        ip_type_output=check_output(ip_type_cmd, shell=True)
        results=ip_type_output.split()

        valRegex=re.match(r"Value=\"(\S+)\"",results[4])
        ip_type=valRegex.group(1)

        return ip_type



    def ip_create(self):
        ip_lookup_in_dest_project = self.check_if_IP_to_be_migrated_already_exists_in_new_proj()

        if not ip_lookup_in_dest_project:                                # create a new ip if it never existed 
            ip_type_gotten = self.get_IP_type()
            pm_IP_create = self.cli.add_variant(self.dst_prj, self.desti_ip)


    def get_config_details(self):
        get_dest_ip_and_its_libtype_details_command = "pm variant -l " + self.dst_prj + " " + self.desti_ip
        dest_ip_and_its_libtype_details = check_output(get_dest_ip_and_its_libtype_details_command, shell=True)

        return self.source_ip_with_libtype_details



    def ip_update_type(self):
        ip_lookup_in_dest_project = self.check_if_IP_to_be_migrated_already_exists_in_new_proj()

        if ip_lookup_in_dest_project:                            #update an ip type only if it exists
            ip_type_gotten_again = self.get_IP_type()
            update_variant_object = UpdateVariant(self.dst_prj, self.desti_ip, ip_type_gotten_again, False)
            update_variant_object.run()



    def update_ip_owner_ship(self):
        ip_lookup_in_dest_project = self.check_if_IP_to_be_migrated_already_exists_in_new_proj()

        if not ip_lookup_in_dest_project:                           #update an ip owner only if it exists
            ip_owner_update_cmd = 'pm propval -v "' + self.userid + '" -o Owner ' + self.dst_prj + " " + self.desti_ip
            ip_owner_update_cmd_id = check_output(ip_owner_update_cmd, shell=True)



    def get_library(self, source_proj, source_ip, source_bom):
        get_library_cmd = "pm configuration -l " + source_proj + " " + source_ip + " -n " + source_bom + ' | grep ' + source_ip
        get_library_cmd_output = check_output(get_library_cmd, shell=True)

        self.source_ip_with_libtype_details = get_library_cmd_output

        return get_library_cmd_output



    def get_actualLibrary_and_libtype_or_deliverable(self, a_string_in):
        important_details = re.split("\s+", a_string_in)
        library = important_details[3]
        deliverable = important_details[2]

        library = library.replace("Library=","")
        library = library.replace('"', '')

        deliverable = deliverable.replace("LibType=","")
        deliverable = deliverable.replace('"', '')

        return (library, deliverable)



    def get_relevant_time_string(self):
        named_tuple = time.localtime() # get struct_time
        time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)

        time_string_split = time_string.split(", ")
        time_string_first_part_split  = time_string_split[0].split("/")

        reconstructed_time_string_first_part = time_string_first_part_split[2] + "/" + time_string_first_part_split[0] + "/" + time_string_first_part_split[1]

        final_time_string = reconstructed_time_string_first_part + " " + time_string_split[1]
        return final_time_string



    def get_string_to_compare_for_source_file(self, some_source_project, some_source_ip, some_source_bom, some_lib_type):
        get_key_details_for_source_cmd = "pm configuration -l " + some_source_project + " " + some_source_ip + " -n " + some_source_bom + " | grep " + some_lib_type + '\\" | grep  ' + some_source_ip

        try:
            get_key_details_for_source_cmd = "pm configuration -l " + some_source_project + " " + some_source_ip + " -n " + some_source_bom + " | grep " + some_lib_type + '\\" | grep  ' + some_source_ip
            key_details = check_output(get_key_details_for_source_cmd, shell=True)

            if key_details == "":
                self.logger.debug("skipping this deliverable " + some_lib_type + " for comparison")
                return None

            icm_details  = key_details.split()

            valRegex=re.match(r"Library=\"(\S+)\"", icm_details[3])
            Library = valRegex.group(1)

            return_string = ""

            if re.search ("REL", some_source_bom):
                return_string += "//depot/icm/proj/" + some_source_project + "/icmrel/" + some_source_ip + "/" + some_lib_type + "/" + Library + "/..."
            else:
                return_string += "//depot/icm/proj/" + some_source_project + "/" + some_source_ip + "/" + some_lib_type + "/" + some_source_bom + "/..."

            return return_string

        except Exception as e:
                exception_string = str(e)
                self.logger.debug(exception_string)



    def import_library(self, lib_type_in, proj_source_in, First_IP_in, library_in, proj_dest, dest_bom_in, second_IP_in = ""):
        if second_IP_in == "":
            second_IP_in = First_IP_in 

        ip_lookup_in_dest_project = self.check_if_IP_to_be_migrated_already_exists_in_new_proj()

        if re.search (str('\"' + lib_type_in + '\"'), self.source_ip_with_libtype_details):                 #create new lib-type if it never existed
            libtype_create = "pm variant -f " + proj_dest + " " + lib_type_in + " " + second_IP_in
            libtype_create_output = check_output(libtype_create, shell=True)

        if re.search (str('\"' + lib_type_in + '\"'), self.source_ip_with_libtype_details):
            importation_cmd = "pm import -U -d ' Library importation by " + self.userid + " ' -e " + lib_type_in + " -p " +  proj_source_in + " " + First_IP_in + " '" + library_in +  "'"  + " integrate " + proj_dest + " " + second_IP_in + " " + lib_type_in + " " + dest_bom_in + " -w '@$variant/" + lib_type_in + "'"
            try:
                importation_cmd_output = check_output(importation_cmd, shell=True)
                
            except:
               self.logger.debug("\nlibrary for " + lib_type_in + " in " + second_IP_in + " already exists\n")

            config_create_for_libtype = "pm configuration -t " + lib_type_in + " " + proj_dest + " " + second_IP_in + " " +  dest_bom_in + " '" + dest_bom_in + "'"
            os.system(config_create_for_libtype)
            magic_command = "pm configuration -n " + dest_bom_in + " -t " + lib_type_in + " -l  " + proj_dest + " " + second_IP_in + " -D '+MaGiC+' -H"
            magic_output = check_output(magic_command, shell=True)

            os.system("pm propval -v " + self.userid + " -C Owner " + proj_dest + " " + second_IP_in + " " +  lib_type_in + " " + dest_bom_in)

            config_creation_time = self.get_relevant_time_string()
            os.system("pm propval -v '" + config_creation_time + "' -C 'Created at' " + proj_dest + " " + second_IP_in + " " + lib_type_in + " " + dest_bom_in)

            simple_config_string = "'" + dest_bom_in + "@" + lib_type_in + "'"

            ##PROPER FILE VERIFICATION
            source_file_path_compare = self.get_string_to_compare_for_source_file(proj_source_in, First_IP_in, self.src_bom, lib_type_in)

            if source_file_path_compare:
                dest_file_path_compare = "//depot/icm/proj/" + proj_dest + "/" + second_IP_in + "/" + lib_type_in + "/" + dest_bom_in + "/..."
                file_verify_result = ""

                try:
                    file_verify_cmd = "icmp4 diff2 -q " + source_file_path_compare + " " + dest_file_path_compare + " | grep -v types "
                    self.logger.debug(file_verify_cmd)
                    file_verify_result = check_output(file_verify_cmd, shell=True)

                except:
                    file_verify_result = ""

                if re.search("no differing files", file_verify_result):
                    self.logger.info("deliverable " + lib_type_in + " between " + First_IP_in + " and " + second_IP_in + " has no missing or mismatched files\n")

                else:
                    self.logger.debug(file_verify_result)

            else:
                self.logger.debug("This deliverable " + lib_type_in + " not being verified")
       
            return simple_config_string    


    def process_library_command_output(self, a_library_output):
        self.dst_res = self.get_Arc_resource()
        self.ip_create()

        array_of_lines = a_library_output.split("\n")
 
        simple_configs = "" 

        for each_line in array_of_lines:
            simple_configs += " "
            if re.search('Library="', each_line):
                my_library, my_deliverable = self.get_actualLibrary_and_libtype_or_deliverable(each_line)

                a_config_object = self.import_library(my_deliverable, self.src_prj, self.ip, my_library, self.dst_prj, self.dst_bom, self.desti_ip)
                simple_configs +=  str(a_config_object) +  " "


        if simple_configs != "":
           os.system("pm configuration " + self.dst_prj + " " + self.desti_ip + " " + self.dst_bom + " " + simple_configs)
           os.system("pm propval -v " + self.userid + " -C Owner " + self.dst_prj + " " + self.desti_ip + " " + self.dst_bom)
          
           composite_config_creation_time = self.get_relevant_time_string()
           os.system("pm propval -v '" + composite_config_creation_time + "' -C 'Created at' " + self.dst_prj + " " + self.desti_ip + " " + self.dst_bom)
     
           self.ip_update_type()
           self.update_ip_owner_ship()



    def run(self):

        a = Pre_Check_Input_For_Errors(self.src_prj, self.dst_prj, self.src_bom, self.dst_bom, self.ip, self.desti_ip)
        a.error_handling()
        config_details = self.get_library( self.src_prj, self.ip, self.src_bom)
        ret = self.process_library_command_output(config_details)
        return ret



