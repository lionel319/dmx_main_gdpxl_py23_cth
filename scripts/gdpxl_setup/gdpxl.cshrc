#To be placed one level up from the root client directory
#e.g. if client installed in /eda/icmanage/gdpxl.0.3.2
#     gdpxl.baschrc file sits in /eda/icmanage
setenv ICM_HOME "/nfs/site/disks/da_scratch_1/users/prevanka/workspace/icmgdp"

setenv PATH "$ICM_HOME/gdpxl.44145/bin.lnx86-64:$ICM_HOME/gdpxl.44145/gdm.lnx86-64:$ICM_HOME/gdpxl.44145/gdm.lnx86:$PATH"
setenv ICM_GDP_SERVER "http://scyapp37.sc.intel.com:5000"
setenv P4PORT "scyapp37.sc.intel.com:1666"
#setenv PYTHONPATH "$ICM_HOME/gdpxl.44145/cli:$ICM_HOME/gdpxl.44145/pypackages"

setenv ICM_SkillRoot "$ICM_HOME/gdpxl.44145"

if ( ! $?DISABLE_DAEMON_JS ) then
  set daemonId=`pgrep -f 'node.*daemon.js'`
  if ( $daemonId == "" ) then
    $ICM_HOME/gdpxl.44145/node/bin/node $ICM_HOME/gdpxl.44145/daemon/daemon.js &
  endif
endif

setenv GDM_USE_SHLIB_ENVVAR 1
#setenv LD_LIBRARY_PATH "$ICM_HOME/gdpxl.44145/gdm.lnx86-64:$ICM_HOME/gdpxl.44145/gdm.lnx86:$LD_LIBRARY_PATH"
#setenv CDS_GDM_SHLIB_LOCATION "$ICM_HOME/gdpxl.45753/gdm.lnx86-64:$ICM_HOME/gdpxl.45753/gdm.lnx86"

setenv P4CONFIG ".icmconfig"
setenv XLP4 "xlp4"

setenv PATH "${PATH}:/nfs/site/disks/da_scratch_1/users/prevanka/workspace/icmgdp/gdpxl.44145/bin.lnx86-64/"

