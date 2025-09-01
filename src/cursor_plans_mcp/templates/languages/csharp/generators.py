"""C# project generators using command templates."""
import pathlib
import subprocess
from typing import Any, Dict, List, Optional

from .commands import CSharpCommands


class CSharpProjectGenerator:
    """Generates C# projects using dotnet commands."""

    def __init__(self, working_directory: Optional[pathlib.Path] = None):
        self.working_directory = working_directory or pathlib.Path.cwd()
        self.commands = CSharpCommands()

    def generate_project(self, project_type: str, project_name: str,
                        output_path: str, **kwargs) -> Dict[str, Any]:
        """Generate a C# project of the specified type."""
        project_commands = self.commands.get_project_commands()

        if project_type not in project_commands:
            raise ValueError(f"Unknown project type: {project_type}")

        command_config = project_commands[project_type]

        # Prepare parameters
        params = {
            "project_name": project_name,
            "output_path": output_path,
            **kwargs
        }

        # Set default framework if not provided
        if "framework" not in params:
            params["framework"] = self.commands.get_default_framework()

        # Validate parameters
        if project_type == "console":
            validation_errors = self.commands.validate_console_params(project_name, output_path, **kwargs)
            if validation_errors:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validation_errors": validation_errors
                }

        required_params = command_config.get("required_params", [])
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        # Execute command
        args = command_config["args"]
        result = self._execute_command(
            command_config["command"],
            args,
            cwd=pathlib.Path(output_path).parent
        )

        if result["success"]:
            # Post-generation customization
            self._customize_project(project_type, output_path, **kwargs)

            return {
                "success": True,
                "project_type": project_type,
                "project_name": project_name,
                "output_path": output_path,
                "command_output": result["output"],
                "post_generation": command_config.get("post_generation", []),
                "framework_used": params.get("framework")
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "command_output": result["output"]
            }

    def create_solution(self, solution_name: str, output_path: str) -> Dict[str, Any]:
        """Create a new solution file."""
        solution_commands = self.commands.get_solution_commands()
        command_config = solution_commands["create_solution"]

        args = command_config["args"]

        result = self._execute_command(
            command_config["command"],
            args,
            cwd=pathlib.Path(output_path)
        )

        return {
            "success": result["success"],
            "solution_name": solution_name,
            "output_path": output_path,
            "command_output": result["output"],
            "error": result["error"] if not result["success"] else None
        }

    def add_project_to_solution(self, solution_path: str, project_path: str) -> Dict[str, Any]:
        """Add a project to an existing solution."""
        solution_commands = self.commands.get_solution_commands()
        command_config = solution_commands["add_project_to_solution"]

        args = command_config["args"]

        result = self._execute_command(
            command_config["command"],
            args,
            cwd=pathlib.Path(solution_path).parent
        )

        return {
            "success": result["success"],
            "solution_path": solution_path,
            "project_path": project_path,
            "command_output": result["output"],
            "error": result["error"] if not result["success"] else None
        }

    def _execute_command(self, command: str, args: List[str],
                        cwd: Optional[pathlib.Path] = None) -> Dict[str, Any]:
        """Execute a command with safety checks."""
        if not self._is_command_allowed(command):
            return {
                "success": False,
                "error": f"Command '{command}' is not allowed",
                "output": ""
            }

        cwd = cwd or self.working_directory
        full_command = [command] + args

        try:
            result = subprocess.run(
                full_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes",
                "output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is in allowed list."""
        allowed_commands = {'dotnet', 'git', 'npm', 'yarn', 'python', 'pip'}
        return command in allowed_commands

    def _customize_project(self, project_type: str, project_path: str, **kwargs):
        """Apply post-generation customizations."""
        if project_type == "console":
            self._customize_console_project(project_path, **kwargs)

    def _customize_console_project(self, project_path: str, **kwargs):
        """Apply console-specific customizations."""
        project_dir = pathlib.Path(project_path)

        # Ensure the project directory exists
        project_dir.mkdir(parents=True, exist_ok=True)

        # Customize Program.cs with better structure
        program_file = project_dir / "Program.cs"
        if program_file.exists():
            self._enhance_program_file(program_file, **kwargs)

        # Add a basic README
        readme_file = project_dir / "README.md"
        if not readme_file.exists():
            self._create_console_readme(readme_file, **kwargs)

    def _enhance_program_file(self, program_file: pathlib.Path, **kwargs):
        """Enhance the Program.cs file with better structure."""
        try:
            content = program_file.read_text(encoding='utf-8')

            # Check if it's the basic template
            if "Console.WriteLine(\"Hello, World!\")" in content:
                enhanced_content = self._get_enhanced_program_content(**kwargs)
                program_file.write_text(enhanced_content, encoding='utf-8')
        except Exception:
            # If we can't enhance, leave the original
            pass

    def _get_enhanced_program_content(self, **kwargs) -> str:
        """Get enhanced Program.cs content."""
        project_name = kwargs.get("project_name", "ConsoleApp")

        return f'''using System;

namespace {project_name}
{{
    class Program
    {{
        static void Main(string[] args)
        {{
            Console.WriteLine("Hello, World!");

            // Display command line arguments if any
            if (args.Length > 0)
            {{
                Console.WriteLine("\\nCommand line arguments:");
                for (int i = 0; i < args.Length; i++)
                {{
                    Console.WriteLine($"[{{i}}]: {{args[i]}}");
                }}
            }}

            // Wait for user input before closing
            Console.WriteLine("\\nPress any key to exit...");
            Console.ReadKey();
        }}
    }}
}}'''

    def _create_console_readme(self, readme_file: pathlib.Path, **kwargs):
        """Create a README file for the console project."""
        project_name = kwargs.get("project_name", "ConsoleApp")
        framework = kwargs.get("framework", self.commands.get_default_framework())

        readme_content = f'''# {project_name}

A C# console application created with .NET.

## Getting Started

### Prerequisites
- .NET 6.0 or later
- Your favorite IDE (Visual Studio, VS Code, Rider, etc.)

### Running the Application

1. Navigate to the project directory:
   ```bash
   cd {project_name}
   ```

2. Build the project:
   ```bash
   dotnet build
   ```

3. Run the application:
   ```bash
   dotnet run
   ```

## Project Structure

- `Program.cs` - Main entry point and program logic
- `{project_name}.csproj` - Project file with dependencies and configuration
- Target Framework: {framework}

## Customization

You can customize this console application by:
- Adding new methods to the Program class
- Creating additional classes for business logic
- Adding NuGet packages for additional functionality

## Building for Production

To create a production build:

```bash
dotnet publish -c Release
```

This will create an optimized build in the `bin/Release/{framework}/publish/` directory.
'''

        readme_file.write_text(readme_content, encoding='utf-8')
