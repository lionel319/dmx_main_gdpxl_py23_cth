#!/usr/bin/env python

'''
Usage:-
    json_schema_validate.py <jsonfile> <schemafile>

Example:-
    json_schema_validate.py ../data/Nadder/products.json ./products.json
'''

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import json
import jsonschema

ref = sys.argv[1]
golden = sys.argv[2]

schema = json.loads(open(golden).read())
data = json.loads(open(ref).read())

try:
    jsonschema.validate(data, schema)
    print "Pass"
except:
    raise
