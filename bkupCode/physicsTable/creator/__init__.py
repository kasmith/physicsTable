# ---------------------------------------------------
# physicsTable
#
# Written by Kevin A Smith (k2smith@ucsd.edu)
#
# ---------------------------------------------------

__all__ = ['RGCreator','startRGCreator']

try:
    import pygame as pg
except:
    raise Exception('pygame is required to load the creator')

from rgcreator import RGCreator

def startRGCreator(tbsize = (900,900), flnm = None):
    cr = RGCreator(tbsize)
    if flnm is not None:
        isgood = cr.load(flnm)
        if not isgood:
            print "Error loading trial - default creator will be loaded"
            cr = creator.RGCreator(tbsize)
    cr.runCreator()
