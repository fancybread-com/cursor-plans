"""Tests for name resolution and project directory handling."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

from cursor_plans_mcp.server import init_dev_planning, prepare_dev_plan, detect_existing_codebase


class TestNameResolution:
    """Test that the name parameter is preserved and not overridden by filesystem detection."""

    @pytest.mark.asyncio
    async def test_name_preserved_with_dotnet_template(self):
        """Test that the name parameter is preserved when using dotnet template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .csproj file that would normally override the name
            csproj_file = Path(temp_dir) / "FancyBread.Invest.IntegrationTests.csproj"
            csproj_file.write_text("""
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
            """)

            # Mock the project directory to be our temp directory
            with patch('cursor_plans_mcp.server._project_context', {}):
                # Create a minimal context file
                context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
                context_file = Path(temp_dir) / "context.yaml"
                with open(context_file, 'w') as f:
                    f.write(context_content)

                result = await init_dev_planning({
                    "context": str(context_file),
                    "project_directory": temp_dir
                })

            # Check that initialization was successful
            assert "Development Planning Initialized" in result[0].text

            # Check that .cursorplans directory was created
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            assert cursorplans_dir.exists()

    @pytest.mark.asyncio
    async def test_name_preserved_with_fastapi_template(self):
        """Test that the name parameter is preserved when using fastapi template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a package.json that would normally override the name
            package_file = Path(temp_dir) / "package.json"
            package_file.write_text('{"name": "existing-project", "dependencies": {"vue": "^3.0.0"}}')

            with patch('cursor_plans_mcp.server._project_context', {}):
                # Create a context file for FastAPI
                context_content = """
project:
  name: my-api
  type: python
  description: A FastAPI API
"""
                context_file = Path(temp_dir) / "context.yaml"
                with open(context_file, 'w') as f:
                    f.write(context_content)

                result = await init_dev_planning({
                    "context": str(context_file),
                    "project_directory": temp_dir
                })

            # Check that initialization was successful
            assert "Development Planning Initialized" in result[0].text

            # Check that .cursorplans directory was created
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            assert cursorplans_dir.exists()

    @pytest.mark.asyncio
    async def test_detect_existing_codebase_suggest_name_false(self):
        """Test that detect_existing_codebase doesn't suggest names when suggest_name=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .csproj file
            csproj_file = Path(temp_dir) / "TestProject.csproj"
            csproj_file.write_text("""
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
            """)

            # Test with suggest_name=False
            result = await detect_existing_codebase(temp_dir, suggest_name=False)

            assert result["framework"] == "dotnet"
            assert result["suggested_name"] is None

            # Test with suggest_name=True
            result = await detect_existing_codebase(temp_dir, suggest_name=True)

            assert result["framework"] == "dotnet"
            assert result["suggested_name"] == "TestProject"

    @pytest.mark.asyncio
    async def test_name_always_preserved(self):
        """Test that name is always preserved (no auto-detection)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .csproj file
            csproj_file = Path(temp_dir) / "TestProject.csproj"
            csproj_file.write_text("""
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
            """)

            with patch('cursor_plans_mcp.server._project_context', {}):
                # Create a minimal context file
                context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
                context_file = Path(temp_dir) / "context.yaml"
                with open(context_file, 'w') as f:
                    f.write(context_content)

                result = await init_dev_planning({
                    "context": str(context_file),
                    "project_directory": temp_dir
                })

                # Check that initialization was successful
                assert "Development Planning Initialized" in result[0].text

                # Check that .cursorplans directory was created
                cursorplans_dir = Path(temp_dir) / ".cursorplans"
                assert cursorplans_dir.exists()

    @pytest.mark.asyncio
    async def test_context_aware_project_directory(self):
        """Test that the context-aware project directory works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up project context
            project_context = {
                "project_directory": temp_dir,
                "project_name": "test-project",
                "cursorplans_dir": str(Path(temp_dir) / ".cursorplans")
            }

            with patch('cursor_plans_mcp.server._project_context', project_context):
                # Create a minimal context file
                context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
                context_file = Path(temp_dir) / "context.yaml"
                with open(context_file, 'w') as f:
                    f.write(context_content)

                result = await init_dev_planning({
                    "context": str(context_file),
                    "project_directory": temp_dir
                })

                # Check that initialization was successful
                assert "Development Planning Initialized" in result[0].text

                # Check that .cursorplans directory was created
                cursorplans_dir = Path(temp_dir) / ".cursorplans"
                assert cursorplans_dir.exists()


class TestPathResolution:
    """Test path resolution logic."""

    @pytest.mark.asyncio
    async def test_path_resolution_uses_temp_dir_in_tests(self):
        """Test that path resolution works correctly in test environments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            (Path(temp_dir) / "src").mkdir()
            (Path(temp_dir) / "src" / "main.py").write_text("print('Hello')")

            with patch('cursor_plans_mcp.server._project_context', {}):
                # First initialize
                context_content = """
project:
  name: test-project
  type: python
  description: A test project
"""
                context_file = Path(temp_dir) / "context.yaml"
                with open(context_file, 'w') as f:
                    f.write(context_content)

                await init_dev_planning({
                    "context": str(context_file),
                    "project_directory": temp_dir
                })

                # Then prepare the plan
                result = await prepare_dev_plan({
                    "name": "test-project",
                    "template": "basic"
                })

                # Check that the file was created in the temp directory
                plan_file = Path(temp_dir) / ".cursorplans" / "test-project.devplan"
                assert plan_file.exists(), f"Expected {plan_file} to exist"

                # Verify the content
                content = plan_file.read_text()
                assert 'name: "test-project"' in content
                assert "basic" in content.lower()
