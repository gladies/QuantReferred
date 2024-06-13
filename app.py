import os
from datetime import datetime, timedelta
from flask import Flask, request, render_template
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
from indicators import calculate_buy_signals
from utils import generate_plot, backtest_strategy
from markupsafe import Markup
import pandas as pd

load_dotenv()

app = Flask(__name__)

def fetch_data_with_retry(symbol, api_key, retries=3):
    ts = TimeSeries(key=api_key, output_format='pandas')
    for _ in range(retries):
        try:
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')
            return data, meta_data
        except Exception as e:
            print(f"Error fetching data: {e}")
    return None, None

@app.template_filter('percentage')
def percentage_filter(value):
    if value is None:
        return "N/A"
    return "{:.2%}".format(value)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = None
    data_html = None
    return_rate = None
    backtest_msg = None
    insufficient_data = False
    first_buy_signal_date = None
    hold_period = None

    if request.method == 'POST':
        stock_symbol = request.form.get('stock_symbol')
        hold_period = request.form.get('hold_period')
        threshold = request.form.get('threshold')

        if not stock_symbol or not hold_period or not threshold:
            return "Missing stock symbol, hold period, or threshold in the request."

        hold_period = int(hold_period)
        threshold = float(threshold)
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

        if not api_key:
            return "API key is missing! Please set the ALPHA_VANTAGE_API_KEY environment variable."

        data, meta_data = fetch_data_with_retry(stock_symbol, api_key)

        if data is None:
            return "Failed to fetch data after multiple retries."

        if data.empty:
            return "No data found for the given stock symbol."

        data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        end_date = data.index.max().strftime('%Y-%m-%d')
        start_date = (data.index.max() - timedelta(days=365)).strftime('%Y-%m-%d')
        filtered_data = data.loc[start_date:end_date].copy()

        filtered_data = calculate_buy_signals(filtered_data, threshold)

        return_rate, first_buy_signal_date, sufficient_data = backtest_strategy(filtered_data, hold_period)
        if return_rate is not None:
            backtest_msg = f"Backtest result: Buying on the first buy signal and holding for {hold_period} days results in a return of {return_rate:.2%}."
            if first_buy_signal_date:
                backtest_msg += f"<br>First buy signal date: {first_buy_signal_date.strftime('%Y-%m-%d')}"
            if not sufficient_data:
                insufficient_data = True
        else:
            backtest_msg = "Backtest result: No valid buy signals found or insufficient data for the holding period."

        plot_url = generate_plot(filtered_data, stock_symbol)

        recent_90_days_data = filtered_data.tail(90).sort_index(ascending=False)
        styled_data = recent_90_days_data.style.applymap(lambda x: 'background-color: yellow' if isinstance(x, (int, float)) and x >= threshold else '', subset=['Buy Signal'])
        data_html = styled_data.to_html()

    return render_template('index.html', plot_url=plot_url, data_html=Markup(data_html), return_rate=return_rate, backtest_msg=backtest_msg, insufficient_data=insufficient_data, hold_period=hold_period)

if __name__ == '__main__':
    app.run(debug=True)








