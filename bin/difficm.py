#!/usr/bin/env python
'''
Utility to diff between 2 files using tkdiff
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
    if len(args) != 2:
        print "ERROR: Please provide only 2 files as inputs for comparison."
        sys.exit(0)
    first_file, second_file = args
    try:
        first_path = print_and_save(first_file)   
        second_path = print_and_save(second_file)
        launch_tkdiff(first_path, second_path)
    finally:
        os.unlink(first_path)
        os.unlink(second_path)

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
    
def launch_tkdiff(first, second):
    subprocess.call(["tkdiff", first, second])
    
if __name__ == '__main__':
    main()
    sys.exit(0)
