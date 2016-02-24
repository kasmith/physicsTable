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
from .utils.EasyMultithread import *
from trials import *
from simpleTable import *
from noisyTable import *
from multiprocessing import Pool
from .utils.dillMultithreading import *
import random, copy

# Unsafe translation of a number between 0 and 256^2-1 to a two character
def toBin(i):
    x = int(np.floor(i / 256))
    y = i % 256
    return chr(x)+chr(y)

def fromBin(s):
    return ord(s[0])*256 + ord(s[1])

class Path(object):
    def __init__(self,tab,kv,kb,km,pe,tl,ts,enforcegoal = True):
        ntab = makeNoisy(tab,kv,kb,km,pe)
        self.o, self.p = ntab.simulate(tl,ts,True)
        # Make sure that we get a valid goal
        while (self.o is TIMEUP or self.o is OUTOFBOUNDS) and enforcegoal:
            ntab = makeNoisy(tab,kv,kb,km,pe)
            self.o, self.p = ntab.simulate(tl,ts,True)
        self.maxtime = len(self.p)*ts
        # Test for compression possibilities
        maxpt = max(map(max,self.p))
        minpt = min(map(min,self.p))
        self.len = len(self.p)
        if maxpt > 256*256-1 or minpt < 0: raise Exception('Path out of bounds - not compressible')

    def compress(self):
        if self.p is None: raise Exception('Already compressed!')
        st = ""
        for p in self.p: st += toBin(p[0]) + toBin(p[1])
        self.comp = st
        self.p = None

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


class PathMaker(object):

    def __init__(self,trial, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, npaths = 100, pathdist = .1, timelen = 60., timeres = 0.05, cpus = cpu_count()):
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

        self.makePaths()

    def makePaths(self):
        self.paths = dict()

        # Get the runtime of the table
        tab = self.trial.makeTable()
        r = None
        while r is None: r = tab.step(self.pdist)
        maxtm = tab.tm
        ntms = int(np.ceil(maxtm / self.pdist))
        tms = [self.pdist*t for t in range(ntms)]
        pths = async_map(self.makePathSingTime,tms,self.ncpu)
        #pths = map(self.makePathSingTime,tms) # PUT async_map BACK!!!!
        for t,p in zip(tms,pths):
            rndtm = str(t)
            self.paths[rndtm] = p

    def makePathSingTime(self,t):
        tab = self.trial.makeTable()
        while tab.tm < t:
            tab.step(self.pdist)
        return map(lambda x: Path(tab,self.kv,self.kb,self.km,self.pe,self.time,self.res),range(self.npaths))

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

def loadPathMaker(flnm):
    fl = open(flnm,'rU')
    pm = pickle.load(fl)
    fl.close()
    pm.decompressPaths()
    return pm