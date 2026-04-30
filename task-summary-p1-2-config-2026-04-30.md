# P1-2 Error Purge 配置项 - 2026-04-30

## 变更
- 添加 `enable_purge_errors: bool = True` 构造参数
- `__init__` 新增参数及 docstring
- `_compact` 中加 guard：`if self.enable_purge_errors:` 再调用 `_purge_old_errors`

## 提交
commit 11c33fec
