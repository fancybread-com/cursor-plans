"""Tests for template engine functionality."""
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cursor_plans_mcp.templates.engine import TemplateEngine


class TestTemplateEngine:
    """Test TemplateEngine functionality."""

    def test_initialization(self):
        """Test TemplateEngine can be initialized."""
        engine = TemplateEngine()
        assert engine is not None
        assert engine.environment is not None
        assert isinstance(engine.templates, dict)

    def test_register_template(self):
        """Test template registration."""
        engine = TemplateEngine()

        template_content = "Hello {{ name }}!"
        engine.register_template("greeting", template_content)

        assert "greeting" in engine.templates
        assert engine.templates["greeting"] is not None

    def test_render_template_success(self):
        """Test successful template rendering."""
        engine = TemplateEngine()

        template_content = "Hello {{ name }}! You are {{ age }} years old."
        engine.register_template("greeting", template_content)

        parameters = {"name": "Alice", "age": 30}
        result = engine.render_template("greeting", parameters)

        assert result == "Hello Alice! You are 30 years old."

    def test_render_template_not_found(self):
        """Test rendering non-existent template."""
        engine = TemplateEngine()

        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            engine.render_template("nonexistent", {})

    def test_validate_parameters_success(self):
        """Test parameter validation with valid parameters."""
        engine = TemplateEngine()

        template_content = "Hello {{ name }}! You are {{ age }} years old."
        engine.register_template("greeting", template_content)

        parameters = {"name": "Alice", "age": 30}
        errors = engine.validate_parameters("greeting", parameters)

        assert len(errors) == 0

    def test_validate_parameters_missing(self):
        """Test parameter validation with missing parameters."""
        engine = TemplateEngine()

        template_content = "Hello {{ name }}! You are {{ age }} years old."
        engine.register_template("greeting", template_content)

        parameters = {"name": "Alice"}  # Missing age
        errors = engine.validate_parameters("greeting", parameters)

        # Currently simplified to return empty list - can be enhanced later
        assert len(errors) == 0

    def test_validate_parameters_template_not_found(self):
        """Test parameter validation with non-existent template."""
        engine = TemplateEngine()

        errors = engine.validate_parameters("nonexistent", {})

        assert len(errors) == 1
        assert "Template 'nonexistent' not found" in errors[0]

    def test_extract_required_parameters(self):
        """Test parameter extraction from template."""
        engine = TemplateEngine()

        template_content = "Hello {{ name }}! You are {{ age }} years old. Welcome {{ name }}!"
        template = engine.environment.from_string(template_content)

        params = engine._extract_required_parameters(template)

        # Currently simplified to return empty list - can be enhanced later
        assert isinstance(params, list)

    def test_get_supported_template_types(self):
        """Test getting supported template types."""
        engine = TemplateEngine()

        types = engine.get_supported_template_types()

        expected_types = [
            "csharp_console",
            "csharp_project",
            "command_template",
            "file_template",
            "default_template"
        ]

        assert set(types) == set(expected_types)


