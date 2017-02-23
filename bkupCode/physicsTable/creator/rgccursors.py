import pygame as pg

move_strings = (
  "       XX       ",
  "      XXXX      ",
  "     XXXXXX     ",
  "       XX       ",
  "       XX       ",
  "  X    XX    X  ",
  " XX    XX    XX ",
  "XXXXXXXXXXXXXXXX",
  "XXXXXXXXXXXXXXXX",
  " XX    XX    XX ",
  "  X    XX    X  ",
  "       XX       ",
  "       XX       ",
  "     XXXXXX     ",
  "      XXXX      ",
  "       XX       ")

mcmove, movemask = pg.cursors.compile(move_strings,black='X',white='.',xor='o')

resize_strings = (
  " XX XX XX XXXXXX",
  "X          XXXXX",
  "X          XXXXX",
  "          XXXXXX",
  "X        XXXXXXX",
  "X       XXXXX  X",
  "       XXXXX    ",
  "X       XXX    X",
  "X        X     X",
  "                ",
  "X              X",
  "X              X",
  "                ",
  "X              X",
  "X              X",
  " XX XX XX XX XX ")
           
mcresize, resizemask = pg.cursors.compile(resize_strings, black='X',white='.',xor='o')

class RGCursor(object):
    def __init__(self):
        self.defcurs = pg.mouse.get_cursor()
    def set(self,type='default'):
        pg.mouse.set_visible(True)
        if type == 'move': pg.mouse.set_cursor( (16,16), (8,8), movemask, mcmove)
        elif type == 'resize': pg.mouse.set_cursor( (16,16), (8,8),resizemask, mcresize)
        elif type == 'none': pg.mouse.set_visible(False)
        else: pg.mouse.set_cursor(*self.defcurs)
