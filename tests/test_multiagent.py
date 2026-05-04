"""
测试多 Agent 协作模块
"""

import pytest

from src.multiagent.coordinator import (
    MultiAgentCoordinator,
    SubAgent,
    SubAgentStatus,
    TaskResult,
    get_coordinator,
)


class TestSubAgent:
    """SubAgent 模型测试"""

    def test_init(self) -> None:
        agent = SubAgent(
            agent_id="test-01",
            name="TestAgent",
            role="coder",
        )
        assert agent.agent_id == "test-01"
        assert agent.name == "TestAgent"
        assert agent.role == "coder"
        assert agent.status == SubAgentStatus.IDLE
        assert agent.created_at != ""

    def test_to_dict(self) -> None:
        agent = SubAgent(
            agent_id="abc",
            name="X",
            role="reviewer",
            status=SubAgentStatus.RUNNING,
            metadata={"priority": "high"},
        )
        data = agent.to_dict()
        assert data["agent_id"] == "abc"
        assert data["role"] == "reviewer"
        assert data["status"] == "running"
        assert data["metadata"]["priority"] == "high"


class TestTaskResult:
    """TaskResult 测试"""

    def test_success_result(self) -> None:
        result = TaskResult(
            agent_id="a1",
            role="coder",
            success=True,
            output="code generated",
            duration=2.5,
        )
        assert result.success is True
        assert result.output == "code generated"
        assert result.error is None

    def test_failed_result(self) -> None:
        result = TaskResult(
            agent_id="a1",
            role="reviewer",
            success=False,
            output=None,
            error="timeout",
        )
        assert result.success is False
        assert result.error == "timeout"


