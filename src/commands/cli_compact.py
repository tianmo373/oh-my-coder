"""
omc compact stats - 显示自动压缩统计信息

用法:
  omc compact stats    # 查看压缩统计
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="compact",
    help="自动压缩统计 - 查看压缩历史和 token 使用情况",
    no_args_is_help=True,
)

console = Console()


def _get_manager(project_path: Path):
    from src.memory.manager import MemoryManager

    return MemoryManager.from_project(project_path)


@app.command("stats")
def compact_stats(
    project_path: Path = typer.Option(".", "--project", "-p", help="项目路径"),
):
    """
    📊 显示当前会话的压缩统计

    显示内容：
    - 压缩总次数
    - 节省的 token 数
    - 清理的消息数
    - 工具调用去重次数
    - 历史错误清理数
    """
    manager = _get_manager(project_path.resolve())
    stats = manager.compact_stats

    table = Table(title="🗜️ AutoCompact 统计", show_header=True, header_style="bold cyan")
    table.add_column("指标", style="dim")
    table.add_column("值", justify="right")

    table.add_row("压缩次数", f"{stats['total_compact_count']}")
    table.add_row("节省 token", f"{stats['total_tokens_saved']:,}")
    table.add_row("清理消息数", f"{stats['total_messages_removed']:,}")
    table.add_row("去重 tool_call", f"{stats['total_deduplicated']}")
    table.add_row("清理错误消息", f"{stats['total_errors_removed']}")

    console.print(table)

    if stats["total_compact_count"] == 0:
        console.print("\n[dim]尚未执行过压缩，暂无统计数据。[/dim]")
