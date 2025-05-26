"""
策略工具模块

这个模块包含了不同类型的交易策略实现。
"""

import backtrader as bt

class BaseStrategy(bt.Strategy):
    """
    通用基础策略类，封装资金管理、日志、订单、交易通知等常用功能。
    子类只需实现 __init__ 和 next 即可专注于信号逻辑。
    """

    params = ()
    

    def log(self, txt, dt=None):
        """标准化日志输出，可重载为写文件等"""
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {txt}")

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.value_history_dates = []
        self.value_history_values = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"[成交] 买单执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}")
            elif order.issell():
                self.log(f"[成交] 卖单执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}")
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("[警告] 订单取消/保证金不足/拒绝")
            self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"[交易结束] 毛收益: {trade.pnl:.2f}, 净收益: {trade.pnlcomm:.2f}")

    def buy_with_sizing(self):
        """按target_percent买入，子类可重载"""
        close_price = self.dataclose[0]
        total_value = self.broker.getvalue()
        size = int((total_value * self.p.target_percent) / close_price)
        size = max(1, size)
        self.log(f"[买入] 价格={close_price:.2f}, 数量={size}")
        self.order = self.buy(size=size)

    def stop(self):
        """回测结束时输出最终市值和收益率"""
        portfolio_value = self.broker.getvalue()
        self.log(f"[回测结束] 策略最终市值: {portfolio_value:.2f}")
        starting_value = self.broker.startingcash
        roi = (portfolio_value / starting_value - 1.0) * 100
        self.log(f"[回测结束] 总收益率: {roi:.2f}%")