

from __future__ import division
import sys,os
from simpleTable import *
import cPickle as pickle
from math import sqrt

class SimpleTrial(object):
    
    def __init__(self, name, dims, closed_ends = [LEFT, RIGHT, BOTTOM, TOP], background_cl = WHITE, def_ball_vel = 600, def_ball_rad = 20, def_ball_cl = BLUE,def_pad_len = 100, def_wall_cl = BLACK, def_occ_cl = GREY, def_pad_cl = BLACK):
        self.name = name
        self.dims = dims
        self.ce = closed_ends
        self.bkc = background_cl
        self.dbr = def_ball_rad
        self.dbc = def_ball_cl
        self.dpl = def_pad_len
        self.dwc = def_wall_cl
        self.doc = def_occ_cl
        self.dpc = def_pad_cl
        self.dbv = def_ball_vel
        
        self.ball = None
        self.normwalls = []
        self.abnormwalls = []
        self.occs = []
        self.goals = []
        self.paddle = None
        
    def addBall(self, initpos, initvel, rad = None, color = None, elast = 1.):
        if self.ball is not None: raise Exception('Cannot add a second ball to a SimpleTrial')
        if rad is None: rad = self.dbr
        if color is None: color = self.dbc
        self.ball = (initpos, initvel, rad, color, elast)
        
    def addWall(self, upperleft, lowerright, color = None, elast = 1.):
        if color is None: color = self.dwc
        self.normwalls.append( (upperleft, lowerright, color, elast) )
        
    def addAbnormWall(self, vertexlist, color = None, elast = 1.):
        if color is None: color = self.dwc
        self.abnormwalls.append( (vertexlist, color, elast) )
    
    def addGoal(self, upperleft, lowerright, onreturn, color = None):
        self.goals.append( (upperleft, lowerright, onreturn, color) )
        
    def addPaddle(self, p1, p2, padlen, padwid, hitret, acol = BLACK, iacol = GREY, pthcol = None, elast = 1.):
        self.paddle = (p1, p2, padlen, padwid, hitret, acol, iacol, pthcol, elast)
        
    def addOcc(self, upperleft, lowerright, color = None):
        if color is None: color = self.doc
        self.occs.append( (upperleft, lowerright, color) )
        
    def makeTable(self,soffset = None, paddleasgoal = False):
        tb = SimpleTable(self.dims,self.ce,self.bkc,self.dbr,self.dbc,self.dpl,self.dwc,self.doc,self.dpc, True, soffset)
        if self.ball: tb.addBall(self.ball[0], self.ball[1], self.ball[2], self.ball[3], self.ball[4])
        if self.paddle: tb.addPaddle(self.paddle[0],self.paddle[1], self.paddle[2], self.paddle[3], self.paddle[4], self.paddle[5], self.paddle[6], self.paddle[7], self.paddle[8], False)
        for w in self.normwalls:
            tb.addWall(w[0],w[1],w[2],w[3])
        for w in self.abnormwalls:
            tb.addAbnormWall(w[0],w[1],w[2])
        for g in self.goals:
            tb.addGoal(g[0],g[1],g[2],g[3])
        for o in self.occs:
            tb.addOcc(o[0],o[1],o[2])
        return tb
    
    def normalizeVel(self):
        v = self.ball[1]
        vmag = sqrt(v[0]*v[0] + v[1]*v[1])
        vadj = self.dbv / vmag
        self.ball = (self.ball[0], (v[0]*vadj, v[1]*vadj), self.ball[2], self.ball[3], self.ball[4])
    
    def checkConsistency(self, maxsteps = 50000):
        good = True
        
        ctb = self.makeTable(paddleasgoal = True)
        
        if self.paddle:
            pbox = ctb.paddle.getbound()
        else:
            pbox = None
        
        if not self.ball:
            print "Need to add a ball"
            good = False
        else:
            br = ctb.balls.getboundrect()
            for w in ctb.walls:
                if w.shapetype == SHAPE_RECT:
                    if br.colliderect(w.r):
                        print "Ball overlaps with wall"
                        good = False
                else:
                    if br.colliderect(w.getBoundRect()):
                        if w.poly.point_query(ctb.balls.getpos()):
                            print "Ball overlaps with abnormal wall"
                            good = False
                        else:
                            print "POSSIBLE WARNING: Ball MAY overlap with abnormal wall"
                            good = -1
            if br.collidelist([g.r for g in ctb.goals]) != -1:
                print "Ball overlaps with goal"
                good = False
            if pbox:
                if br.colliderect(pbox):
                    print "Ball overlaps with paddle path"
                    good = False
            
        for g in ctb.goals:
            for w in ctb.walls:
                if w.shapetype == SHAPE_RECT:
                    if g.r.colliderect(w.r):
                        print "Goal overlaps with wall"
                        good = False
                else:
                    if g.r.colliderect(w.getBoundRect()):
                        if w.poly.segment_query(g.r.topleft,g.r.topright) or w.poly.segment_query(g.r.topleft,g.r.bottomleft) or w.poly.segment_query(g.r.topright,g.r.bottomright) or w.poly.segment_query(g.r.bottomleft,g.r.bottomright):
                            print "Goal overlaps with abnormal wall"
                            good = False
            
            if pbox:
                if g.r.colliderect(pbox):
                    print "Goal and paddle path intersect"
                    good = False
                    
            if g.r.collidelist([o.r for o in ctb.occludes]) != -1:
                print "Goal is at least partially occluded"
                good = False
        
        if len(ctb.goals) > 1:
            for i in range(1,len(ctb.goals)):
                g1 = ctb.goals[i-1]
                g2 = ctb.goals[i]
                if g1.r.colliderect(g2.r):
                    print "Two goals overlap"
                    good = False
        
        if pbox:
            for w in ctb.walls:
                if w.shapetype == SHAPE_RECT:
                    if pbox.colliderect(w.r):
                        print "Paddle path intersects wall"
                        good = False
                else:
                    if pbox.colliderect(w.getBoundRect()):
                        ep = ctb.paddle.getendpts()
                        if w.poly.segment_query(ep[0],ep[1]):
                            print "Paddle path intersects abnormal wall"
                            good = False
            
        if ctb.mostlyOccAll():
            good = False
            print "Ball is mostly occluded at start"
        
        running = True
        stp = 0
        while running:
            stp += 1
            if stp > maxsteps:
                print "Takes too long to end"
                good = False
                running = False
            e = ctb.step(TIMESTEP)
            if e: running = False
        
        if ctb.mostlyOccAll():
            good = False
            print "Ball is mostly occluded at end"
        
        return good
    

    def save(self, flnm = None, askoverwrite = True):
        if flnm is None: flnm = self.name + '.ptr'
        if os.path.exists(flnm) and askoverwrite:
            asking = True
            while asking:
                ans = raw_input('File exists; overwrite? (y/n): ')
                if ans == 'n': return None
                if ans == 'y': asking = False
            
        pickle.dump(self, open(flnm,'wb'))
        
