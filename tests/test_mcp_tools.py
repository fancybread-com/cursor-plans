"""
Integration tests for MCP tools.
"""

import os
from pathlib import Path

import pytest
import yaml

from cursor_plans_mcp.server import (
    apply_dev_plan,
    init_dev_planning,
    prepare_dev_plan,
    validate_dev_plan,
)


class TestPlanInit:
    """Test the plan_init MCP tool."""

    @pytest.mark.asyncio
    async def test_init_basic_project(self, temp_dir):
        """Test initializing a basic project."""
        os.chdir(temp_dir)
        # Create a minimal context file
        context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
        context_file = temp_dir / "context.yaml"
        with open(context_file, "w") as f:
            f.write(context_content)

        result = await init_dev_planning(
            {"context": str(context_file), "project_directory": str(temp_dir)}
        )

        assert len(result) == 1
        assert "Development Planning Initialized" in result[0].text
        assert "Ready to create development plans" in result[0].text

        # Check that .cursorplans directory was created but no plan file yet
        cursorplans_dir = temp_dir / ".cursorplans"
        assert cursorplans_dir.exists()
        plan_file = cursorplans_dir / "test-project.devplan"
        assert not plan_file.exists()

    @pytest.mark.asyncio
    async def test_init_fastapi_plan(self, temp_dir):
        """Test initializing and creating a FastAPI development plan."""
        os.chdir(temp_dir)

        # Create a context file for FastAPI
        context_content = """
project:
  name: api-project
  type: python
  description: A FastAPI web service
"""
        context_file = Path(temp_dir) / "context.yaml"
        with open(context_file, "w") as f:
            f.write(context_content)

        result = await init_dev_planning(
            {"context": str(context_file), "project_directory": str(temp_dir)}
        )

        assert len(result) == 1
        assert "Development Planning Initialized" in result[0].text
        assert "Ready to create development plans" in result[0].text

        # Check that .cursorplans directory was created but no plan file yet
        cursorplans_dir = Path(temp_dir) / ".cursorplans"
        assert cursorplans_dir.exists()
        plan_file = cursorplans_dir / "api-project.devplan"
        assert not plan_file.exists()

    @pytest.mark.asyncio
    async def test_init_with_context(self, temp_dir, sample_context_file):
        """Test initializing with context file."""
        os.chdir(temp_dir)

        result = await init_dev_planning(
            {"context": str(sample_context_file), "project_directory": str(temp_dir)}
        )

        assert len(result) == 1
        assert "Development Planning Initialized" in result[0].text


class TestPlanPrepare:
    """Test the plan_prepare MCP tool."""

    @pytest.mark.asyncio
    async def test_prepare_basic_plan(self, temp_dir):
        """Test preparing a basic development plan."""
        os.chdir(temp_dir)

        # First initialize the project
        context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
        context_file = temp_dir / "context.yaml"
        with open(context_file, "w") as f:
            f.write(context_content)

        # Initialize first
        await init_dev_planning(
            {"context": str(context_file), "project_directory": str(temp_dir)}
        )

        # Now prepare the plan
        result = await prepare_dev_plan({"name": "test-project", "template": "basic"})

        assert len(result) == 1
        assert "Development Plan Created" in result[0].text

        # Check that plan file was created
        plan_file = temp_dir / ".cursorplans" / "test-project.devplan"
        assert plan_file.exists()

        # Verify plan content
        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        assert plan_data["project"]["name"] == "test-project"
        assert "target_state" in plan_data
        assert "resources" in plan_data
        assert "phases" in plan_data

    @pytest.mark.asyncio
    async def test_prepare_fastapi_plan(self, temp_dir):
        """Test preparing a FastAPI development plan."""
        os.chdir(temp_dir)

        # First initialize the project
        context_content = """
project:
  name: api-project
  type: python
  description: A FastAPI web service
"""
        context_file = temp_dir / "context.yaml"
        with open(context_file, "w") as f:
            f.write(context_content)

        # Initialize first
        await init_dev_planning(
            {"context": str(context_file), "project_directory": str(temp_dir)}
        )

        # Now prepare the plan
        result = await prepare_dev_plan({"name": "api-project", "template": "fastapi"})

        assert len(result) == 1
        assert "Development Plan Created" in result[0].text

        # Check FastAPI-specific content
        plan_file = temp_dir / ".cursorplans" / "api-project.devplan"
        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # Check for FastAPI-specific features
        target_state = plan_data.get("target_state", {})
        architecture = target_state.get("architecture", [])
        features = target_state.get("features", [])

        assert any("FastAPI" in str(item) for item in architecture)
        assert "api_endpoints" in features
        assert "database_models" in features

    @pytest.mark.asyncio
    async def test_prepare_without_init(self, temp_dir):
        """Test preparing a plan without initializing first."""
        os.chdir(temp_dir)

        result = await prepare_dev_plan({"name": "test-project", "template": "basic"})

        assert len(result) == 1
        assert "No project context found" in result[0].text
        assert "Please run plan_init first" in result[0].text


