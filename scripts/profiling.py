#! /usr/bin/env python

'''
The cmd_list file need to fulfileld following criteria:
1. Only two command in a section
2. each command should start with arc submit

Example:
[dmx bom clone]
GDP=arc submit -- dmx bom clone -p hpsi10 -i soc_hps_wrapper -b fmx_dev --dstbom gdp-bomclone-wplimtest1__21ww340a --debug
GDPXL=arc submit project/falcon/branch/fm6revbmain/rc,dev/lionelta/gdpxl46444,ostype/suse12,dmx/wplim_gdpdev  -- dmx bom clone -p hpsi10 -i soc_hps_wrapper -b fmx_dev --dstbom gdpxl-bomclone-wplimtest1__21ww340a  --debug

'''

import matplotlib
#matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt

import numpy 
import logging
import argparse
import os
import subprocess
import sys
import re
import glob
import unicodedata
import dmx.utillib.loggingutils
from prettytable import PrettyTable
from dmx.utillib.utils import run_command, create_tempfile_that_is_readable_by_everyone
import configparser
import time
import dmx.utillib.arc_rest_api
import datetime
class ProfilingDmxError(Exception): pass

logger = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)

def main():
    args = _add_args()
    if args.debug:
        logger = setup_logger(level=logging.DEBUG)
    else:
        logger = setup_logger(level=logging.INFO)
    
    if os.path.exists(args.output_directory):
        if not os.path.isdir(args.output_directory) :
            logger.error('{} is not a directory.'.format(args.output_directory))
            sys.exit(1)
    else:
        logger.info('Creating output directory {}'.format(args.output_directory))
        cmd = 'mkdir -p {}'.format(args.output_directory)
        exitcode, stdout, stderr = run_command(cmd)
    cmd = 'cp -rf {} {}/user_provided.cfg'.format(args.cmd_list, args.output_directory)
    exitcode, stdout, stderr = run_command(cmd)
    os.chdir(args.output_directory)
    
    run_cmd_list(args)

def read_config_file(cfg):
    parser = configparser.ConfigParser()
    
    parser.read(cfg)
    for section in parser.sections():
        # Check section name:
        if not re.search('\S+(:\d+)?', section):
            logger.error('Sectioname \'{}\' invalid. Kindly recheck your config file'.format(section))
            sys.exit(1)

        if len(parser.items(section)) != 2 and section != 'UNIQ':
            logger.error('\'{}\' should contain 2 different command. Kindly recheck your config file.'.format(section))
            sys.exit(1)
        for cmdtype, cmd in parser.items(section):
            if re.search('^skip_', cmdtype): continue
#            if cmdtype != 'uniq':
            if 'arc submit' not in cmd and section != 'UNIQ':
                logger.error('Section \'{}\' - {} cmd does not contain arc submit. Kindly recheck your config file'.format(section, cmdtype))
                sys.exit(1)
            
    return parser

def mod_config_file(cfg, limit=1):
    modfilename = create_tempfile_that_is_readable_by_everyone()
    new_config = configparser.ConfigParser(allow_no_value=True)
    new_config.read(modfilename)
    parser = configparser.ConfigParser(allow_no_value=True)
    parser.read(cfg)

    for section in parser.sections():
        if section != 'UNIQ':
            for i in range(0, limit):
                # add new section
                new_section = '{}: {}'.format(section, i)
                new_config.add_section(new_section) 
           
                # add section key:value pair
                for cmdtype, cmd in parser.items(section) :
                    epoch_time = int(time.time())
                    user = os.environ.get('USER')
                    new_cmd = cmd
                    if 'UNIQ' in parser.sections():
                        for key, mod_str in parser.items('UNIQ'):
                            #replace_str = '{}_{}_{}_{}'.format(mod_str, user, epoch_time, i)
                            replace_str = '{}_{}_{}'.format(user, epoch_time, i)
                            new_cmd = cmd.replace(key, replace_str)
                    new_config.set(new_section, cmdtype, new_cmd)

    with open(modfilename, 'wb') as configfile:
        new_config.write(configfile)
    
    exitcode, stdout, stderr = run_command('cp {0} final_profiling_cmd.cfg; rm -rf {0}'.format(modfilename))

    final_config_file = os.path.abspath('final_profiling_cmd.cfg')
    logger.info('Modified config file: {}'.format(final_config_file))

    return final_config_file 


