import pandas as pd
import numpy as np

class IndicatorBase:
    @staticmethod
    def calculate_rsi(data, window=14):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(data):
        short_ema = data['Close'].ewm(span=12, adjust=False).mean()
        long_ema = data['Close'].ewm(span=26, adjust=False).mean()
        macd = short_ema - long_ema
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

    @staticmethod
    def calculate_bollinger_bands(data, window=20, num_of_std=2):
        rolling_mean = data['Close'].rolling(window).mean()
        rolling_std = data['Close'].rolling(window).std()
        upper_band = rolling_mean + (rolling_std * num_of_std)
        lower_band = rolling_mean - (rolling_std * num_of_std)
        return rolling_mean, upper_band, lower_band

    @staticmethod
    def calculate_atr(data, window=14):
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window).mean()
        return atr

    @staticmethod
    def calculate_williams_r(data, window=14):
        highest_high = data['High'].rolling(window).max()
        lowest_low = data['Low'].rolling(window).min()
        williams_r = (highest_high - data['Close']) / (highest_high - lowest_low) * -100
        return williams_r

    @staticmethod
    def calculate_adx(data, window=14):
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





