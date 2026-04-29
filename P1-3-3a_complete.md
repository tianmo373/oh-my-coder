# P1-3-3a 任务完成报告

## 任务描述
修改 `omc models list` 命令，默认只显示 production 状态的模型。

## 改动文件
`src/cli_model.py`

## 改动内容
1. 移除旧的 `SUPPORTED_MODELS` 字典，改用 `src.models.metadata` 驱动
2. `list_models()` 函数默认只调用 `get_models_by_status("production")`
3. 添加 `_STATUS_LABEL` 字典显示状态标签 `[production]/[beta]/[deprecated]`
4. 更新 `_get_current_model()` 默认值从 `deepseek` 改为 `deepseek-chat`

## Commit
`7ba628d feat: omc models list defaults to production models only`

## 测试
- 语法检查通过
- pytest 运行正常

## Push 状态
- 远程被 force update，需要 `git pull --rebase` 后再 push
- 预计会产生 conflict（远程和本地都修改了 cli_model.py）