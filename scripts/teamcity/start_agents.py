#!/p/psg/ctools/python/2.7.13/linux64/suse12/bin/python

import os
import sys

def main():
    frm = 17
    to = 100

    i = frm 
    while i <= to:
        name = "psgcicq_psginfraadm_{0}".format(i)
        cmd = "./{0}/bin/agent.sh start".format(name)
        print "Running: {0}".format(cmd)
        os.system(cmd)

        i = i + 1

if __name__ == "__main__":
    main()
