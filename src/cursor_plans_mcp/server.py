"""Cursor Plans MCP Server - Development Planning DSL for Cursor."""

from typing import Any
import json
import os
from pathlib import Path

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server

from .validation import ValidationEngine
from .execution import PlanExecutor
from .schema import validate_plan_content, create_validated_plan_content

# Global state to store project context
_project_context: dict[str, Any] = {}


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """Main entry point for the Cursor Plans MCP server."""
    app = Server("cursor-plans-mcp")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List all available development planning tools."""
        return [
            types.Tool(
                name="dev_plan_init",
                title="Initialize Development Planning",
                description="Initialize development planning for a project with proper directory setup",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_directory": {
                            "type": "string",
                            "description": "Project directory to initialize (default: current working directory)",
                            "default": ".",
                        },
                        "reset": {
                            "type": "boolean",
                            "description": "Reset/start over: purge all .devplan files and reset context",
                            "default": False,
                        },
                    },
                },
            ),
            types.Tool(
                name="dev_plan_create",
                title="Create Development Plan",
                description="Create a new .devplan file with basic structure",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the development plan",
                        },
                        "template": {
                            "type": "string",
                            "description": "Template to use (basic, fastapi, dotnet, vuejs)",
                            "default": "basic",
                        },
                        "context": {
                            "type": "string",
                            "description": "Context identifier (story-123, feature-auth, etc.) - creates context-{name}.txt",
                            "default": "",
                        },
                        "project_directory": {
                            "type": "string",
                            "description": "Project directory to create plan in (default: current working directory)",
                            "default": ".",
                        },
                    },
                },
            ),
            types.Tool(
                name="dev_plan_show",
                title="Show Development Plan",
                description="Display the current development plan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_file": {
                            "type": "string",
                            "description": "Path to .devplan file (default: ./.cursorplans/project.devplan)",
                            "default": "./project.devplan",
                        },
                        "project_directory": {
                            "type": "string",
                            "description": "Project directory to look for plan in (default: current working directory)",
                            "default": ".",
                        }
                    },
                },
            ),
            types.Tool(
                name="dev_state_show",
                title="Show Current State",
                description="Show the current state of the codebase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to analyze (default: current directory)",
                            "default": ".",
                        }
                    },
                },
            ),
            types.Tool(
                name="dev_state_diff",
                title="Show State Differences",
                description="Compare current state with target state from plan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_file": {
                            "type": "string",
                            "description": "Path to .devplan file (default: ./.cursorplans/project.devplan)",
                            "default": "./project.devplan",
                        }
                    },
                },
            ),
            types.Tool(
                name="dev_context_list",
                title="List Project Context",
                description="List files and folders with context for existing codebases",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to analyze (default: current directory)",
                            "default": ".",
                        },
                        "include_content": {
                            "type": "boolean",
                            "description": "Include file content previews",
                            "default": False,
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum directory depth to analyze",
                            "default": 3,
                        },

                    },
                },
            ),
            types.Tool(
                name="dev_context_add",
                title="Add Files to Context",
                description="Add specific files or folders to development context for planning",
                inputSchema={
                    "type": "object",
                    "required": ["files"],
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of files or folders to add to context",
                        },
                        "context": {
                            "type": "string",
                            "description": "Context name (story-123, feature-auth, etc.)",
                            "default": "main",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of why these files are relevant",
                            "default": "",
                        },
                    },
                },
            ),
            types.Tool(
                name="dev_plan_validate",
                title="Validate Development Plan",
                description="Validate development plan syntax, logic, and compliance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_file": {
                            "type": "string",
                            "description": "Path to .devplan file (default: ./.cursorplans/project.devplan)",
                            "default": "./project.devplan",
                        },
                        "strict_mode": {
                            "type": "boolean",
                            "description": "If true, warnings are treated as errors",
                            "default": False,
                        },
                        "check_cursor_rules": {
                            "type": "boolean",
                            "description": "If true, validate against .cursorrules file",
                            "default": True,
                        },
                    },
                },
            ),
            types.Tool(
                name="dev_apply_plan",
                title="Apply Development Plan",
                description="Execute a development plan to create/modify files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_file": {
                            "type": "string",
                            "description": "Path to .devplan file (default: ./.cursorplans/project.devplan)",
                            "default": "./project.devplan",
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Show what would be executed without making changes",
                            "default": False,
                        },
                    },
                },
            ),
            types.Tool(
                name="dev_rollback",
                title="Rollback Changes",
                description="Rollback to a previous state snapshot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshot_id": {
                            "type": "string",
                            "description": "ID of the snapshot to rollback to",
                        },
                    },
                },
            ),
            types.Tool(
                name="dev_snapshots",
                title="List Snapshots",
                description="List available state snapshots",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),

        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Handle tool calls for development planning operations."""

        if name == "dev_plan_init":
            return await init_dev_planning(arguments)
        elif name == "dev_plan_create":
            return await create_dev_plan(arguments)
        elif name == "dev_plan_show":
            return await show_dev_plan(arguments)
        elif name == "dev_state_show":
            return await show_current_state(arguments)
        elif name == "dev_state_diff":
            return await show_state_diff(arguments)
        elif name == "dev_context_list":
            return await list_project_context(arguments)
        elif name == "dev_context_add":
            return await add_context_files(arguments)
        elif name == "dev_plan_validate":
            return await validate_dev_plan(arguments)
        elif name == "dev_apply_plan":
            return await apply_dev_plan(arguments)
        elif name == "dev_rollback":
            return await rollback_to_snapshot(arguments)
        elif name == "dev_snapshots":
            return await list_snapshots(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    # Transport setup
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:  # type: ignore[reportPrivateUsage]
                await app.run(streams[0], streams[1], app.create_initialization_options())
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="127.0.0.1", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        anyio.run(arun)

    return 0


async def init_dev_planning(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Initialize development planning for a project with proper directory setup."""
    import os
    import shutil
    from pathlib import Path
    global _project_context

    project_directory = arguments.get("project_directory", ".")
    reset = arguments.get("reset", False)

    # Resolve the project directory
    if project_directory == "." or not project_directory:
        if "PWD" in os.environ:
            project_directory = os.environ["PWD"]
        else:
            project_directory = os.getcwd()

    project_path = Path(project_directory).resolve()

    # Handle reset functionality
    if reset:
        cursorplans_dir = project_path / ".cursorplans"
        context_files = []

        # Collect all files to be removed
        if cursorplans_dir.exists():
            for file in cursorplans_dir.glob("*.devplan"):
                context_files.append(str(file))
            for file in cursorplans_dir.glob("context*.txt"):
                context_files.append(str(file))
            for file in cursorplans_dir.glob("*.json"):
                context_files.append(str(file))

        # Remove .cursorplans directory and all contents
        if cursorplans_dir.exists():
            shutil.rmtree(cursorplans_dir)

        # Reset global context
        _project_context = {}

        # Create fresh .cursorplans directory
        cursorplans_dir.mkdir(exist_ok=True)

        reset_output = f"""🔄 **Development Planning Reset Complete**

📁 **Project Directory**: `{project_path}`
🗑️ **Purged Files**: {len(context_files)} files
📂 **Fresh Plans Directory**: `{cursorplans_dir}`

✅ **Ready to start over!**

**Purged Files:**
{chr(10).join(f"  - {f}" for f in context_files) if context_files else "  - No files found"}

**Next Steps:**
1. Create a new plan:
   ```bash
   dev_plan_create name="my-feature" template="basic"
   ```

2. Add context files:
   ```bash
   dev_context_add files["path/to/relevant/files"]
   ```
"""
        return [
            types.TextContent(
                type="text",
                text=reset_output
            )
        ]

    # Store project context in global state
    _project_context = {
        "project_directory": str(project_path),
        "project_name": project_path.name,
        "cursorplans_dir": str(project_path / ".cursorplans")
    }

    # Create .cursorplans directory
    cursorplans_dir = project_path / ".cursorplans"
    try:
        cursorplans_dir.mkdir(exist_ok=True)
    except FileNotFoundError:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Error**: Project directory does not exist: {project_directory}"
            )
        ]

    # Detect project type and provide initialization output
    project_type = "unknown"
    project_name = project_path.name

    # Check for common project indicators
    if (project_path / "package.json").exists():
        project_type = "Node.js"
    elif (project_path / "pyproject.toml").exists():
        project_type = "Python"
    elif (project_path / "Cargo.toml").exists():
        project_type = "Rust"
    elif (project_path / "go.mod").exists():
        project_type = "Go"
    elif (project_path / ".csproj").exists() or (project_path / "*.sln").exists():
        project_type = ".NET"
    elif (project_path / "pom.xml").exists():
        project_type = "Java/Maven"
    elif (project_path / "build.gradle").exists():
        project_type = "Java/Gradle"

    # Generate initialization output with clear project_directory
    init_output = f"""🚀 **Development Planning Initialized**

📁 **Project Directory**: `{project_path}`
🏷️ **Project Name**: `{project_name}`
🔧 **Project Type**: `{project_type}`
📂 **Plans Directory**: `{cursorplans_dir}`

✅ **Ready to create development plans!**

**🎉 Project context stored!** You can now use simplified commands without repeating the project directory.

**Next Steps:**
1. Create your first plan:
   ```bash
   dev_plan_create name="my-feature" template="basic"
   ```

2. For {project_type} projects, consider these templates:
   - `basic` - Simple project structure
   - `from-existing` - Analyze existing codebase
   - `fastapi` - Python FastAPI projects
   - `dotnet` - .NET projects
   - `vuejs` - Vue.js frontend projects

3. Validate your plan:
   ```bash
   dev_plan_validate plan_file="my-feature.devplan"
   ```

**💡 Tip**: The project directory is now remembered from initialization. You only need to specify it again if you want to work with a different project.
"""

    return [
        types.TextContent(
            type="text",
            text=init_output
        )
    ]


async def create_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Create a new development plan file."""
    global _project_context

    name = arguments["name"]
    template = arguments.get("template", "basic")
    context = arguments.get("context", "")
    project_directory = arguments.get("project_directory", ".")

    # Use stored project context if available and no explicit project_directory provided
    if (project_directory == "." or not project_directory) and _project_context:
        project_directory = _project_context["project_directory"]

    # If project_directory is "." or not provided, try to use environment or fallback
    if project_directory == "." or not project_directory:
        # Try to get the project directory from environment variables
        import os
        # PWD is often set by the shell
        if "PWD" in os.environ:
            project_directory = os.environ["PWD"]
        else:
            # Fallback to current working directory
            project_directory = os.getcwd()

    # Ensure we have a valid project directory
    if not project_directory or project_directory == "/":
        # Last resort: use home directory as fallback
        import os
        project_directory = os.path.expanduser("~")

    # Simple context file resolution
    context_files = []
    project_path = Path(project_directory).resolve()

    # Simple context file resolution

    if context:
        context_file = project_path / f"context-{context}.txt"
        if context_file.exists():
            context_files = await load_context_file(str(context_file))
    elif (project_path / "context.txt").exists():
        context_files = await load_context_file(str(project_path / "context.txt"))

    # Simple context file resolution - no automatic detection

    # Template structures
    if template == "basic":
        plan_content = f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "A new software project"

target_state:
  architecture:
    - language: "python"
    - framework: "TBD"

  features:
    - basic_structure
    - documentation

resources:
  files:
    - path: "README.md"
      type: "documentation"
      template: "basic_readme"
    - path: "src/main.py"
      type: "entry_point"
      template: "python_main"

  dependencies:
    - "requests"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - create_basic_files

  development:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - implement_core_features
      - add_tests

  documentation:
    priority: 3
    dependencies: ["development"]
    tasks:
      - write_documentation
      - create_examples

  testing:
    priority: 4
    dependencies: ["development"]
    tasks:
      - unit_tests
      - integration_tests

validation:
  pre_apply:
    - syntax_check
    - dependency_check

  post_apply:
    - unit_test_validation
"""
    elif template == "fastapi":
        plan_content = f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "FastAPI web service"

target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
    - database: "PostgreSQL"
    - auth: "JWT"

  features:
    - api_endpoints
    - database_models
    - authentication
    - testing

resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "fastapi_main"
    - path: "src/models.py"
      type: "data_model"
      template: "sqlalchemy_models"
    - path: "src/auth.py"
      type: "authentication"
      template: "jwt_auth"
    - path: "requirements.txt"
      type: "dependencies"
      template: "fastapi_requirements"

  dependencies:
    - "fastapi"
    - "sqlalchemy"
    - "pyjwt"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - install_dependencies

  data_layer:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - create_models
      - setup_database

  api_layer:
    priority: 3
    dependencies: ["data_layer"]
    tasks:
      - create_endpoints
      - add_middleware

  security:
    priority: 4
    dependencies: ["api_layer"]
    tasks:
      - implement_authentication
      - add_authorization

  testing:
    priority: 5
    dependencies: ["security"]
    tasks:
      - unit_tests
      - integration_tests

validation:
  pre_apply:
    - syntax_check
    - security_scan
    - dependency_check
"""
    elif template == "dotnet":
        plan_content = f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "1.0.0"
  description: ".NET Web API service"

target_state:
  architecture:
    - language: "C#"
    - framework: ".NET 8"
    - api_type: "Web API"
    - database: "SQL Server"
    - auth: "JWT Bearer"

  features:
    - web_api_controllers
    - entity_framework_models
    - authentication_authorization
    - swagger_documentation
    - unit_testing

resources:
  files:
    - path: "Program.cs"
      type: "entry_point"
      template: "dotnet_program"
    - path: "Controllers/BaseController.cs"
      type: "api_controller"
      template: "dotnet_controller"
    - path: "Models/AppDbContext.cs"
      type: "data_context"
      template: "ef_dbcontext"
    - path: "Services/IAuthService.cs"
      type: "service_interface"
      template: "dotnet_service"
    - path: "{name}.csproj"
      type: "project_file"
      template: "dotnet_csproj"

  dependencies:
    - name: "Microsoft.AspNetCore.Authentication.JwtBearer"
      version: "8.0.0"
    - name: "Microsoft.EntityFrameworkCore.SqlServer"
      version: "8.0.0"
    - name: "Swashbuckle.AspNetCore"
      version: "6.5.0"

phases:
  foundation:
    priority: 1
    tasks:
      - create_project_structure
      - setup_dependency_injection
      - configure_swagger

  data_layer:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - setup_entity_framework
      - create_models
      - configure_database

  api_layer:
    priority: 3
    dependencies: ["data_layer"]
    tasks:
      - create_controllers
      - implement_crud_operations
      - add_validation

  security:
    priority: 4
    dependencies: ["api_layer"]
    tasks:
      - implement_jwt_authentication
      - add_authorization_policies
      - secure_endpoints

  testing:
    priority: 5
    dependencies: ["security"]
    tasks:
      - unit_tests
      - integration_tests
      - api_tests

validation:
  pre_apply:
    - dotnet_build_check
    - security_scan
    - code_analysis
"""
    elif template == "vuejs":
        plan_content = f"""# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "Vue.js frontend application"

target_state:
  architecture:
    - language: "TypeScript"
    - framework: "Vue 3"
    - build_tool: "Vite"
    - state_management: "Pinia"
    - ui_framework: "Vuetify"
    - testing: "Vitest + Vue Test Utils"

  features:
    - component_library
    - routing
    - state_management
    - api_integration
    - responsive_design
    - unit_testing

resources:
  files:
    - path: "src/main.ts"
      type: "entry_point"
      template: "vue_main"
    - path: "src/App.vue"
      type: "root_component"
      template: "vue_app"
    - path: "src/router/index.ts"
      type: "router_config"
      template: "vue_router"
    - path: "src/stores/main.ts"
      type: "state_store"
      template: "pinia_store"
    - path: "src/components/HelloWorld.vue"
      type: "component"
      template: "vue_component"
    - path: "package.json"
      type: "dependencies"
      template: "vue_package_json"

  dependencies:
    - name: "vue"
      version: "^3.4.0"
    - name: "vue-router"
      version: "^4.2.0"
    - name: "pinia"
      version: "^2.1.0"
    - name: "vuetify"
      version: "^3.5.0"
    - name: "axios"
      version: "^1.6.0"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_vite_project
      - configure_typescript
      - setup_vuetify

  routing:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - configure_vue_router
      - create_route_components
      - implement_navigation

  state_management:
    priority: 3
    dependencies: ["routing"]
    tasks:
      - setup_pinia_stores
      - implement_state_logic
      - connect_components_to_store

  components:
    priority: 4
    dependencies: ["state_management"]
    tasks:
      - create_reusable_components
      - implement_forms
      - add_data_tables

  api_integration:
    priority: 5
    dependencies: ["components"]
    tasks:
      - setup_axios_client
      - implement_api_services
      - handle_authentication

  testing:
    priority: 6
    dependencies: ["api_integration"]
    tasks:
      - unit_tests
      - component_tests
      - e2e_tests

validation:
  pre_apply:
    - typescript_check
    - vue_template_validation
    - dependency_audit
"""
    else:
        plan_content = f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "Custom project"

target_state:
  architecture:
    - language: "TBD"
    - framework: "TBD"

  features:
    - custom_features

resources:
  files:
    - path: "README.md"
      type: "documentation"
      template: "basic_readme"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - create_basic_files

  development:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - implement_core_features
      - add_tests

validation:
  pre_apply:
    - syntax_check
    - dependency_check

  post_apply:
    - unit_test_validation
"""

        # Add context information to plan if provided
    if context_files:
        context_section = f"""
# Context Files
# These files were specified as relevant context for this plan:
{chr(10).join(f"# - {f}" for f in context_files)}

"""
        plan_content = context_section + plan_content

    # Validate plan content before writing
    is_valid, error_msg, _ = validate_plan_content(plan_content)
    if not is_valid:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Schema validation failed: {error_msg}\n\nPlan content:\n```yaml\n{plan_content}\n```"
            )
        ]

    # Write the plan file
    # Create .cursorplans directory if it doesn't exist
    cursorplans_dir = project_path / ".cursorplans"

    try:
        cursorplans_dir.mkdir(exist_ok=True)
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error creating .cursorplans directory: {str(e)}\n\nPath: {cursorplans_dir}\n\nThis might be a permissions issue or the path might be invalid."
            )
        ]

    plan_file = cursorplans_dir / f"{name}.devplan"

    try:
        with open(plan_file, "w") as f:
            f.write(plan_content)

        context_info = ""
        if context_files:
            context_info = f"\n📁 Context files included: {len(context_files)} files"

        return [
            types.TextContent(
                type="text",
                text=f"✅ Created development plan: {plan_file}\n\nTemplate: {template}{context_info}\n\nNext steps:\n1. Review and customize the plan\n2. Run `dev_state_diff` to see what changes are needed\n3. Use `dev_apply_plan` to execute the plan"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error creating plan file: {str(e)}"
            )
        ]


