import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

def generate_plot(filtered_data, stock_symbol):
    plt.figure(figsize=(14, 7))
    plt.plot(filtered_data.index, filtered_data['Close'], label='Close Price', color='blue')
    plt.plot(filtered_data.index, filtered_data['SMA50'], label='50-Day SMA', color='red')
    plt.plot(filtered_data.index, filtered_data['SMA200'], label='200-Day SMA', color='green')
    plt.title(f'Close Price and Moving Averages for {stock_symbol} (Last 1 Year)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode()
    return f'data:image/png;base64,{img}'

def backtest_strategy(data, hold_period):
    buy_signals = data[data['Buy Signal'] >= 0.7]
    if buy_signals.empty:
        return None, None, False

    first_buy_signal_date = buy_signals.index[0]
    buy_price = data.loc[first_buy_signal_date, 'Close']
    end_date = first_buy_signal_date + pd.Timedelta(days=hold_period)

    sufficient_data = True
    if end_date in data.index:
        sell_price = data.loc[end_date, 'Close']
    else:
        future_data = data[data.index > end_date]
        if future_data.empty:
            sufficient_data = False
            sell_price = data.iloc[-1]['Close']
        else:
            sell_price = future_data.iloc[0]['Close']

    return_rate = (sell_price - buy_price) / buy_price
    return return_rate, first_buy_signal_date, sufficient_data




