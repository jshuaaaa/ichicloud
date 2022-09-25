import oandapyV20
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trade
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import numpy as np
import time
import copy

# Account credentials and parameters
token_path = "D:\My Apps\API-KEYS\oanda.txt"
client = oandapyV20.API(access_token=open(token_path, "r").read(),environment="practice")
account_id = "101-001-23303695-001"

pairs = ['GBP_USD', 'AUD_USD', "NZD_USD", "EUR_USD", "EUR_TRY", "TRY_JPY"]
pos_size = 1000

# indicators
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

# Live trading functions

def trade_signal(DF,l_s):
    signal = ""
    df = copy.deepcopy(DF)
    if l_s == "":
   
    elif l_s == "long":

        
    elif l_s == "short":

    return signal



def market_order(instrument,units,sl, tp):
    """units can be positive or negative, stop loss (in pips) added/subtracted to price """  
    account_id = "101-001-23303695-001"
    data = {
            "order": {
            "price": "",
            "stopLossOnFill": {
            "timeInForce": "GTC",
            "price": str(sl)
                              },
            "takeProfitOnFill": {
                    "timeInForce": "GTC",
                    "price": str(tp)
                    },
            "timeInForce": "FOK",
            "instrument": str(instrument),
            "units": str(units),
            "type": "MARKET",
            "positionFill": "DEFAULT"
                    }
            }
    r = orders.OrderCreate(accountID=account_id, data=data)
    client.request(r)
    
