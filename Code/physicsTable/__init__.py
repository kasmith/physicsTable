# ---------------------------------------------------
# physicsTable
#
# Written by Kevin A Smith (k2smith@ucsd.edu)
#
# ---------------------------------------------------

__all__ = ['objects','SimpleTable','BasicTable','GravityTable','NoisyTable',
           'Path','PathFilter','PointSimulation','SimpleTrial','PongTrial','PathMaker','loadPathMaker',
           'RedGreenTrial','loadTrial','constants','makeNoisy','startRGCreator','creator']

from basicTable import BasicTable
from simpleTable import SimpleTable
from gravityTable import GravityTable
from noisyTable import NoisyTable, makeNoisy        
from pathFilter import Path, PathFilter
from pointSimulation import PointSimulation
from pathMaker import PathMaker, loadPathMaker
from trials import SimpleTrial, PongTrial, RedGreenTrial, loadTrial

import objects
import constants
import creator

def startRGCreator(tbsize = (900,900), flnm = None):
    cr = creator.RGCreator(tbsize)
    if flnm is not None:
        isgood = cr.load(flnm)
        if not isgood:
            print "Error loading trial - default creator will be loaded"
            cr = creator.RGCreator(tbsize)
    cr.runCreator()