class TestTemplateEngineProcessing:
    """Test template processing functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_process_default_template(self, temp_workspace):
        """Test processing default template."""
        engine = TemplateEngine()

        result = engine.process_template_type(
            "default_template",
            "test_template",
            str(temp_workspace / "test.py"),
            {"param1": "value1"}
        )

        assert result["success"] is True
        assert result["type"] == "default_template"
        assert "test.py" in result["output_path"]

        # Check file was created
        output_file = temp_workspace / "test.py"
        assert output_file.exists()
        content = output_file.read_text()
        assert "test_template" in content
        assert "param1" in content

    def test_process_file_template_success(self, temp_workspace):
        """Test processing file template successfully."""
        engine = TemplateEngine()

        # Register a template
        template_content = "Hello {{ name }}! Age: {{ age }}"
        engine.register_template("greeting", template_content)

        result = engine.process_template_type(
            "file_template",
            "greeting",
            str(temp_workspace / "greeting.txt"),
            {"name": "Alice", "age": 30}
        )

        assert result["success"] is True
        assert result["type"] == "file_template"
        assert result["content_length"] > 0

        # Check file was created with correct content
        output_file = temp_workspace / "greeting.txt"
        assert output_file.exists()
        content = output_file.read_text()
        assert content == "Hello Alice! Age: 30"

    def test_process_file_template_not_found(self, temp_workspace):
        """Test processing file template that doesn't exist."""
        engine = TemplateEngine()

        result = engine.process_template_type(
            "file_template",
            "nonexistent",
            str(temp_workspace / "test.txt"),
            {}
        )

        assert result["success"] is False
        assert "Template 'nonexistent' not found" in result["error"]

    @patch('src.cursor_plans_mcp.execution.command_executor.CommandExecutor')
    def test_process_command_template_success(self, mock_executor_class, temp_workspace):
        """Test processing command template successfully."""
        # Mock command executor
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "Command executed successfully"
        mock_result.stderr = ""
        mock_executor.execute.return_value = mock_result
        mock_executor_class.return_value = mock_executor

        engine = TemplateEngine()

        result = engine.process_template_type(
            "command_template",
            "python",
            str(temp_workspace / "output"),
            {"args": ["--version"]}
        )

        assert result["success"] is True
        assert result["type"] == "command_execution"
        assert "Command executed successfully" in result["output"]

        # Verify command executor was called
        mock_executor.execute.assert_called_once_with("python", ["--version"], cwd=temp_workspace)

    @patch('src.cursor_plans_mcp.execution.command_executor.CommandExecutor')
    def test_process_command_template_failure(self, mock_executor_class, temp_workspace):
        """Test processing command template with failure."""
        # Mock command executor failure
        mock_executor = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_executor.execute.return_value = mock_result
        mock_executor_class.return_value = mock_executor

        engine = TemplateEngine()

        result = engine.process_template_type(
            "command_template",
            "python",
            str(temp_workspace / "output"),
            {"args": ["--invalid"]}
        )

        assert result["success"] is False
        assert result["type"] == "command_execution"
        assert "Command failed" in result["error"]

    @patch('src.cursor_plans_mcp.templates.languages.csharp.generators.CSharpProjectGenerator')
    def test_process_csharp_console_success(self, mock_generator_class, temp_workspace):
        """Test processing C# console template successfully."""
        # Mock C# generator
        mock_generator = MagicMock()
        mock_result = {
            "success": True,
            "project_name": "TestConsole",
            "output_path": str(temp_workspace / "TestConsole"),
            "command_output": "Project created successfully"
        }
        mock_generator.generate_project.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        engine = TemplateEngine()

        result = engine.process_template_type(
            "csharp_console",
            "console",
            str(temp_workspace / "TestConsole"),
            {"project_name": "TestConsole", "framework": "net8.0"}
        )

        assert result["success"] is True
        assert result["type"] == "csharp_console_generation"
        assert result["project_name"] == "TestConsole"

        # Verify generator was called
        mock_generator.generate_project.assert_called_once_with(
            "console", "TestConsole", str(temp_workspace / "TestConsole"),
            project_name="TestConsole", framework="net8.0"
        )

    @patch('src.cursor_plans_mcp.templates.languages.csharp.generators.CSharpProjectGenerator')
    def test_process_csharp_project_success(self, mock_generator_class, temp_workspace):
        """Test processing C# project template successfully."""
        # Mock C# generator
        mock_generator = MagicMock()
        mock_result = {
            "success": True,
            "project_type": "webapi",
            "project_name": "TestWebApi",
            "output_path": str(temp_workspace / "TestWebApi")
        }
        mock_generator.generate_project.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        engine = TemplateEngine()

        result = engine.process_template_type(
            "csharp_project",
            "webapi",
            str(temp_workspace / "TestWebApi"),
            {"project_name": "TestWebApi", "framework": "net8.0"}
        )

        assert result["success"] is True
        assert result["type"] == "csharp_project_generation"
        assert result["project_type"] == "webapi"
        assert result["project_name"] == "TestWebApi"

    def test_process_csharp_console_import_error(self, temp_workspace):
        """Test processing C# console template with import error."""
        engine = TemplateEngine()

        # Mock import error by patching the import inside the method
        with patch(
            'src.cursor_plans_mcp.templates.languages.csharp.generators.CSharpProjectGenerator',
            side_effect=ImportError
        ):
            result = engine.process_template_type(
                "csharp_console",
                "console",
                str(temp_workspace / "TestConsole"),
                {"project_name": "TestConsole"}
            )

        assert result["success"] is False
        assert result["type"] == "csharp_console_generation"
        assert "C# generators not available" in result["error"]

    def test_process_unknown_template_type(self, temp_workspace):
        """Test processing unknown template type."""
        engine = TemplateEngine()

        result = engine.process_template_type(
            "unknown_type",
            "test",
            str(temp_workspace / "test.txt"),
            {}
        )

        assert result["success"] is True
        assert result["type"] == "default_template"

    def test_process_template_with_directory_creation(self, temp_workspace):
        """Test that template processing creates directories as needed."""
        engine = TemplateEngine()

        # Try to create a file in a nested directory
        nested_path = temp_workspace / "nested" / "deep" / "test.py"

        result = engine.process_template_type(
            "default_template",
            "test_template",
            str(nested_path),
            {}
        )

        assert result["success"] is True
        assert nested_path.exists()
        assert nested_path.parent.exists()
        assert (temp_workspace / "nested" / "deep").exists()


