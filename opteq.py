# ####################################
#   author: Anthony Tooman
#   date:   202012, 202111
#   desc:   opteq
# ####################################


import sys
import pandas as pd
import numpy as np

import opteq.instrument as optinst
import opteq.measures as optmeas
import opteq.option as optopt
import opteq.time as opttime
import opteq.data as optdata
import opteq.hurst as opthurst
import opteq.polyfit as optfit

PATHREL = '/Users/anthony/Google Drive/dev/py/opteq/data'
SYMBOL = '^GSPC'
PATHDATA = '/Users/anthony/Google Drive/opteq/data'

# get s&p 500 (spx) data
periods=[13*5, 26*5, 52*5]
periodsgrp=[13*5, 26*5]
obsin=5*52*4
obsout=252

prd1=1
prd2=2
prd3=3
prd5=5
prd130=5*26
prd252=252

quants = [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 0.80, 0.85, 0.90, 0.95, 0.97, 0.98, 0.99]

def main():
    # underlying symbol
    under = optinst.stock(_symbol=SYMBOL, _region='US', _path=PATHDATA)
    under.getdaily(_dataprovider=optdata.yahoofin(), _interval='1d', _obsin=f'{obsin}d', _events='div,split', _scale=1.0)
    under.writedaily(_dataprovider=optdata.yahoofin())
    under.readdaily(_dataprovider=optdata.yahoofin())
    under.setidx()

    # common index
    # dependents: run, underlying
    idx = opttime.getidx(_group='idx', _df=under.df[under.symbol])

    dtestart = idx.index.min()
    dteend = idx.index.max()

    # return measures
    # dependents: run, underlying
    # features: Open (o)
    rtn = optmeas.rtn(_group='rtn')
    rtn.setrtn(_group='rtn', _name='o', _feature1=under.df[under.symbol]['open'], _feature2=under.df[under.symbol]['adjclose'], _prd=prd1)
    rtn.setstats(_group='rtn', _feature='oln^2', _prd=prd3)

    # features: Close (c)
    rtn.setrtn(_group='rtn', _name='c', _feature1=under.df[under.symbol]['adjclose'], _feature2=under.df[under.symbol]['adjclose'], _prd=prd1)
    rtn.setstats(_group='rtn', _feature='cln^2', _prd=prd3)

    rtn.setrsi(_group='rtn', _name='c', _feature=under.df[under.symbol]['adjclose'], _length=14)
    rtn.setstats(_group='rtn', _feature='c-rsi', _prd=prd3)

    # rtn.sethurst(_group='rtn', _name='c', _feature=under.df[under.symbol]['adjclose'], _prd=prdlong, _kind='price', _simplified=False, _minwindow=3, _maxwindow=prdlong)

    # feature: Low (l), High (h)
    rtn.setrtn(_group='rtn', _name='l', _feature1=under.df[under.symbol]['low'], _feature2=under.df[under.symbol]['adjclose'], _prd=prd1)
    rtn.setstats(_group='rtn', _feature='lln^2', _prd=prd3)

    rtn.setrtn(_group='rtn', _name='h', _feature1=under.df[under.symbol]['high'], _feature2=under.df[under.symbol]['adjclose'], _prd=prd1)
    rtn.setstats(_group='rtn', _feature='hln^2', _prd=prd3)

    rtn.setmax(_group='rtn', _name='lhln^2', _feature1='lln^2', _feature2='hln^2')
    rtn.setstats(_group='rtn', _feature='lhln^2', _prd=prd2)
    rtn.setstats(_group='rtn', _feature='lhln^2', _prd=prd3)
    rtn.setstats(_group='rtn', _feature='lhln^2', _prd=prd252)

    rtn.setrsi(_group='rtn', _name='lhln^2', _feature=rtn.df[('rtn','lhln^2')], _length=14)
    rtn.df = pd.concat([idx, rtn.getdf()], axis=1)

    # setpolyfit
    fit = optfit.polyfit(_group='rtn', _name='lhln^2', _df=rtn.df['rtn'], _obs=prd252)
    #fit.corr(_df=rtn.df['rtn'], _prd=1)
    fit.runner()
    rtn.df = pd.concat([rtn.getdf(), fit.getdf()], axis=1)

    # run measures
    runner = optmeas.runner(_idx=idx['idx'], _rtn=rtn.df['rtn'], _group='runner')
    runner.setrun()
    runner.setdescribe(_quantiles=quants)

    # all trading days. note all schedules are -/+ 5 days
    extdays = optopt.schedule(_dtestart=dtestart, _dteend=dteend, _exch='CME_Equity', _freq='B', _busconv='nat')
    # spx weekly expiries
    exschedmon = optopt.schedule(_dtestart=dtestart, _dteend=dteend, _exch='CME_Equity', _freq='W-MON', _busconv='following')
    exschedwed = optopt.schedule(_dtestart=dtestart, _dteend=dteend, _exch='CME_Equity', _freq='W-WED', _busconv='preceding')
    exschedfri = optopt.schedule(_dtestart=dtestart, _dteend=dteend, _exch='CME_Equity', _freq='W-FRI', _busconv='preceding')

    # return characteristics of the underlying in relation to option expiry
    underrtn = optopt.underlying(_group='option', _idx=idx['idx'], _rtn=rtn.df['rtn'], _tdays=extdays, _scheds=[exschedmon, exschedwed, exschedfri])
    underrtn.setmeasures()
    underrtn.setdescribe(_quantiles=quants)

    # gather components and write to .xlsx
    optdata.writexlsx(_file=under.getpath()
        , _group=[f'{underrtn.getgrp()}desc', f'{runner.getgrp()}desc', under.getgrp(), rtn.getgrp(), runner.getgrp(), underrtn.getgrp()]
        , _df=[underrtn.dfdesc, runner.dfdesc, under.getdf(), rtn.getdf(), runner.getdf(), underrtn.getdf()]
        , _prd=[obsout, obsout, obsout, obsout, obsout, obsout])
    return

if __name__ == "__main__":
    '''
    SYMBOL = sys.argv[1]
    PATHDATA = sys.argv[2]
    '''
    main()
