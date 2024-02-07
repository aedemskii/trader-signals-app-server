import requests
import math
import numpy as np
from talib import MACD, STOCHRSI, SMA, EMA, BBANDS, RSI


CONST_SMA = 200
CONST_EMA = 50
CONST_RSI = 14
CONST_MACD_FAST = 12
CONST_MACD_SLOW = 26
CONST_MACD_SIGNAL = 9
CONST_STOCHRSI_K = 14
CONST_STOCHRSI_D = 3
CONST_BBANDS_SMA = 20
CONST_BBANDS_MA = 2

KEY_TIME = 'time'
KEY_OPEN = 'open'
KEY_HIGH = 'high'
KEY_LOW = 'low'
KEY_CLOSE = 'close'
KEY_VOLUME = 'volume'
KEY_SMA = 'sma'
KEY_EMA = 'ema'
KEY_RSI = 'rsi'
KEY_MACD_MACD = 'macd-macd'
KEY_MACD_SIGNAL = 'macd-signal'
KEY_MACD_HIST = 'macd-hist'
KEY_STOCHRSI_SLOW = 'stochrsi-slow'
KEY_STOCHRSI_FAST = 'stochrsi-fast'
KEY_BBANDS_LOWER = 'bbands-lower'
KEY_BBANDS_SMA = 'bbands-sma'
KEY_BBANDS_HIGHER = 'bbands-higher'


def gatcher_data_for_client(symbol, interval):
    data = fetch_candlestick_data(symbol, interval)
    if data is None:
        return None
    else:
        indicators = calculate_indicators(data)
        data_for_client = compose_data_for_client(data, indicators)
        return data_for_client


def fetch_candlestick_data(symbol, interval):
    try:
        url = f'https://api.binance.com/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': 600
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data
    
    except Exception as e:
        print(e)
        return None
    

def calculate_indicators(data):
    indicators = {}

    close_prices = np.array([float(entry[4]) for entry in data])

    indicators[KEY_SMA] = SMA(close_prices, CONST_SMA)
    indicators[KEY_EMA] = EMA(close_prices, CONST_EMA)
    indicators[KEY_RSI] = RSI(close_prices, CONST_RSI)

    macd, signal, _ = MACD(close_prices, CONST_MACD_FAST, CONST_MACD_SLOW, CONST_MACD_SIGNAL)
    indicators[KEY_MACD_MACD] = macd
    indicators[KEY_MACD_SIGNAL] = signal

    bb_higher, bb_sma, bb_lower = BBANDS(close_prices, CONST_BBANDS_SMA, CONST_BBANDS_MA)
    indicators[KEY_BBANDS_LOWER] = bb_lower
    indicators[KEY_BBANDS_SMA] = bb_sma
    indicators[KEY_BBANDS_HIGHER] = bb_higher

    srsi_slow, srsi_fast = STOCHRSI(close_prices, CONST_STOCHRSI_D, CONST_STOCHRSI_D, CONST_STOCHRSI_D)
    indicators[KEY_STOCHRSI_SLOW] = srsi_slow
    indicators[KEY_STOCHRSI_FAST] = srsi_fast

    return indicators


def compose_data_for_client(data, indicators):
    data_for_client = []
    for candlestick, sma, ema, rsi, macd_macd, macd_signal, bb_lower, bb_sma, bb_higher, srsi_slow, srsi_fast in zip(data, indicators['sma'], indicators['ema'], indicators['rsi'], indicators['macd-macd'], indicators['macd-signal'], indicators['bbands-lower'], indicators['bbands-sma'], indicators['bbands-higher'], indicators['stochrsi-slow'], indicators['stochrsi-fast']):
        candlestick_data = {
            KEY_TIME: candlestick[0] // 1000,
            KEY_OPEN: float(candlestick[1]),
            KEY_HIGH: float(candlestick[2]),
            KEY_LOW: float(candlestick[3]),
            KEY_CLOSE: float(candlestick[4]),
            KEY_VOLUME: float(candlestick[5])
        }

        if not math.isnan(sma):
            candlestick_data[KEY_SMA] = float(sma)

        if not math.isnan(ema):
            candlestick_data[KEY_EMA] = float(ema)

        if not math.isnan(rsi):
            candlestick_data[KEY_RSI] = float(rsi)

        if (not math.isnan(macd_macd)) and (not math.isnan(macd_signal)):
            candlestick_data[KEY_MACD_MACD] = float(macd_macd)
            candlestick_data[KEY_MACD_SIGNAL] = float(macd_signal)
            candlestick_data[KEY_MACD_HIST] = float(macd_macd - macd_signal)

        if (not math.isnan(bb_lower)) and (not math.isnan(bb_sma)) and (not math.isnan(bb_higher)):
            candlestick_data[KEY_BBANDS_LOWER] = float(bb_lower)
            candlestick_data[KEY_BBANDS_SMA] = float(bb_sma)
            candlestick_data[KEY_BBANDS_HIGHER] = float(bb_higher)

        if (not math.isnan(srsi_slow)) and (not math.isnan(srsi_fast)):
            candlestick_data[KEY_STOCHRSI_SLOW] = float(srsi_slow)
            candlestick_data[KEY_STOCHRSI_FAST] = float(srsi_fast)

        data_for_client.append(candlestick_data)

    return data_for_client