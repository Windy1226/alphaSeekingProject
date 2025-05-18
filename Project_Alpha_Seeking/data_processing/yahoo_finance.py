import datetime
import yfinance as yf
import pandas as pd
import os
import requests
from datetime import timedelta
import calendar

def load_data_yf(ticker: str, start_date: datetime.datetime, end_date: datetime.datetime, interval: str = "5m") -> pd.DataFrame:
    """
    使用 yfinance 下载指定股票在特定时间区间和频率的行情数据。
    实现本地缓存功能，避免重复下载；若数据频率为 5m 且时间范围超过 30 天，
    则分段下载（每次最多 30 天）后合并数据并按日期排序返回。
    """
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_filename = f"yf_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{interval}.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print("从本地缓存加载数据")
            return df
        except Exception as e:
            print("加载缓存失败，准备重新下载数据:", e)
    
    # 如果缓存不存在或加载失败，则从 yf 下载数据
    if interval == "5m":
        max_days = 30
        data_chunks = []
        current_start = start_date
        while current_start < end_date:
            current_end = current_start + timedelta(days=max_days)
            if current_end > end_date:
                current_end = end_date
            print(f"下载数据段: {current_start.strftime('%Y-%m-%d')} 到 {current_end.strftime('%Y-%m-%d')}")
            df_chunk = yf.download(
                tickers=ticker,
                start=current_start.strftime('%Y-%m-%d'),
                end=current_end.strftime('%Y-%m-%d'),
                interval=interval
            )
            if not df_chunk.empty:
                data_chunks.append(df_chunk)
            current_start = current_end
        if data_chunks:
            df = pd.concat(data_chunks)
            df.sort_index(inplace=True)
        else:
            df = pd.DataFrame()
    else:
        # 如果不是 5m 频率，则直接下载
        df = yf.download(
            tickers=ticker,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval=interval
        )
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print("数据已保存到本地缓存")
    except Exception as e:
        print("保存缓存失败:", e)
    
    return df


def flatten_yf_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    将 yfinance 下载的数据 DataFrame 列索引进行扁平化处理，并统一为小写格式。
    支持单只或多只股票的数据格式。
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join(tuple(filter(None, col))).lower()
            for col in df.columns.values
        ]
    else:
        df.columns = [col.lower() for col in df.columns]
    return df

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    如果除日期外的所有列都以相同后缀结尾（例如 _aapl），则去除后缀，
    保留 open、high、low、close、volume 等标准字段名称。
    """
    # 保证日期列名称为 "datetime"
    if "datetime" not in df.columns and "date" in df.columns:
        df.rename(columns={"date": "datetime"}, inplace=True)

    # 对非日期列，如果存在下划线，则取下划线前部分
    new_cols = {}
    for col in df.columns:
        if col != "datetime" and "_" in col:
            new_cols[col] = col.split("_")[0]
    if new_cols:
        df.rename(columns=new_cols, inplace=True)

    return df


def load_data_yf_month(ticker: str, year: int, month: int) -> pd.DataFrame:
    """
    使用 yfinance 下载指定月份的日线数据。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    year : int
        年份，例如2023
    month : int
        月份（1-12）
    
    Returns:
    --------
    pd.DataFrame
        包含该月份日线数据的DataFrame，包含以下列：
        - Open: 开盘价
        - High: 最高价
        - Low: 最低价
        - Close: 收盘价
        - Volume: 成交量
        - Dividends: 分红
        - Stock Splits: 股票拆分
    """
    # 参数验证
    if not 1 <= month <= 12:
        raise ValueError("月份必须在1-12之间")
    
    # 计算月份的起止日期
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)
    
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_filename = f"yf_{ticker}_{year}{month:02d}_1d.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print(f"从本地缓存加载{year}年{month}月的数据")
            return df
        except Exception as e:
            print(f"加载{year}年{month}月缓存失败，准备重新下载数据:", e)
    
    # 下载数据
    print(f"下载{year}年{month}月的数据...")
    df = yf.download(
        tickers=ticker,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1d'  # 日线数据
    )
    
    if df.empty:
        print(f"警告：{year}年{month}月没有数据")
        return df
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print(f"{year}年{month}月的数据已保存到本地缓存")
    except Exception as e:
        print(f"保存{year}年{month}月缓存失败:", e)
    
    return df

def load_data_yf_year(ticker: str, year: int) -> pd.DataFrame:
    """
    使用 yfinance 下载指定年份的日线数据。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    year : int
        年份，例如2023
    
    Returns:
    --------
    pd.DataFrame
        包含该年份所有日线数据的DataFrame
    """
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    cache_filename = f"yf_{ticker}_{year}_1d.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print(f"从本地缓存加载{year}年的数据")
            return df
        except Exception as e:
            print(f"加载{year}年缓存失败，准备重新下载数据:", e)
    
    # 设置年份的起止日期
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year + 1, 1, 1)
    
    # 直接下载整年数据
    print(f"下载{year}年的数据...")
    df = yf.download(
        tickers=ticker,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1d'  # 日线数据
    )
    
    if df.empty:
        print(f"警告：{year}年没有数据")
        return df
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print(f"{year}年的数据已保存到本地缓存")
    except Exception as e:
        print(f"保存{year}年缓存失败:", e)
    
    return df

def load_data_yf_years(ticker: str, start_year: int, end_year: int) -> pd.DataFrame:
    """
    使用 yfinance 下载指定年份范围的日线数据。
    
    Parameters:
    -----------
    ticker : str
        股票代码
    start_year : int
        起始年份，例如2020
    end_year : int
        结束年份，例如2023
    
    Returns:
    --------
    pd.DataFrame
        包含指定年份范围内所有日线数据的DataFrame
    """
    if start_year > end_year:
        raise ValueError("start_year必须小于或等于end_year")
    
    # 定义缓存目录和缓存文件名
    cache_dir = "cache"
    cache_filename = f"yf_{ticker}_{start_year}_{end_year}_1d.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)
    
    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print(f"从本地缓存加载{start_year}-{end_year}年的数据")
            return df
        except Exception as e:
            print(f"加载{start_year}-{end_year}年缓存失败，准备重新下载数据:", e)
    
    # 设置日期范围
    start_date = datetime.datetime(start_year, 1, 1)
    end_date = datetime.datetime(end_year + 1, 1, 1)
    
    # 直接下载多年数据
    print(f"下载{start_year}-{end_year}年的数据...")
    df = yf.download(
        tickers=ticker,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1d',  # 日线数据
        auto_adjust=True
    )
    
    if df.empty:
        print(f"警告：{start_year}-{end_year}年没有数据")
        return df
    
    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print(f"{start_year}-{end_year}年的数据已保存到本地缓存")
    except Exception as e:
        print(f"保存{start_year}-{end_year}年缓存失败:", e)
    
    return df
