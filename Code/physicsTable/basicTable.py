# Basic class for a table with ball(s)

from __future__ import division
import pymunk as pm
import random, math
from .constants import *
from .objects import *
import numpy as np
from rectangles import *
import subprocess, os, sys, shutil, shlex, warnings
from weakref import ref

# Methods:
#  __init__
#  activate
#  deactivate
#  step
#  draw
#  addBall
#  addWall
#  addOcc
#  checkEnd
#  fullyOcc
#  mostlyOcc


# Helper functions
def coll_func_ball_ball(space, arbiter, tableref):
    if tableref() is not None: tableref().coll_ball_ball(arbiter)
        
def coll_func_ball_wall(space, arbiter, tableref):
    if tableref() is not None: tableref().coll_ball_wall(arbiter)
    
def coll_func_ball_pad(space, arbiter, tableref):
    if tableref() is not None: tableref().coll_ball_pad(arbiter)

def euclid_dist(p1, p2, maxdist = None):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    if maxdist is None: return math.sqrt(dx*dx + dy*dy)
    else: return (dx*dx + dy*dy) <= maxdist*maxdist

def ball_rect_collision(ball,rect):
    brect = ball.getboundrect()
    if rect.colliderect(brect):
        if rect.contains(brect): return True
        bcent = ball.getpos()
        rad = ball.getrad()
        if brect.bottom > rect.top or brect.top < rect.bottom:
            if bcent[0] > rect.left and bcent[0] < rect.right: return True
        if brect.right > rect.left or brect.left < rect.right:
            if bcent[1] > rect.top and bcent[1] < rect.bottom: return True
            
        return any(map(lambda pt: euclid_dist(pt,bcent,rad), [rect.topleft,rect.topright,rect.bottomleft,rect.bottomright]))
    else: return False

def check_counterclockwise(pointlist):
    pointlist = [(p[0],p[1]) for p in pointlist]
    if len(pointlist) < 3: return True
    a = np.array(pointlist[0])
    b = np.array(pointlist[1])
    for i in range(2,len(pointlist)):
        c = np.array(pointlist[i])
        l1 = b-a
        l2 = c-b
        if np.cross(l1,l2) > 0: return False
        a = b
        b = c
    c = np.array(pointlist[0])
    l1 = b-a
    l2 = c-b
    if np.cross(l1,l2) > 0: return False
    return True


