from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import pygame as pg
from pygame.constants import *
import pymunk as pm
import sys, os, random, time

if __name__ == '__main__':
    
    args = sys.argv
    if len(args) != 2:
        print 'test.py takes one argument; valid tests are BASIC, NOISY, GRAVITY, SPEED, PATHFILTER, LIMTIME'
        sys.exit(0)
    
    if not args[1] in ['BASIC','NOISY','GRAVITY','SPEED','PATHFILTER', 'LIMTIME','NOISYBOUNCE']:
        print 'test.py takes one argument; valid tests are BASIC, NOISY, GRAVITY, SPEED, PATHFILTER, LIMTIME, NOISYBOUNCE'
        sys.exit(0)
        
    
    pg.init()
    
    
    if args[1] == 'BASIC':
        screen = pg.display.set_mode((1000,600))
        clock = pg.time.Clock()
        running = True
        table = BasicTable((800,400),soffset = (100,100))
        table.addBall((100,100),(300,-300))
        table.addWall((600,100),(700,300))
        table.addOcc((100,50),(600,150))
        table.addGoal((0,300),(100,400),SUCCESS, RED)
        print table.demonstrate()
        
    if args[1] == 'LIMTIME':
        screen = pg.display.set_mode((1000,600))
        clock = pg.time.Clock()
        running = True
        table = BasicTable((800,400),soffset = (100,100))
        table.addBall((100,100),(300,-300))
        table.addWall((600,100),(700,300))
        table.addOcc((100,50),(600,150))
        print table.demonstrate(maxtime = 5)
        
    elif args[1] == 'SPEED':
        screen = pg.display.set_mode((1000,600))
        clock = pg.time.Clock()
        running = True
        table = BasicTable((800,400),soffset = (100,100))
        table.addBall((100,100),(300,-300))
        table.addWall((600,100),(700,300))
        table.addOcc((100,50),(600,150))
        table.addGoal((0,300),(100,400),SUCCESS, RED)
        print table.demonstrate(timesteps = 1/200.)
    elif args[1] == 'NOISY':
        screen = pg.display.set_mode((1000,600))
        clock = pg.time.Clock()
        running = True
        table = SimpleTable((800,400))
        table.addBall((100,100),(300,-300))
        table.addWall((600,100),(700,300))
        table.addOcc((100,50),(600,150))
        table.addAbnormWall([(300,300),(300,400),(400,300),(400,200),(350,200)])
        table.addGoal((700,300),(800,400),SUCCESS,RED)
        table.addGoal((0,300),(100,400),SUCCESS, GREEN)
        
        while True:
            print 'split\n'
            noise = makeNoisy(table)
            noise.set_timestep(1/100.)
            noise.demonstrate()
            #pg.display.flip()
            
            running = True
            while running:
                for e in pg.event.get():
                    if e.type == QUIT: pg.quit(); sys.exit(0)
                    elif e.type == KEYDOWN and e.key == K_ESCAPE: pg.quit(); sys.exit(0)
                    elif e.type == MOUSEBUTTONDOWN: running = False
    
    elif args[1] == 'PATHFILTER':
        sampletrial = SimpleTrial('test',(800,400))
        sampletrial.addBall((100,100),(300,-300))
        sampletrial.addWall((600,100),(700,500))
        sampletrial.addWall((500, 200),(800,300))
        sampletrial.addGoal((0,300),(100,400),REDGOAL, RED)
        sampletrial.addGoal((0,200),(100,300),GREENGOAL, GREEN)
        sampletrial.addOcc((150,200),(500,400))
        clock = pg.time.Clock()
        sc = pg.display.set_mode((1200,900))
        sampocc = sampletrial
        
        while True:
            st = time.time()
            pt = PathFilter(sampocc.makeTable(), nparticles = 5)
            print "Setup time: ", (time.time()-st)
            tscreen = pt.draw(True)
            #sc.blit(tscreen,(0,0))
            pg.display.flip()
            running = True
            pg.event.clear()
        
            while running:
                    for e in pg.event.get():
                        if e.type == QUIT: pg.quit(); sys.exit(0)
                        elif e.type == KEYDOWN and e.key == K_ESCAPE: pg.quit(); sys.exit(0)
                        elif e.type == MOUSEBUTTONDOWN: running = False

            running = True
            st = time.time()
            while running:
                clock.tick(1/pt.tps)
                s = pt.step()
                if s is not None: running = False
                tscreen = pt.draw(True)
                pg.display.flip()

            et = time.time() - st
            print "Time: ", et
            running = True
            pg.event.clear()
            while running:
                    for e in pg.event.get():
                        if e.type == QUIT: pg.quit(); sys.exit(0)
                        elif e.type == KEYDOWN and e.key == K_ESCAPE: pg.quit(); sys.exit(0)
                        elif e.type == MOUSEBUTTONDOWN: running = False

    elif args[1] == "NOISYBOUNCE":
        sc = pg.display.set_mode((600,400))
        tr = SimpleTrial('test', (600, 400))
        tr.addWall((100,100), (600,400))
        tr.addBall((50,300),(50,-280),10)
        tr.addGoal((550,0),(600,100),REDGOAL,RED)
        tab = tr.makeTable()
        ntab = makeNoisy(tab, None, 30., None, None, constrained_bounce=True)
        ntab.demonstrate()

    pg.quit()
    sys.exit(0)

'''
elif args[1] == 'GRAVITY':
    xlim = 2000
    screen = pg.display.set_mode((xlim,500))
    running = True
    while running:
        spin = -20*random.random()
        table = GravityTable((xlim,500))
        table.addBall((100,100),(200,0),spin, rad = 30, elast = 1.)
        table.addPaddle(0,500,xlim - 500,xlim)
        table.addGoal((-100000,501),(2000,1000),FAILURE)
        table.addGoal((-1000,-100),(-1,600),FAILURE)
        table.addGoal((xlim+1,-100),(xlim+1000,600),FAILURE)
        table.demonstrate()
        wait = True
        while wait:
            for e in pg.event.get():
                if e.type == MOUSEBUTTONDOWN: wait = False
                elif e.type == QUIT: running = False
                elif e.type == KEYDOWN and e.key == K_ESCAPE: running = False
'''
