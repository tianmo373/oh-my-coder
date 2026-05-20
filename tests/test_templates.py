"""
Tests for src/templates/__init__.py
"""

from pathlib import Path

from src.templates import (
    TemplateCategory,
    TemplateMarket,
    TemplateMetadata,
    WorkflowStep,
    WorkflowTemplate,
    get_template_market,
)


class TestTemplateCategory:
    """Test TemplateCategory enum."""

    def test_category_values(self):
        """Test that all expected categories exist."""
        assert TemplateCategory.BUILD.value == "build"
        assert TemplateCategory.REVIEW.value == "review"
        assert TemplateCategory.DEBUG.value == "debug"
        assert TemplateCategory.TEST.value == "test"
        assert TemplateCategory.REFACTOR.value == "refactor"
        assert TemplateCategory.DOCUMENT.value == "document"
        assert TemplateCategory.DEPLOY.value == "deploy"
        assert TemplateCategory.CUSTOM.value == "custom"


class TestWorkflowStep:
    """Test WorkflowStep dataclass."""

    def test_basic_step(self):
        """Test creating a basic workflow step."""
        step = WorkflowStep(agent_name="Planner")
        assert step.agent_name == "Planner"
        assert step.description == ""
        assert step.dependencies == []
        assert step.condition is None
        assert step.timeout == 300
        assert step.retry == 0
        assert step.config == {}

    def test_step_with_all_fields(self):
        """Test creating a step with all fields."""
        step = WorkflowStep(
            agent_name="Executor",
            description="Execute the plan",
            dependencies=["Planner"],
            condition="planner_success",
            timeout=600,
            retry=3,
            config={"mode": "fast"},
        )
        assert step.agent_name == "Executor"
        assert step.description == "Execute the plan"
        assert step.dependencies == ["Planner"]
        assert step.condition == "planner_success"
        assert step.timeout == 600
        assert step.retry == 3
        assert step.config == {"mode": "fast"}


class TestTemplateMetadata:
    """Test TemplateMetadata model."""

    def test_basic_metadata(self):
        """Test creating basic metadata."""
        metadata = TemplateMetadata(
            name="test",
            display_name="Test Template",
            description="A test template",
            category=TemplateCategory.BUILD,
        )
        assert metadata.name == "test"
        assert metadata.display_name == "Test Template"
        assert metadata.description == "A test template"
        assert metadata.category == TemplateCategory.BUILD
        assert metadata.version == "0.2.0"
        assert metadata.author == ""
        assert metadata.tags == []
        assert metadata.icon == "📦"
        assert metadata.difficulty == "beginner"

    def test_metadata_with_all_fields(self):
        """Test metadata with all fields."""
        metadata = TemplateMetadata(
            name="advanced",
            display_name="Advanced Template",
            description="An advanced template",
            category=TemplateCategory.REVIEW,
            version="1.0.0",
            author="Test Author",
            tags=["test", "advanced"],
            icon="🚀",
            difficulty="advanced",
            estimated_time="10 minutes",
        )
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.tags == ["test", "advanced"]
        assert metadata.icon == "🚀"
        assert metadata.difficulty == "advanced"
        assert metadata.estimated_time == "10 minutes"


class TestWorkflowTemplate:
    """Test WorkflowTemplate dataclass."""

    def test_basic_template(self):
        """Test creating a basic template."""
        metadata = TemplateMetadata(
            name="test",
            display_name="Test",
            description="Test template",
            category=TemplateCategory.BUILD,
        )
        steps = [WorkflowStep(agent_name="Planner")]

        template = WorkflowTemplate(metadata=metadata, steps=steps)

        assert template.metadata.name == "test"
        assert len(template.steps) == 1
        assert template.variables == {}
        assert template.hooks == {}

    def test_to_dict(self):
        """Test converting template to dict."""
        metadata = TemplateMetadata(
            name="test",
            display_name="Test",
            description="Test template",
            category=TemplateCategory.BUILD,
        )
        steps = [WorkflowStep(agent_name="Planner", description="Plan")]

        template = WorkflowTemplate(
            metadata=metadata,
            steps=steps,
            variables={"var1": "value1"},
            hooks={"pre": "setup"},
        )

        data = template.to_dict()

        assert data["metadata"]["name"] == "test"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["agent_name"] == "Planner"
        assert data["variables"] == {"var1": "value1"}
        assert data["hooks"] == {"pre": "setup"}

    def test_from_dict(self):
        """Test creating template from dict."""
        data = {
            "metadata": {
                "name": "test",
                "display_name": "Test",
                "description": "Test template",
                "category": "build",
            },
            "steps": [
                {
                    "agent_name": "Planner",
                    "description": "Plan",
                    "dependencies": [],
                    "condition": None,
                    "timeout": 300,
                    "retry": 0,
                    "config": {},
                }
            ],
            "variables": {"var1": "value1"},
            "hooks": {},
        }

        template = WorkflowTemplate.from_dict(data)

        assert template.metadata.name == "test"
        assert len(template.steps) == 1
        assert template.steps[0].agent_name == "Planner"
        assert template.variables == {"var1": "value1"}

    def test_round_trip(self):
        """Test to_dict and from_dict round trip."""
        metadata = TemplateMetadata(
            name="test",
            display_name="Test",
            description="Test template",
            category=TemplateCategory.BUILD,
            tags=["test"],
        )
        steps = [
            WorkflowStep(
                agent_name="Planner",
                description="Plan",
                dependencies=[],
                timeout=600,
            )
        ]

        original = WorkflowTemplate(
            metadata=metadata,
            steps=steps,
            variables={"key": "value"},
        )

        data = original.to_dict()
        restored = WorkflowTemplate.from_dict(data)

        assert restored.metadata.name == original.metadata.name
        assert len(restored.steps) == len(original.steps)
        assert restored.steps[0].agent_name == original.steps[0].agent_name
        assert restored.variables == original.variables


