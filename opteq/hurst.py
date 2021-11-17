'''
Hurst exponent and RS-analysis
Modified: https://github.com/Mottl/hurst
https://en.wikipedia.org/wiki/Hurst_exponent
https://en.wikipedia.org/wiki/Rescaled_range
'''

name = "hurst"
__version__ = '0.0.5'

import sys
import math
import warnings
import numpy as np
try:
    import pandas as pd
except:
    pass

class hurst(object):
    '''
    desc: hurst exponent
    '''
    def __init__(self, _kind='price', _simplified=False, _minwindow=3, _maxwindow=5*13):
        self.kind = _kind
        self.simplified = _simplified
        self.minwindow = _minwindow
        self.maxwindow = _maxwindow
        if self.minwindow < 3:
            raise ValueError(f'Minimum window length must be greater than 2')
        return

    def __to_inc(self,x):
        incs = x[1:] - x[:-1]
        return incs

    def __to_pct(self,x):
        pcts = x[1:] / x[:-1] - 1.
        return pcts

    def __get_simplified_RS(self, _series):
        '''
        desc:   simplified version of rescaled range
        series: array-like (Time-)series
        kind:   str, the kind of series (refer to compute_Hc docstring)
        '''
        if self.kind == 'price':
            pcts = self.__to_pct(_series)
            R = max(_series) / min(_series) - 1. # range in percent
            S = np.std(pcts, ddof=1)
        elif self.kind == 'change':
            incs = _series
            _series = np.hstack([[0.],np.cumsum(incs)])
            R = max(_series) - min(_series)  # range in absolute values
            S = np.std(incs, ddof=1)

        if R == 0 or S == 0:
            return 0  # return 0 to skip this interval due the undefined R/S ratio

        return R / S

    def __get_RS(self, _series):
        '''
        desc:   get rescaled range
        series: array-like (Time-)series
        kind:   str, the kind of series (refer to compute_Hc docstring)
        '''
        if self.kind == 'price':
            incs = self.__to_pct(_series)
            mean_inc = np.sum(incs) / len(incs)
            deviations = incs - mean_inc
            Z = np.cumsum(deviations)
            R = max(Z) - min(Z)
            S = np.std(incs,ddof=1)

        elif self.kind == 'change':
            incs = _series
            mean_inc = np.sum(incs) / len(incs)
            deviations = incs - mean_inc
            Z = np.cumsum(deviations)
            R = max(Z) - min(Z)
            S = np.std(incs,ddof=1)

        if R == 0 or S == 0:
            return 0  # return 0 to skip this interval due undefined R/S
        return R / S

    def setwindows(self):
        '''
        desc:   set windows
        '''
        self.windowsizes = list( \
                            map(lambda x: int(10**x), np.arange(math.log10(self.minwindow), math.log10(self.maxwindow), 0.25))
                        )
        self.windowsizes.append(self.serieslen)
        return

    def gethurst(self, _series):
        '''
        desc:    compute H (Hurst exponent) and C according to Hurst equation: E(R/S) = c * T^H
        series:  array-like (Time-)series
        returns: tuple of H, c and data where
                H and c — parameters or Hurst equation
                and data is a list of 2 lists: time intervals and R/S-values for correspoding time interval
                for further plotting log(data[0]) on X and log(data[1]) on Y
        '''
        self.serieslen = len(_series)
        if self.serieslen < self.maxwindow:
            self.maxwindow = min([self.maxwindow, self.serieslen-1])
            print(f'Max window > series length. Max window set to series length')

        ndarray_likes = [np.ndarray]
        if "pandas.core.series" in sys.modules.keys():
            ndarray_likes.append(pd.core.series.Series)

        # convert series to numpy array if series is not numpy array or pandas Series
        if type(_series) not in ndarray_likes:
            _series = np.array(_series)

        if "pandas.core.series" in sys.modules.keys() and type(_series) == pd.core.series.Series:
            if _series.isnull().values.any():
                raise ValueError("Series contains NaNs")
            _series = _series.values  # convert pandas Series to numpy array
        elif np.isnan(np.min(_series)):
            raise ValueError("Series contains NaNs")

        # set RS method
        if self.simplified:
            RS_func = self.__get_simplified_RS
        else:
            RS_func = self.__get_RS
        err = np.geterr()
        np.seterr(all='raise')

        # set windows
        self.setwindows()

        # calculate R/S per window
        RS = []
        for w in self.windowsizes:
            rs = []
            for start in range(0, len(_series), w):
                if (start+w)>len(_series):
                    break
                _ = RS_func(_series[start:start+w])
                if _ != 0:
                    rs.append(_)
            RS.append(np.mean(rs))

        A = np.vstack([np.log10(self.windowsizes), np.ones(len(RS))]).T
        H, c = np.linalg.lstsq(A, np.log10(RS), rcond=-1)[0]
        np.seterr(**err)

        c = 10**c
        #return H, c, [window_sizes, RS]
        return H
