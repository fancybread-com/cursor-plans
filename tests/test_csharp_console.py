"""Tests for C# console template functionality."""

import shutil
import tempfile

import pytest

from src.cursor_plans_mcp.execution.template_processor import TemplateProcessor
from src.cursor_plans_mcp.templates.languages.csharp.commands import CSharpCommands
from src.cursor_plans_mcp.templates.languages.csharp.generators import CSharpProjectGenerator


class TestCSharpCommands:
    """Test C# command definitions."""

    def test_get_project_commands(self):
        """Test that project commands are properly defined."""
        commands = CSharpCommands()
        project_commands = commands.get_project_commands()

        assert "console" in project_commands
        assert "classlib" in project_commands
        assert "webapi" in project_commands

        console_cmd = project_commands["console"]
        assert console_cmd["command"] == "dotnet"
        assert "console" in console_cmd["args"]
        assert "project_name" in console_cmd["required_params"]
        assert "output_path" in console_cmd["required_params"]

    def test_console_parameter_validation(self):
        """Test console parameter validation."""
        commands = CSharpCommands()

        # Valid parameters
        errors = commands.validate_console_params("MyConsoleApp", "/tmp/test")
        assert len(errors) == 0

        # Invalid project name (lowercase)
        errors = commands.validate_console_params("myconsoleapp", "/tmp/test")
        assert len(errors) > 0
        assert any("uppercase" in error.lower() for error in errors)

        # Empty project name
        errors = commands.validate_console_params("", "/tmp/test")
        assert len(errors) > 0
        assert any("required" in error.lower() for error in errors)

        # Invalid characters in project name
        errors = commands.validate_console_params("My App", "/tmp/test")
        assert len(errors) > 0
        assert any("invalid characters" in error.lower() for error in errors)


class TestCSharpProjectGenerator:
    """Test C# project generation."""

    def test_generator_initialization(self):
        """Test generator can be initialized."""
        generator = CSharpProjectGenerator()
        assert generator is not None
        assert generator.working_directory is not None

    def test_command_validation(self):
        """Test that only allowed commands are permitted."""
        generator = CSharpProjectGenerator()

        assert generator._is_command_allowed("dotnet")
        assert generator._is_command_allowed("git")
        assert not generator._is_command_allowed("rm")
        assert not generator._is_command_allowed("sudo")

    def test_console_project_validation(self):
        """Test console project parameter validation."""
        generator = CSharpProjectGenerator()

        # Test with valid parameters
        result = generator.generate_project("console", "TestConsole", "/tmp/test_console")

        # Should fail because we can't actually run dotnet in tests
        # But validation should pass
        assert "validation_errors" not in result or len(result.get("validation_errors", [])) == 0


class TestTemplateProcessor:
    """Test template processing functionality."""

    def test_processor_initialization(self):
        """Test processor can be initialized."""
        processor = TemplateProcessor()
        assert processor is not None

    def test_supported_template_types(self):
        """Test that supported template types are returned."""
        processor = TemplateProcessor()
        types = processor.get_supported_template_types()

        assert "csharp_console" in types
        assert "csharp_project" in types
        assert "command_template" in types
        assert "file_template" in types

    def test_csharp_project_types(self):
        """Test that C# project types are available."""
        processor = TemplateProcessor()
        project_types = processor.get_csharp_project_types()

        assert "console" in project_types
        assert "classlib" in project_types
        assert "webapi" in project_types

    def test_csharp_console_validation(self):
        """Test C# console parameter validation."""
        processor = TemplateProcessor()

        # Valid parameters
        errors = processor.validate_csharp_parameters(
            "console", {"project_name": "TestConsole", "output_path": "/tmp/test"}
        )
        assert len(errors) == 0

        # Invalid parameters
        errors = processor.validate_csharp_parameters(
            "console",
            {
                "project_name": "testconsole",  # lowercase
                "output_path": "/tmp/test",
            },
        )
        assert len(errors) > 0


class TestCSharpConsoleIntegration:
    """Integration tests for C# console template."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_console_template_structure(self, temp_dir):
        """Test that console template creates proper structure."""
        # This test would require actual dotnet CLI execution
        # For now, we'll test the command structure

        commands = CSharpCommands()
        console_cmd = commands.get_project_commands()["console"]

        # Verify command structure
        assert console_cmd["command"] == "dotnet"
        assert "new" in console_cmd["args"]
        assert "console" in console_cmd["args"]
        assert "{project_name}" in console_cmd["args"]
        assert "{output_path}" in console_cmd["args"]

        # Verify post-generation steps
        assert "post_generation" in console_cmd
        assert "customize_namespace" in console_cmd["post_generation"]
        assert "add_basic_structure" in console_cmd["post_generation"]

    def test_console_specific_commands(self, temp_dir):
        """Test console-specific commands are available."""
        commands = CSharpCommands()
        console_commands = commands.get_console_specific_commands()

        assert "add_package" in console_commands
        assert "add_reference" in console_commands
        assert "build" in console_commands
        assert "run" in console_commands

        # Verify build command
        build_cmd = console_commands["build"]
        assert build_cmd["command"] == "dotnet"
        assert "build" in build_cmd["args"]

        # Verify run command
        run_cmd = console_commands["run"]
        assert run_cmd["command"] == "dotnet"
        assert "run" in run_cmd["args"]
