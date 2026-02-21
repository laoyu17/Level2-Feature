# 简历项目描述（中英双语，可直接粘贴）

## 中文版（适合校招/量化实习）

### 一句话版本

l2-features：面向 Level2/Tick 高频行情的数据工程与微观结构特征提取工具，支持 batch/stream 双模式与可视化回放。

### 三行版本

1. 基于 Python + Polars 构建百万级 Level2 数据特征管道，提取 OBI、盘口斜率、OFI、成交冲击、短窗实现波动等因子特征。  
2. 设计在线增量引擎（stream updater），支持逐事件特征更新，并通过 CLI 完成离线计算、回放和性能基准。  
3. 提供 PyQt6 演示界面与 CI/回归测试规范，形成“数据接入-特征计算-可视化展示-质量保障”的完整工程闭环。  

### 面试口述版本（30 秒）

这个项目的核心是把 Level2 高频数据处理做成可复用的工程能力。离线侧我用 Polars 做向量化特征计算，在线侧做了状态化的增量更新器，保证每条事件都能实时产出特征。为了让结果可演示，我又加了 PyQt6 回放界面，能直观看盘口和特征变化。项目里还配了 CI、回归测试和 benchmark，所以不只是 demo，而是一个可持续迭代的研究工具。

## English Version

### One-liner

l2-features: an open-source Level2/Tick microstructure feature toolkit with batch/stream pipelines and a replay UI for quant research workflows.

### Three bullets

- Built a high-throughput Level2 data pipeline in Python/Polars to extract microstructure signals (OBI, book slope, OFI, impact, short-horizon realized volatility).  
- Implemented a stateful stream updater for event-level incremental features, plus CLI commands for compute/replay/benchmark workflows.  
- Delivered an interview-ready PyQt6 replay dashboard and production-style engineering practices (CI, regression tests, and documentation rules).  

### Interview pitch (30s)

I treated this as an engineering-first quant research project: scalable Level2 ingestion, reproducible feature extraction, and real-time incremental updates in one toolkit. Batch features are vectorized with Polars, while stream mode maintains rolling state per symbol for low-latency updates. I also built a PyQt replay panel so the full pipeline is demonstrable end-to-end, and added CI/regression/perf checks to keep it reliable as the project grows.
