"""
Cursor Rules validation for development plans.

Validates plans against .cursorrules files and team coding standards.
"""

import os
import re
from typing import Any, Dict, Optional

from ..results import ValidationResult
from .base import BaseValidator


class CursorRulesValidator(BaseValidator):
    """Validates development plans against Cursor rules and coding standards."""

    @property
    def name(self) -> str:
        return "Cursor Rules validation"

    async def validate(
        self, plan_data: Dict[str, Any], plan_file_path: str
    ) -> ValidationResult:
        result = ValidationResult()

        # Get the directory containing the plan file
        plan_dir = os.path.dirname(os.path.abspath(plan_file_path))

        # Load Cursor rules
        cursor_rules = await self._load_cursor_rules(plan_dir)

        if not cursor_rules:
            result.add_suggestion(
                "No .cursorrules file found",
                plan_dir,
                "Consider creating a .cursorrules file to define coding standards and architectural patterns",
            )
            return result

        # Validate against different rule categories
        self._validate_architectural_patterns(
            plan_data, cursor_rules, plan_file_path, result
        )
        self._validate_naming_conventions(
            plan_data, cursor_rules, plan_file_path, result
        )
        self._validate_security_requirements(
            plan_data, cursor_rules, plan_file_path, result
        )
        self._validate_framework_patterns(
            plan_data, cursor_rules, plan_file_path, result
        )
        self._validate_testing_requirements(
            plan_data, cursor_rules, plan_file_path, result
        )

        return result

    async def _load_cursor_rules(self, plan_dir: str) -> Optional[str]:
        """Load and parse .cursorrules file."""
        cursor_rules_path = os.path.join(plan_dir, ".cursorrules")

        if not os.path.exists(cursor_rules_path):
            # Check parent directories (up to 3 levels)
            current_dir = plan_dir
            for _ in range(3):
                parent_dir = os.path.dirname(current_dir)
                if parent_dir == current_dir:  # Reached root
                    break

                cursor_rules_path = os.path.join(parent_dir, ".cursorrules")
                if os.path.exists(cursor_rules_path):
                    break
                current_dir = parent_dir
            else:
                return None

        try:
            with open(cursor_rules_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def _validate_architectural_patterns(
        self,
        plan_data: Dict[str, Any],
        cursor_rules: str,
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Validate architectural patterns against Cursor rules."""
        rules_lower = cursor_rules.lower()

        # Check for repository pattern requirement
        if "repository pattern" in rules_lower or "use repositories" in rules_lower:
            if self._plan_has_direct_db_access(plan_data):
                result.add_warning(
                    "Direct database access detected, but repository pattern is required",
                    f"resources section in {plan_file_path}",
                    "Consider adding repository classes to abstract database operations",
                )

        # Check for dependency injection requirements
        if "dependency injection" in rules_lower or "use di" in rules_lower:
            if not self._plan_has_dependency_injection(plan_data):
                result.add_suggestion(
                    "Plan may benefit from dependency injection patterns",
                    f"architecture in {plan_file_path}",
                    "Consider adding DI container setup in your foundation phase",
                )

        # Check for layered architecture
        if "layered architecture" in rules_lower or "clean architecture" in rules_lower:
            if not self._plan_has_layered_structure(plan_data):
                result.add_suggestion(
                    "Consider implementing layered architecture",
                    f"resources.files in {plan_file_path}",
                    "Organize files into layers: controllers, services, repositories, models",
                )

    def _validate_naming_conventions(
        self,
        plan_data: Dict[str, Any],
        cursor_rules: str,
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Validate naming conventions against Cursor rules."""
        # Extract naming patterns from rules
        naming_patterns = self._extract_naming_patterns(cursor_rules)

        if "resources" in plan_data and isinstance(plan_data["resources"], dict):
            if "files" in plan_data["resources"]:
                files = plan_data["resources"]["files"]
                if isinstance(files, list):
                    for i, file_resource in enumerate(files):
                        if isinstance(file_resource, dict) and "path" in file_resource:
                            path = file_resource["path"]
                            file_name = os.path.basename(path)

                            # Check against naming patterns
                            for pattern_name, pattern_regex in naming_patterns.items():
                                if not re.match(pattern_regex, file_name):
                                    file_type = file_resource.get("type", "file")
                                    if pattern_name.lower() in file_type.lower():
                                        result.add_warning(
                                            f"File name '{file_name}' may not follow {pattern_name} naming convention",
                                            f"resources.files[{i}].path in {plan_file_path}",
                                            f"Consider using naming pattern: {pattern_regex}",
                                        )

    def _validate_security_requirements(
        self,
        plan_data: Dict[str, Any],
        cursor_rules: str,
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Validate security requirements from Cursor rules."""
        rules_lower = cursor_rules.lower()

        # Check for authentication requirements
        if "authentication" in rules_lower or "auth required" in rules_lower:
            if not self._plan_has_authentication(plan_data):
                result.add_error(
                    "Authentication is required but not found in plan",
                    f"target_state or phases in {plan_file_path}",
                    "Add authentication implementation to your security phase",
                )

        # Check for authorization requirements
        if (
            "authorization" in rules_lower
            or "rbac" in rules_lower
            or "role-based" in rules_lower
        ):
            if not self._plan_has_authorization(plan_data):
                result.add_warning(
                    "Authorization/RBAC may be required",
                    f"security phase in {plan_file_path}",
                    "Consider adding role-based access control to your plan",
                )

        # Check for HTTPS/TLS requirements
        if "https" in rules_lower or "tls" in rules_lower or "ssl" in rules_lower:
            if not self._plan_has_tls(plan_data):
                result.add_warning(
                    "HTTPS/TLS configuration may be required",
                    f"target_state in {plan_file_path}",
                    "Consider adding TLS/HTTPS configuration to your plan",
                )

    def _validate_framework_patterns(
        self,
        plan_data: Dict[str, Any],
        cursor_rules: str,
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Validate framework-specific patterns."""
        # Get target framework
        framework = self._get_target_framework(plan_data)
        if not framework:
            return

        rules_lower = cursor_rules.lower()
        framework_lower = framework.lower()

        # FastAPI specific rules
        if "fastapi" in framework_lower:
            if "pydantic models" in rules_lower and not self._plan_has_pydantic_models(
                plan_data
            ):
                result.add_warning(
                    "Pydantic models are recommended for FastAPI but not found in plan",
                    f"resources in {plan_file_path}",
                    "Add Pydantic model files for request/response validation",
                )

            if "openapi" in rules_lower or "swagger" in rules_lower:
                if not self._plan_has_api_documentation(plan_data):
                    result.add_suggestion(
                        "API documentation (OpenAPI/Swagger) is recommended",
                        f"phases in {plan_file_path}",
                        "Consider adding API documentation generation to your plan",
                    )

        # React/Vue specific rules
        if any(fw in framework_lower for fw in ["react", "vue"]):
            if "typescript" in rules_lower and not self._plan_has_typescript(plan_data):
                result.add_warning(
                    "TypeScript is required but plan may be using JavaScript",
                    f"target_state.architecture in {plan_file_path}",
                    "Consider using TypeScript for better type safety",
                )

    def _validate_testing_requirements(
        self,
        plan_data: Dict[str, Any],
        cursor_rules: str,
        plan_file_path: str,
        result: ValidationResult,
    ):
        """Validate testing requirements from Cursor rules."""
        rules_lower = cursor_rules.lower()

        # Check for testing requirements
        if "unit tests" in rules_lower or "testing required" in rules_lower:
            if not self._plan_has_testing_phase(plan_data):
                result.add_error(
                    "Unit testing is required but no testing phase found",
                    f"phases in {plan_file_path}",
                    "Add a testing phase with unit test implementation",
                )

        # Check for coverage requirements
        if "test coverage" in rules_lower or "coverage" in rules_lower:
            if self._plan_has_testing_phase(
                plan_data
            ) and not self._plan_has_coverage_config(plan_data):
                result.add_suggestion(
                    "Test coverage tracking is recommended",
                    f"testing phase in {plan_file_path}",
                    "Consider adding test coverage configuration and reporting",
                )

    # Helper methods for pattern detection
    def _plan_has_direct_db_access(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan has direct database access patterns."""
        # Look for controller/handler files that might access DB directly
        if "resources" in plan_data and "files" in plan_data["resources"]:
            files = plan_data["resources"]["files"]
            if isinstance(files, list):
                for file_resource in files:
                    if isinstance(file_resource, dict):
                        file_type = file_resource.get("type", "").lower()
                        if "controller" in file_type or "handler" in file_type:
                            return True
        return False

    def _plan_has_dependency_injection(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes dependency injection setup."""
        # Look for DI-related files or phases
        if "phases" in plan_data:
            phases = plan_data["phases"]
            if isinstance(phases, dict):
                for phase_data in phases.values():
                    if isinstance(phase_data, dict) and "tasks" in phase_data:
                        tasks = phase_data["tasks"]
                        if isinstance(tasks, list):
                            for task in tasks:
                                if isinstance(task, str) and (
                                    "di" in task.lower() or "injection" in task.lower()
                                ):
                                    return True
        return False

    def _plan_has_layered_structure(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan follows layered architecture."""
        if "resources" in plan_data and "files" in plan_data["resources"]:
            files = plan_data["resources"]["files"]
            if isinstance(files, list):
                layers = set()
                for file_resource in files:
                    if isinstance(file_resource, dict) and "path" in file_resource:
                        path = file_resource["path"].lower()
                        if any(
                            layer in path
                            for layer in [
                                "controller",
                                "service",
                                "repository",
                                "model",
                            ]
                        ):
                            layers.add(True)
                return len(layers) > 0
        return False

    def _plan_has_authentication(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes authentication."""
        # Check target state
        if "target_state" in plan_data and "architecture" in plan_data["target_state"]:
            arch = plan_data["target_state"]["architecture"]
            if isinstance(arch, list):
                for item in arch:
                    if isinstance(item, dict):
                        for value in item.values():
                            if isinstance(value, str) and "auth" in value.lower():
                                return True

        # Check phases
        if "phases" in plan_data:
            phases = plan_data["phases"]
            if isinstance(phases, dict):
                for phase_name in phases.keys():
                    if "auth" in phase_name.lower() or "security" in phase_name.lower():
                        return True

        return False

    def _plan_has_authorization(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes authorization/RBAC."""
        # Similar to authentication but looking for authorization patterns
        text_content = str(plan_data).lower()
        return any(
            term in text_content
            for term in ["authorization", "rbac", "role", "permission"]
        )

    def _plan_has_tls(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes TLS/HTTPS configuration."""
        text_content = str(plan_data).lower()
        return any(
            term in text_content for term in ["https", "tls", "ssl", "certificate"]
        )

    def _plan_has_testing_phase(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan has a testing phase."""
        if "phases" in plan_data:
            phases = plan_data["phases"]
            if isinstance(phases, dict):
                for phase_name in phases.keys():
                    if "test" in phase_name.lower():
                        return True
        return False

    def _plan_has_pydantic_models(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes Pydantic models."""
        if "resources" in plan_data and "files" in plan_data["resources"]:
            files = plan_data["resources"]["files"]
            if isinstance(files, list):
                for file_resource in files:
                    if isinstance(file_resource, dict):
                        file_type = file_resource.get("type", "").lower()
                        template = file_resource.get("template", "").lower()
                        if "model" in file_type or "pydantic" in template:
                            return True
        return False

    def _plan_has_api_documentation(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes API documentation."""
        text_content = str(plan_data).lower()
        return any(
            term in text_content
            for term in ["openapi", "swagger", "documentation", "docs"]
        )

    def _plan_has_typescript(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan uses TypeScript."""
        if "target_state" in plan_data and "architecture" in plan_data["target_state"]:
            arch = plan_data["target_state"]["architecture"]
            if isinstance(arch, list):
                for item in arch:
                    if isinstance(item, dict):
                        for value in item.values():
                            if isinstance(value, str) and "typescript" in value.lower():
                                return True
        return False

    def _plan_has_coverage_config(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan includes test coverage configuration."""
        text_content = str(plan_data).lower()
        return "coverage" in text_content

    def _get_target_framework(self, plan_data: Dict[str, Any]) -> Optional[str]:
        """Extract target framework from plan."""
        if "target_state" in plan_data and "architecture" in plan_data["target_state"]:
            arch = plan_data["target_state"]["architecture"]
            if isinstance(arch, list):
                for item in arch:
                    if isinstance(item, dict) and "framework" in item:
                        return item["framework"]
        return None

    def _extract_naming_patterns(self, cursor_rules: str) -> Dict[str, str]:
        """Extract naming patterns from Cursor rules text."""
        patterns = {}

        # Simple pattern extraction - this could be made more sophisticated
        lines = cursor_rules.split("\n")
        for line in lines:
            line = line.strip().lower()

            # Look for naming convention patterns
            if "controller" in line and "naming" in line:
                patterns["Controller"] = r".*[Cc]ontroller\.(py|js|ts)$"

            if "model" in line and "naming" in line:
                patterns["Model"] = r".*[Mm]odel\.(py|js|ts)$"

            if "service" in line and "naming" in line:
                patterns["Service"] = r".*[Ss]ervice\.(py|js|ts)$"

        return patterns
