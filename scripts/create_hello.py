"""
脚本：在用户桌面创建 hello.txt 文件，内容为 "OMC"。

用法：
    python scripts/create_hello.py

此脚本会自动检测当前操作系统的桌面路径，并执行文件创建操作。
"""

import os
import platform
import sys
from pathlib import Path


def get_desktop_path() -> Path:
    """
    获取当前用户的桌面目录路径。

    Returns:
        Path: 桌面目录的 Path 对象。

    Raises:
        RuntimeError: 如果无法确定桌面路径或路径不存在。
    """
    system = platform.system()

    if system == "Windows":
        # Windows 桌面路径通常在 %USERPROFILE%/Desktop
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    elif system == "Darwin":
        # macOS 桌面路径是 ~/Desktop
        desktop = Path.home() / "Desktop"
    elif system == "Linux":
        # Linux 桌面路径通常是 ~/Desktop，但也可能被配置为其他路径
        # 首先尝试 XDG 用户目录配置
        xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
        if xdg_desktop:
            desktop = Path(xdg_desktop)
        else:
            desktop = Path.home() / "Desktop"
    else:
        raise RuntimeError(f"不支持的操作系统: {system}")

    # 规范化路径并检查是否存在
    desktop = desktop.resolve()
    if not desktop.exists():
        raise RuntimeError(f"桌面目录不存在: {desktop}")

    return desktop


def create_hello_file(
    target_dir: Path, filename: str = "hello.txt", content: str = "OMC"
) -> Path:
    """
    在指定目录下创建文件并写入内容。

    Args:
        target_dir: 目标目录路径。
        filename: 要创建的文件名。
        content: 要写入的文本内容。

    Returns:
        Path: 创建的文件完整路径。

    Raises:
        PermissionError: 如果没有写入权限。
        FileExistsError: 如果文件已存在且未指定覆盖（当前策略为覆盖）。
        OSError: 其他文件系统错误。
    """
    file_path = target_dir / filename

    # 检查文件是否已存在
    if file_path.exists():
        print(f"⚠️  文件已存在，将覆盖: {file_path}")
        # 这里可以扩展为询问用户，但为了自动化，我们选择覆盖

    # 写入内容
    file_path.write_text(content, encoding="utf-8")
    print(f"✅ 文件创建成功: {file_path}")

    return file_path


def verify_file(file_path: Path, expected_content: str = "OMC") -> bool:
    """
    验证文件内容是否与预期一致。

    Args:
        file_path: 文件路径。
        expected_content: 预期内容。

    Returns:
        bool: 如果内容匹配返回 True，否则返回 False。
    """
    if not file_path.exists():
        print(f"❌ 验证失败: 文件不存在 {file_path}")
        return False

    actual_content = file_path.read_text(encoding="utf-8")
    if actual_content == expected_content:
        print(f"✅ 文件内容验证通过: 内容为 '{expected_content}'")
        return True
    else:
        print(
            f"❌ 文件内容验证失败: 期望 '{expected_content}', 实际 '{actual_content}'"
        )
        return False


def main():
    """主函数：执行文件创建流程。"""
    print("🚀 开始创建 hello.txt 文件...")
    print(f"   操作系统: {platform.system()} {platform.release()}")

    try:
        # 步骤1：获取桌面路径
        desktop_path = get_desktop_path()
        print(f"   桌面路径: {desktop_path}")

        # 步骤2：创建文件
        file_path = create_hello_file(desktop_path)

        # 步骤3：验证内容
        if not verify_file(file_path):
            print("❌ 操作失败: 文件内容验证未通过。")
            sys.exit(1)

        print("\n🎉 操作成功完成！")

    except PermissionError:
        print(f"❌ 权限错误: 没有写入权限，请检查目录权限。")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ 运行时错误: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ 文件系统错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
