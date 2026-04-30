# P1-2 Error Purge 实现总结

## 目标
借鉴 DCP 优化 AutoCompact，添加历史错误消息清理功能（purgeErrors）。

## 实现

### 新增方法
1. `_is_error_message(msg)` - 检测消息是否为错误类型
   - 检查 metadata.is_error=True
   - 检查 name 包含 error/exception/fail/err
   - 检查 content 包含 Error:/Traceback/Exception: 等关键词
   - 仅对 tool role 消息生效

2. `_purge_old_errors(messages, max_age_rounds=4)` - 清理历史错误
   - 按回合分组（每 user 消息算 1 回合）
   - 超过 max_age_rounds 的旧回合：删除所有 error，保留最后 1 条
   - 需保留的回合（keep rounds）：全部保留
   - 返回 (清理后的消息, 被清理的 error 数)

### CompactResult 新字段
- `error_removed_count: int = 0` - 清理的历史 error 消息数

### 集成流程
```
1. 去重 (_deduplicate_tool_calls)
2. 错误清理 (_purge_old_errors)  
3. 分片 (recent 20% + to_compress)
4. 生成摘要
```

### 摘要标记
- `[已清理 N 个历史错误]` - 当 error_count > 0 时追加

## 测试
- 8 个专项测试：TestAutoCompactErrorPurge 类
- 全部 27 个 auto_compact 测试通过

## 提交
- commit 8192ea7d
- 文件：src/memory/auto_compact.py, tests/test_auto_compact.py