class PongTrial(SimpleTrial):
    
    def checkConsistency(self,maxsteps = 50000):
        good = True
        if len(self.goals) != 0:
            print "No goals allowed on a PongTable"
            good = False
        if not super(PongTrial, self).checkConsistency(maxsteps): good = False
        return good
    

class RedGreenTrial(SimpleTrial):
    
    def checkConsistency(self, maxsteps = 50000):
        good = True
        if len(self.goals) != 2:
            print "Need two goals for a red/green trial"
            good = False
            
        if REDGOAL not in map(lambda x: x[2], self.goals): print "Need a REDGOAL return"; good = False
        if GREENGOAL not in map(lambda x: x[2], self.goals): print "Need a GREENGOAL return"; good = False
        if not super(RedGreenTrial, self).checkConsistency(maxsteps): good = False
        return good
    
    def switchRedGreen(self):
        self.goals = map(self.switchGoalRedGreen, self.goals)
    
    @staticmethod
    def switchGoalRedGreen(goal):
        if goal[2] == REDGOAL:
            return ( goal[0], goal[1], GREENGOAL, GREEN )
        if goal[2] == GREENGOAL:
            return ( goal[0], goal[1], REDGOAL, RED )
        
    
def loadTrial(flnm):
    return pickle.load(open(flnm,'rb'))
  