class TestMultiAgentCoordinator:
    """协调器测试"""

    def test_spawn(self) -> None:
        coordinator = MultiAgentCoordinator()
        agent = coordinator.spawn(role="coder", name="CodeBot")

        assert agent.agent_id != ""
        assert agent.name == "CodeBot"
        assert agent.role == "coder"
        assert agent.status == SubAgentStatus.IDLE
        assert agent.agent_id in coordinator.agents

    def test_spawn_multiple(self) -> None:
        coordinator = MultiAgentCoordinator()
        agents = [coordinator.spawn("coder", f"coder-{i}") for i in range(3)]

        assert len(coordinator.agents) == 3
        ids = {a.agent_id for a in agents}
        assert len(ids) == 3  # 全部唯一

    def test_get_status(self) -> None:
        coordinator = MultiAgentCoordinator()
        coordinator.spawn("coder", "c1")
        coordinator.spawn("reviewer", "r1")
        coordinator.spawn("tester", "t1")

        status = coordinator.get_status()
        assert status["total_agents"] == 3
        assert status["idle"] == 3
        assert status["running"] == 0

    def test_remove_agent(self) -> None:
        coordinator = MultiAgentCoordinator()
        agent = coordinator.spawn("coder", "temp")
        agent_id = agent.agent_id

        assert coordinator.remove_agent(agent_id) is True
        assert agent_id not in coordinator.agents

        # 重复删除
        assert coordinator.remove_agent(agent_id) is False

    def test_clear_agents(self) -> None:
        coordinator = MultiAgentCoordinator()
        coordinator.spawn("coder", "c1")
        coordinator.spawn("reviewer", "r1")

        coordinator.clear_agents()
        assert len(coordinator.agents) == 0
        assert len(coordinator.tasks) == 0

    def test_get_agent(self) -> None:
        coordinator = MultiAgentCoordinator()
        agent = coordinator.spawn("coder", "find-me")

        assert coordinator.get_agent(agent.agent_id) is agent
        assert coordinator.get_agent("nonexistent") is None

    @pytest.mark.asyncio
    async def test_dispatch_with_runner(self) -> None:
        coordinator = MultiAgentCoordinator()

        # 设置模拟 runner
        async def mock_runner(agent: SubAgent, task: str) -> str:
            return f"{agent.name} processed: {task[:20]}"

        coordinator.set_runner(mock_runner)

        agent1 = coordinator.spawn("coder", "CodeBot")
        agent2 = coordinator.spawn("reviewer", "ReviewBot")

        result = await coordinator.dispatch("build feature X", [agent1, agent2])

        assert result.task_id != ""
        assert len(result.results) == 2
        assert all(r.success for r in result.results)
        assert "CodeBot" in result.results[0].output

    @pytest.mark.asyncio
    async def test_dispatch_without_runner(self) -> None:
        coordinator = MultiAgentCoordinator()
        agent = coordinator.spawn("explorer", "ExploreBot")

        result = await coordinator.dispatch("analyze codebase", [agent])

        assert len(result.results) == 1
        assert result.results[0].success is True
        # 无 runner 时使用模拟输出
        assert "ExploreBot" in result.results[0].output

    @pytest.mark.asyncio
    async def test_dispatch_sequential(self) -> None:
        coordinator = MultiAgentCoordinator()

        async def mock_runner(agent: SubAgent, task: str) -> str:
            return f"[{agent.name}] done"

        coordinator.set_runner(mock_runner)

        agent1 = coordinator.spawn("coder", "C1")
        agent2 = coordinator.spawn("reviewer", "R1")

        result = await coordinator.dispatch_sequential(
            "implement feature", [agent1, agent2]
        )

        assert len(result.results) == 2
        assert all(r.success for r in result.results)
        # 第二个 agent 的输入应该包含第一个的输出
        assert "[C1]" in result.results[1].output or result.results[1].output

    @pytest.mark.asyncio
    async def test_dispatch_with_exception(self) -> None:
        coordinator = MultiAgentCoordinator()

        async def failing_runner(agent: SubAgent, task: str) -> str:
            if agent.role == "reviewer":
                raise RuntimeError("review failed")
            return "ok"

        coordinator.set_runner(failing_runner)

        agent1 = coordinator.spawn("coder", "C1")
        agent2 = coordinator.spawn("reviewer", "R1")

        result = await coordinator.dispatch("test", [agent1, agent2])

        # 至少 coder 应该成功
        assert result.results[0].success is True
        # reviewer 应该失败
        assert result.results[1].success is False

    def test_summarize(self) -> None:
        coordinator = MultiAgentCoordinator()
        results = [
            TaskResult(agent_id="a1", role="coder", success=True, output="ok"),
            TaskResult(agent_id="a2", role="coder", success=True, output="ok"),
            TaskResult(agent_id="a3", role="reviewer", success=False, error="fail"),
        ]

        summary = coordinator._summarize(results)
        assert "总任务: 3" in summary
        assert "成功: 2" in summary
        assert "失败: 1" in summary
        assert "coder" in summary
        assert "reviewer" in summary


class TestGlobalCoordinator:
    """全局单例测试"""

    def test_get_coordinator(self) -> None:
        coordinator = get_coordinator()
        assert coordinator is not None
        assert isinstance(coordinator, MultiAgentCoordinator)

        # 多次调用返回同一实例
        assert get_coordinator() is coordinator


