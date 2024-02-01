import requests
import numpy as np
import math
from talib import MACD

def fetch_candlestick_data(symbol, interval):
    url = f'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': 1000
    }
    response = requests.get(url, params=params)
    data = response.json()
    candlestick_data = []
    close_prices = []

    for candlestick in data:
        timestamp = candlestick[0] // 1000
        open_price = float(candlestick[1])
        high_price = float(candlestick[2])
        low_price = float(candlestick[3])
        close_price = float(candlestick[4])
        volume = float(candlestick[5])

        candlestick_data.append({
            'time': timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'sma': {}
        })

    close_prices = np.array([float(entry[4]) for entry in data])

    add_sma_to_data(candlestick_data, 20)
    add_sma_to_data(candlestick_data, 50)
    add_rsi_to_data(candlestick_data)
    #add_macd_to_data(candlestick_data)
    add_macd_to_data(close_prices, candlestick_data)
    add_sma_strategy_signals(candlestick_data, 20, 50)
    return {'candlestick_data': candlestick_data, 'smas': [20, 50]}

def add_sma_strategy_signals(data, fast_sma, slow_sma):
    for index, candlestick in enumerate(data):
        if index == 0:
            continue
        fast_sma_value = candlestick['sma'][fast_sma]
        slow_sma_value = candlestick['sma'][slow_sma]
        prev_fast_sma_value = data[index - 1]['sma'][fast_sma]
        prev_slow_sma_value = data[index - 1]['sma'][slow_sma]
        if fast_sma_value and slow_sma_value and prev_fast_sma_value and prev_slow_sma_value:
            candlestick['long'] = False
            candlestick['short'] = False
            if (fast_sma_value > slow_sma_value) and (prev_fast_sma_value <= prev_slow_sma_value):
                candlestick['long'] = True
            elif (fast_sma_value < slow_sma_value) and (prev_fast_sma_value >= prev_slow_sma_value):
                candlestick['short'] = True

def calculate_sma(data, sma_length):
    sma_values = []
    closing_prices = [candlestick['close'] for candlestick in data]

    for i in range(len(data)):
        if i < sma_length - 1:
            sma_values.append(None)
        else:
            sma = sum(closing_prices[i - sma_length + 1: i + 1]) / sma_length
            sma_values.append(sma)

    return sma_values

def add_sma_to_data(data, sma_length = 20):
    sma_values = calculate_sma(data, sma_length)
    for candlestick, sma_value in zip(data, sma_values):
        candlestick['sma'][sma_length] = sma_value
    return data

def add_rsi_to_data(data, rsi_length = 14):
    rsi_values = calculate_rsi(data, rsi_length)
    for candlestick, rsi_value in zip(data, rsi_values):
        candlestick['rsi'] = rsi_value
    return data

def calculate_rsi(data, rsi_length = 14):
    if len(data) < rsi_length:
        raise ValueError("Not enough data to calculate RSI")

    rsi_values = [None] * (rsi_length - 1)
    closing_prices = [candlestick['close'] for candlestick in data]
    
    # Initialize gains and losses
    gains = losses = 0
    for i in range(1, rsi_length):
        change = closing_prices[i] - closing_prices[i - 1]
        gains += max(change, 0)
        losses += abs(min(change, 0))
    
    for i in range(rsi_length, len(data)):
        change = closing_prices[i] - closing_prices[i - 1]
        gains = (gains * (rsi_length - 1) + max(change, 0)) / rsi_length
        losses = (losses * (rsi_length - 1) + abs(min(change, 0))) / rsi_length
        
        rs = gains / losses if losses != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)

    return rsi_values

# def add_macd_to_data(data, fast_window = 12, slow_window = 26, signal_window = 9):
#     macd_values = calculate_macd_signals(data, fast_window, slow_window, signal_window)
#     for candlestick, macd_value in zip(data, macd_values):
#         if macd_value:
#             for property in macd_value:
#                 candlestick[property] = macd_value[property]
#     return data

# def calculate_macd_signals(data, fast_window, slow_window, signal_window):
#     fast_ema = calculate_ema(data, fast_window)
#     slow_ema = calculate_ema(data, slow_window)
    
#     macd_line = [{'close': fast - slow} for fast, slow in zip(fast_ema, slow_ema)]
#     signal_line = calculate_ema(macd_line, signal_window)

#     macd_data = []
#     for macd, signal in zip(macd_line, signal_line):
#         macd_data.append({
#             'macd': macd['close'],
#             'signal': signal,
#             'histogram': macd['close'] - signal
#             })
#     return (len(data) - len(macd_data))*[None] + macd_data

# def calculate_ema(data, window):
#     prices = [candle['close'] for candle in data]
#     ema = []
#     smoothing = 2 / (window + 1)
    
#     # Calculate SMA for the first data point
#     sma = sum(prices[:window]) / window
#     ema.append(sma)
    
#     # Calculate EMA for the rest of the data points
#     for price in prices[window:]:
#         next_ema = (price - ema[-1]) * smoothing + ema[-1]
#         ema.append(next_ema)
    
#     return ema

def add_macd_to_data(closing_prices, data):
    macd, signal, _ = MACD(closing_prices, fastperiod=12, slowperiod=26, signalperiod=9)

    for candlestick, m, s in zip(data, macd, signal):
        if (not math.isnan(m)) and (not math.isnan(s)):
            candlestick['macd'] = m
            candlestick['signal'] = s
            candlestick['histogram'] = m - s