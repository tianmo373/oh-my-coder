"""Tests for src/agents/cost_optimizer.py"""


import pytest

from src.agents.cost_optimizer import (
    MODEL_PRICING,
    Complexity,
    CostEstimate,
    CostOptimizer,
    ModelRecommendation,
    calculate_cost,
    calculate_multi_model_cost,
)


class TestComplexity:
    """Test Complexity enum"""

    def test_low_complexity(self):
        assert Complexity.LOW.value == "low"

    def test_medium_complexity(self):
        assert Complexity.MEDIUM.value == "medium"

    def test_high_complexity(self):
        assert Complexity.HIGH.value == "high"


class TestModelRecommendation:
    """Test ModelRecommendation dataclass"""

    def test_create_recommendation(self):
        rec = ModelRecommendation(
            model="ollama/qwen2.5:7b",
            provider="ollama",
            complexity=Complexity.LOW,
            reason="Test reason",
            estimated_cost=1.0,
            alternatives=[{"model": "gpt-4o-mini", "reason": "备选"}],
        )
        assert rec.model == "ollama/qwen2.5:7b"
        assert rec.provider == "ollama"
        assert rec.complexity == Complexity.LOW
        assert rec.estimated_cost == 1.0
        assert len(rec.alternatives) == 1


class TestCostOptimizerInit:
    """Test CostOptimizer initialization"""

    def test_default_init(self):
        optimizer = CostOptimizer()
        assert optimizer.prefer_local is True

    def test_prefer_local_true(self):
        optimizer = CostOptimizer(prefer_local=True)
        assert optimizer.prefer_local is True

    def test_prefer_local_false(self):
        optimizer = CostOptimizer(prefer_local=False)
        assert optimizer.prefer_local is False


class TestCostOptimizerAnalyzeTask:
    """Test CostOptimizer.analyze_task"""

    def setup_method(self):
        self.optimizer = CostOptimizer()

    def test_simple_task(self):
        result = self.optimizer.analyze_task("修复一个 bug")
        assert result["complexity"] == Complexity.LOW
        assert result["high_score"] == 0
        assert result["medium_score"] == 0

    def test_medium_task_keywords(self):
        result = self.optimizer.analyze_task("添加新的 API 接口")
        assert result["complexity"] == Complexity.MEDIUM
        assert result["medium_score"] >= 2

    def test_high_task_keywords(self):
        result = self.optimizer.analyze_task("重构整个系统架构")
        assert result["complexity"] == Complexity.HIGH
        assert result["high_score"] >= 2

    def test_high_task_refactor(self):
        result = self.optimizer.analyze_task("refactor the authentication system")
        assert result["complexity"] == Complexity.HIGH

    def test_file_count_high(self):
        result = self.optimizer.analyze_task("修改多个文件", file_count=15)
        assert result["complexity"] == Complexity.HIGH
        assert result["high_score"] >= 3

    def test_file_count_medium(self):
        result = self.optimizer.analyze_task("修改几个文件", file_count=7)
        assert result["complexity"] == Complexity.MEDIUM
        assert result["medium_score"] >= 2

    def test_file_count_low(self):
        result = self.optimizer.analyze_task("小改动", file_count=2)
        assert result["complexity"] == Complexity.LOW
        # file_count=2 不满足 >2 条件，medium_score 不增加
        assert result["medium_score"] == 0

    def test_new_files_api(self):
        result = self.optimizer.analyze_task(
            "新功能", new_files=["src/api.py", "src/service.py"]
        )
        assert result["medium_score"] >= 2

    def test_new_files_app(self):
        result = self.optimizer.analyze_task(
            "新项目", new_files=["src/app.py", "src/main.py", "src/server.py"]
        )
        assert result["high_score"] >= 3

    def test_combined_factors(self):
        result = self.optimizer.analyze_task(
            "重构 API 系统", file_count=12, new_files=["src/app.py", "src/api.py"]
        )
        assert result["complexity"] == Complexity.HIGH
        assert result["high_score"] >= 5

    def test_empty_task(self):
        result = self.optimizer.analyze_task("")
        assert result["complexity"] == Complexity.LOW

    def test_none_inputs(self):
        result = self.optimizer.analyze_task("简单任务", file_count=None, new_files=None)
        assert result["file_count"] is None
        assert result["new_files_count"] == 0