async def show_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Show the current development plan."""
    global _project_context

    plan_file = arguments.get("plan_file", "./project.devplan")
    project_directory = arguments.get("project_directory", ".")

    # Use stored project context if available and no explicit project_directory provided
    if (project_directory == "." or not project_directory) and _project_context:
        project_directory = _project_context["project_directory"]

    try:
        project_path = Path(project_directory).resolve()

        # If no specific path is provided, look in .cursorplans directory first
        if plan_file == "./project.devplan":
            cursorplans_path = project_path / ".cursorplans" / "project.devplan"
            if cursorplans_path.exists():
                plan_file = str(cursorplans_path)

        if not os.path.exists(plan_file):
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Plan file not found: {plan_file}\n\nCreate one with `dev_plan_create`"
                )
            ]

        with open(plan_file, "r") as f:
            content = f.read()

        return [
            types.TextContent(
                type="text",
                text=f"📋 Development Plan: {plan_file}\n\n```yaml\n{content}\n```"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error reading plan file: {str(e)}"
            )
        ]


async def show_current_state(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Show the current state of the codebase."""
    directory = arguments.get("directory", ".")

    try:
        current_dir = Path(directory)
        if not current_dir.exists():
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Directory not found: {directory}"
                )
            ]

        # Analyze current state with strict project boundary enforcement
        files = []
        max_files = 1000  # Limit total files to prevent excessive scanning

        # Get the absolute path of the current directory
        current_abs = current_dir.resolve()

        # Use a much simpler approach - only scan the immediate directory and known project subdirectories
        try:
            # Get immediate files only
            for item in current_dir.iterdir():
                if len(files) >= max_files:
                    break

                if item.is_file() and not str(item).startswith("."):
                    try:
                        relative_path = str(item.relative_to(current_dir))
                        files.append(relative_path)
                    except (PermissionError, OSError, ValueError):
                        continue

            # Only scan specific known project directories
            project_dirs = ["cursor-plans", "src", "tests", "docs", "examples"]
            for dir_name in project_dirs:
                if len(files) >= max_files:
                    break

                project_dir = current_dir / dir_name
                if project_dir.exists() and project_dir.is_dir():
                    try:
                        for item in project_dir.rglob("*"):
                            if len(files) >= max_files:
                                break

                            if item.is_file() and not str(item).startswith("."):
                                try:
                                    relative_path = str(item.relative_to(current_dir))
                                    # Skip build and cache directories
                                    if any(skip_dir in relative_path for skip_dir in [
                                        "node_modules/", ".git/", "__pycache__/",
                                        ".pytest_cache/", ".DS_Store", ".Trash"
                                    ]):
                                        continue
                                    files.append(relative_path)
                                except (PermissionError, OSError, ValueError):
                                    continue
                    except (PermissionError, OSError):
                        continue

        except (PermissionError, OSError) as e:
            # If we can't scan the directory at all, return a limited analysis
            return [
                types.TextContent(
                    type="text",
                    text=f"⚠️ Limited analysis due to permission restrictions: {str(e)}\n\n"
                         f"🔍 Current Codebase State for: {directory}\n"
                         f"📁 **Accessible Files**: Limited\n"
                         f"💡 **Suggestion**: Run from project directory or check permissions"
                )
            ]

        # Check for common project files
        project_files = {
            "README.md": "📖 Documentation",
            "requirements.txt": "📦 Python dependencies",
            "package.json": "📦 Node.js dependencies",
            "pyproject.toml": "🔧 Python project config",
            "Dockerfile": "🐳 Container config",
            ".gitignore": "🚫 Git ignore rules",
        }

        found_files = []
        missing_files = []

        for file, desc in project_files.items():
            if file in files:
                found_files.append(f"✅ {file} - {desc}")
            else:
                missing_files.append(f"❌ {file} - {desc}")

        state_report = f"""🔍 Current Codebase State for: {directory}

📁 **Total Files**: {len(files)}

🔍 **Key Project Files**:
{chr(10).join(found_files)}

❓ **Missing Common Files**:
{chr(10).join(missing_files)}

📂 **All Files**:
{chr(10).join(f"  - {f}" for f in sorted(files)[:20])}
{"..." if len(files) > 20 else ""}
"""

        return [
            types.TextContent(
                type="text",
                text=state_report
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error analyzing directory: {str(e)}"
            )
        ]


