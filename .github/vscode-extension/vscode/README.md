# Oh My Coder - VS Code Extension

> 多智能体 AI 编程助手，支持 6 个国产大模型 + Ollama 本地模型 + 31 个智能体

## ✨ 功能特性

### 🎯 核心功能

- **快捷键调用** - 一键运行 AI 任务
  - `Ctrl+Shift+Enter` / `Cmd+Shift+Enter` - 运行选中代码的任务
  - `Ctrl+Shift+R` / `Cmd+Shift+R` - 代码审查
  - `Ctrl+Shift+O` / `Cmd+Shift+O` - 打开侧边栏面板

- **侧边栏面板** - 完整的任务管理界面
  - 任务输入和执行
  - 实时输出显示（Markdown 渲染）
  - 工作流选择
  - 模型切换

- **状态栏集成** - 显示当前任务状态
  - 就绪/运行中/错误状态
  - 点击快速打开面板

### 🤖 31 个智能体（4 大通道）

| 通道 | 智能体 | 说明 |
|------|--------|------|
| **BUILD** | Planner, Architect, Executor, Verifier, CodeSimplifier, Migration | 构建与开发 |
| **REVIEW** | CodeReviewer, SecurityReviewer, Critic, Performance | 代码审查 |
| **DEBUG** | Debugger, Tracer | 调试排错 |
| **DOMAIN** | TestEngineer, QATester, Designer, Writer, Document, Scientist, GitMaster, Explore, Vision, UML, Analyst, Database, DevOps, API, Auth, Data, Prompt, SkillManage, SelfImproving | 领域专家 |

### 🔧 工作流模板（10 个）

| 工作流 | 说明 |
|--------|------|
| **默认** | 自动选择最佳 Agent |
| **autopilot** | 自动路由：根据任务类型智能选择工作流 |
| **build** | 完整构建流程（规划 → 架构 → 编码 → 验证） |
| **review** | 代码审查（质量检查 + 安全扫描） |
| **debug** | 调试流程（问题定位 → 根因分析 → 修复） |
| **test** | 测试生成（单元测试 + 集成测试） |
| **pair** | 结对编程：人机协作开发模式 |
| **refactor** | 重构流程：分析 → 识别 → 规划 → 执行 → 验证 |
| **doc** | 文档生成：自动生成 API 文档和注释 |
| **sequential** | 顺序执行：按步骤依次完成 |
| **explore** | 代码库探索 |

### 🌐 支持的模型

#### Production 模型（6 个国产大模型）

| 模型 | 说明 |
|------|------|
| `deepseek` | DeepSeek - 高性价比编程模型 |
| `glm` | 智谱 GLM - 提供 1M tokens 免费额度 |
| `kimi` | Moonshot Kimi - 长上下文支持 |
| `doubao` | 字节豆包 - 快速响应 |
| `minimax` | MiniMax - 多模态能力 |
| `baichuan` | 百川 - 中文优化 |

#### 本地模型（Ollama）

支持通过 Ollama 运行本地模型：
- `llama3`, `mistral`, `codellama`, `deepseek-coder` 等
- 无需 API Key，完全离线运行
- 在面板中选择 "🖥️ Ollama 本地" 即可

## 📦 安装

### 从 VSIX 安装

1. 下载 `oh-my-coder-0.2.0.vsix`
2. VS Code 中按 `Ctrl+Shift+P`
3. 输入 "Extensions: Install from VSIX"
4. 选择下载的文件

### 从 Marketplace 安装（待发布）

搜索 "Oh My Coder" 并安装

## ⚙️ 配置

在 VS Code 设置中搜索 "omc"：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `omc.apiKey` | API Key | - |
| `omc.defaultModel` | 默认模型 | `deepseek` |
| `omc.autoSave` | 自动保存生成的代码 | `true` |
| `omc.showStatusBar` | 显示状态栏 | `true` |
| `omc.maxTokens` | 最大输出 Token | `4096` |
| `omc.temperature` | 生成温度 | `0.7` |

### 🔑 API Key 配置

**方式 1：VS Code 设置**
```
设置 → 搜索 "omc.apiKey" → 输入你的 API Key
```

**方式 2：环境变量**
```bash
export API_KEY=your_key_here
```

**方式 3：GLM 免费体验**
```bash
# 一行命令配置 GLM 免费模型
export OMC_DEFAULT_MODEL=glm
# GLM 提供 1M tokens 免费额度，无需信用卡
```

**方式 4：Ollama 本地模型**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull llama3

# 无需 API Key，直接使用
```

## 🚀 使用示例

### 1. 代码审查

1. 选中需要审查的代码
2. 右键 → "Oh My Coder: 代码审查"
3. 或按 `Ctrl+Shift+R`

### 2. 生成测试

1. 选中需要测试的函数/类
2. 右键 → "Oh My Coder: 生成测试"
3. 测试文件将自动创建

### 3. 调试问题

1. 选中报错的代码
2. 按 `Ctrl+Shift+Enter`
3. 输入问题描述，例如："这段代码报错 IndexError"

### 4. 使用特定 Agent

1. 打开侧边栏（`Ctrl+Shift+O`）
2. 展开 "Agents" 视图
3. 选择需要的 Agent 类型
4. 在任务面板中指定工作流

### 5. 使用 Ollama 本地模型

1. 确保 Ollama 已安装并运行
2. 打开侧边栏（`Ctrl+Shift+O`）
3. 在模型下拉菜单中选择 "🖥️ Ollama 本地"
4. 选择要使用的本地模型

## 🛠️ 开发

```bash
# 安装依赖
npm install

# 编译
npm run compile

# 监听模式
npm run watch

# 打包
npx vsce package
```

## 📝 故障排除

### 插件无法启动

1. 检查 Node.js 版本（需要 18+）
2. 确认 `omc` CLI 已安装：`pip install oh-my-coder`
3. 查看 Output 面板中的日志

### API Key 无效

1. 确认 Key 有效且未过期
2. 检查环境变量是否正确设置（使用 `API_KEY`）
3. 尝试在设置中直接配置 Key
4. 使用 GLM 免费模型测试：`omc run "hello" --model glm`
5. 使用 Ollama 本地模型，无需 API Key

### CLI 命令找不到

插件会自动查找 `omc` 命令：
- 优先使用 `which omc` / `where omc` 查找
- 回退到常见安装路径
- 最后尝试系统 PATH

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**Oh My Coder** - 让 AI 编程更简单 🚀
