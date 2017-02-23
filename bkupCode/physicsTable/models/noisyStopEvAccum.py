from __future__ import division
from matpltPygame import pgFig
from physicsTable import *
from physicsTable.constants import *
from physicsTable.utils import async_map, apply_async
from physicsTable.visualize import screenPause
from multiprocessing import cpu_count, Pool
import numpy as np
import scipy as sp
import pygame as pg
import os, sys, time
from smoothNShift import MakeSmoother, SmoothFromPre
import cPickle as pickle
from scipy.optimize import minimize, minimize_scalar

pathdir = 'PathFits'
trialdir = os.path.join('..','CriticalTables')
oldtrials = os.path.join('..','OldTrialsAndData')

DEFPATHMAKERPATHS = 200

def getCloudSD(points):
    # Make sure we have more than one point... otherwise doesn't work and just allows for continuous
    if len(points) == 1: return 0
    # Transform into numpy objects
    pts = map(np.array,points)
    # Get the mean
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    mean = np.array([np.mean(xs),np.mean(ys)])
    # Find distances & variance
    dists = [np.linalg.norm(p - mean) for p in pts]
    var = sum([d*d for d in dists])/(len(pts)-1)
    return np.sqrt(var)

def getCloudMean(points):
    pts = map(np.array,points)
    # Get the mean
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    return np.array([np.mean(xs),np.mean(ys)])

def makeFileName(trnm,kapv,kapb,kapm,perr,nsims,path = pathdir):
    kv = str(np.round(kapv))
    kb = str(np.round(kapb))
    km = str(np.round(kapm))
    pe = str(np.round(perr))
    pthname = kv + '_' + kb + '_' + km + '_' + pe + '_' + str(nsims)
    return os.path.join(path,pthname,trnm+'.pmo')

# Keep simulating until all paths hit or all paths diverge beyond a certain amount


# Structure for holding a) predictions b) evidence over time
class BeliefPath(object):
    def __init__(self, pmobj, npaths, maxvar, thresh, leakage):
        self.ev = []
        self.ts = []
        t = 0.
        running = True
        while running:
            if str(t) in pmobj.paths.keys():
                pth = pmobj.getPathsAndOutcomes(t,npaths)
                self.ev.append(self.getInstEvidence(pth,maxvar))
                self.ts.append(t)
                t += .1
            else:
                running = False
        self.cumev = self.accumulateEvidence(self.ev,leakage)
        self.decs = self.setDecisions(self.cumev,thresh)

    # Returns evidence (between -1 and 1) in favor of RED
    def getInstEvidence(self,paths,maxvar):
        pths = [p[1] for p in paths]
        npth = len(paths)
        maxlen = max(map(len,pths))
        i = 0
        while i < maxlen:
            ret = []
            pos = []
            for pth in paths:
                o,p = pth
                # If beyond the path, just return its last position
                if i >= len(p):
                    ret.append(o)
                    pos.append(p[-1])
                else:
                    ret.append(None)
                    pos.append(p[i])
            # Check that all paths don't diverge - skip to the end if they do
            if getCloudSD(pos) > maxvar:
                i = maxlen+1
            i += 1
        # Count up the evidence in favor of each path
        rev = sum([1 for r in ret if r == REDGOAL])
        gev = sum([1 for r in ret if r == GREENGOAL])
        # Return net evidence for RED
        return (rev - gev) / npth

    def accumulateEvidence(self,instev,leakage):
        last = 0
        cumev = []
        for ie in instev:
            last = last*(1-leakage) + ie
            cumev.append(last)
        return cumev

    def setDecisions(self,cumev,thresh):
        def getD(e):
            if e > thresh: return "R"
            elif e < -thresh: return "G"
            else: return "N"
        return [getD(e) for e in cumev]

