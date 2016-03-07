from __future__ import division
from .. import SimpleTrial,RedGreenTrial,BasicTable,SimpleTable,NoisyTable,PathMaker
from ..pathMaker import makeFileName, loadPaths
from ..constants import *
from ..utils import async_map, apply_async, MakeSmoother, SmoothFromPre
from multiprocessing import cpu_count, Pool
import numpy as np
import scipy as sp
import os, sys, time
import cPickle as pickle


# Helper functions for setting / fitting evidence & decisions
def obs2Ev(obs,type1,type2):
    if obs == type1: return 1
    elif obs == type2: return -1
    else: return 0
obs2Ev = np.vectorize(obs2Ev)

def ev2Dec(ev,thresh,type1,type2):
    if ev >= thresh: return type1
    elif ev <= -thresh: return type2
    else: return 0
ev2Dec = np.vectorize(ev2Dec)

def countArray(ar):
    out = dict()
    for a in ar:
        if a not in out: out[a] = 0
        out[a] += 1
    return out

def safeDivide(x,y):
    if y < .00000001: return .5
    else: return x/y
safeDivide = np.vectorize(safeDivide)

# Accumulates evidence over time in an SPRT model with leakage
# Eventual output is in .odec, which is a list over time of array(p(type1),p(type2),p(neither)
class EvidenceAccumulation(object):
    def __init__(self,trial,kapv,kapb,kapm,perr,end1type,end2type,nsims=100,nevpath=200,pmpath = '.'):
        if nsims > nevpath: raise Exception("Pulling too many simulations compared to PathMaker")
        self.trial = trial
        self.tnm = trial.name
        self.kv = kapv
        self.kb = kapb
        self.km = kapm
        self.pe = perr
        self.nsim = nsims
        self.nevs = nevpath
        self.pm = loadPaths(trial,kapv,kapb,kapm,perr,nevpath,pmpath)
        self.e1 = end1type
        self.e2 = end2type
        self.pmpath = pmpath
        self.resetEvidence()

    def reconstructPaths(self):
        self.pm = loadPaths(self.trial,self.kv,self.kb,self.km,self.pe,self.nevs,self.pmpath)

    def resetEvidence(self):
        t = 0.
        self.obs = []
        self.bounces = []
        while t < self.pm.maxtm:
            o,bs = self.pm.getOutcomesAndBounces(t,self.nsim)
            self.obs.append(o)
            self.bounces.append(b)
            t += self.pm.pdist
        self.obs = timepaths
        self.ev = obs2Ev(self.obs,self.e1,self.e2)

        # Reset everything else
        self.cumev = None
        self.decs = None
        self.aggdec = None
        self.ptype1 = None
        self.ptype2 = None
        self.odec = None
        self.leak = None
        self.thresh = None
        self.toff = None
        self.twid = None
        self.sm = None

    def accumEv(self,leakage):
        self.leak = None
        self.cumev = []
        lasts = np.zeros(len(self.ev[0]))
        for i in range(len(self.ev)):
            lasts = lasts*(1-leakage) + self.ev[i]
            self.cumev.append(lasts)

    def setDecs(self,threshold):
        self.thresh = None
        self.decs = ev2Dec(self.cumev,threshold,self.e1,self.e2)
        self.aggdec = [countArray(d) for d in self.decs]
        self.ptype1 = []
        self.ptype2 = []
        for i in range(len(self.aggdec)):
            if self.e1 in self.aggdec[i].keys():
                self.ptype1.append(self.aggdec[i][self.e1] / self.nsim)
            else:
                self.ptype1.append(0.)
            if self.e2 in self.aggdec[i].keys():
                self.ptype2.append(self.aggdec[i][self.e2] / self.nsim)
            else:
                self.ptype2.append(0.)

    def setOffset(self,toff,twid,maxn = 101):
        self.toff = toff
        self.twid = twid
        self.sm = MakeSmoother(maxn, toff / self.pm.pdist, twid / self.pm.pdist)
        op1 = SmoothFromPre(self.ptype1,self.sm)
        op2 = SmoothFromPre(self,ptype2,self.sm)
        self.odec = [np.array([p1,p2,1.-p1-p2]) for p1,p2 in zip(op1,op2)]

    def setOffsetBySM(self,sm):
        self.sm = sm
        self.toff = sm['Offset'] * self.pm.pdist
        self.twid = sm['Width'] * self.pm.pdist
        op1 = SmoothFromPre(self.ptype1,self.sm)
        op2 = SmoothFromPre(self.ptype2,self.sm)
        self.odec = [np.array([p1,p2,1.-p1-p2]) for p1,p2 in zip(op1,op2)]

    def getDecisions(self):
        if self.odec is None: raise Exception('Decisions not yet set')
        return self.odec

    def save(self,flnm = None,asstring = False):
        # Delete the PathMaker - can always be reloaded
        self.pm = None
        if asstring:
            return pickle.dumps(self,protocol=2)
        else:
            if flnm is None:
                flnm = self.tnm + '_ea.eam'
            fl = open(flnm,'w')
            pickle.dump(self,fl,protocol=2)
            fl.close()

def loadEvidenceAccum(filename=None,serialized=None):
    if filename is not None and serialized is not None:
        raise Exception('Cannot load from both file and string!')
    if filename is None and serialized is None:
        raise Exception('Nothing to load!')
    if filename is not None:
        fl = open(filename,'rU')
        ea = pickle.load(fl)
        fl.close()
    else:
        ea = pickle.loads(serialized)
    ea.reconstructPaths()
    return ea


