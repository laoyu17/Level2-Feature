# Changelog

## 0.1.5 - 2026-02-21

- `l2f replay --output` 后缀校验前置：非法后缀在回放前直接失败，不再出现先打印 `Replay done` 再报错
- 强化 replay 非法后缀集成测试，新增“不进入回放主流程且不生成输出文件”的断言
- 文档补充 `l2f compute --output` 的 `.txt` 兼容语义：按 CSV 格式写出

## 0.1.4 - 2026-02-21

- `l2f replay --output` 支持 `.parquet/.csv`，并对非法后缀给出明确参数错误
- `l2f compute` 增加 `--strict-depth`：在请求深度高于数据实际深度时可选择直接失败
- `l2f compute` 输出增加深度信息（requested/detected/effective），避免静默降级歧义
- 读取主链路增加 `--canonicalize` 可选字段别名适配（compute/replay/benchmark/validate-schema）
- 补充 replay 输出格式、strict-depth、canonicalize 的单元与集成测试

## 0.1.3 - 2026-02-21

- 统一 batch/stream 的 `trade_sign` 解析契约，支持 `-1/0/1`、`B/S`、`BUY/SELL` 并在非法值时回退价格推断
- 增加深度档位完整性校验：L2+ 必须成组出现且档位连续，缺列会在 schema 校验阶段直接报错
- 对齐 `FeatureConfig.volatility_windows` 默认语义为事件窗口 `(20, 100, 500)`
- 补充 side 解析、深度缺列失败路径、batch/stream 一致性的单元与集成测试

## 0.1.2 - 2026-02-21

- 修复 `add_cancel_ratio` 在无撤单场景的数值语义，避免异常极值
- 扩展 `StreamFeatureUpdater` 输出契约，补齐与 batch 同名核心特征列并保留 `rv_stream`
- UI 回放增加 `batch-playback` / `stream-playback` 模式切换
- 新增 batch/stream 关键列一致性集成测试
- 更新架构/特征定义/开发指南与 README 说明

## 0.1.1 - 2026-02-21

- 初始化 git 并完成首提，推送到 `origin/main`
- 增加自动化演示录屏脚本 `scripts/demo_record.py`
- 生成演示产物 `assets/demo_replay.gif` 并在 README 展示
- 增加 GitHub Release 模板 `.github/release.yml`
- 增加中英双语简历项目描述 `docs/resume_project_description.md`

## 0.1.0 - 2026-02-21

- 初始化 `l2-features` 项目骨架与工程配置
- 实现 Level2 schema 校验与 IO 读取层
- 实现 batch 特征提取引擎（盘口/订单流/成交冲击/波动）
- 实现 stream 增量更新器与 replay/benchmark CLI
- 提供 PyQt6 回放 UI（盘口面板 + 特征面板）
- 增加示例数据、测试、CI 与开发规范文档
