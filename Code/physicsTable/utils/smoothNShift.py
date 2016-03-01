from __future__ import division
import numpy as np
from scipy.stats import norm, lognorm

__author__ = 'ksmith'

# Function for taking an array and (a) shifting it over and (b) smoothing with a Gaussian kernel
def SmoothNShift(series, offset, width):
    N = len(series)
    # Normalize by all possible values - including those outside
    nrmf = sum([norm.pdf(i,0,width) for i in range(-int(N*max(width,1)*4),int(N*max(width,1)*4))])
    smoother = np.zeros((N,N))
    for i in range(N):
        smoother[i] = np.array([series[i]*norm.pdf(k,offset+i,width)/nrmf for k in range(N)])

    return np.sum(smoother,0)

def MakeSmoother(maxn, offset, width):
    nrmf = sum([norm.pdf(i,0,width) for i in range(-int(maxn*max(width,1)*4),int(maxn*max(width,1)*4))])
    smoother = np.array([norm.pdf(k,offset,width)/nrmf for k in range(-maxn,maxn)])
    return {'MaxN':maxn, 'Smoother':smoother, 'Offset':offset,'Width':width}

def MakeLNSmoother(maxn, offset, width):
    offset = np.log(offset)
    nrmf = sum([lognorm.pdf(i-maxn,offset+maxn,width) for i in range(-int(maxn*max(width,1)*4),int(maxn*max(width,1)*4)) if (i-maxn) > 0])
    smoother = np.zeros(2*maxn)
    for k in range(1,maxn):
        smoother[k+maxn] = lognorm.pdf(k,offset,width)/nrmf
    return {'MaxN':maxn, 'Smoother':smoother}

def SmoothFromPre(series, smoother):
    maxn = smoother['MaxN']
    sm = smoother['Smoother']
    N = len(series)

    if N > maxn: raise Exception('Series length greater than smoother maximum')

    expa = np.zeros((N,N))
    for i in range(N): expa[i] = series[i]*sm[(maxn-i):(maxn+N-i)]
    return np.sum(expa,0)
