"""
测试脚本：验证 create_hello.py 的核心功能。
"""

import os
import platform
import tempfile
from pathlib import Path

import pytest

from scripts.create_hello import create_hello_file, verify_file, get_desktop_path


class TestGetDesktopPath:
    """测试 get_desktop_path 函数。"""

    def test_returns_path_object(self):
        """测试返回类型是 Path。"""
        path = get_desktop_path()
        assert isinstance(path, Path), "返回值应为 Path 类型"

    def test_path_exists(self):
        """测试返回的路径存在。"""
        path = get_desktop_path()
        assert path.exists(), f"桌面路径应存在: {path}"

    def test_path_is_directory(self):
        """测试返回的路径是目录。"""
        path = get_desktop_path()
        assert path.is_dir(), f"桌面路径应为目录: {path}"

    def test_platform_specific(self):
        """测试不同平台的路径格式（仅在当前平台验证）。"""
        path = get_desktop_path()
        system = platform.system()
        if system == "Windows":
            assert "Desktop" in str(path), f"Windows 桌面路径应包含 'Desktop': {path}"
        elif system == "Darwin":
            assert "Desktop" in str(path), f"macOS 桌面路径应包含 'Desktop': {path}"
        elif system == "Linux":
            # Linux 路径可能不同，但至少应该存在
            assert path.exists(), f"Linux 桌面路径应存在: {path}"


class TestCreateHelloFile:
    """测试 create_hello_file 函数。"""

    def test_create_file_success(self):
        """测试成功创建文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = create_hello_file(tmp_path, "test_hello.txt", "OMC")
            assert file_path.exists(), "文件应被创建"
            assert file_path.read_text() == "OMC", "文件内容应为 'OMC'"

    def test_create_file_custom_content(self):
        """测试自定义内容。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = create_hello_file(tmp_path, "custom.txt", "Hello, World!")
            assert file_path.read_text() == "Hello, World!", "文件内容应匹配"

    def test_create_file_overwrite(self):
        """测试覆盖已有文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "overwrite_test.txt"
            # 先创建文件
            file_path.write_text("old content")
            # 覆盖
            create_hello_file(tmp_path, "overwrite_test.txt", "new content")
            assert file_path.read_text() == "new content", "文件内容应被覆盖"

    def test_create_file_invalid_directory(self):
        """测试无效目录。"""
        with pytest.raises((PermissionError, OSError)):
            create_hello_file(Path("/invalid/path/that/does/not/exist"))

    def test_create_file_returns_path(self):
        """测试返回值为 Path 类型。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = create_hello_file(tmp_path)
            assert isinstance(file_path, Path), "返回值应为 Path 类型"


class TestVerifyFile:
    """测试 verify_file 函数。"""

    def test_verify_exact_match(self):
        """测试内容完全匹配。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "verify_test.txt"
            file_path.write_text("OMC")
            assert verify_file(file_path, "OMC") is True, "内容匹配应返回 True"

    def test_verify_mismatch(self):
        """测试内容不匹配。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "verify_test.txt"
            file_path.write_text("WRONG")
            assert verify_file(file_path, "OMC") is False, "内容不匹配应返回 False"

    def test_verify_file_not_found(self):
        """测试文件不存在。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "non_existent.txt"
            assert verify_file(file_path) is False, "文件不存在应返回 False"

    def test_verify_empty_content(self):
        """测试空内容。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "empty.txt"
            file_path.write_text("")
            assert verify_file(file_path, "OMC") is False, "空内容应与 'OMC' 不匹配"


class TestIntegration:
    """集成测试：模拟完整流程。"""

    def test_full_flow(self):
        """测试完整的创建和验证流程。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # 创建文件
            file_path = create_hello_file(tmp_path, "hello.txt", "OMC")
            # 验证内容
            assert verify_file(file_path, "OMC") is True, "完整流程应成功"

    def test_full_flow_multiple_files(self):
        """测试多次创建不同文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            files = ["a.txt", "b.txt", "c.txt"]
            for fname in files:
                file_path = create_hello_file(tmp_path, fname, "OMC")
                assert verify_file(file_path, "OMC") is True, f"文件 {fname} 应创建成功"