# Like BeliefPath above, but allows for drawing to visualize
class DrawBeliefPath(object):
    def __init__(self, pmobj, npaths, maxvar, thresh, leakage, scdim):
        self.ev = []
        self.ts = []
        self.pm = pmobj
        self.npaths = npaths
        self.maxvar = maxvar
        self.thresh = thresh
        self.leak = leakage
        self.t = 0.
        self.pth = None
        self.pi = 0
        self.maxlen = 0
        self.dim = scdim
        self.curev = 0
        self.dec = 'N'

    # Returns [isbreak, (pathpos), instev, cumev, decision, screen]
    # Alternately, returns False if at the end
    def step(self):
        isbreak = False
        drawcontain = False
        if not str(self.t) in self.pm.paths.keys():
            return False # Nothing left
        # Find the paths & positions
        if self.pth is None:
            self.pth = self.pm.getPathsAndOutcomes(self.t,self.npaths)
            self.maxlen = max(map(lambda x: len(x[1]), self.pth))
        if self.pi < self.maxlen:
            ret = []
            pos = []
            for pth in self.pth:
                o,p = pth
                if self.pi >= len(p):
                    ret.append(o)
                    pos.append(p[-1])
                else:
                    ret.append(None)
                    pos.append(p[self.pi])
            if getCloudSD(pos) > self.maxvar:
                isbreak = True
                self.pi = self.maxlen+1
                drawcontain = True
            else:
                self.pi += 1
                drawcontain = False
        else:
            isbreak = True
            ret = [p[0] for p in self.pth]
            pos = [p[1][-1] for p in self.pth]
        # Make the screen
        sc = pg.Surface(self.dim)
        sc.set_colorkey((0,0,0)) # Black background is transparent
        if drawcontain:
            m = getCloudMean(pos)
            s2 = pg.Surface((self.maxvar*2,self.maxvar*2))
            pg.draw.circle(s2,(128,128,128),(self.maxvar,self.maxvar),self.maxvar,2)
            sc.blit(s2,(m[0]-self.maxvar,m[1]-self.maxvar))
        for p in pos:
            pg.draw.circle(sc,(0,0,255),p,5)
        # Get the evidence
        rev = sum([1 for r in ret if r == REDGOAL])
        gev = sum([1 for r in ret if r == GREENGOAL])
        iev = (rev - gev) / self.npaths

        # Update if there's a break point
        if isbreak:
            self.t += .1
            self.pth = None
            self.pi = 0
            self.curev = self.curev*(1-self.leak) + iev
            if self.curev > self.thresh: self.dec = 'R'
            elif self.curev < -self.thresh: self.dec = 'G'
            else: self.dec = 'N'
        return [isbreak, pos, iev, self.curev, self.dec, sc]

def runModel(trial,kapv,kapb,kapm,perr,npaths,maxvar,thresh,leakage,ntimes = 1, verbose = True):
    trpth = makeFileName(trial.name,kapv,kapb,kapm,perr,DEFPATHMAKERPATHS)
    if not os.path.exists(trpth):
        if verbose: print 'Nothing existing for trial ' + trial.name +'; making now'
        trdir = os.path.dirname(trpth)
        if not os.path.exists(trdir): os.mkdir(trdir)
        pm = PathMaker(trial,kapv,kapb,kapm,perr,DEFPATHMAKERPATHS)
        pm.save(trpth)
    else:
        pm = loadPathMaker(trpth)
    if verbose: print "Paths loaded"
    rets = []
    for n in range(ntimes):
        bp = BeliefPath(pm,npaths,maxvar,thresh,leakage)
        rets.append(bp)
    if verbose: print "Evidence accumulated"
    reddecs = []
    greendecs = []
    nonedecs = []
    for i in range(len(rets[0].ts)):
        ds = [r.decs[i] for r in rets]
        reddecs.append(np.mean([d == 'R' for d in ds]))
        greendecs.append(np.mean([d == 'G' for d in ds]))
        nonedecs.append(np.mean([d == 'N' for d in ds]))
    decs = dict()
    decs['R'] = reddecs
    decs['G'] = greendecs
    decs['N'] = nonedecs
    return (decs, rets)

