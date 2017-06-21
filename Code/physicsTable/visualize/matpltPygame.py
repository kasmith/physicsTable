import matplotlib
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg
import pylab
import pygame as pg
from pygame.constants import *

class pgFig(object):
    def __init__(self,figsize,dpi=100):
        self.fs = figsize
        self.dpi = dpi
        self.fig = pylab.figure(figsize=figsize,dpi=dpi)
        self.ax = self.fig.gca()

    # Various plots
    def plot(self,*args,**kwds): self.ax.plot(*args,**kwds)
    def bar(self,*args,**kwds): return self.ax.bar(*args,**kwds)
    def barh(self,*args,**kwds): return self.ax.barh(*args,**kwds)
    def boxplot(self,*args,**kwds): self.ax.boxplot(*args,**kwds)
    def broken_barh(self,*args,**kwds): self.ax.broken_barh(*args,**kwds)
    def bxp(self,*args,**kwds): self.ax.bxp(*args,**kwds)
    def contour(self,*args,**kwds): self.ax.contour(*args,**kwds)
    def errorbar(self,*args,**kwds): self.ax.errorbar(*args,**kwds)
    def fill(self,*args,**kwds): self.ax.fill(*args,**kwds)
    def fill_between(self,*args,**kwds): self.ax.fill_between(*args,**kwds)
    def fill_betweenx(self,*args,**kwds): self.ax.fill_betweenx(*args,**kwds)
    def hexbin(self,*args,**kwds): self.ax.hexbin(*args,**kwds)
    def hist(self,*args,**kwds): self.ax.hist(*args,**kwds)
    def hist2d(self,*args,**kwds): self.ax.hist2d(*args,**kwds)
    def loglog(self,*args,**kwds): self.ax.loglog(*args,**kwds)
    def matshow(self,*args,**kwds): self.ax.matshow(*args,**kwds)
    def pie(self,*args,**kwds): self.ax.pie(*args,**kwds)
    def plot_date(self,*args,**kwds): self.ax.plot_date(*args,**kwds)
    def scatter(self,*args,**kwds): self.ax.scatter(*args,**kwds)
    def stem(self,*args,**kwds): self.ax.stem(*args,**kwds)
    def table(self,**kwds): self.ax.table(**kwds)
    def text(self,*args,**kwds): self.ax.text(*args,**kwds)

    # Draws and returns a pygame Surface of the current graph
    def draw(self):
        dims = [self.fs[0]*self.dpi,self.fs[1]*self.dpi]
        canv = agg.FigureCanvasAgg(self.fig)
        canv.draw()
        renderer = canv.get_renderer()
        raw_dat = renderer.tostring_rgb()
        csize = canv.get_width_height()
        sc = pg.image.fromstring(raw_dat,csize,'RGB')
        return sc

    def xlim(self,xmin,xmax = None):
        if xmax is None:
            try:
                xmax = xmin[1]
                xmin = xmin[0]
            except:
                raise Exception('Must give exactly two axes')
        self.ax.axis(xmin=xmin,xmax=xmax)

    def ylim(self,ymin,ymax = None):
        if ymax is None:
            try:
                ymax = ymin[1]
                ymin = ymin[0]
            except:
                raise Exception('Must give exactly two axes')
        self.ax.axis(ymin=ymin,ymax=ymax)

    # Various key functions from matplotlib.axes
    def acorr(self,x,**kwds): self.ax.acorr(x,**kwds)
    def add_container(self,container): self.ax.add_container(container)
    def add_image(self,image): self.ax.add_image(image)
    def add_line(self,line): self.ax.add_line(line)
    def add_table(self,tab): self.ax.add_table(tab)
    def annotate(self,*args,**kwds): self.ax.annotate(*args,**kwds)
    def arrow(self,x,y,dx,dy,**kwds): self.ax.arrow(x,y,dx,dy,**kwds)
    def axhline(self,y=0,xmin=0,xmax=1,**kwds): self.ax.axhline(y,xmin,xmax,**kwds)
    def axhspan(self,ymin,ymax,xmin=0,xmax=1,**kwds): self.ax.axhspan(ymin,ymax,xmin,xmax,**kwds)
    def axis(self,*v,**kwds): self.ax.axis(*v,**kwds)
    def axvline(self,x=0,ymin=0,ymax=1,**kwds): self.ax.axvline(x,ymin,ymax,**kwds)
    def axvspan(self,xmin,xmax,ymin=0,ymax=1,**kwds): self.ax.axvspan(xmin,xmax,ymin,ymax,**kwds)
    def cla(self): self.ax.cla()
    def clabel(self,cs,*args,**kwds): self.ax.clabel(cs,*args,**kwds)
    def clear(self): self.ax.clear()
    def grid(self,*args,**kwds): self.ax.grid(*args,**kwds)
    def hlines(self,*args,**kwds): self.ax.hlines(*args,**kwds)
    def invert_xaxis(self): self.ax.invert_xaxis()
    def invert_yaxis(self): self.ax.invert_yaxis()
    def legend(self,*args,**kwds): self.ax.legend(*args,**kwds)
    def minorticks_off(self): self.ax.minorticks_off()
    def minorticks_on(self): self.ax.minorticks_on()
    def set(self,**kwds): self.ax.set(**kwds)

    # Makes sure to close down the window
    def __del__(self):
        pylab.close(self.fig)