import sys,os

import itertools
import numpy as np
from numpy.fft import _pocketfft_internal as pfi

import numpy as np
import scipy as sp
import scipy.special

import xraylib as xrl


_sqrt2 = np.sqrt(2.0)
_sqrt2pi = np.sqrt(2.0*np.pi)

# basically from mass by Joe Fowler, NIST
def voigt(x, mean, hwhm, sigma):
    if not isinstance(x, np.ndarray):
        return voigt(np.array(x), mean, hwhm, sigma)

    if hwhm==0. and sigma>0.:# Gaussian
        return np.exp(-0.5*((x-mean)/sigma)**2) / (sigma*_sqrt2pi)
    elif sigma==0. and hwhm>0.:# Lorentzian
        return (hwhm/np.pi) / ((x-mean)**2 + hwhm**2)
    elif sigma==0. and hwhm==0.:
        print("Warning: voigt, sigma=0 and hwhm=0")
        return np.zeros_like(x)

    # General Voigt function
    z = (x-mean + 1j*hwhm)/(sigma * _sqrt2)
    w = scipy.special.wofz(z)
    return (w.real)/(sigma * _sqrt2pi)


# basically from Ichinohe-san
def get_linewidth(z,linetype):
    _e,_b='',''
    if 'K'==linetype[0]:
        _e=xrl.K_SHELL
        if len(linetype[1:])==3:
            _b=xrl.__getattribute__('%s_SHELL'%(linetype[1:-1]))
        else:
            _b=xrl.__getattribute__('%s_SHELL'%(linetype[1:]))
    else:
        _e=xrl.__getattribute__('%s_SHELL'%(linetype[:2]))
        if len(linetype[2:])==3:
            _b=xrl.__getattribute__('%s_SHELL'%(linetype[2:-1]))
        else:
            _b=xrl.__getattribute__('%s_SHELL'%(linetype[2:]))
    try:
        we=xrl.AtomicLevelWidth(z,_e)
    except:
        we=0.0
    try:
        wb=xrl.AtomicLevelWidth(z,_b)
    except:
        wb=0.0
    width=we+wb
    if width>0.: return width# keV
    elif width==0.: return 0.001/1e3# keV
    else: return 0.
    

def get_lineenergy(z,line):
    try:
        ene=xrl.LineEnergy(z,line)
    except:
        ene=0.
    return ene


## from Ichinohe-san
#def gen_voigt_tail(L=800.0,nbin=2048):
#    dL=L/nbin
#    lenxs=2*nbin
#    xs=(np.arange(lenxs)-nbin)*dL
#    ks=np.arange(0,nbin+1)/L*3.14159265
#    z=np.zeros(lenxs,'D')
#    lenxs_inv=1/lenxs
#        
#    def func(x,mu,gauss_sigma,lorentz_gamma,norm,tail_tau=0.0,tail_frac=0.0):
#        fGfL=np.exp(-0.5*(gauss_sigma*ks)**2-lorentz_gamma*ks)
#        fT=1/(1-1j*ks*tail_tau)
#        z[0:nbin+1]=fGfL*((1-tail_frac)+tail_frac*fT)
#        glt=pfi.execute(z,True,False,lenxs_inv) / dL
#        return np.interp(x,xs+mu,np.concatenate([glt[-nbin:],glt[:-nbin]]),
#                         left=0.0,right=0.0)*norm
#
#    return func
#



## http://www011.upp.so-net.ne.jp/dhistory/PytnPageQT02-05.html
#class Logger( object ):
#    def __init__( self, editor, out=None, color=None ):
#        self.editor = editor
#        self.out    = out
#        if not color:
#            self.color = editor.textColor()
#        else:
#            self.color = color
#
#    def write( self, message ):
#        self.editor.moveCursor( QTextCursor.End )
#        self.editor.setTextColor( self.color )
#        self.editor.insertPlainText( message )
#        if self.out:
#            self.out.write( message )
