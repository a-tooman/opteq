# ####################################
#   author: Anthony Tooman
#   date:   202012
#   desc:   opteq-0.02
# ####################################


import pandas as pd
import numpy as np
from scipy.optimize import curve_fit


class polyfit:
    '''
    desc: fitter
    '''

    featuresx = ['cln^2'
            ,'lln^2'
            ,'hln^2'
            ,'lhln^2'
            ,'lhln^2-mu-2'
            ,'lhln^2-mu-3'
            ,'lhln^2-rank-252'
            ,'lhln^2-rsi']

    featuresy = ['lhln^2-mu-2']
    percent = [0.01,0.1]

    lag1 = 1
    lag2 = 2

    def __init__(self, _group, _name, _df, _obs=5*52):
        self.group = _group
        self.name = _name
        self.df = _df
        self.obs = _obs
        return

    def runner(self):
        '''
        print blocks of obs
        '''
        # xdata
        # concat lagged data
        # normalise data
        self.polyfit = []
        for row in range(self.df.shape[0] + 1 - self.obs, self.df.shape[0] + 1):
            self.polyfit.append(self.mdlfit(_row=row))

        self.polyfit = pd.DataFrame.from_records(self.polyfit)
        self.polyfit.index = self.df.tail(self.obs).index
        self.polyfit.columns = [(self.group,f'{self.featuresy[0]}-est'),(self.group,'scalarvar'),(self.group,'scalar10pc'),(self.group,'scalar1pct')]
        self.polyfit.columns = pd.MultiIndex.from_tuples(self.polyfit.columns, names=["group", "var"])
        return

    def getdf(self):
        return self.polyfit

    def corr(self, _df, _prd=1):
        '''
        correlation between featuresx and featuresy
        _prd = shift
        _obs = length of study
        '''
        df = pd.concat([_df.shift(_prd).tail(self.obs), _df[self.featuresy].tail(self.obs)], axis=1)
        corr = np.corrcoef(df, rowvar=False)
        corr = pd.Series(corr[-1], index=df.columns)
        print(corr.sort_values(ascending=False))
        return

    def norm(self, _df):
        '''
        normalise variables
        (x - mu)/std
        return norm, mean, std
        '''
        return (_df-_df.mean())/_df.std(), _df.mean()[0], _df.std()[0]

    def poly(self, _df, _ones):
        '''
        polynomial: x + x^3 + ... + x^n + 1
        '''
        return np.c_[_df, _df**2, _df**3, _df**4, _df**5, _ones]

    def func(self ,_x, *_coef):
        '''
        polynomial: a1*x1 + a2*x2 + ... + an*xn + c*1
        '''
        #x = np.dot(_coef,_x)
        x = np.dot(_x,np.array(_coef).T)
        return x

    def scaleest(self, _y, _yest):
        '''
        yest scaling factors
        '''
        s = _yest/_y
        s = s[s < 1.]
        d = s.describe(percentiles=self.percent)

        # scale yest to 99% confidence interval
        # scale var = mu - 2.6 * std/sqrt(obs)
        scalarvar = s.mean()[0] - 2.576*s.std()[0]/np.sqrt(self.obs)

        # scale by 10% percentile
        scalar10pct = d.loc['10%'].values[0]

        # scale by 1% percentile
        scalar1pct = d.loc['1%'].values[0]

        return scalarvar, scalar10pct, scalar1pct

    def plotfit(self, _y, _yestvar, _yest10pct, _yest1pct):
        from matplotlib import pyplot
        # create a line plot for the mapping function
        pyplot.plot(np.sqrt(_y), color='red', linewidth=1.0)
        pyplot.plot(np.sqrt(_yestvar), color='green',linewidth=1.0)
        pyplot.plot(np.sqrt(_yest10pct), '--', color='blue',linewidth=1.0)
        pyplot.plot(np.sqrt(_yest1pct), '--', color='k',linewidth=1.0)
        pyplot.show()
        return

    def mdlfit(self, _row):
        '''
        dy(t) = f(X^(deg),param) + error
        '''
        # xdata
        # concat lagged data
        # normalise data
        x = pd.concat([self.df.iloc[:_row][self.featuresx].shift(self.lag1).tail(self.obs)
            , self.df.iloc[:_row][self.featuresx].shift(self.lag2).tail(self.obs)],axis=1)
        xnorm, xmu, xstd = self.norm(x)
        xnorm = xnorm.to_numpy()
        xnorm = self.poly(_df=xnorm, _ones=np.ones(self.obs).T)

        # param is same width as x
        param = (1./3.)*np.ones((xnorm.shape[1]), dtype=np.float)

        # y = y0 * exp(alpha * x + c)
        # ln(y) - ln(y0) = alpha * x + c
        y0 = self.df.iloc[:_row][self.featuresy].shift(1).tail(self.obs)
        y = self.df.iloc[:_row][self.featuresy].tail(self.obs)

        # Z = ln(y) - ln(y0) = alpha * x + c
        # (Z - Zmu)/Zstd = alpha' * (x-xmu)/xstd + c'
        Z = np.log(y) - np.log(y0)
        Znorm, Zmu, Zstd = self.norm(Z)
        Znorm = Znorm.to_numpy()[0]

        # curve_fit
        popt, pcov = curve_fit(self.func, xdata=xnorm, ydata=Znorm, p0=param)

        '''
        Recover y from Z
        y = y0*exp(Zstd*(alpha' * (x-xmu)/xstd + c') + Zmu)
        '''
        yest = Zstd*self.func(xnorm, popt) + Zmu
        yest = y0*np.exp(yest)
        yest = yest

        #print(f'Actual {y.describe()}')
        #print(f'Estimate {yest.describe()}')

        scalarvar, scalar10pct, scalar1pct = self.scaleest(_y=y, _yest=yest)

        '''
        estimate Y(t+dt)
        '''
        x = pd.concat([self.df.iloc[:_row][self.featuresx].shift(self.lag1-1).tail(self.obs)
            ,self.df.iloc[:_row][self.featuresx].shift(self.lag2-1).tail(self.obs)],axis=1)
        xnorm, xmu, xstd = self.norm(x)
        xnorm = xnorm.to_numpy()
        xnorm = self.poly(_df=xnorm, _ones=np.ones(self.obs).T)

        yest = Zstd*self.func(xnorm, popt) + Zmu
        yest = y*np.exp(yest)
        yest = yest

        return [yest.tail(1).values[0][0], scalarvar, scalar10pct, scalar1pct]
