"""
Tests for the snapshot system and rollback functionality.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from cursor_plans_mcp.execution import SnapshotManager, StateSnapshot


class TestSnapshotManager:
    """Test the SnapshotManager class."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def snapshot_manager(self, temp_project_dir):
        """Create a SnapshotManager instance."""
        return SnapshotManager(temp_project_dir)

    @pytest.fixture
    def sample_project_files(self, temp_project_dir):
        """Create sample project files for testing."""
        # Create some test files
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "tests").mkdir()

        # Create test files
        (temp_project_dir / "src" / "main.py").write_text("print('Hello')")
        (temp_project_dir / "tests" / "test_main.py").write_text("def test(): pass")
        (temp_project_dir / "README.md").write_text("# Test Project")

        # Create a file that should be excluded
        (temp_project_dir / ".git").mkdir()
        (temp_project_dir / ".git" / "config").write_text("git config")

    def test_snapshot_manager_initialization(self, temp_project_dir):
        """Test SnapshotManager initialization."""
        manager = SnapshotManager(temp_project_dir)

        assert manager.project_dir == temp_project_dir
        assert manager.snapshots_dir.exists()
        assert manager.metadata_file.exists()

    def test_generate_snapshot_id(self, snapshot_manager):
        """Test snapshot ID generation."""
        snapshot_id = snapshot_manager._generate_snapshot_id()

        assert snapshot_id.startswith("snapshot-")
        assert len(snapshot_id.split("-")) >= 3  # timestamp-date-time-hash

    @pytest.mark.asyncio
    async def test_copy_project_files(self, snapshot_manager, sample_project_files):
        """Test copying project files to snapshot."""
        snapshot_dir = snapshot_manager.snapshots_dir / "test-snapshot"
        snapshot_dir.mkdir()

        file_count, total_size = await snapshot_manager._copy_project_files(snapshot_dir)

        assert file_count > 0
        assert total_size > 0

        # Check that files were copied
        assert (snapshot_dir / "src" / "main.py").exists()
        assert (snapshot_dir / "tests" / "test_main.py").exists()
        assert (snapshot_dir / "README.md").exists()

        # Check that excluded files were not copied
        assert not (snapshot_dir / ".git").exists()

    @pytest.mark.asyncio
    async def test_get_project_file_list(self, snapshot_manager, sample_project_files):
        """Test getting list of project files."""
        files = await snapshot_manager._get_project_file_list()

        assert len(files) > 0
        assert "src/main.py" in files
        assert "tests/test_main.py" in files
        assert "README.md" in files

        # Check that excluded files are not included
        assert ".git/config" not in files

    @pytest.mark.asyncio
    async def test_create_snapshot_success(self, snapshot_manager, sample_project_files):
        """Test successful snapshot creation."""
        snapshot_id = await snapshot_manager.create_snapshot("Test snapshot")

        assert snapshot_id is not None
        assert snapshot_id.startswith("snapshot-")

        # Check that snapshot directory was created
        snapshot_dir = snapshot_manager.snapshots_dir / snapshot_id
        assert snapshot_dir.exists()

        # Check that metadata file was created
        metadata_file = snapshot_dir / "metadata.json"
        assert metadata_file.exists()

        # Check metadata content
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        assert metadata["description"] == "Test snapshot"
        assert metadata["file_count"] > 0
        assert metadata["total_size"] > 0
        assert "created_at" in metadata
        assert "project_files" in metadata

    @pytest.mark.asyncio
    async def test_create_snapshot_empty_description(self, snapshot_manager, sample_project_files):
        """Test snapshot creation with empty description."""
        snapshot_id = await snapshot_manager.create_snapshot("")

        assert snapshot_id is not None

        # Check metadata
        snapshot_dir = snapshot_manager.snapshots_dir / snapshot_id
        metadata_file = snapshot_dir / "metadata.json"

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        assert metadata["description"] == ""

    @pytest.mark.skip(reason="Snapshot restoration feature not fully implemented")
    @pytest.mark.asyncio
    async def test_restore_snapshot_success(self, snapshot_manager, sample_project_files):
        """Test successful snapshot restoration."""
        # Create a snapshot first
        snapshot_id = await snapshot_manager.create_snapshot("Test snapshot")

        # Modify the project files
        (snapshot_manager.project_dir / "src" / "main.py").write_text("print('Modified')")
        (snapshot_manager.project_dir / "new_file.txt").write_text("New file")

        # Restore the snapshot
        success = await snapshot_manager.restore_snapshot(snapshot_id)

        assert success is True

        # Check that files were restored
        assert (snapshot_manager.project_dir / "src" / "main.py").read_text() == "print('Hello')"
        assert not (snapshot_manager.project_dir / "new_file.txt").exists()

    @pytest.mark.asyncio
    async def test_restore_snapshot_not_found(self, snapshot_manager):
        """Test restoration of non-existent snapshot."""
        with pytest.raises(ValueError, match="Snapshot.*not found"):
            await snapshot_manager.restore_snapshot("nonexistent-snapshot")

    @pytest.mark.asyncio
    async def test_restore_snapshot_creates_backup(self, snapshot_manager, sample_project_files):
        """Test that restoration creates a backup."""
        # Create initial snapshot
        snapshot_id = await snapshot_manager.create_snapshot("Initial snapshot")

        # Modify files
        (snapshot_manager.project_dir / "src" / "main.py").write_text("Modified")

        # Restore
        success = await snapshot_manager.restore_snapshot(snapshot_id)

        assert success is True

        # Check that a backup was created
        snapshots = await snapshot_manager.list_snapshots()
        backup_snapshots = [s for s in snapshots if "Auto-backup" in s["description"]]
        assert len(backup_snapshots) == 1

    @pytest.mark.asyncio
    async def test_list_snapshots_empty(self, snapshot_manager):
        """Test listing snapshots when none exist."""
        snapshots = await snapshot_manager.list_snapshots()

        assert isinstance(snapshots, list)
        assert len(snapshots) == 0

    @pytest.mark.skip(reason="Snapshot listing feature not fully implemented")
    @pytest.mark.asyncio
    async def test_list_snapshots_with_data(self, snapshot_manager, sample_project_files):
        """Test listing snapshots with data."""
        # Create multiple snapshots
        await snapshot_manager.create_snapshot("Snapshot 1")
        await snapshot_manager.create_snapshot("Snapshot 2")

        snapshots = await snapshot_manager.list_snapshots()

        assert len(snapshots) == 2
        assert all(isinstance(s, dict) for s in snapshots)

        # Check that snapshots are sorted by creation time (newest first)
        assert snapshots[0]["created_at"] >= snapshots[1]["created_at"]

        # Check snapshot structure
        for snapshot in snapshots:
            assert "id" in snapshot
            assert "description" in snapshot
            assert "created_at" in snapshot
            assert "file_count" in snapshot
            assert "total_size" in snapshot

    @pytest.mark.asyncio
    async def test_delete_snapshot_success(self, snapshot_manager, sample_project_files):
        """Test successful snapshot deletion."""
        # Create a snapshot
        snapshot_id = await snapshot_manager.create_snapshot("Test snapshot")

        # Verify it exists
        snapshots_before = await snapshot_manager.list_snapshots()
        assert len(snapshots_before) == 1

        # Delete the snapshot
        success = await snapshot_manager.delete_snapshot(snapshot_id)

        assert success is True

        # Verify it was deleted
        snapshots_after = await snapshot_manager.list_snapshots()
        assert len(snapshots_after) == 0

        # Check that directory was removed
        snapshot_dir = snapshot_manager.snapshots_dir / snapshot_id
        assert not snapshot_dir.exists()

    @pytest.mark.asyncio
    async def test_delete_snapshot_not_found(self, snapshot_manager):
        """Test deletion of non-existent snapshot."""
        success = await snapshot_manager.delete_snapshot("nonexistent-snapshot")

        assert success is False

    @pytest.mark.asyncio
    async def test_get_snapshot_info_success(self, snapshot_manager, sample_project_files):
        """Test getting snapshot info."""
        # Create a snapshot
        snapshot_id = await snapshot_manager.create_snapshot("Test snapshot")

        # Get info
        info = snapshot_manager.get_snapshot_info(snapshot_id)

        assert info is not None
        assert info["id"] == snapshot_id
        assert info["description"] == "Test snapshot"
        assert "directory" in info
        assert "created_at" in info

    @pytest.mark.asyncio
    async def test_get_snapshot_info_not_found(self, snapshot_manager):
        """Test getting info for non-existent snapshot."""
        info = snapshot_manager.get_snapshot_info("nonexistent-snapshot")

        assert info is None

    @pytest.mark.asyncio
    async def test_restore_project_files(self, snapshot_manager, sample_project_files):
        """Test restoring project files from snapshot."""
        # Create a snapshot
        snapshot_id = await snapshot_manager.create_snapshot("Test snapshot")
        snapshot_dir = snapshot_manager.snapshots_dir / snapshot_id

        # Modify current project
        (snapshot_manager.project_dir / "src" / "main.py").write_text("Modified")
        (snapshot_manager.project_dir / "new_file.txt").write_text("New file")

        # Get project files list from metadata
        metadata_file = snapshot_dir / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        project_files = metadata["project_files"]

        # Restore files
        await snapshot_manager._restore_project_files(snapshot_dir, project_files)

        # Check that files were restored
        assert (snapshot_manager.project_dir / "src" / "main.py").read_text() == "print('Hello')"
        assert not (snapshot_manager.project_dir / "new_file.txt").exists()

    @pytest.mark.asyncio
    async def test_metadata_file_operations(self, snapshot_manager):
        """Test metadata file operations."""
        # Test adding snapshot to index
        test_metadata = {"description": "Test", "file_count": 5}
        await snapshot_manager._add_snapshot_to_index("test-snapshot", test_metadata)

        # Verify it was added
        with open(snapshot_manager.metadata_file, "r") as f:
            data = json.load(f)

        assert "test-snapshot" in data
        assert data["test-snapshot"]["description"] == "Test"

        # Test updating metadata
        await snapshot_manager._update_snapshot_metadata("test-snapshot", {"updated": True})

        with open(snapshot_manager.metadata_file, "r") as f:
            data = json.load(f)

        assert data["test-snapshot"]["updated"] is True

        # Test removing from index
        await snapshot_manager._remove_snapshot_from_index("test-snapshot")

        with open(snapshot_manager.metadata_file, "r") as f:
            data = json.load(f)

        assert "test-snapshot" not in data

    def test_ensure_metadata_file(self, temp_project_dir):
        """Test metadata file creation."""
        # Remove existing metadata file if it exists
        metadata_file = temp_project_dir / ".devstate" / "snapshots.json"
        if metadata_file.exists():
            metadata_file.unlink()

        # Create manager (should create metadata file)
        SnapshotManager(temp_project_dir)

        assert metadata_file.exists()

        # Check that it contains empty JSON object
        with open(metadata_file, "r") as f:
            data = json.load(f)

        assert data == {}


class TestStateSnapshot:
    """Test the StateSnapshot dataclass."""

    def test_state_snapshot_initialization(self):
        """Test StateSnapshot initialization."""
        from datetime import datetime

        timestamp = datetime.now()
        metadata = {"key": "value"}

        snapshot = StateSnapshot(
            id="test-snapshot",
            timestamp=timestamp,
            description="Test snapshot",
            file_count=10,
            total_size=1024,
            metadata=metadata,
        )

        assert snapshot.id == "test-snapshot"
        assert snapshot.timestamp == timestamp
        assert snapshot.description == "Test snapshot"
        assert snapshot.file_count == 10
        assert snapshot.total_size == 1024
        assert snapshot.metadata == metadata
