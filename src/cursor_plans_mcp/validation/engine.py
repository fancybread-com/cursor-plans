"""
Main validation engine that orchestrates all validation layers.
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from .results import ValidationResult
from .validators import (
    SyntaxValidator,
    SchemaValidator,
    LogicValidator,
    ContextValidator,
    CursorRulesValidator,
    ConstraintValidator
)


class ValidationEngine:
    """
    Main validation engine that runs all validation layers.

    Provides comprehensive validation of development plans including:
    - Syntax validation (YAML structure, required fields)
    - Schema validation (Pydantic model compliance)
    - Logic validation (dependencies, conflicts)
    - Context validation (file existence, context usage)
    - Cursor Rules validation (team standards, coding practices)
    - Constraint validation (custom rules, business logic)
    """

    def __init__(self):
        """Initialize validation engine with all validators."""
        self.validators = [
            SyntaxValidator(),
            SchemaValidator(),
            LogicValidator(),
            ContextValidator(),
            CursorRulesValidator(),
            ConstraintValidator()
        ]

    async def validate_plan_file(self, plan_file_path: str, strict_mode: bool = False, check_cursor_rules: bool = True) -> ValidationResult:
        """
        Validate a development plan file.

        Args:
            plan_file_path: Path to the .devplan file to validate
            strict_mode: If True, warnings are treated as errors
            check_cursor_rules: If False, skip Cursor Rules validation

        Returns:
            ValidationResult with all validation issues found
        """
        combined_result = ValidationResult()

        # Check if file exists
        if not os.path.exists(plan_file_path):
            combined_result.add_error(
                f"Plan file not found: {plan_file_path}",
                "File system",
                "Ensure the plan file exists and the path is correct"
            )
            return combined_result

        # Load and parse the plan file
        try:
            plan_data = await self._load_plan_file(plan_file_path)
        except Exception as e:
            combined_result.add_error(
                f"Failed to load plan file: {str(e)}",
                plan_file_path,
                "Check YAML syntax and file permissions"
            )
            return combined_result

        # Run all validation layers
        validators_to_run = self.validators.copy()

        # Skip Cursor Rules validation if disabled
        if not check_cursor_rules:
            validators_to_run = [v for v in validators_to_run if not isinstance(v, CursorRulesValidator)]

        for validator in validators_to_run:
            try:
                result = await validator.validate(plan_data, plan_file_path)

                # Track which layers passed/failed
                if result.issues:
                    combined_result.layers_failed.append(validator.name)
                else:
                    combined_result.layers_passed.append(validator.name)

                # Merge results
                combined_result.issues.extend(result.issues)

            except Exception as e:
                # If a validator fails, record it as a validation error
                combined_result.add_error(
                    f"{validator.name} failed: {str(e)}",
                    f"Validator: {validator.__class__.__name__}",
                    "This may indicate a bug in the validation system"
                )
                combined_result.layers_failed.append(validator.name)

        # Apply strict mode if enabled
        if strict_mode:
            self._apply_strict_mode(combined_result)

        return combined_result

    async def validate_plan_data(self, plan_data: Dict[str, Any], plan_file_path: str = "plan_data", strict_mode: bool = False, check_cursor_rules: bool = True) -> ValidationResult:
        """
        Validate plan data directly (without loading from file).

        Args:
            plan_data: Plan data as dictionary
            plan_file_path: Virtual path for error reporting
            strict_mode: If True, warnings are treated as errors
            check_cursor_rules: If False, skip Cursor Rules validation

        Returns:
            ValidationResult with all validation issues found
        """
        combined_result = ValidationResult()

        # Run all validation layers
        validators_to_run = self.validators.copy()

        # Skip Cursor Rules validation if disabled
        if not check_cursor_rules:
            validators_to_run = [v for v in validators_to_run if not isinstance(v, CursorRulesValidator)]

        for validator in validators_to_run:
            try:
                result = await validator.validate(plan_data, plan_file_path)

                # Track which layers passed/failed
                if result.issues:
                    combined_result.layers_failed.append(validator.name)
                else:
                    combined_result.layers_passed.append(validator.name)

                # Merge results
                combined_result.issues.extend(result.issues)

            except Exception as e:
                # If a validator fails, record it as a validation error
                combined_result.add_error(
                    f"{validator.name} failed: {str(e)}",
                    f"Validator: {validator.__class__.__name__}",
                    "This may indicate a bug in the validation system"
                )
                combined_result.layers_failed.append(validator.name)

        # Apply strict mode if enabled
        if strict_mode:
            self._apply_strict_mode(combined_result)

        return combined_result

    async def _load_plan_file(self, plan_file_path: str) -> Dict[str, Any]:
        """Load and parse a YAML plan file."""
        with open(plan_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML
        try:
            data = yaml.safe_load(content)
            if data is None:
                raise ValueError("Plan file is empty or contains only comments")
            if not isinstance(data, dict):
                raise ValueError("Plan file must contain a YAML dictionary at the root level")
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {str(e)}")

    def _apply_strict_mode(self, result: ValidationResult):
        """Convert warnings to errors in strict mode."""
        for issue in result.issues:
            if issue.type.value == "warning":
                issue.type = issue.type.__class__("error")  # Convert warning to error

    def get_validator_info(self) -> List[Dict[str, str]]:
        """Get information about all available validators."""
        return [
            {
                "name": validator.name,
                "class": validator.__class__.__name__,
                "description": validator.__class__.__doc__ or "No description available"
            }
            for validator in self.validators
        ]
