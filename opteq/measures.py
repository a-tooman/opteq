# ####################################
#   author: Anthony Tooman
#   date:   202012
#   desc:   lnr
#           lnrann
#           EWMean
#           RSI
# ####################################


import numpy as np
import pandas as pd
import pandas_ta as ta

import opteq.time as opttime
import opteq.measures as optmeas
import opteq.hurst as opthurst
import opteq.polyfit as optfit
#import ta

class rtn:
    '''
    desc: return class
    '''

    features = ['lnr','lnr^2','dir','lnlow','lnlow^2','lnhigh','lnhigh^2']
    drop = []

    def __init__(self, _group='rtn',_periods=[13*5, 26*5, 52*5]):
        self.group = _group
        self.periods = _periods
        self.df = pd.DataFrame()
        return

    def getdf(self):
        return self.df

    def getdfgrp(self, _grp):
        return self.df(_grp)[self.features]

    def getgrp(self):
        return self.group

    def setrtn(self, _group, _name, _feature1, _feature2, _prd=1):
        '''
        desc:   set the log return between observations
                p(t) = p(0)exp(r)
        '''
        try:
            self.df[(_group,f'{_name}ln')] = pd.Series(np.log(_feature1) - np.log(_feature2.shift(_prd)), index=_feature1.index)
            self.df[(_group,f'{_name}ln^2')] = self.df[(_group,f'{_name}ln')].pow(2)

            self.df[(_group,f'{_name}dir')] = self.df[(_group,f'{_name}ln')]/self.df[(_group,f'{_name}ln')].abs()

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'rtn.setrtn success with {_group}')
        except Exception as e:
            print(f'rtn.setrtn failed with {_group}')
            print(e)
        finally:
            return

    def setstats(self, _group, _feature, _prd):
        '''
        desc:   rolling min, mean, max
        '''
        try:
            self.df[(_group,f'{_feature}-mu-{_prd}')] = self.df[(_group,_feature)].rolling(_prd).mean()
            min = self.df[(_group,_feature)].rolling(_prd).min()
            max = self.df[(_group,_feature)].rolling(_prd).max()

            self.df[(_group,f'{_feature}-rank-{_prd}')] = (self.df[(_group,_feature)] - min)/(max - min)

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'rtn.setstats success with {_group}')
        except Exception as e:
            print(f'rtn.setstats failed with {_group}')
            print(e)
        finally:
            return

    def sethurst(self, _group, _name, _feature, _prd, _kind='price', _simplified=False, _minwindow=3, _maxwindow=5*13):
        '''
        desc:   rolling hurst exponent
        '''
        try:
            hurst = opthurst.hurst(_kind, _simplified, _minwindow, _maxwindow)
            self.df[(_group,f'{_name}-hurst-{_prd}')] = _feature.rolling(_prd).apply(hurst.gethurst)

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'rtn.sethurst success with {_group}')
        except Exception as e:
            print(f'rtn.sethurst failed with {_group}')
            print(e)
        finally:
            return

    def setmax(self, _group, _name, _feature1, _feature2):
        '''
        desc:   max(_feature1^2,_feature2^2)
        '''
        try:
            self.df[(_group,_name)] = np.maximum(self.df[(_group,_feature1)],self.df[(_group,_feature2)])
            self.df[(_group,f'{_name}ln')] = np.log(self.df[(_group,_name)]) - np.log(self.df[(_group,_name)].shift(1))

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'rtn.setmax success with {_group}')
        except Exception as e:
            print(f'rtn.setmax failed with {_group}')
            print(e)
        finally:
            return

    def setrsi(self, _group, _name, _feature, _length=14):
        '''
        desc:   set the wilder rsi
        '''
        try:
            self.df[(_group,f'{_name}-rsi')] = ta.rsi(_feature, length=_length)

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'rtn.setrsi success with {_group}')
        except Exception as e:
            print(f'rtn.setrsi failed with {_group}')
            print(e)
        finally:
            return

def getrtnqs(_df, _grouper, _period=13*5, _quantiles=np.linspace(.1, 1, 9, 0)):
    # [0.00, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 0.80, 0.85, 0.90, 0.95, 0.97, 0.98, 0.99, 1.00]
    # _quantiles=np.linspace(.1, 1, 9, 0)
    '''
    desc:   lnr quantiles
    '''
    try:
        df = pd.DataFrame()
        df = _df.groupby(_grouper).tail(_period)
        df = df.groupby(_grouper).describe(percentiles=_quantiles)
        print(f'getrtnqs success, {_period} periods')
    except Exception as e:
        print(f'getrtnqs failed, {_period} periods')
        print(e)
    finally:
        return df.T


'''
# ##### run measures
'''
class runner:
    '''
    desc: run class
    '''

    def __init__(self, _idx, _rtn, _group='runner'):
        self.idx = _idx
        self.rtn = _rtn
        self.group = _group
        self.df = pd.DataFrame()
        return

    def getdf(self):
        return self.df

    def getdfgrp(self, _grp):
        return self.df(_grp)

    def getgrp(self):
        return self.group

    def setrun(self):
        '''
        desc:   runner stats
        '''
        try:
            self.df[(self.group,'lnr')] = self.rtn['cln']
            self.df[(self.group,'lnr^2')] = self.rtn['cln^2']

            self.df[(self.group,'dir')] = self.rtn['cdir']
            self.df[(self.group,'dirchg')] = self.df[(self.group,'dir')] != self.df[(self.group,'dir')].shift(-1)

            self.df[(self.group, 'len')] = self.idx['obs'].loc[self.df[(self.group,'dirchg')]==True] \
                - self.idx['obs'].loc[self.df[(self.group,'dirchg')]==True].shift()
            self.df[(self.group, 'lengrp')] = self.df[(self.group, 'len')].bfill()

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'runner.setrun success with {self.group}')
        except Exception as e:
            print(f'runner.setrun failed with {self.group}')
            print(e)
        finally:
            return

    def setdescribe(self, _grouper=['dir','lengrp'], _keep=['dir','lengrp','lnr','lnr^2'], _period=26*5, _quantiles=np.linspace(.1, 1, 9, 0)):
        try:
            df = self.df[self.group][_keep]
            df = df.dropna()
            self.dfdesc = optmeas.getrtnqs(_df=df, _grouper=_grouper, _period=_period, _quantiles=_quantiles)
            print(f'runner.setdescribe success with {self.group}')
        except Exception as e:
            print(f'runner.setdescribe failed with {self.group}')
            print(e)
        finally:
            return
