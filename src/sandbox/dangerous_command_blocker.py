from __future__ import annotations

from typing import Optional

"""
危险命令拦截器 - Dangerous Command Blocker

基于 Claude Code Auto Mode 风险分类逻辑实现。
在命令执行前进行多维度安全检查，拦截高危操作。

风险等级：
- BLOCK：直接拒绝执行
- WARN：警告但允许执行
- ALLOW：正常放行

白名单模式（默认启用）：
- 只有白名单内的 base command 才允许执行
- 白名单命令仍会经过黑名单检查（深度防御）
- 设置环境变量 OMC_DISABLE_WHITELIST=1 可临时关闭白名单（仅开发环境）
"""

import os
import re
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""

    ALLOW = "allow"  # 正常放行
    WARN = "warn"  # 警告但允许
    BLOCK = "block"  # 直接拒绝


@dataclass
class BlockReason:
    """拦截原因"""

    risk: RiskLevel
    reason: str
    matched_pattern: Optional[str] = None


class BlockedCommandError(Exception):
    """被拦截的命令异常"""

    def __init__(self, command: str, reason: str, risk: RiskLevel):
        self.command = command
        self.reason = reason
        self.risk = risk
        # 脱敏：不把完整命令写入错误消息，避免敏感信息泄露
        safe_cmd = _sanitize_for_error(command)
        super().__init__(f"[{risk.value.upper()}] {reason}\n命令: {safe_cmd}")


def _sanitize_for_error(text: str) -> str:
    """对错误消息中的敏感信息进行脱敏处理"""
    # 简单脱敏：如果命令长度超过 200 字符，截断
    if len(text) > 200:
        return text[:200] + "...[截断]"
    return text


# =============================================================================
# 白名单模式 - 允许执行的 base command
# =============================================================================

# 白名单：只有这些 base command 允许执行
# 设置环境变量 OMC_DISABLE_WHITELIST=1 可临时禁用（仅开发环境）
ALLOWED_BASE_COMMANDS: set[str] = {
    # ── 文件读取 ──
    "ls", "cat", "grep", "find", "head", "tail",
    "wc", "sort", "uniq", "file", "stat", "tree", "du",
    # ── 文件操作（危险操作由黑名单覆盖）──
    "mkdir", "touch", "cp", "mv", "rm", "rmdir",
    "chmod", "chown", "ln",
    # ── 解压/归档读取 ──
    "tar", "unzip", "gunzip", "bunzip2",
    # ── Python ──
    "python3", "python", "pip", "pip3", "pytest",
    # ── Git ──
    "git",
    # ── Node.js ──
    "node", "npm", "npx",
    # ── C/C++ ──
    "gcc", "g++", "make", "cmake",
    # ── Go ──
    "go",
    # ── Rust ──
    "rustc", "cargo",
    # ── Java ──
    "java", "javac",
    # ── 文本处理 ──
    "sed", "awk", "tr", "cut", "paste",
    # ── Shell 内建/常用 ──
    "echo", "printf", "pwd", "whoami", "date", "hostname",
    "uname", "basename", "dirname", "true", "false", "sleep",
    # ── 下载（受限）──
    "curl", "wget",
    # ── 进程查看 ──
    "ps", "top",
    # ── 网络诊断 ──
    "ping", "netstat", "ss",
    # ── 环境信息 ──
    "env", "which", "whereis",
    # ── 容器 / 编排（危险操作由黑名单覆盖）──
    "docker", "docker-compose", "podman", "kubectl", "helm",
    # ── 包管理 / 系统管理（危险操作由黑名单覆盖）──
    "sudo", "apt-get", "yum", "dnf", "brew", "pacman",
    # ── 数据库 CLI（危险操作由黑名单覆盖）──
    "mysql", "psql", "sqlite3",
}


# 需要完整路径匹配的 base command（防止利用 PATH 绕过）
# 例如：/usr/bin/rm 也会被 extract_base_command 提取为 rm，无需额外处理


def is_whitelist_enabled() -> bool:
    """白名单模式是否启用（可通过环境变量禁用）"""
    return os.environ.get("OMC_DISABLE_WHITELIST", "0") != "1"


def extract_base_command(command: str) -> str:
    """
    从完整命令中提取 base command（去路径、去 flags 前缀）

    示例：
        "python3 script.py" → "python3"
        "/usr/bin/python3 -c 'print(1)'" → "python3"
        "git log --oneline" → "git"
        "PYTHONPATH=/foo python3 -c '...'" → "python3"（跳过环境变量前缀）
        "sudo python3 script.py" → "sudo"（sudo 需要单独处理）
    """
    import shlex

    normalized = " ".join(command.split())

    # 去掉环境变量前缀（KEY=VALUE cmd ...）
    # 处理多个环境变量前缀的情况
    while re.match(r"^[A-Za-z_][A-Za-z0-9_]*=\S+\s+", normalized):
        normalized = re.sub(r"^[A-Za-z_][A-Za-z0-9_]*=\S+\s+", "", normalized, count=1)

    # 去掉 sudo / doas 等提权前缀（这些不应出现在沙箱中）
    tokens = shlex.split(normalized)
    if not tokens:
        return ""

    first = tokens[0]

    # 去掉路径前缀
    base = first.rsplit("/", 1)[-1]

    return base


