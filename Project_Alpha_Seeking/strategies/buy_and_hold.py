

from .base_strategy import BaseStrategy

class BuyAndHoldStrategy(BaseStrategy):
    """
    简单买入并持有策略，继承BaseStrategy
    """
    print("BaseStrategy.params type:", type(BaseStrategy.params))
    params = (
    # --- 资金管理 ---
    ('target_percent', 0.95),    # 默认使用95%的资金买入
    )
    def next(self):
        if self.order:
            return
        if not self.position:
            self.buy_with_sizing()
        dt = self.data.datetime.date(0)
        self.value_history_dates.append(dt)
        self.value_history_values.append(self.broker.getvalue())