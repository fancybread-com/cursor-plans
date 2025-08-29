"""
Syntax validation for development plans.
"""

from typing import Any, Dict

from ..results import ValidationResult
from .base import BaseValidator


class SyntaxValidator(BaseValidator):
    """Validates YAML syntax and basic structure."""

    @property
    def name(self) -> str:
        return "Syntax validation"

    async def validate(
        self, plan_data: Dict[str, Any], plan_file_path: str
    ) -> ValidationResult:
        result = ValidationResult()

        # Check required top-level sections
        required_sections = ["project", "target_state", "resources", "phases"]

        for section in required_sections:
            if section not in plan_data:
                result.add_error(
                    f"Missing required section: {section}",
                    f"Top level of {plan_file_path}",
                    f"Add a '{section}:' section to your plan file",
                )

        # Validate project section structure
        if "project" in plan_data:
            project = plan_data["project"]
            if not isinstance(project, dict):
                result.add_error(
                    "Project section must be a dictionary",
                    f"project section in {plan_file_path}",
                    "Use 'project:' followed by indented key-value pairs",
                )
            else:
                # Check required project fields
                required_project_fields = ["name", "version"]
                for field in required_project_fields:
                    if field not in project:
                        result.add_error(
                            f"Missing required project field: {field}",
                            f"project section in {plan_file_path}",
                            f"Add '{field}: \"your-value\"' to the project section",
                        )

        # Validate phases section structure
        if "phases" in plan_data:
            phases = plan_data["phases"]
            if not isinstance(phases, dict):
                result.add_error(
                    "Phases section must be a dictionary",
                    f"phases section in {plan_file_path}",
                    "Use 'phases:' followed by phase names as keys",
                )
            else:
                # Check each phase has required structure
                for phase_name, phase_data in phases.items():
                    if not isinstance(phase_data, dict):
                        result.add_error(
                            f"Phase '{phase_name}' must be a dictionary",
                            f"phases.{phase_name} in {plan_file_path}",
                            f"Use '{phase_name}:' followed by indented phase configuration",
                        )
                    elif "priority" not in phase_data:
                        result.add_warning(
                            f"Phase '{phase_name}' missing priority",
                            f"phases.{phase_name} in {plan_file_path}",
                            "Add 'priority: N' to define execution order",
                        )

        # Validate resources section structure
        if "resources" in plan_data:
            resources = plan_data["resources"]
            if not isinstance(resources, dict):
                result.add_error(
                    "Resources section must be a dictionary",
                    f"resources section in {plan_file_path}",
                    "Use 'resources:' followed by resource categories",
                )
            elif "files" in resources:
                files = resources["files"]
                if not isinstance(files, list):
                    result.add_error(
                        "Resources.files must be a list",
                        f"resources.files in {plan_file_path}",
                        "Use 'files:' followed by a list of file definitions",
                    )
                else:
                    # Check each file resource
                    for i, file_resource in enumerate(files):
                        if not isinstance(file_resource, dict):
                            result.add_error(
                                f"File resource {i} must be a dictionary",
                                f"resources.files[{i}] in {plan_file_path}",
                                "Each file resource needs path, type, and other properties",
                            )
                        elif "path" not in file_resource:
                            result.add_error(
                                f"File resource {i} missing required 'path' field",
                                f"resources.files[{i}] in {plan_file_path}",
                                "Add 'path: \"file/path\"' to specify the file location",
                            )

        return result