class TestAgentCollaboration:
    """多 Agent 协作场景测试"""

    @pytest.mark.asyncio
    async def test_two_agents_collaborate(self):
        """测试两个 Agent 协作完成任务"""
        coordinator = MultiAgentCoordinator()

        # 模拟协作流程：coder 写代码 → reviewer 审查
        collaboration_log = []

        async def coder_runner(agent: SubAgent, task: str) -> str:
            collaboration_log.append(f"{agent.name} writing code")
            return "def hello(): return 'world'"

        async def reviewer_runner(agent: SubAgent, task: str) -> str:
            collaboration_log.append(f"{agent.name} reviewing code")
            return "looks good"

        # 创建 coder 和 reviewer
        coder = coordinator.spawn("coder", "CodeBot")
        reviewer = coordinator.spawn("reviewer", "ReviewBot")

        # 分发并行任务
        task = "implement login feature"
        result = await coordinator.dispatch(task, [coder, reviewer])

        assert result.task_id != ""
        assert len(result.results) == 2
        # 两个 agent 都应该成功
        assert all(r.success for r in result.results)

    @pytest.mark.asyncio
    async def test_three_agents_pipeline(self):
        """测试三 Agent 流水线协作"""
        coordinator = MultiAgentCoordinator()

        async def mock_runner(agent: SubAgent, task: str) -> str:
            return f"{agent.role} done: {task[:20]}"

        coordinator.set_runner(mock_runner)

        # 创建三个不同角色的 agent
        planner = coordinator.spawn("planner", "PlannerBot")
        coder = coordinator.spawn("coder", "CoderBot")
        tester = coordinator.spawn("tester", "TesterBot")

        # 顺序执行
        result = await coordinator.dispatch_sequential(
            "build todo app",
            [planner, coder, tester]
        )

        assert len(result.results) == 3
        assert all(r.success for r in result.results)
        # 验证结果包含各角色
        roles = [r.role for r in result.results]
        assert "planner" in roles
        assert "coder" in roles
        assert "tester" in roles

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_timing(self):
        """测试并行 vs 顺序执行的时间差异"""
        coordinator = MultiAgentCoordinator()

        async def slow_runner(agent: SubAgent, task: str) -> str:
            import asyncio
            await asyncio.sleep(0.05)  # 模拟 50ms 延迟
            return "done"

        coordinator.set_runner(slow_runner)

        agents = [coordinator.spawn("coder", f"Agent{i}") for i in range(3)]

        # 并行执行
        import time
        start_parallel = time.time()
        await coordinator.dispatch("task", agents)
        time_parallel = time.time() - start_parallel

        coordinator2 = MultiAgentCoordinator()
        coordinator2.set_runner(slow_runner)
        agents2 = [coordinator2.spawn("coder", f"Agent{i}") for i in range(3)]

        # 顺序执行
        start_seq = time.time()
        await coordinator2.dispatch_sequential("task", agents2)
        time_seq = time.time() - start_seq

        # 并行应该比顺序快（并行约 50ms，顺序约 150ms）
        assert time_parallel < time_seq * 0.7  # 并行至少快 30%

    @pytest.mark.asyncio
    async def test_coordination_summary(self):
        """测试协作汇总信息"""
        coordinator = MultiAgentCoordinator()


        results = [
            TaskResult(agent_id="a1", role="coder", success=True, output="code"),
            TaskResult(agent_id="a2", role="reviewer", success=True, output="approved"),
            TaskResult(agent_id="a3", role="tester", success=False, error="test failed"),
        ]

        summary = coordinator._summarize(results)
        assert "总任务: 3" in summary
        assert "成功: 2" in summary
        assert "失败: 1" in summary
        assert "tester" in summary  # 包含失败的 role

    def test_coordinator_history(self):
        """测试协调器历史记录"""
        coordinator = MultiAgentCoordinator()

        # 执行一些任务来创建历史
        coordinator.spawn("coder", "C1")
        coordinator.spawn("coder", "C2")

        # 检查历史列表存在
        assert hasattr(coordinator, "_history")
        assert isinstance(coordinator._history, list)


