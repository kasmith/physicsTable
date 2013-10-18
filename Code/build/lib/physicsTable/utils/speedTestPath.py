from __future__ import division

from EasyMultithread import *
from ..pathFilter import *
from multiprocessing import Pool, cpu_count

import sys,os, time
from ..trials import *

def runPath(tr):
    #for i in range(100): t = tr.makeTable(); del t
    pf =  PathFilter(tr.makeTable())
    while pf.step() is None: pass
    del pf
    return 1


def manyruns(tr, n = 50):
    multimap(lambda i: runPath(tr), range(n))
    print tr.name

def speedTest(tr, n = 50):
    st = time.time()
    manyruns(tr,n)
    et = time.time() - st
    print "Trial", tr.name, "; t =", et

if __name__ == '__main__':
    tnm = sys.argv[1]
    #tnm = 'OccRandTrial_100'
    
    if tnm == 'ALL':
        fls = os.listdir(outpath)
        trs = []
        for f in fls:
            if f[-4:] == '.ptr':
                tr = loadTrial(os.path.join(outpath,f))
                if tr.checkConsistency(): trs.append(tr)
        print "Numtrials:", len(trs)
        
        t = time.time()
        multimap(manyruns, trs)
        et = time.time() - t
        print "All trials; t:", et
        
    else:
        tr = loadTrial(os.path.join(outpath, tnm+'.ptr'))
    
        t = time.time()
        manyruns(tr)
        et = time.time() - t
    
        print "Trial:", tr.name, "; t:", et
    