"""测试 summary.py — 任务总结模块"""

import json
from datetime import datetime

import pytest

from src.core.summary import (
    ModelUsage,
    StepRecord,
    TaskSummary,
    generate_summary,
    load_summary,
    print_summary,
    print_summary_compact,
    quick_summary,
    save_summary,
)

# ===== StepRecord =====


class TestStepRecord:
    def test_to_dict(self):
        step = StepRecord(agent="Coder", status="completed", duration=5.0, tokens=100, cost=0.01)
        d = step.to_dict()
        assert d["agent"] == "Coder"
        assert d["status"] == "completed"
        assert d["duration"] == 5.0
        assert d["tokens"] == 100
        assert d["cost"] == 0.01
        assert d["result"] == ""
        assert d["error"] == ""

    def test_defaults(self):
        step = StepRecord(agent="X", status="failed", duration=1.0)
        assert step.tokens == 0
        assert step.cost == 0.0
        assert step.result == ""
        assert step.error == ""

    def test_with_error(self):
        step = StepRecord(agent="A", status="failed", duration=2.0, error="Timeout")
        assert step.error == "Timeout"


# ===== ModelUsage =====


class TestModelUsage:
    def test_defaults(self):
        m = ModelUsage(provider="deepseek", model_name="chat")
        assert m.calls == 0
        assert m.tokens == 0
        assert m.cost == 0.0


# ===== TaskSummary =====


class TestTaskSummary:
    def test_to_dict(self):
        ts = TaskSummary(task="Test", workflow="build")
        d = ts.to_dict()
        assert d["task"] == "Test"
        assert d["workflow"] == "build"
        assert d["success"] is True
        assert d["steps_completed"] == []

    def test_from_dict(self):
        data = {"task": "X", "workflow": "review", "success": False, "errors": ["e1"]}
        ts = TaskSummary.from_dict(data)
        assert ts.task == "X"
        assert ts.success is False
        assert ts.errors == ["e1"]

    def test_defaults(self):
        ts = TaskSummary(task="T", workflow="build")
        assert ts.start_time == ""
        assert ts.total_tokens == 0
        assert ts.agent_count == 0


# ===== generate_summary =====


class TestGenerateSummary:
    def test_basic(self):
        steps = [
            {"agent": "Coder", "status": "completed", "duration": 10.0, "tokens": 500, "result": "Done"},
        ]
        s = generate_summary("Build feature", "build", steps)
        assert s.task == "Build feature"
        assert s.workflow == "build"
        assert s.success is True
        assert s.agent_count == 1
        assert s.total_tokens == 500
        assert len(s.steps_completed) == 1

    def test_failed_step(self):
        steps = [
            {"agent": "Coder", "status": "completed", "duration": 5.0},
            {"agent": "Reviewer", "status": "failed", "duration": 2.0, "error": "Bad code"},
        ]
        s = generate_summary("Task", "build", steps)
        assert s.success is False
        assert len(s.errors) == 1
        assert "Bad code" in s.errors[0]

    def test_cost_estimate(self):
        """When cost=0 and tokens>0, estimate cost"""
        steps = [{"agent": "A", "status": "completed", "duration": 1.0, "tokens": 100000}]
        s = generate_summary("T", "build", steps)
        assert s.total_cost > 0  # estimated

    def test_skipped_step(self):
        steps = [{"agent": "A", "status": "skipped", "duration": 0.0}]
        s = generate_summary("T", "build", steps)
        assert s.success is False  # skipped != completed

    def test_multiple_agents(self):
        steps = [
            {"agent": "Coder", "status": "completed", "duration": 5.0},
            {"agent": "Coder", "status": "completed", "duration": 3.0},
            {"agent": "Reviewer", "status": "completed", "duration": 2.0},
        ]
        s = generate_summary("T", "build", steps)
        assert s.agent_count == 2  # Coder + Reviewer

    def test_with_explicit_times(self):
        start = datetime(2026, 1, 1, 10, 0)
        end = datetime(2026, 1, 1, 10, 5)
        s = generate_summary("T", "build", [], start_time=start, end_time=end)
        assert s.duration_seconds == 300.0

    def test_unknown_agent(self):
        steps = [{"status": "completed", "duration": 1.0}]  # no agent key
        s = generate_summary("T", "build", steps)
        assert s.steps_completed[0]["agent"] == "unknown"

    def test_empty_steps(self):
        s = generate_summary("T", "build", [])
        assert s.success is True
        assert s.agent_count == 0

    def test_recommendations_high_cost(self):
        steps = [{"agent": "A", "status": "completed", "duration": 1.0, "tokens": 0, "cost": 5.0}]
        s = generate_summary("T", "build", steps)
        assert any("成本较高" in r for r in s.recommendations)

    def test_recommendations_medium_cost(self):
        steps = [{"agent": "A", "status": "completed", "duration": 1.0, "tokens": 0, "cost": 0.15}]
        s = generate_summary("T", "build", steps)
        assert any("成本适中" in r for r in s.recommendations)

    def test_recommendations_high_tokens(self):
        steps = [{"agent": "A", "status": "completed", "duration": 1.0, "tokens": 60000}]
        s = generate_summary("T", "build", steps)
        assert any("Token" in r for r in s.recommendations)

    def test_recommendations_long_duration(self):
        steps = [{"agent": "A", "status": "completed", "duration": 70.0}]
        s = generate_summary("T", "build", steps)
        assert any("执行时间较长" in r for r in s.recommendations)

    def test_recommendations_failed(self):
        steps = [{"agent": "A", "status": "failed", "duration": 1.0, "error": "err"}]
        s = generate_summary("T", "build", steps)
        assert any("失败" in r for r in s.recommendations)

    def test_recommendations_no_issue(self):
        steps = [{"agent": "A", "status": "completed", "duration": 5.0, "tokens": 100}]
        s = generate_summary("T", "build", steps)
        assert any("良好" in r for r in s.recommendations)

    def test_models_build(self):
        s = generate_summary("T", "build", [])
        assert len(s.models_used) == 3

    def test_models_review(self):
        s = generate_summary("T", "review", [])
        assert len(s.models_used) == 1

    def test_models_debug(self):
        s = generate_summary("T", "debug", [])
        assert len(s.models_used) == 1

    def test_models_test(self):
        s = generate_summary("T", "test", [])
        assert len(s.models_used) == 2

    def test_models_unknown(self):
        s = generate_summary("T", "custom", [])
        assert len(s.models_used) == 1


