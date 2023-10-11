## @page QuickStart Quick Start for EcoSphere API
## @{
##
## Getting started with EcoSphere.
## 
## # Import ecosphere
## @code
## from dmx.ecolib.ecosphere import EcoSphere
## @endcode
##
## # Instantiate ecosphere object with preview mode (no changes will be made).
## Any edit/add/delete calls made by this ecosphere object will be ignored.
## Only used for querying calls.
## @code
## e = EcoSphere()
## @endcode
##
## # Instantiate ecosphere object without preview mode (changes will be made to database).
## Any edit/add/delete calls made by this ecosphere object will update the database appropriately.
## @code
## e = EcoSphere(False)
## @endcode
## 
## # Get list of families
## @code
## families = e.get_families() 
## @endcode
## 
## # Get Nadder Family object
## @code
## family = e.get_family('Falcon')
## @endcode
## 
## # Get list of IPs under Falcon 
## @code
## ips = family.get_ips()
## @endcode
## 
## # Get list of IPs that ends with lib under Falcon
## @code
## ips = family.get_ips('.*lib$')
## @endcode
## 
## # Check if ar_lib IP exists in Falcon
## @code
## bool = family.has_ip('vr_lib')
## @endcode
## 
## # Get ar_lib IP object
## @code
## ip = family.get_ip('vr_lib')
## @endcode
## 
## # Get list of deliverables for vr_lib (if run within an icm-workspace, local and bom options are not needed. This applies to all the below commands that have these 2 options)
## @code
## deliverables = ip.get_deliverables(local=False, bom='dev')
## @endcode
## 
## # Get list of unneeded deliverables for vr_lib
## @code
## unneeded_deliverables = ip.get_unneeded_deliverables(local=False, bom='dev')
## @endcode
## 
## # Get list of cells for vr_lib
## @code
## cells = ip.get_cells(local=False, bom='dev')
## @endcode
## 
## # Get list of cells that starts with 'vr' for vr_lib
## @code
## cells = ip.get_cells(local=False, bom='dev', cell_filter='^vr.*')
## @endcode
## 
## # Get cell vr_aux object
## @code
## cell = ip.get_cell('vr_aux', local=False, bom='dev')
## @endcode
## 
## # Get list of unneeded deliverables for vr_aux
## @code
## unneeded_deliverables = cell.get_unneeded_deliverables(local=False, bom='dev')
## @endcode
## 
## # Mark a 'rtl' deliverable as unneeded for ar_spine_3_bf
## @code
## assert(cell.add_unneeded_deliverable('rtl'))
## @endcode
## 
## # Remove 'rtl' as an unneeded deliverabel for ar_spine_3_bf
## @code
## assert(cell.delete_unneeded_deliverable('rtl'))
## @endcode
## 
## # Get rtl deliverable object
## @code
## deliverable = ip.get_deliverable('rtl')
## @endcode
## 
## # Get list of rtl manifest properties
## @code
## successor = deliverable.successor
## predecessor = deliverable.predecessor
## consumer = deliverable.consumer
## producer = deliverable.producer
## pattern = deliverable.pattern
## filelist = deliverable.filelist
## @endcode
## 
## # Get list of checkers for rtl
## @code
## checkers = deliverable.get_checkers()
## @endcode
## 
## # Get list of checkers for rtl for milestone 1.0 with flow rtl
## @code
## checkers = deliverable.get_checkers(flow_filter='rtl',milestone='1.0')
## @endcode
##
## @}