class ResultObj:
    def __init__(self, section, cmd_type, cmd, arc_job, ori_name):
        self.section = section
        self.cmd_type = cmd_type
        self.cmd = cmd
        self.arcjob = arc_job
        self.ori_name = ori_name

def gen_arc_id_config(data):
    logger.info('Genenerate arc id config arc_job.cfg')
    tmpfile = create_tempfile_that_is_readable_by_everyone()
    arc_id_config = configparser.ConfigParser(allow_no_value=True)
    arc_id_config.read(tmpfile)
    MULTI_RUN = True 
    run_num = 0

    for section, result_objs in data.items():
        ori_section = section
        if len(result_objs) == 2:
            MULTI_RUN = False
            arc_id_config.add_section(section) 

        all_result_objs = zip(result_objs, result_objs[1:])[::2]
        for result_obj in all_result_objs:
            if MULTI_RUN:
                section = '{}: {}'.format(ori_section, str(run_num))
                run_num += 1
                arc_id_config.add_section(section) 

            for ea_result_obj in result_obj: 
                cmdtype = ea_result_obj.cmd_type
                if 'skip' not in cmdtype:
                    cmdtype = 'SKIP_{}'.format(ea_result_obj.cmd_type)
                arcjob = ea_result_obj.arcjob
                arc_id_config.set(section, cmdtype, arcjob)

    with open(tmpfile, 'wb') as configfile:
        arc_id_config.write(configfile)
 
    exitcode, stdout, stderr = run_command('cp {0} arc_job.cfg; rm -rf {0}'.format(tmpfile))
 
def run_cmd_list(args):

   # parser = read_config_file(args.cmd_list)
    mod_file_name = mod_config_file('user_provided.cfg', args.limit)
    parser = read_config_file(mod_file_name)
    all_arcjobid =  [] 
    data =  {} 
    multiplesection = {}


    for section in parser.sections():
        for cmdtype, cmd in parser.items(section) :
            start_time = time.time()
            if re.search('^skip_', cmdtype):
                exitcode = 0
                stderr = ''
                stdout = cmd.rstrip().lstrip()
                logger.info('SKIP detected in cmd. Arc id :  {}'.format(stdout))
            else:
                logger.info('Running: {}'.format(cmd))
                exitcode, stdout, stderr = run_command(cmd)
                if args.serial:
                    arcid = stdout.rstrip()
                    logger.info('Run serially, waiting for {}'.format(arcid))
                    os.system('arc wait {}'.format(arcid))

            arcjob = stdout.rstrip()
            all_arcjobid.append(arcjob)

            match = re.search('(.*?):(.*\d+.*)?', section)
            oriname = section
            if match:
                section = match.group(1)
            obj = ResultObj(section, cmdtype, cmd, arcjob, oriname)
            if not data.get(section):
                #print section,  cmdtype, cmd, arcjob
                data[section] = [obj]
            else:
                data[section].append(obj)
    logger.info('Waiting for all arc job to be done...')
    for arcid in all_arcjobid:
        logger.info(arcid)
        os.system('arc wait {}'.format(arcid))
    logger.info('All arc job done.')

    gen_arc_id_config(data)
    name1, name2 = gen_table_html(data, args.output_directory, args.html_type)
    gen_html_main_page()
    gen_summary_page(name1, name2)


def gen_table_html(data, output, html_type):
    logger.info('Generate html page..')
    #if html_type == 'combine':
    foc = open('combine.html','w+')

    for section, objs in data.items():
        split_html_name = section.replace(' ','_') + '.html'
        fos = open(split_html_name,'w+')
        cmd_data = gen_cmd_data(objs)
        if html_type == '1':
            table_html = get_table_html(cmd_data, section)
        elif html_type == '2':
            table_html = get_table_html2(cmd_data, section)
        foc.write('<br>')
        fos.write(table_html)
        foc.write(table_html)

    foc.close()
    fos.close()
    logger.info('Html page generate done.')
    return cmd_data.keys()[0], cmd_data.keys()[1]

def grep_line_before_and_after(html_file, keyword):
    cmd = 'grep -A1 {0} {1} | grep -v {0}'.format(keyword, html_file)
    exitcode, stdout, stderr = run_command(cmd)
    command1 =  stdout.replace('<td>', '').replace('</td>', '').rstrip().lstrip()
    cmd = 'grep -B1 {0} {1} | grep -v {0}'.format(keyword, html_file)
    exitcode, stdout, stderr = run_command(cmd)
    command2 =  stdout.replace('<td>', '').replace('</td>', '').rstrip().lstrip()

 #   match = re.search('>(\S+)</span', command1)
 #   if match:
 #       command1 = match.group(1)
 #   match = re.search('>(\S+)</span', command2)
 #   if match:
 ##       command2 = match.group(1)
