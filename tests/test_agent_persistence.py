"""
测试 Agent 状态持久化

运行: pytest tests/test_agent_persistence.py -v
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, "/Users/vobc/.qclaw/workspace-agent-bf627e2b/projects/oh-my-coder")

from src.agents.persistence.store import (
    AgentConfig,
    AgentState,
    AgentStateStore,
    HistoryEntry,
)


@pytest.fixture
def tmp_store(tmp_path: Path) -> AgentStateStore:
    """临时存储目录"""
    return AgentStateStore(store_root=tmp_path / "agents")


class TestAgentConfig:
    """测试 AgentConfig 数据类"""

    def test_default_values(self):
        config = AgentConfig(name="test-agent")
        assert config.name == "test-agent"
        assert config.model == "deepseek"
        assert config.lane == "build"
        assert config.tools == []
        assert config.max_tokens == 8000
        assert config.temperature == 0.7

    def test_custom_values(self):
        config = AgentConfig(
            name="planner",
            description="规划 Agent",
            model="kimi",
            lane="build",
            default_tier="premium",
            tools=["read_file", "write_file"],
            max_tokens=16000,
            temperature=0.3,
        )
        assert config.name == "planner"
        assert config.model == "kimi"
        assert config.tools == ["read_file", "write_file"]


class TestHistoryEntry:
    """测试 HistoryEntry 数据类"""

    def test_to_dict(self):
        entry = HistoryEntry(
            role="user",
            content="请帮我重构这段代码",
            timestamp="2026-04-28T10:00:00",
            metadata={"source": "cli"},
        )
        d = entry.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "请帮我重构这段代码"
        assert d["metadata"]["source"] == "cli"

    def test_from_dict(self):
        data = {
            "role": "assistant",
            "content": "好的，我来帮你分析",
            "timestamp": "2026-04-28T10:01:00",
            "metadata": {"tokens": 150},
        }
        entry = HistoryEntry.from_dict(data)
        assert entry.role == "assistant"
        assert entry.content == "好的，我来帮你分析"
        assert entry.metadata["tokens"] == 150


class TestAgentState:
    """测试 AgentState 数据类"""

    def test_to_dict(self):
        state = AgentState(
            agent_name="explore",
            session_id="abc123",
            total_tokens=5000,
            total_cost=0.05,
        )
        d = state.to_dict()
        assert d["agent_name"] == "explore"
        assert d["total_tokens"] == 5000
        assert d["total_cost"] == 0.05

    def test_from_dict(self):
        data = {
            "agent_name": "analyst",
            "session_id": "xyz789",
            "total_tokens": 10000,
            "total_cost": 0.12,
            "checkpoints": ["cp1", "cp2"],
        }
        state = AgentState.from_dict(data)
        assert state.agent_name == "analyst"
        assert state.total_tokens == 10000
        assert state.checkpoints == ["cp1", "cp2"]


class TestAgentStateStore:
    """测试 AgentStateStore 核心操作"""

    def test_save_creates_directory(self, tmp_store: AgentStateStore):
        config = AgentConfig(name="test-agent")
        agent_dir = tmp_store.save("test-agent", config)
        assert agent_dir.exists()
        assert (agent_dir / "config.json").exists()

    def test_save_and_restore_config(self, tmp_store: AgentStateStore):
        config = AgentConfig(
            name="planner",
            description="规划任务分解",
            model="deepseek",
            tools=["read", "write"],
        )
        tmp_store.save("planner", config)

        restored_config, _, _ = tmp_store.restore("planner")
        assert restored_config is not None
        assert restored_config.name == "planner"
        assert restored_config.description == "规划任务分解"
        assert restored_config.tools == ["read", "write"]

    def test_save_and_restore_history(self, tmp_store: AgentStateStore):
        config = AgentConfig(name="explore")
        history = [
            HistoryEntry(
                role="user", content="探索项目", timestamp="2026-04-28T10:00:00"
            ),
            HistoryEntry(
                role="assistant", content="正在分析...", timestamp="2026-04-28T10:00:05"
            ),
        ]
        tmp_store.save("explore", config, history)

        _, restored_history, _ = tmp_store.restore("explore")
        assert len(restored_history) == 2
        assert restored_history[0].role == "user"
        assert restored_history[1].content == "正在分析..."

    def test_append_history_mode(self, tmp_store: AgentStateStore):
        config = AgentConfig(name="debugger")
        history1 = [
            HistoryEntry(
                role="user", content="第一次", timestamp="2026-04-28T10:00:00"
            ),
        ]
        history2 = [
            HistoryEntry(
                role="user", content="第二次", timestamp="2026-04-28T10:01:00"
            ),
        ]

        tmp_store.save("debugger", config, history1)
        tmp_store.save("debugger", config, history2, append_history=True)

        _, history, _ = tmp_store.restore("debugger")
        assert len(history) == 2
        assert history[0].content == "第一次"
        assert history[1].content == "第二次"

    def test_save_and_restore_state(self, tmp_store: AgentStateStore):
        config = AgentConfig(name="executor")
        state = AgentState(
            agent_name="executor",
            session_id="sess-123",
            total_tokens=10000,
            total_cost=0.15,
            last_task="执行重构",
        )
        tmp_store.save("executor", config, state=state)

        _, _, restored_state = tmp_store.restore("executor")
        assert restored_state is not None
        assert restored_state.session_id == "sess-123"
        assert restored_state.total_tokens == 10000
        assert restored_state.last_task == "执行重构"

    def test_restore_nonexistent_agent(self, tmp_store: AgentStateStore):
        config, history, state = tmp_store.restore("nonexistent")
        assert config is None
        assert history == []
        assert state is None

    def test_delete_agent(self, tmp_store: AgentStateStore):
        config = AgentConfig(name="to-delete")
        tmp_store.save("to-delete", config)
        assert "to-delete" in tmp_store.list_saved()

        result = tmp_store.delete("to-delete")
        assert result is True
        assert "to-delete" not in tmp_store.list_saved()

    def test_list_saved(self, tmp_store: AgentStateStore):
        for name in ["agent1", "agent2", "agent3"]:
            tmp_store.save(name, AgentConfig(name=name))

        saved = tmp_store.list_saved()
        assert len(saved) == 3
        assert set(saved) == {"agent1", "agent2", "agent3"}

    def test_export_import_roundtrip(self, tmp_store: AgentStateStore, tmp_path: Path):
        # 创建并保存 agent
        config = AgentConfig(
            name="export-test",
            description="导出测试",
            model="kimi",
        )
        state = AgentState(
            agent_name="export-test",
            total_tokens=5000,
            custom_state={"key": "value"},
        )
        history = [
            HistoryEntry(role="user", content="测试", timestamp="2026-04-28T10:00:00"),
        ]
        tmp_store.save("export-test", config, history, state)

        # 导出
        export_file = tmp_path / "export-test.json"
        tmp_store.export_agent("export-test", export_file, include_history=True)
        assert export_file.exists()

        # 验证导出文件结构
        data = json.loads(export_file.read_text(encoding="utf-8"))
        assert data["agent_name"] == "export-test"
        assert data["config"]["model"] == "kimi"
        assert len(data["history"]) == 1
        assert data["state"]["total_tokens"] == 5000

        # 删除原 agent
        tmp_store.delete("export-test")

        # 导入
        imported_name = tmp_store.import_agent(export_file)
        assert imported_name == "export-test"

        # 验证恢复
        restored_config, restored_history, restored_state = tmp_store.restore(
            "export-test"
        )
        assert restored_config is not None
        assert restored_config.model == "kimi"
        assert restored_state.total_tokens == 5000
        assert len(restored_history) == 1

    def test_export_without_history(self, tmp_store: AgentStateStore, tmp_path: Path):
        config = AgentConfig(name="no-history-test")
        history = [
            HistoryEntry(
                role="user", content="不要导出这条", timestamp="2026-04-28T10:00:00"
            ),
        ]
        tmp_store.save("no-history-test", config, history)

        export_file = tmp_path / "no-history.json"
        tmp_store.export_agent("no-history-test", export_file, include_history=False)

        data = json.loads(export_file.read_text(encoding="utf-8"))
        assert "history" not in data or len(data.get("history", [])) == 0

    def test_import_with_new_name(self, tmp_store: AgentStateStore, tmp_path: Path):
        # 创建并导出
        config = AgentConfig(name="original-name")
        tmp_store.save("original-name", config)
        export_file = tmp_path / "original.json"
        tmp_store.export_agent("original-name", export_file)

        # 用新名称导入
        imported_name = tmp_store.import_agent(export_file, new_name="renamed-agent")
        assert imported_name == "renamed-agent"
        assert "renamed-agent" in tmp_store.list_saved()

    def test_get_stats(self, tmp_store: AgentStateStore):
        for i in range(3):
            config = AgentConfig(name=f"agent-{i}")
            history = [
                HistoryEntry(
                    role="user", content=f"msg-{j}", timestamp=f"2026-04-28T10:0{j}:00"
                )
                for j in range(i + 1)
            ]
            tmp_store.save(f"agent-{i}", config, history)

        stats = tmp_store.get_stats()
        assert stats["total_agents"] == 3
        assert stats["total_history_entries"] == 6  # 0+1+2+3 = 6
        assert stats["total_size_bytes"] > 0
