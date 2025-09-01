"""
Tests for permission error handling in the execution engine.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.cursor_plans_mcp.execution.engine import PlanExecutor


class TestPermissionHandling:
    """Test permission error handling in the execution engine."""

    @pytest.mark.asyncio
    async def test_create_file_permission_error(self, temp_dir):
        """Test that permission errors are properly handled when creating files."""
        executor = PlanExecutor(temp_dir)

        # Mock the file creation to simulate a permission error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError) as exc_info:
                await executor._create_file("test.py", "file", "basic")

            assert "File creation failed for test.py" in str(exc_info.value)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_file_os_error(self, temp_dir):
        """Test that OS errors are properly handled when creating files."""
        executor = PlanExecutor(temp_dir)

        # Mock the file creation to simulate an OS error
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            with pytest.raises(OSError) as exc_info:
                await executor._create_file("test.py", "file", "basic")

            assert "File creation failed for test.py" in str(exc_info.value)
            assert "No space left on device" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_directory_permission_error(self, temp_dir):
        """Test that permission errors are properly handled when creating directories."""
        executor = PlanExecutor(temp_dir)

        # Mock the directory creation to simulate a permission error
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError) as exc_info:
                await executor._create_file("subdir/test.py", "file", "basic")

            assert "Cannot create directory" in str(exc_info.value)
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_files_permission_error_propagation(self, temp_dir):
        """Test that permission errors in _create_files are properly propagated."""
        executor = PlanExecutor(temp_dir)

        files = [{"path": "test.py", "type": "file", "template": "basic"}]

        # Mock the file creation to simulate a permission error
        with patch.object(executor, "_create_file", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError) as exc_info:
                await executor._create_files(files, "test_phase")

            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_apply_plan_permission_error_handling(self, temp_dir):
        """Test that permission errors in apply_dev_plan are properly handled."""
        from src.cursor_plans_mcp.server import apply_dev_plan

        # Create a simple plan file
        plan_file = temp_dir / "test.devplan"
        plan_content = """
name: "test-project"
description: "Test project"
phases:
  - name: "setup"
    description: "Setup phase"
    tasks: ["setup_project_structure"]
    priority: 1
resources:
  files:
    - path: "src/main.py"
      type: "file"
      template: "basic"
"""
        plan_file.write_text(plan_content)

        # Mock the PlanExecutor to simulate a permission error
        with patch("src.cursor_plans_mcp.server.PlanExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor_class.return_value = mock_executor
            mock_executor.execute_plan.side_effect = PermissionError("Cannot write to file src/main.py")

            result = await apply_dev_plan({"plan_file": str(plan_file), "dry_run": False})

            # Check that the error is properly formatted
            assert "❌ **Permission Error:**" in result[0].text
            assert "Cannot write to file src/main.py" in result[0].text
            assert "Troubleshooting:" in result[0].text
            assert "Check if you have write permissions" in result[0].text

    @pytest.mark.asyncio
    async def test_apply_plan_os_error_handling(self, temp_dir):
        """Test that OS errors in apply_dev_plan are properly handled."""
        from src.cursor_plans_mcp.server import apply_dev_plan

        # Create a simple plan file
        plan_file = temp_dir / "test.devplan"
        plan_content = """
name: "test-project"
description: "Test project"
phases:
  - name: "setup"
    description: "Setup phase"
    tasks: ["setup_project_structure"]
    priority: 1
resources:
  files:
    - path: "src/main.py"
      type: "file"
      template: "basic"
"""
        plan_file.write_text(plan_content)

        # Mock the PlanExecutor to simulate an OS error
        with patch("src.cursor_plans_mcp.server.PlanExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor_class.return_value = mock_executor
            mock_executor.execute_plan.side_effect = OSError("No space left on device")

            result = await apply_dev_plan({"plan_file": str(plan_file), "dry_run": False})

            # Check that the error is properly formatted
            assert "❌ **OS Error:**" in result[0].text
            assert "No space left on device" in result[0].text
            assert "Troubleshooting:" in result[0].text
            assert "Check disk space" in result[0].text
