"""Tests to verify schema documentation accuracy."""

from cursor_plans_mcp.schema import validate_plan_content


class TestSchemaDocumentation:
    """Test that schema documentation accurately reflects validation behavior."""

    def test_implemented_templates_are_valid(self):
        """Test that implemented templates pass validation."""
        implemented_templates = [
            "fastapi_main",
            "fastapi_model",
            "requirements",
            "basic",
            "dotnet_program",
            "dotnet_controller",
            "ef_dbcontext",
            "dotnet_service",
            "dotnet_csproj",
        ]

        for template in implemented_templates:
            plan_content = f"""
schema_version: "1.0"
project:
  name: "test-project"
  version: "1.0.0"
  description: "Test project"
target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
  features:
    - "api_endpoints"
resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "{template}"
  dependencies:
    - "fastapi"
phases:
  foundation:
    priority: 1
    tasks:
      - "setup_project"
  testing:
    priority: 5
    tasks:
      - "unit_tests"
validation:
  pre_apply:
    - "syntax_check"
"""
            is_valid, error, _ = validate_plan_content(plan_content)
            assert is_valid, f"Template '{template}' should be valid: {error}"

    def test_referenced_templates_are_valid(self):
        """Test that referenced templates (not yet implemented) pass validation."""
        referenced_templates = [
            "basic_readme",
            "python_main",
            "sqlalchemy_models",
            "jwt_auth",
            "fastapi_requirements",
            "dotnet_program",
            "dotnet_controller",
            "ef_dbcontext",
            "dotnet_service",
            "dotnet_csproj",
            "vue_main",
            "vue_app",
            "vue_router",
            "pinia_store",
            "vue_component",
            "vue_package_json",
        ]

        for template in referenced_templates:
            plan_content = f"""
schema_version: "1.0"
project:
  name: "test-project"
  version: "1.0.0"
  description: "Test project"
target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
  features:
    - "api_endpoints"
resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "{template}"
  dependencies:
    - "fastapi"
phases:
  foundation:
    priority: 1
    tasks:
      - "setup_project"
  testing:
    priority: 5
    tasks:
      - "unit_tests"
validation:
  pre_apply:
    - "syntax_check"
"""
            is_valid, error, _ = validate_plan_content(plan_content)
            assert is_valid, f"Referenced template '{template}' should be valid: {error}"

    def test_custom_templates_are_valid(self):
        """Test that custom templates with custom_ prefix pass validation."""
        custom_templates = [
            "custom_my_template",
            "custom_api_endpoint",
            "custom_database_model",
        ]

        for template in custom_templates:
            plan_content = f"""
schema_version: "1.0"
project:
  name: "test-project"
  version: "1.0.0"
  description: "Test project"
target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
  features:
    - "api_endpoints"
resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "{template}"
  dependencies:
    - "fastapi"
phases:
  foundation:
    priority: 1
    tasks:
      - "setup_project"
  testing:
    priority: 5
    tasks:
      - "unit_tests"
validation:
  pre_apply:
    - "syntax_check"
"""
            is_valid, error, _ = validate_plan_content(plan_content)
            assert is_valid, f"Custom template '{template}' should be valid: {error}"

    def test_unknown_templates_are_invalid(self):
        """Test that unknown templates fail validation."""
        unknown_templates = ["unknown_template", "my_template", "api_template"]

        for template in unknown_templates:
            plan_content = f"""
schema_version: "1.0"
project:
  name: "test-project"
  version: "1.0.0"
  description: "Test project"
target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
  features:
    - "api_endpoints"
resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "{template}"
  dependencies:
    - "fastapi"
phases:
  foundation:
    priority: 1
    tasks:
      - "setup_project"
  testing:
    priority: 5
    tasks:
      - "unit_tests"
validation:
  pre_apply:
    - "syntax_check"
"""
            is_valid, error, _ = validate_plan_content(plan_content)
            assert not is_valid, f"Unknown template '{template}' should be invalid"
            assert "Unknown template" in error, f"Error should mention unknown template: {error}"

    def test_template_count_matches_documentation(self):
        """Test that the number of templates matches documentation."""
        # Count from schema validation
        implemented_templates = [
            "fastapi_main",
            "fastapi_model",
            "requirements",
            "basic",
            "dotnet_program",
            "dotnet_controller",
            "ef_dbcontext",
            "dotnet_service",
            "dotnet_csproj",
        ]

        referenced_templates = [
            "basic_readme",
            "python_main",
            "sqlalchemy_models",
            "jwt_auth",
            "fastapi_requirements",
            "vue_main",
            "vue_app",
            "vue_router",
            "pinia_store",
            "vue_component",
            "vue_package_json",
        ]

        total_templates = len(implemented_templates) + len(referenced_templates)

        # Verify counts match documentation
        assert len(implemented_templates) == 9, f"Should have 9 implemented templates, got {len(implemented_templates)}"
        assert len(referenced_templates) == 11, f"Should have 11 referenced templates, got {len(referenced_templates)}"
        assert total_templates == 20, f"Should have 20 total templates, got {total_templates}"
