"""测试 local_model_discovery.py — 本地模型发现"""

from unittest.mock import MagicMock, patch

from src.core.local_model_discovery import (
    OllamaModelInfo,
    discover_ollama_models,
    get_model_info,
    is_ollama_running,
)

# ===== OllamaModelInfo =====


class TestOllamaModelInfo:
    def test_size_gb(self):
        m = OllamaModelInfo(model_name="qwen2:7b", size=4_400_000_000)
        assert m.size_gb == 4.1

    def test_size_gb_zero(self):
        m = OllamaModelInfo(model_name="test", size=0)
        assert m.size_gb == 0.0

    def test_size_mb(self):
        m = OllamaModelInfo(model_name="test", size=1_000_000)
        assert m.size_mb > 0

    def test_size_mb_zero(self):
        m = OllamaModelInfo(model_name="test", size=-1)
        assert m.size_mb == 0.0

    def test_to_dict(self):
        m = OllamaModelInfo(
            model_name="qwen2:7b",
            size=100,
            quantization="q4_K_M",
            parameter_size="7B",
        )
        d = m.to_dict()
        assert d["model_name"] == "qwen2:7b"
        assert "raw" not in d  # raw excluded


# ===== is_ollama_running =====


class TestIsOllamaRunning:
    @patch("src.core.local_model_discovery._make_client")
    def test_running(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert is_ollama_running() is True

    @patch("src.core.local_model_discovery._make_client")
    def test_not_running(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert is_ollama_running() is False

    @patch("src.core.local_model_discovery._make_client")
    def test_exception(self, mock_make):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("timeout")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert is_ollama_running() is False


# ===== discover_ollama_models =====


class TestDiscoverOllamaModels:
    @patch("src.core.local_model_discovery._make_client")
    def test_success(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2:7b", "size": 100, "modified_at": "2024-01-01"},
                {"name": "llama3:8b", "size": 200, "modified_at": "2024-02-01"},
            ]
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        models = discover_ollama_models()
        assert len(models) == 2
        assert models[0].model_name == "llama3:8b"  # sorted by modified_at desc

    @patch("src.core.local_model_discovery._make_client")
    def test_empty_name_filtered(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "", "size": 100}, {"name": "qwen2:7b", "size": 200}]
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        models = discover_ollama_models()
        assert len(models) == 1

    @patch("src.core.local_model_discovery._make_client")
    def test_non_200(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert discover_ollama_models() == []

    @patch("src.core.local_model_discovery._make_client")
    def test_exception(self, mock_make):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("err")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert discover_ollama_models() == []


# ===== get_model_info =====


class TestGetModelInfo:
    def test_empty_name(self):
        assert get_model_info("") is None
        assert get_model_info("  ") is None

    @patch("src.core.local_model_discovery._make_client")
    def test_success(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model_info": {"parameter_size": "7B", "quantization": "q4_K_M"},
            "template": "test template",
            "license": "MIT",
            "system": "You are helpful",
        }
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        info = get_model_info("qwen2:7b")
        assert info is not None
        assert info.parameter_size == "7B"

    @patch("src.core.local_model_discovery._make_client")
    def test_non_200(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert get_model_info("nonexist") is None

    @patch("src.core.local_model_discovery._make_client")
    def test_exception(self, mock_make):
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("err")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        assert get_model_info("test") is None

    @patch("src.core.local_model_discovery._make_client")
    def test_license_from_top_level(self, mock_make):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model_info": {},
            "license": "Apache",
            "template": "tpl",
            "system": "sys",
        }
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_make.return_value = mock_client
        info = get_model_info("test")
        assert info.license == "Apache"
