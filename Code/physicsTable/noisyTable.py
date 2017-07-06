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
from basicTable import *
from objects import *
import random
import numpy as np
import pymunk as pm

def velAngle(vx,vy):
    ang = np.arctan2(vy,vx) % (np.pi * 2)
    mag = np.sqrt(vx * vx + vy * vy)
    return (ang,mag)

class NoisyTable(SimpleTable):
    
    def __init__(self, dims, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, constrained_bounce=False, *args, **kwds):
                     
                     self.kapv = kapv
                     self.kapb = kapb
                     self.kapm = kapm
                     self.perr = perr
                     self.cons_bounce = constrained_bounce
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

    # Special case of wall collision -- doesn't allow ball to reverse course
    def wall_collide(self, ball, wall, kappa = None):
        if type(wall) == AbnormWall:
            print "Cannot do special collision with abnormal walls (yet) - doing normal jitter"
            self.jitter_ball(ball, kappa)
        elif kappa:
            v = ball.getvel()
            vang, vmag = velAngle(v[0], v[1])
            # Find the bounding angles
            if 0 < vang < np.pi/2.:
                bounds = (0, np.pi/2.)
            elif np.pi/2. < vang < np.pi:
                bounds = (np.pi/2., np.pi)
            elif np.pi < vang < np.pi*1.5:
                bounds = (np.pi, np.pi * 1.5)
            elif np.pi*1.5 < vang < np.pi*2.:
                bounds = (np.pi * 1.5, np.pi*2.)
            else:
                raise Exception("Angle outside of 0, 2pi")
            newang = np.random.vonmises(vang, kappa) % (2*np.pi)
            while not (bounds[0] < newang < bounds[1]):
                newang = np.random.vonmises(vang, kappa) % (2*np.pi)
            ball.setvel((vmag * np.cos(newang), vmag * np.sin(newang)))



    def on_wallhit(self, ball, wall):
        if self.cons_bounce:
            self.wall_collide(ball, wall, self.kapb)
        else:
            self.jitter_ball(ball, self.kapb)
    
    def on_addball(self, ball):
        self.jitter_ball(ball,self.kapv, self.perr)
    
    def on_step(self):
        if self.balls is not None: self.jitter_ball(self.balls, self.kapm)

class NoisyMultiTable(BasicTable):

    def __init__(self, dims, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF, *args, **kwds):

                     self.kapv = kapv
                     self.kapb = kapb
                     self.kapm = kapm
                     self.perr = perr
                     super(NoisyMultiTable, self).__init__(dims, *args, **kwds)

    def __del__(self):
        super(NoisyMultiTable,self).__del__()

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

    def on_ballhit(self, ballist):
        for b in ballist: self.jitter_ball(b,self.kapb)

    def on_addball(self, ball):
        self.jitter_ball(ball,self.kapv, self.perr)

    def on_step(self):
        if self.balls is not None:
            for b in self.balls: self.jitter_ball(b, self.kapm)

        
def makeNoisy(table, kapv = KAPV_DEF, kapb = KAPB_DEF, kapm = KAPM_DEF, perr = PERR_DEF,paddlereturn = SUCCESS,
              straddlepaddle = True, constrained_bounce=False):

    sttype = type(table) == SimpleTable

    try:
        import pygame
        if sttype:
            ntab = NoisyTable(table.dim, kapv, kapb, kapm, perr, constrained_bounce, table.stored_closed_ends, table.bk_c, table.dballrad, table.dballc, table.dpadlen, table.dwallc, table.doccc, table.dpadc, table.act, table.stored_soffset)
        else:
            ntab = NoisyMultiTable(table.dim, kapv, kapb, kapm, perr, constrained_bounce, table.stored_closed_ends, table.bk_c, table.dballrad, table.dballc, table.dpadlen, table.dwallc, table.doccc, table.dpadc, table.act, table.stored_soffset)
    except:
        if sttype:
            ntab = NoisyTable(table.dim,kapv,kapb,kapm,perr,constrained_bounce, table.stored_closed_ends,table.dballrad,table.dpadlen,table.act)
        else:
            ntab = NoisyMultiTable(table.dim,kapv,kapb,kapm,perr,constrained_bounce, table.stored_closed_ends,table.dballrad,table.dpadlen,table.act)
    ntab.set_timestep(table.basicts)
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

    if sttype:
        if table.balls: ntab.addBall(table.balls.getpos(), table.balls.getvel(), table.balls.getrad(), color = table.balls.col)
    else:
        for b in table.balls: ntab.addBall(b.getpos(),b.getvel(), b.getrad(), color = b.col)

    ntab.tm = table.tm

    return ntab
    
    

