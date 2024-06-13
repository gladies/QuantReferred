import pandas as pd
import numpy as np

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

def should_buy(row, threshold):
    weights = {
        'sma_crossover': 0.25,
        'rsi': 0.15,
        'bollinger': 0.15,
        'macd': 0.15,
        'williams_r': 0.15,
        'adx': 0.15
    }
    score = 0
    if row['SMA50'] > row['SMA200']:
        score += weights['sma_crossover']
    if row['RSI'] < 30:
        score += weights['rsi']
    if row['Close'] <= row['Lower Band']:
        score += weights['bollinger']
    if row['MACD'] > row['Signal']:
        score += weights['macd']
    if row['Williams %R'] < -80:
        score += weights['williams_r']
    if row['ADX'] > 20:
        score += weights['adx']
    return score if score >= threshold else score

def calculate_buy_signals(data, threshold):
    data['SMA50'] = data['Close'].rolling(window=50, min_periods=1).mean()
    data['SMA200'] = data['Close'].rolling(window=200, min_periods=1).mean()
    data['RSI'] = calculate_rsi(data, 14)
    data['MACD'], data['Signal'] = calculate_macd(data)
    mb, ub, lb = calculate_bollinger_bands(data, 20, 2)
    data['Middle Band'] = mb
    data['Upper Band'] = ub
    data['Lower Band'] = lb
    data['ATR'] = calculate_atr(data, 14)
    data['Williams %R'] = calculate_williams_r(data, 14)
    data['ADX'] = calculate_adx(data, 14)
    data['Buy Signal'] = data.apply(should_buy, axis=1, threshold=threshold)
    return data




