"""Tests for C# templates functionality."""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.cursor_plans_mcp.execution.template_processor import TemplateProcessor
from src.cursor_plans_mcp.templates.languages.csharp.commands import CSharpCommands


class TestCSharpTemplates:
    """Test C# templates functionality."""

    def test_csharp_commands_initialization(self):
        """Test CSharpCommands can be initialized."""
        commands = CSharpCommands()
        assert commands is not None

    def test_get_project_commands(self):
        """Test getting project commands."""
        commands = CSharpCommands()
        project_commands = commands.get_project_commands()

        # Check that all expected project types are available
        expected_types = ["console", "classlib", "webapi", "mvc", "blazor", "xunit", "mstest"]
        for project_type in expected_types:
            assert project_type in project_commands

        # Check console command structure
        console_cmd = project_commands["console"]
        assert console_cmd["command"] == "dotnet"
        assert "console" in console_cmd["args"]
        assert "project_name" in console_cmd["required_params"]
        assert "output_path" in console_cmd["required_params"]

    def test_get_solution_commands(self):
        """Test getting solution commands."""
        commands = CSharpCommands()
        solution_commands = commands.get_solution_commands()

        assert "create_solution" in solution_commands
        assert "add_project_to_solution" in solution_commands

        # Check create_solution command structure
        create_sln_cmd = solution_commands["create_solution"]
        assert create_sln_cmd["command"] == "dotnet"
        assert "sln" in create_sln_cmd["args"]
        assert "solution_name" in create_sln_cmd["required_params"]

    def test_get_console_specific_commands(self):
        """Test getting console-specific commands."""
        commands = CSharpCommands()
        console_commands = commands.get_console_specific_commands()

        expected_commands = ["add_package", "add_reference", "build", "run"]
        for cmd in expected_commands:
            assert cmd in console_commands

        # Check build command
        build_cmd = console_commands["build"]
        assert build_cmd["command"] == "dotnet"
        assert "build" in build_cmd["args"]

        # Check run command
        run_cmd = console_commands["run"]
        assert run_cmd["command"] == "dotnet"
        assert "run" in run_cmd["args"]

    def test_get_supported_frameworks(self):
        """Test getting supported frameworks from config."""
        commands = CSharpCommands()
        frameworks = commands.get_supported_frameworks()

        assert isinstance(frameworks, list)
        assert "net8.0" in frameworks
        assert "net9.0" in frameworks

    def test_get_default_framework(self):
        """Test getting default framework from config."""
        commands = CSharpCommands()
        default_framework = commands.get_default_framework()

        assert isinstance(default_framework, str)
        assert default_framework == "net8.0"

    def test_validate_console_params_success(self):
        """Test successful console parameter validation."""
        commands = CSharpCommands()
        errors = commands.validate_console_params("TestConsole", "/tmp/test")

        assert len(errors) == 0

    def test_validate_console_params_invalid_name(self):
        """Test console parameter validation with invalid project name."""
        commands = CSharpCommands()
        errors = commands.validate_console_params("testconsole", "/tmp/test")

        assert len(errors) > 0
        assert any("uppercase" in error.lower() for error in errors)

    def test_validate_console_params_empty_name(self):
        """Test console parameter validation with empty project name."""
        commands = CSharpCommands()
        errors = commands.validate_console_params("", "/tmp/test")

        assert len(errors) > 0
        assert any("required" in error.lower() for error in errors)

    def test_validate_console_params_invalid_chars(self):
        """Test console parameter validation with invalid characters."""
        commands = CSharpCommands()
        errors = commands.validate_console_params("Test Console", "/tmp/test")

        assert len(errors) > 0
        assert any("invalid characters" in error.lower() for error in errors)

    def test_validate_console_params_invalid_framework(self):
        """Test console parameter validation with invalid framework."""
        commands = CSharpCommands()
        errors = commands.validate_console_params("TestConsole", "/tmp/test", framework="net5.0")

        assert len(errors) > 0
        assert any("net6.0" in error or "net7.0" in error or "net8.0" in error or "net9.0" in error for error in errors)

    def test_validate_console_params_valid_framework(self):
        """Test console parameter validation with valid framework."""
        commands = CSharpCommands()
        errors = commands.validate_console_params("TestConsole", "/tmp/test", framework="net9.0")

        assert len(errors) == 0


