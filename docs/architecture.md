# 架构设计

## 1. 总体架构

`l2-features` 分为四层：

1. IO 层：统一读取与 schema 适配
2. Feature 层：批处理特征计算（Polars）
3. Stream 层：在线增量特征更新（Stateful）
4. Interface 层：CLI 与 PyQt6 UI

## 2. 数据流

- 批处理：`reader -> schema validate -> feature engine -> output parquet/csv`
- 流处理：`event -> StreamFeatureUpdater -> feature vector -> CLI replay/UI(stream 模式)/导出`
- UI 回放：
  - `batch-playback`：`reader -> feature engine -> UI`
  - `stream-playback`：`reader -> StreamFeatureUpdater -> UI`

## 3. 模块职责

- `schema.py`：字段约束、类型归一化、深度档位完整性校验
- `io/reader.py`：文件读取与过滤
- `features/*.py`：按特征类别拆分计算逻辑
- `stream/*.py`：状态管理与增量更新
- `cli/*`：命令行编排与参数接口
- `ui/*`：可视化展示与回放（支持 batch/stream 双模式）

## 4. 性能策略

- 批处理优先使用 Polars 向量化表达式
- 计算链统一在单次 scan/collect 中执行，减少中间拷贝
- 流式波动率使用 numba（可选）加速

## 5. 可扩展点

- 新数据源：扩展 `io/adapter.py`
- 新特征：在 `features/` 新增模块并在 `engine.py` 注册
- 新 UI 面板：在 `ui/widgets` 增加组件
