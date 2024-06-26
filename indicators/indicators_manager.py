from .indicators_base import IndicatorBase
from datetime import timedelta
import pandas as pd

class IndicatorsManager:
    def __init__(self, data, buy_threshold, sell_threshold, use_latest_only=False):
        self.data = data
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.use_latest_only = use_latest_only
        self.add_indicators()

    def add_indicators(self):
        self.data['SMA50'] = self.data['Close'].rolling(window=50, min_periods=1).mean()
        self.data['SMA200'] = self.data['Close'].rolling(window=200, min_periods=1).mean()
        self.data['RSI'] = IndicatorBase.calculate_rsi(self.data)
        self.data['MACD'], self.data['Signal'] = IndicatorBase.calculate_macd(self.data)
        mb, ub, lb = IndicatorBase.calculate_bollinger_bands(self.data)
        self.data['Middle Band'] = mb
        self.data['Upper Band'] = ub
        self.data['Lower Band'] = lb
        self.data['ATR'] = IndicatorBase.calculate_atr(self.data)
        self.data['Williams %R'] = IndicatorBase.calculate_williams_r(self.data)
        self.data['ADX'] = IndicatorBase.calculate_adx(self.data)

    def should_buy(self, row):
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
        return score

    def should_sell(self, row):
        weights = {
            'sma_crossover': 0.25,
            'rsi': 0.15,
            'bollinger': 0.15,
            'macd': 0.15,
            'williams_r': 0.15,
            'adx': 0.15
        }
        score = 0
        if row['SMA50'] < row['SMA200']:
            score += weights['sma_crossover']
        if row['RSI'] > 70:
            score += weights['rsi']
        if row['Close'] >= row['Upper Band']:
            score += weights['bollinger']
        if row['MACD'] < row['Signal']:
            score += weights['macd']
        if row['Williams %R'] > -20:
            score += weights['williams_r']
        if row['ADX'] > 20:
            score += weights['adx']
        return score

    def calculate_signals(self):
        if self.use_latest_only:
            latest_row = self.data.iloc[-1]
            self.data['Buy Signal'] = self.should_buy(latest_row) > self.buy_threshold
            self.data['Sell Signal'] = self.should_sell(latest_row) > self.sell_threshold
        else:
            self.data['Buy Signal'] = self.data.apply(lambda row: self.should_buy(row) > self.buy_threshold, axis=1)
            self.data['Sell Signal'] = self.data.apply(lambda row: self.should_sell(row) > self.sell_threshold, axis=1)
        return self.data


    def backtest_strategy_multiple_signals(self, hold_period):
        buy_signals = self.data[self.data['Buy Signal'] > 0]
        total_return = 0
        num_signals = len(buy_signals)
        
        if num_signals == 0:
            return None, None, False
        
        for buy_date in buy_signals.index:
            sell_date = buy_date + timedelta(days=hold_period)
            if sell_date in self.data.index:
                buy_price = self.data.loc[buy_date, 'Close']
                sell_price = self.data.loc[sell_date, 'Close']
                total_return += (sell_price - buy_price) / buy_price
        
        average_return = total_return / num_signals if num_signals > 0 else 0
        first_buy_signal_date = buy_signals.index[0] if not buy_signals.empty else None
        sufficient_data = all((buy_date + timedelta(days=hold_period)) in self.data.index for buy_date in buy_signals.index)
        
        return average_return, first_buy_signal_date, sufficient_data




