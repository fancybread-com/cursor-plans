"""
Tests for the dependency resolver and execution planning.
"""

import pytest
from cursor_plans_mcp.execution import DependencyResolver, ExecutionPlan, Phase


class TestDependencyResolver:
    """Test the DependencyResolver class."""

    @pytest.fixture
    def resolver(self):
        """Create a DependencyResolver instance."""
        return DependencyResolver()

    @pytest.fixture
    def sample_plan_data(self):
        """Sample plan data with dependencies."""
        return {
            "project": {"name": "test"},
            "target_state": {"architecture": []},
            "resources": {"files": []},
            "phases": {
                "foundation": {
                    "priority": 1,
                    "tasks": ["setup_project"]
                },
                "data_layer": {
                    "priority": 2,
                    "dependencies": ["foundation"],
                    "tasks": ["create_models"]
                },
                "api_layer": {
                    "priority": 3,
                    "dependencies": ["data_layer"],
                    "tasks": ["create_endpoints"]
                },
                "security": {
                    "priority": 4,
                    "dependencies": ["api_layer"],
                    "tasks": ["implement_auth"]
                },
                "testing": {
                    "priority": 5,
                    "dependencies": ["security"],
                    "tasks": ["setup_tests"]
                }
            }
        }

    @pytest.fixture
    def simple_plan_data(self):
        """Simple plan data without dependencies."""
        return {
            "project": {"name": "test"},
            "target_state": {"architecture": []},
            "resources": {"files": []},
            "phases": {
                "phase1": {"priority": 1, "tasks": ["task1"]},
                "phase2": {"priority": 2, "tasks": ["task2"]}
            }
        }

    def test_resolver_initialization(self, resolver):
        """Test DependencyResolver initialization."""
        assert resolver is not None

    def test_parse_phases_success(self, resolver, sample_plan_data):
        """Test successful phase parsing."""
        phases = resolver._parse_phases(sample_plan_data)

        assert len(phases) == 5
        phase_names = [phase.name for phase in phases]
        assert "foundation" in phase_names
        assert "data_layer" in phase_names
        assert "api_layer" in phase_names
        assert "security" in phase_names
        assert "testing" in phase_names

    def test_parse_phases_no_phases(self, resolver):
        """Test parsing when no phases exist."""
        plan_data = {"project": {"name": "test"}}
        phases = resolver._parse_phases(plan_data)

        assert len(phases) == 0

    def test_parse_phases_invalid_phase_data(self, resolver):
        """Test parsing with invalid phase data."""
        plan_data = {
            "phases": {
                "valid_phase": {"priority": 1, "tasks": ["task1"]},
                "invalid_phase": "not_a_dict"  # Invalid
            }
        }
        phases = resolver._parse_phases(plan_data)

        assert len(phases) == 1
        assert phases[0].name == "valid_phase"

    def test_parse_phases_default_values(self, resolver):
        """Test parsing with default priority and dependencies."""
        plan_data = {
            "phases": {
                "phase1": {"tasks": ["task1"]},  # No priority or dependencies
                "phase2": {"priority": "invalid", "dependencies": "not_list"}  # Invalid types
            }
        }
        phases = resolver._parse_phases(plan_data)

        assert len(phases) == 2
        # Should use default priority (999) for invalid values
        assert phases[0].priority == 999
        assert phases[1].priority == 999
        # Should use empty list for invalid dependencies
        assert phases[0].dependencies == []
        assert phases[1].dependencies == []

    def test_validate_dependencies_success(self, resolver, sample_plan_data):
        """Test successful dependency validation."""
        phases = resolver._parse_phases(sample_plan_data)

        # Should not raise any exceptions
        resolver._validate_dependencies(phases)

    def test_validate_dependencies_missing_phase(self, resolver):
        """Test dependency validation with missing phase."""
        phases = [
            Phase(name="phase1", data={}, priority=1, dependencies=[]),
            Phase(name="phase2", data={}, priority=2, dependencies=["missing_phase"])
        ]

        with pytest.raises(ValueError, match="depends on unknown phase"):
            resolver._validate_dependencies(phases)

    def test_validate_dependencies_circular(self, resolver):
        """Test dependency validation with circular dependencies."""
        phases = [
            Phase(name="phase1", data={}, priority=1, dependencies=["phase2"]),
            Phase(name="phase2", data={}, priority=2, dependencies=["phase1"])
        ]

        with pytest.raises(ValueError, match="Circular dependency"):
            resolver._validate_dependencies(phases)

    def test_has_cycles_detection(self, resolver):
        """Test cycle detection in dependency graph."""
        # Simple cycle: A -> B -> A
        phases = [
            Phase(name="A", data={}, priority=1, dependencies=["B"]),
            Phase(name="B", data={}, priority=2, dependencies=["A"])
        ]

        assert resolver._has_cycles(phases) is True

    def test_has_cycles_no_cycles(self, resolver):
        """Test cycle detection with no cycles."""
        # Linear: A -> B -> C
        phases = [
            Phase(name="A", data={}, priority=1, dependencies=[]),
            Phase(name="B", data={}, priority=2, dependencies=["A"]),
            Phase(name="C", data={}, priority=3, dependencies=["B"])
        ]

        assert resolver._has_cycles(phases) is False

    def test_has_cycles_complex_graph(self, resolver):
        """Test cycle detection in complex dependency graph."""
        # Complex graph with cycle: A -> B -> C -> B
        phases = [
            Phase(name="A", data={}, priority=1, dependencies=[]),
            Phase(name="B", data={}, priority=2, dependencies=["A"]),
            Phase(name="C", data={}, priority=3, dependencies=["B"]),
            Phase(name="D", data={}, priority=4, dependencies=["C"])
        ]
        # Add cycle: C depends on B
        phases[2].dependencies.append("B")

        assert resolver._has_cycles(phases) is True

    def test_resolve_execution_order_simple(self, resolver, simple_plan_data):
        """Test execution order resolution for simple plan."""
        phases = resolver._parse_phases(simple_plan_data)
        resolver._validate_dependencies(phases)

        ordered_phases = resolver._resolve_execution_order(phases)

        assert len(ordered_phases) == 2
        # Should be ordered by priority
        assert ordered_phases[0].name == "phase1"
        assert ordered_phases[1].name == "phase2"

    def test_resolve_execution_order_with_dependencies(self, resolver, sample_plan_data):
        """Test execution order resolution with dependencies."""
        phases = resolver._parse_phases(sample_plan_data)
        resolver._validate_dependencies(phases)

        ordered_phases = resolver._resolve_execution_order(phases)

        assert len(ordered_phases) == 5

        # Check that dependencies are respected
        phase_names = [phase.name for phase in ordered_phases]

        # foundation should come first (no dependencies)
        assert phase_names[0] == "foundation"

        # data_layer should come after foundation
        foundation_idx = phase_names.index("foundation")
        data_layer_idx = phase_names.index("data_layer")
        assert data_layer_idx > foundation_idx

        # api_layer should come after data_layer
        api_layer_idx = phase_names.index("api_layer")
        assert api_layer_idx > data_layer_idx

    def test_resolve_execution_order_priority_tie_breaking(self, resolver):
        """Test execution order with priority tie-breaking."""
        # Two phases with same dependencies but different priorities
        phases = [
            Phase(name="A", data={}, priority=1, dependencies=[]),
            Phase(name="B", data={}, priority=3, dependencies=["A"]),
            Phase(name="C", data={}, priority=2, dependencies=["A"])  # Lower priority than B
        ]

        ordered_phases = resolver._resolve_execution_order(phases)

        phase_names = [phase.name for phase in ordered_phases]

        # A should come first (no dependencies)
        assert phase_names[0] == "A"

        # C should come before B (lower priority number = higher priority)
        c_idx = phase_names.index("C")
        b_idx = phase_names.index("B")
        assert c_idx < b_idx

    def test_create_execution_plan_success(self, resolver, sample_plan_data):
        """Test successful execution plan creation."""
        execution_plan = resolver.create_execution_plan(sample_plan_data)

        assert isinstance(execution_plan, ExecutionPlan)
        assert execution_plan.plan_data == sample_plan_data
        assert len(execution_plan.phases) == 5

        # Check that phases are in correct order
        phase_names = [phase.name for phase in execution_plan.phases]
        assert phase_names[0] == "foundation"  # No dependencies

    def test_create_execution_plan_with_circular_dependencies(self, resolver):
        """Test execution plan creation with circular dependencies."""
        plan_data = {
            "project": {"name": "test"},
            "target_state": {"architecture": []},
            "resources": {"files": []},
            "phases": {
                "A": {"priority": 1, "dependencies": ["B"]},
                "B": {"priority": 2, "dependencies": ["A"]}
            }
        }

        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.create_execution_plan(plan_data)

    def test_get_execution_graph(self, resolver, sample_plan_data):
        """Test execution graph generation."""
        phases = resolver._parse_phases(sample_plan_data)
        graph = resolver.get_execution_graph(phases)

        assert isinstance(graph, dict)
        assert "foundation" in graph
        assert "data_layer" in graph
        assert "api_layer" in graph

        # Check that dependencies are correctly mapped
        assert "data_layer" in graph["foundation"]
        assert "api_layer" in graph["data_layer"]

    def test_get_phase_dependencies(self, resolver, sample_plan_data):
        """Test getting dependencies for a specific phase."""
        phases = resolver._parse_phases(sample_plan_data)

        # Test phase with dependencies
        deps = resolver.get_phase_dependencies("data_layer", phases)
        assert deps == ["foundation"]

        # Test phase without dependencies
        deps = resolver.get_phase_dependencies("foundation", phases)
        assert deps == []

    def test_get_dependent_phases(self, resolver, sample_plan_data):
        """Test getting phases that depend on a specific phase."""
        phases = resolver._parse_phases(sample_plan_data)

        # Test phase that others depend on
        dependents = resolver.get_dependent_phases("foundation", phases)
        assert "data_layer" in dependents

        # Test phase that no one depends on
        dependents = resolver.get_dependent_phases("testing", phases)
        assert len(dependents) == 0


