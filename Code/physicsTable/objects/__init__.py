from __future__ import division
from physicsTable.constants import *
import pymunk as pm
from weakref import ref

__all__ = ['Ball', 'Wall','Occlusion','Goal','AbnormWall','Paddle','ptRect']

# A class that replicates some of the basic functionality of pygame's Rect to avoid using pygame
class ptRect(object):
    def __init__(self,left,top,width=None,height=None):
        if width == None and height == None:
            width,height = top
            left,top = left
        right = left + width
        bottom = top + height
        self.width = width
        self.height = height
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.topleft = (left,top)
        self.bottomleft = (left,bottom)
        self.topright = (right,top)
        self.bottomright = (right,bottom)

    def clip(self,Rect):
        newl = max(self.left,Rect.left)
        newr = min(self.right,Rect.right)
        newt = max(self.top,Rect.top)
        newb = min(self.bottom,Rect.bottom)
        if newl >= newr or newt >= newb: return ptRect(self.left,self.top,0,0)
        neww = newr - newl
        newh = newb - newt
        return ptRect(newl,newt,neww,newh)

    def collidepoint(self,x,y=None):
        if y is None: x,y = x
        return (x > self.left and x < self.right and y > self.top and y < self.bottom)

    # Two rectangles collide if their overlap is non-zero
    def colliderect(self,Rect):
        clr = self.clip(Rect)
        return (clr.width != 0 and clr.height != 0)

    def collidelist(self,list):
        for i in range(len(list)):
            if self.colliderect(list[i]): return i
        return -1

    def collidelistall(self,list):
        if r in list:
            if not self.colliderect(r): return False
        return True

    def contains(self,Rect):
        if self.left <= Rect.left and self.right >= Rect.right and \
                        self.top <= Rect.top and self.bottom >= Rect.bottom:
            return 1
        else:
            return 0

    def inflate(self,x,y):
        newl = self.left - x
        newt - self.top - y
        neww = self.width + x*2
        newh = self.height + y*2
        return ptRect(newl,newt,neww,newh)


class Ball(object):
    def __init__(self, initpos, initvel, rad, color, elast, pmsp = None, layer = None):
        initpos = pm.Vec2d(initpos)
        initvel = pm.Vec2d(initvel)
        self.body = pm.Body(1, pm.moment_for_circle(1,0,rad))
        self.circle = pm.Circle(self.body, rad)
        self.circle.elasticity = elast
        self.circle.collision_type = COLLTYPE_BALL
        self.body.position = initpos
        self.body.velocity = pm.Vec2d(initvel)
        if layer:
            if layer < 1 or layer > 31:
                print "Layer must be between 1 and 31 - defaulting to all layers"
            else:
                self.circle.layers = 2**layer
        self.r = ptRect(initpos[0]-rad,initpos[1]-rad,2*rad,2*rad)
        self.sp = ref(pmsp)
        
        self.col = color
        self.bounces = 0
        self.tsb = 0 # Time since last bounce
        self.attached = True
    
        
    def getrad(self): return int(self.circle.radius)
    def getpos(self): return map(float,self.body.position)
    def getvel(self): return map(float,self.body.velocity)
    def setvel(self, velvect): self.body.velocity = pm.Vec2d(velvect)
    def setpos(self, pos):
        self.body.position = pm.Vec2d(pos)
        self.circle.cache_bb()
    def getboundrect(self):
        #self.r.center = self.getpos()
        x,y = self.getpos()
        rad = self.getrad()
        return ptRect(x-rad,y-rad,2*rad,2*rad)
    
    def stop(self): self.body.velocity = pm.Vec2d([0,0])
    def detach(self): 
        if self.attached:
            self.sp().remove(self.body, self.circle)
            self.attached = False
    
    def deactivate(self):
        #print self.sp().bodies
        self.stop()
        self.detach()

    def toStr(self):
        return "Ball object - pos: " + str(self.getpos()) + "; vel: " + str(self.getvel())
    
class Wall(object):
    def __init__(self, upperleft, lowerright, color, elast, stb, pmsp = None):
        w = lowerright[0] - upperleft[0]
        h = lowerright[1] - upperleft[1]
        rect = ptRect(upperleft,(w,h))
        self.poly = pm.Poly(stb,[rect.topleft, rect.topright,rect.bottomright,rect.bottomleft])
        self.poly.elasticity = elast
        self.poly.collision_type = COLLTYPE_WALL
        self.col = color
        self.r = rect
        self.shapetype = SHAPE_RECT
        self.sp = ref(pmsp)
    
    def toStr(self):
        return "Wall object - ul: " + str(self.r.topleft) + "; lr: " + str(self.r.bottomright) 

class Occlusion(object):
    def __init__(self, upperleft, lowerright, color):
        w = lowerright[0] - upperleft[0]
        h = lowerright[1] - upperleft[1]
        self.r = ptRect(upperleft,(w,h))
        self.col = color
    
    def toStr(self):
        return "Occlusion object - ul: " + str(self.r.topleft) + "; lr: " + str(self.r.bottomright) 
        
