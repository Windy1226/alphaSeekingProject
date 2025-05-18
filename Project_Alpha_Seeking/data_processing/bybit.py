import time
import pandas as pd
import requests
from datetime import datetime
import os

def load_data_bybit(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d",
    category: str = "linear",
) -> pd.DataFrame:
    
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

    if not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.max.time())

    interval_map = {"1d": "D", "240": "240", "60": "60", "30": "30", "15": "15", "5": "5", "1": "1"}
    if interval not in interval_map:
        raise ValueError(f"不支持的interval: {interval}")
    bybit_interval = interval_map[interval]

    url = "https://api.bybit.com/v5/market/kline"
    limit = 1000
    all_data = []
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    cur_end = end_ms

    while cur_end > start_ms:
        params = {
            "category": category,
            "symbol": symbol,
            "interval": bybit_interval,
            "start": start_ms,
            "end": cur_end,
            "limit": limit
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        klines = data.get("result", {}).get("list", [])
        if not klines:
            break
        # 按时间升序
        klines = sorted(klines, key=lambda x: int(x[0]))
        all_data.extend(klines)
        # 用本批次最早K线的时间戳推进
        earliest_ts = int(klines[0][0])
        if earliest_ts <= start_ms:
            break
        cur_end = earliest_ts - 1
        if len(klines) < limit:
            break
        time.sleep(0.2)

    if not all_data:
        raise ValueError("未获取到任何K线数据")

    df = pd.DataFrame(all_data, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df["datetime"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
    df = df.sort_values("datetime").drop_duplicates("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[["datetime", "open", "high", "low", "close", "volume"]]
    df = df[(df["datetime"] >= start_date) & (df["datetime"] <= end_date)]

    # 保存数据到本地缓存
    try:
        df.to_pickle(cache_path)
        print("数据已保存到本地缓存")
    except Exception as e:
        print("保存缓存失败:", e)

    return df