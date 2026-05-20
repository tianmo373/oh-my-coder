"""测试 cli_plan.py — Plan Mode 命令"""

from unittest.mock import patch

from rich.console import Console
from typer.testing import CliRunner

from src.commands.cli_plan import _display_plan, _save_plan, app

runner = CliRunner()


class TestCheckEnv:
    @patch("os.getenv", side_effect=lambda k: "sk-test" if k == "DEEPSEEK_API_KEY" else None)
    def test_has_key(self, mock_env):
        # _check_env is defined inside cli_plan module
        from src.commands import cli_plan
        assert cli_plan._check_env() is True

    @patch("os.getenv", return_value=None)
    def test_no_key(self, mock_env):
        from src.commands import cli_plan
        assert cli_plan._check_env() is False


class TestDisplayPlan:
    def test_empty_plan(self, capsys):
        console = Console(file=__import__("io").StringIO(), force_terminal=True)
        _display_plan({}, [], console)
        # Should not crash

    def test_with_phases(self):
        console = Console(file=__import__("io").StringIO(), force_terminal=True)
        plan_data = {
            "title": "Test Plan",
            "summary": "A test",
            "phases": [
                {
                    "name": "Phase1",
                    "tasks": [
                        {"id": "t1", "title": "Do stuff", "files_to_modify": ["a.py"], "agent": "coder"}
                    ],
                }
            ],
        }
        _display_plan(plan_data, ["t1", "t2"], console)

    def test_long_execution_order(self):
        console = Console(file=__import__("io").StringIO(), force_terminal=True)
        order = [f"t{i}" for i in range(10)]
        _display_plan({"title": "T"}, order, console)


class TestSavePlan:
    def test_save(self, tmp_path):
        output = tmp_path / "plan.md"
        plan_data = {"summary": "test summary", "phases": []}
        console = Console(file=__import__("io").StringIO(), force_terminal=True)
        _save_plan(plan_data, ["a", "b"], output, console)
        content = output.read_text()
        assert "test summary" in content
        assert "a → b" in content


class TestPlanCommand:
    @patch("src.commands.cli_plan._check_env", return_value=False)
    def test_no_env(self, mock_check):
        result = runner.invoke(app, ["test task"])
        assert result.exit_code == 1
