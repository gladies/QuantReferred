import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def fetch_data_with_retry(symbol, api_key, retries=3):
    from alpha_vantage.timeseries import TimeSeries
    ts = TimeSeries(key=api_key, output_format='pandas')
    for _ in range(retries):
        try:
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')
            return data, meta_data
        except Exception as e:
            print(f"Error fetching data: {e}")
    return None, None

def fetch_data_from_file(file_path):
    data = pd.read_json(file_path)
    data.index = pd.to_datetime(data.index)
    return data

def style_data(val, col):
    if col == 'RSI':
        if val > 70:
            return 'color: red'
        elif val < 30:
            return 'color: green'
    elif col == 'Williams %R':
        if val > -20:
            return 'color: red'
        elif val < -80:
            return 'color: green'
    elif col == 'ADX':
        if val > 25:
            return 'color: red'
        elif val < 20:
            return 'color: green'
    return 'color: black'

def generate_plot(data, stock_symbol):
    plt.switch_backend('Agg')
    plt.figure(figsize=(14, 7))
    plt.plot(data.index, data['Close'], label='Close Price')
    plt.title(f'Stock Price for {stock_symbol}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plot_path = f'static/{stock_symbol}_plot.png'
    plt.savefig(plot_path)
    plt.close()
    return f'/{plot_path}'

def backtest_strategy_multiple_signals(data, hold_period):
    buy_signals = data[data['Buy Signal'] > 0]
    total_return = 0
    num_signals = len(buy_signals)
    
    if num_signals == 0:
        return None, None, False
    
    for buy_date in buy_signals.index:
        sell_date = buy_date + timedelta(days=hold_period)
        if sell_date in data.index:
            buy_price = data.loc[buy_date, 'Close']
            sell_price = data.loc[sell_date, 'Close']
            total_return += (sell_price - buy_price) / buy_price
    
    average_return = total_return / num_signals if num_signals > 0 else 0
    first_buy_signal_date = buy_signals.index[0] if not buy_signals.empty else None
    sufficient_data = all((buy_date + timedelta(days=hold_period)) in data.index for buy_date in buy_signals.index)
    
    return average_return, first_buy_signal_date, sufficient_data







