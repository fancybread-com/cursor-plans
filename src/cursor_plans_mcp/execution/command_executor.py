"""Command execution engine for template generation."""
import pathlib
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    executed_command: str


class CommandExecutor:
    """Executes shell commands safely."""

    def __init__(self, working_directory: Optional[pathlib.Path] = None):
        self.working_directory = working_directory or pathlib.Path.cwd()
        self.allowed_commands = {
            'dotnet', 'git', 'npm', 'yarn', 'python', 'pip'
        }

    def execute(self, command: str, args: List[str],
                cwd: Optional[pathlib.Path] = None) -> CommandResult:
        """Execute a command with safety checks."""
        if not self._is_command_allowed(command):
            raise ValueError(f"Command '{command}' is not allowed")

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

            return CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                executed_command=' '.join(full_command)
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                stdout="",
                stderr="Command timed out after 5 minutes",
                return_code=-1,
                executed_command=' '.join(full_command)
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                executed_command=' '.join(full_command)
            )

    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is in allowed list."""
        return command in self.allowed_commands

    def add_allowed_command(self, command: str):
        """Add a command to the allowed list."""
        self.allowed_commands.add(command)

    def remove_allowed_command(self, command: str):
        """Remove a command from the allowed list."""
        self.allowed_commands.discard(command)

    def get_allowed_commands(self) -> set:
        """Get the current list of allowed commands."""
        return self.allowed_commands.copy()
