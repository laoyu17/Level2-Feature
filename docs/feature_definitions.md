# 特征定义（MVP）

## 盘口类

- `spread_abs = ask_px_1 - bid_px_1`
- `spread_bps = spread_abs / bid_px_1`
- `mid_px = (ask_px_1 + bid_px_1) / 2`
- `obi_l1 = (bid_sz_1 - ask_sz_1) / (bid_sz_1 + ask_sz_1)`
- `obi_l5/obi_l10`：对应档位深度不平衡
- `microprice = (ask_px_1*bid_sz_1 + bid_px_1*ask_sz_1)/(bid_sz_1+ask_sz_1)`
- `book_slope`：盘口价格相对顶档的深度加权斜率

## 订单流类

- `order_flow_imbalance`：基于 bid/ask 价格与挂单量变化的 OFI 近似
- `cancel_intensity`：撤单量占前一时刻挂单总量比例
- `add_cancel_ratio`：新增挂单量与撤单量的比值

## 成交冲击类

- `trade_sign`：来自 side 或由价格变动推断
- `trade_sign_imbalance_20`：20 事件滚动均值
- `instant_impact = abs(last_px - mid_px) / mid_px`
- `amihud_proxy = abs(log_return) / last_sz`

## 波动类

- `log_return = log(last_px / last_px.shift(1))`
- `rv_20/rv_100/rv_500`：滚动标准差乘以窗口开方
