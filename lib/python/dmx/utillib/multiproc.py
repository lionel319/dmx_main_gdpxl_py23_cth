#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/multiproc.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Library for running tasks across multiple processes
Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''

#from multiprocessing import Pool
import multiprocessing
import multiprocessing.pool

from time import sleep

def run_mp(func, args, num_processes=2):
    '''
    Runs func across multiple processes using the list of argument tuples
    in args.

    :param func: The Python function to run
    :type func: function
    :param args: A list of arg lists. One instance of func will be run for each list.
    :type args: list
    :param num_processes: The number of processes to use. Defaults to 2.
    :type num_processes: int
    :return: List of results from each call to func.
    :rtype: list
    '''
    pool = MyPool(processes=num_processes)
    workers = []
    results = []

    for arg in args:
        workers.append(pool.apply_async(func, arg))

    while workers:
            # Have a brief nap each time around to stop us from consuming
            # 100% CPU when there's the workers are taking a long time to finish
            sleep(0.10)

            completed_workers = [x for x in workers if x.ready()]
            for worker in completed_workers:
                try:
                    results.append(worker.get())
                except (Exception, KeyboardInterrupt, SystemExit):
                    # Just catching exception is bad but all manner of errors could occur here
                    # The most important thing is to clean up the pool before raising the error
                    pool.close()
                    pool.terminate()
                    pool.join()
                    raise

                workers.remove(worker)

    ### CLEAN UP ###
    # Apparently, the spawn processes are not garbage-collected. 
    # The close() needs to be called in order for that to happen.
    # http://stackoverflow.com/questions/18414020/memory-usage-keep-growing-with-pythons-multiprocessing-pool
    # http://stackoverflow.com/a/7650252/335181
    pool.close()
    pool.join()

    return results

########################################################################################################
### We are facing the problem when trying to run an os.system() within a child of a multiprocess.
###    AssertionError: daemonic processes are not allowed to have children
### Shamelessly copied from https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
########################################################################################################
class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon attribute always return False
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess

