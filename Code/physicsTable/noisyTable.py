#######################################
#
# For simulating forwards a SimpleTable with uncertainty
#
#######################################
#
#
#

from __future__ import division

import sys,os
from simpleTable import *
import random
import numpy as np
import pygame as pg
import pymunk as pm

def velAngle(vx,vy):
    ang = np.arctan2(vy,vx) % (np.pi * 2)
    mag = np.sqrt(vx * vx + vy * vy)
    return (ang,mag)

class NoisyTable(SimpleTable):
    
    def __init__(self, dims, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, *args, **kwds):
                     
                     self.kapv = kapv
                     self.kapb = kapb
                     self.kapm = kapm
                     self.perr = perr
                     super(NoisyTable, self).__init__(dims, *args, **kwds)

    def __del__(self):
        super(NoisyTable,self).__del__()
    
    def jitter_ball(self, ball, kappa = None, posjitter = None):
        if posjitter:
            initpos = ball.getpos()
            rad = ball.getrad()
            xdim, ydim = self.dim
            setting = True
            while setting:
                px = random.normalvariate(initpos[0],posjitter)
                py = random.normalvariate(initpos[1],posjitter)
                ball.setpos( (px, py) )
                setting = False
                # Check that the ball isn't outside the screen
                if not (px > rad and py > rad and px < (xdim - rad) and py < (ydim - rad)):
                    setting = True

                # Check that the ball isn't stuck in walls or on a goal
                brect = ball.getboundrect()
                for w in self.walls:
                    if brect.colliderect(w.r): setting = True
                for g in self.goals:
                    if brect.colliderect(g.r): setting = True

        
        if kappa:
            v = ball.getvel()
            vang, vmag = velAngle(v[0], v[1])
            newang = np.random.vonmises(vang, kappa)
            ball.setvel( (vmag * np.cos(newang), vmag * np.sin(newang)) )
    
    def on_wallhit(self, ball, wall):
        self.jitter_ball(ball, self.kapb)
    
    def on_addball(self, ball):
        self.jitter_ball(ball,self.kapv, self.perr)
    
    def on_step(self):
        if self.balls is not None: self.jitter_ball(self.balls, self.kapm)

        
def makeNoisy(table, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF,paddlereturn = SUCCESS, straddlepaddle = True):
    
    ntab = NoisyTable(table.dim, kapv, kapb, kapm, perr, table.stored_closed_ends, table.bk_c, table.dballrad, table.dballc, table.dpadlen, table.dwallc, table.doccc, table.dpadc, table.act, table.stored_soffset)
    ntab.set_timestep(table.basicts)
    if table.balls: ntab.addBall(table.balls.getpos(), table.balls.getvel())
    for w in table.walls: 
        if isinstance(w, AbnormWall): ntab.addAbnormWall(w.poly.get_vertices(), w.col, w.poly.elasticity)
        elif isinstance(w, Wall): ntab.addWall(w.r.topleft, w.r.bottomright,w.col, w.poly.elasticity)
        
    for o in table.occludes: ntab.addOcc(o.r.topleft, o.r.bottomright, o.col)
    for g in table.goals: ntab.addGoal(g.r.topleft, g.r.bottomright, g.ret, g.col)
    # Turn paddle into a special goal that returns paddlereturn (SUCCESS by default)
    if table.paddle and paddlereturn:
        if straddlepaddle:
            op = table.paddle.otherpos
            if table.paddle.dir == HORIZONTAL:
                ul = (0,op-table.paddle.wid)
                lr = (table.dim[0],op+table.paddle.wid)
            else:
                ul = (op-table.paddle.wid,0)
                lr = (op+table.paddle.wid,table.dim[1])
        else:
            e1, e2 = table.paddle.getendpts()
            if table.paddle.dir == HORIZONTAL:
                ul = (e1[0], e1[1] - table.paddle.wid)
                lr = (e2[0], e2[1] + table.paddle.wid)
            else:
                ul = (e1[0] - table.paddle.wid, e1[1])
                lr = (e2[0] + table.paddle.wid, e2[1])
        ntab.addGoal(ul, lr, paddlereturn, LIGHTGREY)
    return ntab
    
    
    