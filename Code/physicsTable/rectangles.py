from __future__ import division
import pygame as pg
import sys, os, time, copy


def rectDiff(rbase, rsub):
    runion = rbase.clip(rsub)
    if runion == rbase: return None
    if runion.width == 0 or runion.height == 0: return [rbase]
    # Test for full block of one dimension
    if rbase.width == runion.width:
        if rbase.top < runion.top:
            if rbase.bottom == runion.bottom:
                return [pg.Rect(rbase.left,rbase.top,runion.width,runion.top - rbase.top)]
            else:
                return [pg.Rect(rbase.left,rbase.top,runion.width,runion.top - rbase.top), \
                        pg.Rect(rbase.left,runion.bottom,runion.width,rbase.bottom - runion.bottom)]
        else:
            return [pg.Rect(rbase.left,runion.bottom,runion.width,rbase.bottom - runion.bottom)]
    if rbase.height == runion.height:
        if rbase.left < runion.left:
            if rbase.right == runion.right:
                return [pg.Rect(rbase.left,rbase.top,runion.left-rbase.left,rbase.height)]
            else:
                return [pg.Rect(rbase.left,rbase.top,runion.left-rbase.left,rbase.height), \
                        pg.Rect(runion.right,rbase.top,rbase.right - runion.right, rbase.height)]
        else:
            return [pg.Rect(runion.right,rbase.top,rbase.right-runion.right,rbase.height)]
            
    if rbase.top < runion.top:
        if rbase.left < runion.left:
            if rbase.right == runion.right:
                if rbase.bottom == runion.bottom:
                    return [pg.Rect(rbase.left,rbase.top,runion.left-rbase.left,rbase.height), \
                            pg.Rect(runion.left,rbase.top,runion.width,runion.top-rbase.top)]
                else:
                    return [pg.Rect(rbase.left,rbase.top,rbase.width,runion.top - rbase.top), \
                            pg.Rect(rbase.left,runion.top,runion.left - rbase.left, runion.height), \
                            pg.Rect(rbase.left,runion.bottom,rbase.width,rbase.bottom - runion.bottom)]
            else:
                return [pg.Rect(rbase.left,rbase.top,rbase.width,runion.top - rbase.top), \
                        pg.Rect(rbase.left,runion.top,runion.left-rbase.left,runion.height), \
                        pg.Rect(runion.right,runion.top,rbase.right - runion.right, runion.height)]
            
        else:
            if rbase.bottom == runion.bottom:
                return [pg.Rect(rbase.left,rbase.top,rbase.width,runion.top - rbase.top), \
                        pg.Rect(runion.right,runion.top,rbase.right-runion.right,rbase.bottom-runion.top)]
            else:
                return [pg.Rect(rbase.left,rbase.top,rbase.width,runion.top - rbase.top), \
                        pg.Rect(runion.right,runion.top,rbase.right - runion.right, runion.height), \
                        pg.Rect(rbase.left,runion.bottom,rbase.width,rbase.bottom - runion.bottom)]
    else:
        if rbase.left < runion.left:
            if rbase.right == runion.right:
                return [pg.Rect(rbase.left,rbase.top,runion.left-rbase.left,rbase.height), \
                        pg.Rect(runion.left,runion.bottom,runion.width,rbase.bottom - runion.bottom)]
            else:
                return [pg.Rect(rbase.left,rbase.top,runion.left - rbase.left, rbase.height), \
                        pg.Rect(runion.left,runion.bottom,runion.width,rbase.bottom - runion.bottom), \
                        pg.Rect(runion.right,rbase.top,rbase.right-runion.right,rbase.height)]
        else:
            return [pg.Rect(rbase.left,runion.bottom,rbase.width,rbase.bottom-runion.bottom), \
                    pg.Rect(runion.right,runion.top,rbase.right - runion.right,runion.height)]

def breakRect(r, breaklist):
    if len(breaklist) == 0: return [r]
    b = breaklist[0]
    bleft = breaklist[1:]
    brk = rectDiff(r,b)
    if brk is None: return []
    ret = []
    for s in brk:
        ret.extend(breakRect(s,bleft))
    return ret

def uniqueOccs(occs, walls = []):
    uos = []
    block = copy.copy(walls)
    for o in occs:
        nos = breakRect(o, block)
        uos.extend(nos)
        block.extend(nos)
    # Go through once more
    #if i in range(len(uos)):
    #    if uos[i].collidelist(uos[:i]+uos[i+1:]) != -1:
            
    # Test code - check for overlaps
    for i in range(len(uos)):
        if uos[i].collidelist(uos[:i]+uos[i+1:]) != -1:
            print uos
            raise Exception("FOUND COLLLISION!!!")
    return uos
