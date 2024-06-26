import os
import json
from datetime import timedelta, datetime
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
from indicators.indicators_manager import IndicatorsManager
from utils import fetch_data_with_retry, fetch_data_from_file, generate_plot, style_data
from markupsafe import Markup
import pandas as pd
from mock_api import fetch_data_mock, fetch_data_real, save_data_to_mock

load_dotenv()

app = Flask(__name__)

@app.template_filter('percentage')
def percentage_filter(value):
    if value is None:
        return "N/A"
    return "{:.2%}".format(value)

@app.route('/')
def index():
    print("Redirecting to /referred_stocks")
    return redirect(url_for('referred_stocks'))

@app.route('/referred_stocks', methods=['GET', 'POST'])
def referred_stocks():
    print("Entering referred_stocks route")
    buy_signals = []
    sell_signals = []
    if request.method == 'POST':
        data_source = request.form.get('data_source')
        stocks_list = request.form.get('stocks_list')
        buy_threshold = request.form.get('buy_threshold')
        sell_threshold = request.form.get('sell_threshold')

        print(f"POST request received with data_source: {data_source}, stocks_list: {stocks_list}, buy_threshold: {buy_threshold}, sell_threshold: {sell_threshold}")

        if not data_source or not stocks_list or not buy_threshold or not sell_threshold:
            print("Missing data source, stocks list, buy threshold, or sell threshold in the request.")
            return "Missing data source, stocks list, buy threshold, or sell threshold in the request."

        buy_threshold = float(buy_threshold)
        sell_threshold = float(sell_threshold)
        stocks_list = json.loads(stocks_list).get("stocks", [])
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

        all_stock_data = {}
        for stock_symbol in stocks_list:
            if data_source == 'mock':
                stock_data = fetch_data_mock(stock_symbol)
                if stock_data is None:
                    print(f"No mock data found for {stock_symbol}, fetching real data...")
                    stock_data = fetch_data_real(stock_symbol, api_key)
                    if stock_data is not None and not stock_data.empty:
                        save_data_to_mock(stock_symbol, stock_data.to_dict())
                        print(f"Saved real data to mock for {stock_symbol}")
                if stock_data is not None:
                    print(f"Fetched data for {stock_symbol}: {stock_data.head()}")
            else:
                stock_data = fetch_data_real(stock_symbol, api_key)
                if stock_data is not None:
                    print(f"Fetched real data for {stock_symbol}: {stock_data.head()}")

            if stock_data is None or stock_data.empty:
                continue

            stock_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            stock_data = stock_data.sort_index()

            print(f"Processing data for {stock_symbol}")
            end_date = stock_data.index.max().strftime('%Y-%m-%d')
            start_date = (stock_data.index.max() - timedelta(days=365)).strftime('%Y-%m-%d')
            filtered_data = stock_data.loc[start_date:end_date].copy()

            print(f"Filtered data for {stock_symbol}: {filtered_data.head()}")
            manager = IndicatorsManager(filtered_data, buy_threshold, sell_threshold, use_latest_only=True)
            filtered_data = manager.calculate_signals()

            print(f"Calculated signals for {stock_symbol}: {filtered_data[['Buy Signal', 'Sell Signal']].tail()}")

            if filtered_data['Buy Signal'].iloc[-1]:
                buy_signals.append(stock_symbol)
            if filtered_data['Sell Signal'].iloc[-1]:
                sell_signals.append(stock_symbol)

            print(f"Processed data for {stock_symbol}: Buy Signals: {buy_signals}, Sell Signals: {sell_signals}")

    print(f"Rendering template with buy_signals: {buy_signals}, sell_signals: {sell_signals}")
    return render_template('referred_stocks.html', buy_signals=buy_signals, sell_signals=sell_signals)