def drawModel(screen, trial,kapv,kapb,kapm,perr,npaths,maxvar,thresh,leakage,withpause = True):
    pm = loadPaths(trial,kapv,kapb,kapm,perr)
    evs = []
    decs = []
    ts = []
    t = 0.
    screen.fill((255,255,255))
    tab = trial.makeTable(soffset=(0,0))
    dbp = DrawBeliefPath(pm,npaths,maxvar,thresh,leakage,trial.dims)
    clk = pg.time.Clock()
    pgf = pgFig((trial.dims[0]/100,2))
    pgf.plot([0],[0])
    pgf.axhline(thresh,linestyle='--',color='red')
    pgf.axhline(-thresh,linestyle='--',color='green')
    pgf.xlim(0,10)
    pgf.ylim(-thresh-.5,thresh + .5)
    screen.blit(pgf.draw(),(0,trial.dims[1]))
    while True:
        s = dbp.step()
        if s is False:
            return
        brk, pos, iev, cev, dec, bpsc = s
        tab.draw()
        screen.blit(bpsc,(0,0))
        pg.display.flip()
        clk.tick(20)
        if brk:
            ts.append(t)
            t += .1
            evs.append(cev)
            decs.append(dec)
            pgf = pgFig((trial.dims[0]/100,2))
            pgf.plot(ts,evs)
            ymin = np.min([np.min(evs),-thresh-.5])
            ymax = np.max([np.max(evs),thresh+.5])
            pgf.axhline(thresh,linestyle='--',color='red')
            pgf.axhline(-thresh,linestyle='--',color='green')
            pgf.xlim(0,10)
            pgf.ylim(ymin,ymax)
            screen.blit(pgf.draw(),(0,trial.dims[1]))
            pg.display.flip()
            if withpause: screenPause(.1)
            tab.step(.1)

def loadPaths(trial,kapv,kapb,kapm,perr,path = pathdir):
    trpth = makeFileName(trial.name,kapv,kapb,kapm,perr,DEFPATHMAKERPATHS,path)
    if not os.path.exists(trpth):
        print 'Nothing existing for trial ' + trial.name +'; making now'
        trdir = os.path.dirname(trpth)
        if not os.path.exists(trdir): os.makedirs(trdir)
        pm = PathMaker(trial,kapv,kapb,kapm,perr,DEFPATHMAKERPATHS)
        pm.save(trpth)
    else:
        pm = loadPathMaker(trpth)
    return pm

# Functions for fitting auxiliary parameters [npaths,maxvar,thresh,leakage,toff,twid]
def offsetDecs(decs, smoother):

    rs, gs, pas, prgas = decs

    ors = SmoothFromPre(rs,smoother)
    ogs = SmoothFromPre(gs,smoother)
    opas = ors+ogs
    oprgas = safeDivide(ors,opas)

    return [ors, ogs, opas, oprgas]

def safeDivide(x,y):
    if y < .00000001: return .5
    else: return x/y
safeDivide = np.vectorize(safeDivide)

def getInstEvidence(paths,maxvar):
    pths = [p[1] for p in paths]
    npth = len(paths)
    maxlen = max(map(len,pths))
    i = 0
    while i < maxlen:
        ret = []
        pos = []
        for pth in paths:
            o,p = pth
            # If beyond the path, just return its last position
            if i >= len(p):
                ret.append(o)
                pos.append(p[-1])
            else:
                ret.append(None)
                pos.append(p[i])
        # Check that all paths don't diverge - skip to the end if they do
        if getCloudSD(pos) > maxvar:
            i = maxlen+1
        i += 1
    # Count up the evidence in favor of each path
    rev = sum([1 for r in ret if r == REDGOAL])
    gev = sum([1 for r in ret if r == GREENGOAL])
    # Return net evidence for RED
    return (rev - gev) / npth

# Functions that need to be rewritten outside of the NSS class to take advantage of parallelization
def NSSsetEvidence(pm,npaths,maxvar,ntimes):
    def setOne():
        ev = []
        t = 0.
        running = True
        while running:
            if str(t) in pm.paths.keys():
                pth = pm.getPathsAndOutcomes(t,npaths)
                ev.append(getInstEvidence(pth,maxvar))
                t += .1
            else:
                running = False
        return ev
    return [setOne() for i in range(ntimes)]

