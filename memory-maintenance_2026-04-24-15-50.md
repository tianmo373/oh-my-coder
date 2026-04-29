# 任务总结：MEMORY.md 进化更新

## 目的
将今天（2026-04-24）的经验教训和项目进展整合进长期记忆，同时精简过期内容。

## 关键操作
1. **MEMORY.md 精简**：从 ~400 行压缩到 317 行
   - 合并 3 处重复的"提交前检查"清单
   - 压缩 04-08 和 04-11 的历史错误表格为简短教训
   - 去掉重复的"推荐工作流"和过期的"每日完成"详细列表
   - 合并 Python 编码规范中的冗余内容

2. **新增教训**：双 Git 仓库陷阱
   - workspace 根目录和 `projects/oh-my-coder/` 是两个独立 git 仓库
   - 根因：114 个本地 commit 从未 push 到远程
   - 规则：`projects/oh-my-coder/` 下操作必须 `cd` 到子仓库

3. **更新项目进度**：P1-3 模型元数据系统完成
   - `src/models/model_metadata.json` + `metadata.py`
   - `cli_model.py`：`--all`/`--beta` 过滤 + 状态标签
   - 桌面端 `ModelSelector.tsx`：隐藏 beta 模型

4. **新建 daily log**：`memory/2026-04-24.md`

## 当前双仓库状态（已一致）
- workspace 仓库 HEAD：`af04e52`
- oh-my-coder 子仓库 HEAD：`af04e52`
- 均指向同一远程 `github.com/VOBC/oh-my-coder.git`
