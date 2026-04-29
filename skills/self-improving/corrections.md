# Corrections Log

<!-- Format:
## YYYY-MM-DD
- [HH:MM] Changed X → Y
  Type: format|technical|communication|project
  Context: where correction happened
  Confirmed: pending (N/3) | yes | no
-->

## 2026-04-27
- [05:35] 时间戳取模 → 单调递增计数器
  Type: technical
  Context: checkpoint.py cp_id 用 `int(time.time() * 1000) % 1000` 生成后缀，CI 同毫秒执行两次导致 ID 冲突
  Changed: `ts_ms = int(time.time() * 1000) % 1000` → `self._seq` 单调计数器
  Confirmed: pending (1/3)

- [03:43] 修改 pyproject.toml → 修改 ruff.toml
  Type: technical
  Context: 修改 ruff 配置后运行 ruff check 仍报 100 个错，发现根目录有独立 ruff.toml 优先级更高
  Changed: 以后修改 ruff 配置前先确认哪个配置文件生效
  Confirmed: pending (1/3)

- [05:35] nosec 只加第一行 → 每行都加
  Type: technical
  Context: sandbox.py `if allowed == Path("/tmp") or str(allowed).startswith("/tmp"):  # nosec B108` 的下一行 `if str(p).startswith("/tmp")` 仍被报 B108
  Changed: 每个含问题字面量的行都需要加 nosec
  Confirmed: pending (1/3)
