from __future__ import division
from ..noisyTable import *
from ..utils import async_map
from multiprocessing import cpu_count
import numpy as np

class PointSimulation(object):
    
    def __init__(self,table, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, ensure_end = False, nsims = 200, maxtime = 50., cpus = cpu_count(), timeres = 0.05):
        self.tab = table
        self.kapv = kapv
        self.kapb = kapb
        self.kapm = kapm / np.sqrt(timeres / 0.001) # Correction for the fact that we're simulating fewer steps and thus jitter must be noisier (by approx sqrt of number of steps)
        self.perr = perr
        self.maxtime = maxtime
        self.nsims = nsims
        self.ts = timeres
        
        self.outcomes = None
        self.endpts = None
        self.bounces = None
        self.run = False
        self.enend = ensure_end
        
        self.ucpus = cpus
        self.badsims = 0
        
    
    def singleSim(self, i):
        n = makeNoisy(self.tab,self.kapv,self.kapb,self.kapm,self.perr)
        n.set_timestep(self.ts)
        r = n.simulate(self.maxtime)
        p = n.balls.getpos()
        nb = n.balls.bounces
        rp = (p[0],p[1])
        if self.enend:
            if r == TIMEUP:
                self.badsims += 1
                return(self.singleSim(i))
            if rp[0] < 0 or rp[0] > self.tab.dim[0] or rp[1] < 0 or rp[1] > self.tab.dim[1]:
                self.badsims += 1
                return(self.singleSim(i))
        return [r, rp, nb, n.tm]
    
    def runSimulation(self):
        
        ret = async_map(self.singleSim,range(self.nsims), self.ucpus)
        
        self.outcomes = [r[0] for r in ret]
        self.endpts = [r[1] for r in ret]
        self.bounces = [r[2] for r in ret]
        self.tsims = [r[3] for r in ret]
        self.run = True
        
        return [self.outcomes, self.endpts, self.bounces, self.tsims]
        
    def getOutcomes(self):
        if not self.run: raise Exception('Cannot get simulation outcome without running simulations first')
        retdict = dict([(r,0) for r in self.tab.goalrettypes])
        for o in self.outcomes:
            retdict[o] += 1
        
        return retdict

    def getEndpoints(self, xonly = False, yonly = False):
        if not self.run: raise Exception('Cannot get simulation endpoints without running simulations first')
        if xonly and not yonly:
            return [p[0] for p in self.endpts]
        if yonly and not xonly:
            return [p[1] for p in self.endpts]
        return self.endpts

    def getBounces(self):
        if not self.run: raise Exception('Cannot get simulation outcome without running simulations first')
        return self.bounces

    def getTimes(self):
        if not self.run: raise Exception('Cannot get simulation outcome without running simulations first')
        return self.tsims

    def replaceOutcomes(self, badoutcomes = [TIMEUP, OUTOFBOUNDS],printout = False):
        # Find the indices of all places where the outcomes are bad
        idxs = [x[0] for x in enumerate(self.outcomes) if badoutcomes.count(x[1]) > 0]
        if len(idxs) == 0: return None

        if printout: print "Resimulating",len(idxs),"times"

        ret = async_map(self.singleSim,range(len(idxs)), self.ucpus)
        for i in range(len(idxs)):
            idx = idxs[i]
            self.outcomes[idx] = ret[i][0]
            self.endpts[idx] = ret[i][1]
            self.bounces[idx] = ret[i][2]
            self.tsims[idx] = ret[i][3]
        self.replaceOutcomes(badoutcomes,printout)

