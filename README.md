# Ichicloud

## Ichicloud is an Open-Source automated trading system utilizing technical indicators such as the Ichimoku Cloud, RSI and ATR.

## How does it work?
The system looks for a signal based on the position of the price relative to the 5 indicators apart of the Ichimoku Cloud and if certain conditions are met and the RSI is strong, the system will open a long position, using ATR to set stop loss and take profit orders relative to current volatility.

## Is the strategy profitable?
The strategy has been backtested and is currently undergoing testing live on an OANDA demo account. The strategy proved to profitable trading forex on 50x, and I have attached a graph generated from the backtesting script of the past 60 days, using 15 minute candles, and another graph from the past 2 years using 1 hour candles.

## 60 days, 15 Minute Candles
![backtesting_graph_60_days](https://user-images.githubusercontent.com/95507083/193339538-3aec8a22-a74e-479a-8ea3-92fa260612bf.png)

### 2 years, 1 hour candles
![backtesting_graph_2_years](https://user-images.githubusercontent.com/95507083/193339712-9a0cc183-6bbf-41e0-b08f-d34a37e15e8b.png)
