# P1-3-3: omc models list filter flags

## Objective
为 CLI `omc models list` 添加 `--all`、`--beta`、`--production` 过滤参数，默认只显示 production 模型。

## Key Decisions

### Import path 问题（踩坑）
- `cli_model.py` 位于 `src/cli_model.py`，需要 import `src/models/metadata.py`
- pytest 运行时 `sys.path[0] = ''`（cwd），不包含项目根目录
- 解决：在 `src/__init__.py` 顶部添加 `sys.path.insert(0, project_root)`（所有 src/* 模块加载前执行）
- 使用 `from src.models.metadata import ...` 而非 `from models.metadata`（因为 models 在 src/ 下，不在项目根目录）

### Model ID 变更
- 旧版 `SUPPORTED_MODELS` 用短 ID（deepseek/glm）
- 新版用 metadata 中的完整 ID（GLM-4-Flash/DeepSeek-V3 等）
- `switch` 命令和配置中的 default_model 改为使用完整 ID

## Files Changed
- `src/__init__.py` — sys.path 修正（+6 行）
- `src/cli_model.py` — 移除旧 SUPPORTED_MODELS，使用 metadata，重构 list/current/switch 命令（~130 行变更）
- `src/models/__init__.py` — 添加 `_load_model_metadata()` 和 `get_model_status()` 工具函数（+72 行）

## Commit
`37f51ba feat(cli): add --all/--beta/--production filters to omc models list`
