####################################################################
#
# Introduces drawing/pygame functions for tables via duck punching
#
####################################################################

from ..basicTable import BasicTable
from ..simpleTable import SimpleTable
from ..constants import *
from ..objects import *
from .__init__ import screenPause
import pygame as pg
from pygame.constants import *
import numpy as np
import sys


# Duck punching the BasicTable
btabinit = BasicTable.__init__
def btvinit(self, dims, closed_ends = [LEFT, RIGHT, BOTTOM, TOP], background_cl = WHITE, \
                 def_ball_rad = 20, def_ball_cl = BLUE,def_pad_len = 100, def_wall_cl = BLACK, \
                 def_occ_cl = GREY, def_pad_cl = BLACK, active = True, soffset = None, defscreen = None):
    btabinit(self,dims,closed_ends,def_ball_rad,def_pad_len, active)

    self.bk_c = background_cl
    self.dballc = def_ball_cl
    self.dwallc = def_wall_cl
    self.doccc = def_occ_cl
    self.dpadc = def_pad_cl

    self.stored_soffset = soffset
    # Make surface and objects
    dsurf = pg.display.get_surface()
    if soffset is not None: self.soff = soffset
    else: self.soff = (0,0)
    if defscreen is None and dsurf is None: self.surface = pg.Surface(dims)
    else:
        if defscreen is None: defscreen = dsurf
        if soffset is None:
            bigdim = defscreen.get_size()
            xoff = int((bigdim[0] - dims[0]) / 2.)
            yoff = int((bigdim[1] - dims[1]) / 2.)
            soffset = (xoff,yoff)
            self.soff = soffset
        thisrect = pg.Rect(soffset,dims)
        self.surface = defscreen.subsurface(thisrect)
BasicTable.__init__ = btvinit

def btassignSurface(self, surface, offset = None):
    if offset is None:
        bigdim = surface.get_size()
        xoff = int((bigdim[0] - self.dim[0]) / 2.)
        yoff = int((bigdim[1] - self.dim[1]) / 2.)
        offset = (xoff,yoff)
    thisrect = pg.Rect(offset, self.dim)
    self.surface = surface.subsurface(thisrect)
BasicTable.assignSurface = btassignSurface


def btdraw(self, stillshow = False):
    self.surface.fill(self.bk_c)

    if not stillshow:
        for b in self.balls: b.draw(self.surface)
    for o in self.occludes: o.draw(self.surface)
    for w in self.walls: w.draw(self.surface)
    for g in self.goals: g.draw(self.surface)
    if stillshow:
        for b in self.balls: b.draw(self.surface)

    if self.paddle: self.paddle.draw(self.surface)

    return self.surface
BasicTable.draw = btdraw


def btstep(self, t = 1/50., maxtime = None):
    substeps = t / self.basicts
    # Check for offsets in substeps, tolerant to rounding errors
    isubs = int(np.floor(substeps + 1e-7))
    if abs(substeps - isubs) > 1e-6:
        print "Warning: steps not evenly divisible - off by", (substeps - isubs)
    if self.paddle and pg.mouse.get_focused():
        self.paddle.update(self.getRelativeMousePos())
        #print any([sh == self.paddle.seg for sh in self.sp.shapes])
        self.sp.reindex_shape(self.paddle.seg)
    if self.act:
        for i in range(int(substeps)):
            self.on_step()
            self.sp.step(self.basicts)
            self.tm += self.basicts
            e = self.checkEnd()
            if e is not None: return e
            if maxtime and self.tm > maxtime: return TIMEUP
        return e
    else: return None
BasicTable.step = btstep

def btgetRelativeMousePos(self):
    mp = pg.mouse.get_pos()
    oset = self.surface.get_offset()
    return (mp[0]-oset[0],mp[1]-oset[1])
BasicTable.getRelativeMousePos = btgetRelativeMousePos

def btaddPaddle(self,p1, p2, padlen = None, padwid = 3, hitret = None, active = True, acol = BLACK, iacol = GREY, pthcol = LIGHTGREY, elast = 1., suppressoverwrite = False, pmsp = None):
    if pmsp is None: pmsp = self.sp
    if active: sta = self.sp
    else: sta = None
    if p1 == p2: print "Paddle endpoints must not overlap:",p1,p2; return None
    if p1[0] != p2[0] and p1[1] != p2[1]: print "Paddle must be horizontal or vertical",p1,p2; return None
    if padlen is None: padlen = self.dpadlen
    if self.paddle is not None and not suppressoverwrite: print "Warning! Overwriting old paddle"
    self.paddle = Paddle(p1,p2,padlen,acol,iacol,pthcol,padwid,hitret, sta, elast, self.sp.static_body,pmsp)
    return self.paddle
BasicTable.addPaddle = btaddPaddle


