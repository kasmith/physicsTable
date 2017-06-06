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
    def getP(self, t, ballpos, ballrad, errsd, iscovered = False, walls = [], occluders = []):
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
                 blocked.append(w.r.inflate(2*brad,2*brad))

            p = 0
            #ps = []

            # Break up occluders into non-overlapping, then run
            uoccs = uniqueOccs(map(lambda x: x.r, occluders), blocked)
            for o in uoccs:
                lefto = o.left
                righto = o.right
                topo = o.top
                boto = o.bottom
                p += mvnormcdf([lefto,topo],[righto,boto],pos,covmat)
                #ps.append(p)

            return p

    # Get a list of ball paths until the end
    def getPath(self,t):
        pth = []
        while True:
            np = self.path.getpos(t)
            if np is not None:
                pth.append(np)
                t += self.path.ts
            else:
                return pth

    # Get the current position of the ball on the path
    def getPos(self, t):
        return self.path.getpos(t)

    def getOutcome(self):
        return self.path.o

    def getBounces(self):
        return self.path.b

    outcome = property(getOutcome)
    bounces = property(getBounces)



class PathFilter(object):
    def __init__(self,trial,**args):
        argnms = args.keys()

        trnm = trial.name
        # Set required trial info
        self.brad = trial.ball[2]

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
            self.pm = args['pathmaker']
            kapv = self.pm.kv
            kapb = self.pm.kb
            kapm = self.pm.km
            perr = self.pm.pe
        elif os.path.exists(flnm) and hasnm:
            self.pm = loadPathMaker(flnm)
            kapv = self.pm.kv
            kapb = self.pm.kb
            kapm = self.pm.km
            perr = self.pm.pe
        else:
            print 'No PathMaker object exists... creating now - please be patient!'
            self.pm = PathMaker(trial,kapv,kapb,kapm,perr,nsims,tps,tlim,tres,ncpu)
            self.pm.save(flnm)

        # Load the decision parameters
        self.newpct = args.get('newpct', 10e-7)
        self.obserr = args.get('obserr', perr)
        self.temp = args.get('temp', 0.2)
        self.sure = args.get('min_sure', 0.99)
        self.endconds = args.get('endconds', None)
        self.npart = args.get('npaths', 10)

        self.tr = trial
        self.table = self.tr.makeTable()
        # Temporary kludge... can't use wonky walls with occluders
        for w in self.table.walls:
             if w.shapetype != SHAPE_RECT:
                 if len(self.table.occludes) > 0: raise Exception('Path filters require walls to be rectangular or no occlusions - do not use AbnormWalls')

        self.kv = kapv
        self.kb = kapb
        self.km = kapm
        self.pe = perr
        self.t = 0.

        self.ncpu = ncpu
        self.tps = tps
        self.tres = tres
        self.tlim = 60.

        self.paths = [self.samplePath(0.) for _ in range(self.npart)]
        self.weights = np.array([1/self.npart for _ in range(self.npart)])

    def samplePath(self,t): return pfPath(self.pm.getSinglePath(t))

    def getNPaths(self):
        return len(self.paths)

    # Goes back to the beginning for another round
    def reset(self):
        self.table = self.tr.makeTable()
        self.t = 0.
        self.paths = [self.samplePath(0.) for _ in range(self.npart)]
        self.weights = np.array([1 / self.npart for _ in range(self.npart)])

    # Steps the world forward, updates the path filter
    def step(self, stepsize = None):
        if stepsize is None:
            stepsize = self.tps

        # 1) Step the world forward and calculate the new ball position
        r = self.table.step(stepsize)
        self.t += stepsize
        bpos = self.table.balls.getpos()

        # 2) Calculate the particle probabilities
        part_ps = self.getPartPs(bpos, self.t, self.table.fullyOcc())

        # 3) Resample paths based on probabilities (plus regen)
        self.resamplePaths(part_ps)

        # 4) Calculate the total weight attributed to each decision and test if enough
        dec = self.getDecision()

        return r, dec

    # Runs a single path
    def runPath(self):
        self.reset()
        decs = []
        while True:
            r, dec = self.step()
            decs.append(dec)
            if r is not None:
                return decs

    # Get a vector of probabilities of the particles for a given ball position
    def getPartPs(self, ballpos, t, occluded = False):
        return np.array([p.getP(t, ballpos, self.brad, self.obserr, occluded, self.table.walls, self.table.occludes) \
                for p in self.paths])

    # Given a set of path probabilities, reweight, and regenerate if needed
    def resamplePaths(self, probs):
        pidxs = range(len(self.paths)) + [-1]
        pwts = list(np.power(probs * self.weights, self.temp)) + [self.newpct]
        pwts = [w/(sum(pwts)) for w in pwts]
        newidxs = selectReplace(pidxs, pwts, self.npart)
        newidxs.sort()
        nextparts = []
        nextweights = []
        lastidx = -1
        for i in newidxs:
            if i == -1:
                nextparts.append(self.samplePath(self.t))
                nextweights.append(1. / self.npart)
            else:
                if i == lastidx:
                    nextweights[-1] += 1. / self.npart
                else:
                    nextparts.append(self.paths[i])
                    nextweights.append(1. / self.npart)
                    lastidx = i
        self.paths = nextparts
        self.weights = np.array(nextweights)

    # Counts up path weights and determines whether it is enough to make a decision
    def getDecision(self):
        ocomes = [p.outcome for p in self.paths]
        odict = {}
        for o,w in zip(ocomes, self.weights):
            if o not in odict:
                odict[o] = 0.
            odict[o] += w
        for o,w in odict.items():
            if w >= self.sure:
                return o
        return UNCERTAIN

