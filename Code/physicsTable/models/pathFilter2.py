from __future__ import division
import os, sys, time, copy, bisect, random

from ..noisyTable import *
from ..trials import *
from ..utils import *
from ..constants import UNCERTAIN
from ..pathMaker import Path, PathMaker, loadPathMaker, makeFileName
from scipy.stats import norm
import numpy as np

def selectReplace(items, weights, n):
    if len(items) != len(weights): raise(Exception("Needs equal number of items, weights"))
    cumw = [sum(weights[:(x+1)]) for x in range(len(weights))]
    return [items[bisect.bisect(cumw,random.random()*max(cumw))] for _ in range(n)]


class pfPath(object):

    def __init__(self,path):
        self.path = path

    # Get the probability of observing the ball given the current path
    #  Can somewhat account for occlusion
    def get_p(self, t, ballpos, ballrad, errsd, iscovered = False, walls = [], occluders = []):
        p = self.path
        pos = p.getpos(t)
        if not iscovered:
            dist = euclidist(pos, ballpos)
            return norm.pdf(dist,loc = 0,scale = errsd)
        else:
            # If the particle is in the goal while the ball is covered, it shouldn't be
            idx = int((t - p.inittime) / self.tps)
            if idx > len(p.path):
                return 1e-100

            # If the ball is covered, the particle should test vs probability that it should be covered
            covmat = np.array([[errsd,0],[0,errsd]])
            brad = int(ballrad)
            blocked = []
            for w in walls:
                 blocked.append(w.inflate(2*brad,2*brad))

            p = 0
            #ps = []

            # Break up occluders into non-overlapping, then run
            uoccs = uniqueOccs(map(lambda x: x, occluders), blocked)
            for o in uoccs:
                lefto = o.left
                righto = o.right
                topo = o.top
                boto = o.bottom
                p += mvnormcdf([lefto,topo],[righto,boto],pos,covmat)
                #ps.append(p)

            return p

    # Get a list of ball paths until the end
    def get_path(self,t):
        pth = []
        while True:
            np = self.path.getpos(t)
            if np is not None:
                pth.append(np)
                t += self.path.ts
            else:
                return pth

    # Get the current position of the ball on the path
    def get_pos(self, t):
        return self.path.getpos(t)

    def get_outcome(self):
        return self.path.o

    def get_bounces(self):
        return self.path.b

    outcome = property(get_outcome)
    bounces = property(get_bounces)



