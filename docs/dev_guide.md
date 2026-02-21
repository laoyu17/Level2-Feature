# 开发指南

## 1. 环境准备

```bash
python -m pip install -e .[dev]
# UI 可选
python -m pip install -e .[ui]
```

## 2. 常用命令

```bash
ruff check .
pytest tests/unit -q
pytest tests/integration -q
pytest tests/integration/test_batch_stream_consistency.py -q
l2f compute --input examples/sample_data/l2_sample.csv --output outputs/features.parquet
l2f ui
```

## 3. 开发流程

1. 从 `main` 拉出 `feat/*` 或 `fix/*`
2. 先写/更新测试，再实现功能
3. 本地通过最小门禁后提交
4. PR 中描述性能影响与文档变更点

## 4. 回归策略

- 关键特征保留 snapshot 基线
- 新优化必须附带 benchmark 对比
- batch/stream 关键列做一致性校验
- UI 回放需覆盖 `batch-playback` 与 `stream-playback` 两种模式

## 5. 数据契约注意事项

- `side` 支持 `-1/0/1`、`B/S`、`BUY/SELL`，无法解析时回退为价格推断 `trade_sign`
- 深度档位必须完整且连续（每档 `bid_px_i/bid_sz_i/ask_px_i/ask_sz_i` 成组出现）
- 建议在接入新数据源后先运行：`l2f validate-schema --input <path>`
