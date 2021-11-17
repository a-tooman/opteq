# ####################################
#   author: Anthony Tooman
#   date:   202101
#   desc:
# ####################################


import pandas as pd


from datetime import datetime
import calendar


'''
# #### time methods
'''
def gettdays():
    '''
    desc:   get trading days in given year
    '''
    return 252.0


def getdays(_year):
    '''
    desc:   set days given year
    '''
    days = 365.0
    if calendar.isleap(_year):days = 366.0
    return days


def getidx(_group, _df):
    '''
    desc:   get year fraction
    '''
    try:
        df = pd.DataFrame()
        df[(_group,'obs')] = pd.Series(list(range(1, _df.shape[0]+1)), index=_df.index, dtype=float)

        df[(_group,'diff')] = _df.index.to_series().diff().dt.days
        df[(_group,'diffsum')] = df[(_group,'diff')].cumsum()
        df[(_group,'yrdays')] = [getdays(year) for year in df.index.year]
        df[(_group,'yrfrac')] = df[(_group,'diff')]/df[(_group,'yrdays')]

        df.columns = pd.MultiIndex.from_tuples(df.columns, names=["group", "var"])
        print(f'getidx success with {_group}')
    except:
        print(f'getidx failed with {_group}')
    finally:
        return df