class PathFilter(object):
    def __init__(self,trial,**args):
        argnms = args.keys()

        trnm = trial.name
        # Set required trial info
        self._brad = trial.ball[2]

        # Set simulation parameters
        kapv = args.get('kapv',KAPV_DEF)
        kapb = args.get('kapb',KAPB_DEF)
        kapm = args.get('kapm',KAPM_DEF)
        perr = args.get('perr',PERR_DEF)
        nsims = args.get('nsims',200)
        tps = args.get('timeperstep',0.1)
        tres = args.get('simtimeres',0.05)
        tlim = args.get('timelim',60.)
        ncpu = args.get('ncpu', 1)

        # Either load the existing PathMaker or make a new one
        if 'flnm' in argnms:
            flnm = args['flnm']
            hasnm = True
        else:
            flnm = makeFileName(trnm,kapv,kapb,kapm,perr,nsims,'.')
            hasnm = False

        if 'pathmaker' in argnms:
            self._pm = args['pathmaker']
            kapv = self._pm.kv
            kapb = self._pm.kb
            kapm = self._pm.km
            perr = self._pm.pe
        elif os.path.exists(flnm) and hasnm:
            self._pm = loadPathMaker(flnm)
            kapv = self._pm.kv
            kapb = self._pm.kb
            kapm = self._pm.km
            perr = self._pm.pe
        else:
            print 'No PathMaker object exists... creating now - please be patient!'
            self._pm = PathMaker(trial,kapv,kapb,kapm,perr,nsims,tps,tlim,tres,ncpu)
            self._pm.save(flnm)

        # Load the decision parameters
        self._newpct = args.get('newpct', 10e-7)
        self._obserr = args.get('obserr', perr)
        self._temp = args.get('temp', 0.2)
        self._sure = args.get('min_sure', 0.99)
        self._endconds = args.get('endconds', None)
        self._npath = args.get('npaths', 10)

        self._tr = trial
        self._table = self._tr.makeTable()
        # Temporary kludge... can't use wonky walls with occluders
        for w in self._table.walls:
             if w.shapetype != SHAPE_RECT:
                 if len(self._table.occludes) > 0: raise Exception('Path filters require walls to be rectangular or no occlusions - do not use AbnormWalls')

        self._kv = kapv
        self._kb = kapb
        self._km = kapm
        self._pe = perr
        self._t = 0.

        self._ncpu = ncpu
        self._tps = tps
        self._tres = tres
        self._tlim = 60.

        self._make_obs()
        self.reset()

    def sample_path(self,t):
        return pfPath(self._pm.getSinglePath(t))

    def get_n_paths(self):
        return len(self._paths)

    # Runs the table forwards once so you don't have to keep re-physicsing
    def _make_obs(self):
        self._observations = {}
        self._occludes = {}
        t = 0.
        tab = self._tr.makeTable()
        self._tabwalls = copy.deepcopy([w.r for w in tab.walls])
        self._taboccs = copy.deepcopy([o.r for o in tab.occludes])
        r = None
        while r is None:
            self._observations[t] = tab.balls.getpos()
            self._occludes[t] = tab.fullyOcc()
            r = tab.step(self._tps)
            t += self._tps
        self._outcome = r

    # Goes back to the beginning for another round
    def reset(self):
        #self._table = self._tr.makeTable()
        self._t = 0.
        self._paths = [self.sample_path(0.) for _ in range(self._npath)]
        self._weights = np.array([1 / self._npath for _ in range(self._npath)])

    # Steps the world forward, updates the path filter
    def step(self):

        # 1) Get the ball position at the new time - end if the ball has hit the end
        self._t += self._tps
        if self._t not in self._observations.keys():
            return self._outcome, self.get_decision()
        bpos = self._observations[self._t]

        # 2) Calculate the particle probabilities
        part_ps = self.get_part_ps(bpos, self._t, self._occludes[self._t])

        # 3) Resample paths based on probabilities (plus regen)
        self.resample_paths(part_ps)

        # 4) Calculate the total weight attributed to each decision and test if enough
        dec = self.get_decision()

        return None, dec

    # Runs a single path
    def run_path(self):
        self.reset()
        decs = []
        while True:
            r, dec = self.step()
            decs.append(dec)
            if r is not None:
                return decs

    # Get a vector of probabilities of the particles for a given ball position
    def get_part_ps(self, ballpos, t, occluded = False):
        return np.array([p.get_p(t, ballpos, self._brad, self._obserr, occluded, self._tabwalls, self._taboccs) \
                for p in self._paths])

    # Given a set of path probabilities, reweight, and regenerate if needed
    def resample_paths(self, probs):
        pidxs = range(len(self._paths)) + [-1]
        pwts = list(np.power(probs * self._weights, self._temp)) + [self._newpct]
        pwts = [w/(sum(pwts)) for w in pwts]
        newidxs = selectReplace(pidxs, pwts, self._npath)
        newidxs.sort()
        nextparts = []
        nextweights = []
        lastidx = -1
        for i in newidxs:
            if i == -1:
                nextparts.append(self.sample_path(self._t))
                nextweights.append(1. / self._npath)
            else:
                if i == lastidx:
                    nextweights[-1] += 1. / self._npath
                else:
                    nextparts.append(self._paths[i])
                    nextweights.append(1. / self._npath)
                    lastidx = i
        self._paths = nextparts
        self._weights = np.array(nextweights)

    # Counts up path weights and determines whether it is enough to make a decision
    def get_decision(self):
        odict = self.get_outcome_beliefs()
        for o,w in odict.items():
            if w >= self._sure:
                return o
        return UNCERTAIN

    def get_outcome_beliefs(self):
        ocomes = [p.outcome for p in self._paths]
        odict = {}
        for o, w in zip(ocomes, self._weights):
            if o not in odict:
                odict[o] = 0.
            odict[o] += w
        return odict