class TestTemplateProcessor:
    """Test template processor functionality."""

    def test_initialization(self):
        """Test TemplateProcessor can be initialized."""
        processor = TemplateProcessor()
        assert processor is not None
        assert processor.csharp_generator is not None

    def test_get_supported_template_types(self):
        """Test getting supported template types."""
        processor = TemplateProcessor()
        types = processor.get_supported_template_types()

        expected_types = ["command_template", "file_template", "csharp_project", "csharp_console"]

        for template_type in expected_types:
            assert template_type in types

    def test_get_csharp_project_types(self):
        """Test getting C# project types."""
        processor = TemplateProcessor()
        project_types = processor.get_csharp_project_types()

        expected_types = ["console", "classlib", "webapi", "mvc", "blazor", "xunit", "mstest"]
        for project_type in expected_types:
            assert project_type in project_types

    def test_validate_csharp_parameters_success(self):
        """Test successful C# parameter validation."""
        processor = TemplateProcessor()
        errors = processor.validate_csharp_parameters(
            "console", {"project_name": "TestConsole", "output_path": "/tmp/test"}
        )

        assert len(errors) == 0

    def test_validate_csharp_parameters_invalid(self):
        """Test C# parameter validation with invalid parameters."""
        processor = TemplateProcessor()
        errors = processor.validate_csharp_parameters(
            "console",
            {
                "project_name": "testconsole",  # lowercase
                "output_path": "/tmp/test",
            },
        )

        assert len(errors) > 0
        assert any("uppercase" in error.lower() for error in errors)

    def test_validate_csharp_parameters_unknown_type(self):
        """Test C# parameter validation with unknown project type."""
        processor = TemplateProcessor()
        errors = processor.validate_csharp_parameters(
            "unknown", {"project_name": "TestConsole", "output_path": "/tmp/test"}
        )

        assert len(errors) == 0  # Should return empty list for unknown types


class TestCSharpTemplateIntegration:
    """Integration tests for C# templates."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_console_command_structure(self, temp_workspace):
        """Test console command structure."""
        commands = CSharpCommands()
        console_cmd = commands.get_project_commands()["console"]

        # Verify command structure
        assert console_cmd["command"] == "dotnet"
        assert "new" in console_cmd["args"]
        assert "console" in console_cmd["args"]
        assert "{project_name}" in console_cmd["args"]
        assert "{output_path}" in console_cmd["args"]

        # Verify required parameters
        required_params = console_cmd["required_params"]
        assert "project_name" in required_params
        assert "output_path" in required_params

        # Verify optional parameters
        optional_params = console_cmd["optional_params"]
        assert "framework" in optional_params
        assert "lang_version" in optional_params

    def test_webapi_command_structure(self, temp_workspace):
        """Test Web API command structure."""
        commands = CSharpCommands()
        webapi_cmd = commands.get_project_commands()["webapi"]

        # Verify command structure
        assert webapi_cmd["command"] == "dotnet"
        assert "new" in webapi_cmd["args"]
        assert "webapi" in webapi_cmd["args"]
        assert "{project_name}" in webapi_cmd["args"]
        assert "{output_path}" in webapi_cmd["args"]

        # Verify optional parameters
        optional_params = webapi_cmd["optional_params"]
        assert "framework" in optional_params
        assert "auth" in optional_params
        assert "https" in optional_params

    def test_solution_command_structure(self, temp_workspace):
        """Test solution command structure."""
        commands = CSharpCommands()
        create_sln_cmd = commands.get_solution_commands()["create_solution"]

        # Verify command structure
        assert create_sln_cmd["command"] == "dotnet"
        assert "new" in create_sln_cmd["args"]
        assert "sln" in create_sln_cmd["args"]
        assert "{solution_name}" in create_sln_cmd["args"]

    def test_framework_configuration(self, temp_workspace):
        """Test framework configuration integration."""
        commands = CSharpCommands()

        # Test supported frameworks
        supported_frameworks = commands.get_supported_frameworks()
        assert "net8.0" in supported_frameworks
        assert "net9.0" in supported_frameworks

        # Test default framework
        default_framework = commands.get_default_framework()
        assert default_framework == "net8.0"

        # Test validation with supported frameworks
        for framework in supported_frameworks:
            errors = commands.validate_console_params("TestConsole", "/tmp/test", framework=framework)
            assert len(errors) == 0

    def test_template_processor_integration(self, temp_workspace):
        """Test template processor integration with C# commands."""
        processor = TemplateProcessor()
        commands = CSharpCommands()

        # Test that processor can access C# project types
        project_types = processor.get_csharp_project_types()
        assert len(project_types) > 0

        # Test that all project types from commands are available in processor
        command_project_types = list(commands.get_project_commands().keys())
        for project_type in command_project_types:
            assert project_type in project_types

    def test_parameter_validation_integration(self, temp_workspace):
        """Test parameter validation integration."""
        processor = TemplateProcessor()

        # Test valid parameters
        valid_params = {"project_name": "TestConsole", "output_path": "/tmp/test", "framework": "net8.0"}
        errors = processor.validate_csharp_parameters("console", valid_params)
        assert len(errors) == 0

        # Test invalid parameters
        invalid_params = {
            "project_name": "testconsole",  # lowercase
            "output_path": "/tmp/test",
        }
        errors = processor.validate_csharp_parameters("console", invalid_params)
        assert len(errors) > 0

    def test_command_argument_substitution(self, temp_workspace):
        """Test command argument substitution."""
        commands = CSharpCommands()
        console_cmd = commands.get_project_commands()["console"]

        # Test that arguments contain placeholders
        args = console_cmd["args"]
        assert "{project_name}" in args
        assert "{output_path}" in args

        # Test that we can substitute values
        project_name = "TestConsole"
        output_path = "/tmp/test"

        # This would be done by the template engine in practice
        substituted_args = [
            arg.replace("{project_name}", project_name).replace("{output_path}", output_path) for arg in args
        ]

        assert project_name in substituted_args
        assert output_path in substituted_args
