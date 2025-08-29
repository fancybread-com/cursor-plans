"""
Logic validation for development plans.
"""

from typing import Any, Dict, List, Set

from ..results import ValidationResult
from .base import BaseValidator


class LogicValidator(BaseValidator):
    """Validates business logic and dependencies in development plans."""

    @property
    def name(self) -> str:
        return "Logic validation"

    async def validate(
        self, plan_data: Dict[str, Any], plan_file_path: str
    ) -> ValidationResult:
        result = ValidationResult()

        # Validate phase dependencies
        if "phases" in plan_data:
            self._validate_phase_dependencies(
                plan_data["phases"], plan_file_path, result
            )

        # Validate resource conflicts
        if "resources" in plan_data:
            self._validate_resource_conflicts(
                plan_data["resources"], plan_file_path, result
            )

        # Validate template compatibility
        self._validate_template_compatibility(plan_data, plan_file_path, result)

        return result

    def _validate_phase_dependencies(
        self, phases: Dict[str, Any], plan_file_path: str, result: ValidationResult
    ):
        """Check for circular dependencies and invalid phase references."""
        if not isinstance(phases, dict):
            return

        phase_names = set(phases.keys())

        # Build dependency graph
        dependencies = {}
        for phase_name, phase_data in phases.items():
            if isinstance(phase_data, dict) and "dependencies" in phase_data:
                deps = phase_data["dependencies"]
                if isinstance(deps, list):
                    dependencies[phase_name] = deps
                else:
                    dependencies[phase_name] = []
            else:
                dependencies[phase_name] = []

        # Check for invalid phase references
        for phase_name, deps in dependencies.items():
            for dep in deps:
                if dep not in phase_names:
                    result.add_error(
                        f"Phase '{phase_name}' depends on unknown phase '{dep}'",
                        f"phases.{phase_name}.dependencies in {plan_file_path}",
                        f"Remove '{dep}' or add it as a phase",
                    )

        # Check for circular dependencies using DFS
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dependencies.get(node, []):
                if neighbor in phase_names:  # Only check valid phases
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        visited = set()
        for phase_name in phase_names:
            if phase_name not in visited:
                if has_cycle(phase_name, visited, set()):
                    result.add_error(
                        f"Circular dependency detected involving phase '{phase_name}'",
                        f"phases section in {plan_file_path}",
                        "Review phase dependencies to remove circular references",
                    )
                    break  # Only report first cycle found

    def _validate_resource_conflicts(
        self, resources: Dict[str, Any], plan_file_path: str, result: ValidationResult
    ):
        """Check for conflicting file paths and resource definitions."""
        if not isinstance(resources, dict) or "files" not in resources:
            return

        files = resources["files"]
        if not isinstance(files, list):
            return

        # Track file paths to detect conflicts
        file_paths = {}

        for i, file_resource in enumerate(files):
            if not isinstance(file_resource, dict) or "path" not in file_resource:
                continue

            path = file_resource["path"]
            if path in file_paths:
                result.add_error(
                    f"Duplicate file path '{path}' found",
                    f"resources.files[{i}] and resources.files[{file_paths[path]}] in {plan_file_path}",
                    "Each file path should be unique across all resources",
                )
            else:
                file_paths[path] = i

            # Check for path conflicts (parent/child relationships)
            for existing_path in file_paths.keys():
                if path != existing_path:
                    if path.startswith(existing_path + "/") or existing_path.startswith(
                        path + "/"
                    ):
                        result.add_warning(
                            f"Potential path conflict: '{path}' and '{existing_path}'",
                            f"resources.files in {plan_file_path}",
                            "Ensure file and directory paths don't conflict",
                        )

    def _validate_template_compatibility(
        self, plan_data: Dict[str, Any], plan_file_path: str, result: ValidationResult
    ):
        """Validate template references and compatibility with target architecture."""
        # Get target architecture
        target_arch = {}
        if "target_state" in plan_data and isinstance(plan_data["target_state"], dict):
            if "architecture" in plan_data["target_state"]:
                arch_list = plan_data["target_state"]["architecture"]
                if isinstance(arch_list, list):
                    for item in arch_list:
                        if isinstance(item, dict):
                            target_arch.update(item)

        # Check template compatibility
        if "resources" in plan_data and isinstance(plan_data["resources"], dict):
            if "files" in plan_data["resources"]:
                files = plan_data["resources"]["files"]
                if isinstance(files, list):
                    self._check_template_references(
                        files, target_arch, plan_file_path, result
                    )

    def _check_template_references(
        self,
        files: List[Any],
        target_arch: Dict[str, str],
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Check template references against available templates."""
        # Known templates and their requirements
        template_requirements = {
            "fastapi_main": {"framework": "FastAPI", "language": "python"},
            "fastapi_model": {"framework": "FastAPI", "language": "python"},
            "fastapi_router": {"framework": "FastAPI", "language": "python"},
            "react_component": {"framework": "React", "language": "javascript"},
            "dotnet_controller": {"framework": ".NET", "language": "csharp"},
            "vue_component": {"framework": "Vue.js", "language": "javascript"},
        }

        for i, file_resource in enumerate(files):
            if not isinstance(file_resource, dict) or "template" not in file_resource:
                continue

            template = file_resource["template"]

            # Check if template exists (basic check)
            if template not in template_requirements and not template.startswith(
                "custom_"
            ):
                result.add_warning(
                    f"Unknown template '{template}' referenced",
                    f"resources.files[{i}].template in {plan_file_path}",
                    f"Verify template exists or use 'custom_{template}' for custom templates",
                )
                continue

            # Check template compatibility with target architecture
            if template in template_requirements:
                requirements = template_requirements[template]

                for req_key, req_value in requirements.items():
                    target_value = target_arch.get(req_key, "").lower()
                    if (
                        req_value.lower() not in target_value
                        and target_value not in req_value.lower()
                    ):
                        result.add_warning(
                            (
                                f"Template '{template}' may not be compatible with target {req_key}: "
                                f"{target_arch.get(req_key, 'not specified')}"
                            ),
                            f"resources.files[{i}].template in {plan_file_path}",
                            f"Consider using a template compatible with {req_key}: {target_arch.get(req_key)}",
                        )
