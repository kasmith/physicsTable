from __future__ import division
from multiprocessing import *
from itertools import izip

# Functions to fake multiprocessing (from internet: http://stackoverflow.com/questions/3288595/multiprocessing-using-pool-map-on-a-function-defined-in-a-class)
def spawn(f):
    def fun(pipe,x):
        pipe.send(f(x))
        pipe.close()
    return fun

def parmap(f,X,timeout = None):
    pipe = [Pipe() for x in X]
    proc = [Process(target=spawn(f),args=(c,x)) for x,(p,c) in izip(X,pipe)]
    [p.start() for p in proc]
    [p.join(timeout) for p in proc]
    return [p.recv() for (p,c) in pipe]
    
def chunks(l, n): return [l[i:i+n] for i in range(0, len(l), n)]


# Custom: works like map but does so across processors
def multimap(f,X,cpus = cpu_count(),timeout = None):
    return [r for sl in parmap(lambda x: [f(i) for i in x],chunks(X,int(len(X)/min(len(X),cpus))),timeout) for r in sl]