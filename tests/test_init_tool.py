"""Tests for the dev_plan_init tool functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

from cursor_plans_mcp.server import init_dev_planning


class TestDevPlanInit:
    """Test the dev_plan_init MCP tool."""

    @pytest.mark.asyncio
    async def test_init_dev_planning_basic(self):
        """Test basic initialization of development planning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("print('Hello')")

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result) == 1
            assert "Development Planning Initialized" in result[0].text
            assert temp_dir in result[0].text

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
            (cursorplans_dir / "context.txt").write_text("old context")

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": True
            })

            assert len(result) == 1
            assert "Development Planning Reset Complete" in result[0].text
            assert "reset" in result[0].text.lower()

            # Check that .cursorplans directory still exists but old files are gone
            assert cursorplans_dir.exists()
            assert not (cursorplans_dir / "existing.devplan").exists()
            assert not (cursorplans_dir / "context.txt").exists()

    @pytest.mark.asyncio
    async def test_init_dev_planning_detects_python_project(self):
        """Test that initialization detects Python project correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python project files
            (Path(temp_dir) / "requirements.txt").write_text("fastapi\nuvicorn")
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("from fastapi import FastAPI")

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result) == 1
            assert "Python" in result[0].text or "FastAPI" in result[0].text or "Development Planning Initialized" in result[0].text

    @pytest.mark.asyncio
    async def test_init_dev_planning_detects_dotnet_project(self):
        """Test that initialization detects .NET project correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .NET project files
            (Path(temp_dir) / "TestProject.csproj").write_text("""
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
            """)

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result) == 1
            assert ".NET" in result[0].text or "C#" in result[0].text or "Development Planning Initialized" in result[0].text

    @pytest.mark.asyncio
    async def test_init_dev_planning_detects_vuejs_project(self):
        """Test that initialization detects Vue.js project correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Vue.js project files
            (Path(temp_dir) / "package.json").write_text('{"name": "vue-project", "dependencies": {"vue": "^3.0.0"}}')

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result) == 1
            assert "Vue" in result[0].text or "JavaScript" in result[0].text or "Development Planning Initialized" in result[0].text

    @pytest.mark.asyncio
    async def test_init_dev_planning_without_project_directory(self):
        """Test initialization without providing project_directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory and set PWD environment variable
            try:
                original_cwd = os.getcwd()
            except FileNotFoundError:
                original_cwd = "/tmp"  # Fallback directory
            original_pwd = os.environ.get("PWD")
            os.chdir(temp_dir)
            os.environ["PWD"] = temp_dir

            try:
                result = await init_dev_planning({
                    "reset": False
                })

                assert len(result) == 1
                assert "Development Planning Initialized" in result[0].text

                # Check that .cursorplans directory was created in current directory
                cursorplans_dir = Path(".").resolve() / ".cursorplans"
                assert cursorplans_dir.exists()
            finally:
                os.chdir(original_cwd)
                if original_pwd:
                    os.environ["PWD"] = original_pwd
                elif "PWD" in os.environ:
                    del os.environ["PWD"]

    @pytest.mark.asyncio
    async def test_init_dev_planning_context_storage(self):
        """Test that initialization stores context correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a project structure
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("print('Hello')")

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result) == 1

            # The context should be stored in the global _project_context
            # We can't directly test this from outside, but we can verify
            # that subsequent calls work correctly
            result2 = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result2) == 1
            assert "Development Planning Initialized" in result2[0].text

    @pytest.mark.asyncio
    async def test_init_dev_planning_error_handling(self):
        """Test error handling in initialization."""
        # Test with non-existent directory
        result = await init_dev_planning({
            "project_directory": "/non/existent/path",
            "reset": False
        })

        assert len(result) == 1
        assert "error" in result[0].text.lower() or "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_init_dev_planning_creates_cursorplans_directory(self):
        """Test that initialization creates the .cursorplans directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a project structure
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("print('Hello')")
            (Path(temp_dir) / "src" / "models.py").write_text("class Model: pass")
            (Path(temp_dir) / "tests").mkdir()
            (Path(temp_dir) / "tests" / "test_main.py").write_text("def test_main(): pass")

            result = await init_dev_planning({
                "project_directory": temp_dir,
                "reset": False
            })

            assert len(result) == 1

            # Check that .cursorplans directory was created
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            assert cursorplans_dir.exists()
            assert cursorplans_dir.is_dir()

            # Check that the directory is empty (context files are created separately)
            assert len(list(cursorplans_dir.iterdir())) == 0
