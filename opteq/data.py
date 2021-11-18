# ####################################
#   author: Anthony Tooman
#   date:   202012
#   desc:
# ####################################


import pandas as pd
import requests
import os

class alphavan(object):
    BASE_URL = 'https://www.alphavantage.co/query?'

class iex(object):
    '''
    IEX limit on free account limited
    '''
    BASE_URL = 'https://cloud.iexapis.com/v1'
    SANDBOX_URL = 'https://sandbox.iexapis.com/stable'
    TOKEN = os.environ.get('IEX_TOKEN')

    def __init__(self):
        return

    def getdaily(self, _symbol='TSLA', _period='1y'):
        '''
        endppoint:  #historical-prices
        desc:       get historical daily data
        '''
        params = {'token':self.TOKEN}
        endpoint = f'{self.BASE_URL}/stock/{_symbol}/chart/{_period}'
        print(endpoint)
        try:
            resp = requests.get(endpoint, params=params)
            self.df = pd.DataFrame(resp.json())
            print("dataiex.getdaily df created")
        except:
            print("dataiex.getdaily failed")
        finally:
            return

    def mapcolumns(self):
        '''
        notes:  model expects the column adjclose
                IEX close = adjusted
                IEX uclose = unadjusted
        '''
        self.df.rename(columns={'close':'adjclose', 'uClose':'close'}, inplace=True)
        return

    def setindex(self):
        '''
        notes:  model expects date column as index
        '''
        self.df.index = self.df['date']
        return

class yahoofin(object):
    PROVIDER = 'yahoofin'
    BASE_URL = 'https://yfapi.net/v6/finance/'
    HOST_URL = None
    TOKEN = os.environ.get('YAHOOFIN_TOKEN')
    TYPEMAP = {'open':'float64', 'high':'float64', 'low':'float64', 'close':'float64', 'adjclose':'float64', 'volume':'int'}
    PARSEDATES = None #['date']

    def __init__(self):
        return

    def getdaily(self, _symbol='^GSPC', _region='US', _interval='1d', _obsin='252d', _events='div,split', _scale=1.0):
        '''
        endppoint:  chart
        desc:       get historical daily data
                    close is adjusted for splits
                    adjclose is adjusted for splits and dividends
                    close and adjclose include extended trading hours
        '''
        headers = {
                    'x-api-key': self.TOKEN
                    }
        params = {
                    "interval":_interval
                    ,"range":_obsin
                    ,"region":_region
                    ,"events":_events
                    }
        endpoint = f'{self.BASE_URL}/chart/{_symbol}'

        try:
            resp = requests.get(endpoint, headers=headers, params=params)
            print(resp)
            '''
            # create DatetimeIndex
            idx = pd.to_datetime(resp.json()['chart']['result'][0]['timestamp'], errors='raise', unit='s', origin='unix').date

            data = pd.DataFrame(resp.json()['chart']['result'][0]['indicators']['quote'][0], index=idx)
            dataadj = pd.DataFrame(resp.json()['chart']['result'][0]['indicators']['adjclose'][0], index=idx)
            df = pd.concat([_scale*data, _scale*dataadj], axis=1)

            df.index = pd.DatetimeIndex(df.index)
            print("data.yahoofin.getdaily df success")
            '''
        except:
            df = None
            print("data.yahoofin.getdaily failed")
        finally:
            return df

    def writedaily(self, _df, _symbol='^GSPC', _path='py/equity/data/'):
        '''
        desc:       write daily df to files
        '''
        try:
            file = f'{_path}{self.PROVIDER}-{_symbol}.csv'
            _df.to_csv(file)
            print("data.yahoofin.write success ", file)
        except:
            print("data.yahoofin.write failed")
        finally:
            return

    def readdaily(self, _symbol='^GSPC', _path='py/equity/data/', _typemap=TYPEMAP, _parsedates=PARSEDATES):
        '''
        desc:       read csv of daily data to df
        '''
        try:
            file = f'{_path}{self.PROVIDER}-{_symbol}.csv'
            df = pd.read_csv(file, index_col=0, dtype=_typemap, parse_dates=_parsedates)
            df.index = pd.DatetimeIndex(df.index)
            print("data.yahoofin.readdf success ", file)
        except:
            df = None
            print("data.yahoofin.readdf failed ", file)
        finally:
            return df

def writexlsx(_file, _group, _df, _prd):
    '''
    desc:   write df and measures to files
    '''
    try:
        options = {}
        options['strings_to_formulas'] = False
        options['strings_to_urls'] = False

        with pd.ExcelWriter(_file, engine='openpyxl', mode='wb', options=options) as writer:
            for group, df, prd in zip(_group, _df, _prd):
                prd = min(prd, df.shape[0])
                df.tail(prd).to_excel(writer, sheet_name=group)
        print("writexlsx success ", _file)
    except:
        print("writexlsx failed", _file)
    finally:
        return