class Goal(object):
    def __init__(self, upperleft, lowerright, color, onreturn):
        w = lowerright[0] - upperleft[0]
        h = lowerright[1] - upperleft[1]
        self.r = ptRect(upperleft,(w,h))
        self.col = color
        self.ret = onreturn
        
    def toStr(self):
        return "Goal object - ul: " + str(self.r.topleft) + "; lr: " + str(self.r.bottomright) + "; return value: " + str(self.ret)


class AbnormWall(Wall):
    def __init__(self, vertexlist, color, elast, stb, pmsp = None):
        self.poly = pm.Poly(stb, vertexlist)
        self.poly.elasticity = elast
        self.poly.collision_type = COLLTYPE_WALL
        self.col = color
        self.shapetype = SHAPE_POLY
        self.sp = ref(pmsp)
    
    def toStr(self):
        ret = "AbnormWall object - vertices: "
        for v in self.poly.get_vertices():
            ret += (v) + ", "
        return ret
    
    def getBoundRect(self):
        bb = self.poly.cache_bb()
        top = bb.top
        height = bb.bottom - bb.top
        left = bb.left
        width = bb.right - bb.left
        return ptRect(left,top,width,height)
    
class Paddle(object):
    def __init__(self,p1, p2, length, actcolor, inactcolor, pathcolor, width, hitreturn, spacetoadd,elast,stb, pmsp):
        if p1 == p2: raise Exception("Need separable points; should never be here")
        if p1[0] == p2[0]:
            self.dir = VERTICAL
            self.lwrbound = min(p1[1],p2[1]) + int(length / 2)
            self.uprbound = max(p1[1],p2[1]) - int(length / 2)
            self.otherpos = p1[0]
        elif p1[1] == p2[1]:
            self.dir = HORIZONTAL
            self.lwrbound = min(p1[0],p2[0]) + int(length / 2)
            self.uprbound = max(p1[0],p2[0]) - int(length / 2)
            self.otherpos = p1[1]
        else: raise Exception("Paddle bounding line should be horizontal or vertical; should never be here")
        self.col = actcolor
        self.iacol = inactcolor
        self.pcol = pathcolor
        self.ret = hitreturn
        self.wid = width
        self.hlen = int(length / 2)
        self.frozen = False
        self.pos = int((self.uprbound + self.lwrbound)/2)
        ps = self.getendpts()
        self.seg = pm.Segment(stb, ps[0],ps[1],self.wid)
        self.seg.elasticity = elast
        self.seg.collision_type = COLLTYPE_PAD
        if spacetoadd is not None:
            if self.dir == HORIZONTAL: mp = (self.pos,self.otherpos)
            else: mp = (self.otherpos,self.pos)
            self.activate(spacetoadd,mp)
        else: self.act = False
        self.sp = ref(pmsp)

        
    
    def update(self,mp):
        if self.frozen: return None
        if self.dir == HORIZONTAL: np = mp[0]
        else: np = mp[1]
        self.pos = min(max(np,self.lwrbound),self.uprbound)
        if self.act:
            pts = self.getendpts()
            self.seg.unsafe_set_a(pts[0])
            self.seg.unsafe_set_b(pts[1])
            self.seg.cache_bb()
        
    def getendpts(self):
        if self.dir == HORIZONTAL:
            p1 = (self.pos - self.hlen, self.otherpos)
            p2 = (self.pos + self.hlen, self.otherpos)
        else:
            p1 = (self.otherpos, self.pos - self.hlen)
            p2 = (self.otherpos, self.pos + self.hlen)
        return [p1,p2]
    
    def getbound(self):
        if self.dir == HORIZONTAL:
            top = self.otherpos - int(self.wid /2)
            left = self.lwrbound - self.hlen
            height = self.wid
            width = (self.uprbound - self.lwrbound) + self.hlen*2
        else:
            top = self.lwrbound - self.hlen
            left = self.otherpos - int(self.wid / 2)
            height = (self.uprbound - self.lwrbound) + self.hlen*2
            width = self.wid
        return ptRect(left, top, width, height)
        
    def activate(self, space = None, mp = (0,0)):
        if space is None: space = self.sp
        self.act = True
        space.add(self.seg)
        self.update(mp)

    def freeze(self): self.frozen = True
    def unfreeze(self): self.frozen = False

    def changeLen(self,newsize, mp = None):
        if self.frozen: return None
        oldhlen = self.hlen
        self.hlen = int(newsize / 2)
        self.lwrbound = self.lwrbound - oldhlen + self.hlen
        self.uprbound = self.uprbound + oldhlen - self.hlen
        if mp is None:
            if self.dir == HORIZONTAL: mp = (self.pos,self.otherpos)
            else: mp = (self.otherpos,self.pos)
        self.update(mp)

    def deactivate(self, space = None):
        if space is None: space = self.sp
        self.act = False
        space.remove(self.seg)
        

        
    def toStr(self):
        ret = "Paddle object - direction: "
        if self.dir == HORIZONTAL: ret += "horizontal"
        else: ret += "vertical"
        ret += "; endpoints: " + str(self.getendpts()) + "; current position: " + str(self.pos)
        return ret