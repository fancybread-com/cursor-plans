"""
State snapshot management for rollback capabilities.
"""

import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class StateSnapshot:
    """Represents a state snapshot."""
    id: str
    timestamp: datetime
    description: str
    file_count: int
    total_size: int
    metadata: Dict[str, Any]


class SnapshotManager:
    """
    Manages state snapshots for rollback capabilities.

    Handles:
    - Creating snapshots of current state
    - Restoring snapshots
    - Listing available snapshots
    - Snapshot metadata management
    """

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.snapshots_dir = self.project_dir / ".devstate" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        self.metadata_file = self.project_dir / ".devstate" / "snapshots.json"
        self._ensure_metadata_file()

    async def create_snapshot(self, description: str = "") -> str:
        """
        Create a snapshot of the current project state.

        Args:
            description: Human-readable description of the snapshot

        Returns:
            Snapshot ID
        """
        snapshot_id = self._generate_snapshot_id()
        timestamp = datetime.now()

        # Create snapshot directory
        snapshot_dir = self.snapshots_dir / snapshot_id
        snapshot_dir.mkdir(exist_ok=True)

        # Copy project files
        file_count, total_size = await self._copy_project_files(snapshot_dir)

        # Create metadata
        metadata = {
            "description": description,
            "file_count": file_count,
            "total_size": total_size,
            "created_at": timestamp.isoformat(),
            "project_files": await self._get_project_file_list()
        }

        # Save metadata
        metadata_file = snapshot_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Update snapshots index
        await self._add_snapshot_to_index(snapshot_id, metadata)

        return snapshot_id

    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore project state from a snapshot.

        Args:
            snapshot_id: ID of the snapshot to restore

        Returns:
            True if restoration was successful
        """
        snapshot_dir = self.snapshots_dir / snapshot_id

        if not snapshot_dir.exists():
            raise ValueError(f"Snapshot {snapshot_id} not found")

        try:
            # Read metadata
            metadata_file = snapshot_dir / "metadata.json"
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Create backup of current state before restoration
            backup_id = await self.create_snapshot("Auto-backup before restoration")

            # Restore files
            project_files = metadata.get("project_files", [])
            await self._restore_project_files(snapshot_dir, project_files)

            # Update metadata to indicate restoration
            await self._update_snapshot_metadata(snapshot_id, {
                "restored_at": datetime.now().isoformat(),
                "backup_created": backup_id
            })

            return True

        except Exception as e:
            print(f"Failed to restore snapshot {snapshot_id}: {str(e)}")
            return False

    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots."""
        snapshots = []

        if not self.metadata_file.exists():
            return snapshots

        try:
            with open(self.metadata_file, 'r') as f:
                snapshots_data = json.load(f)

            for snapshot_id, metadata in snapshots_data.items():
                snapshot_info = {
                    "id": snapshot_id,
                    "description": metadata.get("description", ""),
                    "created_at": metadata.get("created_at", ""),
                    "file_count": metadata.get("file_count", 0),
                    "total_size": metadata.get("total_size", 0),
                    "restored_at": metadata.get("restored_at"),
                    "backup_created": metadata.get("backup_created")
                }
                snapshots.append(snapshot_info)

            # Sort by creation time (newest first)
            snapshots.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            print(f"Failed to load snapshots: {str(e)}")

        return snapshots

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Args:
            snapshot_id: ID of the snapshot to delete

        Returns:
            True if deletion was successful
        """
        snapshot_dir = self.snapshots_dir / snapshot_id

        if not snapshot_dir.exists():
            return False

        try:
            # Remove snapshot directory
            shutil.rmtree(snapshot_dir)

            # Remove from index
            await self._remove_snapshot_from_index(snapshot_id)

            return True

        except Exception as e:
            print(f"Failed to delete snapshot {snapshot_id}: {str(e)}")
            return False

    def _generate_snapshot_id(self) -> str:
        """Generate a unique snapshot ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        random_suffix = hashlib.md5(f"{timestamp}-{os.getpid()}".encode()).hexdigest()[:8]
        return f"snapshot-{timestamp}-{random_suffix}"

    async def _copy_project_files(self, snapshot_dir: Path) -> tuple[int, int]:
        """Copy project files to snapshot directory."""
        file_count = 0
        total_size = 0

        # Files/directories to exclude
        exclude_patterns = [
            ".devstate",
            ".git",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".venv",
            "node_modules",
            ".DS_Store"
        ]

        for item in self.project_dir.rglob("*"):
            # Skip excluded patterns
            if any(pattern in str(item) for pattern in exclude_patterns):
                continue

            # Skip the snapshot directory itself
            if item.is_relative_to(snapshot_dir):
                continue

            relative_path = item.relative_to(self.project_dir)
            target_path = snapshot_dir / relative_path

            if item.is_file():
                # Copy file
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)
                file_count += 1
                total_size += item.stat().st_size
            elif item.is_dir():
                # Create directory
                target_path.mkdir(parents=True, exist_ok=True)

        return file_count, total_size

    async def _restore_project_files(self, snapshot_dir: Path, project_files: List[str]):
        """Restore project files from snapshot."""
        # First, remove existing files (except .devstate)
        for item in self.project_dir.iterdir():
            if item.name == ".devstate":
                continue

            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Separate files and directories
        files = [f for f in project_files if not (snapshot_dir / f).is_dir()]
        directories = [d for d in project_files if (snapshot_dir / d).is_dir()]

        # First restore directories
        for dir_path in directories:
            source_path = snapshot_dir / dir_path
            target_path = self.project_dir / dir_path

            if source_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)

        # Then restore individual files
        for file_path in files:
            source_path = snapshot_dir / file_path
            target_path = self.project_dir / file_path

            if source_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)

    async def _get_project_file_list(self) -> List[str]:
        """Get list of project files (relative paths)."""
        files = []

        exclude_patterns = [
            ".devstate",
            ".git",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".venv",
            "node_modules",
            ".DS_Store"
        ]

        for item in self.project_dir.rglob("*"):
            # Skip excluded patterns
            if any(pattern in str(item) for pattern in exclude_patterns):
                continue

            if item.is_file() or item.is_dir():
                relative_path = item.relative_to(self.project_dir)
                files.append(str(relative_path))

        return files

    def _ensure_metadata_file(self):
        """Ensure the snapshots metadata file exists."""
        if not self.metadata_file.exists():
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)

    async def _add_snapshot_to_index(self, snapshot_id: str, metadata: Dict[str, Any]):
        """Add snapshot to the metadata index."""
        try:
            with open(self.metadata_file, 'r') as f:
                snapshots_data = json.load(f)

            snapshots_data[snapshot_id] = metadata

            with open(self.metadata_file, 'w') as f:
                json.dump(snapshots_data, f, indent=2)

        except Exception as e:
            print(f"Failed to update snapshot index: {str(e)}")

    async def _remove_snapshot_from_index(self, snapshot_id: str):
        """Remove snapshot from the metadata index."""
        try:
            with open(self.metadata_file, 'r') as f:
                snapshots_data = json.load(f)

            if snapshot_id in snapshots_data:
                del snapshots_data[snapshot_id]

            with open(self.metadata_file, 'w') as f:
                json.dump(snapshots_data, f, indent=2)

        except Exception as e:
            print(f"Failed to remove snapshot from index: {str(e)}")

    async def _update_snapshot_metadata(self, snapshot_id: str, updates: Dict[str, Any]):
        """Update snapshot metadata."""
        try:
            with open(self.metadata_file, 'r') as f:
                snapshots_data = json.load(f)

            if snapshot_id in snapshots_data:
                snapshots_data[snapshot_id].update(updates)

            with open(self.metadata_file, 'w') as f:
                json.dump(snapshots_data, f, indent=2)

        except Exception as e:
            print(f"Failed to update snapshot metadata: {str(e)}")

    def get_snapshot_info(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific snapshot."""
        snapshot_dir = self.snapshots_dir / snapshot_id

        if not snapshot_dir.exists():
            return None

        metadata_file = snapshot_dir / "metadata.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            return {
                "id": snapshot_id,
                "directory": str(snapshot_dir),
                **metadata
            }

        except Exception as e:
            print(f"Failed to read snapshot info: {str(e)}")
            return None
