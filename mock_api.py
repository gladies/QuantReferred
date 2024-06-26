import json
import pandas as pd

def fetch_data_mock(stock_symbol):
    try:
        with open('old_data.json', 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return None

    stock_data = data.get(stock_symbol, None)
    if stock_data:
        df = pd.DataFrame.from_dict(stock_data, orient='index')
        df.index = pd.to_datetime(df.index)
        return df
    return None

def fetch_data_real(stock_symbol, api_key):
    from alpha_vantage.timeseries import TimeSeries
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, _ = ts.get_daily(symbol=stock_symbol, outputsize='full')
    return data

def save_data_to_mock(stock_symbol, data):
    try:
        with open('old_data.json', 'r') as file:
            existing_data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        existing_data = {}

    existing_data[stock_symbol] = data

    with open('old_data.json', 'w') as file:
        json.dump(existing_data, file, indent=4, default=str)
