import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta

def calculate_rsi(data, window):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    short_ema = data['Close'].ewm(span=12, adjust=False).mean()
    long_ema = data['Close'].ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(data, window, num_of_std):
    rolling_mean = data['Close'].rolling(window).mean()
    rolling_std = data['Close'].rolling(window).std()
    upper_band = rolling_mean + (rolling_std * num_of_std)
    lower_band = rolling_mean - (rolling_std * num_of_std)
    return rolling_mean, upper_band, lower_band

def calculate_atr(data, window):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window).mean()
    return atr

def calculate_williams_r(data, window):
    highest_high = data['High'].rolling(window).max()
    lowest_low = data['Low'].rolling(window).min()
    williams_r = (highest_high - data['Close']) / (highest_high - lowest_low) * -100
    return williams_r

def calculate_adx(data, window):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window).mean()

    up_move = data['High'] - data['High'].shift()
    down_move = data['Low'].shift() - data['Low']
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    pos_dm = pd.Series(pos_dm, index=data.index)
    neg_dm = pd.Series(neg_dm, index=data.index)
    
    pos_di = 100 * (pos_dm.rolling(window).sum() / atr)
    neg_di = 100 * (neg_dm.rolling(window).sum() / atr)
    dx = 100 * np.abs((pos_di - neg_di) / (pos_di + neg_di))
    adx = dx.rolling(window).mean()

    return adx

def should_buy(filtered_data):
    weights = {
        'sma_crossover': 0.25,
        'rsi': 0.15,
        'bollinger': 0.15,
        'macd': 0.15,
        'williams_r': 0.15,
        'adx': 0.15
    }
    score = 0
    if filtered_data['SMA50'].iloc[-1] > filtered_data['SMA200'].iloc[-1]:
        score += weights['sma_crossover']
    if filtered_data['RSI'].iloc[-1] < 30:
        score += weights['rsi']
    if filtered_data['Close'].iloc[-1] <= filtered_data['Lower Band'].iloc[-1]:
        score += weights['bollinger']
    if filtered_data['MACD'].iloc[-1] > filtered_data['Signal'].iloc[-1]:
        score += weights['macd']
    if filtered_data['Williams %R'].iloc[-1] < -80:
        score += weights['williams_r']
    if filtered_data['ADX'].iloc[-1] > 20:
        score += weights['adx']
    return score >= 0.7  # Adjust the threshold as needed

def filter_stocks(stock_symbols, api_key):
    buy_signals = []
    ts = TimeSeries(key=api_key, output_format='pandas')

    for symbol in stock_symbols:
        try:
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data.index = pd.to_datetime(data.index)
            data = data.sort_index()

            latest_date = data.index.max()
            start_date = latest_date - timedelta(days=365)
            # Explicitly create a copy of the filtered DataFrame to modify
            filtered_data = data[(data.index >= start_date) & (data.index <= latest_date)].copy()

            filtered_data['SMA50'] = filtered_data['Close'].rolling(window=50, min_periods=1).mean()
            filtered_data['SMA200'] = filtered_data['Close'].rolling(window=200, min_periods=1).mean()
            filtered_data['RSI'] = calculate_rsi(filtered_data, 14)
            filtered_data['MACD'], filtered_data['Signal'] = calculate_macd(filtered_data)
            # Ensure calculations are done and set correctly
            mb, ub, lb = calculate_bollinger_bands(filtered_data, 20, 2)
            filtered_data['Middle Band'] = mb
            filtered_data['Upper Band'] = ub
            filtered_data['Lower Band'] = lb
            filtered_data['ATR'] = calculate_atr(filtered_data, 14)
            filtered_data['Williams %R'] = calculate_williams_r(filtered_data, 14)
            filtered_data['ADX'] = calculate_adx(filtered_data, 14)

            if should_buy(filtered_data):
                buy_signals.append(symbol)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    return buy_signals