#

    return (command1, command2) 
 
 
def get_summary_info(html_file):
    data = {}
    (command1, command2) = grep_line_before_and_after(html_file, 'Name')
    (avg_time1, avg_time2) = grep_line_before_and_after(html_file, 'Average')
    (stddev1, stddev2) = grep_line_before_and_after(html_file, 'stddev')
    match = re.search('<b>\S+\s*\|\s*\S+\s*\|\s*\S+\s*\|\s*(\S+)<b>', stddev1)

    if match:
        stddev1 = match.group(1)

    match = re.search('<b>\S+\s*\|\s*\S+\s*\|\s*\S+\s*\|\s*(\S+)<b>', stddev2)
    if match:
        stddev2 = match.group(1)

    print stddev1
    print stddev2
    data[command1] = [avg_time1, stddev1]
    data[command2] = [avg_time2, stddev2]
    return data

def gen_summary_page(name1, name2):
    x = PrettyTable()
    x.field_names = ['', name1, name2, name1, name2]
    x.add_row(['', 'Average time','Average time', 'Std deviation', 'Std deviation'])
    logger.info('Generate summary page')
    fo = open('summary.html', 'wb+')
    all_html = glob.glob('*.html')
    for ea_html in all_html:
        html_noext = ea_html.replace('.html', '')
        section_name = '<a href="{0}.html">{0}</a><br>'.format(html_noext)
        if ea_html == 'main.html' or ea_html == 'combine.html' or ea_html == 'summary.html': continue
        data = get_summary_info(ea_html)
        cmd1 = data.keys()[0]
        cmd2 = data.keys()[1]
        avgtime1 = data[cmd1][0]
        avgtime2 = data[cmd2][0]
        stddev1 = data[cmd1][1]
        stddev2 = data[cmd2][1]


        x.add_row([section_name, avgtime1, avgtime2, stddev1, stddev2])

    summary_html = post_process_prettytable_string(x.get_html_string())

  #  print summary_html
    fo.write('<h1>Summary table</h1>')
    fo.write(summary_html)
    fo.close()
    logger.info('Done')


def gen_html_main_page():
    logger.info('Generate html main page')
    fo = open('main.html', 'wb+')
    all_html = glob.glob('*.html')
    for ea_html in all_html:
        if ea_html == 'main.html' or ea_html == 'combine.html': continue
        ea_html = ea_html.replace('.html', '')
        line = '<a href="{0}.html">{0}</a><br>'.format(ea_html)
        fo.write(line)
    fo.close()
    logger.info('Done')

def gen_cmd_data(objs):
    cmd_data = {}
    for obj in objs: 
        EC_SITE = os.environ.get('EC_SITE')
        a = dmx.utillib.arc_rest_api.ArcRestApi(EC_SITE) 
        data = a.get_job(obj.arcjob)
        #elapsed_time = datetime.timedelta(seconds=int(data['elapsed_time']))
        elapsed_time = int(data['elapsed_time'])
        storage = data['storage']
        stdout = "<a href=\"https://psg-{1}-arc.{1}.intel.com/{0}/stdout.txt\">Stdout </a>".format(storage, EC_SITE)
        stderr = "<a href=\"https://psg-{1}-arc.{1}.intel.com/{0}/stderr.txt\">Stderr</a>".format(storage, EC_SITE)
        arcdb = "<a href=\"https://psg-{0}-arc.{0}.intel.com/arc/dashboard/reports/show_job/{1}\">{1}</a>".format(EC_SITE, obj.arcjob)
        cmd = obj.cmd
        exitcode = data['return_code']
        oriname = obj.ori_name
        cmdtype = obj.cmd_type
        match = re.search('^skip_(\S+)', obj.cmd_type)
        if match:
            cmdtype = match.group(1)
            cmd = data['command']

        if not cmd_data.get(cmdtype):
            cmd_data[cmdtype] = {}
            cmd_data[cmdtype]['Name'] = [cmdtype]
            cmd_data[cmdtype]['Average elapsed time(hh:mm:ss)'] = [elapsed_time]
            cmd_data[cmdtype]['Stdout'] = [stdout]
            cmd_data[cmdtype]['Stderr'] = [stderr]
            cmd_data[cmdtype]['Exitcode'] = [exitcode]
            cmd_data[cmdtype]['Arc'] = [arcdb]
            cmd_data[cmdtype]['Command'] = [cmd]
        else:
            cmd_data[cmdtype]['Name'].append(cmdtype)
            cmd_data[cmdtype]['Average elapsed time(hh:mm:ss)'].append(elapsed_time)
            cmd_data[cmdtype]['Stdout'].append(stdout)
            cmd_data[cmdtype]['Stderr'].append(stderr)
            cmd_data[cmdtype]['Exitcode'].append(exitcode)
            cmd_data[cmdtype]['Arc'].append(arcdb)
            cmd_data[cmdtype]['Command'].append(cmd)
    
    return cmd_data

