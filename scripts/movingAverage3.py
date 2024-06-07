import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta

# 设置API密钥
api_key = '你的API密钥'

# 创建TimeSeries对象
ts = TimeSeries(key=api_key, output_format='pandas')

# 获取苹果公司的股票数据
data, meta_data = ts.get_daily(symbol='AAPL', outputsize='full')

# 重命名列
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# 转换索引为日期类型
data.index = pd.to_datetime(data.index)

# 确保索引是单调递增的
data = data.sort_index()

# 获取数据中的最新日期作为美股收盘最新一天的日期
end_date = data.index.max().strftime('%Y-%m-%d')

# 设置开始日期为一年前
start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')

print(f"Filtering data from {start_date} to {end_date}")

# 检查指定的日期范围是否在索引中
if start_date not in data.index or end_date not in data.index:
    raise ValueError(f"Date range {start_date} to {end_date} is not within the available data.")

# 过滤数据范围
filtered_data = data.loc[start_date:end_date]

# 去除缺失值（如果有）
filtered_data = filtered_data.dropna()

# 计算50天移动平均线
filtered_data['SMA50'] = filtered_data['Close'].rolling(window=50, min_periods=1).mean()

# 计算200天移动平均线
filtered_data['SMA200'] = filtered_data['Close'].rolling(window=200, min_periods=1).mean()

# 检查NaN值
print("NaN values in SMA50:")
print(filtered_data['SMA50'].isna().sum())

# 打印SMA50列中的NaN值
print("Rows with NaN values in SMA50:")
print(filtered_data[filtered_data['SMA50'].isna()])

# 检查最后几天的数据
print("Last 60 rows of data:")
print(filtered_data[['Close', 'SMA50', 'SMA200']].tail(60))

# 绘图
plt.figure(figsize=(14, 7))

# 绘制收盘价
plt.plot(filtered_data.index, filtered_data['Close'], label='Close Price', color='blue', zorder=1)

# 绘制50天移动平均线
plt.plot(filtered_data.index, filtered_data['SMA50'], label='50-Day SMA', color='red', zorder=2)

# 绘制200天移动平均线
plt.plot(filtered_data.index, filtered_data['SMA200'], label='200-Day SMA', color='green', zorder=3)

plt.title('Close Price and Moving Averages (Last 1 Year)')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.grid(True)
plt.show()
