"""
Execution engine for development plans.

Provides plan execution, dependency resolution, and rollback capabilities.
"""

from .engine import ExecutionResult, ExecutionStatus, PlanExecutor
from .planner import DependencyResolver, ExecutionPlan, Phase
from .snapshot import SnapshotManager, StateSnapshot

__all__ = [
    "PlanExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "DependencyResolver",
    "ExecutionPlan",
    "Phase",
    "StateSnapshot",
    "SnapshotManager",
]
