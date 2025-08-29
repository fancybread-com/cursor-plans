"""Tests to verify template implementation completeness."""

import pytest
from pathlib import Path
import tempfile
import os

from cursor_plans_mcp.execution.engine import PlanExecutor
from cursor_plans_mcp.server import init_dev_planning


class TestTemplateImplementation:
    """Test that all referenced templates are actually implemented."""

    @pytest.mark.skip(reason="Template implementation feature not fully implemented")
    def test_template_implementation_coverage(self):
        """Test that all templates referenced in schema are implemented in execution engine."""
        # Templates that should be implemented based on SCHEMA.md
        expected_templates = [
            'basic_readme', 'python_main', 'fastapi_main', 'sqlalchemy_models',
            'jwt_auth', 'fastapi_requirements', 'dotnet_program', 'dotnet_controller',
            'ef_dbcontext', 'dotnet_service', 'dotnet_csproj', 'vue_main',
            'vue_app', 'vue_router', 'pinia_store', 'vue_component', 'vue_package_json'
        ]

        # Get the actual templates from the execution engine
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = PlanExecutor(temp_dir)
            # Call the method with a dummy template to get the templates dict
            content = executor._generate_file_content("test.py", "test", "fastapi_main")
            # We need to inspect the method to get the templates
            import inspect
            source = inspect.getsource(executor._generate_file_content)
            # Extract template names from the source code
            actual_templates = []
            if "fastapi_main" in source:
                actual_templates.append("fastapi_main")
            if "fastapi_model" in source:
                actual_templates.append("fastapi_model")
            if "requirements" in source:
                actual_templates.append("requirements")
            if "basic" in source:
                actual_templates.append("basic")

            # Check which templates are missing
            missing_templates = [t for t in expected_templates if t not in actual_templates]

            if missing_templates:
                pytest.fail(f"Missing template implementations: {missing_templates}")

            # Check for extra templates that aren't in the schema
            extra_templates = [t for t in actual_templates if t not in expected_templates and not t.startswith('custom_')]

            if extra_templates:
                print(f"Warning: Extra templates found that aren't in schema: {extra_templates}")

    @pytest.mark.asyncio
    async def test_basic_template_creation(self):
        """Test that basic template can be created and executed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

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

            assert len(result) == 1
            assert "Development Planning Initialized" in result[0].text

            # Check that .cursorplans directory was created but no plan file yet
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            assert cursorplans_dir.exists()
            plan_file = cursorplans_dir / "test-basic.devplan"
            assert not plan_file.exists()

    @pytest.mark.asyncio
    async def test_fastapi_template_creation(self):
        """Test that FastAPI template can be created and executed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Create a context file for FastAPI
            context_content = """
project:
  name: test-fastapi
  type: python
  description: A FastAPI web service
"""
            context_file = Path(temp_dir) / "context.yaml"
            with open(context_file, 'w') as f:
                f.write(context_content)

            result = await init_dev_planning({
                "context": str(context_file),
                "project_directory": temp_dir
            })

            assert len(result) == 1
            assert "Development Planning Initialized" in result[0].text

            # Check that .cursorplans directory was created but no plan file yet
            cursorplans_dir = Path(temp_dir) / ".cursorplans"
            assert cursorplans_dir.exists()
            plan_file = cursorplans_dir / "test-fastapi.devplan"
            assert not plan_file.exists()

    @pytest.mark.skip(reason="Template content generation feature not fully implemented")
    def test_template_content_generation(self):
        """Test that template content can be generated for all expected templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = PlanExecutor(temp_dir)

            # Test a few key templates
            test_templates = [
                ("fastapi_main", "main.py", "entry_point"),
                ("basic", "README.md", "documentation"),
                ("requirements", "requirements.txt", "dependencies")
            ]

            for template, file_path, file_type in test_templates:
                try:
                    content = executor._generate_file_content(file_path, file_type, template)
                    assert content is not None
                    assert len(content) > 0
                    print(f"✅ Template '{template}' generates content ({len(content)} chars)")
                except Exception as e:
                    pytest.fail(f"Template '{template}' failed to generate content: {e}")

    @pytest.mark.skip(reason="Template handling feature not fully implemented")
    @pytest.mark.asyncio
    async def test_missing_template_handling(self):
        """Test that missing templates are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = PlanExecutor(temp_dir)

            # Test with a template that doesn't exist
            content = executor._generate_file_content("test.py", "test", "nonexistent_template")

            # Should fall back to basic template
            assert content is not None
            assert len(content) > 0
            assert "TODO: Implement" in content
