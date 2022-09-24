import yfinance as yf
import numpy as np



stocks = ["JPY=X", "EUR=X"]
clhv = {}

for ticker in stocks:
    temp = yf.download(ticker, period='1mo', interval='15m')
    temp.dropna(how="any", inplace=True)
    clhv[ticker] = temp
