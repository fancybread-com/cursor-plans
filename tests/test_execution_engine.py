"""
Tests for the execution engine and PlanExecutor.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cursor_plans_mcp.execution import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    Phase,
    PlanExecutor,
)


class TestPlanExecutor:
    """Test the main PlanExecutor class."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def executor(self, temp_project_dir):
        """Create a PlanExecutor instance."""
        return PlanExecutor(str(temp_project_dir))

    @pytest.fixture
    def sample_plan_data(self):
        """Sample plan data for testing."""
        return {
            "project": {"name": "test-project", "version": "1.0.0"},
            "target_state": {
                "architecture": [{"language": "python"}, {"framework": "FastAPI"}]
            },
            "resources": {
                "files": [
                    {
                        "path": "src/main.py",
                        "type": "entry_point",
                        "template": "fastapi_main",
                    }
                ]
            },
            "phases": {
                "foundation": {"priority": 1, "tasks": ["setup_project_structure"]},
                "api_layer": {
                    "priority": 2,
                    "dependencies": ["foundation"],
                    "tasks": ["create_endpoints"],
                },
            },
        }

    @pytest.fixture
    def sample_plan_file(self, temp_project_dir, sample_plan_data):
        """Create a sample plan file."""
        import yaml

        plan_file = temp_project_dir / "test.devplan"
        with open(plan_file, "w") as f:
            yaml.dump(sample_plan_data, f)
        return str(plan_file)

    @pytest.mark.asyncio
    async def test_executor_initialization(self, temp_project_dir):
        """Test PlanExecutor initialization."""
        executor = PlanExecutor(str(temp_project_dir))
        assert executor.project_dir == temp_project_dir
        assert executor.snapshot_manager is not None
        assert executor.dependency_resolver is not None

    @pytest.mark.asyncio
    async def test_load_plan_success(self, executor, sample_plan_file):
        """Test successful plan loading."""
        plan_data = await executor._load_plan(sample_plan_file)
        assert "project" in plan_data
        assert "target_state" in plan_data
        assert "resources" in plan_data
        assert "phases" in plan_data

    @pytest.mark.asyncio
    async def test_load_plan_file_not_found(self, executor):
        """Test plan loading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            await executor._load_plan("nonexistent.devplan")

    @pytest.mark.asyncio
    async def test_load_plan_missing_sections(self, executor, temp_project_dir):
        """Test plan loading with missing required sections."""
        import yaml

        invalid_plan = {"project": {"name": "test"}}  # Missing required sections
        plan_file = temp_project_dir / "invalid.devplan"
        with open(plan_file, "w") as f:
            yaml.dump(invalid_plan, f)

        with pytest.raises(ValueError, match="Missing required section"):
            await executor._load_plan(str(plan_file))

    @pytest.mark.asyncio
    async def test_dry_run_execution(self, executor, sample_plan_file):
        """Test dry run execution."""

        # Mock the dependency resolver
        with patch.object(
            executor.dependency_resolver, "create_execution_plan"
        ) as mock_create:
            mock_plan = ExecutionPlan(
                phases=[
                    Phase(
                        name="foundation",
                        data={"priority": 1},
                        priority=1,
                        dependencies=[],
                    ),
                    Phase(
                        name="api_layer",
                        data={"priority": 2},
                        priority=2,
                        dependencies=["foundation"],
                    ),
                ],
                plan_data={"resources": {"files": [{"path": "src/main.py"}]}},
            )
            mock_create.return_value = mock_plan

            result = await executor.execute_plan(sample_plan_file, dry_run=True)

            assert result.success is True
            assert result.status == ExecutionStatus.COMPLETED
            assert len(result.executed_phases) == 2
            assert "foundation" in result.executed_phases
            assert "api_layer" in result.executed_phases
            assert "Would create: src/main.py" in result.changes_made

    @pytest.mark.asyncio
    async def test_actual_execution_success(self, executor, sample_plan_file):
        """Test successful actual execution."""
        with patch.object(
            executor.snapshot_manager, "create_snapshot"
        ) as mock_snapshot:
            mock_snapshot.return_value = "test-snapshot-id"

            result = await executor.execute_plan(sample_plan_file, dry_run=False)

            assert result.success is True
            assert result.status == ExecutionStatus.COMPLETED
            assert result.snapshot_id == "test-snapshot-id"
            assert len(result.executed_phases) == 2

    @pytest.mark.asyncio
    async def test_execution_failure_with_rollback(self, executor, sample_plan_file):
        """Test execution failure triggers rollback."""
        with patch.object(
            executor.snapshot_manager, "create_snapshot"
        ) as mock_snapshot:
            with patch.object(
                executor.snapshot_manager, "restore_snapshot"
            ) as mock_restore:
                mock_snapshot.return_value = "test-snapshot-id"

                # Mock execution to fail
                with patch.object(
                    executor, "_execute_plan", side_effect=Exception("Test error")
                ):
                    result = await executor.execute_plan(
                        sample_plan_file, dry_run=False
                    )

                    assert result.success is False
                    assert result.status == ExecutionStatus.FAILED
                    assert "Test error" in result.error_message
                    mock_restore.assert_called_once_with("test-snapshot-id")

    @pytest.mark.asyncio
    async def test_rollback_to_snapshot(self, executor):
        """Test rollback functionality."""
        with patch.object(
            executor.snapshot_manager, "restore_snapshot"
        ) as mock_restore:
            mock_restore.return_value = True

            result = await executor.rollback_to_snapshot("test-snapshot")

            assert result.success is True
            assert result.status == ExecutionStatus.ROLLED_BACK
            mock_restore.assert_called_once_with("test-snapshot")

    @pytest.mark.asyncio
    async def test_rollback_failure(self, executor):
        """Test rollback failure handling."""
        with patch.object(
            executor.snapshot_manager, "restore_snapshot"
        ) as mock_restore:
            mock_restore.return_value = False

            result = await executor.rollback_to_snapshot("test-snapshot")

            assert result.success is False
            assert result.status == ExecutionStatus.FAILED
            assert "Failed to restore snapshot" in result.error_message

    @pytest.mark.asyncio
    async def test_list_snapshots(self, executor):
        """Test listing snapshots."""
        mock_snapshots = [
            {"id": "snap1", "description": "Test 1"},
            {"id": "snap2", "description": "Test 2"},
        ]

        with patch.object(executor.snapshot_manager, "list_snapshots") as mock_list:
            mock_list.return_value = mock_snapshots

            snapshots = await executor.list_snapshots()

            assert snapshots == mock_snapshots
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_phase(self, executor, sample_plan_data):
        """Test phase execution."""
        phase = Phase(
            name="foundation",
            data={"tasks": ["setup_project_structure"]},
            priority=1,
            dependencies=[],
        )

        with patch.object(executor, "_execute_task") as mock_task:
            mock_task.return_value = ["Created directory: src"]

            changes = await executor._execute_phase(phase, sample_plan_data)

            assert len(changes) > 0
            mock_task.assert_called_once_with(
                "setup_project_structure", sample_plan_data
            )

    @pytest.mark.asyncio
    async def test_execute_task_mapping(self, executor, sample_plan_data):
        """Test task execution mapping."""
        with patch.object(executor, "_setup_project_structure") as mock_setup:
            mock_setup.return_value = ["Created directory: src"]

            changes = await executor._execute_task(
                "setup_project_structure", sample_plan_data
            )

            assert len(changes) > 0
            mock_setup.assert_called_once_with(sample_plan_data)

    @pytest.mark.asyncio
    async def test_execute_unknown_task(self, executor, sample_plan_data):
        """Test execution of unknown task."""
        changes = await executor._execute_task("unknown_task", sample_plan_data)

        assert len(changes) == 1
        assert "Executed task: unknown_task" in changes[0]

    @pytest.mark.asyncio
    async def test_create_files(self, executor):
        """Test file creation from resources."""
        files = [
            {"path": "src/main.py", "type": "entry_point", "template": "fastapi_main"},
            {
                "path": "requirements.txt",
                "type": "dependencies",
                "template": "requirements",
            },
        ]

        with patch.object(executor, "_create_file") as mock_create:
            mock_create.return_value = True

            changes = await executor._create_files(files, "foundation")

            assert len(changes) == 2
            assert "Created: src/main.py" in changes
            assert "Created: requirements.txt" in changes
            assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_create_file_success(self, executor, temp_project_dir):
        """Test successful file creation."""
        result = await executor._create_file("test.py", "python", "basic")

        assert result is True
        assert (temp_project_dir / "test.py").exists()

    @pytest.mark.asyncio
    async def test_generate_file_content(self, executor):
        """Test file content generation."""
        content = executor._generate_file_content(
            "main.py", "entry_point", "fastapi_main"
        )

        assert "from fastapi import FastAPI" in content
        assert "app = FastAPI" in content

    @pytest.mark.asyncio
    async def test_setup_project_structure(self, executor, sample_plan_data):
        """Test project structure setup."""
        changes = await executor._setup_project_structure(sample_plan_data)

        assert len(changes) == 3
        assert "Created directory: src" in changes
        assert "Created directory: tests" in changes
        assert "Created directory: docs" in changes

    @pytest.mark.asyncio
    async def test_install_dependencies(self, executor, sample_plan_data):
        """Test dependency installation."""
        changes = await executor._install_dependencies(sample_plan_data)

        assert len(changes) == 1
        assert "Created: requirements.txt" in changes[0]

    @pytest.mark.asyncio
    async def test_create_models(self, executor, sample_plan_data):
        """Test model creation."""
        changes = await executor._create_models(sample_plan_data)

        assert len(changes) == 1
        assert "Created: src/models/models.py" in changes[0]

    @pytest.mark.asyncio
    async def test_create_endpoints(self, executor, sample_plan_data):
        """Test endpoint creation."""
        changes = await executor._create_endpoints(sample_plan_data)

        assert len(changes) == 1
        assert "Created: src/routes/main.py" in changes[0]

    @pytest.mark.asyncio
    async def test_implement_jwt(self, executor, sample_plan_data):
        """Test JWT implementation."""
        changes = await executor._implement_jwt(sample_plan_data)

        assert len(changes) == 1
        assert "Created: src/auth/jwt.py" in changes[0]

    @pytest.mark.asyncio
    async def test_add_auth_middleware(self, executor, sample_plan_data):
        """Test auth middleware creation."""
        changes = await executor._add_auth_middleware(sample_plan_data)

        assert len(changes) == 1
        assert "Created: src/middleware/auth.py" in changes[0]

    @pytest.mark.asyncio
    async def test_setup_testing(self, executor, sample_plan_data):
        """Test testing setup."""
        changes = await executor._setup_testing(sample_plan_data)

        assert len(changes) == 2
        assert "Created: tests/test_main.py" in changes
        assert "Created: tests/conftest.py" in changes


class TestExecutionResult:
    """Test the ExecutionResult dataclass."""

    def test_execution_result_initialization(self):
        """Test ExecutionResult initialization."""
        result = ExecutionResult(
            success=True,
            status=ExecutionStatus.COMPLETED,
            executed_phases=["foundation", "api_layer"],
        )

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED
        assert result.executed_phases == ["foundation", "api_layer"]
        assert result.changes_made == []

    def test_execution_result_with_changes(self):
        """Test ExecutionResult with changes."""
        result = ExecutionResult(
            success=True,
            status=ExecutionStatus.COMPLETED,
            executed_phases=["foundation"],
            changes_made=["Created: src/main.py"],
        )

        assert result.changes_made == ["Created: src/main.py"]

    def test_execution_result_failure(self):
        """Test ExecutionResult for failed execution."""
        result = ExecutionResult(
            success=False,
            status=ExecutionStatus.FAILED,
            executed_phases=["foundation"],
            failed_phase="api_layer",
            error_message="Test error",
        )

        assert result.success is False
        assert result.status == ExecutionStatus.FAILED
        assert result.failed_phase == "api_layer"
        assert result.error_message == "Test error"
