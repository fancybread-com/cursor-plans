"""Tests for name resolution and project directory handling."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

from cursor_plans_mcp.server import create_dev_plan, detect_existing_codebase


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
                result = await create_dev_plan({
                    "name": "middleware",
                    "template": "dotnet",
                    "project_directory": temp_dir
                })

            # Check that the result mentions the correct filename
            assert "middleware.devplan" in result[0].text
            assert "FancyBread.Invest.IntegrationTests.devplan" not in result[0].text

            # Check that the file was actually created with the correct name
            plan_file = Path(temp_dir) / ".cursorplans" / "middleware.devplan"
            assert plan_file.exists(), f"Expected {plan_file} to exist"

            # Verify the file content uses the correct name
            content = plan_file.read_text()
            assert 'name: "middleware"' in content
            assert 'name: "FancyBread.Invest.IntegrationTests"' not in content

    @pytest.mark.asyncio
    async def test_name_preserved_with_fastapi_template(self):
        """Test that the name parameter is preserved when using fastapi template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a package.json that would normally override the name
            package_file = Path(temp_dir) / "package.json"
            package_file.write_text('{"name": "existing-project", "dependencies": {"vue": "^3.0.0"}}')

            with patch('cursor_plans_mcp.server._project_context', {}):
                result = await create_dev_plan({
                    "name": "my-api",
                    "template": "fastapi",
                    "project_directory": temp_dir
                })

            # Check that the result mentions the correct filename
            assert "my-api.devplan" in result[0].text
            assert "existing-project.devplan" not in result[0].text

            # Check that the file was actually created with the correct name
            plan_file = Path(temp_dir) / ".cursorplans" / "my-api.devplan"
            assert plan_file.exists(), f"Expected {plan_file} to exist"

            # Verify the file content uses the correct name
            content = plan_file.read_text()
            assert 'name: "my-api"' in content
            assert 'name: "existing-project"' not in content

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
    async def test_name_override_only_when_analyze_existing_true(self):
        """Test that name is only overridden when analyze_existing=True."""
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
                # Test with analyze_existing=False (should preserve name)
                result = await create_dev_plan({
                    "name": "middleware",
                    "template": "dotnet",
                    "analyze_existing": False,
                    "project_directory": temp_dir
                })

                plan_file = Path(temp_dir) / ".cursorplans" / "middleware.devplan"
                assert plan_file.exists()
                content = plan_file.read_text()
                assert 'name: "middleware"' in content

                # Clean up
                plan_file.unlink()

                # Test with analyze_existing=True (should override name)
                result = await create_dev_plan({
                    "name": "middleware",
                    "template": "dotnet",
                    "analyze_existing": True,
                    "project_directory": temp_dir
                })

                plan_file = Path(temp_dir) / ".cursorplans" / "TestProject.devplan"
                assert plan_file.exists()
                content = plan_file.read_text()
                assert 'name: "TestProject"' in content

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
                result = await create_dev_plan({
                    "name": "middleware",
                    "template": "basic"
                    # No project_directory specified - should use context
                })

                # Check that the result mentions the correct filename
                assert "middleware.devplan" in result[0].text

                # Check that the file was created in the context directory
                plan_file = Path(temp_dir) / ".cursorplans" / "middleware.devplan"
                assert plan_file.exists(), f"Expected {plan_file} to exist"


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
                result = await create_dev_plan({
                    "name": "test-project",
                    "template": "basic",
                    "project_directory": temp_dir
                })

                # Check that the file was created in the temp directory
                plan_file = Path(temp_dir) / ".cursorplans" / "test-project.devplan"
                assert plan_file.exists(), f"Expected {plan_file} to exist"

                # Verify the content
                content = plan_file.read_text()
                assert 'name: "test-project"' in content
                assert "basic" in content.lower()
