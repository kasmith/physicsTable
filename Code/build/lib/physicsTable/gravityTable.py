

from __future__ import division
from simpleTable import *
from math import atan, pi
import random

ENERGYTRANSFER = 20.
PUSHRATIO = .2


def getang( vct ):
    if vct[0] == 0:
        if vct[1] > 0: return pi/2
        else: return 3*pi/2
    if vct[0] < 0:
        ret = pi + atan(vct[1] / vct[0])
    else:
        ret = atan(vct[1] / vct[0])
    if ret < 0: ret += 2*pi
    return ret


class GravityTable(SimpleTable):
    
    def __init__(self, dims, gravity_force = 1000., wall_friction = 1.5, background_cl = WHITE, def_ball_rad = 20, def_ball_cl = BLUE,def_pad_len = 100, def_wall_cl = BLACK, def_occ_cl = GREY, def_pad_cl = BLACK, active = True, soffset = None):
        super(GravityTable, self).__init__(dims, [BOTTOM], background_cl, def_ball_rad,def_ball_cl, def_pad_len, def_wall_cl, def_occ_cl, def_pad_cl, active, soffset)
        self.sp.gravity = pm.Vec2d(0., gravity_force)
        #self.top.friction = wall_friction
        self.bottom.friction = wall_friction
    
    def addBall(self, initpos, initvel = (0.,0.),rot = 0., rad = None, color = None, elast = 1.):
        if self.balls: print "Note: only one ball allowed - overwriting"
        if rad is None: rad = self.dballrad
        if color is None: color = self.dballc
        newball = self.RotateBall(initpos,initvel,rad,color,rot, elast)
        self.sp.add(newball.body, newball.circle)
        self.on_addball(newball)
        self.balls = newball
        return newball    
    
    def addPaddle(self, top, bottom, left, right, padlen = None, padwid = 3, color = None, bkcolor = GREY, elast = 1.):
        if padlen is None: padlen = self.dpadlen
        if color is None: color = self.dpadc
        npad = self.VelcroPaddle(top,bottom, left, right, padlen, padwid, color, bkcolor, self.sp, elast, self.sp.static_body)
        self.paddle = npad
        return npad
    
    def on_wallhit(self, ball,wall):
        reltouchvel = self.balls.body.angular_velocity*self.balls.circle.radius # - self.balls.getvel()[0]
        #self.balls.body.apply_impulse((reltouchvel*PUSHRATIO,0.),(0.,self.balls.getrad()))
        #self.balls.body.apply_impulse((-reltouchvel*PUSHRATIO*(ENERGYTRANSFER-1),0.), (0.,0.))
        print self.balls.body.angular_velocity, self.balls.getvel()
        
    def on_paddlehit(self, ball, paddle):
        if ball.body.rotation_vector[0] > 0:
            self.deactivate()
            paddle.ret = SUCCESS
    
    class RotateBall(object):
        def __init__(self, initpos, initvel, rad, color, rotation, elast):
            self.body = pm.Body(1, pm.moment_for_circle(1,rad,rad))
            self.circle = pm.Circle(self.body, rad)
            self.circle.elasticity = elast
            self.circle.collision_type = COLLTYPE_BALL
            self.body.position = initpos
            self.body.angular_velocity = rotation
            self.body.velocity = pm.Vec2d(initvel)
            self.body.friction = 1.
            self.r = pg.Rect(initpos[0]-rad,initpos[1]-rad,2*rad,2*rad)
            
            self.col = color
            self.bounces = 0
            self.tsb = 0 # Time since last bounce
            
        def getrad(self): return int(self.circle.radius)
        def getpos(self): return self.body.position
        def getvel(self): return self.body.velocity
        def setvel(self, velvect): self.body.velocity = pm.Vec2d(velvect)
        def setpos(self, pos):
            self.body.position = pm.Vec2d(pos)
            self.circle.cache_bb()
        def getboundrect(self):
            self.r.center = self.getpos()
            return self.r
        
        def draw(self, screen):
            p = map(int, self.getpos())
            sp = self.body.rotation_vector
            defang = getang(sp)
            r = self.getrad()
            #ep = (p[0] + r*sp[0], p[1] + r*sp[1])
            pg.draw.circle(screen, self.col, p, r, 0)
            pg.draw.arc(screen, GREEN, self.getboundrect(),defang - pi/2, defang + pi/2 ,10)
        
        def toStr(self):
            return "Ball object - pos: " + str(self.getpos()) + "; vel: " + str(self.getvel())
            
            
    class VelcroPaddle(object):
        def __init__(self, top, bottom, left, right, padlen, padwid, color, bkcol, spacetoadd, elast, stb):
            self.r = pg.Rect(left,top,right-left,bottom-top)
            self.p = self.r.center
            self.col = color
            self.bkc = bkcol
            self.hlen = int(padlen / 2)
            self.wid = padwid
            ep = self.getendpts()
            self.seg = pm.Segment(stb, ep[0],ep[1], padwid)
            self.seg.elasticity = elast
            self.seg.collision_type = COLLTYPE_PAD
            self.ret = None
            if spacetoadd:
                spacetoadd.add(self.seg)
                self.update(self.p)
                
        def update(self, mp):
            x = mp[0]
            y = mp[1]
            if x < self.r.left: x = self.r.left
            if x > self.r.right: x = self.r.right
            if y < (self.r.top + self.hlen): y = self.r.top + self.hlen
            if y > (self.r.bottom - self.hlen): y = self.r.bottom - self.hlen
            self.p = (x,y)
            ep = self.getendpts()
            self.seg.a = ep[0]
            self.seg.b = ep[1]
            self.seg.cache_bb()
            
        def getendpts(self):
            p1 = (self.p[0], self.p[1]-self.hlen)
            p2 = (self.p[0], self.p[1]+self.hlen)
            return (p1,p2)
        
        def draw(self, screen):
            pg.draw.rect(screen, self.bkc, self.r, 2)
            ep = self.getendpts()
            pg.draw.line(screen, self.col, ep[0],ep[1],self.wid)
            