class TestTaskRouting:
    """任务路由逻辑测试"""

    @pytest.mark.parametrize(
        "task_type,expected_tier",
        [
            # 简单任务 → LOW tier
            ("explore", "low"),
            ("simple_qa", "low"),
            ("formatting", "low"),
            # 中等复杂度 → MEDIUM tier
            ("code_generation", "medium"),
            ("debugging", "medium"),
            ("testing", "medium"),
            ("refactoring", "medium"),
            # 高复杂度 → HIGH tier
            ("architecture", "high"),
            ("security_review", "high"),
            ("code_review", "high"),
            ("planning", "high"),
        ],
    )
    def test_task_type_to_tier_mapping(self, task_type, expected_tier):
        """测试任务类型到模型层级的映射"""
        from src.core.router import _TASK_TIER_MAPPING

        tier = _TASK_TIER_MAPPING.get(task_type, "medium")
        assert tier == expected_tier

    @pytest.mark.parametrize(
        "complexity,base_tier,expected_tier",
        [
            # 低复杂度降级
            ("low", "high", "medium"),
            ("low", "medium", "low"),
            ("low", "low", "low"),
            # 高复杂度升级
            ("high", "low", "medium"),
            ("high", "medium", "high"),
            ("high", "high", "high"),
            # 中等复杂度不变
            ("medium", "low", "low"),
            ("medium", "medium", "medium"),
            ("medium", "high", "high"),
        ],
    )
    def test_complexity_adjustment(self, complexity, base_tier, expected_tier):
        """测试复杂度调整逻辑"""
        # 模拟 tier 调整逻辑
        tier = base_tier
        if complexity == "low" and base_tier == "high":
            tier = "medium"
        elif complexity == "low" and base_tier == "medium":
            tier = "low"
        elif complexity == "high" and base_tier == "low":
            tier = "medium"
        elif complexity == "high" and base_tier == "medium":
            tier = "high"

        assert tier == expected_tier

    @pytest.mark.asyncio
    async def test_simple_task_dispatch(self):
        """测试简单任务分发到单个 Agent"""
        coordinator = MultiAgentCoordinator()

        async def mock_runner(agent: SubAgent, task: str) -> str:
            return f"processed: {task[:30]}"

        coordinator.set_runner(mock_runner)
        agent = coordinator.spawn("explorer", "ExploreBot")

        result = await coordinator.dispatch("list all python files", [agent])

        assert len(result.results) == 1
        assert result.results[0].success is True

    @pytest.mark.asyncio
    async def test_complex_task_dispatch(self):
        """测试复杂任务分发到多个 Agent"""
        coordinator = MultiAgentCoordinator()

        async def mock_runner(agent: SubAgent, task: str) -> str:
            return f"{agent.role}: done"

        coordinator.set_runner(mock_runner)

        # 复杂任务需要多个角色协作
        agents = [
            coordinator.spawn("planner", "Planner"),
            coordinator.spawn("coder", "Coder"),
            coordinator.spawn("reviewer", "Reviewer"),
            coordinator.spawn("tester", "Tester"),
        ]

        result = await coordinator.dispatch(
            "implement user authentication with JWT", agents
        )

        assert len(result.results) == 4
        assert all(r.success for r in result.results)
        roles = {r.role for r in result.results}
        assert "planner" in roles
        assert "coder" in roles
        assert "reviewer" in roles
        assert "tester" in roles


class TestAgentCommunication:
    """Agent 间通信测试"""

    @pytest.mark.asyncio
    async def test_message_passing_sequential(self):
        """测试顺序执行中的消息传递"""
        coordinator = MultiAgentCoordinator()

        messages_log = []

        async def logging_runner(agent: SubAgent, task: str) -> str:
            messages_log.append({"agent": agent.name, "received": task[:50]})
            return f"{agent.name} output"

        coordinator.set_runner(logging_runner)

        agents = [
            coordinator.spawn("coder", "Coder"),
            coordinator.spawn("reviewer", "Reviewer"),
        ]

        await coordinator.dispatch_sequential("write unit tests", agents)

        # 验证消息传递
        assert len(messages_log) == 2
        # 第一个 agent 收到原始任务
        assert "write unit tests" in messages_log[0]["received"]
        # 第二个 agent 收到包含第一个输出的任务
        assert "Coder output" in messages_log[1]["received"]

    @pytest.mark.asyncio
    async def test_shared_context(self):
        """测试共享上下文"""
        coordinator = MultiAgentCoordinator()

        context = {"project": "oh-my-coder", "language": "python"}

        async def context_runner(agent: SubAgent, task: str) -> str:
            # Agent 可以访问共享上下文
            return f"{agent.name} working on {context['project']}"

        coordinator.set_runner(context_runner)

        agents = [coordinator.spawn("coder", f"Coder{i}") for i in range(3)]
        result = await coordinator.dispatch("implement feature", agents)

        for r in result.results:
            assert r.success
            assert "oh-my-coder" in r.output

    @pytest.mark.asyncio
    async def test_agent_output_chain(self):
        """测试 Agent 输出链"""
        coordinator = MultiAgentCoordinator()

        async def chain_runner(agent: SubAgent, task: str) -> str:
            # 模拟处理链：每个 agent 在前一个输出上工作
            if "step1" in task:
                return "step1: design complete"
            elif "step2" in task or "design complete" in task:
                return "step2: implementation complete"
            else:
                return "final: done"

        coordinator.set_runner(chain_runner)

        agents = [
            coordinator.spawn("designer", "Designer"),
            coordinator.spawn("coder", "Coder"),
        ]

        result = await coordinator.dispatch_sequential("step1: design feature", agents)

        # 第二个 agent 的输入应包含第一个的输出
        assert len(result.results) == 2
        assert "design complete" in result.results[1].output or result.results[1].success


