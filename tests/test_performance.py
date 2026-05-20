"""
Tests for src/utils/performance.py
"""

import asyncio
import time

import pytest

from src.utils.performance import (
    AsyncExecutor,
    LRUCache,
    PerformanceMonitor,
    cache_result,
    get_cache,
    get_monitor,
    measure_time,
)


class TestLRUCache:
    """Test LRUCache class."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key."""
        cache = LRUCache()
        assert cache.get("nonexistent") is None

    def test_delete(self):
        """Test deleting a key."""
        cache = LRUCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_nonexistent_key(self):
        """Test deleting a non-existent key."""
        cache = LRUCache()
        assert cache.delete("nonexistent") is False

    def test_clear(self):
        """Test clearing the cache."""
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        # Add a fourth item, should evict key1
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_ordering(self):
        """Test that accessing an item moves it to the end."""
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1, should move it to the end
        cache.get("key1")

        # Add a new item, should evict key2 (not key1)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still exists
        assert cache.get("key2") is None  # Evicted

    def test_update_existing_key(self):
        """Test updating an existing key."""
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_stats(self):
        """Test cache statistics."""
        cache = LRUCache()
        cache.set("key1", "value1")

        # Hit
        cache.get("key1")
        # Miss
        cache.get("nonexistent")

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 50.0

    def test_stats_empty_cache(self):
        """Test stats for empty cache."""
        cache = LRUCache()
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_thread_safety(self):
        """Test that cache operations are thread-safe."""
        import threading

        cache = LRUCache(max_size=100)
        errors = []

        def writer(start, count):
            try:
                for i in range(start, start + count):
                    cache.set(f"key{i}", f"value{i}")
            except Exception as e:
                errors.append(e)

        def reader(start, count):
            try:
                for i in range(start, start + count):
                    cache.get(f"key{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(0, 50)),
            threading.Thread(target=writer, args=(50, 50)),
            threading.Thread(target=reader, args=(0, 50)),
            threading.Thread(target=reader, args=(50, 50)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestAsyncExecutor:
    """Test AsyncExecutor class."""

    @pytest.mark.asyncio
    async def test_run_single_coro(self):
        """Test running a single coroutine."""
        executor = AsyncExecutor(max_concurrent=5)

        async def task():
            return "result"

        result = await executor.run(task())
        assert result == "result"

    @pytest.mark.asyncio
    async def test_run_all_success(self):
        """Test running multiple coroutines successfully."""

        async def task(n):
            await asyncio.sleep(0.01)
            return n * 2

        executor = AsyncExecutor(max_concurrent=5)
        results = await executor.run_all([task(1), task(2), task(3)])

        assert len(results) == 3
        assert all(r[0] for r in results)  # All succeeded
        assert results[0][1] == 2
        assert results[1][1] == 4
        assert results[2][1] == 6

    @pytest.mark.asyncio
    async def test_run_all_with_failure(self):
        """Test running coroutines with some failures."""

        async def success():
            return "ok"

        async def failure():
            raise ValueError("test error")

        executor = AsyncExecutor()
        results = await executor.run_all([success(), failure(), success()])

        assert results[0][0] is True
        assert results[0][1] == "ok"
        assert results[1][0] is False
        assert results[1][1] == "ValueError"
        assert results[2][0] is True

    @pytest.mark.asyncio
    async def test_run_all_fail_fast(self):
        """Test fail_fast mode."""

        async def success():
            return "ok"

        async def failure():
            raise RuntimeError("test error")

        executor = AsyncExecutor()
        with pytest.raises(RuntimeError):
            await executor.run_all([success(), failure(), success()], fail_fast=True)

    @pytest.mark.asyncio
    async def test_run_all_empty_list(self):
        """Test running empty list of coroutines."""
        executor = AsyncExecutor()
        results = await executor.run_all([])
        assert results == []


class TestCacheResult:
    """Test cache_result decorator."""

    def test_caches_result(self):
        """Test that results are cached."""
        call_count = 0

        @cache_result(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

        # Call with different args
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cache_expires(self):
        """Test that cache expires after TTL."""
        call_count = 0

        @cache_result(ttl_seconds=1)
        def timed_function(x):
            nonlocal call_count
            call_count += 1
            return x

        # First call
        timed_function(5)
        assert call_count == 1

        # Wait for cache to expire
        time.sleep(1.5)

        # Should call function again
        timed_function(5)
        assert call_count == 2

    def test_cache_clear(self):
        """Test that cache can be cleared."""
        call_count = 0

        @cache_result(ttl_seconds=60)
        def function(x):
            nonlocal call_count
            call_count += 1
            return x

        function(5)
        assert call_count == 1

        # Clear cache
        function.cache_clear()

        # Should call function again
        function(5)
        assert call_count == 2

    def test_cache_different_kwargs(self):
        """Test that different kwargs create different cache entries."""
        call_count = 0

        @cache_result(ttl_seconds=60)
        def function(x, y=0):
            nonlocal call_count
            call_count += 1
            return x + y

        function(5, y=1)
        assert call_count == 1

        function(5, y=2)
        assert call_count == 2

        function(5, y=1)  # Cached
        assert call_count == 2


class TestMeasureTime:
    """Test measure_time decorator."""

    def test_prints_execution_time(self, capsys):
        """Test that execution time is printed."""

        @measure_time
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()
        assert result == "done"

        captured = capsys.readouterr()
        assert "执行耗时" in captured.out
        assert "slow_function" in captured.out

    def test_returns_correct_result(self):
        """Test that the decorated function returns the correct result."""

        @measure_time
        def add(a, b):
            return a + b

        assert add(2, 3) == 5


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    def test_record_and_get_stats(self):
        """Test recording operations and getting stats."""
        monitor = PerformanceMonitor()
        monitor.record("api_call", 0.5)
        monitor.record("api_call", 1.0)
        monitor.record("api_call", 0.3)

        stats = monitor.get_stats("api_call")
        assert stats["min"] == 0.3
        assert stats["max"] == 1.0
        assert stats["avg"] == pytest.approx(0.6)
        assert stats["count"] == 3

    def test_get_stats_nonexistent(self):
        """Test getting stats for non-existent operation."""
        monitor = PerformanceMonitor()
        stats = monitor.get_stats("nonexistent")
        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0
        assert stats["count"] == 0

    def test_get_all_stats(self):
        """Test getting all stats."""
        monitor = PerformanceMonitor()
        monitor.record("api_call", 0.5)
        monitor.record("db_query", 0.1)

        all_stats = monitor.get_all_stats()
        assert "api_call" in all_stats
        assert "db_query" in all_stats
        assert all_stats["api_call"]["count"] == 1
        assert all_stats["db_query"]["count"] == 1

    def test_clear(self):
        """Test clearing all records."""
        monitor = PerformanceMonitor()
        monitor.record("api_call", 0.5)
        monitor.clear()
        stats = monitor.get_stats("api_call")
        assert stats["count"] == 0


class TestGlobalInstances:
    """Test global instances."""

    def test_get_cache(self):
        """Test getting global cache instance."""
        cache = get_cache()
        assert isinstance(cache, LRUCache)

    def test_get_monitor(self):
        """Test getting global monitor instance."""
        monitor = get_monitor()
        assert isinstance(monitor, PerformanceMonitor)

    def test_global_cache_is_singleton(self):
        """Test that global cache is a singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_global_monitor_is_singleton(self):
        """Test that global monitor is a singleton."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        assert monitor1 is monitor2
