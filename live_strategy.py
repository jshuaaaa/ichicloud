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

pairs = ['GBP_USD', 'AUD_USD', "NZD_USD", "EUR_USD", "GBP_JPY", "CAD_CHF", "GBP_PLN"]
pos_size = 1000

# indicators
def ichimoku_cloud(DF):
    df = DF.copy()
    nine_period_high = df['h'].rolling(window= 9).max()
    nine_period_low = df['l'].rolling(window= 9).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) /2
    
    period26_high = df['h'].rolling(window=26).max()
    period26_low = df['l'].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2
    
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = df['h'].rolling(window=52).max()
    period52_low = df['l'].rolling(window=52).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    # The most current closing price plotted 26 time periods behind (optional)
    df['chikou_span'] = df['c'].shift(-26)
    return df.loc[:,['tenkan_sen', 'kijun_sen','senkou_span_a', 'senkou_span_b', 'chikou_span']]

def RSI(DF, n=14):
    df = DF.copy()
    df["change"] = df["c"] - df["c"].shift(1)
    df["gain"] = np.where(df["change"]>=0,df["change"], 0)
    df["loss"] = np.where(df["change"]<0,-1*df["change"], 0)
    df["avgGain"] = df["gain"].ewm(alpha=1/n, min_periods=n).mean()
    df["avgLoss"] = df["loss"].ewm(alpha=1/n, min_periods=n).mean()
    df["rs"] = df["avgGain"]/df["avgLoss"]
    df["rsi"] = 100 - (100/(1+df["rs"]))
    return df["rsi"]

