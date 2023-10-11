#!/usr/bin/env python
'''
USAGE:-
    check_current_is_pointing_to_correct_version.py project/bundle [project/bundle ...]
'''

from dmx.utillib.utils import run_command
import os
import sys

#EMAILS = ['lionelta', 'kwlim', 'taraclar', 'nbaklits']
EMAILS = ['lionelta']
#EMAILS = ['lionelta']

def main():
    arcreses = sys.argv[1:]

    txt = 'Site: {}\n\n\n'.format(os.environ['ARC_SITE'])
    for arcres in arcreses:

        [arcused, arcdmxver, arcdmxdataver] = get_version_from_latest_project_bundle(arcres)
        [curdmxver, curdmxdataver] = get_version_from_current_link()

        if arcdmxver == curdmxver and arcdmxdataver == curdmxdataver:
            status = "PASS"
            retcode = 0
        else:
            status = "FAIL"
            retcode = 1

        txt += '==============================================\n'
        txt += '{}: {}\n'.format(status, arcused)
        txt += '==============================================\n'
        txt += "arc_dmx_ver:{}\n".format(arcdmxver)
        txt += "cur_dmx_ver:{}\n".format(curdmxver)
        txt += '---------------------\n'
        txt += "arc_dmxdata_ver:{}\n".format(arcdmxdataver)
        txt += "cur_dmxdata_ver:{}\n".format(curdmxdataver)
        txt += '---------------------\n'
        txt += '\n\n'


    print txt
    sendmail(txt)
    return retcode


def sendmail(txt):
    cmd = ''' echo '{}' | mail -s 'dmx link version check({})' {} '''.format(txt, os.environ['ARC_SITE'], ' '.join(EMAILS))
    os.system(cmd)

def get_version_from_current_link():
    dmx = ''
    dmxdata = ''
    dmx = os.path.basename(os.path.realpath("/p/psg/flows/common/dmx/current"))
    dmxdata = os.path.basename(os.path.realpath("/p/psg/flows/common/dmxdata/current"))
    return [dmx.strip(), dmxdata.strip()]


def get_version_from_latest_project_bundle(arcres):
    dmx = ''
    dmxdata = ''
    (exitcode, stdout, stderr) = run_command('arc resource {} address'.format(arcres))
    arcused = "{}".format(stdout.strip())
    (exitcode, stdout, stderr) = run_command('arc resource {} resolved'.format(arcres))

    ### If stdout is still pointing to another bundle, keep looping until it is really resolved
    while stdout.startswith("project/"):
        (exitcode, stdout, stderr) = run_command('arc resource {} resolved'.format(stdout.strip()))

    for x in stdout.split(','):
        if x.startswith('dmx/'):
            dmx = x.lstrip('dmx/')
        elif x.startswith('dmxdata/'):
            dmxdata = x.lstrip('dmxdata/')
    return [arcused, dmx.strip(), dmxdata.strip()]


if __name__ == "__main__":
    sys.exit(main())
