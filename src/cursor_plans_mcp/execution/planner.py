"""
Dependency resolution and execution planning.
"""

from typing import Dict, Any, List, Set
from dataclasses import dataclass
from collections import defaultdict, deque


@dataclass
class Phase:
    """Represents a single execution phase."""
    name: str
    data: Dict[str, Any]
    priority: int
    dependencies: List[str]


@dataclass
class ExecutionPlan:
    """Complete execution plan with resolved dependencies."""
    phases: List[Phase]
    plan_data: Dict[str, Any]


class DependencyResolver:
    """
    Resolves phase dependencies and creates execution plans.

    Handles:
    - Dependency graph construction
    - Cycle detection
    - Topological sorting
    - Priority-based ordering
    """

    def create_execution_plan(self, plan_data: Dict[str, Any]) -> ExecutionPlan:
        """
        Create an execution plan from plan data.

        Args:
            plan_data: Parsed plan data

        Returns:
            ExecutionPlan with phases in correct execution order
        """
        phases = self._parse_phases(plan_data)

        # Validate dependencies
        self._validate_dependencies(phases)

        # Resolve execution order
        ordered_phases = self._resolve_execution_order(phases)

        return ExecutionPlan(phases=ordered_phases, plan_data=plan_data)

    def _parse_phases(self, plan_data: Dict[str, Any]) -> List[Phase]:
        """Parse phases from plan data."""
        phases = []

        if "phases" not in plan_data:
            return phases

        for phase_name, phase_data in plan_data["phases"].items():
            if not isinstance(phase_data, dict):
                continue

            # Extract phase information
            priority = phase_data.get("priority", 999)  # Default low priority
            dependencies = phase_data.get("dependencies", [])

            # Ensure priority is an integer
            if not isinstance(priority, int):
                priority = 999

            # Ensure dependencies is a list
            if not isinstance(dependencies, list):
                dependencies = []

            phase = Phase(
                name=phase_name,
                data=phase_data,
                priority=priority,
                dependencies=dependencies
            )

            phases.append(phase)

        return phases

    def _validate_dependencies(self, phases: List[Phase]):
        """Validate that all dependencies exist and detect cycles."""
        phase_names = {phase.name for phase in phases}

        # Check for missing dependencies
        for phase in phases:
            for dep in phase.dependencies:
                if dep not in phase_names:
                    raise ValueError(f"Phase '{phase.name}' depends on unknown phase '{dep}'")

        # Check for cycles
        if self._has_cycles(phases):
            raise ValueError("Circular dependency detected in phases")

    def _has_cycles(self, phases: List[Phase]) -> bool:
        """Check for cycles in the dependency graph using DFS."""
        # Build adjacency list
        graph = defaultdict(list)
        for phase in phases:
            for dep in phase.dependencies:
                graph[phase.name].append(dep)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle_dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for phase in phases:
            if phase.name not in visited:
                if has_cycle_dfs(phase.name):
                    return True

        return False

    def _resolve_execution_order(self, phases: List[Phase]) -> List[Phase]:
        """
        Resolve execution order using topological sort with priority tie-breaking.

        Returns phases in the order they should be executed.
        """
        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        for phase in phases:
            in_degree[phase.name] = 0

        for phase in phases:
            for dep in phase.dependencies:
                graph[dep].append(phase.name)
                in_degree[phase.name] += 1

        # Topological sort with priority queue
        from queue import PriorityQueue

        # Queue of (priority, phase_name) tuples
        queue = PriorityQueue()

        # Add phases with no dependencies
        for phase in phases:
            if in_degree[phase.name] == 0:
                queue.put((phase.priority, phase.name))

        ordered_phases = []
        phase_map = {phase.name: phase for phase in phases}

        while not queue.empty():
            priority, phase_name = queue.get()
            phase = phase_map[phase_name]
            ordered_phases.append(phase)

            # Process dependents
            for dependent in graph[phase_name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    dependent_phase = phase_map[dependent]
                    queue.put((dependent_phase.priority, dependent))

        # Check if all phases were processed
        if len(ordered_phases) != len(phases):
            raise ValueError("Circular dependency detected (should have been caught earlier)")

        return ordered_phases

    def get_execution_graph(self, phases: List[Phase]) -> Dict[str, List[str]]:
        """Get the execution dependency graph for visualization."""
        graph = defaultdict(list)

        for phase in phases:
            for dep in phase.dependencies:
                graph[dep].append(phase.name)

        return dict(graph)

    def get_phase_dependencies(self, phase_name: str, phases: List[Phase]) -> List[str]:
        """Get all dependencies for a specific phase."""
        phase_map = {phase.name: phase for phase in phases}

        if phase_name not in phase_map:
            return []

        return phase_map[phase_name].dependencies.copy()

    def get_dependent_phases(self, phase_name: str, phases: List[Phase]) -> List[str]:
        """Get all phases that depend on the specified phase."""
        dependents = []

        for phase in phases:
            if phase_name in phase.dependencies:
                dependents.append(phase.name)

        return dependents
