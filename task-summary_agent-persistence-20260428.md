# Agent 状态持久化实现

## 目标
实现 Agent 会话状态持久化，保存/恢复 Agent 上下文到本地存储 `~/.oh-my-coder/agents/`

## 完成内容

### 1. 核心模块
- **`src/agents/persistence/store.py`** — AgentStateStore 类
  - `save()`: 保存 config.json + history.jsonl + state.json
  - `restore()`: 从磁盘恢复 Agent 状态
  - `export_agent()`: 打包为单 JSON 文件（可分享）
  - `import_agent()`: 从 JSON 导入
  - `list_saved()`, `delete()`, `get_stats()`

### 2. CLI 子命令（omc agent）
- `save <name>` — 保存 Agent 到 ~/.oh-my-coder/agents/<name>/
- `restore <name>` — 从磁盘恢复
- `export <name> <file>` — 导出为 JSON
- `import <file>` — 从 JSON 导入
- `list-saved` — 列出所有已保存 Agent
- `delete-saved <name>` — 删除已保存状态

### 3. 测试
- **`tests/test_agent_persistence.py`** — 18 个测试全部通过
- 覆盖：配置/历史/状态 保存恢复、追加模式、导出导入、重命名、统计

## 目录结构
```
~/.oh-my-coder/agents/<agent_name>/
├── config.json       # Agent 配置快照
├── history.jsonl     # 对话历史（append-only）
└── state.json        # 运行时状态（tokens, cost, session_id）
```

## 验证命令
```bash
# 保存
python3 -m src.cli_agent save planner -m deepseek -d "规划 Agent"

# 恢复
python3 -m src.cli_agent restore planner

# 导出
python3 -m src.cli_agent export planner planner-backup.json

# 导入
python3 -m src.cli_agent import planner-backup.json -n planner-new

# 列出
python3 -m src.cli_agent list-saved
```

## 下一步建议
1. 在 Orchestrator 中集成自动保存（workflow 结束时调用）
2. 添加 `--checkpoint` 参数支持断点续传
3. 支持压缩旧历史文件（gzip）
