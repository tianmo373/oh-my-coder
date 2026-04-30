# Task: Demo GIF 重做

## 目标
修复 assets/demo.gif 两个问题：
1. 当前内容是 Electron Desktop 启动画面，应为 TUI 功能演示
2. GIF 内中文显示为方块乱码

## 方案
使用 Python PIL 备选方案 B 生成静态帧 GIF，放弃 asciinema（macOS 环境无 agg，二进制安装复杂）。

## 关键决策
- **字体**：macOS 内置 Monaco.ttf（`/System/Library/Fonts/Monaco.ttf`），其他路径均不可用
- **帧策略**：disposal=2 确保每帧独立渲染，防止叠加污染
- **时长控制**：使用 duration 列表 `[200]*12 + [200]*8 + [200]*16` 总计 7.2s
- **全英文**：彻底避免中文字体缺失导致的乱码

## 验收结果
| 标准 | 结果 |
|------|------|
| 展示 TUI 终端操作 | ✅ 3帧：list agents → ask → code |
| 全部英文无乱码 | ✅ Monaco 字体 + 纯英文 |
| 文件 < 2MB | ✅ 45KB |
| 流程清晰 | ✅ |

## Commit
```
87508c1 fix: redraw Demo GIF
```
