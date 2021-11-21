# ####################################
#   author: Anthony Tooman
#   date:   202102
#   desc:
# ####################################


import pandas as pd
import numpy as np

from datetime import datetime
import pandas_market_calendars as mcal
import calendar

import opteq.time as opttime
import opteq.measures as optmeas

class schedule(object):
    '''
    desc:   schedule base class
            np.busday_offset, roll
                spx wkly monday (EOW) ='following'
                spx wkly wednesday ='preceding'
                spx wkly friday (EOW) ='preceding'

            pandas_market_calendars as mcal
                cboe calandar = 'CFE'
    '''

    def __init__(self, _dtestart=datetime(2021,1,1), _dteend=datetime(2022,1,1), _exch='CME_Equity', _freq='W-FRI', _busconv='preceding'):
        self.dtestart = _dtestart
        self.dteend = _dteend
        self.exchange = _exch
        self.freq = _freq
        self.busconv = _busconv
        self.df = pd.DataFrame()
        return

    def getholidays(self):
        '''
        desc:   get exchange holidays
                pandas_market_calendars as mcal
                    cboe calandar = 'CFE'
        '''
        exch = mcal.get_calendar(self.exchange)
        return list(exch.holidays().holidays)

    def getbusdays(self):
        '''
        desc:   apply business day conventions
        '''
        self.df = np.busday_offset(self.df.values.astype('datetime64[D]'), 0, roll=self.busconv, holidays=self.getholidays())
        self.df = pd.to_datetime(self.df).dropna()
        self.df = pd.DataFrame(self.df, index=self.df, columns = [(self.group,'expiry')])
        return

    def getweekdays(self):
        '''
        desc:   map date to weekday
        '''
        self.df[(self.group,'freq')] = self.freq
        self.df[(self.group,'day')] = [f'{calendar.day_name[date.weekday()]}' for date in self.df.index]
        return

    def setsched(self, _group):
        '''
        desc:   given a start and end date, return a list of expiry days
        '''
        try:
            self.group = _group
            self.df = pd.date_range(self.dtestart-pd.Timedelta("7 days"), self.dteend+pd.Timedelta("7 days"), freq=self.freq)
            self.getbusdays()
            self.getweekdays()

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            print(f'schedule.setsched success {self.group}')
        except:
            print(f'schedule.setsched failed {self.group}')
        finally:
            return

    def getsched(self):
        '''
        desc:   return esdte
        '''
        return self.df

    def getschedidx(self):
        '''
        desc:   return index
        '''
        return self.df.index


class underlying(object):
    '''
    desc:   assess underlying inrelation to options expiries
    '''

    def __init__(self, _group, _idx, _rtn, _tdays, _scheds):
        self.group = _group
        self.idx = _idx
        self.rtn = _rtn
        self.tdays = _tdays
        self.scheds = _scheds
        self.df = pd.DataFrame()
        return

    def getdf(self):
        return self.df

    def getdfgrp(self, _grp):
        return self.df(_grp)

    def getgrp(self):
        return self.group

    def settdays(self):
        '''
        desc:   set trading days. tdays will be -/+ 7 days in length
        '''
        self.tdays.setsched(self.group)
        return

    def setsched(self):
        '''
        desc:   set option expiry dates for each sched
        '''
        for sched in self.scheds: sched.setsched(self.group)
        return

    def getsched(self):
        '''
        desc:   merge the associated schedules
                set option open date
                set date difference in days
        '''
        self.df = pd.concat([sched.getsched() for sched in self.scheds], axis=0)
        self.df = self.df.sort_index()

        self.df[(self.group,'open')] = self.df[(self.group,'expiry')].shift()
        self.df[(self.group,'diff')] = (self.df.index - self.df[(self.group,'open')]).dt.days
        return

    def setobs(self):
        '''
        desc:   set obs id
        '''
        try:
            obs = pd.Series(data=list(range(1, self.df.shape[0]+1)), index=self.df.index, dtype=float)

            open = self.df[(self.group,'open')].dropna()
            obsopen = obs[open]
            obsopen.index = open

            self.df[(self.group,'obsdiff')] = obs - obsopen

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            self.df = pd.DataFrame(self.df, index=self.idx.index)
            print(f'underlying.setobs success {self.group}')
        except Exception as e:
            print(f'underlying.setobs failed {self.group}')
            print(e)
        finally:
            return

    def setfill(self):
        '''
        desc:   set index and option dates
        '''
        try:
            # reduces self.df to trading days only
            self.df = pd.DataFrame(self.df, index=self.tdays.getschedidx())

            self.df[(self.group,'freq')] = self.df[(self.group,'freq')].bfill()
            self.df[(self.group,'day')] = self.df[(self.group,'day')].bfill()
            self.df[(self.group,'expiry')] = self.df[(self.group,'expiry')].bfill()
            self.df[(self.group,'open')] = self.df[(self.group,'open')].bfill()

            self.df.columns = pd.MultiIndex.from_tuples(self.df.columns, names=["group", "var"])
            self.df = pd.DataFrame(self.df, index=self.idx.index)
            print(f'underlying.setfill success {self.group}')
        except Exception as e:
            print(f'underlying.setfill failed {self.group}')
            print(e)
        finally:
            return

    def setrtn(self):
        '''
        desc:   self.df.shape[0]>self.rtn.shape[0]
                set option returns
                P(prd) = P(open)exp(lnropenann prd/tdays)
        '''
        try:
            self.df[(self.group,'lnr')] = self.rtn['cln']
            self.df[(self.group,'lnr^2')] = self.rtn['cln^2']
            self.df[(self.group,'dir')] = self.rtn['cdir']

            print(f'underlying.setrtn success {self.group}')
        except Exception as e:
            print(f'underlying.setrtn failed {self.group}')
            print(e)
        finally:
            return

    def setmeasures(self):
        '''
        desc:   set option open and expiry dates for each sched
        '''
        try:
            self.settdays()
            self.setsched()
            self.getsched()
            self.setobs()
            self.setfill()
            self.setrtn()
            print(f'underlying.setmeasures success {self.group}')
        except Exception as e:
            print(f'underlying.setmeasures failed {self.group}')
            print(e)
        finally:
            return

    def setdescribe(self, _grouper=['freq','dir'], _keep=['freq','dir','lnr','lnr^2'], _period=26*5, _quantiles=np.linspace(.1, 1, 9, 0)):
        df = self.df[self.group][_keep]
        df = df.dropna()
        self.dfdesc = optmeas.getrtnqs(_df=df, _grouper=_grouper, _period=_period, _quantiles=_quantiles)
        return
