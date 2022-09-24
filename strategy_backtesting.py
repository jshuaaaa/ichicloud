import yfinance as yf
import numpy as np
import copy
import pandas as pd
import matplotlib.pyplot as plt

stocks = ["JPY=X", "EUR=X"]
clhv = {}

# Indicators  
def ichimoku_cloud(DF):
    df = DF.copy()
    nine_period_high = df['High'].rolling(window= 9).max()
    nine_period_low = df['Low'].rolling(window= 9).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) /2
    
    period26_high = df['High'].rolling(window=26).max()
    period26_low = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2
    
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = df['High'].rolling(window=52).max()
    period52_low = df['Low'].rolling(window=52).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    # The most current closing price plotted 26 time periods behind (optional)
    df['chikou_span'] = df['Close'].shift(-26)
    return df.loc[:,['tenkan_sen', 'kijun_sen','senkou_span_a', 'senkou_span_b', 'chikou_span']]

def RSI(DF, n=14):
    df = DF.copy()
    df["change"] = df["Adj Close"] - df["Adj Close"].shift(1)
    df["gain"] = np.where(df["change"]>=0,df["change"], 0)
    df["loss"] = np.where(df["change"]<0,-1*df["change"], 0)
    df["avgGain"] = df["gain"].ewm(alpha=1/n, min_periods=n).mean()
    df["avgLoss"] = df["loss"].ewm(alpha=1/n, min_periods=n).mean()
    df["rs"] = df["avgGain"]/df["avgLoss"]
    df["rsi"] = 100 - (100/(1+df["rs"]))
    return df["rsi"]



# Downloading Data
tickers_signal = {}
tickers_ret = {}
for ticker in stocks:
    temp = yf.download(ticker, period='60d', interval='15m')
    temp.dropna(how="any", inplace=True)
    clhv[ticker] = temp
    clhv[ticker][['tenkan_sen', 'kijun_sen','senkou_span_a', 'senkou_span_b', 'chikou_span']] = ichimoku_cloud(clhv[ticker])
    clhv[ticker]["RSI"] = RSI(clhv[ticker])
    tickers_signal[ticker] = ""
    tickers_ret[ticker] = []
    

        
    
    
############################ BACKTESTING ###############################

df = copy.deepcopy(clhv)

# adding neccesary data into our dataframe
for ticker in stocks:
    df[ticker].dropna(inplace=True)
    df[ticker]["above_cloud"] = 0
    df[ticker]["above_cloud"] = np.where((df[ticker]['Low'] > df[ticker]['senkou_span_a'])  & (df[ticker]['Low'] > df[ticker]['senkou_span_b'] ), 1, df[ticker]['above_cloud'])
    df[ticker]["above_cloud"] = np.where((df[ticker]['High'] < df[ticker]['senkou_span_a']) & (df[ticker]['High'] < df[ticker]['senkou_span_b']), -1, df[ticker]['above_cloud'])
    df[ticker]['A_above_B'] = np.where((df[ticker]['senkou_span_a'] > df[ticker]['senkou_span_b']), 1, -1)
    df[ticker]['tenkan_kiju_cross'] = np.NaN
    df[ticker]['tenkan_kiju_cross'] = np.where((df[ticker]['tenkan_sen'].shift(1) <= df[ticker]['kijun_sen'].shift(1)) & (df[ticker]['tenkan_sen'] > df[ticker]['kijun_sen']), 1, df[ticker]['tenkan_kiju_cross'])
    df[ticker]['tenkan_kiju_cross'] = np.where((df[ticker]['tenkan_sen'].shift(1) >= df[ticker]['kijun_sen'].shift(1)) & (df[ticker]['tenkan_sen'] < df[ticker]['kijun_sen']), -1, df[ticker]['tenkan_kiju_cross'])
    df[ticker]['price_tenkan_cross'] = np.NaN
    df[ticker]['price_tenkan_cross'] = np.where((df[ticker]['Open'].shift(1) <= df[ticker]['tenkan_sen'].shift(1)) & (df[ticker]['Open'] > df[ticker]['tenkan_sen']), 1, df[ticker]['price_tenkan_cross'])
    df[ticker]['price_tenkan_cross'] = np.where((df[ticker]['Open'].shift(1) >= df[ticker]['tenkan_sen'].shift(1)) & (df[ticker]['Open'] < df[ticker]['tenkan_sen']), -1, df[ticker]['price_tenkan_cross'])


strategy_df = pd.DataFrame()
 
for ticker in stocks:
    print("calculating returns for ", ticker)

    for i in range(len(df[ticker])):
        if tickers_signal[ticker] == "":
            tickers_ret[ticker].append(0)
            if (((df[ticker]["above_cloud"][i-1] == 1)  and (df[ticker]["A_above_B"][i-1] == 1)  and (df[ticker]['tenkan_kiju_cross'][i-1]==1))  or df[ticker]['price_tenkan_cross'][i-1] == 1)  and df[ticker]["RSI"][i] > 60:
                tickers_signal[ticker] = "Buy"
            elif (((df[ticker]["above_cloud"][i-1] == -1)  and (df[ticker]["A_above_B"][i-1] == -1)  and (df[ticker]['tenkan_kiju_cross'][i-1]==-1))  or df[ticker]['price_tenkan_cross'][i-1] == -1)  and df[ticker]["RSI"][i] < 40:
                tickers_signal[ticker] = "Sell"
                
                
        elif tickers_signal[ticker] == "Buy":
            tickers_ret[ticker].append(((df[ticker]["Adj Close"][i-1]/df[ticker]["Adj Close"][i])-1))
            if (((df[ticker]["above_cloud"][i-1] == -1)  and (df[ticker]["A_above_B"][i-1] == -1)  and (df[ticker]['tenkan_kiju_cross'][i-1]==-1))  or df[ticker]['price_tenkan_cross'][i-1] == -1)  and df[ticker]["RSI"][i] < 40:
                tickers_signal[ticker] = "Sell"
         
            
        elif tickers_signal[ticker] == "Sell":
            tickers_ret[ticker].append(((df[ticker]["Adj Close"][i]/df[ticker]["Adj Close"][i-1])-1))
            if (((df[ticker]["above_cloud"][i-1] == 1)  and (df[ticker]["A_above_B"][i-1] == 1)  and (df[ticker]['tenkan_kiju_cross'][i-1]==1))  or df[ticker]['price_tenkan_cross'][i-1] == 1)  and df[ticker]["RSI"][i] > 60:
                tickers_signal[ticker] = "Buy"
    
    df[ticker]["ret"] = np.array(tickers_ret[ticker])

    


strategy_df = pd.DataFrame()
for ticker in stocks:
    strategy_df[ticker] = df[ticker]["ret"]
strategy_df["ret"] = strategy_df.mean(axis=1)  

(1+strategy_df["ret"]).cumprod().plot() 
    
    
    
    
    
    
    
    
    