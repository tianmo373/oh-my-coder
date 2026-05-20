"""
思维链可视化测试 — chain_of_thought.py

覆盖：ReasoningStepType, ConfidenceLevel, ReasoningStep, ChainOfThought,
      ChainOfThoughtRecorder, ChainVisualizer, 便捷函数
"""

import json
from pathlib import Path

import pytest

from src.core.chain_of_thought import (
    ChainOfThought,
    ChainOfThoughtRecorder,
    ChainVisualizer,
    ConfidenceLevel,
    ReasoningStep,
    ReasoningStepType,
    create_recorder,
    visualize_chain,
)

# ===== 枚举 =====


class TestReasoningStepType:
    def test_all_values(self):
        expected = {
            "analysis": ReasoningStepType.ANALYSIS,
            "planning": ReasoningStepType.PLANNING,
            "decision": ReasoningStepType.DECISION,
            "execution": ReasoningStepType.EXECUTION,
            "observation": ReasoningStepType.OBSERVATION,
            "reflection": ReasoningStepType.REFLECTION,
            "correction": ReasoningStepType.CORRECTION,
        }
        for val, member in expected.items():
            assert member.value == val

    def test_member_count(self):
        assert len(ReasoningStepType) == 7


class TestConfidenceLevel:
    def test_all_values(self):
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.UNCERTAIN.value == "uncertain"

    def test_member_count(self):
        assert len(ConfidenceLevel) == 4


# ===== ReasoningStep =====


class TestReasoningStep:
    @pytest.fixture()
    def step(self) -> ReasoningStep:
        return ReasoningStep(
            step_id="step-001",
            step_type=ReasoningStepType.ANALYSIS,
            agent_name="planner",
            description="Analyze the problem",
            reasoning="The problem requires decomposition",
            evidence=["evidence1", "evidence2"],
            conclusion="Problem decomposed",
            confidence=ConfidenceLevel.HIGH,
            timestamp="2026-01-01T00:00:00",
            duration_ms=100,
            parent_step_id=None,
            metadata={"key": "value"},
        )

    def test_to_dict(self, step: ReasoningStep):
        d = step.to_dict()
        assert d["step_id"] == "step-001"
        assert d["step_type"] == "analysis"
        assert d["agent_name"] == "planner"
        assert d["evidence"] == ["evidence1", "evidence2"]
        assert d["confidence"] == "high"
        assert d["duration_ms"] == 100
        assert d["parent_step_id"] is None
        assert d["metadata"] == {"key": "value"}

    def test_to_dict_defaults(self):
        step = ReasoningStep(
            step_id="step-002",
            step_type=ReasoningStepType.DECISION,
            agent_name="coder",
            description="Decide approach",
            reasoning="Chose iterative",
            evidence=[],
            conclusion="Iterative approach",
            confidence=ConfidenceLevel.MEDIUM,
            timestamp="2026-01-01T00:00:00",
        )
        d = step.to_dict()
        assert d["duration_ms"] == 0
        assert d["parent_step_id"] is None
        assert d["metadata"] == {}

    def test_to_dict_with_parent(self):
        step = ReasoningStep(
            step_id="step-003",
            step_type=ReasoningStepType.EXECUTION,
            agent_name="coder",
            description="Execute",
            reasoning="Running code",
            evidence=[],
            conclusion="Done",
            confidence=ConfidenceLevel.HIGH,
            timestamp="2026-01-01T00:00:00",
            parent_step_id="step-001",
        )
        assert step.to_dict()["parent_step_id"] == "step-001"


# ===== ChainOfThought =====


