"""
Main execution engine for development plans.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .planner import DependencyResolver, ExecutionPlan
from .snapshot import SnapshotManager


class ExecutionStatus(Enum):
    """Execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExecutionResult:
    """Result of plan execution."""

    success: bool
    status: ExecutionStatus
    executed_phases: List[str]
    failed_phase: Optional[str] = None
    error_message: Optional[str] = None
    snapshot_id: Optional[str] = None
    execution_time: Optional[float] = None
    changes_made: List[str] = None

    def __post_init__(self):
        if self.changes_made is None:
            self.changes_made = []


class PlanExecutor:
    """
    Main execution engine for development plans.

    Handles:
    - Plan parsing and validation
    - Dependency resolution
    - Phase execution
    - State snapshots
    - Rollback capabilities
    """

    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.snapshot_manager = SnapshotManager(self.project_dir)
        self.dependency_resolver = DependencyResolver()

    async def execute_plan(
        self, plan_file: str, dry_run: bool = False
    ) -> ExecutionResult:
        """
        Execute a development plan.

        Args:
            plan_file: Path to the .devplan file
            dry_run: If True, show what would be executed without making changes

        Returns:
            ExecutionResult with execution status and details
        """
        start_time = datetime.now()

        try:
            # Load and validate plan
            plan_data = await self._load_plan(plan_file)

            # Create execution plan with dependency resolution
            execution_plan = self.dependency_resolver.create_execution_plan(plan_data)

            if dry_run:
                return await self._dry_run_execution(execution_plan, start_time)

            # Create snapshot before execution
            snapshot_id = await self.snapshot_manager.create_snapshot(
                f"pre-execution-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )

            # Execute the plan
            result = await self._execute_plan(execution_plan, snapshot_id, start_time)

            return result

        except Exception as e:
            # If execution fails, attempt rollback
            if "snapshot_id" in locals():
                await self._rollback_on_failure(snapshot_id, str(e))

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                executed_phases=[],
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def rollback_to_snapshot(self, snapshot_id: str) -> ExecutionResult:
        """
        Rollback to a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot to rollback to

        Returns:
            ExecutionResult with rollback status
        """
        start_time = datetime.now()

        try:
            success = await self.snapshot_manager.restore_snapshot(snapshot_id)

            return ExecutionResult(
                success=success,
                status=(
                    ExecutionStatus.ROLLED_BACK if success else ExecutionStatus.FAILED
                ),
                executed_phases=[],
                error_message=None if success else "Failed to restore snapshot",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                executed_phases=[],
                error_message=f"Rollback failed: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """List available snapshots."""
        return await self.snapshot_manager.list_snapshots()

    async def _load_plan(self, plan_file: str) -> Dict[str, Any]:
        """Load and validate plan file."""
        plan_path = Path(plan_file)
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")

        with open(plan_path, "r") as f:
            plan_data = yaml.safe_load(f)

        # Basic validation
        required_sections = ["project", "target_state", "resources", "phases"]
        for section in required_sections:
            if section not in plan_data:
                raise ValueError(f"Missing required section: {section}")

        return plan_data

    async def _dry_run_execution(
        self, execution_plan: ExecutionPlan, start_time: datetime
    ) -> ExecutionResult:
        """Perform a dry run showing what would be executed."""
        changes = []

        for phase in execution_plan.phases:
            phase_name = phase.name
            changes.append(f"Phase: {phase_name}")

            # Simulate file creation
            if "resources" in execution_plan.plan_data:
                resources = execution_plan.plan_data["resources"]
                if "files" in resources:
                    for file_resource in resources["files"]:
                        if isinstance(file_resource, dict) and "path" in file_resource:
                            changes.append(f"Would create: {file_resource['path']}")

        return ExecutionResult(
            success=True,
            status=ExecutionStatus.COMPLETED,
            executed_phases=[phase.name for phase in execution_plan.phases],
            changes_made=changes,
            execution_time=(datetime.now() - start_time).total_seconds(),
        )

    async def _execute_plan(
        self, execution_plan: ExecutionPlan, snapshot_id: str, start_time: datetime
    ) -> ExecutionResult:
        """Execute the development plan."""
        executed_phases = []
        changes_made = []

        try:
            for phase in execution_plan.phases:
                phase_name = phase.name
                print(f"Executing phase: {phase_name}")

                # Execute phase
                phase_changes = await self._execute_phase(
                    phase, execution_plan.plan_data
                )
                changes_made.extend(phase_changes)
                executed_phases.append(phase_name)

                print(f"Completed phase: {phase_name}")

            return ExecutionResult(
                success=True,
                status=ExecutionStatus.COMPLETED,
                executed_phases=executed_phases,
                snapshot_id=snapshot_id,
                changes_made=changes_made,
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        except Exception as e:
            # Execution failed - rollback
            await self._rollback_on_failure(snapshot_id, str(e))

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                executed_phases=executed_phases,
                failed_phase=phase_name if "phase_name" in locals() else None,
                error_message=str(e),
                snapshot_id=snapshot_id,
                changes_made=changes_made,
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _execute_phase(self, phase, plan_data: Dict[str, Any]) -> List[str]:
        """Execute a single phase."""
        changes = []
        phase_name = phase.name
        phase_data = phase.data

        # Get tasks for this phase
        tasks = phase_data.get("tasks", [])

        for task in tasks:
            if isinstance(task, str):
                task_changes = await self._execute_task(task, plan_data)
                changes.extend(task_changes)

        # Handle file resources for this phase
        if "resources" in plan_data and "files" in plan_data["resources"]:
            file_changes = await self._create_files(
                plan_data["resources"]["files"], phase_name
            )
            changes.extend(file_changes)

        return changes

    async def _execute_task(self, task: str, plan_data: Dict[str, Any]) -> List[str]:
        """Execute a single task."""
        changes = []

        # Map common tasks to actions
        task_actions = {
            "setup_project_structure": self._setup_project_structure,
            "install_dependencies": self._install_dependencies,
            "create_models": self._create_models,
            "create_endpoints": self._create_endpoints,
            "implement_jwt": self._implement_jwt,
            "add_auth_middleware": self._add_auth_middleware,
            "setup_testing": self._setup_testing,
        }

        if task in task_actions:
            task_changes = await task_actions[task](plan_data)
            changes.extend(task_changes)
        else:
            # Generic task - create a placeholder file
            changes.append(f"Executed task: {task}")

        return changes

    async def _create_files(
        self, files: List[Dict[str, Any]], phase_name: str
    ) -> List[str]:
        """Create files based on plan resources."""
        changes = []

        for file_resource in files:
            if isinstance(file_resource, dict) and "path" in file_resource:
                file_path = file_resource["path"]
                file_type = file_resource.get("type", "file")
                template = file_resource.get("template", "basic")

                try:
                    # Create the file
                    created = await self._create_file(file_path, file_type, template)
                    if created:
                        changes.append(f"Created: {file_path}")
                except PermissionError as e:
                    changes.append(f"❌ Permission denied: {file_path} - {e}")
                    raise  # Re-raise to stop execution
                except OSError as e:
                    changes.append(f"❌ OS Error: {file_path} - {e}")
                    raise  # Re-raise to stop execution
                except Exception as e:
                    changes.append(f"❌ Error creating {file_path}: {e}")
                    raise  # Re-raise to stop execution

        return changes

    async def _create_file(self, file_path: str, file_type: str, template: str) -> bool:
        """Create a single file based on template."""
        try:
            full_path = self.project_dir / file_path

            # Ensure directory exists
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(
                    f"Cannot create directory {full_path.parent}: {e}"
                )
            except OSError as e:
                raise OSError(f"Failed to create directory {full_path.parent}: {e}")

            # Generate content based on template
            content = self._generate_file_content(file_path, file_type, template)

            # Write file with proper error handling
            try:
                with open(full_path, "w") as f:
                    f.write(content)
            except PermissionError as e:
                raise PermissionError(f"Cannot write to file {full_path}: {e}")
            except OSError as e:
                raise OSError(f"Failed to write file {full_path}: {e}")

            return True

        except (PermissionError, OSError) as e:
            # Re-raise with more context
            raise type(e)(f"File creation failed for {file_path}: {e}")
        except Exception as e:
            # Catch any other unexpected errors
            raise Exception(f"Unexpected error creating file {file_path}: {e}")

    def _generate_file_content(
        self, file_path: str, file_type: str, template: str
    ) -> str:
        """Generate file content based on template and type."""
        file_name = Path(file_path).name

        # Basic template content
        templates = {
            "fastapi_main": """from fastapi import FastAPI

app = FastAPI(title="API Service")

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
            "fastapi_model": """from pydantic import BaseModel
from typing import Optional

class BaseModel(BaseModel):
    class Config:
        from_attributes = True
""",
            "requirements": """fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0
""",
            # .NET Templates
            "dotnet_program": """using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "API Service", Version = "v1" });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
""",
            "dotnet_controller": """using Microsoft.AspNetCore.Mvc;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class BaseController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new { message = "Hello from API" });
    }
}
""",
            "ef_dbcontext": """using Microsoft.EntityFrameworkCore;

namespace API.Models;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    // Add DbSet properties for your entities here
    // public DbSet<YourEntity> YourEntities { get; set; }
}
""",
            "dotnet_service": """namespace API.Services;

public interface IAuthService
{
    Task<bool> ValidateUserAsync(string username, string password);
    Task<string> GenerateTokenAsync(string username);
}

public class AuthService : IAuthService
{
    public async Task<bool> ValidateUserAsync(string username, string password)
    {
        // TODO: Implement user validation logic
        return await Task.FromResult(true);
    }

    public async Task<string> GenerateTokenAsync(string username)
    {
        // TODO: Implement JWT token generation
        return await Task.FromResult("sample-token");
    }
}
""",
            "dotnet_csproj": """<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

</Project>
""",
            "basic": f"""# {file_name}
# Generated by Cursor Plans MCP
# File type: {file_type}
# Template: {template}

# TODO: Implement {file_type} functionality
""",
        }

        return templates.get(template, templates["basic"])

    async def _setup_project_structure(self, plan_data: Dict[str, Any]) -> List[str]:
        """Setup basic project structure."""
        changes = []

        # Create common directories
        directories = ["src", "tests", "docs"]
        for directory in directories:
            dir_path = self.project_dir / directory
            dir_path.mkdir(exist_ok=True)
            changes.append(f"Created directory: {directory}")

        return changes

    async def _install_dependencies(self, plan_data: Dict[str, Any]) -> List[str]:
        """Install project dependencies."""
        changes = []

        # Create requirements.txt if it doesn't exist
        requirements_file = self.project_dir / "requirements.txt"
        if not requirements_file.exists():
            content = self._generate_file_content(
                "requirements.txt", "dependencies", "requirements"
            )
            with open(requirements_file, "w") as f:
                f.write(content)
            changes.append("Created: requirements.txt")

        return changes

    async def _create_models(self, plan_data: Dict[str, Any]) -> List[str]:
        """Create data models."""
        changes = []

        # Create models directory and basic model file
        models_dir = self.project_dir / "src" / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        models_file = models_dir / "models.py"
        if not models_file.exists():
            content = self._generate_file_content(
                "src/models/models.py", "models", "fastapi_model"
            )
            with open(models_file, "w") as f:
                f.write(content)
            changes.append("Created: src/models/models.py")

        return changes

    async def _create_endpoints(self, plan_data: Dict[str, Any]) -> List[str]:
        """Create API endpoints."""
        changes = []

        # Create routes directory and basic router
        routes_dir = self.project_dir / "src" / "routes"
        routes_dir.mkdir(parents=True, exist_ok=True)

        router_file = routes_dir / "main.py"
        if not router_file.exists():
            content = """from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
"""
            with open(router_file, "w") as f:
                f.write(content)
            changes.append("Created: src/routes/main.py")

        return changes

    async def _implement_jwt(self, plan_data: Dict[str, Any]) -> List[str]:
        """Implement JWT authentication."""
        changes = []

        # Create auth directory and JWT implementation
        auth_dir = self.project_dir / "src" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        jwt_file = auth_dir / "jwt.py"
        if not jwt_file.exists():
            content = """import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "your-secret-key"  # TODO: Use environment variable
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
"""
            with open(jwt_file, "w") as f:
                f.write(content)
            changes.append("Created: src/auth/jwt.py")

        return changes

    async def _add_auth_middleware(self, plan_data: Dict[str, Any]) -> List[str]:
        """Add authentication middleware."""
        changes = []

        # Create middleware directory
        middleware_dir = self.project_dir / "src" / "middleware"
        middleware_dir.mkdir(parents=True, exist_ok=True)

        auth_middleware_file = middleware_dir / "auth.py"
        if not auth_middleware_file.exists():
            content = """from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = security):
    # TODO: Implement token verification
    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials
"""
            with open(auth_middleware_file, "w") as f:
                f.write(content)
            changes.append("Created: src/middleware/auth.py")

        return changes

    async def _setup_testing(self, plan_data: Dict[str, Any]) -> List[str]:
        """Setup testing infrastructure."""
        changes = []

        # Create test files
        test_files = [
            (
                "tests/test_main.py",
                """import pytest
from fastapi.testclient import TestClient

def test_health_check():
    # TODO: Implement health check test
    assert True
""",
            ),
            (
                "tests/conftest.py",
                """import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    # TODO: Setup test client
    pass
""",
            ),
        ]

        for file_path, content in test_files:
            full_path = self.project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if not full_path.exists():
                with open(full_path, "w") as f:
                    f.write(content)
                changes.append(f"Created: {file_path}")

        return changes

    async def _rollback_on_failure(self, snapshot_id: str, error_message: str):
        """Rollback to snapshot on execution failure."""
        print(f"Execution failed: {error_message}")
        print(f"Rolling back to snapshot: {snapshot_id}")

        try:
            await self.snapshot_manager.restore_snapshot(snapshot_id)
            print("Rollback completed successfully")
        except Exception as e:
            print(f"Rollback failed: {str(e)}")
            raise