class NoisyStopEvAccum(object):
    def __init__(self,empdat,triallist,kapv,kapb,kapm,perr,nsims=200,ncpu = cpu_count(),pmpath = pathdir):
        # Load everything in
        self.emp = empdat
        self.trs = triallist
        self.tnms = triallist.keys()
        self.ncpu = ncpu
        self.pmpath = pmpath
        pms = map(lambda t: loadPaths(self.trs[t],kapv,kapb,kapm,perr,pmpath),self.tnms)
        self.pms = dict(zip(self.tnms,pms))
        self.kv = kapv
        self.kb = kapb
        self.km = kapm
        self.pe = perr
        self.nsims = nsims

        # Set all things to set & fit to null
        self.npaths = None
        self.maxvar = None
        self.leak = None
        self.thresh = None
        self.toff = None
        self.twid = None
        self.llh = None
        self.evs = None
        self.cumev = None
        self.fulldecs = None
        self.decs = None
        self.osets = None

    def setEvidence(self,npaths,maxvar,setpar = True):
        if setpar:
            self.npaths = npaths
            self.maxvar = maxvar
        nsims = self.nsims
        tnms = self.tnms
        ncpu = self.ncpu

        P = Pool(self.ncpu)
        jobs = []
        for tr in self.tnms:
            pm = self.pms[tr]
            def f():
                return NSSsetEvidence(pm,npaths,maxvar,nsims)
            jobs.append(apply_async(P,f, () ))
        evs = [j.get() for j in jobs]

        #def setE(tr): NSSsetEvidence(pms[tr],npaths,maxvar,nsims)
        #evs = async_map(setE,tnms,ncpu)
        self.evs = dict(zip(self.tnms,evs))

    def setCumEv(self,leakage, setpar = True):
        if setpar: self.leak = leakage
        rem = 1 - leakage
        if self.evs is None: raise Exception('Cannot set cumulative evidence without evidence first')
        def setem(ev):
            cumev = np.zeros(len(ev))
            cumev[0] = ev[0]
            for i in range(1,len(ev)):
                cumev[i] = cumev[i-1]*rem + ev[i]
            return cumev
        def setmany(tr):
            return [setem(e) for e in self.evs[tr]]
        cums = map(setmany,self.tnms)
        self.cumev = dict(zip(self.tnms,cums))
        return

    def setDecs(self,thresh,setpar = True):
        if setpar: self.thresh = thresh
        if self.cumev is None: raise Exception("Cannot set decisions without cumulative evidence")
        def setem(cev):
            decs = []
            for c in cev:
                if c < -thresh: decs.append('G')
                elif c > thresh: decs.append('R')
                else: decs.append('U')
            return decs
        def setmany(tr):
            return [setem(ce) for ce in self.cumev[tr]]
        #decs = async_map(setmany,self.tnms,self.ncpu)
        decs = map(setmany,self.tnms)
        self.fulldecs = dict(zip(self.tnms,decs))
        # Aggregate over trials to get p(red/green/none/rga) for all trials
        def aggdecs(tr):
            alldecs = self.fulldecs[tr]
            plen = len(alldecs[0])
            rdecs = []
            gdecs = []
            udecs = []
            for i in range(plen):
                rs = 0
                gs = 0
                us = 0
                for s in range(self.nsims):
                    if alldecs[s][i] == 'R': rs += 1
                    elif alldecs[s][i] == 'G': gs += 1
                    elif alldecs[s][i] == 'U': us += 1
                    else: raise Exception('Uh oh should not be here')
                rdecs.append(rs / self.nsims)
                gdecs.append(gs / self.nsims)
                udecs.append(us / self.nsims)
            rdecs = np.array(rdecs)
            gdecs = np.array(gdecs)
            adecs = rdecs + gdecs
            rgas = safeDivide(rdecs, adecs)
            return [rdecs,gdecs,adecs,rgas]
        self.decs = dict([(tr,aggdecs(tr)) for tr in self.tnms])
        return

    def offsetTime(self,toff,twid, setpar = True):
        if self.decs is None: raise Exception('Need to set decisions first')
        sm = MakeSmoother(101,toff*10,twid*10)
        if setpar:
            self.toff = toff
            self.twid = twid
            self.sm = sm
        osets = map(lambda t: offsetDecs(self.decs[t],sm),self.tnms)
        #print self.decs[self.tnms[0]]
        #osets = map(lambda t: offsetDecs(self.decs[t],sm),self.tnms)
        self.osets = dict(zip(self.tnms,osets))

    def getLLH(self, prior = None):
        if self.osets is None: raise Exception('Need offsets to get LLH')
        llh = 0
        for tr in self.tnms:
            decs = self.osets[tr]
            emp = self.emp[tr]
            # Adjust likelihoods by a slight prior to ensure well-formedness
            if prior is None: prior = 1 / self.nsims # Like one observation of each type
            pr = np.array(decs[0])
            pg = np.array(decs[1])
            pu = 1 - np.array(decs[2])

            pr = (pr + prior) / (1+3*prior)
            pg = (pg + prior) / (1+3*prior)
            pu = (pu + prior) / (1+3*prior)

            # Add in each of the decision likelihoods
            llh += sum(np.array(emp['R'])*np.log(pr))
            llh += sum(np.array(emp['G'])*np.log(pg))
            llh += sum(np.array(emp['U'])*np.log(pu))
        self.llh = llh
        return llh

    def save(self,flnm = None):
        if flnm is None:
            flnm = "NoisyStop_" + str(self.npaths) + '_' + str(round(self.maxvar,0)) + '_' + str(round(self.thresh,3)) + '_'
            flnm += str(round(self.leak,3)) + '_' + str(round(self.toff,3)) + '_' + str(round(self.twid,3)) + '.nss'
        flnm = os.path.join(self.pmpath,flnm)
        # Remove existing PathMakers (for space)
        pms = self.pms
        self.pms = None
        ofl = open(flnm,'w')
        pickle.dump(self,ofl,protocol=2)
        self.pms = pms
        ofl.close()
        return flnm

    def fitTimeParams(self, initpar = (1.,0.5), ftol = .05):
        def fit(p):
            toff, twid = p
            self.offsetTime(toff,twid,False)
            return -self.getLLH()
        o = minimize(fit, initpar, method = 'L-BFGS-B', bounds = [(.0001, 2.), (.0001, 2.)], options={'ftol':ftol})
        toff, twid = o.x
        self.offsetTime(toff,twid)
        return self.getLLH()

    def fitThreshParam(self, tol = .05):
        def fit(th):
            self.setDecs(th,False)
            return -self.fitTimeParams()
        o = minimize_scalar(fit,bounds = [0.001,10], tol = tol)
        return o

    def fitNonPathPicks(self, initpar = (1.,.2,1.,0.5), ftol = .05):
        bnds = [(.001,10),(0.0,1.0),(.0001,2.),(.0001,2.)]
        def fit(p):
            thresh, rleak, toff, twid = p
            if thresh < bnds[0][0] or thresh > bnds[0][1]: return 99999999999
            if rleak < bnds[1][0] or thresh > bnds[1][1]: return 99999999999
            if toff < bnds[2][0] or thresh > bnds[2][1]: return 99999999999
            if twid < bnds[3][0] or thresh > bnds[3][1]: return 99999999999
            maxleak = 1. / max(1,thresh)
            leak = rleak*maxleak
            self.setCumEv(leak,False)
            self.setDecs(thresh,False)
            self.offsetTime(toff,twid,False)
            return -self.getLLH()
        o = minimize(fit,initpar,method='Nelder-Mead',options={'ftol':ftol,'disp':True})
        thresh, rleak, toff, twid = o.x
        maxleak = 1. / max(1,thresh)
        leak = rleak*maxleak
        print o.x
        self.setCumEv(leak)
        self.setDecs(thresh)
        self.offsetTime(toff,twid)
        return self.getLLH()

def loadNoisyStopSim(flnm):
    ifl = open(flnm,'rU')
    nss = pickle.load(ifl)
    ifl.close()
    # Readd PathMakers
    rpms = map(lambda t: loadPaths(nss.trs[t],nss.kv,nss.kb,nss.km,nss.pe,nss.pmpath),nss.tnms)
    nss.pms = dict(zip(nss.tnms,rpms))
    return nss