class TestTemplateMarket:
    """Test TemplateMarket class."""

    def test_init_with_default_dir(self, tmp_path: Path):
        """Test initialization with default directory."""
        import os

        # Change to tmp_path to avoid creating .omc in project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            market = TemplateMarket()
            assert market.template_dir.exists()
            assert market.template_dir.name == "templates"
            assert market.template_dir.parent.name == ".omc"
        finally:
            os.chdir(original_cwd)

    def test_init_with_custom_dir(self, tmp_path: Path):
        """Test initialization with custom directory."""
        market = TemplateMarket(template_dir=tmp_path / "custom_templates")
        assert market.template_dir.exists()
        assert market.template_dir.name == "custom_templates"

    def test_builtin_templates_loaded(self, tmp_path: Path):
        """Test that builtin templates are loaded."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        # Should have builtin templates
        templates = market.list_templates()
        assert len(templates) > 0

        # Should have specific builtin templates
        build_template = market.get_template("build")
        assert build_template is not None
        assert build_template.metadata.name == "build"

    def test_get_template(self, tmp_path: Path):
        """Test getting a template by name."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        template = market.get_template("build")
        assert template is not None
        assert template.metadata.name == "build"

    def test_get_nonexistent_template(self, tmp_path: Path):
        """Test getting a non-existent template."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        template = market.get_template("nonexistent")
        assert template is None

    def test_list_templates_no_filter(self, tmp_path: Path):
        """Test listing all templates."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        templates = market.list_templates()
        assert len(templates) > 0

    def test_list_templates_by_category(self, tmp_path: Path):
        """Test filtering templates by category."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        build_templates = market.list_templates(category="build")
        assert all(t.metadata.category.value == "build" for t in build_templates)

    def test_list_templates_by_tags(self, tmp_path: Path):
        """Test filtering templates by tags."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        templates = market.list_templates(tags=["开发"])
        # All returned templates should have at least one of the tags
        for template in templates:
            assert any(tag in template.metadata.tags for tag in ["开发"])

    def test_list_templates_by_difficulty(self, tmp_path: Path):
        """Test filtering templates by difficulty."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        beginner_templates = market.list_templates(difficulty="beginner")
        assert all(t.metadata.difficulty == "beginner" for t in beginner_templates)

    def test_register_template(self, tmp_path: Path):
        """Test registering a new template."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        metadata = TemplateMetadata(
            name="custom",
            display_name="Custom",
            description="Custom template",
            category=TemplateCategory.CUSTOM,
        )
        template = WorkflowTemplate(
            metadata=metadata,
            steps=[WorkflowStep(agent_name="Planner")],
        )

        market.register_template(template)

        retrieved = market.get_template("custom")
        assert retrieved is not None
        assert retrieved.metadata.name == "custom"

    def test_save_and_load_template(self, tmp_path: Path):
        """Test saving and loading template from file."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        metadata = TemplateMetadata(
            name="saved",
            display_name="Saved Template",
            description="A saved template",
            category=TemplateCategory.TEST,
        )
        template = WorkflowTemplate(
            metadata=metadata,
            steps=[WorkflowStep(agent_name="Executor")],
            variables={"test_var": "test_value"},
        )

        # Save
        file_path = market.save_template(template)
        assert file_path.exists()
        assert file_path.name == "saved.json"

        # Clear templates and reload
        market._templates.clear()
        assert market.get_template("saved") is None

        # Load
        loaded = market.load_template("saved")
        assert loaded is not None
        assert loaded.metadata.name == "saved"
        assert loaded.variables == {"test_var": "test_value"}

    def test_load_nonexistent_template(self, tmp_path: Path):
        """Test loading a non-existent template file."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        loaded = market.load_template("nonexistent")
        assert loaded is None

    def test_get_categories(self, tmp_path: Path):
        """Test getting all categories."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        categories = market.get_categories()
        assert len(categories) > 0

        # Each category should have name, icon, and count
        for cat in categories:
            assert "name" in cat
            assert "icon" in cat
            assert "count" in cat
            assert cat["count"] > 0

    def test_search_by_name(self, tmp_path: Path):
        """Test searching templates by name."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        results = market.search("build")
        assert len(results) > 0
        assert all("build" in t.metadata.name.lower() for t in results)

    def test_search_by_description(self, tmp_path: Path):
        """Test searching templates by description."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        results = market.search("审查")
        assert len(results) > 0
        # At least one should have "审查" in description or tags
        found = any("审查" in t.metadata.description or "审查" in t.metadata.tags for t in results)
        assert found

    def test_search_no_results(self, tmp_path: Path):
        """Test searching with no matches."""
        market = TemplateMarket(template_dir=tmp_path / "templates")

        results = market.search("xyznonexistent123")
        assert results == []


class TestGlobalInstance:
    """Test global template market instance."""

    def test_get_template_market_returns_instance(self):
        """Test that get_template_market returns an instance."""
        market = get_template_market()
        assert isinstance(market, TemplateMarket)

    def test_global_instance_is_singleton(self):
        """Test that global instance is a singleton."""
        market1 = get_template_market()
        market2 = get_template_market()
        assert market1 is market2