# ===== save_summary =====


class TestSaveSummary:
    @pytest.fixture()
    def summary(self):
        return TaskSummary(
            task="Test task",
            workflow="build",
            duration_seconds=10.0,
            total_tokens=500,
            total_cost=0.01,
            success=True,
            steps_completed=[
                {"agent": "Coder", "status": "completed", "duration": 5.0, "tokens": 500, "result": "Done", "cost": 0.0, "error": ""},
            ],
            recommendations=["✅ 执行效率良好"],
        )

    def test_save_json(self, summary, tmp_path):
        path = save_summary(summary, output_dir=tmp_path, format="json")
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["task"] == "Test task"

    def test_save_txt(self, summary, tmp_path):
        path = save_summary(summary, output_dir=tmp_path, format="txt")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Test task" in content
        assert "执行步骤" in content

    def test_save_html(self, summary, tmp_path):
        path = save_summary(summary, output_dir=tmp_path, format="html")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "<html" in content
        assert "Test task" in content

    def test_save_custom_filename(self, summary, tmp_path):
        path = save_summary(summary, output_dir=tmp_path, format="json", filename="custom.json")
        assert path.name == "custom.json"

    def test_save_creates_dir(self, summary, tmp_path):
        subdir = tmp_path / "new"
        path = save_summary(summary, output_dir=subdir, format="json")
        assert subdir.exists()
        assert path.exists()

    def test_save_invalid_format(self, summary, tmp_path):
        with pytest.raises(ValueError, match="不支持的格式"):
            save_summary(summary, output_dir=tmp_path, format="csv")

    def test_save_failed_summary_html(self, tmp_path):
        s = TaskSummary(task="Fail", workflow="debug", success=False)
        path = save_summary(s, output_dir=tmp_path, format="html")
        content = path.read_text(encoding="utf-8")
        assert "失败" in content or "F44336" in content

    def test_save_txt_with_recommendations(self, summary, tmp_path):
        path = save_summary(summary, output_dir=tmp_path, format="txt")
        content = path.read_text(encoding="utf-8")
        assert "优化建议" in content

    def test_save_html_with_recommendations(self, summary, tmp_path):
        path = save_summary(summary, output_dir=tmp_path, format="html")
        content = path.read_text(encoding="utf-8")
        assert "优化建议" in content or "rec" in content


# ===== load_summary =====


class TestLoadSummary:
    def test_load_json(self, tmp_path):
        s = TaskSummary(task="Loaded", workflow="build")
        path = save_summary(s, output_dir=tmp_path, format="json")
        loaded = load_summary(path)
        assert loaded.task == "Loaded"

    def test_load_invalid_format(self, tmp_path):
        txt_file = tmp_path / "summary.csv"
        txt_file.write_text("data", encoding="utf-8")
        with pytest.raises(ValueError, match="不支持的文件格式"):
            load_summary(txt_file)


# ===== print functions =====


class TestPrintSummary:
    def test_print_summary_success(self, capsys):
        s = TaskSummary(task="T", workflow="build", success=True, duration_seconds=5.0)
        print_summary(s)
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "T" in captured.out

    def test_print_summary_failed(self, capsys):
        s = TaskSummary(task="T", workflow="debug", success=False, errors=["err"])
        print_summary(s)
        captured = capsys.readouterr()
        assert "❌" in captured.out

    def test_print_summary_with_steps(self, capsys):
        s = TaskSummary(
            task="T",
            workflow="build",
            steps_completed=[
                {"agent": "AgentCoder", "status": "completed", "duration": 5.0, "tokens": 100, "result": "Result text that is longer than fifty chars for truncation test"},
                {"agent": "AgentReviewer", "status": "failed", "duration": 2.0, "tokens": 50, "result": "Bad"},
            ],
        )
        print_summary(s)
        captured = capsys.readouterr()
        assert "Coder" in captured.out  # "AgentCoder" -> "Coder" after strip
        assert "❌" in captured.out

    def test_print_summary_with_recommendations(self, capsys):
        s = TaskSummary(task="T", workflow="build", recommendations=["💡 Tip"])
        print_summary(s)
        captured = capsys.readouterr()
        assert "优化建议" in captured.out

    def test_print_compact(self, capsys):
        s = TaskSummary(task="A long task name that will be truncated", workflow="build", success=True, duration_seconds=10.0)
        print_summary_compact(s)
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "build" in captured.out

    def test_print_compact_failed(self, capsys):
        s = TaskSummary(task="T", workflow="debug", success=False)
        print_summary_compact(s)
        captured = capsys.readouterr()
        assert "❌" in captured.out


# ===== quick_summary =====


class TestQuickSummary:
    def test_basic(self):
        s = quick_summary("Fast task", "build", 5.0, 100, ["step1", "step2"])
        assert s.task == "Fast task"
        assert s.workflow == "build"
        assert len(s.steps_completed) == 2

    def test_empty_steps(self):
        s = quick_summary("T", "build", 1.0, 0, [])
        assert s.steps_completed == []
