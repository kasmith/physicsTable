# ---------------------------------------------------
# physicsTable
#
# Written by Kevin A Smith (k2smith@ucsd.edu)
#
# ---------------------------------------------------

__all__ = ['WHITE','BLACK','BLUE','RED','GREEN','GREY','LIGHTGREY','YELLOW','GOLD',
           'TIMESTEP','DEACT_TIME','KAPV_DEF','KAPB_DEF','KAPM_DEF','PERR_DEF',
           'LEFT','RIGHT','BOTTOM','TOP','HORIZONTAL','VERTICAL',
           'TIMEUP','SUCCESS','FAILURE','OUTOFBOUNDS','UNCERTAIN',
           'REDGOAL','GREENGOAL','BLUEGOAL','YELLOWGOAL',
           'COLLTYPE_DEFAULT','COLLTYPE_WALL','COLLTYPE_BALL','COLLTYPE_GOAL',
           'SHAPE_RECT','SHAPE_BALL','SHAPE_POLY','getConst']

from constants import *
del(constants)