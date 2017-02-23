import pygame as pg
from ..objects import Ball, Wall, Paddle, Goal, Occlusion, AbnormWall, ptRect
from ..constants import *

def topgrect(self): return pg.Rect(self.left,self.top,self.width,self.height)
ptRect.topg = topgrect

baseballinit = Ball.__init__
def newballinit(self,initpos, initvel, rad, color, elast, pmsp = None, layer = None):
    baseballinit(self,initpos,initvel,rad,color,elast,pmsp,layer)
    self.r = self.r.topg()

def balldraw(self, screen): pg.draw.circle(screen, self.col, map(int,self.getpos()), self.getrad())
Ball.draw = balldraw

def rectdraw(self,screen):
    if self.col is not None: pg.draw.rect(screen,self.col,self.r.topg())
Wall.draw= rectdraw
Occlusion.draw = rectdraw
Goal.draw = rectdraw

def anwdraw(self,screen): pg.draw.polygon(screen,self.col,self.poly.get_vertices())
AbnormWall.draw = anwdraw

def paddraw(self,screen):
    ps = self.getendpts()
    if self.act: c = self.col
    else: c= self.iacol
    if self.pcol:
        if self.dir == HORIZONTAL:
            p1 = (self.lwrbound - self.hlen, self.otherpos)
            p2 = (self.uprbound + self.hlen, self.otherpos)
        else:
            p1 = (self.otherpos, self.lwrbound - self.hlen)
            p2 = (self.otherpos, self.uprbound + self.hlen)
        pg.draw.line(screen, self.pcol, p1,p2, 1)
    pg.draw.line(screen, c, ps[0], ps[1], self.wid)
Paddle.draw = paddraw

