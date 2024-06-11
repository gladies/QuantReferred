from dotenv import load_dotenv
import os
import matplotlib
matplotlib.use('Agg')

from flask import Flask, request, render_template
from markupsafe import Markup
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta

from indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_atr, calculate_williams_r, calculate_adx, filter_stocks
from utils import generate_plot

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol']
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')  # 从环境变量中读取API密钥

        if not api_key:
            return "API key is missing! Please set the ALPHA_VANTAGE_API_KEY environment variable."

        ts = TimeSeries(key=api_key, output_format='pandas')
        try:
            data, meta_data = ts.get_daily(symbol=stock_symbol, outputsize='full')
        except Exception as e:
            return f"Error fetching data: {e}"

        if data.empty:
            return "No data found for the given stock symbol."

        data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        end_date = data.index.max().strftime('%Y-%m-%d')
        start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')

        filtered_data = data.loc[start_date:end_date].dropna()

        filtered_data['SMA50'] = filtered_data['Close'].rolling(window=50, min_periods=1).mean()
        filtered_data['SMA200'] = filtered_data['Close'].rolling(window=200, min_periods=1).mean()
        filtered_data['RSI'] = calculate_rsi(filtered_data, 14)
        filtered_data['MACD'], filtered_data['Signal'] = calculate_macd(filtered_data)
        filtered_data['Middle Band'], filtered_data['Upper Band'], filtered_data['Lower Band'] = calculate_bollinger_bands(filtered_data, 20, 2)
        filtered_data['ATR'] = calculate_atr(filtered_data, 14)
        filtered_data['Williams %R'] = calculate_williams_r(filtered_data, 14)
        filtered_data['ADX'] = calculate_adx(filtered_data, 14)

        # 计算买入信号：当50日均线向上穿过200日均线时
        filtered_data['Buy Signal'] = np.where(filtered_data['SMA50'] > filtered_data['SMA200'], 'Buy', '')

        # 数据倒序排列
        filtered_data = filtered_data.iloc[::-1]

        # 将买入信号高亮显示
        def highlight_buy(val):
            color = 'yellow' if val == 'Buy' else ''
            return f'background-color: {color}'

        try:
            styled_data = filtered_data.style.applymap(highlight_buy, subset=['Buy Signal'])
            data_html = styled_data.to_html()
        except Exception as e:
            return f"Error in styling data: {e}"

        plot_url = generate_plot(filtered_data, stock_symbol)

        return render_template('index.html', plot_url=plot_url, data=Markup(data_html))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)



