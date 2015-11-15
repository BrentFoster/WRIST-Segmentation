import multiprocessing
import os

def call_it(args=()):
    "indirect caller for instance methods and multiprocessing"
    return '1'

class Klass(object):
    def __init__(self, nobj):
 
        pool = multiprocessing.Pool(processes = multiprocessing.cpu_count())

        async_results = [pool.apply_async(call_it, args = ((i,))) for i in xrange(0,7)]

        pool.close()

        map(multiprocessing.pool.ApplyResult.wait, async_results)

        lst_results = [r.get() for r in async_results]

        print lst_results


Klass(nobj=8)