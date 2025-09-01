"""Template engine for command-based project generation."""

import pathlib
from typing import Any, Dict, List

from jinja2 import Environment, Template


class TemplateEngine:
    """Engine for processing command templates."""

    def __init__(self):
        self.environment = Environment(autoescape=False)
        self.templates = {}

    def register_template(self, name: str, template_content: str):
        """Register a template by name."""
        self.templates[name] = Template(template_content)

    def render_template(self, template_name: str, parameters: Dict[str, Any]) -> str:
        """Render a template with parameters."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = self.templates[template_name]
        return template.render(**parameters)

    def validate_parameters(self, template_name: str, parameters: Dict[str, Any]) -> List[str]:
        """Validate parameters against template requirements."""
        if template_name not in self.templates:
            return [f"Template '{template_name}' not found"]

        # For now, return empty list - parameter validation can be enhanced later
        return []

    def _extract_required_parameters(self, template: Template) -> List[str]:
        """Extract required parameters from template."""
        # This is a simplified approach - in practice you'd want more robust parsing
        # Get the template source by rendering with empty context and capturing the original
        try:
            # Try to get the source from the template's internal structure
            content = str(template)
            # Look for {{ param }} patterns
            import re

            params = re.findall(r"\{\{\s*(\w+)\s*\}\}", content)
            return list(set(params))
        except Exception:
            # Fallback: return empty list if we can't extract parameters
            return []

    def process_template_type(
        self, template_type: str, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a template based on its type."""

        if template_type == "csharp_console":
            return self._process_csharp_console(template_name, output_path, parameters)
        elif template_type == "csharp_project":
            return self._process_csharp_project(template_name, output_path, parameters)
        elif template_type == "command_template":
            return self._process_command_template(template_name, output_path, parameters)
        elif template_type == "file_template":
            return self._process_file_template(template_name, output_path, parameters)
        else:
            return self._process_default_template(template_name, output_path, parameters)

    def _process_csharp_console(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a C# console template."""
        try:
            from .languages.csharp.generators import CSharpProjectGenerator

            generator = CSharpProjectGenerator()
            project_name = parameters.get("project_name", pathlib.Path(output_path).name)

            result = generator.generate_project("console", project_name, output_path, **parameters)

            return {
                "success": result["success"],
                "type": "csharp_console_generation",
                "project_name": project_name,
                "output_path": output_path,
                "details": result,
            }
        except ImportError:
            return {"success": False, "type": "csharp_console_generation", "error": "C# generators not available"}
        except Exception as e:
            return {"success": False, "type": "csharp_console_generation", "error": str(e)}

    def _process_csharp_project(
        self, project_type: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a C# project template."""
        try:
            from .languages.csharp.generators import CSharpProjectGenerator

            generator = CSharpProjectGenerator()
            project_name = parameters.get("project_name", pathlib.Path(output_path).name)

            result = generator.generate_project(project_type, project_name, output_path, **parameters)

            return {
                "success": result["success"],
                "type": "csharp_project_generation",
                "project_type": project_type,
                "project_name": project_name,
                "output_path": output_path,
                "details": result,
            }
        except ImportError:
            return {"success": False, "type": "csharp_project_generation", "error": "C# generators not available"}
        except Exception as e:
            return {"success": False, "type": "csharp_project_generation", "error": str(e)}

    def _process_command_template(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a command-based template."""
        try:
            from ..execution.command_executor import CommandExecutor

            executor = CommandExecutor()
            command = template_name
            args = parameters.get("args", [])

            result = executor.execute(command, args, cwd=pathlib.Path(output_path).parent)

            return {
                "success": result.success,
                "type": "command_execution",
                "output": result.stdout,
                "error": result.stderr if not result.success else None,
                "command": result.executed_command,
            }
        except ImportError:
            return {"success": False, "type": "command_execution", "error": "Command executor not available"}
        except Exception as e:
            return {"success": False, "type": "command_execution", "error": str(e)}

    def _process_file_template(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a traditional file template."""
        try:
            if template_name in self.templates:
                content = self.render_template(template_name, parameters)

                # Write the content to the output path
                output_file = pathlib.Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(content, encoding="utf-8")

                return {
                    "success": True,
                    "type": "file_template",
                    "output_path": output_path,
                    "content_length": len(content),
                }
            else:
                return {"success": False, "type": "file_template", "error": f"Template '{template_name}' not found"}
        except Exception as e:
            return {"success": False, "type": "file_template", "error": str(e)}

    def _process_default_template(
        self, template_name: str, output_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a default template (fallback)."""
        try:
            # Create a basic file with template info
            output_file = pathlib.Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            content = f"""# {output_file.name}
# Generated by Cursor Plans MCP
# Template: {template_name}
# Parameters: {parameters}

# TODO: Implement {template_name} functionality
"""
            output_file.write_text(content, encoding="utf-8")

            return {"success": True, "type": "default_template", "output_path": output_path}
        except Exception as e:
            return {"success": False, "type": "default_template", "error": str(e)}

    def get_supported_template_types(self) -> List[str]:
        """Get list of supported template types."""
        return ["csharp_console", "csharp_project", "command_template", "file_template", "default_template"]
