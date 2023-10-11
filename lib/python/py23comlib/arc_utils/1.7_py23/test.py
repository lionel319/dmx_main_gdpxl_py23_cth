#!/usr/bin/env python

import sys
import os
sys.path.insert(0, '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_py23/lib/python/py23comlib/arc_utils/1.7_py23')

os.environ['DJANGO_SETTINGS_MODULE'] = 'arc_orm.arc_orm_settings'
from arc_orm.models import Jobs, ResourceData
import arc_orm
print(arc_orm.__file__)
site = 'psg-sc-arc.sc.intel.com'

a = Jobs.objects.using(site).get(id='450656523')
print(a.id)
print(a.user)
print(a.storage)
print(a.status)
print("+++++++++++++++++++")

s = ResourceData.objects.using(site).filter(resource='1301580')
for b in s:
    print(b.id)
    print(b.resource)
    print(b.name)
    print(b.value)
    print("---")
