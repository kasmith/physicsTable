import os, sys
import pygame as pg
from pygame.constants import *
from physicsTable.constants import *

# Load the menu icons
icondir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Icons')
isave = pg.image.load(os.path.join(icondir, 'Save.png'))
isaveas = pg.image.load(os.path.join(icondir, 'SaveAs.png'))
iload = pg.image.load(os.path.join(icondir, 'Load.png'))
iplay = pg.image.load(os.path.join(icondir, 'Play.png'))
istop = pg.image.load(os.path.join(icondir, 'Stop.png'))
iundo = pg.image.load(os.path.join(icondir, 'Undo.png'))
iredo = pg.image.load(os.path.join(icondir, 'Redo.png'))
iball = pg.image.load(os.path.join(icondir, 'Ball.png'))
irgoal = pg.image.load(os.path.join(icondir, 'RedGoal.png'))
iggoal = pg.image.load(os.path.join(icondir, 'GreenGoal.png'))
iwall = pg.image.load(os.path.join(icondir, 'Wall.png'))
iocc = pg.image.load(os.path.join(icondir, 'Occ.png'))
icurs = pg.image.load(os.path.join(icondir, 'Cursor.png'))
irec = pg.image.load(os.path.join(icondir, 'Record.png'))

class RGMenu(object):
    
    def __init__(self, xlen):
        self.dims = (xlen, 50)
        self.buttons = {'save': RGButton('save',(5,5),isave, False),
                        'saveas': RGButton('saveas',(50,5),isaveas,False),
                        'load': RGButton('load',(95,5),iload, False),
                        'play': RGButton('play',(140,5),iplay),
                        'record': RGButton('record',(185,5),irec,False),
                        'undo': RGButton('undo',(230,5), iundo, False, True),
                        'redo': RGButton('redo',(275, 5), iredo, False, True),
                        'cursor': RGButton('cursor',(320,5),icurs),
                        'ball': RGButton('ball',(365,5),iball),
                        'ggoal': RGButton('ggoal',(410,5),iggoal),
                        'rgoal': RGButton('rgoal',(455,5),irgoal),
                        'wall': RGButton('wall',(500,5),iwall),
                        'occ': RGButton('occ',(545,5),iocc)}
        
    def draw(self):
        surf = pg.Surface(self.dims)
        pg.draw.rect(surf,WHITE, pg.Rect((2,2), (self.dims[0]-4,self.dims[1]-4)))
        for bnm in self.buttons.keys():
            surf.blit(self.buttons[bnm].draw(), self.buttons[bnm].pos)
        return surf
    
    def checkClick(self, mpos):
        for k in self.buttons.keys():
            r = self.buttons[k].checkClick(mpos)
            if r: return r
        return None
        
    def clearAct(self, keepon = None):
        for k in self.buttons.keys():
            if k != keepon: self.buttons[k].pressed = False
    def disableButtonsButOne(self, keepon):
        for k in self.buttons.keys():
            if k != keepon: self.buttons[k].disable()
    
    def enableButtons(self):
        for b in self.buttons.values(): b.enable()
        

class RGButton(object):
    def __init__(self, name, pos, icon, allowpress = True, disab = False, size = (40,40)):
        self.name = name
        self.pos = pos
        self.icon = icon
        self.size = size
        self.allowpress = allowpress
        self.pressed = False
        self.ulicon = (int(size[0]/2-16), int(size[1]/2-16))
        self.disabled = disab
        
    def checkClick(self, cpos):
        if self.disabled: return None
        if cpos[0] > self.pos[0] and cpos[0] < (self.pos[0] + self.size[0]) and \
            cpos[1] > self.pos[1] and cpos[1] < (self.pos[1] + self.size[1]):
            self.pressed = self.allowpress
            return self.name
        else: return None
        
    def setIcon(self, newicon): self.icon = newicon
    
    def draw(self):
        surf = pg.Surface(self.size)
        if self.disabled: col = GREY
        else: col = WHITE
        if self.pressed: pg.draw.rect(surf, col, pg.Rect(self.ulicon, (32,32)))
        else: pg.draw.rect(surf, col, pg.Rect((1,1), (self.size[0]-2, self.size[1]-2)))
        surf.blit(self.icon, self.ulicon)
        return surf
    
    def disable(self): self.disabled = True
    def enable(self): self.disabled = False
            
        
    