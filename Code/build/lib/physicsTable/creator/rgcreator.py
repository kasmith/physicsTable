import os, sys, platform, time, warnings
import numpy as np
import pygame as pg
from pygame.constants import *
from .. import RedGreenTrial, BasicTable, SimpleTable, loadTrial, constants
from rgcmenu import *
from rgccursors import RGCursor
import Tkinter, tkFileDialog, tkMessageBox

# Figure out which keys are the modifiers
if platform.system() == 'Darwin':
    MODKEYS = [K_LMETA, K_RMETA]
else:
    MODKEYS = [K_LCTRL, K_RCTRL]

def pause():
    waiting = True
    while waiting:
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_ESCAPE: sys.exit(0)
            elif event.type == MOUSEBUTTONDOWN: waiting = False

# Takes an object and the new upper-left, then moves the lower right too
def move(obj, newul):
    w = obj[1][0] - obj[0][0]
    h = obj[1][1] - obj[0][1]
    return (newul, (newul[0] + w, newul[1] + h))
            
# Takes an object and the new size, then moves the lower right
def resize(obj, newsize):
    return(obj[0], (obj[0] + newsize[0], obj[1] + newsize[1]))

def objtype(objname):
    if objname in ['ball','rgoal','ggoal']: return objname
    elif objname[0]=='w': return 'wall'
    elif objname[0]=='o': return 'occ'
    else: return None
    
def euclidDist(p1, p2):
    return np.linalg.norm(np.array(p1)-np.array(p2))
    
def getCorner(pt, rect):
    uld = euclidDist(rect.topleft,pt)
    urd = euclidDist(rect.topright,pt)
    bld = euclidDist(rect.bottomleft,pt)
    brd = euclidDist(rect.bottomright,pt)
    if uld == min([uld,urd,bld,brd]): return 'topleft'
    elif urd == min([uld,urd,bld,brd]): return 'topright'
    elif bld == min([uld,urd,bld,brd]): return 'bottomleft'
    elif brd == min([uld,urd,bld,brd]): return 'bottomright'

defcols = {'ball': BLUE, 'ggoal': GREEN, 'rgoal': RED, 'wall': BLACK, 'occ': GREY}
DEFBALLRAD = 20
FPS = 25



class Action(object):
    
    # Acceptable acttypes:
    #  add, delete, move, resize
    #
    # Acceptable objtypes:
    #  rgoal, ggoal, wall, occ
    #
    # Specifics for each acttype:
    #  add: (upper-left, lower-right)
    #  delete: (upper-left, lower-right)
    #  replace: (new-upper-left, new-lower-right, old-upper-left, old-lower-right)
    #  move: (new-upper-left, old-upper-left)
    #  resize: (new-size, old-size)
    
    def __init__(self, acttype,objtype, objname, specifics):
        self.acttype = acttype
        self.objtype = objtype
        self.objname = objname
        self.specifics = specifics
        
    def reverse(self):
        if self.acttype == 'add':
            return Action('delete',self.objtype,self.objname, self.specifics)
        elif self.acttype == 'delete':
            return Action('add',self.objtype,self.objname, self.specifics)
        elif self.acttype == 'replace':
            return Action('replace',self.objtype,self.objname, (self.specifics[2],self.specifics[3],self.specifics[0],self.specifics[1]))
        elif self.acttype == 'move':
            return Action('move',self.objtype,self.objname, (self.specifics[1],self.specifics[0]))
        elif self.acttype == 'resize':
            return Action('resize', self.objtype,self.objname, (self.specifics[1],self.specifics[0]))
        else:
            raise Exception('Oops! Something went wrong with this action reversal!')