def get_table_html(cmd_data, section):
    x = PrettyTable()
    x.field_names = [section, "Comparison", section]
  
    values = ['Command', 'Name', 'Arc', 'Stdout', 'Stderr', 'Exitcode', 'Average elapsed time(hh:mm:ss)']
    #values = ['Command', 'Arc', 'Stdout', 'Stderr', 'Total elapsed time(hh:mm:ss)']
    for v in values:

        cmdtypes = cmd_data.keys()
        totalt = 0
        if v == 'Average elapsed time(hh:mm:ss)':
            elasped_time1 = cmd_data[cmdtypes[0]].get(v)
            elasped_time2 = cmd_data[cmdtypes[1]].get(v)
            name1 = cmd_data[cmdtypes[0]].get('Name')[0]
            name2 = cmd_data[cmdtypes[1]].get('Name')[0]
            command_name = section.replace(' ', '_')

            min_elapsed_time1 = min(elasped_time1)
            min_elapsed_time2 = min(elasped_time2)
            max_elapsed_time1 = max(elasped_time1)
            max_elapsed_time2 = max(elasped_time2)
            mean_elapsed_time1 = datetime.timedelta(seconds=int(numpy.mean(elasped_time1)))
            mean_elapsed_time2 = datetime.timedelta(seconds=int(numpy.mean(elasped_time2)))
            median_elapsed_time1 = numpy.median(elasped_time1)
            median_elapsed_time2 = numpy.median(elasped_time2)

            graph_name = gen_graph(elasped_time1, elasped_time2, name1, name2, command_name)

            if mean_elapsed_time1 > mean_elapsed_time2:
                 mean_elapsed_time1 = "<b><span style=\"color:red\">{}</span><b>".format(mean_elapsed_time1)
                 mean_elapsed_time2 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time2)
            elif mean_elapsed_time1 < mean_elapsed_time2:
                 mean_elapsed_time1 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time1)
                 mean_elapsed_time2 = "<b><span style=\"color:red\">{}</span><b>".format(mean_elapsed_time2)
            else:
                 mean_elapsed_time1 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time1)
                 mean_elapsed_time2 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time2)
    
            d1 = mean_elapsed_time1
            d2 = mean_elapsed_time2

            mmm1 = '<b>' + str(datetime.timedelta(seconds=int(min_elapsed_time1))) + ' | ' + str(datetime.timedelta(seconds=int(max_elapsed_time1))) + ' | ' +str(datetime.timedelta(seconds=int(median_elapsed_time1))) + '<b>'
            mmm2 = '<b>' + str(datetime.timedelta(seconds=int(min_elapsed_time2))) + ' | ' + str(datetime.timedelta(seconds=int(max_elapsed_time2))) + ' | ' +str(datetime.timedelta(seconds=int(median_elapsed_time2))) + '<b>'
            x.add_row([mmm1, 'min | max | median', mmm2])
            x.add_row(['MaGiccolspan="3" align="center"><img src="{}" >'.format(graph_name),'',''])
           # x.add_row([ '' ])
        elif v == 'Exitcode':
            CONTAIN_NON_ZERO = False
            d1 = cmd_data[cmdtypes[0]].get(v)
            d2 = cmd_data[cmdtypes[1]].get(v)
            for element in d1:
                if element != '0': CONTAIN_NON_ZERO = True
            if CONTAIN_NON_ZERO:
                d1 = 'MaGicbgcolor="red">' + '<br>'.join(d1)
            else:
                d1 = '<br>'.join(d1)

            CONTAIN_NON_ZERO = False
            for element in d2:
                if element != '0': CONTAIN_NON_ZERO = True 

            if CONTAIN_NON_ZERO:
                d2 = 'MaGicbgcolor="red">' + '<br>'.join(d2)
            else:
                d2 = '<br>'.join(d2)



        else:

            d1 = '<br>'.join(cmd_data[cmdtypes[0]].get(v))
            d2 = '<br>'.join(cmd_data[cmdtypes[1]].get(v))
        
        x.add_row([d1, v, d2])
    html = post_process_prettytable_string(x.get_html_string())
    return html 


