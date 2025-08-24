"""
Unit tests for the ValidationEngine and individual validators.
"""

import pytest
import yaml
from cursor_plans_mcp.validation import ValidationEngine, ValidationResult, IssueType


class TestValidationEngine:
    """Test the main ValidationEngine."""

    @pytest.mark.asyncio
    async def test_validate_valid_plan(self, sample_basic_plan, temp_dir):
        """Test validation of a valid plan."""
        # Create plan file
        plan_file = temp_dir / "valid.devplan"
        with open(plan_file, 'w') as f:
            yaml.dump(sample_basic_plan, f)

        engine = ValidationEngine()
        result = await engine.validate_plan_file(str(plan_file), check_cursor_rules=False)

        # Should have some warnings but no errors
        assert len(result.errors) == 0
        assert result.is_valid
        assert "Syntax validation" in result.layers_passed
        assert "Schema validation" in result.layers_passed

    @pytest.mark.asyncio
    async def test_validate_invalid_plan(self, sample_invalid_plan, temp_dir):
        """Test validation of a plan with issues."""
        # Create plan file
        plan_file = temp_dir / "invalid.devplan"
        with open(plan_file, 'w') as f:
            yaml.dump(sample_invalid_plan, f)

        engine = ValidationEngine()
        result = await engine.validate_plan_file(str(plan_file), check_cursor_rules=False)

        # Should have errors
        assert len(result.errors) > 0
        assert not result.is_valid

        # Check for expected error types
        error_messages = [error.message for error in result.errors]
        assert any("Duplicate file path" in msg for msg in error_messages)

    @pytest.mark.asyncio
    async def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        engine = ValidationEngine()
        result = await engine.validate_plan_file("nonexistent.devplan")

        assert len(result.errors) == 1
        assert "Plan file not found" in result.errors[0].message
        assert not result.is_valid

    @pytest.mark.asyncio
    async def test_validate_plan_data_directly(self, sample_basic_plan):
        """Test validation of plan data without file."""
        engine = ValidationEngine()
        result = await engine.validate_plan_data(
            sample_basic_plan,
            "test_plan",
            check_cursor_rules=False
        )

        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_strict_mode(self, sample_basic_plan, temp_dir):
        """Test strict mode converts warnings to errors."""
        # Create plan file
        plan_file = temp_dir / "plan.devplan"
        with open(plan_file, 'w') as f:
            yaml.dump(sample_basic_plan, f)

        engine = ValidationEngine()

        # Normal mode
        result_normal = await engine.validate_plan_file(
            str(plan_file),
            strict_mode=False,
            check_cursor_rules=False
        )

        # Strict mode
        result_strict = await engine.validate_plan_file(
            str(plan_file),
            strict_mode=True,
            check_cursor_rules=False
        )

        # In strict mode, warnings become errors
        if result_normal.has_warnings:
            assert len(result_strict.errors) >= len(result_normal.warnings)

    def test_get_validator_info(self):
        """Test getting validator information."""
        engine = ValidationEngine()
        info = engine.get_validator_info()

        assert len(info) > 0
        assert all("name" in validator for validator in info)
        assert all("class" in validator for validator in info)

        # Check that all expected validators are present
        validator_names = [v["name"] for v in info]
        expected_validators = [
            "Syntax validation",
            "Schema validation",
            "Logic validation",
            "Context validation",
            "Cursor Rules validation",
            "Constraint validation"
        ]

        for expected in expected_validators:
            assert expected in validator_names


class TestSyntaxValidator:
    """Test the SyntaxValidator."""

    @pytest.mark.asyncio
    async def test_missing_required_sections(self, temp_dir):
        """Test validation of plan missing required sections."""
        from cursor_plans_mcp.validation.validators.syntax import SyntaxValidator

        incomplete_plan = {
            "project": {"name": "test", "version": "1.0.0"}
            # Missing target_state, resources, phases
        }

        validator = SyntaxValidator()
        result = await validator.validate(incomplete_plan, "test.devplan")

        assert len(result.errors) >= 3  # Missing sections
        error_messages = [error.message for error in result.errors]
        assert any("Missing required section: target_state" in msg for msg in error_messages)
        assert any("Missing required section: resources" in msg for msg in error_messages)
        assert any("Missing required section: phases" in msg for msg in error_messages)

    @pytest.mark.asyncio
    async def test_invalid_project_structure(self):
        """Test validation of invalid project structure."""
        from cursor_plans_mcp.validation.validators.syntax import SyntaxValidator

        invalid_plan = {
            "project": "invalid_string",  # Should be dict
            "target_state": {},
            "resources": {},
            "phases": {}
        }

        validator = SyntaxValidator()
        result = await validator.validate(invalid_plan, "test.devplan")

        assert len(result.errors) >= 1
        assert any("Project section must be a dictionary" in error.message for error in result.errors)