class TestPlanValidate:
    """Test the plan_validate MCP tool."""

    @pytest.mark.asyncio
    async def test_validate_valid_plan(self, sample_plan_file, temp_dir):
        """Test validating a valid plan."""
        os.chdir(temp_dir)

        result = await validate_dev_plan(
            {
                "plan_file": str(sample_plan_file),
                "strict_mode": False,
                "check_cursor_rules": False,
            }
        )

        assert len(result) == 1
        # Should either pass or have only warnings/suggestions
        result_text = result[0].text
        assert "validation" in result_text.lower()

    @pytest.mark.asyncio
    async def test_validate_nonexistent_plan(self, temp_dir):
        """Test validating a non-existent plan."""
        os.chdir(temp_dir)

        result = await validate_dev_plan(
            {
                "plan_file": "nonexistent.devplan",
                "strict_mode": False,
                "check_cursor_rules": False,
            }
        )

        assert len(result) == 1
        assert "Plan file not found" in result[0].text

    @pytest.mark.asyncio
    async def test_validate_with_cursor_rules(
        self, sample_plan_file, sample_cursorrules, temp_dir
    ):
        """Test validation with Cursor rules."""
        os.chdir(temp_dir)

        result = await validate_dev_plan(
            {
                "plan_file": str(sample_plan_file),
                "strict_mode": False,
                "check_cursor_rules": True,
            }
        )

        assert len(result) == 1
        result_text = result[0].text
        assert "validation" in result_text.lower()
        # Should not suggest creating .cursorrules since it exists
        assert "No .cursorrules file found" not in result_text

    @pytest.mark.asyncio
    async def test_validate_strict_mode(self, sample_plan_file, temp_dir):
        """Test validation in strict mode."""
        os.chdir(temp_dir)

        # First validate in normal mode
        normal_result = await validate_dev_plan(
            {
                "plan_file": str(sample_plan_file),
                "strict_mode": False,
                "check_cursor_rules": False,
            }
        )

        # Then in strict mode
        strict_result = await validate_dev_plan(
            {
                "plan_file": str(sample_plan_file),
                "strict_mode": True,
                "check_cursor_rules": False,
            }
        )

        # Both should return results
        assert len(normal_result) == 1
        assert len(strict_result) == 1


class TestErrorHandling:
    """Test error handling in MCP tools."""

    @pytest.mark.asyncio
    async def test_init_plan_invalid_template(self, temp_dir):
        """Test initializing plan with invalid template."""
        os.chdir(temp_dir)  # Create a minimal context file
        context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
        context_file = temp_dir / "context.yaml"

        with open(context_file, "w") as f:
            f.write(context_content)

        result = await init_dev_planning(
            {
                "context": str(context_file),
                "name": "test-project",
                "template": "invalid_template",
                "project_directory": str(temp_dir),
            }
        )

        assert len(result) == 1
        # Should either create a plan or show an error message
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_validation_engine_failure(self, temp_dir):
        """Test validation when engine fails."""
        os.chdir(temp_dir)

        # Create an invalid YAML file
        invalid_file = temp_dir / "invalid.devplan"
        invalid_file.write_text("invalid: yaml: content: [unclosed")

        result = await validate_dev_plan(
            {
                "plan_file": str(invalid_file),
                "strict_mode": False,
                "check_cursor_rules": False,
            }
        )

        assert len(result) == 1
        result_text = result[0].text
        assert "validation" in result_text.lower() or "error" in result_text.lower()


class TestExecutionTools:
    """Test the execution-related MCP tools."""

    @pytest.mark.asyncio
    async def test_dev_apply_plan_dry_run(self, temp_dir):
        """Test dev_apply_plan tool with dry run."""
        os.chdir(temp_dir)

        result = await apply_dev_plan(
            {"plan_file": "nonexistent.devplan", "dry_run": True}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_dev_apply_plan_execution(self, temp_dir):
        """Test dev_apply_plan tool with actual execution."""
        os.chdir(temp_dir)

        result = await apply_dev_plan(
            {"plan_file": "nonexistent.devplan", "dry_run": False}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "error" in result[0].text.lower()
