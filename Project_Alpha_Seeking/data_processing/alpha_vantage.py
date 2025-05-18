import datetime
import pandas as pd
import os
import requests
from datetime import timedelta
import calendar


def load_data_av(ticker: str, start_date: datetime.datetime, end_date: datetime.datetime, interval: str = "5min", api_key: str = None) -> pd.DataFrame:
    """
    使用 Alpha Vantage API 下载指定股票在特定时间区间和频率的行情数据。
    实现本地缓存功能，避免重复下载。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    start_date : datetime
        开始日期
    end_date : datetime
        结束日期
    interval : str
        数据频率，可选值：
        - "1min" : 1分钟
        - "5min" : 5分钟
        - "15min" : 15分钟
        - "30min" : 30分钟
        - "60min" : 60分钟
        - "daily" : 每日
    api_key : str
        Alpha Vantage API key，如果为None则使用环境变量ALPHA_VANTAGE_API_KEY
    """
    if api_key is None:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if api_key is None:
            raise ValueError("需要提供Alpha Vantage API key")
    
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_filename = f"a v_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{interval}.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print("从本地缓存加载数据")
            return df
        except Exception as e:
            print("加载缓存失败，准备重新下载数据:", e)
    
    # 构建API URL
    function = "TIME_SERIES_INTRADAY" if interval.endswith("min") else "TIME_SERIES_DAILY"
    interval_param = interval if interval.endswith("min") else None
    
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": ticker,
        "apikey": api_key,
        "outputsize": "full"  # 获取完整数据集
    }
    if interval_param:
        params["interval"] = interval_param
    
    # 发送请求获取数据
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # 解析返回的数据
    if function == "TIME_SERIES_INTRADAY":
        time_series_key = f"Time Series ({interval})"
    else:
        time_series_key = "Time Series (Daily)"
    
    if time_series_key not in data:
        raise ValueError(f"API返回错误: {data.get('Note', data)}")
    
    # 将数据转换为DataFrame
    df = pd.DataFrame.from_dict(data[time_series_key], orient="index")
    
    # 重命名列
    column_map = {
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    }
    df.rename(columns=column_map, inplace=True)
    
    # 转换数据类型
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    
    # 设置日期索引
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    # 过滤日期范围
    df = df[start_date:end_date]
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print("数据已保存到本地缓存")
    except Exception as e:
        print("保存缓存失败:", e)
    
    return df

def load_data_month(ticker: str, month: str, interval: str = "5min", api_key: str = None) -> pd.DataFrame:
    """
    使用 Alpha Vantage API 获取指定月份的历史数据。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    month : str
        目标月份，格式为'YYYY-MM'，例如'2009-01'
    interval : str
        数据频率，可选值：
        - "1min" : 1分钟
        - "5min" : 5分钟
        - "15min" : 15分钟
        - "30min" : 30分钟
        - "60min" : 60分钟
    api_key : str
        Alpha Vantage API key，如果为None则使用环境变量ALPHA_VANTAGE_API_KEY
    
    Returns:
    --------
    pd.DataFrame
        包含该月份历史数据的DataFrame
    """
    if api_key is None:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if api_key is None:
            raise ValueError("需要提供Alpha Vantage API key")
    
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_filename = f"av_{ticker}_{month}_{interval}.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print(f"从本地缓存加载{month}的数据")
            return df
        except Exception as e:
            print(f"加载{month}缓存失败，准备重新下载数据:", e)
    
    # 构建API URL
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": interval,
        "month": month,
        "outputsize": "full",
        "apikey": api_key
    }
    
    # 发送请求获取数据
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # 解析返回的数据
    time_series_key = f"Time Series ({interval})"
    if time_series_key not in data:
        raise ValueError(f"API返回错误: {data.get('Note', data)}")
    
    # 将数据转换为DataFrame
    df = pd.DataFrame.from_dict(data[time_series_key], orient="index")
    
    # 重命名列
    column_map = {
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    }
    df.rename(columns=column_map, inplace=True)
    
    # 转换数据类型
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    
    # 设置日期索引
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print(f"{month}的数据已保存到本地缓存")
    except Exception as e:
        print(f"保存{month}缓存失败:", e)
    
    return df

def load_data_year(ticker: str, year: int, interval: str = "5min", api_key: str = None) -> pd.DataFrame:
    """
    使用 Alpha Vantage API 获取指定年份的历史数据。
    通过按月获取数据并合并来实现。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    year : int
        目标年份，例如2009
    interval : str
        数据频率，可选值：
        - "1min" : 1分钟
        - "5min" : 5分钟
        - "15min" : 15分钟
        - "30min" : 30分钟
        - "60min" : 60分钟
    api_key : str
        Alpha Vantage API key，如果为None则使用环境变量ALPHA_VANTAGE_API_KEY
    
    Returns:
    --------
    pd.DataFrame
        包含该年份所有历史数据的DataFrame
    """
    if api_key is None:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if api_key is None:
            raise ValueError("需要提供Alpha Vantage API key")
    
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    cache_filename = f"av_{ticker}_{year}_{interval}.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print(f"从本地缓存加载{year}年的数据")
            return df
        except Exception as e:
            print(f"加载{year}年缓存失败，准备重新下载数据:", e)
    
    # 获取每个月的数据
    monthly_data = []
    for month in range(1, 13):
        month_str = f"{year}-{month:02d}"
        try:
            print(f"获取{month_str}的数据...")
            df_month = load_data_month(ticker, month_str, interval, api_key)
            if not df_month.empty:
                monthly_data.append(df_month)
            # Alpha Vantage API有访问频率限制，添加延时
            import time
            time.sleep(12)  # 每分钟最多5个请求
        except Exception as e:
            print(f"获取{month_str}数据失败: {e}")
    
    # 合并所有月份的数据
    if not monthly_data:
        print(f"警告：{year}年没有获取到任何数据")
        return pd.DataFrame()
    
    df = pd.concat(monthly_data)
    df = df.sort_index()
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print(f"{year}年的数据已保存到本地缓存")
    except Exception as e:
        print(f"保存{year}年缓存失败:", e)
    
    return df 

def load_data_multi_year(ticker: str, start_year: int, end_year: int, interval: str = "5min", api_key: str = None) -> pd.DataFrame:
    """
    使用 Alpha Vantage API 获取指定年份范围内的历史数据。
    通过按年获取数据并合并来实现。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    start_year : int
        开始年份，例如2009
    end_year : int
        结束年份，例如2023
    interval : str
        数据频率，可选值：
        - "1min" : 1分钟
        - "5min" : 5分钟
        - "15min" : 15分钟
        - "30min" : 30分钟
        - "60min" : 60分钟
    api_key : str
        Alpha Vantage API key，如果为None则使用环境变量ALPHA_VANTAGE_API_KEY
    
    Returns:
    --------
    pd.DataFrame
        包含指定年份范围内所有历史数据的DataFrame
    """
    if start_year > end_year:
        raise ValueError("start_year 必须小于或等于 end_year")
    
    all_data = []
    
    for year in range(start_year, end_year + 1):
        try:
            print(f"获取 {year} 年的数据...")
            df_year = load_data_year(ticker, year, interval, api_key)
            if not df_year.empty:
                all_data.append(df_year)
            # Alpha Vantage API有访问频率限制，添加延时
            import time
            time.sleep(12)  # 每分钟最多5个请求
        except Exception as e:
            print(f"获取 {year} 年数据失败: {e}")
    
    if not all_data:
        print(f"警告：未能获取 {start_year}-{end_year} 年的数据")
        return pd.DataFrame()
    
    df = pd.concat(all_data)
    df = df.sort_index()
    
    return df
