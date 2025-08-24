"""
Context validation for development plans.
"""

import os
from typing import Dict, Any
from .base import BaseValidator
from ..results import ValidationResult


class ContextValidator(BaseValidator):
    """Validates context files and referenced paths."""

    @property
    def name(self) -> str:
        return "Context validation"

    async def validate(self, plan_data: Dict[str, Any], plan_file_path: str) -> ValidationResult:
        result = ValidationResult()

        # Get the directory containing the plan file
        plan_dir = os.path.dirname(os.path.abspath(plan_file_path))

        # Check for context files
        self._validate_context_files(plan_dir, result)

        # Validate paths in context files
        await self._validate_context_paths(plan_dir, result)

        # Check if plan references context appropriately
        self._validate_plan_context_usage(plan_data, plan_dir, plan_file_path, result)

        return result

    def _validate_context_files(self, plan_dir: str, result: ValidationResult):
        """Check for existence and accessibility of context files."""
        # Check for default context file
        default_context = os.path.join(plan_dir, "context.txt")
        if os.path.exists(default_context):
            try:
                with open(default_context, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        result.add_warning(
                            "Default context file is empty",
                            "context.txt",
                            "Add relevant files and folders to provide context for development planning"
                        )
            except Exception as e:
                result.add_error(
                    f"Cannot read context file: {str(e)}",
                    "context.txt",
                    "Ensure the context file has proper read permissions"
                )

        # Check for story-specific context files
        context_files = []
        try:
            for file in os.listdir(plan_dir):
                if file.startswith("context-") and file.endswith(".txt"):
                    context_files.append(file)
        except Exception:
            pass  # Directory read issues will be caught elsewhere

        if context_files:
            result.add_suggestion(
                f"Found {len(context_files)} story-specific context files",
                f"Context files: {', '.join(context_files)}",
                "Consider using story-specific context when creating plans"
            )

    async def _validate_context_paths(self, plan_dir: str, result: ValidationResult):
        """Validate that paths in context files actually exist."""
        context_files_to_check = []

        # Check default context
        default_context = os.path.join(plan_dir, "context.txt")
        if os.path.exists(default_context):
            context_files_to_check.append(("context.txt", default_context))

        # Check story-specific context files
        try:
            for file in os.listdir(plan_dir):
                if file.startswith("context-") and file.endswith(".txt"):
                    full_path = os.path.join(plan_dir, file)
                    context_files_to_check.append((file, full_path))
        except Exception:
            pass

        # Validate paths in each context file
        for context_name, context_path in context_files_to_check:
            try:
                with open(context_path, 'r') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Check if path exists (relative to plan directory)
                    full_path = os.path.join(plan_dir, line)
                    if not os.path.exists(full_path):
                        # Also try absolute path
                        if not os.path.isabs(line) or not os.path.exists(line):
                            result.add_warning(
                                f"Context path does not exist: {line}",
                                f"{context_name}:line {line_num}",
                                "Remove invalid paths or ensure they exist before planning"
                            )

            except Exception as e:
                result.add_error(
                    f"Cannot validate context file: {str(e)}",
                    context_name,
                    "Ensure the context file is readable and properly formatted"
                )

    def _validate_plan_context_usage(self, plan_data: Dict[str, Any], plan_dir: str, plan_file_path: str, result: ValidationResult):
        """Check if the plan makes good use of available context."""
        # Check if context files exist but plan doesn't seem to reference them
        has_context_files = (
            os.path.exists(os.path.join(plan_dir, "context.txt")) or
            any(f.startswith("context-") and f.endswith(".txt")
                for f in os.listdir(plan_dir) if os.path.isfile(os.path.join(plan_dir, f)))
        )

        if has_context_files:
            # Check if plan resources reference context-related paths
            context_aware = False

            if "resources" in plan_data and isinstance(plan_data["resources"], dict):
                if "files" in plan_data["resources"]:
                    files = plan_data["resources"]["files"]
                    if isinstance(files, list):
                        for file_resource in files:
                            if isinstance(file_resource, dict) and "path" in file_resource:
                                path = file_resource["path"]
                                # Check if path references existing project structure
                                full_path = os.path.join(plan_dir, path)
                                parent_dir = os.path.dirname(full_path)
                                if os.path.exists(parent_dir):
                                    context_aware = True
                                    break

            if not context_aware:
                result.add_suggestion(
                    "Context files available but plan may not be using them effectively",
                    f"Plan resources in {plan_file_path}",
                    "Consider reviewing context files and ensuring plan resources align with existing project structure"
                )
        else:
            # No context files - suggest creating them for better planning
            if "resources" in plan_data and isinstance(plan_data["resources"], dict):
                if "files" in plan_data["resources"]:
                    files = plan_data["resources"]["files"]
                    if isinstance(files, list) and len(files) > 3:  # Non-trivial plan
                        result.add_suggestion(
                            "Consider creating context files for better development planning",
                            plan_file_path,
                            "Create context.txt with relevant existing files to improve plan accuracy"
                        )
