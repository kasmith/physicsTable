

__all__ = ['mvstdnormcdf', 'mvnormcdf', 'SimpleSPSA','async_map','apply_async','euclidist',
           'MakeSmoother','SmoothFromPre','SmoothNShift']

from mvncdf import mvstdnormcdf, mvnormcdf
from SPSA import SimpleSPSA
from dillMultithreading import async_map, apply_async
from smoothNShift import MakeSmoother, SmoothFromPre, SmoothNShift
import numpy as np

def euclidist(p1, p2):
    dx = p1[0]-p2[0]
    dy = p1[1]-p2[1]
    return np.sqrt( dx*dx + dy*dy )