# 量化策略研究与回测平台

## 项目简介

本项目是一个基于 Python 的量化交易策略开发、回测与优化平台。采用模块化架构，支持多策略、多数据源，便于扩展和维护。核心依赖包括 `pandas`、`numpy`、`backtrader`、`ta-lib`、`scikit-learn` 等，适用于股票、期货、数字货币等多品种量化研究。

## 目录结构
   ```
   Project_Alpha_Seeking/       # 量化策略项目A（主关注）
   ├── .cursorignore            # Cursor忽略规则
   ├── requirements.txt         # 依赖清单
   ├── backtest/                # 回测相关
   ├── data_processing/         # 数据处理
   ├── indicators/              # 技术指标
   ├── notebooks/               # 执行文件
   ├── plotting/                # 可视化
   ├── strategies/              # 策略实现
   ├── utils/                   # 工具函数
   └── README.md                # 项目说明
