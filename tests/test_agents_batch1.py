"""Batch 1 tests for 5 agent modules (coverage 40-45%)."""

import pytest


@pytest.fixture(params=[
    "src.agents.code_reviewer",
    "src.agents.code_simplifier",
    "src.agents.debugger",
    "src.agents.security",
    "src.agents.git_master",
])
def agent_class(request):
    """Import and instantiate each agent."""
    module_name = request.param
    import importlib
    module = importlib.import_module(module_name)
    # Find the agent class (ends with Agent)
    agent_class = None
    for attr_name in dir(module):
        if attr_name.endswith("Agent") and attr_name != "BaseAgent":
            agent_class = getattr(module, attr_name)
            break
    if agent_class is None:
        pytest.skip(f"No agent class found in {module_name}")
    return agent_class()


class TestAgentProperties:
    """Test basic agent properties."""

    def test_name(self, agent_class):
        """Agent has a name."""
        assert hasattr(agent_class, "name")
        assert isinstance(agent_class.name, str)
        assert len(agent_class.name) > 0

    def test_lane(self, agent_class):
        """Agent has a lane."""
        assert hasattr(agent_class, "lane")

    def test_icon(self, agent_class):
        """Agent has an icon."""
        assert hasattr(agent_class, "icon")
        assert isinstance(agent_class.icon, str)


class TestAgentMethods:
    """Test agent methods."""

    def test_system_prompt(self, agent_class):
        """System prompt is a non-empty string."""
        prompt = agent_class.system_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should have substantial prompt

    def test_post_process(self, agent_class):
        """_post_process returns AgentOutput."""
        from src.agents.base import AgentOutput
        result = "test result"
        output = agent_class._post_process(result, None)
        assert isinstance(output, AgentOutput)
        assert output.status.value in ["completed", "failed", "running"]