async def show_state_diff(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Compare current state with target state from plan."""
    plan_file = arguments.get("plan_file", "./project.devplan")

    try:
        # If no specific path is provided, look in .cursorplans directory first
        if plan_file == "./project.devplan":
            cursorplans_path = Path(".cursorplans") / "project.devplan"
            if cursorplans_path.exists():
                plan_file = str(cursorplans_path)

        if not os.path.exists(plan_file):
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Plan file not found: {plan_file}\n\nCreate one with `dev_plan_create`"
                )
            ]

        # Read the actual plan content
        with open(plan_file, "r") as f:
            plan_content = f.read()

        # Parse YAML content to extract file information
        import yaml
        try:
            plan_data = yaml.safe_load(plan_content)
        except yaml.YAMLError as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error parsing plan YAML: {str(e)}\n\nPlan file: {plan_file}"
                )
            ]

        # Extract files from the plan structure
        planned_files = set()
        if plan_data and 'resources' in plan_data and 'files' in plan_data['resources']:
            for file_info in plan_data['resources']['files']:
                if isinstance(file_info, dict) and 'path' in file_info:
                    planned_files.add(file_info['path'])

        # Also check for any other file references in the plan
        lines = plan_content.split("\n")
        for line in lines:
            if "path:" in line and ":" in line:
                # Extract path value more carefully
                parts = line.split("path:", 1)
                if len(parts) > 1:
                    path = parts[1].strip().strip('"').strip("'")
                    if path and not path.startswith("#"):
                        planned_files.add(path)

        # Get current files in the project (limited scope)
        current_files = set()
        current_dir = Path(".")

        # Get immediate files only
        for item in current_dir.iterdir():
            if item.is_file() and not item.name.startswith("."):
                try:
                    relative_path = str(item.relative_to(current_dir))
                    current_files.add(relative_path)
                except ValueError:
                    pass

        # Only scan specific known project directories
        project_dirs = ["cursor-plans", "src", "tests", "docs", "examples"]
        for dir_name in project_dirs:
            project_dir = current_dir / dir_name
            if project_dir.exists() and project_dir.is_dir():
                try:
                    for item in project_dir.rglob("*"):
                        if item.is_file() and not item.name.startswith("."):
                            try:
                                relative_path = str(item.relative_to(current_dir))
                                current_files.add(relative_path)
                            except ValueError:
                                pass
                except (PermissionError, OSError):
                    pass

        # Calculate differences
        files_to_create = planned_files - current_files
        files_existing = planned_files & current_files

        # Create detailed diff report
        diff_report = f"""🔄 State Difference Analysis

📋 **Plan File**: {plan_file}
📊 **Plan Content Length**: {len(plan_content)} characters

📋 **Plan Summary**:
  - Total planned files: {len(planned_files)}
  - Files to create: {len(files_to_create)}
  - Files already exist: {len(files_existing)}

➕ **Files to Create**:
{chr(10).join(f"  + {f}" for f in sorted(files_to_create)) if files_to_create else "  (none)"}

✅ **Files Already Exist**:
{chr(10).join(f"  ✓ {f}" for f in sorted(files_existing)) if files_existing else "  (none)"}

🔍 **Debug Information**:
  - Current directory files: {len(current_files)}
  - Plan file exists: ✅
  - Plan content parsed: ✅

🚀 **Next Steps**:
  1. Review the planned changes above
  2. Use `dev_apply_plan` to create missing files
  3. Customize templates and configurations as needed
"""

        return [
            types.TextContent(
                type="text",
                text=diff_report
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error analyzing state diff: {str(e)}\n\nPlan file: {plan_file}"
            )
        ]


async def load_context_file(context_file_path: str) -> list[str]:
    """Load context files from a text file."""
    context_files = []
    try:
        with open(context_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    context_files.append(line)
    except FileNotFoundError:
        pass
    return context_files


async def add_context_files(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Add specific files to development context."""
    files = arguments["files"]
    context = arguments.get("context", "main")
    description = arguments.get("description", "")

    context_file = f"context-{context}.txt" if context != "main" else "context.txt"

    try:
        # Load existing context
        existing_context = []
        if os.path.exists(context_file):
            existing_context = await load_context_file(context_file)

        # Add new files (avoid duplicates)
        new_files = []
        for file_path in files:
            if file_path not in existing_context:
                new_files.append(file_path)
                existing_context.append(file_path)

        # Write updated context file
        with open(context_file, 'w') as f:
            if description:
                f.write(f"# {description}\n")
            f.write("# Context files for development planning\n")
            f.write("# Add files and folders that are relevant to your development plans\n\n")
            for file_path in existing_context:
                f.write(f"{file_path}\n")

        # Verify files exist
        existing_files = []
        missing_files = []
        for file_path in files:
            if os.path.exists(file_path):
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)

        result_text = f"✅ Updated context file: {context_file}\n\n"

        if new_files:
            result_text += f"➕ **Added {len(new_files)} new files:**\n"
            result_text += "\n".join(f"  + {f}" for f in new_files) + "\n\n"

        if existing_files:
            result_text += f"✅ **Verified {len(existing_files)} files exist:**\n"
            result_text += "\n".join(f"  ✓ {f}" for f in existing_files) + "\n\n"

        if missing_files:
            result_text += f"⚠️ **Warning - {len(missing_files)} files not found:**\n"
            result_text += "\n".join(f"  ❌ {f}" for f in missing_files) + "\n\n"

        result_text += f"📋 **Total context files**: {len(existing_context)}\n\n"
        result_text += "💡 **Usage:**\n"
        result_text += f"- Use `dev_plan_create name=\"project\" context=\"{context}\"` to create plans with this context\n"
        result_text += f"- Use `@{context_file}` to reference this context in Cursor conversations"

        return [
            types.TextContent(
                type="text",
                text=result_text
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error updating context file: {str(e)}"
            )
        ]


