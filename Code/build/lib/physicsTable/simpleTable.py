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
import time

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
    
    def draw(self, stillshow = False):
        self.surface.fill(self.bk_c)
        
        if not stillshow:
            if self.balls: self.balls.draw(self.surface)
        for o in self.occludes: o.draw(self.surface)
        for w in self.walls: w.draw(self.surface)
        for g in self.goals: g.draw(self.surface)
        if stillshow:
            if self.balls: self.balls.draw(self.surface)
        
        if self.paddle: self.paddle.draw(self.surface)
        
        return self.surface
    
    def addBounce(self, shapeobj):
        if self.balls.circle == shapeobj: self.balls.bounces += 1
        
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
        
    def mostlyOcc(self): return super(SimpleTable,self).mostlyOcc(self.balls)
    def mostlyOccAll(self): return self.mostlyOcc()
    def fullyOcc(self): return super(SimpleTable,self).fullyOcc(self.balls)
    def fullyOccAll(self): return self.fullyOcc()
    
    def checkEnd(self):
        if self.padhit: return self.paddle.ret
        for g in self.goals:
            if ball_rect_collision(self.balls,g.r): return g.ret
        return None
    
    #def fastUpdate(self):
    #    r = self.balls.getrad()
    #    pg.display.update(self.balls.getboundrect().move(self.soff[0],self.soff[1]).inflate(r,r))
        
    def demonstrate(self, screen = None, timesteps = 1./50, retpath = False, onclick = None,maxtime = None,waitafter = True):
        tm = super(SimpleTable, self).demonstrate(screen, timesteps, retpath, onclick, maxtime,waitafter)
        p = self.balls.getpos()
        if retpath: return [p, tm[0], tm[1]]
        else: return [p, tm]
        
    def simulate(self, maxtime = 50., timeres = None, return_path = False, rp_wid = None):
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
        
        if return_path: return [r, path]
        else: return r
        
    def drawPath(self, pathcl = None):
        if pathcl is None: pathcl = self.balls.col
        sc = self.draw()
        r, p = self.simulate(return_path = True)
        pg.draw.lines(sc,pathcl, False, p)
        return sc
            
    