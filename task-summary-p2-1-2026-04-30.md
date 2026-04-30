# P2-1 omc compact stats - 2026-04-30

## 实现
- MemoryManager 新增持久化统计：`compact_stats.json`
  - `total_compact_count`：压缩次数
  - `total_tokens_saved`：节省 token
  - `total_messages_removed`：清理消息数
  - `total_deduplicated`：去重 tool_call
  - `total_errors_removed`：清理错误消息
- `auto_compact_check()` 每次压缩后自动记录
- 新 CLI 命令：`omc compact stats`

## 提交
commit 5c50513c
