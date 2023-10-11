## @page ecolibgraph A Detail Hierarchical Graph Of the EcoSphere Architecture
## @image html ecolib.png

import os
# This switch tells us if we are using dmx in legacy or non-legacy environment
# Main difference would be in legacy, infos are coming from ICM, for non-legacy, infos are coming from django
LEGACY = True if os.getenv('DMX_LEGACY', '1') == '1' else False
