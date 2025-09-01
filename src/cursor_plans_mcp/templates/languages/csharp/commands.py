"""C# command templates for project generation."""
import pathlib
from typing import Any, Dict, List

import yaml


class CSharpCommands:
    """C# project generation commands."""

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        """Load C# configuration from config.yaml."""
        config_path = pathlib.Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    @staticmethod
    def get_supported_frameworks() -> List[str]:
        """Get supported framework versions from config."""
        config = CSharpCommands._load_config()
        return config.get("frameworks", {}).get("supported", ["net8.0", "net9.0"])

    @staticmethod
    def get_default_framework() -> str:
        """Get default framework version from config."""
        config = CSharpCommands._load_config()
        return config.get("frameworks", {}).get("default", "net8.0")

    @staticmethod
    def get_project_commands() -> Dict[str, Dict[str, Any]]:
        """Get all available C# project generation commands."""
        return {
            "console": {
                "command": "dotnet",
                "args": ["new", "console", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# console application",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework", "lang_version"],
                "post_generation": ["customize_namespace", "add_basic_structure"]
            },
            "classlib": {
                "command": "dotnet",
                "args": ["new", "classlib", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# class library",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework", "lang_version"],
                "post_generation": ["customize_namespace", "add_basic_class"]
            },
            "webapi": {
                "command": "dotnet",
                "args": ["new", "webapi", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# Web API project",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework", "auth", "https"],
                "post_generation": ["customize_namespace", "add_swagger", "add_basic_controller"]
            },
            "mvc": {
                "command": "dotnet",
                "args": ["new", "mvc", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# MVC project",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework", "auth", "https"],
                "post_generation": ["customize_namespace", "add_basic_views"]
            },
            "blazor": {
                "command": "dotnet",
                "args": ["new", "blazorserver", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# Blazor Server project",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework", "auth", "https"],
                "post_generation": ["customize_namespace", "add_basic_pages"]
            },
            "xunit": {
                "command": "dotnet",
                "args": ["new", "xunit", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# xUnit test project",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework"],
                "post_generation": ["customize_namespace", "add_basic_test"]
            },
            "mstest": {
                "command": "dotnet",
                "args": ["new", "mstest", "-n", "{project_name}", "-o", "{output_path}"],
                "description": "Create a new C# MSTest project",
                "required_params": ["project_name", "output_path"],
                "optional_params": ["framework"],
                "post_generation": ["customize_namespace", "add_basic_test"]
            }
        }

    @staticmethod
    def get_solution_commands() -> Dict[str, Dict[str, Any]]:
        """Get solution-related commands."""
        return {
            "create_solution": {
                "command": "dotnet",
                "args": ["new", "sln", "-n", "{solution_name}"],
                "description": "Create a new solution file",
                "required_params": ["solution_name"]
            },
            "add_project_to_solution": {
                "command": "dotnet",
                "args": ["sln", "{solution_path}", "add", "{project_path}"],
                "description": "Add project to solution",
                "required_params": ["solution_path", "project_path"]
            }
        }

    @staticmethod
    def get_console_specific_commands() -> Dict[str, Dict[str, Any]]:
        """Get console-specific commands and customizations."""
        return {
            "add_package": {
                "command": "dotnet",
                "args": ["add", "package", "{package_name}"],
                "description": "Add a NuGet package to the console project",
                "required_params": ["package_name"],
                "optional_params": ["version"]
            },
            "add_reference": {
                "command": "dotnet",
                "args": ["add", "reference", "{project_path}"],
                "description": "Add a project reference to the console project",
                "required_params": ["project_path"]
            },
            "build": {
                "command": "dotnet",
                "args": ["build"],
                "description": "Build the console project",
                "required_params": []
            },
            "run": {
                "command": "dotnet",
                "args": ["run"],
                "description": "Run the console project",
                "required_params": []
            }
        }

    @staticmethod
    def validate_console_params(project_name: str, output_path: str, **kwargs) -> List[str]:
        """Validate parameters for console project creation."""
        errors = []

        if not project_name or not project_name.strip():
            errors.append("Project name is required and cannot be empty")

        if not output_path or not output_path.strip():
            errors.append("Output path is required and cannot be empty")

        # Validate project name format (C# naming conventions)
        if project_name and not project_name[0].isupper():
            errors.append("Project name should start with an uppercase letter (PascalCase)")

        # Check for invalid characters in project name
        invalid_chars = [' ', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in project_name for char in invalid_chars):
            errors.append("Project name contains invalid characters")

        # Validate framework version if provided (now dynamic from config)
        framework = kwargs.get("framework")
        if framework:
            supported_frameworks = CSharpCommands.get_supported_frameworks()
            if framework not in supported_frameworks:
                errors.append(f"Framework must be one of: {', '.join(supported_frameworks)}")

        return errors
