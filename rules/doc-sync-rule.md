# 文档同步规则（Doc-Sync Rule）

> 核心原则：**改了代码就 grep 一遍文档，旧值必须清零。**

## 触发条件

以下任何操作完成后，**必须**检查文档和示例中的引用是否过时：

- 文件/目录移动或重命名
- API 签名变更（函数名、参数、返回值）
- 配置项 key 变更或路径变更
- 删除公共模块或导出
- CLI 命令/子命令/参数变更

## 检查方法

```bash
# 1. 用旧名称/旧路径 grep 整个项目（排除 .git、node_modules、dist）
grep -rn "旧路径或旧名称" . --include="*.md" --include="*.py" --include="*.ts" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.toml" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist

# 2. 检查文档目录
grep -rn "旧路径或旧名称" docs/ examples/ README.md CONTRIBUTING.md

# 3. 检查代码中的引用（import、字符串常量）
grep -rn "旧路径或旧名称" src/ --include="*.py" --exclude-dir=__pycache__
```

## 必须检查的位置

| 位置 | 容易遗漏 |
|------|----------|
| README.md | ✅ |
| CONTRIBUTING.md | ✅ |
| docs/ 目录 | ✅ |
| examples/ 目录 | ✅ |
| CI workflow (.github/) | ✅ |
| CLI help 文本（typer help） | ✅ |
| 错误信息/提示字符串 | ✅ |
| 注释中的路径引用 | ✅ |

## 反面教训

### CONTRIBUTING.md 相对路径断裂（2026-05-06）

`examples/templates/community/simple-agent/README.md` 引用 `../../../CONTRIBUTING.md`，
但 CONTRIBUTING.md 在项目根目录，需要 `../../../../CONTRIBUTING.md`。
CI lychee 链接检查报错，阻塞合并。

**根因**：移动文件后没有 grep 旧路径。

---

> **一句话总结**：重命名/移动后，`grep -rn 旧值 .`，改完才算完。
