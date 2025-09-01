"""
Constraint validation for development plans.

Validates custom constraints and business rules.
"""

from typing import Any, Dict, List

from ..results import ValidationResult
from .base import BaseValidator


class ConstraintValidator(BaseValidator):
    """Validates custom constraints and business rules."""

    @property
    def name(self) -> str:
        return "Constraint validation"

    async def validate(self, plan_data: Dict[str, Any], plan_file_path: str) -> ValidationResult:
        result = ValidationResult()

        # Load custom constraints (could be from a constraints.yaml file or embedded in plan)
        constraints = self._load_constraints(plan_data)

        # Apply each constraint
        for constraint in constraints:
            await self._apply_constraint(constraint, plan_data, plan_file_path, result)

        # Built-in constraint validations
        self._validate_builtin_constraints(plan_data, plan_file_path, result)

        return result

    def _load_constraints(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load constraints from plan or external configuration."""
        constraints = []

        # Check if plan has embedded constraints
        if "constraints" in plan_data:
            plan_constraints = plan_data["constraints"]
            if isinstance(plan_constraints, list):
                constraints.extend(plan_constraints)
            elif isinstance(plan_constraints, dict):
                constraints.append(plan_constraints)

        # Add default constraints
        constraints.extend(self._get_default_constraints())

        return constraints

    def _get_default_constraints(self) -> List[Dict[str, Any]]:
        """Get default constraints that apply to all plans."""
        return [
            {
                "name": "no_empty_phases",
                "type": "phase_validation",
                "description": "Phases must have at least one task",
                "severity": "warning",
            },
            {
                "name": "unique_file_paths",
                "type": "resource_validation",
                "description": "File paths must be unique across resources",
                "severity": "error",
            },
            {
                "name": "valid_priorities",
                "type": "phase_validation",
                "description": "Phase priorities must be positive integers",
                "severity": "error",
            },
        ]

    async def _apply_constraint(
        self,
        constraint: Dict[str, Any],
        plan_data: Dict[str, Any],
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Apply a specific constraint to the plan."""
        constraint.get("name", "unknown")
        constraint_type = constraint.get("type", "generic")
        severity = constraint.get("severity", "warning")

        # Route to specific constraint handlers
        if constraint_type == "phase_validation":
            self._validate_phase_constraint(constraint, plan_data, plan_file_path, result, severity)
        elif constraint_type == "resource_validation":
            self._validate_resource_constraint(constraint, plan_data, plan_file_path, result, severity)
        elif constraint_type == "architecture_validation":
            self._validate_architecture_constraint(constraint, plan_data, plan_file_path, result, severity)
        elif constraint_type == "dependency_validation":
            self._validate_dependency_constraint(constraint, plan_data, plan_file_path, result, severity)

    def _validate_phase_constraint(
        self,
        constraint: Dict[str, Any],
        plan_data: Dict[str, Any],
        plan_file_path: str,
        result: ValidationResult,
        severity: str,
    ):
        """Validate phase-related constraints."""
        constraint_name = constraint.get("name")

        if constraint_name == "no_empty_phases":
            if "phases" in plan_data and isinstance(plan_data["phases"], dict):
                for phase_name, phase_data in plan_data["phases"].items():
                    if isinstance(phase_data, dict):
                        tasks = phase_data.get("tasks", [])
                        if not tasks or (isinstance(tasks, list) and len(tasks) == 0):
                            if severity == "error":
                                result.add_error(
                                    f"Phase '{phase_name}' has no tasks defined",
                                    f"phases.{phase_name} in {plan_file_path}",
                                    "Add at least one task to this phase or remove it",
                                )
                            else:
                                result.add_warning(
                                    f"Phase '{phase_name}' has no tasks defined",
                                    f"phases.{phase_name} in {plan_file_path}",
                                    "Consider adding tasks or removing empty phases",
                                )

        elif constraint_name == "valid_priorities":
            if "phases" in plan_data and isinstance(plan_data["phases"], dict):
                for phase_name, phase_data in plan_data["phases"].items():
                    if isinstance(phase_data, dict) and "priority" in phase_data:
                        priority = phase_data["priority"]
                        if not isinstance(priority, int) or priority <= 0:
                            result.add_error(
                                f"Phase '{phase_name}' has invalid priority: {priority}",
                                f"phases.{phase_name}.priority in {plan_file_path}",
                                "Priority must be a positive integer (1, 2, 3, ...)",
                            )

    def _validate_resource_constraint(
        self,
        constraint: Dict[str, Any],
        plan_data: Dict[str, Any],
        plan_file_path: str,
        result: ValidationResult,
        severity: str,
    ):
        """Validate resource-related constraints."""
        constraint_name = constraint.get("name")

        if constraint_name == "unique_file_paths":
            if "resources" in plan_data and isinstance(plan_data["resources"], dict):
                if "files" in plan_data["resources"] and isinstance(plan_data["resources"]["files"], list):
                    file_paths = {}
                    for i, file_resource in enumerate(plan_data["resources"]["files"]):
                        if isinstance(file_resource, dict) and "path" in file_resource:
                            path = file_resource["path"]
                            if path in file_paths:
                                result.add_error(
                                    f"Duplicate file path '{path}' found",
                                    f"resources.files[{i}] and resources.files[{file_paths[path]}] in {plan_file_path}",
                                    "Each file path must be unique",
                                )
                            else:
                                file_paths[path] = i

    def _validate_architecture_constraint(
        self,
        constraint: Dict[str, Any],
        plan_data: Dict[str, Any],
        plan_file_path: str,
        result: ValidationResult,
        severity: str,
    ):
        """Validate architecture-related constraints."""
        # Custom architecture constraints would be implemented here
        pass

    def _validate_dependency_constraint(
        self,
        constraint: Dict[str, Any],
        plan_data: Dict[str, Any],
        plan_file_path: str,
        result: ValidationResult,
        severity: str,
    ):
        """Validate dependency-related constraints."""
        # Custom dependency constraints would be implemented here
        pass

    def _validate_builtin_constraints(self, plan_data: Dict[str, Any], plan_file_path: str, result: ValidationResult):
        """Apply built-in constraint validations."""

        # Validate reasonable resource counts
        if "resources" in plan_data and isinstance(plan_data["resources"], dict):
            if "files" in plan_data["resources"] and isinstance(plan_data["resources"]["files"], list):
                file_count = len(plan_data["resources"]["files"])

                if file_count > 50:
                    result.add_warning(
                        f"Plan defines {file_count} files, which may be overly complex",
                        f"resources.files in {plan_file_path}",
                        "Consider breaking large plans into smaller, focused plans",
                    )
                elif file_count == 0:
                    result.add_warning(
                        "Plan defines no files to create",
                        f"resources.files in {plan_file_path}",
                        "Add file resources or this plan may not produce any output",
                    )

        # Validate reasonable phase counts
        if "phases" in plan_data and isinstance(plan_data["phases"], dict):
            phase_count = len(plan_data["phases"])

            if phase_count > 10:
                result.add_suggestion(
                    f"Plan has {phase_count} phases, consider consolidation",
                    f"phases in {plan_file_path}",
                    "Large numbers of phases can be difficult to manage",
                )
            elif phase_count == 0:
                result.add_error(
                    "Plan has no execution phases defined",
                    f"phases in {plan_file_path}",
                    "Add at least one phase to define how the plan should be executed",
                )

        # Validate project naming
        if "project" in plan_data and isinstance(plan_data["project"], dict):
            if "name" in plan_data["project"]:
                name = plan_data["project"]["name"]
                if isinstance(name, str):
                    if len(name) < 2:
                        result.add_warning(
                            f"Project name '{name}' is very short",
                            f"project.name in {plan_file_path}",
                            "Consider using a more descriptive project name",
                        )
                    elif len(name) > 50:
                        result.add_warning(
                            f"Project name is very long ({len(name)} characters)",
                            f"project.name in {plan_file_path}",
                            "Consider using a shorter, more concise project name",
                        )

                    # Check for special characters that might cause issues
                    if not name.replace("-", "").replace("_", "").replace(" ", "").isalnum():
                        result.add_suggestion(
                            f"Project name '{name}' contains special characters",
                            f"project.name in {plan_file_path}",
                            "Consider using only letters, numbers, hyphens, and underscores",
                        )
