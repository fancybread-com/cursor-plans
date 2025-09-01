"""Enhanced template processor that handles command-based templates."""

import pathlib
from typing import Any, Dict, List

from ..templates.languages.csharp.generators import CSharpProjectGenerator


class TemplateProcessor:
    """Processes different types of templates including command-based ones."""

    def __init__(self):
        self.csharp_generator = CSharpProjectGenerator()

    def process_template(
        self, template_type: str, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a template based on its type."""

        if template_type == "command_template":
            return self._process_command_template(template_name, output_path, parameters)
        elif template_type == "file_template":
            return self._process_file_template(template_name, output_path, parameters)
        elif template_type == "csharp_project":
            return self._process_csharp_project(template_name, output_path, parameters)
        elif template_type == "csharp_console":
            return self._process_csharp_console(template_name, output_path, parameters)
        else:
            return self._process_default_template(template_name, output_path, parameters)

    def _process_command_template(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a command-based template."""
        # For now, we'll handle this through the C# generator
        # In the future, this could be expanded to handle other command types
        return {
            "success": False,
            "type": "command_execution",
            "error": "Command templates not yet implemented for this type",
            "output": "",
        }

    def _process_csharp_project(
        self, project_type: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a C# project template."""
        project_name = parameters.get("project_name", pathlib.Path(output_path).name)

        result = self.csharp_generator.generate_project(project_type, project_name, output_path, **parameters)

        return {
            "success": result["success"],
            "type": "csharp_project_generation",
            "project_type": project_type,
            "project_name": project_name,
            "output_path": output_path,
            "details": result,
        }

    def _process_csharp_console(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a C# console template specifically."""
        project_name = parameters.get("project_name", pathlib.Path(output_path).name)

        result = self.csharp_generator.generate_project("console", project_name, output_path, **parameters)

        return {
            "success": result["success"],
            "type": "csharp_console_generation",
            "project_name": project_name,
            "output_path": output_path,
            "details": result,
        }

    def _process_file_template(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a traditional file template."""
        # Existing file template logic
        return {"success": True, "type": "file_template", "output_path": output_path}

    def _process_default_template(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a default template (fallback)."""
        return {"success": True, "type": "default_template", "output_path": output_path}

    def get_supported_template_types(self) -> List[str]:
        """Get list of supported template types."""
        return ["command_template", "file_template", "csharp_project", "csharp_console"]

    def get_csharp_project_types(self) -> List[str]:
        """Get available C# project types."""
        from ..templates.languages.csharp.commands import CSharpCommands

        commands = CSharpCommands()
        return list(commands.get_project_commands().keys())

    def validate_csharp_parameters(self, project_type: str, parameters: Dict[str, Any]) -> List[str]:
        """Validate parameters for C# project generation."""
        if project_type == "console":
            from ..templates.languages.csharp.commands import CSharpCommands

            commands = CSharpCommands()
            return commands.validate_console_params(
                parameters.get("project_name", ""), parameters.get("output_path", "")
            )
        return []
