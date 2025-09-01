"""
Schema validation using Pydantic models.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from ..results import ValidationResult
from .base import BaseValidator


class ProjectConfig(BaseModel):
    """Project configuration schema."""

    name: str
    version: str
    description: Optional[str] = None


class TargetState(BaseModel):
    """Target state schema."""

    architecture: Optional[List[Dict[str, str]]] = None
    features: Optional[List[str]] = None


class FileResource(BaseModel):
    """File resource schema."""

    path: str
    type: str
    template: Optional[str] = None
    dependencies: Optional[List[str]] = None


class Resources(BaseModel):
    """Resources schema."""

    files: Optional[List[FileResource]] = None
    dependencies: Optional[List[str]] = None


class Phase(BaseModel):
    """Phase schema."""

    priority: int
    description: Optional[str] = None
    tasks: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class DevPlanSchema(BaseModel):
    """Complete development plan schema."""

    project: ProjectConfig
    target_state: TargetState
    resources: Resources
    phases: Dict[str, Phase]


class SchemaValidator(BaseValidator):
    """Validates plan data against Pydantic schema."""

    @property
    def name(self) -> str:
        return "Schema validation"

    async def validate(self, plan_data: Dict[str, Any], plan_file_path: str) -> ValidationResult:
        result = ValidationResult()

        try:
            # Attempt to parse with Pydantic
            DevPlanSchema(**plan_data)

        except ValidationError as e:
            # Convert Pydantic validation errors to our format
            for error in e.errors():
                location = ".".join(str(loc) for loc in error["loc"])
                message = error["msg"]

                # Provide helpful suggestions based on error type
                suggestion = self._get_suggestion_for_error(error)

                result.add_error(
                    f"Schema validation failed: {message}",
                    f"{location} in {plan_file_path}",
                    suggestion,
                )

        # Additional schema-level validations
        if "phases" in plan_data and isinstance(plan_data["phases"], dict):
            self._validate_phase_priorities(plan_data["phases"], plan_file_path, result)

        return result

    def _get_suggestion_for_error(self, error: Any) -> str:
        """Generate helpful suggestions based on Pydantic error type."""
        error_type = error.get("type", "")
        field = error.get("loc", [])[-1] if error.get("loc") else ""

        suggestions = {
            "missing": f"Add the required '{field}' field",
            "type_error.str": f"'{field}' should be a string (text value)",
            "type_error.int": f"'{field}' should be an integer (number)",
            "type_error.list": f"'{field}' should be a list (array of items)",
            "type_error.dict": f"'{field}' should be a dictionary (key-value pairs)",
        }

        return suggestions.get(error_type, "Check the field type and format")

    def _validate_phase_priorities(self, phases: Dict[str, Any], plan_file_path: str, result: ValidationResult):
        """Validate phase priorities are logical."""
        priorities = []

        for phase_name, phase_data in phases.items():
            if isinstance(phase_data, dict) and "priority" in phase_data:
                priority = phase_data["priority"]
                if isinstance(priority, int):
                    priorities.append((phase_name, priority))

        # Check for duplicate priorities
        priority_values = [p[1] for p in priorities]
        if len(priority_values) != len(set(priority_values)):
            duplicates = [p for p in set(priority_values) if priority_values.count(p) > 1]
            result.add_error(
                f"Duplicate phase priorities found: {duplicates}",
                f"phases section in {plan_file_path}",
                "Each phase should have a unique priority number (1, 2, 3, ...)",
            )

        # Check for gaps in priorities (optional warning)
        if priorities:
            sorted_priorities = sorted(priority_values)
            expected = list(range(1, len(sorted_priorities) + 1))
            if sorted_priorities != expected:
                result.add_warning(
                    f"Phase priorities have gaps: {sorted_priorities}",
                    f"phases section in {plan_file_path}",
                    f"Consider using consecutive priorities: {expected}",
                )
