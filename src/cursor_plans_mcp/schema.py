"""Schema validation for development plan files."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
import yaml


class Project(BaseModel):
    """Project metadata."""
    name: str = Field(..., description="Project name")
    version: str = Field(..., description="Project version")
    description: str = Field(..., description="Project description")


class Architecture(BaseModel):
    """Target architecture specification."""
    language: Optional[str] = None
    framework: Optional[str] = None
    type: Optional[str] = None
    middleware: Optional[str] = None
    focus: Optional[str] = None
    api_type: Optional[str] = None
    database: Optional[str] = None
    auth: Optional[str] = None


class TargetState(BaseModel):
    """Target state specification."""
    architecture: List[Architecture] = Field(..., description="Architecture components")
    features: List[str] = Field(..., description="Target features")


class FileResource(BaseModel):
    """File resource specification."""
    path: str = Field(..., description="File path")
    type: str = Field(..., description="File type")
    template: str = Field(..., description="Template to use")


class Dependency(BaseModel):
    """Dependency specification."""
    name: str = Field(..., description="Dependency name")
    version: Optional[str] = None


class Resources(BaseModel):
    """Resources specification."""
    files: List[FileResource] = Field(..., description="Files to create")
    dependencies: List[Union[str, Dependency]] = Field(..., description="Package dependencies")


class Phase(BaseModel):
    """Development phase."""
    priority: int = Field(..., description="Phase priority")
    description: Optional[str] = None
    dependencies: Optional[List[str]] = Field(default_factory=list)
    tasks: List[str] = Field(..., description="Phase tasks")


class Validation(BaseModel):
    """Validation configuration."""
    pre_apply: List[str] = Field(..., description="Pre-apply validations")
    post_apply: Optional[List[str]] = Field(default_factory=list)


class Constraint(BaseModel):
    """Project constraints."""
    name: str = Field(..., description="Constraint name")
    description: str = Field(..., description="Constraint description")


class DevelopmentPlan(BaseModel):
    """Complete development plan schema."""
    schema_version: str = Field(default="1.0", description="Schema version")
    project: Project = Field(..., description="Project metadata")
    target_state: TargetState = Field(..., description="Target state")
    resources: Resources = Field(..., description="Resources")
    phases: Dict[str, Phase] = Field(..., description="Development phases")
    validation: Validation = Field(..., description="Validation rules")
    constraints: Optional[List[Constraint]] = Field(default_factory=list)

    @validator('phases')
    def validate_phases(cls, v):
        """Ensure required phases exist."""
        required_phases = ['testing']
        missing_phases = [phase for phase in required_phases if phase not in v]
        if missing_phases:
            raise ValueError(f"Missing required phases: {missing_phases}")
        return v

    @validator('resources')
    def validate_resources(cls, v):
        """Validate resource templates."""
                # Actually implemented templates
        implemented_templates = [
            'fastapi_main', 'fastapi_model', 'requirements', 'basic',
            'dotnet_program', 'dotnet_controller', 'ef_dbcontext', 'dotnet_service', 'dotnet_csproj'
        ]

        # Referenced templates (not yet implemented but allowed)
        referenced_templates = [
            'basic_readme', 'python_main', 'sqlalchemy_models',
            'jwt_auth', 'fastapi_requirements', 'vue_main',
            'vue_app', 'vue_router', 'pinia_store', 'vue_component', 'vue_package_json'
        ]

        # All allowed templates
        allowed_templates = implemented_templates + referenced_templates

        for file in v.files:
            if not file.template.startswith('custom_') and file.template not in allowed_templates:
                raise ValueError(f"Unknown template '{file.template}'. Use 'custom_{file.template}' for custom templates")
        return v


def validate_plan_content(content: str) -> tuple[bool, str, Optional[DevelopmentPlan]]:
    """Validate plan content against schema.

    Returns:
        (is_valid, error_message, parsed_plan)
    """
    try:
        # Parse YAML
        data = yaml.safe_load(content)
        if not data:
            return False, "Empty plan content", None

        # Validate against schema
        plan = DevelopmentPlan(**data)
        return True, "", plan

    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {str(e)}", None
    except Exception as e:
        return False, f"Schema validation error: {str(e)}", None


def create_validated_plan_content(plan_data: Dict[str, Any]) -> str:
    """Create plan content with schema validation."""
    try:
        # Add schema version if not present
        if 'schema_version' not in plan_data:
            plan_data['schema_version'] = "1.0"

        # Validate and create plan
        plan = DevelopmentPlan(**plan_data)

        # Convert back to YAML
        return yaml.dump(plan.dict(), default_flow_style=False, sort_keys=False)

    except Exception as e:
        raise ValueError(f"Failed to create validated plan: {str(e)}")
