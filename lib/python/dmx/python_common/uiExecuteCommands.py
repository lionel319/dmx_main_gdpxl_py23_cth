import subprocess as _subprocess
#from multiprocessing import Pool, Process, cpu_count
from dmx.python_common.uiPrintMessage import uiInfo

#########################################################
# Run command
#   -> display in the console
#   -> print in the log file
#########################################################
def run(cmd):

    p = _subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=_subprocess.PIPE, stderr=_subprocess.STDOUT)
       
    while p.poll() is None:
        try:
            line = p.stdout.readline().rstrip().encode('utf-8', 'ignore')
            uiInfo(line.decode('utf-8'))
        except UnicodeDecodeError:
            continue
    
    return p.returncode

#########################################################
# Run command
#   -> Wait the process terminated to output log
#########################################################
def run_command(cmd, input_data=None):

    p = _subprocess.Popen(
            cmd, bufsize=1, shell=True, universal_newlines=True,
            stdin=_subprocess.PIPE, stdout=_subprocess.PIPE, stderr=_subprocess.STDOUT)

    (stdout, stderr) = p.communicate(input_data)
    exitstatus = p.returncode

    return (exitstatus, stdout)