def ATR(DF, n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['h']-df['l'])
    df['H-PC']=abs(df['h']-df['c'].shift(1))
    df['L-PC']=abs(df['l']-df['c'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return round(df2["ATR"][-1],4)

# Live trading functions

def trade_signal(DF,l_s):
    signal = ""
    df = copy.deepcopy(DF)
    if l_s == "":
        if (((df["above_cloud"].tolist()[-1] == 1)  and (df["A_above_B"].tolist()[-1] == 1)  and (df['tenkan_kiju_cross'].tolist()[-1]-1)))  and df["RSI"].tolist()[-1] > 70:
            signal = "Buy"
        elif (((df["above_cloud"].tolist()[-1] == -1)  and (df["A_above_B"].tolist()[-1] == -1)  and (df['tenkan_kiju_cross'].tolist()[-1]==-1)))  and df["RSI"].tolist()[-1] < 40:
            signal = "Sell"
   
    elif l_s == "short":
        if (((df["above_cloud"].tolist()[-1] == 1)  and (df["A_above_B"].tolist()[-1] == 1)  and (df['tenkan_kiju_cross'].tolist()[-1]==1)))  and df["RSI"].tolist()[-1] > 70:
            signal = "Close_Buy"
        elif (df['tenkan_kiju_cross'].tolist()[-1]==1):
            signal = "Close"
        
    elif l_s == "long":
        if (((df["above_cloud"].tolist()[-1] == -1)  and (df["A_above_B"].tolist()[-1] == -1)  and (df['tenkan_kiju_cross'].tolist()[-1]== -1)))  and df["RSI"].tolist()[-1] < 40:
            signal = "Close_Sell"
        elif (df['tenkan_kiju_cross'].tolist()[-1]==-1):
            signal = "Close"
            

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
    

# Script for trading

def main():
    try:
        for currency in pairs:
            print("Looking for trades for", currency)
            params = {"instruments": currency}
            r = trade.TradesList(accountID=account_id,params=params)
            open_pos = client.request(r)
            long_short = ""
            if len(open_pos["trades"])>0:
                if int(open_pos['trades'][0]['initialUnits']) > 0:
                    long_short = "long"
                else:
                    long_short='short'
                
            params = {"count":2500,"granularity": "M15"}
            candles = instruments.InstrumentsCandles(instrument=currency, params=params)
            client.request(candles)
            ohlc_dict = candles.response["candles"]
            temp = pd.DataFrame(ohlc_dict)
            ohlc_df = temp.mid.dropna().apply(pd.Series)
            ohlc_df["volume"] = temp["volume"]
            ohlc_df.index = temp["time"]
            ohlc_df = ohlc_df.apply(pd.to_numeric)
            ohlc_df[['tenkan_sen', 'kijun_sen','senkou_span_a', 'senkou_span_b', 'chikou_span']] = ichimoku_cloud(ohlc_df)
            ohlc_df["RSI"] = RSI(ohlc_df)

            ohlc_df["above_cloud"] = 0
            ohlc_df["above_cloud"] = np.where((ohlc_df['l'] > ohlc_df['senkou_span_a'])  & (ohlc_df['l'] > ohlc_df['senkou_span_b'] ), 1, ohlc_df['above_cloud'])
            ohlc_df["above_cloud"] = np.where((ohlc_df['h'] < ohlc_df['senkou_span_a']) & (ohlc_df['h'] < ohlc_df['senkou_span_b']), -1, ohlc_df['above_cloud'])
            ohlc_df['A_above_B'] = np.where((ohlc_df['senkou_span_a'] > ohlc_df['senkou_span_b']), 1, -1)
            ohlc_df['tenkan_kiju_cross'] = np.NaN
            ohlc_df['tenkan_kiju_cross'] = np.where((ohlc_df['tenkan_sen'].shift(1) <= ohlc_df['kijun_sen'].shift(1)) & (ohlc_df['tenkan_sen'] > ohlc_df['kijun_sen']), 1, ohlc_df['tenkan_kiju_cross'])
            ohlc_df['tenkan_kiju_cross'] = np.where((ohlc_df['tenkan_sen'].shift(1) >= ohlc_df['kijun_sen'].shift(1)) & (ohlc_df['tenkan_sen'] < ohlc_df['kijun_sen']), -1, ohlc_df['tenkan_kiju_cross'])
            ohlc_df['price_tenkan_cross'] = np.NaN
            ohlc_df['price_tenkan_cross'] = np.where((ohlc_df['o'].shift(1) <= ohlc_df['tenkan_sen'].shift(1)) & (ohlc_df['o'] > ohlc_df['tenkan_sen']), 1, ohlc_df['price_tenkan_cross'])
            ohlc_df['price_tenkan_cross'] = np.where((ohlc_df['o'].shift(1) >= ohlc_df['tenkan_sen'].shift(1)) & (ohlc_df['o'] < ohlc_df['tenkan_sen']), -1, ohlc_df['price_tenkan_cross'])
            signal = trade_signal(ohlc_df,long_short)

            if signal == "Buy":
                params = {"instruments": currency}
                r = pricing.PricingInfo(accountID=account_id, params=params)
                rv = client.request(r)
                sl = round(float(rv["prices"][0]["bids"][0]["price"]) - round(2*ATR(ohlc_df,14),3))
                tp = round(float(rv["prices"][0]["bids"][0]["price"]) + round(4*ATR(ohlc_df,14),3))
                market_order(currency,pos_size,sl,tp)
                print("long entered for ", currency)
            
            elif signal == "Sell":
                params = {"instruments": currency}
                r = pricing.PricingInfo(accountID=account_id, params=params)
                rv = client.request(r)
                sl = round(float(rv["prices"][0]["bids"][0]["price"]) + round(2*ATR(ohlc_df,14),3))
                tp = round(float(rv["prices"][0]["bids"][0]["price"]) - round(4*ATR(ohlc_df,14),3))
                market_order(currency,-1*pos_size,sl,tp)
                print("short entered for ", currency)
            
            elif signal == "Close":
                params = {"instruments": currency}
                r = pricing.PricingInfo(accountID=account_id, params=params)
                rv = client.request(r)
                cl = trade.TradeClose(accountID=account_id, tradeID=open_pos['trades'][0]['id'])
                client.request(cl)
                print('position closed')
            
            elif signal == "Close_Buy":
                params = {"instruments": currency}
                r = pricing.PricingInfo(accountID=account_id, params=params)
                rv = client.request(r)
                sl = round(float(rv["prices"][0]["bids"][0]["price"]) - round(2*ATR(ohlc_df,14),3))
                tp = round(float(rv["prices"][0]["bids"][0]["price"]) + round(4*ATR(ohlc_df,14),3))
                market_order(currency,pos_size,sl,tp)
                market_order(currency,pos_size,sl,tp)
                print("short closed and long entered for ", currency)
            
            elif signal == "Close_Sell":
                params = {"instruments": currency}
                r = pricing.PricingInfo(accountID=account_id, params=params)
                rv = client.request(r)
                sl = round(float(rv["prices"][0]["bids"][0]["price"]) + round(2*ATR(ohlc_df,14),3))
                tp = round(float(rv["prices"][0]["bids"][0]["price"]) - round(4*ATR(ohlc_df,14),3))
                market_order(currency,-1*pos_size,sl,tp)
                market_order(currency,-1*pos_size,sl,tp)
                print("short entered for ", currency)
                
                 
    except:
        print("error encountered....skipping this iteration")


starttime=time.time()
timeout = time.time() + 60*60*24  # 60 seconds times 60 times 8 meaning the script will run for 8 hrs

while time.time() <= timeout:
    try:
        print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main()
        time.sleep(900 - ((time.time() - starttime) % 900.0)) # 5 minute interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()
  
    