@app.route('/stock_analysis', methods=['GET', 'POST'])
def stock_analysis():
    print("Entering stock_analysis route")
    plot_url = None
    data_html = None
    return_rate = None
    backtest_msg = None
    insufficient_data = False
    first_buy_signal_date = None
    buy_signals = []
    sell_signals = []
    hold_period = None  # 初始化 hold_period

    if request.method == 'POST':
        stock_symbol = request.form.get('stock_symbol')
        hold_period = request.form.get('hold_period')
        buy_threshold = request.form.get('buy_threshold')
        sell_threshold = request.form.get('sell_threshold')

        print(f"POST request received with stock_symbol: {stock_symbol}, hold_period: {hold_period}, buy_threshold: {buy_threshold}, sell_threshold: {sell_threshold}")

        if not stock_symbol or not hold_period or not buy_threshold or not sell_threshold:
            print("Missing stock symbol, hold period, buy threshold, or sell threshold in the request.")
            return "Missing stock symbol, hold period, buy threshold, or sell threshold in the request."

        hold_period = int(hold_period)
        buy_threshold = float(buy_threshold)
        sell_threshold = float(sell_threshold)
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

        if not api_key:
            print("API key is missing! Please set the ALPHA_VANTAGE_API_KEY environment variable.")
            return "API key is missing! Please set the ALPHA_VANTAGE_API_KEY environment variable."

        data, meta_data = fetch_data_with_retry(stock_symbol, api_key)
        print(f"Fetched data for {stock_symbol}: {data.head() if data is not None else 'No data'}")

        if data is None:
            print("Failed to fetch data after multiple retries.")
            return "Failed to fetch data after multiple retries."

        if data.empty:
            print("No data found for the given stock symbol.")
            return "No data found for the given stock symbol."

        data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        end_date = data.index.max().strftime('%Y-%m-%d')
        start_date = (data.index.max() - timedelta(days=365)).strftime('%Y-%m-%d')
        filtered_data = data.loc[start_date:end_date].copy()

        manager = IndicatorsManager(filtered_data, buy_threshold, sell_threshold, use_latest_only=False)
        filtered_data = manager.calculate_signals()

        return_rate, first_buy_signal_date, sufficient_data = manager.backtest_strategy_multiple_signals(hold_period)
        print(f"Backtest result: Return Rate: {return_rate}, First Buy Signal Date: {first_buy_signal_date}, Sufficient Data: {sufficient_data}")

        if return_rate is not None:
            backtest_msg = f"Backtest result: Buying on the first buy signal and holding for {hold_period} days results in an average return of {return_rate:.2%}."
            if first_buy_signal_date:
                backtest_msg += f"<br>First buy signal date: {first_buy_signal_date.strftime('%Y-%m-%d')}"
            if not sufficient_data:
                insufficient_data = True
        else:
            backtest_msg = "Backtest result: No valid buy signals found or insufficient data for the holding period."

        plot_url = generate_plot(filtered_data, stock_symbol)

        recent_90_days_data = filtered_data.tail(90).sort_index(ascending=False)
        styled_data = recent_90_days_data.style.apply(
            lambda x: ['background-color: yellow' if isinstance(val, (int, float)) and val >= buy_threshold else '' for val in x],
            subset=['Buy Signal']
        )
        styled_data = styled_data.apply(
            lambda x: ['background-color: red' if val > 0 else '' for val in x],
            subset=['Sell Signal']
        )
        styled_data = styled_data.apply(
            lambda x: [style_data(val, col) for val, col in zip(x, x.index)],
            axis=1, subset=['RSI', 'Williams %R', 'ADX']
        )
        data_html = styled_data.to_html()

    print(f"Rendering template with plot_url: {plot_url}, return_rate: {return_rate}, backtest_msg: {backtest_msg}, insufficient_data: {insufficient_data}")
    return render_template('stock_analysis.html', plot_url=plot_url, data_html=Markup(data_html), return_rate=return_rate, backtest_msg=backtest_msg, insufficient_data=insufficient_data, hold_period=hold_period, buy_signals=buy_signals, sell_signals=sell_signals)

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True, port=5000)
    print("Flask application has started.")