'''
class PathFilter(object):
    
    def __init__(self, table, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, nparticles = 5, newpct = 10e-7, temp = .2, timelim = 10., timeperstep = .05, min_sure = .99, endconds = None):
        # CHECK THAT TABLE DOESN"T HAVE ABNORMAL WALLS
        for w in table.walls:
             if w.shapetype != SHAPE_RECT:
                 if len(table.occludes) > 0: raise Exception('Path filters require walls to be rectangular or no occlusions - do not use AbnormWalls')
        
        if endconds is None: self.endconds = table.goalrettypes
        else: self.endconds = endconds
        
        self.table = table
        self.kv = kapv
        self.kb = kapb
        self.km = kapm
        self.pe = perr
        self.npart = nparticles
        self.tps = timeperstep
        self.t = 0.
        
        self.particles = [Path(self.table, self.kv, self.kb, self.km, self.pe, self.endconds, self.tps) for i in range(nparticles)]
        
        self.lastseen = table.balls.getpos()
        self.lastseent = 0.
        self.newp = newpct
        self.temp = temp
        self.tlim = timelim
        self.sure = min_sure
        self.getPartPs()

    def getPartPs(self):
        return map(lambda p: p.getP(self), self.particles)
        
    def getPartPos(self):
        return map(lambda p: p.getpos(self.t), self.particles)
    
    def getDecision(self, ps = None):
        decs = map(lambda p: p.getdecision(self.t, self.tlim), self.particles)
        if ps is None: ps = self.getPartPs()
        
        decps = dict([(tp,0.) for tp in self.endconds])
        totp = 0
        for d, p in zip(decs, ps):
            decps[d] += p
            totp += p
            
        for k in decps.keys():
            if (decps[k]/totp) > self.sure: return k
        
        return UNCERTAIN
    
    def step(self):
        r = self.table.step(self.tps)
        self.t += self.tps
        if not self.table.fullyOcc():
            self.lastseent = self.t
            self.lastseen = map(int, self.table.balls.getpos())
        
        weights = [p.weight for p in self.particles]
        ps = self.getPartPs()
        newws = [w*p for w,p in zip(weights,ps)]
        newws.append(self.newp)
        newws = map(lambda x: np.power(x, self.temp), newws)
        totw = sum(newws)
        newws = map(lambda x: x/totw, newws)
        newparts = copy.copy(self.particles)
        newparts.append("Empty")
        newps = selectReplace(newparts,newws, len(self.particles))
        for i in range(len(newps)):
            if newps[i] == 'Empty': newps[i] = Path(self.table, self.kv, self.kb, self.km, self.pe, self.endconds, self.tps, self.lastseent, self.lastseen)
        for pt in self.particles:
            if pt not in newps: del(pt) # For memory reasons, clean up old (unused) paths
        for p in newps: p.weight = 1
        self.particles = newps
        return r

    # MOVE TO VISUALIZATION
    def draw(self, drawlines = False):
        sc = self.table.draw()
        for part, p in zip(self.particles, self.getPartPs()):
            dec = part.getdecision(self.t)
            if dec == REDGOAL: col = RED
            elif dec == GREENGOAL: col = GREEN
            elif dec == BLUEGOAL: col = BLUE
            elif dec == YELLOWGOAL: col = YELLOW
            elif dec == UNCERTAIN or dec == TIMEUP: col = GREY
            else: col = BLACK
            
            rad = 15 + int(np.log(p))
            if rad < 2: rad = 2
            pg.draw.circle(sc,col,map(int,part.getpos(self.t)),rad)
            if drawlines:
                pth = part.getPath(self.t,self.tlim)
                if len(pth) > 1: pg.draw.lines(sc, col, False, pth)
        return sc
    
    def makeMovie(self, moviename, outputdir = '.', removeframes = True):
        fps = int(1 / self.tps)
        timeperframe = self.tps
        try:
            subprocess.call('ffmpeg')
            print 'ffmpeg installed'
        except:
            print 'ffmpeg not installed - required to make movie'
            return None
        pthnm = os.path.join(outputdir, 'tmp_' + moviename)
        if not os.path.isdir(pthnm):
            os.mkdir(pthnm)
        
        if os.listdir(pthnm) != []:
            print "Files exist in temporary directory", pthnm,'; delete and try again'
            return None
        
        tnmbase = os.path.join(pthnm, moviename+'_%04d.png')
        
        pg.image.save(self.draw(True),tnmbase % 0)
        i = 1
        running = True
        while running:
            e = self.step()
            pg.image.save(self.draw(True),tnmbase % i)
            i += 1
            
            if e is not None: running = False
        
        
        ffcall = 'ffmpeg -r ' + str(fps) + ' -i ' + tnmbase + ' -pix_fmt yuv420p ' + os.path.join(outputdir, moviename + '.mov')
        ffargs = shlex.split(ffcall)
        print ffargs
        subprocess.call(ffargs)
        
        if removeframes:
            shutil.rmtree(pthnm)
    '''

