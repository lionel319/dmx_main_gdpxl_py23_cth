import dmx.ecolib.ecosphere
import pprint
import json

result = {}
e = dmx.ecolib.ecosphere.EcoSphere()
for f in e.get_families():
    icm_projects = e.get_family(f.name).get_icmprojects()

    for ea_icm_proj in icm_projects:
        ea_icm_proj = ea_icm_proj.name
        result[ea_icm_proj] = {} 
        result[ea_icm_proj]['Family'] = f.name

        deliverables = dmx.ecolib.loader.load_manifest(f.name)


        for deliverable in deliverables.keys():
            manifest = dmx.ecolib.manifest.Manifest(f.name, deliverable)
            deliverable = str(deliverable)
            if manifest.large:
                result[ea_icm_proj][deliverable]  = {}
                result[ea_icm_proj][deliverable]['dm'] = 'naa'
                result[ea_icm_proj][deliverable]['excluded_ip'] = manifest.large_excluded_ip

    j = json.dumps(result, indent=4)
    f = open('ld.json', 'w')
    f.write(j)
    f.close()


   # print deliverables.keys()
