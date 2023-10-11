#!/p/psg/ctools/python/2.7.13/linux64/suse12/bin/python

import os
import sys

def main():
    template = './psgcicq_psginfraadm_template_79008'
    frm = 17
    to = 100

    i = frm 
    while i <= to:
        name = "psgcicq_psginfraadm_{0}".format(i)
        print "Init {0} ...".format(name)
        outdir = './{0}'.format(name)
        incfgfile = outdir + "/conf/buildAgent.dist.properties"
        outcfgfile = outdir + "/conf/buildAgent.properties"
        os.system("cp -rf {0} {1}".format(template, outdir))

        IH = open(incfgfile, 'r')
        OH = open(outcfgfile, 'w')
        for line in IH:
            if line.startswith("serverUrl="):
                OH.write("serverUrl=https://teamcity01-fm.devtools.intel.com\n")
            elif line.startswith("name="):
                OH.write("name={}\n".format(name))
            else:
                OH.write(line)
        IH.close()
        OH.close()
        

        i = i + 1

if __name__ == "__main__":
    main()
