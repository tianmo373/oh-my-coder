# P3 单元测试和文档 - 2026-04-30

## 单元测试
新增 4 个测试类，18 个新测试：

- `TestCompactResultFields` (3 tests): deduplicated_count, error_removed_count 字段
- `TestCompactStats` (4 tests): 空统计默认值、record_compact 累加、持久化
- `TestCompactSweepIntegration` (6 tests): get_latest_session, save/load roundtrip, force/since_last_user 参数, list_sessions 排序
- `TestGenerateSummaryNewFormat` (5 tests): 新摘要格式（文件读取/命令/错误/混合内容）

Commit: `87b53fd1` — 45 tests pass

## 文档
更新 `docs/guide/memory-system.md`：
- 新增「AutoCompact：自动上下文压缩」章节（压缩流程、CompactResult 字段表、配置参数、force/since_last_user）
- 新增 `omc compact stats/sweep` 命令到 CLI 命令章节

Commit: `72c9b7ed`
