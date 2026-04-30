# P1-3 摘要生成改进 - 2026-04-30

## 变更
重写 `_generate_summary`：

**旧格式：**
```
省略了 4 条消息 (2 user, 2 assistant)。关键词: token, auth, jwt
```

**新格式：**
```
省略了 4 条消息（2 个文件读取, 3 个命令, 1 个错误）
```

**分类逻辑：**
- 文件读取：`read`, `read_file`, `read_file_list`
- 命令执行：`bash`, `execute`, `command`, `run_command`
- 错误：`is_error=True` 或 name/content 含 error/exception
- 搜索：`grep`, `search`, `web_search`, `find`
- 函数调用：`edit`, `write`, `write_file`, `create_file`
- 其他工具

## 提交
commit db67d058