# =============================================================================
# 危险模式定义（正则 + 关键词）
# 参考 Claude Code Auto Mode 风险分类
# =============================================================================

# P0 - 极高危：直接删除系统文件、破坏性操作
CRITICAL_PATTERNS: list[tuple[str, str]] = [
    # 递归删除根目录
    (r"rm\s+-rf\s+/(?:\s|$|&&|;|\|)", "递归删除根目录，会清空整个系统"),
    (r"rm\s+-rf\s+/\*", "递归删除根目录所有文件"),
    (r"rm\s+-rf\s+\.", "递归删除当前目录及其所有子目录"),
    # 格式化磁盘
    (r"dd\s+if=.*\s+of=/dev/", "直接写入磁盘设备，可能导致数据丢失"),
    (r"mkfs", "格式化文件系统"),
    (r"mke2fs", "创建 ext2/3/4 文件系统"),
    # 危险重定向覆盖系统文件
    (r">\s*/etc/", "尝试覆盖系统配置文件"),
    (r">\s*/usr/", "尝试覆盖系统目录"),
    (r">\s*/bin/", "尝试覆盖系统二进制文件"),
    # Fork bomb（叉弹）
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;:", "Fork Bomb - 会耗尽系统资源"),
    (r"fork\(\)\s*;\s*fork\(\)", "嵌套 fork 调用 - 可能导致资源耗尽"),
    # 删除 SSH 密钥
    (r"rm\s+-rf\s+.*\.ssh", "删除 SSH 密钥目录"),
    # 禁用防火墙
    (r"iptables\s+-F", "清空 iptables 规则"),
    (r"ufw\s+disable", "禁用 UFW 防火墙"),
    # Wipe disk
    (r"shred\s+-f", "粉碎文件"),
    # 危险网络下载执行
    (r"(curl|wget).*\|.*(bash|sh)", "下载并直接执行脚本（Pipe to Bash）"),
    (r"bash\s+<\(", "Process Substitution 执行远程脚本"),
    (r"curl.*>.*&&.*bash", "下载脚本后执行"),
    (r"wget.*>.*&&.*bash", "下载脚本后执行"),
    # 修改 /etc/hosts
    (r"echo.*>>\s*/etc/hosts", "修改 hosts 文件"),
    # 添加可疑 cron
    (r"crontab\s+-r", "删除用户 crontab"),
    # 可疑 Python 执行
    (r"python.*exec", "动态代码执行"),
    # 危险 sudo
    (r"chmod\s+777\s+/etc/sudoers", "修改 sudoers 权限"),
    (r"sudo\s+su\s+-", "提权到 root 的快捷方式"),
]

# P1 - 高危：可能造成数据丢失但有一定合理性
HIGH_RISK_PATTERNS: list[tuple[str, str]] = [
    # 大范围删除
    (r"rm\s+-rf\s+/tmp", "递归删除 /tmp 目录"),
    (r"rm\s+-rf\s+/var/log", "递归删除日志目录"),
    (r"rm\s+-rf\s+/home", "递归删除用户目录"),
    (r"rm\s+-rf\s+/opt", "递归删除可选软件目录"),
    # 强制删除
    (r"rm\s+-f\s+/\S+", "强制删除文件"),
    # chmod 777
    (r"chmod\s+777", "设置最大权限 777"),
    (r"chmod\s+-R\s+777", "递归设置 777 权限"),
    (r"chmod\s+0", "移除所有权限"),
    # 覆盖文件
    (r">\s*~/.bashrc", "覆盖 shell 配置文件"),
    (r">\s*~/.zshrc", "覆盖 shell 配置文件"),
    # killall 强制终止
    (r"killall\s+-9", "强制终止所有进程"),
    (r"kill\s+-9\s+-1", "终止所有进程"),
    # 网络端口操作
    (r"nc\s+-l\s+-p", "在端口上监听连接"),
    (r"nc\s+-e", "执行远程命令"),
    # Docker 危险操作
    (r"docker\s+run\s+--privileged", "特权模式运行容器"),
    (r"docker\s+exec\s+--privileged", "特权模式进入容器"),
    (r"docker\s+rm\s+-f\s+\$\(", "删除所有容器"),
]

