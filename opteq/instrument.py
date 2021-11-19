# ####################################
#   author: Anthony Tooman
#   date:   202012
#   desc:
# ####################################


import opteq.data as optdata
import opteq.measures as optmeas
import opteq.time as opttime

import numpy as np
import pandas as pd
from openpyxl import load_workbook

import requests
import os

PATHREL = 'opteq/data/'

class instrument:
    '''
    desc: instrument base class
    '''
    dataprovider = None
    symbol = None
    region = None
    path = None
    features = None

    comps={"group":[], "df":[], "obs":[]}
    df = pd.DataFrame()

    parsedates = ['exdate','exopen']

    def __init__(self):
        return

    def getdf(self):
        return self.df

    def getdfgrp(self, _grp):
        return self.df[_grp][self.features]

    def getgrp(self):
        return 'inst'

    def getdaily(self, _dataprovider=optdata.yahoofin(), _interval='1d', _obsin='252d', _events='div,split', _scale=1.0):
        '''
        desc:  get daily data from dataprovider
        '''
        self.df = _dataprovider.getdaily(_symbol = self.symbol
            , _region = self.region
            , _interval = _interval
            , _obsin = _obsin
            , _events = _events
            , _scale = _scale)
        self.df = self.df.ffill()
        return

    def getpath(self):
        return f'{self.path}{self.dataprovider.PROVIDER}-{self.symbol}-{self.df.index.max().date()}.xlsx'

    def writedaily(self, _dataprovider=optdata.yahoofin()):
        _dataprovider.writedaily(self.df, self.symbol, self.path)
        return

    def readdaily(self, _dataprovider=optdata.yahoofin()):
        self.df = _dataprovider.readdaily(self.symbol, self.path)
        return


class stock(instrument):
    '''
    desc:       equity timeseries
    default:    ^GPSC
    '''
    features = ['open', 'high', 'low', 'close', 'adjclose', 'volume']
    drop = []

    def __init__(self, _symbol='^GSPC', _region='US', _path=PATHREL):
        self.symbol = _symbol
        self.region = _region
        self.path = _path
        return

    def setidx(self):
        self.df = self.df.reindex(columns=self.features)
        self.df.columns = [(self.symbol, column) for column in self.df.columns]
        self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
        return

    def getdf(self):
        return self.df

class intrate(instrument):
    '''
    desc: us treasury bill
    default: ^IRX = 13 week treasury bill
    '''
    features=['close']

    def __init__(self, _dataprovider=optdata.yahoofin(), _symbol='^IRX', _region='US', _obsin=2*52*5, _obsout=252, _scale=0.01, _path=PATHREL):
        self.dataprovider = _dataprovider
        self.symbol = _symbol
        self.region = _region
        self.obsin = _obsin
        self.obsout = _obsout
        self.scale = _scale
        self.path = _path
        return

    def setmeasures(self):
        return


class vix(instrument):
    '''
    desc: vol index timeseries
    default: ^VIX = s&p500 vix index
    '''
    features=['close', 'adjclose', 'volume']

    def __init__(self, _dataprovider=optdata.yahoofin(), _symbol='^VIX', _region='US', _obsin=2*52*5, _obsout=252, _scale=0.01, _path=PATHREL):
        self.dataprovider = _dataprovider
        self.symbol = _symbol
        self.region = _region
        self.obsin = _obsin
        self.obsout = _obsout
        self.scale = _scale
        self.path = _path
        return

    def setmeasures(self):
        '''set log return measures'''
        self.lndiff()
        return
