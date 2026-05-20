"""Tests for QATesterAgent."""

import pytest
from src.agents.qa_tester import QATesterAgent
from src.agents.base import AgentOutput, AgentStatus


def test_agent_properties():
    """Test agent class properties."""
    agent = QATesterAgent()
    assert agent.name == "qa-tester"
    assert agent.lane.value == "domain"
    assert agent.default_tier == "medium"
    assert agent.icon == "🛠️"
    assert "bash" in agent.tools


def test_system_prompt():
    """Test system prompt contains key content."""
    agent = QATesterAgent()
    prompt = agent.system_prompt
    assert "QA" in prompt
    assert "测试" in prompt
    assert "CLI" in prompt


def test_post_process():
    """Test _post_process method."""
    agent = QATesterAgent()
    result = "## 测试结果\n\n| TC-01 | ✅ PASS |"
    output = agent._post_process(result, None)
    
    assert output.status == AgentStatus.COMPLETED
    assert output.result == result
    assert len(output.recommendations) > 0
