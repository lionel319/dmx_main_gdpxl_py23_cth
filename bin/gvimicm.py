#!/usr/bin/env python
'''
Utility to display an ICM file using gvim
'''
import os
import sys
import subprocess
from tempfile import NamedTemporaryFile


LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.icm import ICManageCLI

def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print "ERROR: Please provide only 1 file to display."
        sys.exit(0)
    file = args[0]
    print_and_save(file)   

    file_path = print_and_save(file)   
    launch_gvim(file_path)

def print_and_save(file):
    '''
    Saves the content of the file#version into a temporary file        
    '''
    icm = ICManageCLI(preview=True)
    file_content = icm.p4_print(file)
    f = NamedTemporaryFile(delete=False, prefix='file')
    with open(f.name, 'w') as w:
        w.write(file_content)
        
    return f.name
    
def launch_gvim(file):
    subprocess.call(["gvim", file])
    
if __name__ == '__main__':
    main()
    sys.exit(0)