async def detect_existing_codebase(directory: str, context_files: list[str] = None, suggest_name: bool = True) -> dict[str, Any]:
    """Detect the framework and structure of an existing codebase."""
    current_dir = Path(directory)
    detected_info = {
        "framework": None,
        "language": None,
        "suggested_name": None,
        "key_files": [],
        "structure": "unknown"
    }

    # If suggest_name is False, we won't set any suggested_name
    if not suggest_name:
        detected_info["suggested_name"] = None

    try:
        # If context files are provided, focus on those first
        if context_files:
            context_paths = []
            for context_file in context_files:
                context_path = current_dir / context_file
                if context_path.exists():
                    if context_path.is_file():
                        context_paths.append(context_path)
                    else:
                        # If it's a directory, add all files in it (limited scope)
                        try:
                            for item in context_path.rglob("*"):
                                if item.is_file():
                                    context_paths.append(item)
                        except (PermissionError, OSError):
                            pass
            files = context_paths
        else:
            # Check for various framework indicators (limited scope)
            files = []
            # Get immediate files only
            for item in current_dir.iterdir():
                if item.is_file():
                    files.append(item)

            # Only scan specific known project directories
            project_dirs = ["cursor-plans", "src", "tests", "docs", "examples"]
            for dir_name in project_dirs:
                project_dir = current_dir / dir_name
                if project_dir.exists() and project_dir.is_dir():
                    try:
                        for item in project_dir.rglob("*"):
                            if item.is_file():
                                files.append(item)
                    except (PermissionError, OSError):
                        pass

        file_names = [f.name for f in files if f.is_file()]

        # .NET detection
        if any(f.endswith('.csproj') or f.endswith('.sln') for f in file_names):
            detected_info["framework"] = "dotnet"
            detected_info["language"] = "C#"
            detected_info["structure"] = "dotnet_project"

            # Try to get project name from .csproj
            if suggest_name:
                for f in files:
                    if f.name.endswith('.csproj'):
                        detected_info["suggested_name"] = f.stem
                        break
            else:
                # Ensure suggested_name stays None when suggest_name is False
                detected_info["suggested_name"] = None

        # Vue.js detection
        elif "package.json" in file_names:
            try:
                package_json_path = current_dir / "package.json"
                if package_json_path.exists():
                    with open(package_json_path, 'r') as f:
                        package_data = json.loads(f.read())
                        deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}

                        if 'vue' in deps:
                            detected_info["framework"] = "vuejs"
                            detected_info["language"] = "JavaScript/TypeScript"
                            detected_info["structure"] = "vue_project"
                            if suggest_name:
                                detected_info["suggested_name"] = package_data.get("name", "vue-app")
                            else:
                                detected_info["suggested_name"] = None
                        elif 'react' in deps:
                            detected_info["framework"] = "react"
                            detected_info["language"] = "JavaScript/TypeScript"
                            detected_info["structure"] = "react_project"
                            if suggest_name:
                                detected_info["suggested_name"] = package_data.get("name", "react-app")
                            else:
                                detected_info["suggested_name"] = None
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # Python/FastAPI detection
        elif any(f in file_names for f in ["requirements.txt", "pyproject.toml", "setup.py"]):
            detected_info["framework"] = "fastapi"
            detected_info["language"] = "Python"
            detected_info["structure"] = "python_project"

            # Check if it's specifically FastAPI
            try:
                if "requirements.txt" in file_names:
                    with open(current_dir / "requirements.txt", 'r') as f:
                        reqs = f.read().lower()
                        if 'fastapi' in reqs:
                            detected_info["framework"] = "fastapi"
                        elif 'django' in reqs:
                            detected_info["framework"] = "django"
                        elif 'flask' in reqs:
                            detected_info["framework"] = "flask"
            except FileNotFoundError:
                pass

        # Collect key files for context
        key_patterns = [
            "*.csproj", "*.sln", "Program.cs", "Startup.cs",  # .NET
            "package.json", "vite.config.*", "vue.config.*", "src/main.*",  # Vue/JS
            "requirements.txt", "pyproject.toml", "main.py", "app.py",  # Python
            "README.*", "LICENSE", ".gitignore", "Dockerfile"  # Common
        ]

        for pattern in key_patterns:
            matches = list(current_dir.glob(pattern))
            detected_info["key_files"].extend([str(f.relative_to(current_dir)) for f in matches])

    except Exception as e:
        print(f"Error detecting codebase: {e}")

    return detected_info


