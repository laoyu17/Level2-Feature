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
- `add_cancel_ratio`：新增挂单量与撤单量的比值（当撤单量为 0 时记为 `0`，避免无穷大）

## 成交冲击类

- `trade_sign`：优先使用 `side`，支持 `-1/0/1`、`B/S`、`BUY/SELL`（大小写不敏感）；无法解析时回退到价格变动推断
- `trade_sign_imbalance_20`：20 事件滚动均值
- `instant_impact = abs(last_px - mid_px) / mid_px`
- `amihud_proxy = abs(log_return) / last_sz`

## 波动类

- `log_return = log(last_px / last_px.shift(1))`
- `rv_20/rv_100/rv_500`：滚动标准差乘以窗口开方

## Stream 输出约定（核心）

- Stream 输出字段与 batch 同名核心列保持一致（如 `mid_px`、`spread_abs`、`obi_l1`、`order_flow_imbalance`、`log_return`）
- 同时提供 `rv_stream` 作为向后兼容字段

## Schema 约束补充

- L2+ 深度列必须按档位完整出现（每档同时包含 `bid_px_i/bid_sz_i/ask_px_i/ask_sz_i`）
- 深度档位必须连续，不允许跳档（例如存在 L3 但缺失 L2）