class TestPhase:
    """Test the Phase dataclass."""

    def test_phase_initialization(self):
        """Test Phase initialization."""
        phase = Phase(
            name="test_phase",
            data={"priority": 1, "tasks": ["task1"]},
            priority=1,
            dependencies=["dep1", "dep2"]
        )

        assert phase.name == "test_phase"
        assert phase.data == {"priority": 1, "tasks": ["task1"]}
        assert phase.priority == 1
        assert phase.dependencies == ["dep1", "dep2"]

    def test_phase_equality(self):
        """Test Phase equality comparison."""
        phase1 = Phase(name="A", data={}, priority=1, dependencies=[])
        phase2 = Phase(name="A", data={}, priority=1, dependencies=[])
        phase3 = Phase(name="B", data={}, priority=1, dependencies=[])

        assert phase1 == phase2
        assert phase1 != phase3


class TestExecutionPlan:
    """Test the ExecutionPlan dataclass."""

    def test_execution_plan_initialization(self):
        """Test ExecutionPlan initialization."""
        phases = [
            Phase(name="A", data={}, priority=1, dependencies=[]),
            Phase(name="B", data={}, priority=2, dependencies=["A"])
        ]
        plan_data = {"project": {"name": "test"}}

        execution_plan = ExecutionPlan(phases=phases, plan_data=plan_data)

        assert execution_plan.phases == phases
        assert execution_plan.plan_data == plan_data
        assert len(execution_plan.phases) == 2
