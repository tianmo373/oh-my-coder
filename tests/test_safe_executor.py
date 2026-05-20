"""
Tests for src/utils/safe_executor.py

Coverage target: 32% → 60%+
"""

import httpx
import pytest

from src.utils.safe_executor import (
    RETRYABLE_EXCEPTIONS,
    BlockedError,
    _default_retry_if,
    safe_execute,
    safe_execute_sync,
)


class TestDefaultRetryIf:
    """Test _default_retry_if function."""

    def test_httpx_read_timeout(self):
        """httpx.ReadTimeout should return True."""
        exc = httpx.ReadTimeout("timeout")
        assert _default_retry_if(exc) is True

    def test_httpx_connect_timeout(self):
        """httpx.ConnectTimeout should return True."""
        exc = httpx.ConnectTimeout("timeout")
        assert _default_retry_if(exc) is True

    def test_httpx_pool_timeout(self):
        """httpx.PoolTimeout should return True."""
        exc = httpx.PoolTimeout("timeout")
        assert _default_retry_if(exc) is True

    def test_httpx_remote_protocol_error(self):
        """httpx.RemoteProtocolError should return True."""
        exc = httpx.RemoteProtocolError("protocol error")
        assert _default_retry_if(exc) is True

    def test_httpx_read_error(self):
        """httpx.ReadError should return True."""
        exc = httpx.ReadError("read error")
        assert _default_retry_if(exc) is True

    def test_httpx_connect_error(self):
        """httpx.ConnectError should return True."""
        exc = httpx.ConnectError("connect error")
        assert _default_retry_if(exc) is True

    def test_httpx_http_error(self):
        """httpx.HTTPError should return True."""
        exc = httpx.HTTPError("http error")
        assert _default_retry_if(exc) is True

    def test_connection_error(self):
        """ConnectionError should return True."""
        exc = ConnectionError("connection error")
        assert _default_retry_if(exc) is True

    def test_timeout_error(self):
        """TimeoutError should return True."""
        exc = TimeoutError("timeout")
        assert _default_retry_if(exc) is True

    def test_os_error(self):
        """OSError should return True."""
        exc = OSError("os error")
        assert _default_retry_if(exc) is True

    def test_value_error(self):
        """ValueError should return False (not retryable)."""
        exc = ValueError("value error")
        assert _default_retry_if(exc) is False

    def test_runtime_error(self):
        """RuntimeError should return False (not retryable)."""
        exc = RuntimeError("runtime error")
        assert _default_retry_if(exc) is False

    def test_key_error(self):
        """KeyError should return False (not retryable)."""
        exc = KeyError("key error")
        assert _default_retry_if(exc) is False


class TestRetryableExceptions:
    """Test RETRYABLE_EXCEPTIONS constant."""

    def test_not_empty(self):
        """RETRYABLE_EXCEPTIONS should not be empty."""
        assert len(RETRYABLE_EXCEPTIONS) > 0

    def test_contains_httpx_exceptions(self):
        """Should contain common httpx exceptions."""
        assert httpx.ReadTimeout in RETRYABLE_EXCEPTIONS
        assert httpx.ConnectTimeout in RETRYABLE_EXCEPTIONS

    def test_all_exceptions(self):
        """All items should be Exception subclasses."""
        for exc_cls in RETRYABLE_EXCEPTIONS:
            assert issubclass(exc_cls, Exception)


class TestBlockedError:
    """Test BlockedError exception."""

    def test_init(self):
        """BlockedError should store command and reason."""
        exc = BlockedError("rm -rf /", "Dangerous command")
        assert exc.command == "rm -rf /"
        assert exc.reason == "Dangerous command"

    def test_message(self):
        """BlockedError should have informative message."""
        exc = BlockedError("rm -rf /", "Dangerous command")
        assert "Blocked" in str(exc)
        assert "rm -rf /" in str(exc)
        assert "Dangerous command" in str(exc)

    def test_raise(self):
        """BlockedError should be raiseable."""
        with pytest.raises(BlockedError):
            raise BlockedError("test", "reason")


class TestSafeExecuteSync:
    """Test safe_execute_sync decorator (basic tests)."""

    def test_decorator_exists(self):
        """safe_execute_sync should be callable."""
        assert callable(safe_execute_sync)

    def test_decorator_returns_wrapper(self):
        """safe_execute_sync should return a decorator."""
        decorator = safe_execute_sync(max_attempts=3)
        assert callable(decorator)

    def test_successful_call(self):
        """Decorated function should execute successfully."""

        @safe_execute_sync(max_attempts=3)
        def success_func():
            return 42

        result = success_func()
        assert result == 42

    def test_retry_on_retryable_error(self):
        """Should retry on retryable errors."""
        call_count = 0

        @safe_execute_sync(max_attempts=3, base_wait=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ReadTimeout("timeout")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_no_retry_on_non_retryable_error(self):
        """Should not retry on non-retryable errors."""
        call_count = 0

        @safe_execute_sync(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("value error")

        with pytest.raises(ValueError):
            failing_func()

        # Should only be called once (no retry)
        assert call_count == 1


@pytest.mark.asyncio
class TestSafeExecute:
    """Test safe_execute decorator (async, basic tests)."""

    async def test_decorator_exists(self):
        """safe_execute should be callable."""
        assert callable(safe_execute)

    async def test_successful_call(self):
        """Decorated async function should execute successfully."""

        @safe_execute(max_attempts=3)
        async def success_func():
            return 42

        result = await success_func()
        assert result == 42

    async def test_retry_on_retryable_error(self):
        """Should retry on retryable errors."""
        call_count = 0

        @safe_execute(max_attempts=3, base_wait=0.01)
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ReadTimeout("timeout")
            return "success"

        result = await failing_func()
        assert result == "success"
        assert call_count == 3