# P2 - 中危：需要确认的操作
MEDIUM_RISK_PATTERNS: list[tuple[str, str]] = [
    # 系统配置修改
    (r"systemctl\s+stop", "停止系统服务"),
    (r"service\s+stop", "停止系统服务"),
    # 数据库操作
    (r"mysql.*DROP\s+DATABASE", "删除 MySQL 数据库"),
    (r"psql.*DROP\s+DATABASE", "删除 PostgreSQL 数据库"),
    (r"redis-cli\s+FLUSHALL", "清空 Redis 所有数据"),
    # Git 危险操作
    (r"git\s+push\s+--force", "强制推送到远程"),
    (r"git\s+push\s+-f", "强制推送到远程"),
    # 网络操作
    (r"curl\s+-X\s+DELETE", "发送 DELETE 请求"),
    (r"wget\s+-r\s+-np", "递归下载网站"),
]

# 需要警告但允许的操作
WARN_PATTERNS: list[tuple[str, str]] = [
    # 破坏性 Git 操作
    (r"git\s+reset\s+--hard", "硬重置 Git 工作区"),
    (r"git\s+clean\s+-fd", "清理未跟踪文件"),
    # 全局包安装
    (r"npm\s+install\s+-g", "全局安装 npm 包"),
    (r"pip\s+install\s+--user", "用户级安装 pip 包"),
]


# =============================================================================
# 主拦截器
# =============================================================================


class DangerousCommandBlocker:
    """
    危险命令拦截器

    在命令执行前进行多维度安全检查。

    使用示例：
        blocker = DangerousCommandBlocker()
        result = blocker.check("rm -rf /tmp/test")
        if result.risk == RiskLevel.BLOCK:
            raise BlockedCommandError("rm -rf /tmp/test", result.reason, result.risk)
    """

    def __init__(self) -> None:
        self._critical_re = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in CRITICAL_PATTERNS
        ]
        self._high_re = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in HIGH_RISK_PATTERNS
        ]
        self._medium_re = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in MEDIUM_RISK_PATTERNS
        ]
        self._warn_re = [
            (re.compile(p, re.IGNORECASE), msg) for p, msg in WARN_PATTERNS
        ]

    def check(self, command: str) -> BlockReason:
        """
        检查命令是否危险

        Args:
            command: 待检查的命令字符串

        Returns:
            BlockReason: 包含风险等级和原因的检查结果
        """
        if not command or not command.strip():
            return BlockReason(RiskLevel.ALLOW, "")

        # 去除多余空白，规范化命令
        normalized = " ".join(command.split())

        # ── 白名单检查（最高优先级，在黑名单之前）──
        if is_whitelist_enabled():
            base_cmd = extract_base_command(command)
            if base_cmd and base_cmd not in ALLOWED_BASE_COMMANDS:
                return BlockReason(
                    risk=RiskLevel.BLOCK,
                    reason=f"base command '{base_cmd}' 不在白名单中，禁止执行",
                    matched_pattern=None,
                )

        # 第一优先级：检查极高危模式（直接拒绝）
        for pattern, msg in self._critical_re:
            if pattern.search(normalized):
                return BlockReason(
                    risk=RiskLevel.BLOCK,
                    reason=msg,
                    matched_pattern=pattern.pattern,
                )

        # 第二优先级：检查高危模式（直接拒绝）
        for pattern, msg in self._high_re:
            if pattern.search(normalized):
                return BlockReason(
                    risk=RiskLevel.BLOCK,
                    reason=msg,
                    matched_pattern=pattern.pattern,
                )

        # 第三优先级：检查中危模式（警告）
        for pattern, msg in self._medium_re:
            if pattern.search(normalized):
                return BlockReason(
                    risk=RiskLevel.WARN,
                    reason=msg,
                    matched_pattern=pattern.pattern,
                )

        # 第四优先级：检查警告模式（仅警告）
        for pattern, msg in self._warn_re:
            if pattern.search(normalized):
                return BlockReason(
                    risk=RiskLevel.WARN,
                    reason=msg,
                    matched_pattern=pattern.pattern,
                )

        return BlockReason(RiskLevel.ALLOW, "")

    def validate(self, command: str, strict: bool = True) -> None:
        """
        验证命令，危险时抛出异常

        Args:
            command: 待检查的命令
            strict: True=BLOCK/WARN 都抛异常，False=只 BLOCK 抛异常

        Raises:
            BlockedCommandError: 命令被拦截时抛出
        """
        result = self.check(command)

        if result.risk == RiskLevel.BLOCK:
            raise BlockedCommandError(command, result.reason, result.risk)

        if strict and result.risk == RiskLevel.WARN:
            raise BlockedCommandError(command, result.reason, result.risk)


# =============================================================================
# 全局单例
# =============================================================================

_default_blocker: Optional[DangerousCommandBlocker] = None


def get_blocker() -> DangerousCommandBlocker:
    """获取全局拦截器单例"""
    global _default_blocker
    if _default_blocker is None:
        _default_blocker = DangerousCommandBlocker()
    return _default_blocker


def check_command(command: str) -> BlockReason:
    """快捷函数：检查命令"""
    return get_blocker().check(command)


def validate_command(command: str, strict: bool = True) -> None:
    """快捷函数：验证命令"""
    return get_blocker().validate(command, strict=strict)