async def list_project_context(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """List files and folders with context for existing codebases."""
    directory = arguments.get("directory", ".")
    include_content = arguments.get("include_content", False)
    max_depth = arguments.get("max_depth", 3)
    context_files = arguments.get("context_files", [])

    try:
        current_dir = Path(directory)
        if not current_dir.exists():
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Directory not found: {directory}"
                )
            ]

        # Load context from file if available
        if not context_files and os.path.exists("context.txt"):
            context_files = await load_context_file("context.txt")

        # Detect framework first
        detected_info = await detect_existing_codebase(directory, context_files)

        # Build directory tree (focus on context files if provided)
        focused_analysis = bool(context_files)
        tree_structure = []
        ignore_patterns = {'.git', '.vscode', 'node_modules', '__pycache__', 'bin', 'obj', '.next', 'dist', 'build'}

        def build_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return

            items = []
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') and item.name not in {'.env', '.gitignore', '.cursorrules'}:
                        continue
                    if item.name in ignore_patterns:
                        continue
                    items.append(item)
            except PermissionError:
                return

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree_structure.append(f"{prefix}{current_prefix}{item.name}")

                if item.is_dir() and depth < max_depth:
                    extension = "    " if is_last else "│   "
                    build_tree(item, prefix + extension, depth + 1)

        build_tree(current_dir)

        # Prepare context report
        framework_info = ""
        if detected_info["framework"]:
            framework_info = f"""
🔍 **Detected Framework**: {detected_info['framework'].upper()}
📝 **Language**: {detected_info['language']}
🏗️ **Structure**: {detected_info['structure']}
{f"💡 **Suggested Name**: {detected_info['suggested_name']}" if detected_info['suggested_name'] else ""}
"""

        key_files_info = ""
        if detected_info["key_files"]:
            key_files_info = f"""
🗝️ **Key Files Found**:
{chr(10).join(f"  • {f}" for f in detected_info["key_files"][:10])}
{"  • ..." if len(detected_info["key_files"]) > 10 else ""}
"""

        tree_display = chr(10).join(tree_structure[:50])
        if len(tree_structure) > 50:
            tree_display += "\n  ... (truncated)"

        # Add context-specific information
        context_info = ""
        if context_files:
            context_info = f"""
🎯 **Focused Analysis** (using {len(context_files)} context files):
{chr(10).join(f"  • {f}" for f in context_files[:10])}
{"  • ..." if len(context_files) > 10 else ""}
"""
        elif os.path.exists("context.txt"):
            context_info = f"""
📋 **Context file found**: context.txt (use dev_context_add to manage)
"""

        context_report = f"""📂 **Project Context Analysis**: {directory}
{framework_info}
{context_info}
{key_files_info}

📁 **Directory Structure**:
```
{current_dir.name}/
{tree_display}
```

💡 **Usage Tips**:
- Use `dev_context_add files=["path1", "path2"]` to add files to context
- Use `dev_plan_create name="project" template="from-existing"` to create a plan based on detected framework
- Use `@context.txt` to reference context files in your conversations with Cursor
- Consider creating a `.cursorrules` file to maintain consistency with detected patterns
"""

        # Add file content previews if requested
        if include_content and detected_info["key_files"]:
            content_previews = []
            for file_path in detected_info["key_files"][:5]:  # Limit to first 5 files
                try:
                    full_path = current_dir / file_path
                    if full_path.is_file() and full_path.stat().st_size < 10000:  # Skip large files
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()[:500]  # First 500 chars
                            content_previews.append(f"\n**{file_path}**:\n```\n{content}\n{'...' if len(content) == 500 else ''}\n```")
                except Exception:
                    continue

            if content_previews:
                context_report += f"\n\n📄 **File Previews**:{''.join(content_previews)}"

        return [
            types.TextContent(
                type="text",
                text=context_report
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error analyzing project context: {str(e)}"
            )
        ]