def btfastUpdate(self):
    pg.display.update(self.surface.get_rect().move(self.soff[0],self.soff[1]))
BasicTable.fastUpdate = btfastUpdate

def btdemonstrate(self, screen = None, timesteps = 1./50, retpath = False, onclick = None, maxtime = None, waitafter = True):
    frrate = int(1 / timesteps)
    if maxtime is not None: maxsteps = int(frrate * maxtime)
    else: maxsteps = 99999999999

    if screen is None:
        screen = pg.display.get_surface()

    #screen.fill(WHITE)
    offset = (int((screen.get_width() - self.dim[0])/2), int((screen.get_height() - self.dim[1])/2))
    #screen.blit(self.draw(),offset)
    self.draw()
    pg.display.flip()
    for event in pg.event.get(): pass # Flush queue
    stp = 0
    if retpath: rets = [[stp,self.balls.getpos()[0],self.balls.getpos()[1],self.balls.getvel()[0],self.balls.getvel()[1]]]
    '''
    waiting = True
    while waiting:
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_ESCAPE: sys.exit(0)
            elif event.type == MOUSEBUTTONDOWN: waiting = False
    '''
    screenPause(0.)
    clk = pg.time.Clock()
    running = True
    while running:
        if self.step(timesteps) is not None: running = False
        stp += 1
        fpsstr = "FPS: " + str(clk.get_fps())
        #if retpath: rets.append([stp,self.balls.getpos()[0],self.balls.getpos()[1],self.balls.getvel()[0],self.balls.getvel()[1]])
        #screen.fill(WHITE)
        #screen.blit(self.draw(),offset)
        self.draw()
        pg.display.set_caption(fpsstr)
        #pg.display.flip()
        self.fastUpdate()
        clk.tick(frrate)
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_ESCAPE: sys.exit(0)
            elif event.type == MOUSEBUTTONDOWN and onclick:
                onclick(self)
        if stp == maxsteps: running = False

    #if self.mostlyOcc(): return False
    self.draw()
    pg.display.flip()
    '''
    waiting = waitafter
    while waiting:
        for event in pg.event.get():
            if event.type == QUIT: sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_ESCAPE: sys.exit(0)
            elif event.type == MOUSEBUTTONDOWN: waiting = False
    '''
    if waitafter: screenPause(0.)

    #if retpath: return [self.tm, rets]
    return self.tm
BasicTable.demonstrate = btdemonstrate

def btmakeMovie(self, moviename, outputdir = '.', fps = 20, removeframes = True, maxtime = None):

    spl = moviename.split('.')
    if len(spl) == 2 and spl[1] != 'mov':
        warnings.warn('Incorrect extension - requires .mov')
        return None
    elif len(spl) == 2: moviename = spl[0]

    try:
        subprocess.call('ffmpeg',stdout = open(os.devnull,'w'),stderr=subprocess.STDOUT)
    except:
        warnings.warn('ffmpeg not installed - required to make movie')
        return None

    pthnm = os.path.join(outputdir, 'tmp_' + moviename)
    if not os.path.isdir(pthnm):
        os.mkdir(pthnm)

    if os.listdir(pthnm) != []:
        warnings.warn("Files exist in temporary directory " + pthnm + '; delete and try again')
        return None

    timeperframe = 1. / fps
    tnmbase = os.path.join(pthnm, moviename+'_%04d.png')

    pg.image.save(self.draw(),tnmbase % 0)
    i = 1
    running = True
    while running:
        e = self.step(t = timeperframe, maxtime = maxtime)
        pg.image.save(self.draw(),tnmbase % i)
        i += 1

        if e is not None: running = False


    ffcall = 'ffmpeg -y -r ' + str(fps) + ' -i ' + tnmbase + ' -pix_fmt yuv420p ' + os.path.join(outputdir, moviename + '.mov')
    ffargs = shlex.split(ffcall)
    print ffargs
    subprocess.call(ffargs)

    if removeframes:
        shutil.rmtree(pthnm)

    return True
BasicTable.makeMove = btmakeMovie

# Duck punch the simple table
def stdraw(self, stillshow = False):
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
SimpleTable.draw = stdraw

def stdemonstrate(self, screen = None, timesteps = 1./50, retpath = False, onclick = None,maxtime = None,waitafter = True):
    tm = super(SimpleTable, self).demonstrate(screen, timesteps, retpath, onclick, maxtime,waitafter)
    p = self.balls.getpos()
    if retpath: return [p, tm[0], tm[1]]
    else: return [p, tm]
SimpleTable.demonstrate = stdemonstrate


def stdrawPath(self, pathcl = None):
    if pathcl is None: pathcl = self.balls.col
    sc = self.draw()
    r, p = self.simulate(return_path = True)
    pg.draw.lines(sc,pathcl, False, p)
    return sc
SimpleTable.drawPath = stdrawPath
