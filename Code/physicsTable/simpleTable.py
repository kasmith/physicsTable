####################################################################
#
# Extends a BasicTable, but only allows for a single ball at a time
#
####################################################################
#
# Changes from BasicTable:
#  1) SimpleTable.balls is a single instance rather than a list
#  2) fullyOcc / mostlyOcc no longer take a ball argument
#  3) fullyOccAll / mostlyOccAll no longer return a list
#  4) simulate() method to return either 
#  4) Other changes for compatability only
#
####################################################################

from __future__ import division
from basicTable import *
from .objects import *

class SimpleTable(BasicTable):
    
    def __init__(self, *args, **kwds):
        super(SimpleTable,self).__init__(*args, **kwds)
        self.balls = None
        
    def __del__(self):
        super(SimpleTable,self).__del__()
        
    def addBall(self, initpos, initvel = (0.,0.), rad = None, color = None, elast = 1., dispwarn = True, pmsp = None):
        if pmsp is None: pmsp = self.sp
        if self.balls:
            if dispwarn: print "Note: only one ball allowed - overwriting"
            self.sp.remove(self.balls.circle)
            self.sp.remove(self.balls.body)
        if rad is None: rad = self.dballrad
        if color is None: color = self.dballc
        newball = Ball(initpos,initvel,rad,color,elast,pmsp)
        self.sp.add(newball.body, newball.circle)
        self.on_addball(newball)
        self.balls = newball
        return newball

    def removeBall(self):
        if self.balls is None: return True
        self.sp.remove(self.balls.body, self.balls.circle)
        self.balls = None
    
    def addBounce(self, shapeobj):
        if self.balls and self.balls.circle == shapeobj: self.balls.bounces += 1
        
    def coll_ball_wall(self, arbiter):
        map(self.addBounce,arbiter.shapes)
        if len(arbiter.shapes) > 2: print "Shouldn't have multi-collision... may be errors"
        ss = [self.findWallByShape(s) for s in arbiter.shapes]
        wl = [w for w in ss if w is not None][0]
        self.on_wallhit(self.balls, w)
        
    def coll_ball_pad(self, arbiter):
        map(self.addBounce,arbiter.shapes)
        if len(arbiter.shapes) > 2: print "Shouldn't have multi-collision... may be errors"
        self.padhit = True
        self.on_paddlehit(self.balls, self.paddle)

    def coll_ball_ball(self, arbiter):
        print arbiter.shapes
        raise Exception('Found two balls colliding when at most one exists')
        #self.on_ballhit([b for b in self.balls if b.circle in arbiter.shapes])
        
    def mostlyOcc(self): return super(SimpleTable,self).mostlyOcc(self.balls)
    def mostlyOccAll(self): return self.mostlyOcc()
    def fullyOcc(self): return super(SimpleTable,self).fullyOcc(self.balls)
    def fullyOccAll(self): return self.fullyOcc()
    
    def checkEnd(self):
        if self.padhit: return self.paddle.ret
        for g in self.goals:
            if ball_rect_collision(self.balls,g.r): return g.ret
        return None

    def simulate(self, maxtime = 50., timeres = None, return_path = False,return_bounces = False, rp_wid = None):
        if timeres is None: timeres = self.basicts
        if return_path:
            bx = int(self.balls.getpos()[0])
            by = int(self.balls.getpos()[1])
            if rp_wid:
                path = np.zeros(self.dim)
                for i in range(max(0,bx - rp_wid), min(self.dim[0],bx + rp_wid + 1)):
                    for j in range(max(0,by - rp_wid), min(self.dim[1],by + rp_wid + 1)):
                        pdiff = abs(bx - i) + abs(by - j)
                        col = max((rp_wid-pdiff)*(rp_wid-pdiff), 0)
                        path[i,j] = max(col,path[i,j])
            else:
                path = []
                path.append( (bx, by) )
        if return_bounces:
            bnc = []
            bnc.append(0)
        running = True
        while running:
            
            r = self.step(timeres, maxtime)
            if r: running = False
            if return_path:
                bx = int(self.balls.getpos()[0])
                by = int(self.balls.getpos()[1])
                if rp_wid:
                    for i in range(max(0,bx - rp_wid), min(self.dim[0],bx + rp_wid + 1)):
                        for j in range(max(0,by - rp_wid), min(self.dim[1],by + rp_wid + 1)):
                            pdiff = abs(bx - i) + abs(by - j)
                            col = max((rp_wid-pdiff)*(rp_wid-pdiff), 0)
                            path[i,j] = max(col,path[i,j])
                else:
                    path.append( (bx, by) )
            if return_bounces:
                bnc.append(self.balls.bounces)
        
        if return_path:
            if return_bounces:
                return [r, path,bnc]
            else:
                return [r,path]
        else:
            if return_bounces:
                return [r,bnc]
            else:
                return r
        

            
    