class TestSchemaValidator:
    """Test the SchemaValidator."""

    @pytest.mark.asyncio
    async def test_valid_schema(self, sample_basic_plan):
        """Test validation of valid schema."""
        from cursor_plans_mcp.validation.validators.schema import SchemaValidator

        validator = SchemaValidator()
        result = await validator.validate(sample_basic_plan, "test.devplan")

        # Should pass schema validation
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_invalid_types(self):
        """Test validation of invalid data types."""
        from cursor_plans_mcp.validation.validators.schema import SchemaValidator

        invalid_plan = {
            "project": {
                "name": 123,  # Should be string
                "version": "1.0.0"
            },
            "target_state": {},
            "resources": {},
            "phases": {
                "test_phase": {
                    "priority": "invalid"  # Should be int
                }
            }
        }

        validator = SchemaValidator()
        result = await validator.validate(invalid_plan, "test.devplan")

        assert len(result.errors) >= 2
        error_messages = [error.message for error in result.errors]
        assert any("should be a string" in msg.lower() for msg in error_messages)
        assert any("should be an integer" in msg.lower() for msg in error_messages)


class TestLogicValidator:
    """Test the LogicValidator."""

    @pytest.mark.asyncio
    async def test_duplicate_file_paths(self):
        """Test detection of duplicate file paths."""
        from cursor_plans_mcp.validation.validators.logic import LogicValidator

        plan_with_duplicates = {
            "project": {"name": "test", "version": "1.0.0"},
            "target_state": {},
            "resources": {
                "files": [
                    {"path": "src/main.py", "type": "entry_point"},
                    {"path": "src/main.py", "type": "duplicate"}  # Duplicate
                ]
            },
            "phases": {}
        }

        validator = LogicValidator()
        result = await validator.validate(plan_with_duplicates, "test.devplan")

        assert len(result.errors) >= 1
        assert any("Duplicate file path" in error.message for error in result.errors)

    @pytest.mark.asyncio
    async def test_circular_dependencies(self):
        """Test detection of circular phase dependencies."""
        from cursor_plans_mcp.validation.validators.logic import LogicValidator

        plan_with_cycles = {
            "project": {"name": "test", "version": "1.0.0"},
            "target_state": {},
            "resources": {},
            "phases": {
                "phase_a": {
                    "priority": 1,
                    "dependencies": ["phase_b"]
                },
                "phase_b": {
                    "priority": 2,
                    "dependencies": ["phase_a"]  # Circular dependency
                }
            }
        }

        validator = LogicValidator()
        result = await validator.validate(plan_with_cycles, "test.devplan")

        assert len(result.errors) >= 1
        assert any("Circular dependency" in error.message for error in result.errors)


class TestCursorRulesValidator:
    """Test the CursorRulesValidator."""

    @pytest.mark.asyncio
    async def test_with_cursor_rules(self, sample_basic_plan, sample_cursorrules, temp_dir):
        """Test validation with Cursor rules present."""
        from cursor_plans_mcp.validation.validators.cursor_rules import CursorRulesValidator

        # Change to temp directory for rules file discovery
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            validator = CursorRulesValidator()
            result = await validator.validate(sample_basic_plan, "test.devplan")

            # Should find issues based on our sample rules
            assert len(result.issues) > 0

            # Should suggest missing elements based on rules
            issue_messages = [issue.message for issue in result.issues]
            # The exact messages depend on the plan content and rules

        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_without_cursor_rules(self, sample_basic_plan):
        """Test validation without Cursor rules file."""
        from cursor_plans_mcp.validation.validators.cursor_rules import CursorRulesValidator

        validator = CursorRulesValidator()
        result = await validator.validate(sample_basic_plan, "test.devplan")

        # Should suggest creating rules file
        assert len(result.suggestions) >= 1
        assert any("No .cursorrules file found" in suggestion.message for suggestion in result.suggestions)


class TestValidationResult:
    """Test the ValidationResult class."""

    def test_empty_result(self):
        """Test empty validation result."""
        result = ValidationResult()

        assert result.is_valid
        assert not result.has_warnings
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.suggestions) == 0

    def test_add_issues(self):
        """Test adding different types of issues."""
        result = ValidationResult()

        result.add_error("Test error", "location", "suggestion")
        result.add_warning("Test warning", "location")
        result.add_suggestion("Test suggestion", "location")

        assert not result.is_valid  # Has errors
        assert result.has_warnings
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1

    def test_format_for_cursor(self):
        """Test formatting results for Cursor display."""
        result = ValidationResult()
        result.layers_passed.append("Test validation")

        # Test successful result
        formatted = result.format_for_cursor()
        assert "Plan validation passed!" in formatted
        assert "Test validation" in formatted

        # Test result with issues
        result.add_error("Test error", "location", "fix suggestion")
        result.add_warning("Test warning", "location")
        result.layers_failed.append("Failed validation")

        formatted_with_issues = result.format_for_cursor()
        assert "Plan validation failed" in formatted_with_issues
        assert "Test error" in formatted_with_issues
        assert "Test warning" in formatted_with_issues
        assert "fix suggestion" in formatted_with_issues