def get_table_html2(cmd_data, section):
    x = PrettyTable()
    x.field_names = [section, "Comparison", section]
  
    values = ['Command', 'Name', 'Exitcode|ARC|Stdout|Stderr', 'Average elapsed time(hh:mm:ss)']
    #values = ['Command', 'Arc', 'Stdout', 'Stderr', 'Total elapsed time(hh:mm:ss)']
    for v in values:

        cmdtypes = cmd_data.keys()
        totalt = 0
        if v == 'Average elapsed time(hh:mm:ss)':
            elasped_time1 = cmd_data[cmdtypes[0]].get(v)
            elasped_time2 = cmd_data[cmdtypes[1]].get(v)
            name1 = cmd_data[cmdtypes[0]].get('Name')[0]
            name2 = cmd_data[cmdtypes[1]].get('Name')[0]
            command_name = section.replace(' ', '_')

            min_elapsed_time1 = min(elasped_time1)
            min_elapsed_time2 = min(elasped_time2)
            max_elapsed_time1 = max(elasped_time1)
            max_elapsed_time2 = max(elasped_time2)
            mean_elapsed_time1 = datetime.timedelta(seconds=int(numpy.mean(elasped_time1)))
            mean_elapsed_time2 = datetime.timedelta(seconds=int(numpy.mean(elasped_time2)))
            median_elapsed_time1 = numpy.median(elasped_time1)
            median_elapsed_time2 = numpy.median(elasped_time2)
            stddev_elapsed_time1 = str(datetime.timedelta(seconds=int(numpy.std(elasped_time1))))
            stddev_elapsed_time2 = str(datetime.timedelta(seconds=int(numpy.std(elasped_time2))))


            graph_name = gen_graph(elasped_time1, elasped_time2, name1, name2, command_name)

            if mean_elapsed_time1 > mean_elapsed_time2:
                 mean_elapsed_time1 = "<b><span style=\"color:red\">{}</span><b>".format(mean_elapsed_time1)
                 mean_elapsed_time2 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time2)
            elif mean_elapsed_time1 < mean_elapsed_time2:
                 mean_elapsed_time1 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time1)
                 mean_elapsed_time2 = "<b><span style=\"color:red\">{}</span><b>".format(mean_elapsed_time2)
            else:
                 mean_elapsed_time1 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time1)
                 mean_elapsed_time2 = "<b><span style=\"color:green\">{}</span><b>".format(mean_elapsed_time2)
    
            d1 = mean_elapsed_time1
            d2 = mean_elapsed_time2

            mmm1 = '<b>' + str(datetime.timedelta(seconds=int(min_elapsed_time1))) + ' | ' + str(datetime.timedelta(seconds=int(max_elapsed_time1))) + ' | ' +str(datetime.timedelta(seconds=int(median_elapsed_time1))) + ' | ' + stddev_elapsed_time1  + '<b>'
            mmm2 = '<b>' + str(datetime.timedelta(seconds=int(min_elapsed_time2))) + ' | ' + str(datetime.timedelta(seconds=int(max_elapsed_time2))) + '  | ' +str(datetime.timedelta(seconds=int(median_elapsed_time2))) + ' | ' + stddev_elapsed_time2 + '<b>'
            x.add_row([mmm1, 'min | max | median | stddev', mmm2])
            x.add_row(['MaGiccolspan="3" align="center"><img src="{}" >'.format(graph_name),'',''])
           # x.add_row([ '' ])
        elif v == 'Exitcode|ARC|Stdout|Stderr':

            d1 = []
            d2 = []

            CONTAIN_NON_ZERO = False
            Exitcode1 = cmd_data[cmdtypes[0]].get('Exitcode')
            Exitcode2 = cmd_data[cmdtypes[1]].get('Exitcode')

            Arc1 = cmd_data[cmdtypes[0]].get('Arc') 
            Arc2 = cmd_data[cmdtypes[1]].get('Arc') 

            Stdout1 = cmd_data[cmdtypes[0]].get('Stdout') 
            Stdout2 = cmd_data[cmdtypes[1]].get('Stdout') 

            Stderr1 = cmd_data[cmdtypes[0]].get('Stderr') 
            Stderr2 = cmd_data[cmdtypes[1]].get('Stderr') 


            for i,  element in enumerate(Exitcode1):
                if element != '0': CONTAIN_NON_ZERO = True

                temp = '{} | {} | {} | {}'.format(element, Arc1[i], Stdout1[i], Stderr1[i])
                d1.append(temp)

            if CONTAIN_NON_ZERO:
                d1 = 'MaGicbgcolor="red">' + '<br>'.join(d1)
            else:
                d1 = '<br>'.join(d1)

            CONTAIN_NON_ZERO = False
            for i, element in enumerate(Exitcode2):
                if element != '0': CONTAIN_NON_ZERO = True 

                temp = '{} | {} | {} | {}'.format(element, Arc2[i], Stdout2[i], Stderr2[i])
                d2.append(temp)


            if CONTAIN_NON_ZERO:
                d2 = 'MaGicbgcolor="red">' + '<br>'.join(d2)
            else:
                d2 = '<br>'.join(d2)

        else:

           # d1 = '<br>'.join(cmd_data[cmdtypes[0]].get(v))
           # d2 = '<br>'.join(cmd_data[cmdtypes[1]].get(v))
            d1 = cmd_data[cmdtypes[0]].get(v)[0]
            d2 = cmd_data[cmdtypes[1]].get(v)[0]
        

        x.add_row([d1, v, d2])
    html = post_process_prettytable_string(x.get_html_string())
    return html 

