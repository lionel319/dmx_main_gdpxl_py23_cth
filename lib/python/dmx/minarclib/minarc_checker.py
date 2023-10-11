#!/usr/bin/env python

from __future__ import print_function
import argparse

from dmx.minarclib.parse_audit_files import atomic_parse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse the arguments')
    parser.add_argument('command', nargs=1, help='The command to run')
    parser.add_argument('-i','--ip_name', type=str, dest='ip_name', action='store', required=False, help='IP Name')
    parser.add_argument('-d', '--deliverable', type=str, dest='deliverable', action='store', required=False, help='deliverable name')
    parser.add_argument('-m','--milestone', type=str, dest='milestone', action='store',  required=True, help='milestone name')
    parser.add_argument('-o', '--override', type=str, dest='override', action='store', required=False, help='an override file (relative path)')
    parser.add_argument('-f', '--file_output', type=str, dest='output', action='store', required=False, help='a destination for the output file. (e.g., $HOME/output.txt)')
    args = parser.parse_args()

    if args.deliverable and args.deliverable not in ['cdl','oasis','pnr','timemod','bcmrbc','cvrtl','fv','schmisc','rcxt','sta','rv','dftdsm','lint','cdc','ippwrmod','upf_rtl','rtlcompchk','yx2gln','stamod','rdf','cvsignoff','fvpnr','upf_netlist','cvimpl']:
      print('Error: this deliverable is not part of the approved list for minarc')
      exit()
    
    atomic_parse(
        args.ip_name, 
        args.milestone, 
        cli=True, 
        single_deliverable=args.deliverable,
        arc_override=args.override,
        output_file=args.output
    )
