from warnings import warn


__all__ = ['displayInstructions','mousePos','FONT_L','FONT_M','FONT_S','FONT_VL', 'screenPause',
           'WHITE','BLACK','BLUE','RED','GREEN','GREY','LIGHTGREY','YELLOW','GOLD','PURPLE',
           'Ball','Wall','Occlusion','AbnormWall','Goal','Paddle','ptRect','BasicTable','SimpleTable']

try:
    import pygame as pg
    from pyText import displayInstructions, mousePos, FONT_L, FONT_M, FONT_S, FONT_VL, screenPause
    from vizobjects import Ball, Wall, Occlusion, AbnormWall, Goal, Paddle, ptRect
    from viztables import BasicTable, SimpleTable
except:
    raise Exception("pygame is required to import any visualizations")

try:
    from matpltPygame import pgFig
except:
    warn("Need matplotlib to import pgFig for graph plotting",ImportWarning)
    def pgFig(*kwds, **args): raise Exception('Need matplotlib for pgFig!s')

# Set color names
WHITE = pg.Color('White')
BLACK = pg.Color('Black')
BLUE = pg.Color('Blue')
RED = pg.Color('Red')
GREEN = pg.Color('Green')
GREY = pg.Color('Grey')
LIGHTGREY = pg.Color('lightgrey')
YELLOW = pg.Color('Yellow')
GOLD = pg.Color('Gold')
PURPLE = pg.Color('Purple')