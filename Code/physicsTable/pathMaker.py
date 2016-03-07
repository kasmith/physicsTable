#################################
#
#
# For making and storing a compressed set of potential paths at every moment in time
#
#
#################################

from __future__ import division
import numpy as np
import cPickle as pickle
from .constants import *
from trials import *
from simpleTable import *
from noisyTable import *
from multiprocessing import Pool, cpu_count
from .utils import async_map, apply_async
import random, copy, os

# Unsafe translation of a number between 0 and 256^2-1 to a two character
def toBin(i):
    x = int(np.floor(i / 256))
    y = i % 256
    return chr(x)+chr(y)

def fromBin(s):
    return ord(s[0])*256 + ord(s[1])

def makeFileName(trnm,kapv,kapb,kapm,perr,nsims,path = '.'):
    kv = str(np.round(kapv))
    kb = str(np.round(kapb))
    km = str(np.round(kapm))
    pe = str(np.round(perr))
    pthname = kv + '_' + kb + '_' + km + '_' + pe + '_' + str(nsims)
    return os.path.join(path,pthname,trnm+'.pmo')

def loadPaths(trial,kapv,kapb,kapm,perr,nsims=200,path = '.',verbose=False):
    trpth = makeFileName(trial.name,kapv,kapb,kapm,perr,nsims,path)
    if not os.path.exists(trpth):
        print 'Nothing existing for trial ' + trial.name +'; making now'
        print 'Saving into: ' + trpth
        trdir = os.path.dirname(trpth)
        if not os.path.exists(trdir): os.makedirs(trdir)
        pm = PathMaker(trial,kapv,kapb,kapm,perr,nsims,verbose=verbose)
        pm.save(trpth)
    else:
        pm = loadPathMaker(trpth)
    return pm

class Path(object):
    def __init__(self,tab,kv,kb,km,pe,tl,ts,enforcegoal = True,verbose = False):
        ntab = makeNoisy(tab,kv,kb,km,pe)
        nbads = 0
        self.o, self.p, self.b = ntab.simulate(tl,ts,True,True)
        # Make sure that we get a valid goal
        while (self.o is TIMEUP or self.o is OUTOFBOUNDS or ntab.balls.bounces > 255) and enforcegoal:
            del ntab
            ntab = makeNoisy(tab,kv,kb,km,pe)
            nbads += 1
            self.o, self.p, self.b = ntab.simulate(tl,ts,True,True)
        self.maxtime = len(self.p)*ts
        # Test for compression possibilities
        maxpt = max(map(max,self.p))
        minpt = min(map(min,self.p))
        self.len = len(self.p)
        if maxpt > 256*256-1 or minpt < 0: raise Exception('Path out of bounds - not compressible')
        if max(self.b) > 255: raise Exception('Too many bounces to compress')
        self.maxbounce = max(self.b)
        self.ts = ts
        self.tl = tl
        self.initt = tab.tm
        del ntab
        if verbose:
            print "Done with path; ", tab.tm, "; redos:",nbads

    def compress(self):
        if self.p is None: raise Exception('Already compressed!')
        st = ""
        for p in self.p: st += toBin(p[0]) + toBin(p[1])
        self.comp = st
        self.p = None
        bst = ""
        for b in self.b: bst += chr(b)
        self.compb = bst
        self.b = None

    def decompress(self):
        if self.comp is None: raise Exception('Already uncompressed')
        self.p = []
        i = 0
        while i < len(self.comp):
            x = fromBin(self.comp[i:(i+2)])
            y = fromBin(self.comp[(i+2):(i+4)])
            self.p.append( (x,y) )
            i += 4
        if len(self.p) != self.len: raise Exception('Length mismatch - decompression error!')
        self.comp = None
        self.b = []
        for i in range(len(self.compb)):
            self.b.append(ord(self.compb[i]))
        if len(self.b) != self.len: raise Exception('Length mismatch (bounce) - decompression error!')
        self.compb = None

    def getpos(self,t):
        if self.p is None: self.decompress()
        if t > self.tl: return None
        i = int(t/self.ts)
        return self.p[i]


class PathMaker(object):

    def __init__(self,trial, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, npaths = 100, pathdist = .1, timelen = 60., timeres = 0.05, cpus = cpu_count(),verbose = False):
        self.trial = trial
        self.npaths = npaths
        self.kv = kapv
        self.kb = kapb
        self.km = kapm
        self.pe = perr
        self.time = timelen
        self.res = timeres
        self.pdist = pathdist
        self.ncpu = cpus

        self.makePaths(verbose)

    def makePaths(self,verbose=False):
        self.paths = dict()

        # Get the runtime of the table
        tab = self.trial.makeTable()
        r = None
        while r is None: r = tab.step(self.pdist)
        maxtm = tab.tm
        self.maxtm = maxtm
        ntms = int(np.ceil(maxtm / self.pp201.dist))
        tms = [self.pdist*t for t in range(ntms)]
        def f(t): return(self.makePathSingTime(t,verbose))
        pths = async_map(f,tms,self.ncpu)
        #pths = map(self.makePathSingTime,tms) # PUT async_map BACK!!!!
        for t,p in zip(tms,pths):
            rndtm = str(t)
            self.paths[rndtm] = p

    def makePathSingTime(self,t,verbose = False):
        tab = self.trial.makeTable()
        while tab.tm < t:
            tab.step(self.pdist)
        return map(lambda x: Path(tab,self.kv,self.kb,self.km,self.pe,self.time,self.res,verbose=verbose),range(self.npaths))

    def compressPaths(self):
        for k in self.paths.keys():
            for p in self.paths[k]:
                p.compress()

    def decompressPaths(self):
        for k in self.paths.keys():
            for p in self.paths[k]:
                p.decompress()

    def save(self,flnm):
        cp = copy.deepcopy(self)
        cp.compressPaths()
        fl = open(flnm,'w')
        pickle.dump(cp,fl,protocol=2)
        fl.close()

    # Simple way of pulling out a few outcomes and/or paths
    def getOutcomes(self,time,n):
        pths = self.paths[str(time)]
        rs = random.sample(pths,n)
        return [r.o for r in rs]

    def getPaths(self,time,n):
        pths = self.paths[str(time)]
        rs = random.sample(pths,n)
        return [r.p for r in rs]

    def getPathsAndOutcomes(self,time,n):
        pths = self.paths[str(time)]
        rs = random.sample(pths,n)
        return [(r.o,r.p) for r in rs]

    def getSinglePath(self, time):
        pths = self.paths[str(time)]
        return random.choice(pths)

    def getOutcomesAndBounces(self,time,n):
        pths = self.paths[str(time)]
        rs = random.sample(pths,n)
        return [(r.o,r.b) for r in rs]

def loadPathMaker(flnm):
    fl = open(flnm,'rU')
    pm = pickle.load(fl)
    fl.close()
    pm.decompressPaths()
    return pm