def gen_graph(data1, data2, name1, name2, command_name):
    graph_name = command_name + '.png'
    average1 = [sum(data1) / len(data1)] * len(data1)
    average2 = [sum(data2) / len(data2)] * len(data2)

    # If there is only 1 data in list, we insert a zero number to the first list so that a line graph can be plotted
    if len(data1) == 1 and len(data2) == 1:
        data1.insert(0, 0)
        data2.insert(0, 0)
    plt.plot(data1, label=name1)
    plt.plot(data2, label=name2)

    x = [x for x in range(0, len(average1))]
    mean_line1 = plt.plot(x,average1, label='Mean of {}'.format(name1), linestyle='--')
    mean_line2 = plt.plot(x,average2, label='Mean of {}'.format(name2), linestyle='--')

    plt.xlabel('Run')
    plt.ylabel('Time(s)')
    plt.title('Line plot of runtime between {} and {} run in {}'.format(name1, name2, command_name))
    plt.legend()
    plt.savefig(graph_name)
    plt.close()

    return graph_name

def post_process_prettytable_string(txt):
    '''
    Post Process the prettytable html which contain >MaGic and &gt; keyword

    Parameters
    ----------
    txt : string
        The html text from pretty table get_html_string()

    Returns
    ----------
    txt : string
        pretty html code that able to output correct color
    '''
    return txt.replace('>MaGic',' ').replace('&gt;','>').replace('&lt;','<')
    #return txt.replace('&gt;','>').replace('&lt;','<')


def _add_args():
    ''' Parse the cmdline arguments '''
    # Simple Parser Example
    parser = argparse.ArgumentParser(description="Desc")
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    optional.add_argument("-d", "--debug", action='store_true', help="debug level")
    required.add_argument("-c", "--cmd_list", required=True, help="file contain cmd list")
  #  required.add_argument("-o", "--output", required=True, help="output file")
    required.add_argument("-o", "--output_directory", required=True, help="output directory")
    optional.add_argument("-l", "--limit", default=1,   type=int, required=False, help="limit, number of run")
    optional.add_argument("--html_type", default='2', required=False,  choices=['1', '2'], help="html type")
    optional.add_argument("-s", '--serial',  action='store_true', required=False, help="run serially on each command")

    args = parser.parse_args()


    return args


def setup_logger(name=None, level=logging.INFO):
    ''' Setup the logger for the logging module.

    If this is a logger for the top level (root logger),
        name=None
    else
        the __name__ variable from the caller should be passed into name

    Returns the logger instant.
    '''

    if name:
        LOGGER = logging.getLogger(name)
    else:
        LOGGER = logging.getLogger()

    if level <= logging.DEBUG:
        fmt = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
    else:
        fmt = "%(levelname)s: %(message)s"

    logging.basicConfig(format=fmt)
    LOGGER.setLevel(level)

    return LOGGER


if __name__ == '__main__':
    sys.exit(main())

   
