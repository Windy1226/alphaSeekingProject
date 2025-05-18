# -*- coding: utf-8 -*-
import datetime
import tushare as ts
import pandas as pd
import os


def load_data_ts(ts_code: str, start_date: datetime.datetime, end_date: datetime.datetime, freq: str = "D", api_key: str = None) -> pd.DataFrame:
    """
    使用 tushare 下载指定股票在特定时间区间和频率的行情数据。
    实现本地缓存功能，避免重复下载。
    支持日线（D）、周线（W）、月线（M）。
    freq : str
        数据频率，可选值：
        - 分钟线用get_ts_data()
        - "daily" : 每日
        - "weekly" : 每周
        - "monthly" : 每月
    """
    if api_key is None:
        api_key = os.getenv("TUSHARE_API_KEY")
        if api_key is None:
            raise ValueError("需要提供tushare API key")
    
    pro = ts.pro_api(api_key)

    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_filename = f"ts_{ts_code}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{freq}.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)

    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print("从本地缓存加载数据")
            return df
        except Exception as e:
            print("加载缓存失败，准备重新下载数据:", e)

    # tushare日期格式为YYYYMMDD字符串
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')

    # tushare接口
    if freq == "daily":
        df = pro.daily(ts_code=ts_code, start_date=start_str, end_date=end_str)
    elif freq == "weekly":
        df = pro.weekly(ts_code=ts_code, start_date=start_str, end_date=end_str)
    elif freq == "monthly":
        df = pro.monthly(ts_code=ts_code, start_date=start_str, end_date=end_str)
    else:
        raise ValueError("不支持此freq")

    if df is not None and not df.empty:
        df.sort_values('trade_date', inplace=True)
        df.reset_index(drop=True, inplace=True)
    else:
        df = pd.DataFrame()

    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print("数据已保存到本地缓存")
    except Exception as e:
        print("保存缓存失败:", e)

    return df

def get_ts_data(ts_code, start_date, end_date, freq='30min', api_key: str = None): 
    """
    使用 tushare 下载指定股票在特定时间区间和频率的行情数据。
    实现本地缓存功能，避免重复下载。
    支持日线（D）、周线（W）、月线（M）。
    freq : str
        数据频率，可选值：
        - "1min" : 1分钟
        - "5min" : 5分钟
        - "15min" : 15分钟
        - "30min" : 30分钟
        - "60min" : 60分钟
    """
    
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_filename = f"ts_{ts_code}-{start_date}-{end_date}-{freq}.pkl"
    cache_path = os.path.join(cache_dir, cache_filename)

    # 尝试从本地缓存加载数据
    if os.path.exists(cache_path):
        try:
            df = pd.read_pickle(cache_path)
            print("从本地缓存加载数据")
            return df
        except Exception as e:
            print("加载缓存失败，准备重新下载数据:", e)
    
    # 设置Tushare token
    if api_key is None:
        api_key = os.getenv("TUSHARE_API_KEY")
        if api_key is None:
            raise ValueError("需要提供tushare API key")
    
    pro = ts.pro_api(api_key)

    
    # 获取数据
    df = ts.pro_bar( 
        ts_code=ts_code,  
        start_date=start_date, 
        end_date=end_date,  
        freq=freq,    
        asset='E',     
        adj='qfq',     
    )  

    if df is None or df.empty: 
        print("从 Tushare 获取的数据为空，请检查权限或参数设置。")  
        return None  

    # 创建目录（如果不存在）
    os.makedirs('./data', exist_ok=True)  

    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print("数据已保存到本地缓存")
    except Exception as e:
        print("保存缓存失败:", e)

    return df  

def standardize_ts_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化tushare下载的数据列名，统一为小写，常用字段重命名为open/high/low/close/volume。
    """
    col_map = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'vol': 'volume',
        'trade_date': 'datetime'
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df.columns = [col.lower() for col in df.columns]
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        df = df.set_index('datetime')
    return df