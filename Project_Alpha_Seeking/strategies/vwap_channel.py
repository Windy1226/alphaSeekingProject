

from .base_strategy import BaseStrategy
from indicators.vwap import VWAP

class VWAPChannelStrategy(BaseStrategy):
    """
    VWAP通道策略，继承BaseStrategy
    """
    params = (
        ('target_percent', 0.95),
        ('vwap_period', 20),
        ('reset_daily', False),
        ('use_typical', True),
        ('std_dev_mult', 2.0),
    )

    def __init__(self):
        super().__init__()
        self.vwap = VWAP(
            self.datas[0],
            period=self.p.vwap_period,
            reset_daily=self.p.reset_daily,
            use_typical=self.p.use_typical,
            std_dev_mult=self.p.std_dev_mult
        )

    def next(self):
        if self.order:
            return
        vwap_lower = self.vwap.vwap_lower[0]
        vwap_upper = self.vwap.vwap_upper[0]
        close = self.dataclose[0]
        self.log(f"close={close:.2f}, vwap_lower={vwap_lower:.2f}, vwap_upper={vwap_upper:.2f}, position={self.position.size}")
        if not self.position and close < vwap_lower:
            self.buy_with_sizing()
        elif self.position and close > vwap_upper:
            self.log(f"[卖出] VWAP上轨卖出: 价格={close:.2f}, VWAP上轨={vwap_upper:.2f}")
            self.order = self.sell(size=self.position.size)
        dt = self.data.datetime.date(0)
        self.value_history_dates.append(dt)
        self.value_history_values.append(self.broker.getvalue())