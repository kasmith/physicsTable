from ..models import *

def psdrawdensity(self, rp_wid = 5, greyscale = (0,255), gamadj = .2):
    ptharray = np.zeros(table.dim)

    def singpth(i):
        print i
        n = makeNoisy(self.tab,self.kapv,self.kapb,self.kapm,self.perr)
        r = n.simulate(self.maxtime, return_path = True, rp_wid = rp_wid)
        print 'd',i
        return r[1]
    sims = map(singpth, range(self.nsims))

    print 'simulated'
    for s in sims:
        ptharray = np.add(ptharray,s)
    paths = ptharray / np.max(ptharray)

    gsadj = greyscale[1] - greyscale[0]
    #colarray = np.zeros(table.dim)

    print 'some adjustments'
    n = makeNoisy(self.tab,None,None,None,None)
    realpath = n.simulate(self.maxtime,return_path=True)[1]

    print 'real made'

    sc = table.draw()
    #sarray = pg.surfarray.pixels3d(sc)
    #print sarray

    print 'initial draw'
    for i in range(table.dim[0]):
        print i
        for j in range(table.dim[1]):
            if paths[i,j] > 0:
                tmpcol = int(greyscale[1] - gsadj * paths[i,j] * gamadj)
                if tmpcol < 0: tmpcol = 0
                #sarray[i,j] = (tmpcol,tmpcol,tmpcol)
                sc.set_at((i,j), pg.Color(tmpcol,tmpcol,tmpcol,255))
            #else:
            #    colarray[i,j] = 255


    table.balls.draw(sc)
    pg.draw.lines(sc, table.balls.col, False, realpath)
    return sc
PointSimulation.drawdensity = psdrawdensity

def pssavepath(self, imgnm):
    sc = self.drawdensity()
    pg.image.save(sc, imgnm)
PointSimulation.savepath = pssavepath



# OTHER STUFF TO FIX
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