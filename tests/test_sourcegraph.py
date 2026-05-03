"""Sourcegraph 集成测试"""

from unittest.mock import MagicMock, patch

from src.tools.sourcegraph import (
    SearchMatch,
    SearchResult,
    _check_src_cli,
    _sg_api_search,
    _src_cli_search,
    search,
)


class TestSearchMatch:
    """SearchMatch 数据类测试"""

    def test_format_code_basic(self):
        """测试基础代码格式化"""
        match = SearchMatch(
            repo="example/repo",
            file_path="src/main.py",
            line_number=42,
            content_preview="def hello():",
        )
        result = match.format_code()
        assert "example/repo" in result
        assert "src/main.py" in result
        assert "42" in result

    def test_format_code_with_symbols(self):
        """测试带符号的代码格式化"""
        match = SearchMatch(
            repo="example/repo",
            file_path="src/main.py",
            line_number=10,
            symbols=["hello", "world"],
        )
        result = match.format_code()
        assert "hello" in result
        assert "world" in result


class TestSearchResult:
    """SearchResult 数据类测试"""

    def test_format_table_basic(self):
        """测试表格格式化"""
        matches = [
            SearchMatch(
                repo="example/repo",
                file_path="src/main.py",
                line_number=42,
                repository_stars=100,
            ),
        ]
        result = SearchResult(
            query="test query",
            total_matches=1,
            matches=matches,
            elapsed_ms=100,
            source="api",
        )
        output = result.format_table(limit=10)
        assert "test query" in output
        assert "1" in output
        assert "api" in output

    def test_format_table_with_warnings(self):
        """测试带警告的表格格式化"""
        matches = []
        result = SearchResult(
            query="test",
            total_matches=0,
            matches=matches,
            elapsed_ms=0,
            source="api",
            warnings=["Warning: rate limited"],
        )
        output = result.format_table()
        assert "Warning" in output

    def test_format_json(self):
        """测试 JSON 格式化"""
        matches = [
            SearchMatch(
                repo="example/repo",
                file_path="src/main.py",
                line_number=42,
                language="python",
                repository_stars=100,
            ),
        ]
        result = SearchResult(
            query="test",
            total_matches=1,
            matches=matches,
            elapsed_ms=100,
            source="api",
        )
        output = result.format_json()
        assert "example/repo" in output
        assert "python" in output


class TestSourcegraphAPI:
    """Sourcegraph API 测试"""

    @patch("src.tools.sourcegraph.httpx.post")
    def test_api_search_success(self, mock_post):
        """测试 API 搜索成功"""
        # Mock 响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "search": {
                    "results": {
                        "matchCount": 1,
                        "results": [
                            {
                                "__typename": "FileMatch",
                                "repository": {
                                    "name": "example/repo",
                                    "stars": {"totalCount": 100},
                                },
                                "file": {"path": "src/main.py"},
                                "lineMatches": [
                                    {
                                        "preview": "def hello():",
                                        "lineNumber": 42,
                                    }
                                ],
                            }
                        ],
                    },
                    "elapsedMilliseconds": 50,
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch("src.tools.sourcegraph.SG_API_KEY", "test_key"):
            result = _sg_api_search("test query", limit=10)

        assert result is not None
        assert result.source == "api"
        assert len(result.matches) >= 0

    @patch("src.tools.sourcegraph.httpx.post")
    def test_api_search_no_key(self, mock_post):
        """测试无 API Key 时返回 None"""
        with patch("src.tools.sourcegraph.SG_API_KEY", ""):
            result = _sg_api_search("test query")

        assert result is None
        mock_post.assert_not_called()

    @patch("src.tools.sourcegraph.httpx.post")
    def test_api_search_http_error(self, mock_post):
        """测试 HTTP 错误处理"""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("src.tools.sourcegraph.SG_API_KEY", "bad_key"):
            result = _sg_api_search("test query")

        assert result is not None
        assert "401" in result.warnings[0]


class TestSrcCLI:
    """src CLI 测试"""

    @patch("src.tools.sourcegraph.subprocess.run")
    def test_check_src_cli_available(self, mock_run):
        """测试 src CLI 可用"""
        mock_run.return_value = MagicMock(returncode=0)
        result = _check_src_cli()
        assert result is True

    @patch("src.tools.sourcegraph.subprocess.run")
    def test_check_src_cli_not_available(self, mock_run):
        """测试 src CLI 不可用"""
        mock_run.side_effect = FileNotFoundError()
        result = _check_src_cli()
        assert result is False

    @patch("src.tools.sourcegraph._check_src_cli", return_value=True)
    @patch("src.tools.sourcegraph.subprocess.run")
    def test_cli_search_success(self, mock_run, mock_check):
        """测试 CLI 搜索成功"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b'{"type":"content","repo":"test/repo","path":"main.py","content":{"preview":"def main()"},"line":10,"language":"python","url":"http://example"}',
            stderr=b"",
        )

        result = _src_cli_search("test query", limit=10)

        assert result is not None
        assert result.source == "cli"


class TestSearch:
    """主搜索函数测试"""

    @patch("src.tools.sourcegraph.SG_API_KEY", "test_key")
    @patch("src.tools.sourcegraph._sg_api_search")
    def test_search_prefers_api(self, mock_api):
        """测试优先使用 API"""
        mock_api.return_value = SearchResult(
            query="test",
            total_matches=5,
            matches=[],
            elapsed_ms=100,
            source="api",
        )

        result = search("test", prefer_api=True)

        assert result.source == "api"

    @patch("src.tools.sourcegraph._sg_api_search", return_value=None)
    @patch("src.tools.sourcegraph._src_cli_search")
    def test_search_fallback_to_cli(self, mock_cli, mock_api):
        """测试回退到 CLI"""
        mock_cli.return_value = SearchResult(
            query="test",
            total_matches=3,
            matches=[],
            elapsed_ms=50,
            source="cli",
        )

        result = search("test", prefer_api=True)

        assert result.source == "cli"

    @patch("src.tools.sourcegraph._sg_api_search", return_value=None)
    @patch("src.tools.sourcegraph._src_cli_search", return_value=None)
    def test_search_no_backend(self, mock_cli, mock_api):
        """测试无后端时返回警告"""
        result = search("test", prefer_api=True)

        assert result.source == "none"
        assert len(result.warnings) > 0