class TestChainOfThought:
    @pytest.fixture()
    def chain(self) -> ChainOfThought:
        return ChainOfThought(
            chain_id="chain-abc",
            task_description="Write tests",
            agent_name="coder",
        )

    def test_init_defaults(self, chain: ChainOfThought):
        assert chain.steps == []
        assert chain.start_time == ""
        assert chain.end_time is None
        assert chain.status == "running"
        assert chain.final_conclusion == ""
        assert chain.metadata == {}

    def test_add_step(self, chain: ChainOfThought):
        step = ReasoningStep(
            step_id="step-001",
            step_type=ReasoningStepType.ANALYSIS,
            agent_name="coder",
            description="test",
            reasoning="test",
            evidence=[],
            conclusion="test",
            confidence=ConfidenceLevel.HIGH,
            timestamp="2026-01-01T00:00:00",
        )
        chain.add_step(step)
        assert len(chain.steps) == 1
        assert chain.steps[0].step_id == "step-001"

    def test_complete(self, chain: ChainOfThought):
        chain.complete("All done")
        assert chain.status == "completed"
        assert chain.end_time is not None
        assert chain.final_conclusion == "All done"

    def test_complete_empty_conclusion(self, chain: ChainOfThought):
        chain.complete()
        assert chain.final_conclusion == ""

    def test_fail(self, chain: ChainOfThought):
        chain.fail("Timeout")
        assert chain.status == "failed"
        assert chain.end_time is not None
        assert "Timeout" in chain.final_conclusion

    def test_fail_empty_error(self, chain: ChainOfThought):
        chain.fail()
        assert "失败" in chain.final_conclusion

    def test_to_dict(self, chain: ChainOfThought):
        step = ReasoningStep(
            step_id="step-001",
            step_type=ReasoningStepType.PLANNING,
            agent_name="coder",
            description="plan",
            reasoning="plan reasoning",
            evidence=[],
            conclusion="plan done",
            confidence=ConfidenceLevel.MEDIUM,
            timestamp="2026-01-01T00:00:00",
        )
        chain.add_step(step)
        d = chain.to_dict()
        assert d["chain_id"] == "chain-abc"
        assert len(d["steps"]) == 1
        assert d["steps"][0]["step_type"] == "planning"
        assert d["status"] == "running"


# ===== ChainOfThoughtRecorder =====