class BasicTable(object):
    
    def __init__(self, dims, closed_ends = [LEFT, RIGHT, BOTTOM, TOP], def_ball_rad = 20, def_pad_len = 100, active = True):
        
        # Default characteristics
        self.dim = dims
        self.dballrad = def_ball_rad
        self.dpadlen = def_pad_len
        self.act = active
        
        # Make the pymunk space (& sink output)
        _stderr = sys.stderr
        _stdout = sys.stdout
        nullout = open(os.devnull,'wb')
        sys.stderr = sys.stdout = nullout
        self.sp = pm.Space(10)
        sys.stderr = _stderr
        sys.stdout = _stdout
        self.sp.gravity = pm.Vec2d(0.,0.)
        stb = self.sp.static_body
        self.sp.add_collision_handler(COLLTYPE_BALL,COLLTYPE_BALL, None, None, None, coll_func_ball_ball, tableref = ref(self))
        self.sp.add_collision_handler(COLLTYPE_BALL,COLLTYPE_WALL, None, None,None, coll_func_ball_wall, tableref = ref(self))
        self.sp.add_collision_handler(COLLTYPE_BALL,COLLTYPE_PAD,None, None,None, coll_func_ball_pad, tableref = ref(self))
        

        self.balls = []
        self.walls = []
        self.occludes = []
        self.goals = []
        self.goalrettypes = [TIMEUP]
        self.paddle = None
        self.padhit = False
        
        self.stored_closed_ends = closed_ends

        
        self.top = self.bottom = self.right = self.left = None
        for ce in closed_ends:
            if ce == TOP: s = pm.Segment(stb, (-1,-10), (self.dim[0]+1,-10),10); s.elasticity = 1.; self.sp.add(s); s.collision_type = COLLTYPE_WALL; self.top = s
            elif ce == BOTTOM: s = pm.Segment(stb, (-1,self.dim[1]+10), (self.dim[0]+1,self.dim[1]+10),10); s.elasticity = 1.; self.sp.add(s); s.collision_type = COLLTYPE_WALL; self.bottom = s
            elif ce == RIGHT: s = pm.Segment(stb, (self.dim[0]+10,-1), (self.dim[0]+10,self.dim[1]+1),10); s.elasticity = 1.; self.sp.add(s); s.collision_type = COLLTYPE_WALL; self.right = s
            elif ce == LEFT: s = pm.Segment(stb, (-10,-1), (-10,self.dim[1]+1),10); s.elasticity = 1.; self.sp.add(s); s.collision_type = COLLTYPE_WALL; self.left = s
            else: print "Warning: Inappropriate closed_ends:", ce
            
        # Other characteristics
        self.tm = 0.
        self.basicts = TIMESTEP
    

    
    def __del__(self):
        # Clean up the objects
        #del self.balls
        #del self.walls
        #del self.occludes
        #del self.goals
        #del self.paddle
        
        # Clean up the pymunk space
        self.sp.remove(self.sp.bodies)
        self.sp.remove(self.sp.shapes)
        del self.sp
    
    def set_timestep(self, ts):
        self.basicts = ts
    
    def coll_ball_ball(self, arbiter):
        map(self.addBounce,arbiter.shapes)
        self.on_ballhit([b for b in self.balls if b.circle in arbiter.shapes])
        
    def coll_ball_wall(self, arbiter):
        map(self.addBounce,arbiter.shapes)
        if len(arbiter.shapes) > 2: print "Shouldn't have multi-collision... may be errors"
        ss = [self.findWallByShape(s) for s in arbiter.shapes]
        wl = [w for w in ss if w is not None][0]
        self.on_wallhit([b for b in self.balls if b.circle in arbiter.shapes][0], w)
        
    def coll_ball_pad(self, arbiter):
        map(self.addBounce,arbiter.shapes)
        if len(arbiter.shapes) > 2: print "Shouldn't have multi-collision... may be errors"
        self.padhit = True
        self.on_paddlehit([b for b in self.balls if b.circle in arbiter.shapes][0], self.paddle)
    
    def on_step(self): pass
    def on_addball(self,ball): pass
    def on_ballhit(self, balllist): pass
    def on_wallhit(self, ball, wall): pass
    def on_paddlehit(self, ball, paddle): pass
    def on_goalhit(self, ball, paddle): pass
    
    def activate(self): self.act = True
    def deactivate(self): self.act = False
    
    def mostlyOcc(self,ball):
        bpos = ball.getpos()
        for o in self.occludes:
            if o.r.collidepoint(bpos): return True
        return False
    
    def mostlyOccAll(self):
        return [self.mostlyOcc(b) for b in self.balls]
    
    def fullyOcc(self,ball):
        brect = ball.getboundrect()
        orects = [o.r.inflate(1,1) for o in self.occludes]
        testos = []
        for o in orects:
            if o.contains(brect): return True
            if o.colliderect(brect): testos.append(o)
        if len(breakRect(brect,testos)) == 0: return True
        return False
    
    def fullyOccAll(self):
        return [self.fullyOcc(b) for b in self.balls]
    
    def addBall(self, initpos, initvel = (0.,0.), rad = None, color = None, elast = 1., pmsp = None, layers = None):
        if pmsp is None: pmsp = self.sp
        if rad is None: rad = self.dballrad
        if color is None: color = self.dballc
        newball = Ball(initpos,initvel,rad,color,elast,pmsp, layers)
        self.sp.add(newball.body, newball.circle)
        self.on_addball(newball)
        self.balls.append(newball)
        return newball
    
    def addWall(self, upperleft, lowerright, color = None, elast = 1., pmsp = None):
        if pmsp is None: pmsp = self.sp
        if color is None: color = self.dwallc
        newwall = Wall(upperleft, lowerright,color,elast,self.sp.static_body,pmsp)
        self.sp.add(newwall.poly)
        self.walls.append(newwall)
        return newwall
    
    def addAbnormWall(self, vertexlist, color = None, elast = 1., pmsp = None):
        if pmsp is None: pmsp = self.sp
        if not check_counterclockwise(vertexlist): print 'In addAbnormWall, vertices must be counterclockwise and convex, no wall added:',vertexlist; return None
        if color is None: color = self.dwallc
        newwall = AbnormWall(vertexlist,color,elast,self.sp.static_body,pmsp)
        self.sp.add(newwall.poly)
        self.walls.append(newwall)
        return newwall
    
    def addOcc(self, upperleft, lowerright, color = None):
        if color is None: color = self.doccc
        newocc = Occlusion(upperleft,lowerright,color)
        self.occludes.append(newocc)
        return newocc
    
    def addGoal(self,upperleft,lowerright,onreturn ,color = None):
        try: dict([(onreturn,0)])
        except:
            raise TypeError("'onreturn' argument is not hashable: " + str(onreturn))
        newgoal = Goal(upperleft,lowerright,color,onreturn)
        self.goals.append(newgoal)
        if onreturn not in self.goalrettypes:
            self.goalrettypes.append(onreturn)
        return newgoal
        
    def addPaddle(self,p1, p2, padlen = None, padwid = 3, hitret = None, active = True, acol = None, iacol = None, pthcol = None, elast = 1., suppressoverwrite = False, pmsp = None):
        if pmsp is None: pmsp = self.sp
        if active: sta = self.sp
        else: sta = None
        if p1 == p2: print "Paddle endpoints must not overlap:",p1,p2; return None
        if p1[0] != p2[0] and p1[1] != p2[1]: print "Paddle must be horizontal or vertical",p1,p2; return None
        if padlen is None: padlen = self.dpadlen
        if self.paddle is not None and not suppressoverwrite: print "Warning! Overwriting old paddle"
        self.paddle = Paddle(p1,p2,padlen,acol,iacol,pthcol,padwid,hitret, sta, elast, self.sp.static_body,pmsp)
        return self.paddle
        
    def activatePaddle(self):
        if not self.paddle: print "Can't activate a missing paddle!"; return None
        self.paddle.activate(self.sp, self.getRelativeMousePos())
    
    def deactivatePaddle(self):
        if not self.paddle: print "Can't deactivate a missing paddle!"; return None
        self.paddle.deactivate(self.sp)
        
    def togglePaddle(self):
        if not self.paddle: print "Can't toggle a missing paddle!"; return None
        if self.paddle.act: self.paddle.deactivate(self.sp)
        else: self.paddle.activate(self.sp, self.getRelativeMousePos())
     
    # Default: does any ball overlap with any of the goals? Has it hit the paddle?
    def checkEnd(self):
        rets = []
        if self.padhit: return self.paddle.ret
        for g in self.goals:
            for b in self.balls:
                if ball_rect_collision(b,g.r):
                    self.on_goalhit(b,g)
                    if g.ret: rets.append(g.ret)
        if len(rets) > 0: return rets
        return None
    
    def addBounce(self, shapeobj):
        for b in self.balls:
            if b.circle == shapeobj: b.bounces +=1
     
    def findWallByShape(self, shape):
        wls = [w for w in self.walls if w.poly == shape]
        if len(wls) == 1: return wls[0]
        elif self.top == shape: return TOP
        elif self.bottom == shape: return BOTTOM
        elif self.left == shape: return LEFT
        elif self.right == shape: return RIGHT
        else: return None
        
    def step(self, t = 1/50., maxtime = None):
        substeps = t / self.basicts
        if substeps != int(substeps): print "Warning: steps not evenly divisible - off by", (substeps - int(substeps))
        if self.act:
            for i in range(int(substeps)):
                self.on_step()
                self.sp.step(self.basicts)
                self.tm += self.basicts
                e = self.checkEnd()
                if e is not None: return e
                if maxtime and self.tm > maxtime: return TIMEUP
            return e
        else: return None