class TestCostOptimizerRecommend:
    """Test CostOptimizer.recommend"""

    def setup_method(self):
        self.optimizer = CostOptimizer(prefer_local=True)

    def test_recommend_low_complexity(self):
        rec = self.optimizer.recommend("修复一个小 bug")
        assert rec.complexity == Complexity.LOW
        assert rec.model == "ollama/qwen2.5:7b"
        assert rec.provider == "ollama"
        assert "本地" in rec.reason or "免费" in rec.reason

    def test_recommend_medium_complexity(self):
        rec = self.optimizer.recommend("添加新的 API 接口", file_count=5)
        assert rec.complexity == Complexity.MEDIUM
        assert rec.model == "ollama/qwen2.5:14b"
        assert rec.provider == "ollama"

    def test_recommend_high_complexity(self):
        rec = self.optimizer.recommend("重构系统架构", file_count=15)
        assert rec.complexity == Complexity.HIGH
        assert rec.model == "ollama/qwen2.5:14b"
        assert "本地模型" in rec.reason

    def test_recommend_no_prefer_local(self):
        optimizer = CostOptimizer(prefer_local=False)
        rec = optimizer.recommend("修复 bug")
        assert rec.model == "qwen-turbo"
        assert rec.provider == "qwen"

    def test_recommend_medium_no_prefer_local(self):
        optimizer = CostOptimizer(prefer_local=False)
        rec = optimizer.recommend("添加 API", file_count=5)
        assert rec.model == "deepseek-chat"
        assert rec.provider == "deepseek"

    def test_recommend_high_no_prefer_local(self):
        optimizer = CostOptimizer(prefer_local=False)
        rec = optimizer.recommend("重构架构", file_count=15)
        assert rec.model == "gpt-4o"
        assert rec.provider == "openai"

    def test_recommend_has_alternatives(self):
        rec = self.optimizer.recommend("简单任务")
        assert len(rec.alternatives) >= 1
        assert "model" in rec.alternatives[0]
        assert "reason" in rec.alternatives[0]

    def test_recommend_cost_estimate(self):
        rec = self.optimizer.recommend("简单任务")
        assert rec.estimated_cost > 0
        assert isinstance(rec.estimated_cost, (int, float))


class TestCostOptimizerGetAllModels:
    """Test CostOptimizer.get_all_models"""

    def setup_method(self):
        self.optimizer = CostOptimizer()

    def test_returns_list(self):
        models = self.optimizer.get_all_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_sorted_by_cost(self):
        models = self.optimizer.get_all_models()
        costs = [m["cost"] for m in models]
        assert costs == sorted(costs)

    def test_model_structure(self):
        models = self.optimizer.get_all_models()
        for m in models:
            assert "model" in m
            assert "provider" in m
            assert "cost" in m
            assert "strengths" in m

    def test_all_providers_present(self):
        models = self.optimizer.get_all_models()
        providers = {m["provider"] for m in models}
        assert "ollama" in providers
        assert "deepseek" in providers
        assert "openai" in providers
        assert "anthropic" in providers


class TestCalculateCost:
    """Test calculate_cost function"""

    def test_gpt4o_mini_cost(self):
        estimate = calculate_cost("gpt-4o-mini", 1000000, 500000)
        assert estimate.model == "gpt-4o-mini"
        assert estimate.input_tokens == 1000000
        assert estimate.output_tokens == 500000
        # input: 0.15/1M, output: 0.60/1M
        assert estimate.input_cost == pytest.approx(0.15)
        assert estimate.output_cost == pytest.approx(0.30)
        assert estimate.total_cost == pytest.approx(0.45)

    def test_deepseek_cost(self):
        estimate = calculate_cost("deepseek-chat", 2000000, 1000000)
        # input: 0.14/1M, output: 0.28/1M
        assert estimate.input_cost == 0.28
        assert estimate.output_cost == 0.28
        assert estimate.total_cost == 0.56

    def test_ollama_free(self):
        estimate = calculate_cost("ollama/qwen2.5:7b", 1000000, 500000)
        assert estimate.input_cost == 0.0
        assert estimate.output_cost == 0.0
        assert estimate.total_cost == 0.0

    def test_claude_opus_expensive(self):
        estimate = calculate_cost("claude-3-opus", 1000000, 1000000)
        # input: 15/1M, output: 75/1M
        assert estimate.input_cost == 15.0
        assert estimate.output_cost == 75.0
        assert estimate.total_cost == 90.0

    def test_zero_tokens(self):
        estimate = calculate_cost("gpt-4o-mini", 0, 0)
        assert estimate.input_cost == 0.0
        assert estimate.output_cost == 0.0
        assert estimate.total_cost == 0.0

    def test_small_tokens(self):
        estimate = calculate_cost("deepseek-chat", 1000, 500)
        assert estimate.input_cost == pytest.approx(0.00014, abs=1e-6)
        assert estimate.output_cost == pytest.approx(0.00014, abs=1e-6)

    def test_model_not_in_pricing(self):
        with pytest.raises(ValueError, match="不在定价表中"):
            calculate_cost("nonexistent-model", 1000, 500)


