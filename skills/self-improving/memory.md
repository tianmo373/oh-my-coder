# Self-Improving Memory

## Confirmed Preferences
<!-- Patterns confirmed by user, never decay -->

- **commit 后立即 push** — 不攒，链不断
- **ruff + black 全量跑** — 不只修 CI 点名的那一个文件
- **测试写实际行为** — 先验证再写断言，不写预期行为

## Active Patterns
<!-- Patterns observed 3+ times, subject to decay -->

- **配置文件优先级**：ruff.toml > pyproject.toml，修改配置前先确认哪个文件生效（2 次踩坑：ruff、eslint）
- **时间戳取模不唯一**：CI 环境可能同一毫秒执行两次 → 用单调计数器（1 次，但影响严重）
- **bandit nosec 行号**：多行语句中每个含问题字面量的行都需要 nosec（1 次）

## Recent (last 7 days)
<!-- New corrections pending confirmation -->

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
