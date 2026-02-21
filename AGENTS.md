# AGENTS.md - Level2-Feature 项目执行规范

## 1. 项目信息

- 项目名称：`Level2-Feature`
- GitHub 仓库：`https://github.com/laoyu17/Level2-Feature.git`
- 默认分支：`main`
- 主要开发分支：`feat/*`、`fix/*`

## 2. 开发原则

- 保持向后兼容，非必要不破坏 CLI 参数和输出列
- 先补测试再改行为，确保 batch/stream 行为一致
- 代码优先可维护性：函数单一职责，避免隐式状态

## 3. 提交规范（Conventional Commits）

允许前缀：

- `feat:` 新功能
- `fix:` 缺陷修复
- `perf:` 性能优化
- `refactor:` 重构（无行为变化）
- `test:` 测试相关
- `docs:` 文档更新
- `chore:` 工程杂项

示例：

- `feat(features): add L10 order book imbalance`
- `perf(stream): speed up rolling rv update`

## 4. 每次开发的测试与回归要求

### 4.1 Commit 前（最小门禁，必须通过）

1. `ruff check .`
2. `pytest tests/unit -q`
3. `pytest tests/integration/test_cli_compute.py -q`

### 4.2 PR 合并前（完整门禁，必须通过）

1. `pytest -q`
2. 回归快照：`tests/regression` 全通过
3. 性能烟测：`tests/perf` 不低于基线阈值（默认 -10%）
4. 文档校验：README 命令可运行、路径与参数一致

## 5. 文档更新要求

出现下列变化必须同步更新文档：

- 新特征或公式变化：更新 `docs/feature_definitions.md`
- CLI 参数变化：更新 `README.md` 与 `README_EN.md`
- 架构变化：更新 `docs/architecture.md`
- 用户可感知行为变化：更新 `docs/changelog.md`

## 6. 数据与合规

- 默认仅使用公开样例和模拟数据
- 私有行情接入必须通过适配层并完成脱敏
- 禁止提交密钥、账号、许可证文件等敏感信息