class BallAction(Action):
    
    # Acttypes same as above
    # Specifics for each acttype:
    #  add: (center, velocity, radius)
    #  delete: (center, velocity, radius)
    #  replace: (new-center, new-velocity, new-rad, old-center, old-velocity, old-rad)
    #  move: (new-center, new-vel, old-center, old-vel)
    #  resize: (new-rad, old-rad)
    
    def __init__(self, acttype, specifics):
        self.acttype = acttype
        self.objtype = 'ball'
        self.objname = 'ball'
        self.specifics = specifics
    def reverse(self):
        if self.acttype == 'add':
            return BallAction('delete',self.specifics)
        elif self.acttype == 'delete':
            return BallAction('add',self.specifics)
        elif self.acttype == 'replace':
            return BallAction('replace',(self.specifics[3],self.specifics[4],self.specifics[5],self.specifics[0],self.specifics[1],self.specifics[2]))
        elif self.acttype == 'move':
            return BallAction('move',(self.specifics[2], self.specifics[3], self.specifics[0], self.specifics[1]))
        elif self.acttype == 'resize':
            return BallAction('resize',(self.specifics[1], self.specifics[0]))
        else:
            raise Exception('Oops! Something went wrong with this action reversal!')
                          

class RGCreator(object):
    
    def __init__(self, tbdims, quitonquit = True):
        self.sizeScreen(tbdims)
        
        self.name = 'Untitled'
        self.qonq = quitonquit
        
        # Set up object lists
        self.ball = None
        self.rgoal = None
        self.ggoal = None
        self.walls = dict()
        self.occs = dict()
        self.wct = 0
        self.oct = 0
        
        self.curaction = None
        self.changed = False # Tests if change since last save
        
        self.curs = None
        
        self.clk = pg.time.Clock()
        
        self.deffl = None
        
        self.selectedobj = None
        
        # To add later
        self.undostack = []
        self.redostack = []
        
        self.tkon = False
    
    # Runs the creator from scratch
    def runCreator(self):
        # Set up Tkinter & pygame 
        root = Tkinter.Tk()
        root.withdraw()
        self.tkon = True
        pg.init()
        sc = pg.display.set_mode(self.dims)
        sc.blit(self.draw(), (0,0))
        pg.display.flip()
        
        self.curs = RGCursor()
        
        while True:
            for e in pg.event.get():
                act = None
                if e.type == QUIT: self.quit()
                    
                elif e.type == MOUSEBUTTONDOWN:
                    act = self.doclick(pg.mouse.get_pos())
                elif e.type == KEYDOWN: 
                    act = self.dokey()
    
                if act:
                    if act == 'resize':
                        sc = pg.display.set_mode(self.dims)
                    sc.blit(self.draw(), (0,0))
                    pg.display.flip()
                
    # Runs the table forward in its given state
    def play(self):
        tr = self.makeTrial()
        if tr is None:
            #tkMessageBox.showerror('Trial error!', 'Trial is not a valid red/green trial. Needs the ball, each goal, and no overlaps between ball, goals, and wall')
            return None
        
        tb = tr.makeTable()
        self.menu.buttons['play'].setIcon('stop')
        self.menu.disableButtonsButOne('play')
        
        sc = pg.display.get_surface()
        sf = self.draw()
        sf.blit(tb.draw(), self.tbpos)
        sc.blit(sf, (0,0))
        pg.display.flip()
        running = True
        
        while True:
            self.clk.tick(FPS)
            if running:
                if tb.step( 1. / FPS ): running = False
            for e in pg.event.get():
                if e.type == QUIT: self.quit()
                elif e.type == MOUSEBUTTONDOWN:
                    act = self.menu.checkClick(pg.mouse.get_pos())
                    if act == 'play':
                        self.menu.buttons['play'].setIcon('play')
                        self.menu.enableButtons()
                        if len(self.undostack) == 0: self.menu.buttons['undo'].disable()
                        if len(self.redostack) == 0: self.menu.buttons['redo'].disable()
                        return True
            sf.blit(tb.draw(), self.tbpos)
            sc.blit(sf, (0,0))
            pg.display.flip()
            
    
    
    # Safe quitting from anywhere
    def quit(self):
        if self.changed:
            dosave = tkMessageBox.askyesno('Save?', 'Would you like to save before quitting?')
            if dosave:
                sv = self.save()
                if sv is None: return False
        pg.quit()
        if self.qonq: sys.exit(0)
    
    # Figure out what action to do based on keyboard press
    def dokey(self):
        kp = pg.key.get_pressed()
        act = None
        if kp[MODKEYS[0]] or kp[MODKEYS[1]]:
            if kp[K_q]: self.quit() # Quit
            if kp[K_z]: # Undo
                if len(self.undostack) > 0: self.implementAction(self.undostack.pop(),isundo=True)
                if len(self.undostack) == 0: self.menu.buttons['undo'].disable()
                return True
            if kp[K_y]: # Redo
                if len (self.redostack) > 0: self.implementAction(self.redostack.pop(),isredo = True)
                if len(self.redostack) == 0: self.menu.buttons['redo'].disable()
                return True
            if kp[K_s]: self.save(); return True
            if kp[K_o]: self.load(); return 'resize'
        
        # Delete action
        elif kp[K_BACKSPACE] or kp[K_DELETE]:
            if self.selectedobj == 'ball': act = BallAction('delete', self.ball)
            elif self.selectedobj == 'ggoal': act = Action('delete','ggoal','ggoal',self.ggoal)
            elif self.selectedobj == 'rgoal': act = Action('delete','rgoal','rgoal',self.rgoal)
            elif self.selectedobj[0] == 'w': act = Action('delete','wall',self.selectedobj,self.walls[self.selectedobj])
            elif self.selectedobj[0] == 'o': act = Action('delete','occ',self.selectedobj,self.occs[self.selectedobj])
                
        elif kp[K_UP]:
            if self.selectedobj == 'ball': act = BallAction('move', ((self.ball[0][0],self.ball[0][1]-1), self.ball[1], self.ball[0], self.ball[1]))
            elif self.selectedobj:
                so = self.getObjRect(self.selectedobj)
                act = Action('move',objtype(self.selectedobj),self.selectedobj, ((so.left, so.top-1), so.topleft))
        elif kp[K_DOWN]:
            if self.selectedobj == 'ball': act = BallAction('move', ((self.ball[0][0],self.ball[0][1]+1), self.ball[1], self.ball[0], self.ball[1]))
            elif self.selectedobj:
                so = self.getObjRect(self.selectedobj)
                act = Action('move',objtype(self.selectedobj),self.selectedobj, ((so.left, so.top+1), so.topleft))
        elif kp[K_RIGHT]:
            if self.selectedobj == 'ball': act = BallAction('move', ((self.ball[0][0]+1,self.ball[0][1]), self.ball[1], self.ball[0], self.ball[1]))
            elif self.selectedobj:
                so = self.getObjRect(self.selectedobj)
                act = Action('move',objtype(self.selectedobj),self.selectedobj, ((so.left+1, so.top), so.topleft))
        elif kp[K_LEFT]:
            if self.selectedobj == 'ball': act = BallAction('move', ((self.ball[0][0]-1,self.ball[0][1]), self.ball[1], self.ball[0], self.ball[1]))
            elif self.selectedobj:
                so = self.getObjRect(self.selectedobj)
                act = Action('move',objtype(self.selectedobj),self.selectedobj, ((so.left-1, so.top), so.topleft))
        
        if act:
            self.implementAction(act)
            return True
        else: return False
    
    # Performs actions arising from mouse clicks
    def doclick(self, mpos):
        # In menu territory
        if mpos[1] < 50:
            act = self.menu.checkClick(mpos)
            if act == 'load': self.load(); return 'resize'
            elif act == 'save': self.save(); return True
            elif act == 'saveas': self.save(saveas = True); return True
            elif act == 'undo':
                self.implementAction(self.undostack.pop(),isundo=True)
                if len(self.undostack) == 0: self.menu.buttons['undo'].disable()
                return True
            elif act == 'redo':
                self.implementAction(self.redostack.pop(),isredo = True)
                if len(self.redostack) == 0: self.menu.buttons['redo'].disable()
                return True
            elif act == 'play':
                self.play()
                return True
            elif act == 'record':
                self.record()
                return True
            elif act in ['cursor','ball','ggoal','rgoal','wall','occ']:
                self.curaction = act
                self.menu.clearAct(act)
                self.selectedobj = None
                return True
            
        # Otherwise in table territory
        elif mpos[0] > self.tbpos[0] and mpos[0] < (self.tbpos[0] + self.tbdim[0]):
            # Adding rectangular objects
            if self.curaction in ['ggoal','rgoal','wall','occ']:
                nobj = self.findRect(mpos, defcols[self.curaction])
                if self.curaction == 'ggoal':
                    if self.ggoal: act = Action('replace','ggoal','ggoal',nobj + self.ggoal)
                    else: act = Action('add','ggoal','ggoal',nobj)
                elif self.curaction == 'rgoal':
                    if self.rgoal: act = Action('replace','rgoal','rgoal',nobj + self.rgoal)
                    else: act = Action('add','rgoal','rgoal',nobj)
                elif self.curaction == 'wall':
                    nm = 'w'+str(self.wct)
                    self.wct += 1
                    act = Action('add','wall',nm,nobj)
                elif self.curaction == 'occ':
                    nm = 'o' + str(self.oct)
                    self.oct += 1
                    act = Action('add','occ',nm, nobj)
                self.implementAction(act)
                return True
            
            # Adding the ball
            elif self.curaction == 'ball':
                vel = self.findBall(mpos, DEFBALLRAD)
                if self.ball: act = BallAction('replace', (self.mouseontab(mpos),vel,DEFBALLRAD) + self.ball)
                else: act = BallAction('add', (self.mouseontab(mpos), vel, DEFBALLRAD) )
                self.implementAction(act)
                return True
            
            # Cursor selects then moves
            elif self.curaction == 'cursor':
                if self.selectedobj: 
                    if self.getObjRect(self.selectedobj).collidepoint(self.mouseontab(mpos)):
                        self.docursor(mpos)
                        return True
                
                if self.ball:
                    if self.getObjRect('ball').collidepoint(self.mouseontab(mpos)):
                        self.selectedobj = 'ball'
                        self.docursor(mpos)
                        return True
                
                if self.rgoal:
                    if self.getObjRect('rgoal').collidepoint(self.mouseontab(mpos)):
                        self.selectedobj = 'rgoal'
                        self.docursor(mpos)
                        return True
                
                if self.ggoal:
                    if self.getObjRect('ggoal').collidepoint(self.mouseontab(mpos)):
                        self.selectedobj = 'ggoal'
                        self.docursor(mpos)
                        return True
                    
                for wk in self.walls.keys():
                    if self.getObjRect(wk).collidepoint(self.mouseontab(mpos)):
                        self.selectedobj = wk
                        self.docursor(mpos)
                        return True
                    
                for ok in self.occs.keys():
                    if self.getObjRect(ok).collidepoint(self.mouseontab(mpos)):
                        self.selectedobj = ok
                        self.docursor(mpos)
                        return True
                
        return None
    
    # Runs the movement or resizing of the selected object
    def docursor(self, mpos):
        
        # Make sure the button is held down for more than 200ms before any moving or resizing
        stime = time.time()
        while (time.time() - stime) < .2:
            if not any(pg.mouse.get_pressed()): return False
        
        orect = self.getObjRect(self.selectedobj)
        shr = orect.inflate(-.2*orect.width, -.2*orect.height)
        act = None
        # Replacing ball velocity
        if self.selectedobj == 'ball' and pg.mouse.get_pressed()[2]:
            self.curs.set('none')
            newvel = self.findBall(self.objonscreen(self.ball[0]),self.ball[2])
            act = BallAction('move',(self.ball[0],newvel,self.ball[0],self.ball[1]))
            self.curs.set('default')
        
        # Moving objects - placeholder until test for resizing
        elif shr.collidepoint(mpos):
            self.curs.set('move')
            act = self.domove(mpos)
            self.curs.set('default')
        else:
            self.curs.set('resize')
            # Find the closest corner
            corn = getCorner(self.mouseontab(mpos), orect)
            orig = [orect.topleft,orect.bottomright]
            if corn == 'topleft': act = self.doresize(orect.bottomright,mpos,orig)
            elif corn == 'topright': act = self.doresize(orect.bottomleft,mpos,orig)
            elif corn == 'bottomleft': act = self.doresize(orect.topright,mpos,orig)
            elif corn == 'bottomright': act = self.doresize(orect.topleft,mpos,orig)
            self.curs.set('default')
            
        if act: self.implementAction(act); return True
        else: return False
    
    def doresize(self, ref, mpos,origobj):
        if self.selectedobj == 'ball':
            while True:
                nmpos = self.mouseontab(self.bindmouse(pg.mouse.get_pos()))
                bpos = self.ball[0]
                
                nrad = int(euclidDist(nmpos,bpos))
                sc = pg.display.get_surface()
                sf = self.draw([self.selectedobj])
                pg.draw.circle(sf,BLUE,self.objonscreen(bpos),nrad)
                sc.blit(sf,(0,0))
                pg.display.flip()
                for e in pg.event.get():
                    if e.type == QUIT: self.quit()
                    if e.type == MOUSEBUTTONUP:
                        return BallAction('replace',[self.ball[0],self.ball[1],nrad,self.ball[0],self.ball[1],self.ball[2]]) 
                self.clk.tick(FPS)
        else:
            col = defcols[objtype(self.selectedobj)]
            while True:
                nmpos = self.mouseontab(self.bindmouse(pg.mouse.get_pos()))
                
                top = min(ref[1],nmpos[1])
                bottom = max(ref[1],nmpos[1])
                left = min(ref[0],nmpos[0])
                right = max(ref[0],nmpos[0])
                
                drect = pg.Rect(left + self.tbpos[0],top + self.tbpos[1],right-left,bottom-top)
                sc = pg.display.get_surface()
                sf = self.draw([self.selectedobj])
                pg.draw.rect(sf,col,drect,3)
                sc.blit(sf,(0,0))
                pg.display.flip()
                for e in pg.event.get():
                    if e.type == QUIT: self.quit()
                    if e.type == MOUSEBUTTONUP:
                        return Action('replace',objtype(self.selectedobj),self.selectedobj,[(left,top),(right,bottom)]+origobj) 
                self.clk.tick(FPS)
        
    def domove(self, mpos):
        if self.selectedobj == 'ball':
            bpos = self.ball[0]
            brad = self.ball[2]
            while True:
                nmpos = pg.mouse.get_pos()
                mpoff = (nmpos[0] - mpos[0], nmpos[1] - mpos[1])
                npos = (min(max(bpos[0]+mpoff[0],brad),self.tbdim[0]-brad),
                        min(max(bpos[1]+mpoff[1],brad),self.tbdim[1]-brad))
                sc = pg.display.get_surface()
                sf = self.draw([self.selectedobj])
                pg.draw.circle(sf,BLUE,(npos[0] + self.tbpos[0], npos[1]+self.tbpos[1]),brad)
                sc.blit(sf,(0,0))
                pg.display.flip()
                
                for e in pg.event.get():
                    if e.type == QUIT: self.quit()
                    if e.type == MOUSEBUTTONUP:
                        return BallAction('move',[npos, self.ball[1],self.ball[0],self.ball[1]])
                
                self.clk.tick(FPS)
                
                
        else:
            sorect = self.getObjRect(self.selectedobj)
            col = defcols[objtype(self.selectedobj)]
            while True:
                nmpos = pg.mouse.get_pos()
                mpoff = (nmpos[0] - mpos[0], nmpos[1] - mpos[1])
                nrect = sorect.move(mpoff)
                nrect.top = max(0,nrect.top)
                nrect.left = max(0,nrect.left)
                nrect.right = min(self.tbdim[0],nrect.right)
                nrect.bottom = min(self.tbdim[1],nrect.bottom)
                
                sc = pg.display.get_surface()
                sf = self.draw([self.selectedobj])
                pg.draw.rect(sf,col, nrect.move(self.tbpos))
                sc.blit(sf,(0,0))
                pg.display.flip()
                
                for e in pg.event.get():
                    if e.type == QUIT: self.quit()
                    if e.type == MOUSEBUTTONUP:
                        return Action('move',objtype(self.selectedobj),self.selectedobj,[nrect.topleft, sorect.topleft])
                
                self.clk.tick(FPS)
            
                
    
    def getObjRect(self, oname):
        if oname == 'ball':
            rad = self.ball[2]
            r = ( (self.ball[0][0] - rad, self.ball[0][1] - rad), (self.ball[0][0] + rad, self.ball[0][1] + rad) )
        elif oname == 'rgoal': r = self.rgoal
        elif oname == 'ggoal': r = self.ggoal
        elif oname[0] == 'w': r = self.walls[oname]
        elif oname[0] == 'o': r = self.occs[oname]
        else: print oname
        
        return pg.Rect(r[0], (r[1][0] - r[0][0], r[1][1] - r[0][1]) )
    
    
    def findRect(self, origpos, col):
        # Goes until mouse up
        pg.mouse.set_visible(False)
        while True:
            mpos = self.bindmouse(pg.mouse.get_pos())
            l = min(mpos[0], origpos[0])
            r = max(mpos[0], origpos[0])
            u = min(mpos[1], origpos[1])
            b = max(mpos[1], origpos[1])
            sc = self.draw()
            pg.draw.rect(sc, col, pg.Rect((l,u), (r - l, b - u)), 3)
            pg.display.get_surface().blit(sc,(0,0))
            pg.display.flip()
            for e in pg.event.get():
                if e.type == QUIT: self.quit()
                    
                if e.type == MOUSEBUTTONUP:
                    pg.mouse.set_visible(True)
                    return ( self.mouseontab( (l,u) ), self.mouseontab( (r,b) ) )
            self.clk.tick(20)
    # Binds the mouse to within the physics table area
    def bindmouse(self, mpos):
        x = min(max(mpos[0], self.tbpos[0]), self.tbpos[0] + self.tbdim[0])
        y = min(max(mpos[1], self.tbpos[1]), self.tbpos[1] + self.tbdim[1])
        return (x,y)
    
    # Finds the velocity of the ball
    def findBall(self, origpos, rad):
        pg.mouse.set_visible(False)
        while True:
            mpos = self.bindmouse(pg.mouse.get_pos())
            sc = self.draw(['ball'])
            pg.draw.circle(sc, BLUE, origpos, rad, 3)
            pg.draw.line(sc, BLUE, origpos, mpos, 3)
            pg.display.get_surface().blit(sc,(0,0))
            pg.display.flip()
            for e in pg.event.get():
                if e.type == QUIT: self.quit()
                if e.type == MOUSEBUTTONUP:
                    pg.mouse.set_visible(True)
                    return ( mpos[0] - origpos[0], mpos[1] - origpos[1] )
            self.clk.tick(20)
    
    # Takes an action object and makes it happen
    def implementAction(self, action, isundo = False, isredo = False):        
        if action.acttype == 'add':
            if action.objtype == 'ball':
                self.ball = action.specifics
            elif action.objtype == 'rgoal':
                self.rgoal = action.specifics
            elif action.objtype == 'ggoal':
                self.ggoal = action.specifics
            elif action.objtype == 'wall':
                self.walls[action.objname] = action.specifics
            elif action.objtype == 'occ':
                self.occs[action.objname] = action.specifics
        elif action.acttype == 'delete':
            self.selectedobj = None
            if action.objtype == 'ball': self.ball = None
            elif action.objtype == 'rgoal': self.rgoal = None
            elif action.objtype == 'ggoal': self.ggoal = None
            elif action.objtype == 'wall': del self.walls[action.objname]
            elif action.objtype == 'occ': del self.occs[action.objname]
        elif action.acttype == 'replace':
            if action.objtype == 'ball':
                self.ball = action.specifics[:3]
            elif action.objtype == 'rgoal':
                self.rgoal = action.specifics[:2]
            elif action.objtype == 'ggoal':
                self.ggoal = action.specifics[:2]
            elif action.objtype == 'wall':
                self.walls[action.objname] = action.specifics[:2]
            elif action.objtype == 'occ':
                self.occs[action.objname] = action.specifics[:2]
        elif action.acttype == 'move':
            if action.objtype == 'ball': self.ball = (action.specifics[0], action.specifics[1], self.ball[2])
            elif action.objtype == 'rgoal': self.rgoal = move(self.rgoal, action.specifics[0])
            elif action.objtype == 'ggoal': self.ggoal = move(self.ggoal, action.specifics[0])
            elif action.objtype == 'wall':
                w = self.walls[action.objname]
                self.walls[action.objname] = move(w,action.specifics[0])
            elif action.objtype == 'occ':
                o = self.occs[action.objname]
                self.occs[action.objname] = move(o, action.specifics[0])
        elif action.acttype == 'resize':
            if action.objtype == 'ball': self.ball = (self.ball[0], self.ball[1], action.specifics[0])
            elif action.objtype == 'rgoal': self.rgoal = resize(self.rgoal, action.specifics[0])
            elif action.objtype == 'ggoal': self.ggoal = resize(self.ggoal, action.specifics[0])
            elif action.objtype == 'wall':
                w = self.walls[action.objname]
                self.walls[action.objname] = resize(w, action.specifics[0])
            elif action.objtype == 'occ':
                o = self.occs[action.objname]
                self.occs[action.objname] = resize(o, action.specifics[0])
        if isundo:
            self.redostack.append(action.reverse())
            if len(self.redostack) > 100:
                self.redostack = self.redostack[1:]
            self.menu.buttons['redo'].enable()
        else:
            self.undostack.append(action.reverse())
            if len(self.undostack) > 100:
                self.undostack = self.undostack[1:]
            self.menu.buttons['undo'].enable()
            if not isredo: self.redostack = []; self.menu.buttons['redo'].disable()
            
        
        self.changed = True
    
    # Sets the dimensions of the screen based on object size
    def sizeScreen(self, tbdims):
        self.tbdim = tbdims
        self.dims = (max(self.tbdim[0] + 4, 600), self.tbdim[1] + 52)
        self.menu = RGMenu(self.dims[0])
        self.tbpos = ( int((self.dims[0] - self.tbdim[0])/2) , 50)
    
    # Offset mouse clicks or objects
    def mouseontab(self, mpos): return (mpos[0] - self.tbpos[0], mpos[1] - self.tbpos[1])
    def objonscreen(self, pos): return(pos[0] + self.tbpos[0], pos[1] + self.tbpos[1])
    
    # Helper function for drawing rectangular items in native form
    def drawRectThing(self, sc, obj, color):
        ul = obj[0]
        lr = obj[1]
        w = lr[0] - ul[0]
        h = lr[1] - ul[1]
        pg.draw.rect(sc, color, pg.Rect(ul, (w,h) ))
    
    def draw(self, excludeobjs = []):
        surf = pg.Surface(self.dims)
        surf.blit(self.menu.draw(), (0,0))
        
        # Draw the table
        tabsurf = pg.Surface(self.tbdim)
        tabsurf.fill(WHITE)
        
        if self.ball and 'ball' not in excludeobjs: pg.draw.circle(tabsurf, BLUE, self.ball[0], self.ball[2])
        for k in self.occs.keys():
            if k not in excludeobjs: self.drawRectThing(tabsurf, self.occs[k], GREY)
        for k in self.walls.keys(): 
            if k not in excludeobjs: self.drawRectThing(tabsurf, self.walls[k], BLACK)
        if self.rgoal and 'rgoal' not in excludeobjs: self.drawRectThing(tabsurf, self.rgoal, RED)
        if self.ggoal and 'ggoal' not in excludeobjs: self.drawRectThing(tabsurf, self.ggoal, GREEN)
        
        if self.selectedobj and self.selectedobj not in excludeobjs:
            rct = self.getObjRect(self.selectedobj)
            pg.draw.rect(tabsurf, PURPLE, rct.inflate(4,4),2)
        
        surf.blit(tabsurf, self.tbpos)
        return surf
    
    def record(self, movfl = None):
        
        tr = self.makeTrial()
        if tr is None: return None
        
        if movfl is None:
            movfl = tkFileDialog.asksaveasfilename(defaultextension='.mov', initialfile = self.name+'.mov')
            if movfl == '': return None
        
        movpath = os.path.dirname(movfl)
        movnm = os.path.basename(movfl)
        
        tb = tr.makeTable()
        with warnings.catch_warnings(record = True) as w:
            warnings.simplefilter('always')
            isgood = tb.makeMovie(movnm, movpath)
            if not isgood:
                tkMessageBox.showerror('Cannot make movie!', str(w[0].message))
                return None
            else:
                tkMessageBox.showinfo('Done!','Your movie has been created')
                return True
    
    def load(self, trpath = None):
        if trpath is None:
            if self.tkon:
                trpath = tkFileDialog.askopenfilename(filetypes = [('PhysicsTrials','*.ptr')])
                if trpath == '': return False
            else: return False
        
        try:
            tr = loadTrial(trpath)
        except:
            if self.tkon: tkMessageBox.showerror('File not found!','File not found!')
            else: warnings.warn( "File not found!")
            return False
        if tr.__class__.__name__ != "RedGreenTrial":
            if self.tkon: tkMessageBox.showerror('Incorrect file type','File is not a RedGreenTrial type')
            else: warnings.warn( "File is not a RedGreenTrial type")
            return False
        
        for g in tr.goals:
            if g[2] not in [REDGOAL, GREENGOAL]:
                if self.tkon: tkMessageBox.showerror('Goal error','Goal that is not red or green found')
                else: warnings.warn( "Goal that is not red or green found")
                return False
        
        self.sizeScreen(tr.dims)
        self.name = tr.name
        self.ball = (tr.ball[0], tr.ball[1], tr.ball[2])
        self.walls = dict()
        self.occs = dict()
        for g in tr.goals:
            if g[2] == REDGOAL: self.rgoal = g[0:2]
            elif g[2] == GREENGOAL: self.ggoal = g[0:2]
        self.wct = 0
        for w in tr.normwalls:
            self.walls['w'+str(self.wct)] = w[0:2]
            self.wct += 1
        self.oct = 0
        for o in tr.occs:
            self.occs['o'+str(self.oct)] = o[0:2]
            self.oct += 1
        if len(tr.abnormwalls) > 0:
            if self.tkon: tkMessageBox.showwarning('Feature not implemented yet!', "Abnormal walls (polygons) not supported yet and will not be loaded" )
            else: warnings.warn( "Abnormal walls (polygons) not supported yet and will not be loaded" )
        self.changed = False
        self.deffl = trpath
        
        return True
        
    def makeTrial(self, bvel = 300):
        if self.ball is None or self.rgoal is None or self.ggoal is None:
            tkMessageBox.showerror('Missing object','Cannot do this until you have a ball, red goal, and green goal')
            return None
        tr = RedGreenTrial(self.name, self.tbdim, def_ball_vel=bvel)
        tr.addBall(self.ball[0],self.ball[1],self.ball[2])
        tr.addGoal(self.rgoal[0],self.rgoal[1],REDGOAL,RED)
        tr.addGoal(self.ggoal[0],self.ggoal[1],GREENGOAL,GREEN)
        for w in self.walls.values():
            tr.addWall(w[0],w[1])
        for o in self.occs.values():
            tr.addOcc(o[0],o[1])
        tr.normalizeVel()
        
        with warnings.catch_warnings(record = True) as w:
            warnings.simplefilter('always')
            consist = tr.checkConsistency()
            if len(w) > 1:
                msg = "Multiple trial errors:"
                for wm in w:
                    msg += '\n' + str(wm.message)
                tkMessageBox.showerror('Trial consistency error!',msg)
            elif len(w) == 1:
                tkMessageBox.showerror('Trial consistency error!',str(w[0].message))
        if not consist: return None
        return tr
    
    def save(self, flnm = None, saveas = False):
        
        tr = self.makeTrial()
        if tr is None:
            #tkMessageBox.showerror('Trial error!', 'Trial is not a valid red/green trial. See console for details on what must be changed.')
            return None
        
        if flnm is None and (self.deffl is None or saveas):
            if self.deffl is None: nm = self.name + '.ptr'
            else: nm = os.path.basename(self.deffl)
            flnm = tkFileDialog.asksaveasfilename(defaultextension='.ptr', initialfile = nm)
            if flnm == '': return False
        else: flnm = self.deffl
        
        tr.save(flnm, askoverwrite = False)
        self.deffl = flnm
        self.name = os.path.splitext(os.path.basename(flnm))[0]
        self.changed = False
        return True
    
if __name__ == '__main__':
    
    rgc = RGCreator((900,900))
    rgc.runCreator()
        