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
    obsin = None
    obsout = None
    scale = None
    path = None
    features = None

    comps={"group":[], "df":[], "obs":[]}
    df = pd.DataFrame()

    typemap = {'open':'float64'
        ,'high':'float64'
        ,'low':'float64'
        ,'close':'float64'
        ,'adjclose':'float64'
        , 'volume':'int'}

    parsedates = ['exdate','exopen']

    def __init__(self):
        return

    def getdf(self):
        return self.df

    def getdfgrp(self, _grp):
        return self.df[_grp][self.features]

    def getgrp(self):
        return 'inst'

    def getdaily(self):
        self.df = self.dataprovider.getdaily(self.symbol, self.region, self.obsin, self.scale)
        self.df = self.df.ffill()
        return

    def getpath(self):
        return f'{self.path}{self.dataprovider.PROVIDER}-{self.symbol}-{self.df.index.max().date()}.xlsx'

    def writedaily(self):
        self.dataprovider.writedaily(self.df, self.symbol, self.path)
        return

    def readdaily(self):
        self.df = self.dataprovider.readdaily(self.symbol, self.path)
        return


class stock(instrument):
    '''
    desc:       equity timeseries
    default:    ^GPSC = s&p500 index
    '''
    features = ['open', 'high', 'low', 'close', 'adjclose', 'volume']
    drop = []

    def __init__(self, _dataprovider=optdata.yahoofin(), _symbol='^GSPC', _region='US', _scale=1.0, _obsin=4*52*5, _obsout=252, _path=PATHREL):
        self.dataprovider = _dataprovider
        self.symbol = _symbol
        self.region = _region
        self.obsin = f'{_obsin}d'
        self.obsout = _obsout
        self.scale = _scale
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
