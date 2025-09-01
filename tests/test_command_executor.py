"""Tests for command executor functionality."""
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cursor_plans_mcp.execution.command_executor import CommandExecutor, CommandResult


class TestCommandResult:
    """Test CommandResult dataclass."""

    def test_command_result_creation(self):
        """Test CommandResult can be created with all fields."""
        result = CommandResult(
            success=True,
            stdout="test output",
            stderr="",
            return_code=0,
            executed_command="test command"
        )

        assert result.success is True
        assert result.stdout == "test output"
        assert result.stderr == ""
        assert result.return_code == 0
        assert result.executed_command == "test command"


class TestCommandExecutor:
    """Test CommandExecutor functionality."""

    def test_initialization(self):
        """Test CommandExecutor can be initialized."""
        executor = CommandExecutor()
        assert executor is not None
        assert executor.working_directory is not None
        assert isinstance(executor.allowed_commands, set)

    def test_initialization_with_custom_working_directory(self):
        """Test CommandExecutor with custom working directory."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            executor = CommandExecutor(working_directory=temp_dir)
            assert executor.working_directory == temp_dir
        finally:
            shutil.rmtree(temp_dir)

    def test_allowed_commands_default(self):
        """Test default allowed commands."""
        executor = CommandExecutor()
        expected_commands = {'dotnet', 'git', 'npm', 'yarn', 'python', 'pip'}
        assert executor.allowed_commands == expected_commands

    def test_is_command_allowed(self):
        """Test command allowance checking."""
        executor = CommandExecutor()

        assert executor._is_command_allowed("dotnet") is True
        assert executor._is_command_allowed("git") is True
        assert executor._is_command_allowed("rm") is False
        assert executor._is_command_allowed("sudo") is False

    def test_add_allowed_command(self):
        """Test adding commands to allowed list."""
        executor = CommandExecutor()

        executor.add_allowed_command("custom_command")
        assert executor._is_command_allowed("custom_command") is True

    def test_remove_allowed_command(self):
        """Test removing commands from allowed list."""
        executor = CommandExecutor()

        executor.remove_allowed_command("pip")
        assert executor._is_command_allowed("pip") is False

    def test_get_allowed_commands(self):
        """Test getting copy of allowed commands."""
        executor = CommandExecutor()
        commands = executor.get_allowed_commands()

        assert isinstance(commands, set)
        assert commands == executor.allowed_commands
        # Should be a copy, not the same object
        assert commands is not executor.allowed_commands

    @patch('subprocess.run')
    def test_execute_successful_command(self, mock_run):
        """Test successful command execution."""
        # Mock successful subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("python", ["--version"])

        assert result.success is True
        assert result.stdout == "Success output"
        assert result.stderr == ""
        assert result.return_code == 0
        assert result.executed_command == "python --version"

    @patch('subprocess.run')
    def test_execute_failed_command(self, mock_run):
        """Test failed command execution."""
        # Mock failed subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("python", ["nonexistent_script.py"])

        assert result.success is False
        assert result.stdout == ""
        assert result.stderr == "Error message"
        assert result.return_code == 1
        assert result.executed_command == "python nonexistent_script.py"

    def test_execute_disallowed_command(self):
        """Test that disallowed commands raise ValueError."""
        executor = CommandExecutor()

        with pytest.raises(ValueError, match="Command 'rm' is not allowed"):
            executor.execute("rm", ["-rf", "/"])

    @patch('subprocess.run')
    def test_execute_with_custom_working_directory(self, mock_run):
        """Test command execution with custom working directory."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Mock successful subprocess result
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            executor = CommandExecutor()
            result = executor.execute("python", ["--version"], cwd=temp_dir)

            # Verify subprocess.run was called with correct cwd
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]['cwd'] == temp_dir

            assert result.success is True
        finally:
            shutil.rmtree(temp_dir)

    @patch('subprocess.run')
    def test_execute_timeout(self, mock_run):
        """Test command execution timeout."""
        # Mock timeout exception
        mock_run.side_effect = TimeoutError("Command timed out")

        executor = CommandExecutor()
        result = executor.execute("python", ["--version"])

        assert result.success is False
        assert result.stderr == "Command timed out"
        assert result.return_code == -1

    @patch('subprocess.run')
    def test_execute_exception(self, mock_run):
        """Test command execution with general exception."""
        # Mock general exception
        mock_run.side_effect = Exception("Unexpected error")

        executor = CommandExecutor()
        result = executor.execute("python", ["--version"])

        assert result.success is False
        assert result.stderr == "Unexpected error"
        assert result.return_code == -1

    @patch('subprocess.run')
    def test_execute_with_complex_args(self, mock_run):
        """Test command execution with complex arguments."""
        # Mock successful subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        executor = CommandExecutor()
        args = ["new", "console", "-n", "MyApp", "-o", "./output"]
        result = executor.execute("dotnet", args)

        assert result.success is True
        assert result.executed_command == "dotnet new console -n MyApp -o ./output"

    def test_execute_empty_args(self):
        """Test command execution with empty arguments."""
        executor = CommandExecutor()

        with pytest.raises(ValueError, match="Command 'rm' is not allowed"):
            executor.execute("rm", [])

    @patch('subprocess.run')
    def test_execute_with_unicode_output(self, mock_run):
        """Test command execution with unicode output."""
        # Mock subprocess result with unicode
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello 世界"
        mock_result.stderr = "Error 错误"
        mock_run.return_value = mock_result

        executor = CommandExecutor()
        result = executor.execute("python", ["--version"])

        assert result.success is True
        assert result.stdout == "Hello 世界"
        assert result.stderr == "Error 错误"


class TestCommandExecutorIntegration:
    """Integration tests for CommandExecutor."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_execute_echo_command(self, temp_workspace):
        """Test executing a simple echo command (if available)."""
        executor = CommandExecutor(working_directory=temp_workspace)

        # Try to execute echo if it's available (Unix-like systems)
        try:
            result = executor.execute("echo", ["Hello World"])
            if result.success:
                assert "Hello World" in result.stdout
        except ValueError:
            # echo might not be in allowed commands, which is fine
            pass

    def test_execute_python_version(self, temp_workspace):
        """Test executing python --version."""
        executor = CommandExecutor(working_directory=temp_workspace)

        result = executor.execute("python", ["--version"])

        # Should succeed and contain version info
        assert result.success is True
        assert "Python" in result.stdout
        assert result.return_code == 0

    def test_execute_python_help(self, temp_workspace):
        """Test executing python --help."""
        executor = CommandExecutor(working_directory=temp_workspace)

        result = executor.execute("python", ["--help"])

        # Should succeed and contain help text
        assert result.success is True
        assert len(result.stdout) > 0
        assert result.return_code == 0

    def test_execute_nonexistent_command(self, temp_workspace):
        """Test executing a command that doesn't exist."""
        executor = CommandExecutor(working_directory=temp_workspace)

        # Add a fake command to allowed list
        executor.add_allowed_command("fake_command")

        result = executor.execute("fake_command", [])

        # Should fail because command doesn't exist
        assert result.success is False
        assert result.return_code != 0