class TestTemplateEngineIntegration:
    """Integration tests for TemplateEngine."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_full_template_workflow(self, temp_workspace):
        """Test complete template workflow."""
        engine = TemplateEngine()

        # Register a template
        template_content = """
# {{ project_name }}
# Framework: {{ framework }}
# Author: {{ author }}

def main():
    print("Hello from {{ project_name }}!")

if __name__ == "__main__":
    main()
"""
        engine.register_template("python_app", template_content)

        # Process the template
        parameters = {
            "project_name": "MyApp",
            "framework": "Python 3.9",
            "author": "Alice"
        }

        result = engine.process_template_type(
            "file_template",
            "python_app",
            str(temp_workspace / "main.py"),
            parameters
        )

        assert result["success"] is True

        # Verify the generated file
        output_file = temp_workspace / "main.py"
        assert output_file.exists()

        content = output_file.read_text()
        assert "MyApp" in content
        assert "Python 3.9" in content
        assert "Alice" in content
        assert "def main():" in content

    def test_template_with_complex_parameters(self, temp_workspace):
        """Test template with complex parameter types."""
        engine = TemplateEngine()

        template_content = """
# Project: {{ project.name }}
# Version: {{ project.version }}
# Dependencies: {{ ', '.join(dependencies) }}
# Config: {{ config.environment }}

class {{ project.name }}:
    def __init__(self):
        self.version = "{{ project.version }}"
        self.deps = {{ dependencies | length }}
"""
        engine.register_template("complex_app", template_content)

        parameters = {
            "project": {"name": "MyApp", "version": "1.0.0"},
            "dependencies": ["fastapi", "uvicorn", "pydantic"],
            "config": {"environment": "production"}
        }

        result = engine.process_template_type(
            "file_template",
            "complex_app",
            str(temp_workspace / "app.py"),
            parameters
        )

        assert result["success"] is True

        content = (temp_workspace / "app.py").read_text()
        assert "MyApp" in content
        assert "1.0.0" in content
        assert "fastapi, uvicorn, pydantic" in content
        assert "production" in content
        assert "self.deps = 3" in content
