"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_basic_plan() -> Dict[str, Any]:
    """Sample basic development plan data."""
    return {
        "project": {
            "name": "test-project",
            "version": "1.0.0",
            "description": "Test project"
        },
        "target_state": {
            "architecture": [
                {"language": "python"},
                {"framework": "FastAPI"}
            ],
            "features": ["api_endpoints", "testing"]
        },
        "resources": {
            "files": [
                {
                    "path": "src/main.py",
                    "type": "entry_point",
                    "template": "fastapi_main"
                },
                {
                    "path": "src/models.py",
                    "type": "data_model",
                    "template": "fastapi_model"
                }
            ],
            "dependencies": ["fastapi", "uvicorn", "pydantic"]
        },
        "phases": {
            "foundation": {
                "priority": 1,
                "description": "Setup project foundation",
                "tasks": ["setup_project_structure", "install_dependencies"]
            },
            "development": {
                "priority": 2,
                "description": "Core development",
                "tasks": ["create_models", "create_endpoints"]
            }
        }
    }


@pytest.fixture
def sample_invalid_plan() -> Dict[str, Any]:
    """Sample plan with validation issues."""
    return {
        "project": {
            "name": "invalid-project",
            "version": "1.0.0"
        },
        "target_state": {
            "architecture": [{"language": "python"}]
        },
        "resources": {
            "files": [
                {
                    "path": "src/main.py",
                    "type": "entry_point",
                    "template": "unknown_template"
                },
                {
                    "path": "src/main.py",  # Duplicate path
                    "type": "duplicate",
                    "template": "another_template"
                }
            ]
        },
        "phases": {
            "foundation": {
                "priority": 1,
                "description": "Foundation phase",
                "tasks": ["setup_project"]
            },
            "development": {
                "priority": 1,  # Duplicate priority
                "description": "Development phase",
                "dependencies": ["unknown_phase"]  # Invalid dependency
            },
            "empty_phase": {
                "priority": 3
                # No tasks - should trigger warning
            }
        }
    }


@pytest.fixture
def sample_cursorrules(temp_dir):
    """Create a sample .cursorrules file."""
    rules_content = """# Test Cursor Rules

## Architecture Patterns
- Use repository pattern for all database operations
- Implement dependency injection for better testability

## Security Requirements
- Authentication is required for all API endpoints
- Use HTTPS for all communications

## FastAPI Specific
- Use Pydantic models for all request/response validation
- Generate OpenAPI documentation for all endpoints

## Testing Requirements
- Unit testing is mandatory for all business logic
- Maintain test coverage above 80%

## Naming Conventions
- Controllers should end with "Controller"
- Models should end with "Model"
"""

    rules_file = temp_dir / ".cursorrules"
    rules_file.write_text(rules_content)
    return rules_file


@pytest.fixture
def sample_context_file(temp_dir):
    """Create a sample context file."""
    context_content = """# Test context file
src/main.py
src/models.py
requirements.txt
README.md
"""

    context_file = temp_dir / "context.txt"
    context_file.write_text(context_content)
    return context_file


@pytest.fixture
def sample_plan_file(temp_dir, sample_basic_plan):
    """Create a sample plan file on disk."""
    import yaml

    plan_file = temp_dir / "test.devplan"
    with open(plan_file, 'w') as f:
        yaml.dump(sample_basic_plan, f)

    return plan_file


@pytest.fixture
def mock_existing_files(temp_dir):
    """Create some existing files to simulate a project structure."""
    files_to_create = [
        "src/main.py",
        "src/models.py",
        "requirements.txt",
        "README.md",
        ".gitignore"
    ]

    created_files = []
    for file_path in files_to_create:
        full_path = temp_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(f"# {file_path}\n# Sample content")
        created_files.append(full_path)

    return created_files
