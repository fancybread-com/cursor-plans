"""
Integration tests for MCP tools.
"""

import pytest
import os
import yaml
from unittest.mock import patch
from cursor_plans_mcp.server import (
    create_dev_plan,
    show_dev_plan,
    validate_dev_plan,
    show_current_state,
    show_state_diff,
    list_project_context,
    add_context_files,
    apply_dev_plan,
    rollback_to_snapshot,
    list_snapshots
)


class TestDevPlanCreate:
    """Test the dev_plan_create MCP tool."""

    @pytest.mark.asyncio
    async def test_create_basic_plan(self, temp_dir):
        """Test creating a basic development plan."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "test-project",
            "template": "basic",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        assert len(result) == 1
        assert "Created development plan" in result[0].text

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
    async def test_create_fastapi_plan(self, temp_dir):
        """Test creating a FastAPI development plan."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "api-project",
            "template": "fastapi",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        assert len(result) == 1
        assert "Created development plan" in result[0].text

        # Check FastAPI-specific content
        plan_file = temp_dir / ".cursorplans" / "api-project.devplan"
        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # Should have FastAPI-specific elements
        architecture = plan_data["target_state"]["architecture"]
        assert any("FastAPI" in str(item) for item in architecture)

        # Should have multiple phases
        phases = plan_data["phases"]
        assert len(phases) >= 3
        assert "foundation" in phases
        assert "security" in phases

    @pytest.mark.asyncio
    async def test_create_with_context(self, temp_dir, sample_context_file):
        """Test creating a plan with context file."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "context-project",
            "template": "basic",
            "analyze_existing": False,
            "context": "",  # Will use default context.txt
            "project_directory": str(temp_dir)
        })

        assert len(result) == 1
        assert "Context files included" in result[0].text or "Created development plan" in result[0].text


class TestDevPlanShow:
    """Test the dev_plan_show MCP tool."""

    @pytest.mark.asyncio
    async def test_show_existing_plan(self, sample_plan_file, temp_dir):
        """Test showing an existing plan."""
        os.chdir(temp_dir)

        result = await show_dev_plan({
            "plan_file": str(sample_plan_file)
        })

        assert len(result) == 1
        assert "Development Plan" in result[0].text
        assert "test-project" in result[0].text
        assert "```yaml" in result[0].text

    @pytest.mark.asyncio
    async def test_show_nonexistent_plan(self, temp_dir):
        """Test showing a non-existent plan."""
        os.chdir(temp_dir)

        result = await show_dev_plan({
            "plan_file": "nonexistent.devplan"
        })

        assert len(result) == 1
        assert "Plan file not found" in result[0].text


class TestDevPlanValidate:
    """Test the dev_plan_validate MCP tool."""

    @pytest.mark.asyncio
    async def test_validate_valid_plan(self, sample_plan_file, temp_dir):
        """Test validating a valid plan."""
        os.chdir(temp_dir)

        result = await validate_dev_plan({
            "plan_file": str(sample_plan_file),
            "strict_mode": False,
            "check_cursor_rules": False
        })

        assert len(result) == 1
        # Should either pass or have only warnings/suggestions
        result_text = result[0].text
        assert "validation" in result_text.lower()

    @pytest.mark.asyncio
    async def test_validate_nonexistent_plan(self, temp_dir):
        """Test validating a non-existent plan."""
        os.chdir(temp_dir)

        result = await validate_dev_plan({
            "plan_file": "nonexistent.devplan",
            "strict_mode": False,
            "check_cursor_rules": False
        })

        assert len(result) == 1
        assert "Plan file not found" in result[0].text

    @pytest.mark.asyncio
    async def test_validate_with_cursor_rules(self, sample_plan_file, sample_cursorrules, temp_dir):
        """Test validation with Cursor rules."""
        os.chdir(temp_dir)

        result = await validate_dev_plan({
            "plan_file": str(sample_plan_file),
            "strict_mode": False,
            "check_cursor_rules": True
        })

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
        normal_result = await validate_dev_plan({
            "plan_file": str(sample_plan_file),
            "strict_mode": False,
            "check_cursor_rules": False
        })

        # Then in strict mode
        strict_result = await validate_dev_plan({
            "plan_file": str(sample_plan_file),
            "strict_mode": True,
            "check_cursor_rules": False
        })

        # Both should return results
        assert len(normal_result) == 1
        assert len(strict_result) == 1


class TestDevStateShow:
    """Test the dev_state_show MCP tool."""

    @pytest.mark.asyncio
    async def test_show_state_existing_directory(self, temp_dir, mock_existing_files):
        """Test showing state of existing directory."""
        os.chdir(temp_dir)

        result = await show_current_state({
            "directory": "."
        })

        assert len(result) == 1
        result_text = result[0].text
        assert "Current Codebase State" in result_text
        assert "Total Files" in result_text

        # Should list some of the mock files
        assert any(f.name in result_text for f in mock_existing_files)

    @pytest.mark.asyncio
    async def test_show_state_nonexistent_directory(self, temp_dir):
        """Test showing state of non-existent directory."""
        os.chdir(temp_dir)

        result = await show_current_state({
            "directory": "nonexistent"
        })

        assert len(result) == 1
        assert "Directory not found" in result[0].text


class TestDevStateDiff:
    """Test the dev_state_diff MCP tool."""

    @pytest.mark.asyncio
    async def test_diff_with_existing_plan(self, sample_plan_file, temp_dir):
        """Test state diff with existing plan."""
        os.chdir(temp_dir)

        result = await show_state_diff({
            "plan_file": str(sample_plan_file)
        })

        assert len(result) == 1
        result_text = result[0].text
        assert "State Difference Analysis" in result_text or "diff" in result_text.lower()

    @pytest.mark.asyncio
    async def test_diff_nonexistent_plan(self, temp_dir):
        """Test state diff with non-existent plan."""
        os.chdir(temp_dir)

        result = await show_state_diff({
            "plan_file": "nonexistent.devplan"
        })

        assert len(result) == 1
        assert "Plan file not found" in result[0].text


class TestDevContextList:
    """Test the dev_context_list MCP tool."""

    @pytest.mark.asyncio
    async def test_list_context_existing_directory(self, temp_dir, mock_existing_files):
        """Test listing context for existing directory."""
        os.chdir(temp_dir)

        result = await list_project_context({
            "directory": ".",
            "include_content": False,
            "max_depth": 3
        })

        assert len(result) == 1
        result_text = result[0].text
        assert "Project Context Analysis" in result_text

        # Should detect some project structure
        assert any(f.name in result_text for f in mock_existing_files)

    @pytest.mark.asyncio
    async def test_list_context_with_content(self, temp_dir, mock_existing_files):
        """Test listing context with content previews."""
        os.chdir(temp_dir)

        result = await list_project_context({
            "directory": ".",
            "include_content": True,
            "max_depth": 2
        })

        assert len(result) == 1
        result_text = result[0].text
        assert "Project Context Analysis" in result_text

        # When include_content is True, should show file previews
        if "File Previews" in result_text:
            assert "Sample content" in result_text or "```" in result_text


class TestDevContextAdd:
    """Test the dev_context_add MCP tool."""

    @pytest.mark.asyncio
    async def test_add_context_files(self, temp_dir, mock_existing_files):
        """Test adding files to context."""
        os.chdir(temp_dir)

        # Add some files to context
        files_to_add = [f.name for f in mock_existing_files[:3]]

        result = await add_context_files({
            "files": files_to_add,
            "context": "main",
            "description": "Test context"
        })

        assert len(result) == 1
        result_text = result[0].text
        assert "Added" in result_text or "Updated" in result_text

        # Check that context file was created
        context_file = temp_dir / "context.txt"
        assert context_file.exists()

        # Verify content
        context_content = context_file.read_text()
        assert all(file_name in context_content for file_name in files_to_add[:2])  # At least some files

    @pytest.mark.asyncio
    async def test_add_context_with_story_name(self, temp_dir, mock_existing_files):
        """Test adding files to story-specific context."""
        os.chdir(temp_dir)

        result = await add_context_files({
            "files": ["src/main.py"],
            "context": "story-123",
            "description": "Story 123 context"
        })

        assert len(result) == 1

        # Check that story-specific context file was created
        context_file = temp_dir / "context-story-123.txt"
        assert context_file.exists()

        context_content = context_file.read_text()
        assert "src/main.py" in context_content
        assert "Story 123 context" in context_content


class TestErrorHandling:
    """Test error handling in MCP tools."""

    @pytest.mark.asyncio
    async def test_create_plan_invalid_template(self, temp_dir):
        """Test creating plan with invalid template."""
        os.chdir(temp_dir)

        # This should not crash, but might create a basic plan or show an error
        result = await create_dev_plan({
            "name": "test-project",
            "template": "invalid_template",
            "analyze_existing": False,
            "context": ""
        })

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

        result = await validate_dev_plan({
            "plan_file": str(invalid_file),
            "strict_mode": False,
            "check_cursor_rules": False
        })

        assert len(result) == 1
        result_text = result[0].text
        assert "validation" in result_text.lower() or "error" in result_text.lower()


class TestExecutionTools:
    """Test the execution-related MCP tools."""

    @pytest.mark.asyncio
    async def test_dev_apply_plan_dry_run(self, temp_dir):
        """Test dev_apply_plan tool with dry run."""
        os.chdir(temp_dir)

        result = await apply_dev_plan({
            'plan_file': 'nonexistent.devplan',
            'dry_run': True
        })

        assert len(result) == 1
        assert result[0].type == "text"
        assert "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_dev_apply_plan_execution(self, temp_dir):
        """Test dev_apply_plan tool with actual execution."""
        os.chdir(temp_dir)

        result = await apply_dev_plan({
            'plan_file': 'nonexistent.devplan',
            'dry_run': False
        })

        assert len(result) == 1
        assert result[0].type == "text"
        assert "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_dev_rollback_no_snapshot_id(self, temp_dir):
        """Test dev_rollback tool without snapshot ID."""
        os.chdir(temp_dir)

        result = await rollback_to_snapshot({})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "No snapshot ID provided" in result[0].text

    @pytest.mark.asyncio
    async def test_dev_rollback_with_snapshot_id(self, temp_dir):
        """Test dev_rollback tool with snapshot ID."""
        os.chdir(temp_dir)

        result = await rollback_to_snapshot({
            'snapshot_id': 'test-snapshot'
        })

        assert len(result) == 1
        assert result[0].type == "text"
        # Should show rollback result (success or failure)

    @pytest.mark.asyncio
    async def test_dev_snapshots(self, temp_dir):
        """Test dev_snapshots tool."""
        os.chdir(temp_dir)

        result = await list_snapshots({})

        assert len(result) == 1
        assert result[0].type == "text"
        # Should show snapshots list (empty or with data)