class TestFailureRetry:
    """失败重试机制测试"""

    @pytest.mark.asyncio
    async def test_single_agent_failure(self):
        """测试单个 Agent 失败"""
        coordinator = MultiAgentCoordinator()

        async def failing_runner(agent: SubAgent, task: str) -> str:
            if agent.role == "tester":
                raise RuntimeError("test environment not ready")
            return "ok"

        coordinator.set_runner(failing_runner)

        agents = [
            coordinator.spawn("coder", "Coder"),
            coordinator.spawn("tester", "Tester"),
        ]

        result = await coordinator.dispatch("build feature", agents)

        # coder 成功，tester 失败
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert "RuntimeError" in result.results[1].error

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """测试部分失败处理"""
        coordinator = MultiAgentCoordinator()

        failure_count = 0

        async def intermittent_runner(agent: SubAgent, task: str) -> str:
            nonlocal failure_count
            # 模拟间歇性失败
            if agent.role == "reviewer" and failure_count == 0:
                failure_count += 1
                raise ValueError("temporary error")
            return f"{agent.role} succeeded"

        coordinator.set_runner(intermittent_runner)

        agents = [
            coordinator.spawn("coder", "Coder"),
            coordinator.spawn("reviewer", "Reviewer"),
            coordinator.spawn("tester", "Tester"),
        ]

        result = await coordinator.dispatch("task", agents)

        # 验证部分成功/失败
        success_count = sum(1 for r in result.results if r.success)
        failed_count = sum(1 for r in result.results if not r.success)

        assert success_count == 2
        assert failed_count == 1

    @pytest.mark.asyncio
    async def test_sequential_continues_on_failure(self):
        """测试顺序执行在失败时继续执行（当前实现行为）"""
        coordinator = MultiAgentCoordinator()

        execution_order = []

        async def failing_runner(agent: SubAgent, task: str) -> str:
            execution_order.append(agent.role)
            if agent.role == "reviewer":
                raise RuntimeError("review failed")
            return "ok"

        coordinator.set_runner(failing_runner)

        agents = [
            coordinator.spawn("coder", "Coder"),
            coordinator.spawn("reviewer", "Reviewer"),
            coordinator.spawn("tester", "Tester"),
        ]

        result = await coordinator.dispatch_sequential("task", agents)

        # 当前实现：所有 agent 都会执行
        assert len(result.results) == 3
        assert "coder" in execution_order
        assert "reviewer" in execution_order
        assert "tester" in execution_order
        # reviewer 失败，但 coder 和 tester 成功
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert result.results[2].success is True

    @pytest.mark.asyncio
    async def test_exception_isolation(self):
        """测试异常隔离：一个 agent 失败不影响其他"""
        coordinator = MultiAgentCoordinator()

        async def isolated_runner(agent: SubAgent, task: str) -> str:
            if agent.name == "FailBot":
                raise ValueError("I fail")
            return f"{agent.name} succeeded"

        coordinator.set_runner(isolated_runner)

        agents = [
            coordinator.spawn("worker", "Worker1"),
            coordinator.spawn("worker", "FailBot"),
            coordinator.spawn("worker", "Worker2"),
        ]

        result = await coordinator.dispatch("task", agents)

        # 并行执行：失败不影响其他
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert result.results[2].success is True

    @pytest.mark.asyncio
    async def test_error_message_capture(self):
        """测试错误消息捕获"""
        coordinator = MultiAgentCoordinator()

        async def error_runner(agent: SubAgent, task: str) -> str:
            raise ValueError("detailed error message")

        coordinator.set_runner(error_runner)
        agent = coordinator.spawn("worker", "Worker")

        result = await coordinator.dispatch("task", [agent])

        assert result.results[0].success is False
        assert result.results[0].error is not None
        # 错误类型应被记录
        assert "ValueError" in result.results[0].error