async def validate_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Validate development plan syntax, logic, and compliance."""
    plan_file = arguments.get("plan_file", "./project.devplan")
    strict_mode = arguments.get("strict_mode", False)
    check_cursor_rules = arguments.get("check_cursor_rules", True)

    try:
        # If no specific path is provided, look in .cursorplans directory first
        if plan_file == "./project.devplan":
            cursorplans_path = Path(".cursorplans") / "project.devplan"
            if cursorplans_path.exists():
                plan_file = str(cursorplans_path)

        # Initialize validation engine
        validation_engine = ValidationEngine()

        # Run validation
        result = await validation_engine.validate_plan_file(
            plan_file_path=plan_file,
            strict_mode=strict_mode,
            check_cursor_rules=check_cursor_rules
        )

        # Format results for Cursor chat
        formatted_result = result.format_for_cursor()

        return [
            types.TextContent(
                type="text",
                text=formatted_result
            )
        ]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Validation engine error: {str(e)}\n\nThis may indicate a configuration issue with the validation system."
            )
        ]


async def apply_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Execute a development plan to create/modify files."""
    plan_file = arguments.get("plan_file", "./project.devplan")
    dry_run = arguments.get("dry_run", False)

    try:
        # If no specific path is provided, look in .cursorplans directory first
        if plan_file == "./project.devplan":
            cursorplans_path = Path(".cursorplans") / "project.devplan"
            if cursorplans_path.exists():
                plan_file = str(cursorplans_path)

        # Initialize execution engine
        executor = PlanExecutor()

        # Execute the plan
        result = await executor.execute_plan(plan_file, dry_run=dry_run)

        # Format results for Cursor chat
        if result.success:
            if dry_run:
                output = f"🔍 **Dry Run Results**\n\n"
                output += f"✅ Would execute {len(result.executed_phases)} phases:\n"
                for phase in result.executed_phases:
                    output += f"  - {phase}\n"

                if result.changes_made:
                    output += f"\n📝 **Would create/modify:**\n"
                    for change in result.changes_made:
                        output += f"  - {change}\n"
            else:
                output = f"✅ **Plan Execution Completed**\n\n"
                output += f"🎯 **Executed {len(result.executed_phases)} phases:**\n"
                for phase in result.executed_phases:
                    output += f"  - {phase}\n"

                if result.changes_made:
                    output += f"\n📝 **Changes made:**\n"
                    for change in result.changes_made:
                        output += f"  - {change}\n"

                if result.snapshot_id:
                    output += f"\n💾 **Snapshot created:** {result.snapshot_id}\n"

                if result.execution_time:
                    output += f"⏱️ **Execution time:** {result.execution_time:.2f}s\n"
        else:
            output = f"❌ **Plan Execution Failed**\n\n"
            output += f"🚫 **Error:** {result.error_message}\n"

            if result.failed_phase:
                output += f"📋 **Failed at phase:** {result.failed_phase}\n"

            if result.executed_phases:
                output += f"✅ **Completed phases:** {', '.join(result.executed_phases)}\n"

            if result.snapshot_id:
                output += f"🔄 **Rollback attempted to:** {result.snapshot_id}\n"

        return [
            types.TextContent(
                type="text",
                text=output
            )
        ]

    except PermissionError as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Permission Error:** {str(e)}\n\n**Troubleshooting:**\n"
                     f"• Check if you have write permissions in the current directory\n"
                     f"• Try running Cursor with elevated permissions if needed\n"
                     f"• Ensure the target directory is not read-only\n"
                     f"• Check if any files are locked by other processes"
            )
        ]
    except OSError as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **OS Error:** {str(e)}\n\n**Troubleshooting:**\n"
                     f"• Check disk space and file system permissions\n"
                     f"• Ensure the target path is valid and accessible\n"
                     f"• Try creating the directory manually first"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Execution error:** {str(e)}\n\nThis may indicate a configuration issue with the execution system."
            )
        ]


