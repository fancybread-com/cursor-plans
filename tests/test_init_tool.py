"""Tests for the dev_plan_init tool functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from cursor_plans_mcp.server import init_dev_planning


class TestDevPlanInit:
    """Test the dev_plan_init MCP tool."""

    def create_sample_context_file(self, temp_dir: str, project_name: str = "test-project") -> str:
        """Helper to create a sample context YAML file."""
        context_content = {
            "project": {
                "directory": temp_dir,
                "name": project_name,
                "type": "python",
                "description": "Test project",
                "objectives": ["Build a test application"],
                "architecture_notes": ["Use clean architecture"],
            },
            "context_files": {
                "source": ["src/", "*.py"],
                "docs": ["README.md"],
                "config": ["pyproject.toml"],
            },
        }

        context_path = Path(temp_dir) / "test.context.yaml"
        with open(context_path, "w") as f:
            yaml.dump(context_content, f)

        return str(context_path)

    @pytest.mark.asyncio
    async def test_init_dev_planning_basic(self):
        """Test basic initialization of development planning with YAML context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("print('Hello')")
            (Path(temp_dir) / "README.md").write_text("# Test Project")

            # Create context file
            context_file = self.create_sample_context_file(temp_dir)

            result = await init_dev_planning({"context": context_file, "reset": False})

            assert len(result) == 1
            assert "Development Planning Initialized" in result[0].text  # type: ignore[attr-defined]
            assert "test-project" in result[0].text  # type: ignore[attr-defined]
            assert temp_dir in result[0].text  # type: ignore[attr-defined]

            # Check that .cursorplans directory was created
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            assert cursorplans_dir.exists()
            assert cursorplans_dir.is_dir()

    @pytest.mark.asyncio
    async def test_init_dev_planning_with_reset(self):
        """Test initialization with reset flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing .cursorplans directory with some files
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            cursorplans_dir.mkdir()
            (cursorplans_dir / "existing.devplan").write_text("old content")
            (cursorplans_dir / "old.yaml").write_text("old context")

            # Create context file
            context_file = self.create_sample_context_file(temp_dir)

            result = await init_dev_planning({"context": context_file, "reset": True})

            assert len(result) == 1
            assert "Development Planning Reset Complete" in result[0].text  # type: ignore[attr-defined]
            assert "reset" in result[0].text.lower()  # type: ignore[attr-defined]

            # Check that .cursorplans directory still exists but old files are gone
            assert cursorplans_dir.exists()
            assert not (cursorplans_dir / "existing.devplan").exists()
            assert not (cursorplans_dir / "old.yaml").exists()

    @pytest.mark.asyncio
    async def test_init_dev_planning_missing_context_file(self):
        """Test error handling when context file is missing."""
        result = await init_dev_planning({"context": "/non/existent/context.yaml", "reset": False})

        assert len(result) == 1
        assert "Error" in result[0].text  # type: ignore[attr-defined]
        assert "Context file not found" in result[0].text  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_init_dev_planning_no_context_parameter(self):
        """Test error handling when no context parameter is provided."""
        result = await init_dev_planning({"reset": False})

        assert len(result) == 1
        assert "Error" in result[0].text  # type: ignore[attr-defined]
        assert "Context file path is required" in result[0].text  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_init_dev_planning_invalid_yaml(self):
        """Test error handling with invalid YAML content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid YAML file
            context_path = Path(temp_dir) / "invalid.context.yaml"
            context_path.write_text("invalid: yaml: content: [")

            result = await init_dev_planning({"context": str(context_path), "reset": False})

            assert len(result) == 1
            assert "Error" in result[0].text  # type: ignore[attr-defined]
            assert "Invalid YAML" in result[0].text  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_init_dev_planning_missing_project_section(self):
        """Test error handling when YAML is missing project section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create YAML without project section
            context_path = Path(temp_dir) / "incomplete.context.yaml"
            context_path.write_text("context_files:\n  source: ['*.py']")

            result = await init_dev_planning({"context": str(context_path), "reset": False})

            assert len(result) == 1
            assert "Error" in result[0].text  # type: ignore[attr-defined]
            assert "Missing 'project' section" in result[0].text  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_init_dev_planning_context_file_scanning(self):
        """Test that initialization scans and finds context files correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a comprehensive project structure
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("from fastapi import FastAPI")
            (Path(temp_dir) / "src" / "models.py").write_text("class User: pass")
            (Path(temp_dir) / "README.md").write_text("# Test Project")
            (Path(temp_dir) / "pyproject.toml").write_text("[project]\nname = 'test'")

            # Create context file
            context_file = self.create_sample_context_file(temp_dir, "test-scanning")

            result = await init_dev_planning({"context": context_file, "reset": False})

            assert len(result) == 1
            assert "Development Planning Initialized" in result[0].text  # type: ignore[attr-defined]
            assert "Context Files Found" in result[0].text  # type: ignore[attr-defined]
            assert "source: src/main.py" in result[0].text  # type: ignore[attr-defined]
            assert "docs: README.md" in result[0].text  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_init_dev_planning_with_objectives_and_architecture(self):
        """Test that objectives and architecture notes are displayed correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create enhanced context file with objectives and architecture
            context_content = {
                "project": {
                    "directory": temp_dir,
                    "name": "feature-rich-project",
                    "type": "fastapi",
                    "description": "A comprehensive test project",
                    "objectives": [
                        "Build scalable API",
                        "Implement authentication",
                        "Add comprehensive testing",
                    ],
                    "architecture_notes": [
                        "Use repository pattern",
                        "Implement dependency injection",
                        "Follow clean architecture principles",
                    ],
                },
                "context_files": {
                    "source": ["src/"],
                    "docs": ["README.md"],
                    "config": ["requirements.txt"],
                },
            }

            context_path = Path(temp_dir) / "enhanced.context.yaml"
            with open(context_path, "w") as f:
                yaml.dump(context_content, f)

            result = await init_dev_planning({"context": str(context_path), "reset": False})

            assert len(result) == 1
            result_text = result[0].text  # type: ignore[attr-defined]
            assert "Development Planning Initialized" in result_text
            assert "Project Objectives" in result_text
            assert "Build scalable API" in result_text
            assert "Architecture Notes" in result_text
            assert "Use repository pattern" in result_text
            assert "feature-rich-project" in result_text

    @pytest.mark.asyncio
    async def test_init_dev_planning_nonexistent_project_directory(self):
        """Test error handling when project directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create context file pointing to non-existent directory
            context_content = {
                "project": {
                    "directory": "/non/existent/path",
                    "name": "test-project",
                    "type": "python",
                },
                "context_files": {"source": ["*.py"]},
            }

            context_path = Path(temp_dir) / "bad.context.yaml"
            with open(context_path, "w") as f:
                yaml.dump(context_content, f)

            result = await init_dev_planning({"context": str(context_path), "reset": False})

            assert len(result) == 1
            assert "Error" in result[0].text  # type: ignore[attr-defined]
            assert "Project directory does not exist" in result[0].text  # type: ignore[attr-defined]
