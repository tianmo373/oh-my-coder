# Self-Improving Memory

## Confirmed Preferences
<!-- Patterns confirmed by user, never decay -->

- **commit 后立即 push** — 不攒，链不断
- **ruff + black 全量跑** — 不只修 CI 点名的那一个文件
- **测试写实际行为** — 先验证再写断言，不写预期行为

## Active Patterns
<!-- Patterns observed 3+ times, subject to decay -->

- **配置文件优先级**：ruff.toml > pyproject.toml，修改配置前先确认哪个文件生效（2 次踩坑：ruff、eslint）
- **写入→读取链路验证**：任何涉及「配置写入→运行时读取」的功能，必须做端到端验证（写→读→确认）。遗漏型 bug 多发于模块衔接处（cli_self_config.py 写 ~/.omc/.env → router.py 读 os.getenv()，中间缺少 load_dotenv() 胶水代码）
- **时间戳取模不唯一**：CI 环境可能同一毫秒执行两次 → 用单调计数器（1 次，但影响严重）
- **bandit nosec 行号**：多行语句中每个含问题字面量的行都需要 nosec（1 次）

## Recent (last 7 days)
<!-- New corrections pending confirmation -->

- [2026-04-29] 写入→读取链路需端到端验证（load_dotenv 遗漏）
  Type: design-pattern
  Context: Bug #9，cli_self_config.py 写 ~/.omc/.env，router.py 读 os.getenv()，CLI 启动时漏了 load_dotenv() 注入 os.environ。属于模块衔接处的遗漏型 bug。
  预防：涉及「写入→读取」链路的功能，完成后加端到端验证测试。
  Confirmed: true

- [2026-04-27] 时间戳取模 → 单调计数器
  Type: technical
  Context: checkpoint cp_id 唯一性，CI 同毫秒执行导致 ID 冲突
  Confirmed: pending (1/3)

- [2026-04-27] ruff.toml 优先级高于 pyproject.toml
  Type: technical
  Context: 修改 ruff 配置后不生效，发现根目录有独立 ruff.toml
  Confirmed: pending (1/3)

- [2026-04-27] bandit nosec 要对齐问题行号
  Type: technical
  Context: sandbox.py 多行 if 语句，nosec 只加在第一行，第二行的 /tmp 仍被报
  Confirmed: pending (1/3)
