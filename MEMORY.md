# MEMORY.md - 长期记忆

> 最后更新：2026-04-29

---

## 🛡️ CI/CD 经验教训（核心能力）

### 核心原则：本地验证 ≠ CI 通过

CI 是干净环境，本地有缓存/残留配置。本地测试通过不代表 CI 一定通过。

### 提交前必须运行的完整检查

```bash
python3 -m pytest tests/ -q          # 1. 测试通过
python3 -m ruff check src/ tests/    # 2. 无 lint 错误
python3 -m black src/ tests/        # 3. 全量格式化
git status                           # 4. 确认所有更改已暂存
```

### 推荐工作流

```
写代码 → ruff --fix → black → pytest → 提交 → push
```

### 常见 CI 问题模式

| 问题类型 | 本地行为 | CI 行为 | 解决方案 |
|----------|----------|---------|----------|
| Typer exit_code | 返回 0 | 返回 2 | 测试输出内容而非 exit_code |
| shell 解析 | `[dev]` 正常 | 被解析为通配符 | 加引号 `'.[dev]'` |
| 路径格式 | macOS 路径 | Linux 路径 | 使用 `Path(__file__).parent` |
| 硬编码路径 | 正常 | 找不到文件 | 禁止硬编码任何用户名/绝对路径 |
| node_modules symlink | git 正常 | cp -r 报错 | 不要提交 node_modules（废料桶中的 4275 文件） |

---

## 🐍 Python 编码规范

### Python 3.9 兼容性

```python
# ❌ 错误
def foo(x: Path | str) -> ModuleInfo | None:
    pass

# ✅ 正确
from typing import Union, Optional
def foo(x: Union[Path, str]) -> Optional[ModuleInfo]:
    pass
```

### f-string

```python
# ❌ 错误 - 没有占位符
print(f"  [dim]使用 [green]-y[/dim] 自动确认[/dim]")
# ✅ 正确
print("  [dim]使用 [green]-y[/dim] 自动确认[/dim]")
```

### 路径处理
- 永远使用 `pathlib.Path`，禁止硬编码绝对路径
- 动态获取路径：`Path(__file__).parent`

### ast 模块

```python
# ❌ ast 节点没有 parent 属性
# ✅ 手动维护父子关系
def walk_with_parent(tree, parent=None):
    for node in ast.iter_child_nodes(parent or tree):
        yield node, parent
        yield from walk_with_parent(node, node)
```

### 导入规范
- 所有导入放顶部，不在函数内部 import-as-local（否则 CI ruff F821）
- 导入时想清楚在哪用，没用就不导（不留下 F401）

---

## 🧪 本周教训精选（4/24 - 4/29）

### 1. 双 Git 仓库陷阱（4/24）
workspace 根目录和 `projects/oh-my-coder/` 是两个独立的 git 仓库指向同一远程。
- **问题**：在根目录 commit 了子仓库内的文件，子仓库不感知
- **方案**：修改 `projects/oh-my-coder/` 下文件时，先 `cd` 到该目录再操作

### 2. 移动文件后必须检查所有引用（4/29）
P27 把 `install.sh` 移到 `scripts/` 后，CI 报错。
- **检查清单**：CI workflow（install-test.yml）、文档、内部脚本引用、dockerfile
- 漏一个 CI 就红

### 3. ShellCheck 全量通过才绿（4/29）
`ludeeus/action-shellcheck@master` 把 warning 和 note 都视为错误（exit 1）。
- 常见修复模式：SC2034（删未用变量）、SC2227（重定向位置）、SC1091（加 source directive）、SC2162（read -r）、SC2086（双引号）、SC2126（grep -c）

### 4. ruff.toml 优先级高于 pyproject.toml（4/27）
同时存在 `ruff.toml` 和 `pyproject.toml` 时，ruff 只读前者。
- **修复前**：改了 pyproject.toml 的 ruff 配置，CI 仍报 100 个错

### 5. 时间戳取模不保证唯一（4/27）
`cp_id = f"{ts}-{ts_ms:03d}-{task_id}"` → CI 环境同一毫秒执行两次 → cp_id 相同
- **修复**：自增计数器替代毫秒取模

### 6. Desktop 端 — 必须有 fallback（4/26）
`window.omc` API 在 Vite dev 模式不存在，API 返回 undefined 时组件报错。
- **规则**：所有桌面端 UI 组件必须提供 fallback 数据，不要假设 API 可用

### 7. chrome CDP port 每次重启都会变（4/26）
Chrome 重启后 `--remote-debugging-port=9222` 不一定保持同一端口。
- 测试前需确保 Chrome 在正确端口运行

---

## 📅 项目进度

**oh-my-coder** (CLI): https://github.com/VOBC/oh-my-coder
- **测试**: 500+ passed
- **近期完成**：P27 根目录整理、ShellCheck 全绿、Desktop P1-1~P1-4

**桌面端** (oh-my-coder/desktop):
- 可运行 .app，18 个模型，完整 UI

### 待完成任务
- 桌面端：应用图标 / Apple 签名 / notarization
- omc CLI：P2-1 自动测试增强、P2-2 成本优化建议（`omc cost` CLI）