class TestCalculateMultiModelCost:
    """Test calculate_multi_model_cost function"""

    def test_single_model(self):
        usages = [{"model": "gpt-4o-mini", "input_tokens": 1000000, "output_tokens": 500000}]
        results = calculate_multi_model_cost(usages)
        assert len(results) == 1
        assert results[0].model == "gpt-4o-mini"
        assert results[0].total_cost == pytest.approx(0.45)

    def test_multiple_models(self):
        usages = [
            {"model": "gpt-4o-mini", "input_tokens": 1000000, "output_tokens": 500000},
            {"model": "deepseek-chat", "input_tokens": 2000000, "output_tokens": 1000000},
            {"model": "ollama/qwen2.5:7b", "input_tokens": 500000, "output_tokens": 200000},
        ]
        results = calculate_multi_model_cost(usages)
        assert len(results) == 3
        assert results[0].total_cost == pytest.approx(0.45)
        assert results[1].total_cost == pytest.approx(0.56)
        assert results[2].total_cost == pytest.approx(0.0)

    def test_total_cost_sum(self):
        usages = [
            {"model": "gpt-4o-mini", "input_tokens": 1000000, "output_tokens": 500000},
            {"model": "deepseek-chat", "input_tokens": 1000000, "output_tokens": 500000},
        ]
        results = calculate_multi_model_cost(usages)
        total = sum(r.total_cost for r in results)
        # gpt-4o-mini: 0.45 + deepseek-chat: 0.28 = 0.73
        assert total == pytest.approx(0.73)


class TestCostEstimate:
    """Test CostEstimate dataclass"""

    def test_create_cost_estimate(self):
        estimate = CostEstimate(
            model="gpt-4o-mini",
            input_tokens=1000000,
            output_tokens=500000,
            input_cost=0.15,
            output_cost=0.30,
            total_cost=0.45,
        )
        assert estimate.model == "gpt-4o-mini"
        assert estimate.input_tokens == 1000000
        assert estimate.total_cost == 0.45


class TestModelPricing:
    """Test MODEL_PRICING dictionary"""

    def test_has_openai_models(self):
        assert "gpt-4o" in MODEL_PRICING
        assert "gpt-4o-mini" in MODEL_PRICING

    def test_has_anthropic_models(self):
        assert "claude-3-opus" in MODEL_PRICING
        assert "claude-3-sonnet" in MODEL_PRICING

    def test_has_deepseek(self):
        assert "deepseek-chat" in MODEL_PRICING

    def test_has_ollama(self):
        assert "ollama/qwen2.5:7b" in MODEL_PRICING
        assert "ollama/qwen2.5:14b" in MODEL_PRICING

    def test_pricing_structure(self):
        for _model, pricing in MODEL_PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert isinstance(pricing["input"], (int, float))
            assert isinstance(pricing["output"], (int, float))


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def setup_method(self):
        self.optimizer = CostOptimizer()

    def test_very_long_task_description(self):
        long_desc = "refactor " * 100 + "system architecture"
        result = self.optimizer.analyze_task(long_desc)
        assert result["complexity"] == Complexity.HIGH

    def test_special_characters(self):
        result = self.optimizer.analyze_task("修复 bug #123 & *特殊* 字符")
        assert result["complexity"] == Complexity.LOW

    def test_mixed_case_keywords(self):
        result = self.optimizer.analyze_task("Refactor The API System")
        assert result["complexity"] == Complexity.HIGH

    def test_boundary_file_count(self):
        # file_count > 10 才触发 HIGH (high_score += 3)
        # file_count=10 不满足 >10，所以 high_score 不增加
        result = self.optimizer.analyze_task("任务", file_count=10)
        assert result["high_score"] == 0

    def test_file_count_high_boundary(self):
        # file_count=11 才触发 HIGH
        result = self.optimizer.analyze_task("任务", file_count=11)
        assert result["high_score"] >= 3

    def test_file_count_zero(self):
        result = self.optimizer.analyze_task("任务", file_count=0)
        assert result["file_count"] == 0
        assert result["complexity"] == Complexity.LOW
