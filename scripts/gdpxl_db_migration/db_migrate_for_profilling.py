#!/p/psg/ctools/python/2.7.13/linux64/suse12/bin/python -u

import os
import sys
sys.stdout.flush()
sys.stderr.flush()

def main():

    infile = './gdpxl_libtypes'
    rootdir = '/nfs/site/disks/fln_lionel_1/lionelta'

    with open(infile) as f:
        for line in f:
            sline = line.strip()
            print "======================================"
            print "Working on {} ...".format(sline)

            gdpxl_ws, variant, libtype = sline.split('/')
            gdp_ws = 'lionelta.Falcon_Mesa.z1574b.1999'

            rsync = "rsync -avxzln --exclude '.icm*' {}/{}/{}/ {}/{}/{}/".format(
                gdp_ws, variant, libtype, 
                gdpxl_ws, variant, libtype)

            os.chdir(rootdir)

            print '--------------------------------------'
            print "> {}".format(rsync)
            os.system(rsync)


            os.chdir('{}/{}/{}'.format(gdpxl_ws, variant, libtype))

            checkin = 'xlp4 rec ...; xlp4 submit -d "db migration" ...'
            print '--------------------------------------'
            print "> {}".format(checkin)
            #os.system(checkin)
            

if __name__ == '__main__':
    main()
