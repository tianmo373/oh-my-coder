from __future__ import annotations

"""
omc quality - 代码质量检查命令

支持以下子命令：
- omc quality check [path]  # 运行 ruff check
- omc quality fix [path]   # 运行 ruff check --fix
- omc quality all [path]   # 先 black 再 ruff check
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="代码质量检查 - ruff/black 集成")
console = Console()


def _check_ruff_installed() -> bool:
    """检查 ruff 是否已安装"""
    return shutil.which("ruff") is not None


def _check_black_installed() -> bool:
    """检查 black 是否已安装"""
    return shutil.which("black") is not None


@app.command("check")
def quality_check(
    path: Optional[str] = typer.Argument("src", help="要检查的路径（默认 src/）"),
) -> None:
    """
    运行 ruff check 检查代码

    Examples:
        omc quality check
        omc quality check src/
        omc quality check src/commands/
    """
    if not _check_ruff_installed():
        console.print("[red]❌ ruff 未安装，请运行:[/red]")
        console.print("  [cyan]pip install ruff[/cyan]")
        raise typer.Exit(1)

    target_path = Path(path) if path else Path("src")

    console.print(f"[bold]🔍 运行 ruff check {target_path}...[/bold]\n")

    try:
        result = subprocess.run(
            ["ruff", "check", str(target_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✅ ruff check passed[/green]")
        else:
            console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            console.print(f"\n[yellow]⚠️ 发现 {result.returncode} 个问题[/yellow]")
            raise typer.Exit(result.returncode)

    except FileNotFoundError:
        console.print("[red]❌ ruff 命令未找到[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 执行失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("fix")
def quality_fix(
    path: Optional[str] = typer.Argument("src", help="要修复的路径（默认 src/）"),
) -> None:
    """
    运行 ruff check --fix 自动修复代码

    Examples:
        omc quality fix
        omc quality fix src/
        omc quality fix src/commands/
    """
    if not _check_ruff_installed():
        console.print("[red]❌ ruff 未安装，请运行:[/red]")
        console.print("  [cyan]pip install ruff[/cyan]")
        raise typer.Exit(1)

    target_path = Path(path) if path else Path("src")

    console.print(f"[bold]🔧 运行 ruff check --fix {target_path}...[/bold]\n")

    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", str(target_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✅ 所有问题已自动修复[/green]")
        else:
            console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            console.print(f"\n[yellow]⚠️ 已修复部分问题，仍有 {result.returncode} 个问题待手动处理[/yellow]")

    except FileNotFoundError:
        console.print("[red]❌ ruff 命令未找到[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 执行失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("all")
def quality_all(
    path: Optional[str] = typer.Argument("src", help="要处理的路径（默认 src/）"),
) -> None:
    """
    先运行 black 格式化，再运行 ruff check

    Examples:
        omc quality all
        omc quality all src/
        omc quality all src/commands/
    """
    if not _check_ruff_installed():
        console.print("[red]❌ ruff 未安装，请运行:[/red]")
        console.print("  [cyan]pip install ruff[/cyan]")
        raise typer.Exit(1)

    if not _check_black_installed():
        console.print("[red]❌ black 未安装，请运行:[/red]")
        console.print("  [cyan]pip install black[/cyan]")
        raise typer.Exit(1)

    target_path = Path(path) if path else Path("src")

    # Step 1: black 格式化
    console.print(f"[bold]📝 运行 black 格式化 {target_path}...[/bold]\n")

    try:
        result = subprocess.run(
            ["black", str(target_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✅ black 格式化完成[/green]\n")
        else:
            console.print(result.stdout)
            if result.stderr:
                console.print(f"[yellow]⚠️ {result.stderr}[/yellow]")
            console.print()

    except FileNotFoundError:
        console.print("[red]❌ black 命令未找到[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ black 执行失败: {e}[/red]")
        raise typer.Exit(1)

    # Step 2: ruff check
    console.print(f"[bold]🔍 运行 ruff check {target_path}...[/bold]\n")

    try:
        result = subprocess.run(
            ["ruff", "check", str(target_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✅ ruff check passed[/green]")
        else:
            console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            console.print(f"\n[yellow]⚠️ 发现 {result.returncode} 个问题[/yellow]")
            raise typer.Exit(result.returncode)

    except FileNotFoundError:
        console.print("[red]❌ ruff 命令未找到[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ ruff 执行失败: {e}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """默认显示帮助"""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
