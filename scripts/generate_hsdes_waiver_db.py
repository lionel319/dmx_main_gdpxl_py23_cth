import datetime
import subprocess
import dmx.utillib.utils
date = datetime.datetime.today().strftime('%d-%m-%Y')
cmd = 'dmx waiver list > hsdes_waiver_{}'.format(date)
print "-I- Running {}".format(cmd)
exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
if exitcode:
    print "-E- {}".format(stderr)
else:
    print stdout
    print stderr
print "-I- Done"

