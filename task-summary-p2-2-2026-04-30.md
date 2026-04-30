# P2-2 omc compact sweep - 2026-04-30

## 实现
- `omc compact sweep` — 强制触发最新会话压缩
- `omc compact sweep --since-last-user` — 从最后用户消息开始裁剪，再压缩
- `omc compact sweep --dry-run` — 预览结果，不实际压缩
- ShortTermMemory 新增：`list_sessions()`, `get_latest_session()`
- MemoryManager 新增：`get_latest_session()`, `save_session()`
- AutoCompact.check_and_compact 新增：`force`, `since_last_user` 参数

## 提交
commit fe4bae71