'''
class Path(object):
    def __init__(self, parenttable, kv, kb, km, pe, endconds, timeperstep = 1/100., inittime = 0., spos = None, toff = 0.):
        if spos is None: self.pos = parenttable.balls.getpos()
        else: self.pos = spos
        self.v = parenttable.balls.getvel()
        kmadj = timeperstep / parenttable.basicts
        self.tab = makeNoisy(parenttable, kv, kb, km*kmadj, pe)
        self.tab.set_timestep(timeperstep)
        self.inittime = inittime
        self.tps = timeperstep
        self.endconds = endconds
        self.weight = 1.
        self.setpath()


    def setpath(self, limittime = 26.):
        ntab = self.tab
        b = ntab.addBall(pm.Vec2d(self.pos), self.v, dispwarn = False)
        tbhz = 1 / ntab.basicts
        capturesteps = int(limittime / self.tps)
        #limitsteps = int(limittime / tbhz)

        self.path = [b.getpos()]

        for i in range(1,capturesteps):
            r = ntab.step(self.tps, maxtime = limittime)
            self.path.append(b.getpos())
            if r in self.endconds:
                self.end = r
                self.timedec = self.inittime + (i * ntab.basicts)
                return self.path
        self.end = TIMEUP
        self.timedec = self.inittime + limittime
        del(self.tab) # For memory reasons, get rid of the table
        return self.path

    def getpos(self,t):
        if t < self.inittime: raise Exception("Cannot call position from before simulation starts")
        idx = int( (t - self.inittime) / self.tps)
        if idx >= len(self.path): return self.path[-1]
        return self.path[idx]

    def getdecision(self, curtime, tlimit = 10.):
        if self.timedec > (curtime + tlimit): return TIMEUP
        return self.end

    def getPath(self, t, tlimit = 10.):
        begidx = int( (t - self.inittime) / self.tps)
        endidx = int( (t - self.inittime + tlimit) / self.tps)
        if endidx > len(self.path): endidx = len(self.path)
        return self.path[begidx:endidx]

    def getP(self, parentmodel):
        pos = self.getpos(parentmodel.t)
        if not parentmodel.table.fullyOcc():
            dist = euclidist(pos, parentmodel.table.balls.getpos())
            return norm.pdf(dist,loc = 0,scale = parentmodel.pe)
        else:
            # If the particle is in the goal while the ball is covered, it shouldn't be
            idx = int((parentmodel.t - self.inittime) / self.tps)
            if idx > len(self.path): return 1e-100

            # If the ball is covered, the particle should test vs probability that it should be covered
            covmat = np.array([[parentmodel.pe,0],[0,parentmodel.pe]])
            brad = int(parentmodel.table.balls.getrad())
            blocked = []
            for w in parentmodel.table.walls:
                 blocked.append(w.r.inflate(2*brad,2*brad))

            p = 0
            ps = []

            # Break up occluders into non-overlapping, then run
            uoccs = uniqueOccs(map(lambda x: x.r, parentmodel.table.occludes), blocked)
            for o in uoccs:
                lefto = o.left
                righto = o.right
                topo = o.top
                boto = o.bottom

                tst = mvnormcdf([lefto,topo],[righto,boto],pos,covmat)
                p += mvnormcdf([lefto,topo],[righto,boto],pos,covmat)

                ps.append(p)

            return p
  '''