class TestChainOfThoughtRecorder:
    @pytest.fixture()
    def recorder(self, tmp_path: Path) -> ChainOfThoughtRecorder:
        return ChainOfThoughtRecorder(storage_dir=tmp_path / "chains")

    def test_init_creates_dir(self, tmp_path: Path):
        storage = tmp_path / "new_dir"
        ChainOfThoughtRecorder(storage_dir=storage)
        assert storage.exists()

    def test_start_chain(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Write code", "coder")
        assert chain.task_description == "Write code"
        assert chain.agent_name == "coder"
        assert chain.chain_id.startswith("chain-")
        assert chain.start_time != ""
        assert chain.chain_id in recorder.active_chains

    def test_start_chain_with_metadata(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "agent", metadata={"priority": "high"})
        assert chain.metadata == {"priority": "high"}

    def test_add_step(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        step = recorder.add_step(
            chain_id=chain.chain_id,
            step_type=ReasoningStepType.ANALYSIS,
            description="Analyze",
            reasoning="Need to check",
            evidence=["doc1"],
            conclusion="Checked",
            confidence=ConfidenceLevel.HIGH,
        )
        assert step is not None
        assert step.step_id == "step-001"
        assert step.step_type == ReasoningStepType.ANALYSIS
        assert step.evidence == ["doc1"]
        assert len(chain.steps) == 1

    def test_add_step_default_evidence(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        step = recorder.add_step(
            chain_id=chain.chain_id,
            step_type=ReasoningStepType.EXECUTION,
            description="Run",
            reasoning="Execute code",
        )
        assert step is not None
        assert step.evidence == []
        assert step.confidence == ConfidenceLevel.MEDIUM

    def test_add_step_with_parent(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        recorder.add_step(
            chain_id=chain.chain_id,
            step_type=ReasoningStepType.ANALYSIS,
            description="Analyze",
            reasoning="Check",
        )
        step2 = recorder.add_step(
            chain_id=chain.chain_id,
            step_type=ReasoningStepType.EXECUTION,
            description="Execute",
            reasoning="Do it",
            parent_step_id="step-001",
        )
        assert step2 is not None
        assert step2.parent_step_id == "step-001"

    def test_add_step_invalid_chain(self, recorder: ChainOfThoughtRecorder):
        result = recorder.add_step(
            chain_id="nonexistent",
            step_type=ReasoningStepType.ANALYSIS,
            description="Test",
            reasoning="Test",
        )
        assert result is None

    def test_complete_chain(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        recorder.complete_chain(chain.chain_id, "Done")
        assert chain.status == "completed"
        assert chain.final_conclusion == "Done"
        # Verify saved to file
        saved = recorder.storage_dir / f"{chain.chain_id}.json"
        assert saved.exists()
        data = json.loads(saved.read_text(encoding="utf-8"))
        assert data["chain_id"] == chain.chain_id

    def test_complete_chain_empty_conclusion(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        recorder.complete_chain(chain.chain_id)
        assert chain.final_conclusion == ""

    def test_complete_chain_invalid(self, recorder: ChainOfThoughtRecorder):
        # Should not raise
        recorder.complete_chain("nonexistent", "Done")

    def test_fail_chain(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        recorder.fail_chain(chain.chain_id, "Error occurred")
        assert chain.status == "failed"
        assert "Error occurred" in chain.final_conclusion
        saved = recorder.storage_dir / f"{chain.chain_id}.json"
        assert saved.exists()

    def test_fail_chain_invalid(self, recorder: ChainOfThoughtRecorder):
        recorder.fail_chain("nonexistent", "Error")

    def test_get_chain(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder")
        assert recorder.get_chain(chain.chain_id) is chain

    def test_get_chain_invalid(self, recorder: ChainOfThoughtRecorder):
        assert recorder.get_chain("nonexistent") is None

    def test_list_chains(self, recorder: ChainOfThoughtRecorder):
        recorder.start_chain("Task1", "coder")
        recorder.start_chain("Task2", "planner")
        chains = recorder.list_chains()
        assert len(chains) == 2

    def test_list_chains_filter_agent(self, recorder: ChainOfThoughtRecorder):
        recorder.start_chain("Task1", "coder")
        recorder.start_chain("Task2", "planner")
        chains = recorder.list_chains(agent_name="coder")
        assert len(chains) == 1
        assert chains[0].agent_name == "coder"

    def test_list_chains_no_match(self, recorder: ChainOfThoughtRecorder):
        recorder.start_chain("Task", "coder")
        assert recorder.list_chains(agent_name="reviewer") == []

    def test_save_chain_json_content(self, recorder: ChainOfThoughtRecorder):
        chain = recorder.start_chain("Task", "coder", metadata={"key": "val"})
        recorder.add_step(
            chain_id=chain.chain_id,
            step_type=ReasoningStepType.ANALYSIS,
            description="Analyze",
            reasoning="Check",
            evidence=["e1"],
            conclusion="Done",
        )
        recorder.complete_chain(chain.chain_id, "Finished")
        saved = recorder.storage_dir / f"{chain.chain_id}.json"
        data = json.loads(saved.read_text(encoding="utf-8"))
        assert data["task_description"] == "Task"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["evidence"] == ["e1"]
        assert data["status"] == "completed"


# ===== ChainVisualizer =====


class TestChainVisualizer:
    @pytest.fixture()
    def chain(self) -> ChainOfThought:
        c = ChainOfThought(
            chain_id="chain-test",
            task_description="Test task",
            agent_name="coder",
            start_time="2026-01-01T00:00:00",
        )
        c.add_step(
            ReasoningStep(
                step_id="step-001",
                step_type=ReasoningStepType.ANALYSIS,
                agent_name="coder",
                description="Analyze problem",
                reasoning="Need to understand the problem first",
                evidence=["doc1", "doc2"],
                conclusion="Understood",
                confidence=ConfidenceLevel.HIGH,
                timestamp="2026-01-01T00:00:01",
            )
        )
        c.add_step(
            ReasoningStep(
                step_id="step-002",
                step_type=ReasoningStepType.EXECUTION,
                agent_name="coder",
                description="Execute solution",
                reasoning="x" * 150,  # Long reasoning to test truncation
                evidence=[],
                conclusion="Executed",
                confidence=ConfidenceLevel.LOW,
                timestamp="2026-01-01T00:00:02",
                parent_step_id="step-001",
            )
        )
        c.complete("All done")
        return c

    def test_to_text(self, chain: ChainOfThought):
        text = ChainVisualizer.to_text(chain)
        assert "chain-test" in text
        assert "Test task" in text
        assert "ANALYSIS" in text
        assert "EXECUTION" in text
        assert "Understood" in text
        assert "最终结论" in text
        assert "All done" in text

    def test_to_text_long_reasoning_truncated(self, chain: ChainOfThought):
        text = ChainVisualizer.to_text(chain)
        # Long reasoning should be truncated with ...
        assert "..." in text

    def test_to_text_evidence(self, chain: ChainOfThought):
        text = ChainVisualizer.to_text(chain)
        assert "doc1" in text

    def test_to_text_no_final_conclusion(self):
        chain = ChainOfThought(
            chain_id="chain-x",
            task_description="No conclusion",
            agent_name="coder",
        )
        text = ChainVisualizer.to_text(chain)
        assert "最终结论" not in text

    def test_to_text_no_evidence_no_conclusion(self):
        chain = ChainOfThought(
            chain_id="chain-y",
            task_description="Minimal",
            agent_name="coder",
            start_time="2026-01-01T00:00:00",
        )
        chain.add_step(
            ReasoningStep(
                step_id="step-001",
                step_type=ReasoningStepType.REFLECTION,
                agent_name="coder",
                description="Reflect",
                reasoning="Short",
                evidence=[],
                conclusion="",
                confidence=ConfidenceLevel.UNCERTAIN,
                timestamp="2026-01-01T00:00:00",
            )
        )
        text = ChainVisualizer.to_text(chain)
        assert "REFLECTION" in text
        assert "uncertain" in text

    def test_to_html(self, chain: ChainOfThought):
        html = ChainVisualizer.to_html(chain)
        assert "<html>" in html
        assert "chain-test" in html
        assert "ANALYSIS" in html.upper() or "analysis" in html
        assert "#3b82f6" in html  # ANALYSIS color

    def test_to_html_no_conclusion(self):
        chain = ChainOfThought(
            chain_id="chain-x",
            task_description="No conclusion",
            agent_name="coder",
        )
        html = ChainVisualizer.to_html(chain)
        assert "最终结论" not in html

    def test_to_html_step_with_conclusion(self, chain: ChainOfThought):
        html = ChainVisualizer.to_html(chain)
        assert "Understood" in html

    def test_to_html_step_without_conclusion(self):
        chain = ChainOfThought(
            chain_id="chain-x",
            task_description="Test",
            agent_name="coder",
        )
        chain.add_step(
            ReasoningStep(
                step_id="step-001",
                step_type=ReasoningStepType.OBSERVATION,
                agent_name="coder",
                description="Observe",
                reasoning="See result",
                evidence=[],
                conclusion="",  # No conclusion
                confidence=ConfidenceLevel.MEDIUM,
                timestamp="2026-01-01T00:00:00",
            )
        )
        html = ChainVisualizer.to_html(chain)
        # Step without conclusion should not have conclusion div
        assert "<b>结论:</b>" not in html

    def test_to_mermaid(self, chain: ChainOfThought):
        mermaid = ChainVisualizer.to_mermaid(chain)
        assert "graph TD" in mermaid
        assert "step_001" in mermaid
        assert "step_002" in mermaid
        # step-002 has parent_step_id="step-001"
        assert "step_001 --> step_002" in mermaid

    def test_to_mermaid_no_parent(self):
        chain = ChainOfThought(
            chain_id="chain-x",
            task_description="Test",
            agent_name="coder",
        )
        chain.add_step(
            ReasoningStep(
                step_id="step-001",
                step_type=ReasoningStepType.PLANNING,
                agent_name="coder",
                description="Plan",
                reasoning="Think",
                evidence=[],
                conclusion="Plan done",
                confidence=ConfidenceLevel.HIGH,
                timestamp="2026-01-01T00:00:00",
            )
        )
        mermaid = ChainVisualizer.to_mermaid(chain)
        assert "-->" not in mermaid

    def test_to_text_all_step_types(self):
        """Verify all step types have icons"""
        chain = ChainOfThought(
            chain_id="chain-all",
            task_description="All types",
            agent_name="coder",
        )
        for st in ReasoningStepType:
            chain.add_step(
                ReasoningStep(
                    step_id=f"step-{st.value}",
                    step_type=st,
                    agent_name="coder",
                    description=f"Step {st.value}",
                    reasoning="test",
                    evidence=[],
                    conclusion="done",
                    confidence=ConfidenceLevel.MEDIUM,
                    timestamp="2026-01-01T00:00:00",
                )
            )
        text = ChainVisualizer.to_text(chain)
        for st in ReasoningStepType:
            assert st.value.upper() in text


# ===== 便捷函数 =====


class TestConvenienceFunctions:
    def test_create_recorder(self, tmp_path: Path):
        recorder = create_recorder()
        assert isinstance(recorder, ChainOfThoughtRecorder)

    def test_visualize_chain_text(self):
        chain = ChainOfThought(
            chain_id="chain-v",
            task_description="Visualize",
            agent_name="coder",
        )
        result = visualize_chain(chain, format="text")
        assert "chain-v" in result

    def test_visualize_chain_html(self):
        chain = ChainOfThought(
            chain_id="chain-v",
            task_description="Visualize",
            agent_name="coder",
        )
        result = visualize_chain(chain, format="html")
        assert "<html>" in result

    def test_visualize_chain_mermaid(self):
        chain = ChainOfThought(
            chain_id="chain-v",
            task_description="Visualize",
            agent_name="coder",
        )
        result = visualize_chain(chain, format="mermaid")
        assert "graph TD" in result

    def test_visualize_chain_default_format(self):
        chain = ChainOfThought(
            chain_id="chain-v",
            task_description="Visualize",
            agent_name="coder",
        )
        result = visualize_chain(chain)
        assert "chain-v" in result  # defaults to text