async def rollback_to_snapshot(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Rollback to a previous state snapshot."""
    snapshot_id = arguments.get("snapshot_id")

    if not snapshot_id:
        return [
            types.TextContent(
                type="text",
                text="❌ **Error:** No snapshot ID provided. Use `dev_snapshots` to list available snapshots."
            )
        ]

    try:
        # Initialize execution engine
        executor = PlanExecutor()

        # Perform rollback
        result = await executor.rollback_to_snapshot(snapshot_id)

        # Format results for Cursor chat
        if result.success:
            output = f"✅ **Rollback Completed**\n\n"
            output += f"🔄 **Rolled back to:** {snapshot_id}\n"

            if result.execution_time:
                output += f"⏱️ **Rollback time:** {result.execution_time:.2f}s\n"
        else:
            output = f"❌ **Rollback Failed**\n\n"
            output += f"🚫 **Error:** {result.error_message}\n"

            if result.execution_time:
                output += f"⏱️ **Attempt time:** {result.execution_time:.2f}s\n"

        return [
            types.TextContent(
                type="text",
                text=output
            )
        ]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Rollback error:** {str(e)}\n\nThis may indicate a configuration issue with the snapshot system."
            )
        ]


async def list_snapshots(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """List available state snapshots."""
    try:
        # Initialize execution engine
        executor = PlanExecutor()

        # Get snapshots
        snapshots = await executor.list_snapshots()

        # Format results for Cursor chat
        if snapshots:
            output = f"📸 **Available Snapshots**\n\n"

            for snapshot in snapshots:
                output += f"**{snapshot['id']}**\n"
                output += f"  📅 Created: {snapshot['created_at']}\n"
                output += f"  📝 Description: {snapshot['description']}\n"
                output += f"  📁 Files: {snapshot['file_count']}\n"
                output += f"  💾 Size: {snapshot['total_size']} bytes\n"

                if snapshot.get('restored_at'):
                    output += f"  🔄 Restored: {snapshot['restored_at']}\n"

                output += "\n"
        else:
            output = "📸 **No snapshots available**\n\n"
            output += "Create snapshots by executing development plans with `dev_apply_plan`.\n"

        return [
            types.TextContent(
                type="text",
                text=output
            )
        ]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Snapshot listing error:** {str(e)}\n\nThis may indicate a configuration issue with the snapshot system."
            )
        ]


if __name__ == "__main__":
    main()