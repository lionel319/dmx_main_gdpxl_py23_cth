#!/usr/bin/env python

import argparse

from dmx.minarclib.store_configs import store_configs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Store new rels into DB')
    parser.add_argument('-p','--project', type=str, dest='project_name', action='store', required=True, help='Project Name')
    
    args = parser.parse_args()
    store_configs(args.project_name)

