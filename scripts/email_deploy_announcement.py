#!/usr/bin/env python

import sys
import ast
import argparse
import re
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tool')
    parser.add_argument('--change', nargs='*')
    parser.add_argument('--version')
    parser.add_argument('--subscriber', nargs='*')
    args = parser.parse_args()
    
    tool = args.tool
    change = ' '.join(args.change)
    version = args.version

    print 'subscribers: {}'.format(args.subscriber)
    import altera.build.makedeploy
    assert altera.build.makedeploy.announce_deployment(tool, change, version, recipients=args.subscriber)

if __name__ == '__main__':
    main()
