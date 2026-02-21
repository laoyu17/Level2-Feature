# Changelog

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
